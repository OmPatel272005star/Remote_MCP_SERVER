from fastmcp import FastMCP
import httpx
import os

mcp = FastMCP("Weather server")

WTTR_URL = "https://wttr.in/{city}"


async def fetch_weather(city: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(WTTR_URL.format(city=city), params={"format": "j1"})
        response.raise_for_status()
        return response.json()


@mcp.tool
async def get_current_weather(city: str) -> dict:
    """Get the current weather for a city."""

    data = await fetch_weather(city)
    current = data["current_condition"][0]

    return {
        "city": city,
        "temperature_c": float(current["temp_C"]),
        "wind_kph": float(current["windspeedKmph"]),
        "condition": current["weatherDesc"][0]["value"].strip(),
    }


@mcp.tool
async def get_forecast(city: str, days: int = 3) -> dict:
    """Get a daily weather forecast for a city (1-3 days)."""

    days = max(1, min(days, 3))
    data = await fetch_weather(city)

    forecast = [
        {
            "date": day["date"],
            "temp_max_c": float(day["maxtempC"]),
            "temp_min_c": float(day["mintempC"]),
            "condition": day["hourly"][4]["weatherDesc"][0]["value"].strip(),
        }
        for day in data["weather"][:days]
    ]

    return {"city": city, "forecast": forecast}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    mcp.run(transport="http", host="0.0.0.0", port=port)
