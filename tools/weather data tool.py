"""
weather data tool.py

Description:
    Retrieves current weather conditions for a given latitude/longitude using
    the Open-Meteo API (open-meteo.com). Free, no API key required.
    Returns temperature, wind speed, precipitation, weather code, and
    a plain-English weather description for use by traffic analysis agents.
"""

import json
import argparse
import requests
from pydantic import BaseModel, Field
from typing import Optional


class UserParameters(BaseModel):
    """
    Parameters used to configure a tool. This may include API keys,
    database connections, environment variables, etc.
    """
    pass  # Open-Meteo is free and requires no API key.


class ToolParameters(BaseModel):
    """
    Arguments of a tool call. These arguments are passed to this tool whenever
    an Agent calls this tool. The descriptions below are also provided to agents
    to help them make informed decisions of what to pass to the tool.
    """
    latitude: float = Field(
        description="Latitude of the location from the geocoding tool."
    )
    longitude: float = Field(
        description="Longitude of the location from the geocoding tool."
    )
    location_name: Optional[str] = Field(
        default="Unknown",
        description="Human-readable location name for labelling the output."
    )


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

# WMO weather interpretation codes → plain English
WMO_CODES = {
    0: "Clear sky",
    1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Icy fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snowfall", 73: "Moderate snowfall", 75: "Heavy snowfall",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail",
}

def weather_description(code: int) -> str:
    return WMO_CODES.get(code, f"Weather code {code}")

def traffic_weather_impact(code: int, wind_speed: float, precip: float) -> str:
    """Plain-English assessment of how weather conditions affect traffic."""
    if code in (95, 96, 99):
        return "Severe — thunderstorm conditions significantly reduce visibility and road traction"
    if code in (65, 75, 82, 86):
        return "High — heavy precipitation reduces road speed and increases accident risk"
    if code in (63, 73, 80, 81, 85):
        return "Moderate — precipitation may slow traffic on arterial roads"
    if code in (45, 48):
        return "Moderate — fog reduces visibility; expect cautious driving speeds"
    if wind_speed > 60:
        return "Moderate — high winds may affect larger vehicles and exposed roads"
    if precip > 0:
        return "Low — light precipitation; minor impact on traffic flow expected"
    return "Minimal — clear conditions, no significant weather impact on traffic"


def run_tool(config: UserParameters, args: ToolParameters):
    params = {
        "latitude": args.latitude,
        "longitude": args.longitude,
        "current": [
            "temperature_2m",
            "apparent_temperature",
            "precipitation",
            "weather_code",
            "wind_speed_10m",
            "wind_direction_10m",
            "relative_humidity_2m",
            "cloud_cover",
        ],
        "wind_speed_unit": "kmh",
        "precipitation_unit": "mm",
        "timezone": "auto",
    }

    try:
        resp = requests.get(OPEN_METEO_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.Timeout:
        return {"error": "Open-Meteo request timed out.", "location": args.location_name}
    except Exception as e:
        return {"error": str(e), "location": args.location_name}

    current = data.get("current", {})
    units = data.get("current_units", {})

    weather_code = current.get("weather_code", 0)
    wind_speed = current.get("wind_speed_10m", 0)
    precip = current.get("precipitation", 0)
    temp = current.get("temperature_2m")
    apparent_temp = current.get("apparent_temperature")

    return {
        "location": args.location_name,
        "coordinates": {"latitude": args.latitude, "longitude": args.longitude},
        "timestamp": current.get("time"),
        "weather": {
            "description": weather_description(weather_code),
            "weather_code": weather_code,
            "temperature_c": temp,
            "apparent_temperature_c": apparent_temp,
            "precipitation_mm": precip,
            "wind_speed_kmh": wind_speed,
            "wind_direction_deg": current.get("wind_direction_10m"),
            "humidity_percent": current.get("relative_humidity_2m"),
            "cloud_cover_percent": current.get("cloud_cover"),
        },
        "traffic_weather_impact": traffic_weather_impact(weather_code, wind_speed, precip),
        "source": "Open-Meteo (open-meteo.com) — free, no API key required",
    }


OUTPUT_KEY = "tool_output"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-params", required=True)
    parser.add_argument("--tool-params", required=True)
    cli_args = parser.parse_args()
    config = UserParameters(**json.loads(cli_args.user_params))
    params = ToolParameters(**json.loads(cli_args.tool_params))
    output = run_tool(config, params)
    print(OUTPUT_KEY, json.dumps(output, indent=2))
