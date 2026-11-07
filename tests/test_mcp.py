"""Actual MCP client/server protocol tests, with in-memory and stdio transports."""

import os
import sys

import pytest
from mcp import Client, StdioServerParameters

from weather_mcp_server.config import Settings
from weather_mcp_server.rate_limit import RateLimiter
from weather_mcp_server.server import create_server


@pytest.mark.asyncio
async def test_list_tools_and_schemas():
    server = create_server(settings=Settings(backend="mock"))
    async with Client(server, raise_exceptions=True) as client:
        listing = await client.list_tools()
        assert {item.name for item in listing.tools} == {
            "get_current_weather",
            "get_weather_forecast",
            "compare_weather",
        }
        by_name = {item.name: item for item in listing.tools}
        assert "city" in by_name["get_current_weather"].input_schema["properties"]
        assert "days" in by_name["get_weather_forecast"].input_schema["properties"]
        assert by_name["get_weather_forecast"].input_schema["properties"]["days"]["maximum"] == 7
        assert all(tool.description for tool in listing.tools)
        assert all(tool.annotations and tool.annotations.read_only_hint for tool in listing.tools)


@pytest.mark.asyncio
async def test_tool_calls_return_real_structured_content():
    server = create_server(settings=Settings(backend="mock"))
    async with Client(server, raise_exceptions=True) as client:
        current = await client.call_tool("get_current_weather", {"city": "Berlin"})
        assert not current.is_error
        assert current.structured_content["source"] == "mock-fixture"
        assert current.structured_content["temperature_c"] == 18
        forecast = await client.call_tool("get_weather_forecast", {"city": "Berlin", "days": 2})
        assert not forecast.is_error
        assert len(forecast.structured_content["days"]) == 2
        comparison = await client.call_tool(
            "compare_weather", {"first_city": "Berlin", "second_city": "Tokyo"}
        )
        assert not comparison.is_error
        assert comparison.structured_content["temperature_difference_c"] == -5


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("tool", "arguments"),
    [
        ("get_current_weather", {"city": ""}),
        ("get_current_weather", {"city": "Berlin\nTokyo"}),
        ("get_weather_forecast", {"city": "Berlin", "days": 0}),
        ("get_weather_forecast", {"city": "Berlin", "days": 8}),
        ("get_weather_forecast", {"city": "Berlin", "days": "many"}),
        ("compare_weather", {"first_city": "Berlin", "second_city": "<invalid>"}),
    ],
)
async def test_tool_schema_rejects_invalid_inputs(tool, arguments):
    server = create_server(settings=Settings(backend="mock"))
    async with Client(server, raise_exceptions=True) as client:
        result = await client.call_tool(tool, arguments)
        assert result.is_error
        assert result.structured_content is None


@pytest.mark.asyncio
async def test_unknown_city_has_safe_public_error():
    server = create_server(settings=Settings(backend="mock"))
    async with Client(server, raise_exceptions=True) as client:
        result = await client.call_tool("get_current_weather", {"city": "Atlantis"})
        assert result.is_error
        assert "City not found" in result.content[0].text
        assert "traceback" not in result.content[0].text.lower()


@pytest.mark.asyncio
async def test_rate_limit_is_enforced_per_tool_call():
    settings = Settings(backend="mock")
    limiter = RateLimiter(calls=1, window_seconds=60)
    server = create_server(settings=settings, limiter=limiter)
    async with Client(server, raise_exceptions=True) as client:
        first = await client.call_tool("get_current_weather", {"city": "Berlin"})
        second = await client.call_tool("get_current_weather", {"city": "Tokyo"})
        assert not first.is_error
        assert second.is_error
        assert "Too many requests" in second.content[0].text


@pytest.mark.asyncio
async def test_real_stdio_subprocess_protocol():
    """End-to-end launch through the SDK's real stdio protocol transport."""
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "weather_mcp_server"],
        env={**os.environ, "MCP_BACKEND": "mock"},
    )
    async with Client(params) as client:
        result = await client.list_tools()
        assert len(result.tools) == 3
        reading = await client.call_tool("get_current_weather", {"city": "Tokyo"})
        assert not reading.is_error
        assert reading.structured_content["source"] == "mock-fixture"
