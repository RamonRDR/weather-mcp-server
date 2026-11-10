"""Public messages never include upstream payloads, hostnames, secrets or tracebacks."""


class WeatherError(Exception):
    public_message = "Unable to retrieve weather data."


class CityNotFound(WeatherError):
    public_message = "City not found. Try a more specific city name."


class WeatherTimeout(WeatherError):
    public_message = "Weather provider timed out. Try again later."


class WeatherUnavailable(WeatherError):
    public_message = "Weather service is temporarily unavailable."


class InvalidWeatherPayload(WeatherError):
    public_message = "Weather provider returned incomplete or invalid data."


class TooManyRequests(WeatherError):
    public_message = "Too many requests. Try again later."


class InvalidCity(WeatherError):
    public_message = "City must contain 1–100 printable characters."
