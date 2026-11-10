# MCP demonstration and proof

**Offline reproducible MCP demo** (fictional values):
```bash
python -m pip install -e '.[dev]'
python -m weather_mcp_server.demo
```

The demo opens an actual SDK MCP client, discovers tools, invokes all three, invokes an invalid forecast request, and prints structured results and error flags. `mock-fixture` is shown explicitly in all successful responses. The reference observations have fixed timestamps and are not real weather measurements.

**Real stdio integration test**, no external calls:
```bash
MCP_BACKEND=mock python -m pytest -q tests/test_mcp.py
```

**Inspector**, using `npx` as required by the official client:
```bash
MCP_BACKEND=mock npx @modelcontextprotocol/inspector python -m weather_mcp_server
```
The Inspector is interactive, so manually inspect tools/list and call the three tools. This README does not claim an Inspector screenshot or a live-provider recording.

**Optional real integration**: start the Weather Cache API from its main branch (requires its Redis setup), select `MCP_BACKEND=cache_api`, and run the MCP server via stdio. No real-provider calls are part of the required CI checks. Some upstream behavior depends on the other project's deployment and third-party availability.

Status statements should be based on actual GitHub Actions results, not assumed checks.
