"""
geocoding tool.py

Description:
    Converts a city or district name into geographic coordinates (latitude/longitude)
    using the Nominatim OpenStreetMap geocoding API.
    Free to use — no API key required.
    Returns coordinates for use by the weather, air quality, and road network tools.
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
    pass  # Nominatim is free and requires no API key.


class ToolParameters(BaseModel):
    """
    Arguments of a tool call. These arguments are passed to this tool whenever
    an Agent calls this tool. The descriptions below are also provided to agents
    to help them make informed decisions of what to pass to the tool.
    """
    location: str = Field(
        description=(
            "City, district, or neighbourhood name to geocode. "
            "Include the city or country for accuracy, e.g. 'Marina District, San Francisco' "
            "or 'Downtown Dubai'."
        )
    )
    country_code: Optional[str] = Field(
        default=None,
        description=(
            "ISO 3166-1 alpha-2 country code to narrow the search, e.g. 'US', 'AE', 'IN'. "
            "Recommended when the district name may be ambiguous."
        )
    )


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "ClouederaHOL-TrafficSenseAI/1.0 (education; contact: support@cloudera.com)"


def run_tool(config: UserParameters, args: ToolParameters):
    params = {
        "q": args.location,
        "format": "json",
        "limit": 1,
        "addressdetails": 1,
    }
    if args.country_code:
        params["countrycodes"] = args.country_code.lower()

    headers = {"User-Agent": USER_AGENT}

    try:
        resp = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        results = resp.json()
    except requests.exceptions.Timeout:
        return {"error": "Nominatim geocoding request timed out.", "location": args.location}
    except Exception as e:
        return {"error": str(e), "location": args.location}

    if not results:
        return {
            "error": f"Location not found: '{args.location}'",
            "suggestion": (
                "Try adding more context, e.g. 'Marina District, San Francisco, USA' "
                "or use the country_code parameter."
            ),
        }

    r = results[0]
    address = r.get("address", {})

    return {
        "location_query": args.location,
        "display_name": r.get("display_name"),
        "latitude": float(r["lat"]),
        "longitude": float(r["lon"]),
        "type": r.get("type"),
        "address": {
            "district": address.get("suburb") or address.get("neighbourhood") or address.get("quarter"),
            "city": address.get("city") or address.get("town") or address.get("village"),
            "state": address.get("state"),
            "country": address.get("country"),
            "country_code": address.get("country_code", "").upper(),
        },
        "source": "Nominatim / OpenStreetMap (nominatim.openstreetmap.org)",
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
