"""Real MCP tools with typed schemas, safe public failures and stdio transport."""

import logging
from collections.abc import Awaitable, Callable
from typing import Annotated, TypeVar

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import Field

from weather_mcp_server.config import Settings
from weather_mcp_server.errors import WeatherError
from weather_mcp_server.logging_config import configure_logging
from weather_mcp_server.rate_limit import RateLimiter
from weather_mcp_server.schemas import City, ComparisonReport, ForecastReport, WeatherReport
from weather_mcp_server.service import WeatherService

T = TypeVar("T")


def create_server(
    service: WeatherService | None = None,
    settings: Settings | None = None,
    limiter: RateLimiter | None = None,
) -> MCPServer:
    settings = settings or Settings()
    service = service or WeatherService(settings)
    limiter = limiter or RateLimiter(settings.rate_limit_calls, settings.rate_limit_window_seconds)
    logger = configure_logging(settings.log_level)
    server = MCPServer("Weather MCP Server")

    async def invoke(action: Callable[[], Awaitable[T]]) -> T:
        try:
            await limiter.check()
            return await action()
        except WeatherError as exc:
            logger.warning("tool_failure:%s", type(exc).__name__)
            raise ToolError(exc.public_message) from None
        except Exception:
            logger.error("unexpected_tool_failure", exc_info=True)
            raise ToolError("Unexpected weather service failure.") from None

    @server.tool()
    async def get_current_weather(city: City) -> WeatherReport:
        """Read current weather for a city with units, observation time and source."""
        return await invoke(lambda: service.current(city))

    @server.tool()
    async def get_weather_forecast(
        city: City,
        days: Annotated[int, Field(ge=1, le=7, description="Forecast days (1 to 7).")] = 3,
    ) -> ForecastReport:
        """Read 1–7 daily forecasts, with dates, temperatures and possible rainfall."""
        return await invoke(lambda: service.forecast(city, days))

    @server.tool()
    async def compare_weather(first_city: City, second_city: City) -> ComparisonReport:
        """Compare current temperatures in two cities; first minus second, in °C."""
        return await invoke(lambda: service.compare(first_city, second_city))

    logger.debug("server_registered_three_read_only_tools")
    return server


mcp = create_server()
