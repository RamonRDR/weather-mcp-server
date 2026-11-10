# Architecture and decisions

## 001: Official MCP SDK v2, stdio first

The server uses the **official MCP Python SDK 2.x** `MCPServer` class, with typed Pydantic inputs and structured tool outputs. The old `FastMCP` import was renamed in SDK v2. We deliberately use **stdio**, not an HTTP endpoint, because the initial use case is a local assistant launching a child process. The standard output stream is protocol-only; JSON operational logs go to stderr.

## 002: Cache API as current-weather backend, not an invented forecast endpoint

The actual `RamonRDR/weather-cache-api` current **main** branch exposes:
- `GET /weather?city=...` for current data
- `GET /metrics` for process-local metrics

The endpoint returns `location` and `current` objects, `source`, and `cached`. This server validates those objects, forwards cached status, and maps WMO codes to descriptions. No caching logic is repeated here. The API also uses Redis and an upstream Open-Meteo integration, but that setup belongs to the other repository.

**No daily forecast endpoint exists yet.** Forecast requests therefore use Open-Meteo directly through a separate fixed-destination adapter. No changes are made to the Cache API.

## 003: Three backends, explicit semantics

- `MCP_BACKEND=cache_api` (default): current weather calls the running Weather Cache API; forecast calls Open-Meteo.
- `MCP_BACKEND=open_meteo`: both current and forecast call Open-Meteo. Useful if the Weather Cache API is not running. No Redis cache is provided.
- `MCP_BACKEND=mock`: deterministic, fictional sample data for testing and offline demo. Never label these values as current live weather.

## 004: Minimal security boundaries

No tool accepts a URL, file path, SQL statement, executable, script, credentials or write operation. The base URL is *operator-controlled* by an environment variable. HTTP may be used only with a loopback host, and remote origins require HTTPS. Arbitrary redirects are disabled. Open-Meteo hosts are constants.

Pydantic enforces city size/character boundaries and a 1–7-day forecast. Upstream response models reject missing required fields, non-finite numbers, inconsistent daily arrays and invalid temperatures. A 100 KB response cap avoids oversized data being parsed (a full streamed size cap would be needed for hostile remote providers). The stdio server implements a bounded, per-process, fixed-window request quota. The limiter is not distributed and does not constitute production multi-tenant rate limiting.

Public errors are intentionally generic. The SDK marks anticipated tool errors as `is_error=true`. Exceptions and stack traces are not returned to the assistant. Logs do not include city names, raw provider bodies, URLs or credentials. Host environment proxies are ignored in production-managed httpx clients.

## 005: Scope boundaries

The code has no remote HTTP transport, no OAuth, no user accounts, no multi-tenancy, no background workers, and no deployment. Exposing a remote MCP endpoint would require additional authentication, origin and host validation, session safety, transport rate limits and a fresh threat model.
