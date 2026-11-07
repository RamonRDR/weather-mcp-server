"""Console entry point: stdout must remain exclusively MCP protocol traffic."""

from weather_mcp_server.server import mcp


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
