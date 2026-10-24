"""
air quality tool.py

Description:
    Retrieves current air quality data for a given latitude/longitude using
    the Open-Meteo Air Quality API (air-quality-api.open-meteo.com).
    Free, no API key required.
    Returns PM2.5, PM10, NO2, O3, and a European Air Quality Index (AQI)
    with plain-English health guidance for use by traffic analysis agents.
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
    pass  # Open-Meteo Air Quality API is free and requires no API key.


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


AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

# European AQI scale
AQI_LEVELS = [
    (20,  "Good",        "Air quality is satisfactory. No health concern."),
    (40,  "Fair",        "Acceptable quality. Sensitive individuals may experience minor discomfort."),
    (60,  "Moderate",    "Sensitive groups (children, elderly, respiratory conditions) should limit prolonged outdoor exertion."),
    (80,  "Poor",        "Everyone may begin to experience health effects. Sensitive groups may experience more serious effects."),
    (100, "Very Poor",   "Health alert: everyone may experience serious health effects. Avoid prolonged outdoor activity."),
    (999, "Extremely Poor", "Health emergency. Entire population is likely to be affected. Stay indoors."),
]

def aqi_category(aqi: float):
    for threshold, label, guidance in AQI_LEVELS:
        if aqi <= threshold:
            return label, guidance
    return "Extremely Poor", AQI_LEVELS[-1][2]


def run_tool(config: UserParameters, args: ToolParameters):
    params = {
        "latitude": args.latitude,
        "longitude": args.longitude,
        "current": [
            "pm10",
            "pm2_5",
            "nitrogen_dioxide",
            "ozone",
            "european_aqi",
            "carbon_monoxide",
        ],
        "timezone": "auto",
    }

    try:
        resp = requests.get(AIR_QUALITY_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.Timeout:
        return {"error": "Open-Meteo Air Quality request timed out.", "location": args.location_name}
    except Exception as e:
        return {"error": str(e), "location": args.location_name}

    current = data.get("current", {})
    aqi = current.get("european_aqi")
    pm25 = current.get("pm2_5")
    pm10 = current.get("pm10")
    no2 = current.get("nitrogen_dioxide")
    o3 = current.get("ozone")
    co = current.get("carbon_monoxide")

    aqi_label, aqi_guidance = aqi_category(aqi) if aqi is not None else ("Unknown", "No AQI data available.")

    # Traffic context: NO2 and CO are direct markers of vehicle emissions
    emission_note = None
    if no2 is not None and no2 > 40:
        emission_note = (
            f"NO2 is elevated ({no2:.1f} µg/m³ vs WHO guideline 25 µg/m³). "
            "This may indicate heavy vehicle traffic or industrial activity nearby."
        )
    if co is not None and co > 4000:
        emission_note = (emission_note or "") + (
            f" CO is elevated ({co:.0f} µg/m³). "
            "High CO can indicate significant combustion vehicle congestion."
        )

    return {
        "location": args.location_name,
        "coordinates": {"latitude": args.latitude, "longitude": args.longitude},
        "timestamp": current.get("time"),
        "air_quality": {
            "european_aqi": aqi,
            "aqi_category": aqi_label,
            "health_guidance": aqi_guidance,
            "pm2_5_ug_m3": pm25,
            "pm10_ug_m3": pm10,
            "nitrogen_dioxide_ug_m3": no2,
            "ozone_ug_m3": o3,
            "carbon_monoxide_ug_m3": co,
        },
        "traffic_emission_note": emission_note,
        "source": "Open-Meteo Air Quality API (air-quality-api.open-meteo.com) — free, no API key required",
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
