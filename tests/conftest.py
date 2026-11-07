"""HTTP MockTransport fixtures: no live network or paid services in tests."""

import httpx
import pytest

from weather_mcp_server.config import Settings
from weather_mcp_server.service import WeatherService


@pytest.fixture
def sample_weather() -> dict[str, object]:
    return {
        "location": {
            "name": "Berlin",
            "country": "Germany",
            "latitude": 52.52,
            "longitude": 13.41,
        },
        "current": {
            "observed_at": "2026-11-01T12:00:00Z",
            "temperature_c": 12.3,
            "apparent_temperature_c": 10.0,
            "relative_humidity_percent": 68,
            "precipitation_mm": 0,
            "wind_speed_kmh": 12,
            "weather_code": 2,
        },
        "source": "open-meteo",
        "cached": True,
    }


@pytest.fixture
def mock_weather_service(sample_weather: dict[str, object]):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/weather":
            return httpx.Response(200, json=sample_weather)
        if request.url.host == "geocoding-api.open-meteo.com":
            return httpx.Response(
                200,
                json={
                    "results": [{
                        "name": "Berlin",
                        "country": "Germany",
                        "latitude": 52.52,
                        "longitude": 13.41,
                    }]
                },
            )
        if request.url.host == "api.open-meteo.com":
            if "daily" in request.url.params:
                days = int(request.url.params["forecast_days"])
                dates = [f"2026-11-{i + 1:02d}" for i in range(days)]
                return httpx.Response(
                    200,
                    json={
                        "daily": {
                            "time": dates,
                            "temperature_2m_min": [5.1] * days,
                            "temperature_2m_max": [14.2] * days,
                            "precipitation_probability_max": [20] * days,
                            "weather_code": [2] * days,
                        }
                    },
                )
            return httpx.Response(
                200,
                json={
                    "current": {
                        "time": "2026-11-01T12:00",
                        "temperature_2m": 12.3,
                        "apparent_temperature": 10,
                        "relative_humidity_2m": 68,
                        "precipitation": 0,
                        "weather_code": 2,
                        "wind_speed_10m": 12,
                    }
                },
            )
        return httpx.Response(500)

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    service = WeatherService(Settings(backend="cache_api"), client)
    yield service
    import asyncio

    asyncio.run(client.aclose())
