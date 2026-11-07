"""Validated input/output contracts; missing values are never fabricated."""

from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

City = Annotated[
    str,
    Field(
        min_length=1,
        max_length=100,
        pattern=r"^[^\x00-\x1f\x7f<>]*$",
        description="City name (1–100 characters; no control characters or markup).",
    ),
]


class CleanModel(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False, extra="ignore")


class Location(CleanModel):
    name: str = Field(min_length=1)
    country: str | None = None
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class CacheCurrent(CleanModel):
    observed_at: datetime
    temperature_c: float
    apparent_temperature_c: float | None = None
    relative_humidity_percent: int | None = Field(default=None, ge=0, le=100)
    precipitation_mm: float | None = None
    weather_code: int
    wind_speed_kmh: float | None = None


class CachePayload(CleanModel):
    location: Location
    current: CacheCurrent
    source: str = Field(min_length=1)
    cached: bool = False


class WeatherReport(CleanModel):
    location: Location
    observed_at: datetime
    temperature_c: float
    apparent_temperature_c: float | None
    relative_humidity_percent: int | None
    precipitation_mm: float | None
    wind_speed_kmh: float | None
    weather_code: int
    condition: str | None
    source: str
    cached: bool | None = None


class ForecastDay(CleanModel):
    date: date
    temperature_min_c: float
    temperature_max_c: float
    precipitation_probability_percent: int | None = Field(default=None, ge=0, le=100)
    weather_code: int | None
    condition: str | None

    @model_validator(mode="after")
    def check_temps(self) -> "ForecastDay":
        if self.temperature_min_c > self.temperature_max_c:
            raise ValueError("Minimum temperature exceeds maximum")
        return self


class ForecastReport(CleanModel):
    location: Location
    days: list[ForecastDay]
    source: str


class ComparisonReport(CleanModel):
    first: WeatherReport
    second: WeatherReport
    temperature_difference_c: float


class GeocodingPayload(CleanModel):
    results: list[Location] = Field(default_factory=list)


class MeteoCurrent(CleanModel):
    time: datetime
    temperature_2m: float
    relative_humidity_2m: int | None = Field(default=None, ge=0, le=100)
    apparent_temperature: float | None = None
    precipitation: float | None = None
    weather_code: int
    wind_speed_10m: float | None = None


class MeteoCurrentPayload(CleanModel):
    current: MeteoCurrent


class MeteoDaily(CleanModel):
    time: list[date]
    temperature_2m_min: list[float]
    temperature_2m_max: list[float]
    weather_code: list[int] | None = None
    precipitation_probability_max: list[int] | None = None

    @model_validator(mode="after")
    def validate_lengths(self) -> "MeteoDaily":
        size = len(self.time)
        arrays = [
            self.temperature_2m_min,
            self.temperature_2m_max,
            self.weather_code,
            self.precipitation_probability_max,
        ]
        if any(x is not None and len(x) != size for x in arrays):
            raise ValueError("Inconsistent daily forecast array lengths")
        if self.precipitation_probability_max and any(
            value < 0 or value > 100 for value in self.precipitation_probability_max
        ):
            raise ValueError("Invalid precipitation probability")
        return self


class MeteoDailyPayload(CleanModel):
    daily: MeteoDaily
