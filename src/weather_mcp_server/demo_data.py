"""Deterministic, explicitly fictional sample observations for offline demonstrations."""

from datetime import UTC, date, datetime, timedelta

from weather_mcp_server.errors import CityNotFound
from weather_mcp_server.schemas import ForecastDay, ForecastReport, Location, WeatherReport

# These values are *not* measurements, predictions or historical weather.
SAMPLES = {
    "berlin": ("Berlin", "Germany", 52.52, 13.41, 18.0),
    "tokyo": ("Tokyo", "Japan", 35.68, 139.69, 23.0),
    "itajai": ("Itajaí", "Brazil", -26.91, -48.66, 26.0),
    "itajaí": ("Itajaí", "Brazil", -26.91, -48.66, 26.0),
}
FIXTURE_TIME = datetime(2026, 10, 1, 12, tzinfo=UTC)


def current(city: str) -> WeatherReport:
    sample = SAMPLES.get(city.casefold())
    if sample is None:
        raise CityNotFound
    name, country, lat, lon, temperature = sample
    return WeatherReport(
        location=Location(name=name, country=country, latitude=lat, longitude=lon),
        observed_at=FIXTURE_TIME,
        temperature_c=temperature,
        apparent_temperature_c=None,
        relative_humidity_percent=None,
        precipitation_mm=None,
        wind_speed_kmh=None,
        weather_code=0,
        condition="Clear sky (fictional sample)",
        source="mock-fixture",
        cached=None,
    )


def forecast(city: str, days: int) -> ForecastReport:
    reading = current(city)
    return ForecastReport(
        location=reading.location,
        days=[
            ForecastDay(
                date=date(2026, 10, 1) + timedelta(days=offset),
                temperature_min_c=reading.temperature_c - 4,
                temperature_max_c=reading.temperature_c,
                precipitation_probability_percent=None,
                weather_code=0,
                condition="Clear sky (fictional sample)",
            )
            for offset in range(days)
        ],
        source="mock-fixture",
    )
