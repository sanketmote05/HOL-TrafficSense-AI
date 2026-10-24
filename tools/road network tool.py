import requests
import json
import argparse
import math
from pydantic import BaseModel, Field
from typing import Optional

class UserParameters(BaseModel):
    api_key: str = Field(
        description="TomTom API key. Register free at https://developer.tomtom.com/user/register"
    )

class ToolParameters(BaseModel):
    latitude: float = Field(
        description="Latitude of the district centre from the geocoding agent."
    )
    longitude: float = Field(
        description="Longitude of the district centre from the geocoding agent."
    )
    district_name: Optional[str] = Field(
        default="Unknown",
        description="Human-readable district name for labelling the output."
    )

def get_traffic_flow(lat: float, lon: float, api_key: str, zoom: int = 10):
    """
    Call TomTom Traffic Flow Segment Data API.
    Returns speed, free-flow speed, and travel time for the nearest road segment.
    zoom: 1 (motorway) to 22 (local road). 10 is a good balance for urban districts.
    """
    url = (
        f"https://api.tomtom.com/traffic/services/4/flowSegmentData"
        f"/absolute/{zoom}/json"
    )
    params = {
        "point": f"{lat},{lon}",
        "key": api_key,
        "unit": "KMPH",
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.HTTPError as e:
        return None, f"HTTP {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return None, str(e)

def classify_congestion(current_speed: float, free_flow_speed: float):
    """
    Calculate congestion ratio and return level + score.
    ratio = current / free_flow. Lower ratio = more congestion.
    """
    if free_flow_speed <= 0:
        return 0, "Unknown", 50
    ratio = current_speed / free_flow_speed
    score = int((1 - ratio) * 100)  # 0 = free flow, 100 = standstill
    if score < 20:
        level = "Low"
    elif score < 45:
        level = "Moderate"
    elif score < 70:
        level = "High"
    else:
        level = "Critical"
    return score, level, ratio

def run_tool(config: UserParameters, args: ToolParameters):

    lat = args.latitude
    lon = args.longitude

    # ── Call TomTom at two zoom levels ───────────────────────────
    # zoom 10 = arterial/primary roads (district-level overview)
    # zoom 14 = local roads (street-level detail)
    primary_data, primary_err = get_traffic_flow(lat, lon, config.api_key, zoom=10)
    local_data,   local_err   = get_traffic_flow(lat, lon, config.api_key, zoom=14)

    if primary_data is None and local_data is None:
        return {
            "district": args.district_name,
            "error": "TomTom API call failed for both zoom levels.",
            "details": {
                "primary_road_error": primary_err,
                "local_road_error":   local_err,
            },
            "troubleshooting": [
                "Verify your TomTom API key is correct and active.",
                "Register free at https://developer.tomtom.com/user/register",
                "Check the API key is entered correctly in the Agent Studio "
                "Configure step under UserParameters -> api_key.",
                "Ensure your free tier quota (2,500 requests/day) has not been exceeded.",
            ]
        }

    results = {}

    for label, data, err in [
        ("arterial_roads", primary_data, primary_err),
        ("local_roads",    local_data,   local_err),
    ]:
        if data and "flowSegmentData" in data:
            seg = data["flowSegmentData"]
            current_speed    = seg.get("currentSpeed", 0)
            free_flow_speed  = seg.get("freeFlowSpeed", 1)
            current_time     = seg.get("currentTravelTime", 0)
            free_flow_time   = seg.get("freeFlowTravelTime", 1)
            confidence       = seg.get("confidence", 0)
            road_closure     = seg.get("roadClosure", False)

            score, level, ratio = classify_congestion(current_speed, free_flow_speed)
            delay_pct = round((1 - ratio) * 100, 1)

            results[label] = {
                "current_speed_kmh":    current_speed,
                "free_flow_speed_kmh":  free_flow_speed,
                "current_travel_time_s": current_time,
                "free_flow_travel_time_s": free_flow_time,
                "speed_ratio":          round(ratio, 3),
                "delay_percent":        delay_pct,
                "congestion_score":     score,
                "congestion_level":     level,
                "data_confidence":      confidence,
                "road_closure":         road_closure,
            }
        else:
            results[label] = {
                "error": err or "No flowSegmentData in response",
                "congestion_level": "Unknown",
                "congestion_score": 0,
            }

    # ── Aggregate score across both zoom levels ───────────────────
    scores = [
        v["congestion_score"]
        for v in results.values()
        if isinstance(v.get("congestion_score"), int)
    ]
    avg_score = int(sum(scores) / len(scores)) if scores else 0

    if avg_score < 20:
        overall_level = "Low"
    elif avg_score < 45:
        overall_level = "Moderate"
    elif avg_score < 70:
        overall_level = "High"
    else:
        overall_level = "Critical"

    # ── Operator advisory notes ───────────────────────────────────
    notes = [
        f"District: {args.district_name} (centre: {lat}, {lon})",
        f"Overall congestion: {overall_level} (score {avg_score}/100)",
    ]

    art = results.get("arterial_roads", {})
    loc = results.get("local_roads", {})

    if "current_speed_kmh" in art:
        notes.append(
            f"Arterial roads: {art['current_speed_kmh']} km/h "
            f"(free flow: {art['free_flow_speed_kmh']} km/h) "
            f"— {art['delay_percent']}% slower than normal"
        )
    if "current_speed_kmh" in loc:
        notes.append(
            f"Local roads: {loc['current_speed_kmh']} km/h "
            f"(free flow: {loc['free_flow_speed_kmh']} km/h) "
            f"— {loc['delay_percent']}% slower than normal"
        )

    if art.get("road_closure") or loc.get("road_closure"):
        notes.append("ALERT: Road closure detected in this district.")

    if overall_level == "Critical":
        notes.append(
            "OPERATOR ACTION REQUIRED: Critical congestion. "
            "Recommend issuing diversion advisory and increasing public "
            "transport frequency."
        )
    elif overall_level == "High":
        notes.append(
            "CAUTION: High congestion. Monitor signal timing and "
            "consider issuing peak-hour rerouting advisory."
        )
    elif overall_level == "Low" and not (art.get("road_closure") or loc.get("road_closure")):
        notes.append(
            "Traffic flowing normally. No operator intervention required."
        )
    elif overall_level == "Low" and (art.get("road_closure") or loc.get("road_closure")):
        notes.append(
            "OPERATOR NOTE: Despite low congestion score, a road closure "
            "is active. Monitor for knock-on delays as diversion traffic builds."
        )

    return {
        "district":              args.district_name,
        "centre":                {"latitude": lat, "longitude": lon},
        "overall_congestion_score": avg_score,
        "overall_congestion_level": overall_level,
        "traffic_flow": results,
        "operator_notes": notes,
        "source": "TomTom Traffic Flow API v4 (api.tomtom.com)",
    }

OUTPUT_KEY = "tool_output"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-params", required=True)
    parser.add_argument("--tool-params", required=True)
    args = parser.parse_args()
    config = UserParameters(**json.loads(args.user_params))
    params = ToolParameters(**json.loads(args.tool_params))
    output = run_tool(config, params)
    print(OUTPUT_KEY, json.dumps(output))
