"""Fixed-destination HTTP adapters and weather-specific transformations."""

import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC

import httpx
from pydantic import ValidationError

from weather_mcp_server import demo_data
from weather_mcp_server.config import Settings
from weather_mcp_server.errors import (
    CityNotFound,
    InvalidCity,
    InvalidWeatherPayload,
    WeatherTimeout,
    WeatherUnavailable,
)
from weather_mcp_server.schemas import (
    CachePayload,
    ComparisonReport,
    ForecastDay,
    ForecastReport,
    GeocodingPayload,
    Location,
    MeteoCurrentPayload,
    MeteoDailyPayload,
    WeatherReport,
)

GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
CURRENT_FIELDS = (
    "temperature_2m,relative_humidity_2m,apparent_temperature,"
    "precipitation,weather_code,wind_speed_10m"
)
DAILY_FIELDS = "temperature_2m_min,temperature_2m_max,precipitation_probability_max,weather_code"
WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def normalize_city(city: str) -> str:
    normalized = " ".join(city.split())
    if (
        not 1 <= len(normalized) <= 100
        or any(ord(char) < 32 or ord(char) == 127 for char in city)
        or re.search(r"[<>]", city)
    ):
        raise InvalidCity
    return normalized


def condition(code: int | None) -> str | None:
    if code is None:
        return None
    return WEATHER_CODES.get(code, f"Unrecognized WMO code ({code})")


class WeatherService:
    def __init__(self, settings: Settings, http_client: httpx.AsyncClient | None = None) -> None:
        self.settings = settings
        self.http_client = http_client

    @asynccontextmanager
    async def _client(self) -> AsyncIterator[httpx.AsyncClient]:
        if self.http_client is not None:
            yield self.http_client
        else:
            async with httpx.AsyncClient(
                timeout=self.settings.http_timeout_seconds,
                follow_redirects=False,
                trust_env=False,
            ) as client:
                yield client

    async def _json(self, client: httpx.AsyncClient, url: str, params: dict[str, object]) -> object:
        try:
            response = await client.get(url, params=params)
            if response.status_code == 404:
                raise CityNotFound
            response.raise_for_status()
            if len(response.content) > 100_000:
                raise InvalidWeatherPayload
            return response.json()
        except httpx.TimeoutException as exc:
            raise WeatherTimeout from exc
        except (httpx.RequestError, httpx.HTTPStatusError) as exc:
            raise WeatherUnavailable from exc
        except ValueError as exc:
            raise InvalidWeatherPayload from exc

    async def _geocode(self, client: httpx.AsyncClient, city: str) -> Location:
        raw = await self._json(
            client,
            GEO_URL,
            {"name": city, "count": 1, "language": "en", "format": "json"},
        )
        try:
            locations = GeocodingPayload.model_validate(raw).results
        except ValidationError as exc:
            raise InvalidWeatherPayload from exc
        if not locations:
            raise CityNotFound
        return locations[0]

    async def current(self, city: str) -> WeatherReport:
        city = normalize_city(city)
        if self.settings.backend == "mock":
            return demo_data.current(city)
        async with self._client() as client:
            if self.settings.backend == "cache_api":
                raw = await self._json(
                    client, f"{self.settings.cache_api_base_url}/weather", {"city": city}
                )
                try:
                    result = CachePayload.model_validate(raw)
                except ValidationError as exc:
                    raise InvalidWeatherPayload from exc
                return WeatherReport(
                    location=result.location,
                    observed_at=result.current.observed_at,
                    temperature_c=result.current.temperature_c,
                    apparent_temperature_c=result.current.apparent_temperature_c,
                    relative_humidity_percent=result.current.relative_humidity_percent,
                    precipitation_mm=result.current.precipitation_mm,
                    wind_speed_kmh=result.current.wind_speed_kmh,
                    weather_code=result.current.weather_code,
                    condition=condition(result.current.weather_code),
                    source=result.source,
                    cached=result.cached,
                )
            location = await self._geocode(client, city)
            raw = await self._json(
                client,
                WEATHER_URL,
                {
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                    "current": CURRENT_FIELDS,
                    "timezone": "GMT",
                },
            )
            try:
                current = MeteoCurrentPayload.model_validate(raw).current
            except ValidationError as exc:
                raise InvalidWeatherPayload from exc
            observed_at = current.time
            if observed_at.tzinfo is None:
                observed_at = observed_at.replace(tzinfo=UTC)
            return WeatherReport(
                location=location,
                observed_at=observed_at,
                temperature_c=current.temperature_2m,
                apparent_temperature_c=current.apparent_temperature,
                relative_humidity_percent=current.relative_humidity_2m,
                precipitation_mm=current.precipitation,
                wind_speed_kmh=current.wind_speed_10m,
                weather_code=current.weather_code,
                condition=condition(current.weather_code),
                source="open-meteo",
                cached=None,
            )

    async def forecast(self, city: str, days: int) -> ForecastReport:
        city = normalize_city(city)
        if not 1 <= days <= 7:
            raise InvalidWeatherPayload
        if self.settings.backend == "mock":
            return demo_data.forecast(city, days)
        # The Weather Cache API does not implement daily forecasts.
        # Forecast always uses the fixed Open-Meteo endpoints; no cache is duplicated.
        async with self._client() as client:
            location = await self._geocode(client, city)
            raw = await self._json(
                client,
                WEATHER_URL,
                {
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                    "daily": DAILY_FIELDS,
                    "timezone": "GMT",
                    "forecast_days": days,
                },
            )
            try:
                daily = MeteoDailyPayload.model_validate(raw).daily
                if len(daily.time) != days:
                    raise InvalidWeatherPayload
                reports = [
                    ForecastDay(
                        date=day,
                        temperature_min_c=daily.temperature_2m_min[index],
                        temperature_max_c=daily.temperature_2m_max[index],
                        precipitation_probability_percent=(
                            daily.precipitation_probability_max[index]
                            if daily.precipitation_probability_max is not None
                            else None
                        ),
                        weather_code=(
                            daily.weather_code[index] if daily.weather_code is not None else None
                        ),
                        condition=condition(
                            daily.weather_code[index] if daily.weather_code is not None else None
                        ),
                    )
                    for index, day in enumerate(daily.time)
                ]
            except (ValidationError, ValueError, IndexError) as exc:
                raise InvalidWeatherPayload from exc
            return ForecastReport(location=location, days=reports, source="open-meteo")

    async def compare(self, first: str, second: str) -> ComparisonReport:
        left = await self.current(first)
        right = await self.current(second)
        return ComparisonReport(
            first=left,
            second=right,
            temperature_difference_c=round(left.temperature_c - right.temperature_c, 2),
        )
