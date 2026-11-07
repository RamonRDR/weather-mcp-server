"""HTTP contract, validation, provider degradation and mock-mode tests."""

import httpx
import pytest
from pydantic import ValidationError

from weather_mcp_server.config import Settings
from weather_mcp_server.errors import (
    CityNotFound,
    InvalidCity,
    InvalidWeatherPayload,
    WeatherTimeout,
    WeatherUnavailable,
)
from weather_mcp_server.service import WeatherService, normalize_city


@pytest.mark.asyncio
async def test_current_from_existing_cache_api(mock_weather_service):
    report = await mock_weather_service.current("  Berlin  ")
    assert report.location.country == "Germany"
    assert report.temperature_c == 12.3
    assert report.condition == "Partly cloudy"
    assert report.cached is True
    assert report.source == "open-meteo"


@pytest.mark.asyncio
async def test_forecast_uses_open_meteo_not_missing_cache_endpoint(mock_weather_service):
    forecast = await mock_weather_service.forecast("Berlin", 3)
    assert len(forecast.days) == 3
    assert forecast.days[0].precipitation_probability_percent == 20
    assert forecast.days[1].temperature_min_c == 5.1
    assert forecast.source == "open-meteo"


@pytest.mark.asyncio
async def test_comparison_subtracts_first_minus_second(mock_weather_service):
    report = await mock_weather_service.compare("Berlin", "Berlin")
    assert report.temperature_difference_c == 0
    assert report.first.cached is True


@pytest.mark.asyncio
async def test_direct_provider_mode_without_cache_api(mock_weather_service):
    mock_weather_service.settings = Settings(backend="open_meteo")
    report = await mock_weather_service.current("Berlin")
    assert report.temperature_c == 12.3
    assert report.cached is None
    assert report.observed_at.tzinfo is not None


@pytest.mark.asyncio
async def test_mock_mode_is_explicitly_fictional():
    service = WeatherService(Settings(backend="mock"))
    berlin = await service.current("Berlin")
    tokyo = await service.current("Tokyo")
    assert berlin.source == "mock-fixture"
    assert berlin.observed_at.year == 2026
    assert tokyo.temperature_c != berlin.temperature_c
    assert len((await service.forecast("Berlin", 7)).days) == 7
    with pytest.raises(CityNotFound):
        await service.current("Atlantis")


@pytest.mark.parametrize("invalid", ["", "   ", "x" * 101, "<script>", "Berlin\nTokyo"])
def test_city_validation(invalid):
    with pytest.raises(InvalidCity):
        normalize_city(invalid)


@pytest.mark.parametrize(
    "value",
    [
        "http://example.org",
        "https://name:secret@example.org",
        "https://example.org/a",
        "https://example.org?key=secret",
    ],
)
def test_reject_unsafe_cache_origins(value):
    with pytest.raises(ValidationError):
        Settings(cache_api_base_url=value)


@pytest.mark.asyncio
async def test_city_not_found():
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _: httpx.Response(404))
    ) as client:
        with pytest.raises(CityNotFound):
            await WeatherService(Settings(backend="cache_api"), client).current("Nowhere")


@pytest.mark.asyncio
async def test_http_error_is_not_exposed():
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _: httpx.Response(503, text="token=SECRET"))
    ) as client:
        with pytest.raises(WeatherUnavailable):
            await WeatherService(Settings(backend="cache_api"), client).current("Berlin")


@pytest.mark.asyncio
async def test_network_timeout():
    def timeout(_: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("super-secret-url")

    async with httpx.AsyncClient(transport=httpx.MockTransport(timeout)) as client:
        with pytest.raises(WeatherTimeout):
            await WeatherService(Settings(backend="cache_api"), client).current("Berlin")


@pytest.mark.asyncio
async def test_invalid_json():
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, text="not json"))
    ) as client:
        with pytest.raises(InvalidWeatherPayload):
            await WeatherService(Settings(backend="cache_api"), client).current("Berlin")


@pytest.mark.asyncio
async def test_incomplete_payload():
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json={"current": {}}))
    ) as client:
        with pytest.raises(InvalidWeatherPayload):
            await WeatherService(Settings(backend="cache_api"), client).current("Berlin")


@pytest.mark.asyncio
async def test_oversize_response():
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, text="a" * 100001))
    ) as client:
        with pytest.raises(InvalidWeatherPayload):
            await WeatherService(Settings(backend="cache_api"), client).current("Berlin")


@pytest.mark.asyncio
async def test_daily_array_length_mismatch():
    def handler(request: httpx.Request) -> httpx.Response:
        if "geocoding" in str(request.url):
            return httpx.Response(
                200,
                json={"results": [{"name": "Berlin", "latitude": 52.52, "longitude": 13.41}]},
            )
        return httpx.Response(
            200,
            json={
                "daily": {
                    "time": ["2026-11-01", "2026-11-02"],
                    "temperature_2m_min": [2],
                    "temperature_2m_max": [8, 9],
                }
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(InvalidWeatherPayload):
            await WeatherService(Settings(backend="cache_api"), client).forecast("Berlin", 2)
