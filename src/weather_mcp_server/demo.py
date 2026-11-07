"""MCP demonstration using an actual in-process client and clearly fictional readings."""

import asyncio
import json

from mcp import Client

from weather_mcp_server.config import Settings
from weather_mcp_server.server import create_server


async def run() -> None:
    # Deliberately no network calls. The returned weather is fictional.
    server = create_server(settings=Settings(backend="mock"))
    async with Client(server) as client:
        tools = await client.list_tools()
        print("DEMO: fictional mock weather, NOT observed or live data")
        print("MCP tools:", [tool.name for tool in tools.tools])
        for name, arguments in [
            ("get_current_weather", {"city": "Berlin"}),
            ("get_weather_forecast", {"city": "Berlin", "days": 2}),
            ("compare_weather", {"first_city": "Berlin", "second_city": "Tokyo"}),
            ("get_weather_forecast", {"city": "Berlin", "days": 99}),
        ]:
            response = await client.call_tool(name, arguments)
            print(json.dumps({
                "tool": name,
                "is_error": bool(response.is_error),
                "structured": response.structured_content,
            }, ensure_ascii=False, default=str))


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
