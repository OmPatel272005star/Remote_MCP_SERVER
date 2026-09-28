from fastmcp import FastMCP
import httpx
import os

mcp = FastMCP("Weather server")

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

WMO_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Freezing fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
}


def describe(code: int) -> str:
    return WMO_CODES.get(code, f"Unknown (code {code})")


async def geocode(city: str) -> tuple[float, float, str]:
    async with httpx.AsyncClient() as client:
        response = await client.get(GEOCODE_URL, params={"name": city, "count": 1})
        response.raise_for_status()
        results = response.json().get("results")

    if not results:
        raise ValueError(f"City not found: {city}")

    location = results[0]
    return location["latitude"], location["longitude"], location.get("name", city)


@mcp.tool
async def get_current_weather(city: str) -> dict:
    """Get the current weather for a city."""

    latitude, longitude, resolved_name = await geocode(city)

    async with httpx.AsyncClient() as client:
        response = await client.get(
            FORECAST_URL,
            params={"latitude": latitude, "longitude": longitude, "current_weather": "true"},
        )
        response.raise_for_status()
        current = response.json()["current_weather"]

    return {
        "city": resolved_name,
        "temperature_c": current["temperature"],
        "wind_kph": current["windspeed"],
        "condition": describe(current["weathercode"]),
    }


@mcp.tool
async def get_forecast(city: str, days: int = 3) -> dict:
    """Get a daily weather forecast for a city (1-7 days)."""

    days = max(1, min(days, 7))
    latitude, longitude, resolved_name = await geocode(city)

    async with httpx.AsyncClient() as client:
        response = await client.get(
            FORECAST_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "daily": "temperature_2m_max,temperature_2m_min,weathercode",
                "timezone": "auto",
                "forecast_days": days,
            },
        )
        response.raise_for_status()
        daily = response.json()["daily"]

    forecast = [
        {
            "date": date,
            "temp_max_c": daily["temperature_2m_max"][i],
            "temp_min_c": daily["temperature_2m_min"][i],
            "condition": describe(daily["weathercode"][i]),
        }
        for i, date in enumerate(daily["time"])
    ]

    return {"city": resolved_name, "forecast": forecast}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    mcp.run(transport="http", host="0.0.0.0", port=port)
