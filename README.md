# TrafficSense AI — Hands-On Lab Guide

**Course:** DSCI-275 Agentic AI with Cloudera Agent Studio  
**Domain:** Smart City / Urban Mobility  
**Pattern:** Parallel Fan-out (4 agents, Manager Agent ON, Conversational ON)  
**Estimated time:** 60–75 minutes

---

## Overview

TrafficSense AI is a real-time urban traffic intelligence system built on Cloudera Agent Studio. It accepts conversational queries about city districts (e.g. *"How is traffic in Marina and Downtown right now?"*), fans out parallel intelligence-gathering agents across three data sources — live traffic flow, current weather, and air quality — then synthesises a unified operator briefing.

### What you will build

| # | Agent | Role | Tool |
|---|-------|------|------|
| 1 | **Geocoding Agent** | Converts district names to lat/lon coordinates | `geocoding tool` |
| 2 | **Traffic Flow Agent** | Fetches live road speed & closure data from TomTom | `road network tool` |
| 3 | **Weather Intelligence Agent** | Retrieves current weather conditions | `weather data tool` |
| 4 | **Air Quality Agent** | Retrieves current air quality index | `air quality tool` |

> **Manager Agent** orchestrates agents 2, 3, and 4 in parallel after agent 1 geocodes the location.

### Architecture

```
User query: "How is traffic in Marina and Downtown?"
                        ↓
              [Manager Agent] ← Conversational ON
                        ↓
         Geocoding Agent (sequential first step)
                        ↓
    ┌───────────────────┼──────────────────────┐
    ↓                   ↓                      ↓
Traffic Flow Agent   Weather Agent       Air Quality Agent
(TomTom API)         (Open-Meteo)        (Open-Meteo AQ)
    ↓                   ↓                      ↓
    └───────────────────┼──────────────────────┘
                        ↓
            [Manager Agent synthesises]
                        ↓
          "Marina: Moderate congestion, 40/49 km/h.
           Road closure detected — OPERATOR ALERT.
           Temperature 36°C, AQI Fair."
```

### APIs Used

| API | Purpose | Cost | Key required? |
|-----|---------|------|--------------|
| TomTom Traffic Flow v4 | Live road speed & closures | Free (2,500 req/day) | **Yes** — free registration |
| Open-Meteo Forecast | Current weather | Free, unlimited | No |
| Open-Meteo Air Quality | PM2.5, PM10, AQI | Free, unlimited | No |
| Nominatim (OpenStreetMap) | District geocoding | Free, unlimited | No |

---

## Prerequisites

- Access to **Cloudera Agent Studio**
- A free **TomTom Developer account** with an API key
  - Register at: [https://developer.tomtom.com/user/register](https://developer.tomtom.com/user/register)
  - Free tier: 2,500 requests/day (sufficient for lab use)
  - Your API key will be entered in Agent Studio **UserParameters** (Step 6)

---

## Part 1 — Create the Custom Tools

### Step 1 — Open Tools Catalog

1. In Agent Studio top navigation, click **Tools Catalog**.

---

### Step 2 — Create the `geocoding tool`

1. Click **Create Tool Template**.
2. Enter the tool name:
   ```
   geocoding tool
   ```
   > Use spaces, not underscores.
3. Click **Generate**.
4. Click **Edit Tool File** → **Edit** next to `tool.py`.
5. Replace the entire contents with the code from:
   ```
   trafficsense-ai/tools/geocoding tool.py
   ```
6. `requirements.txt` only needs `pydantic` and `requests`:
   ```
   # https://pip.pypa.io/en/stable/reference/requirements-file-format/
   pydantic
   requests
   ```
7. Click **Save**.

---

### Step 3 — Create the `road network tool`

1. Click **Create Tool Template**.
2. Enter the tool name:
   ```
   road network tool
   ```
3. Click **Generate** → **Edit Tool File** → **Edit** next to `tool.py`.
4. Replace the contents with the code from:
   ```
   trafficsense-ai/tools/road network tool.py
   ```
5. Update `requirements.txt`:
   ```
   # https://pip.pypa.io/en/stable/reference/requirements-file-format/
   pydantic
   requests
   ```
6. Click **Save**.

> **Note:** This tool has a `UserParameters` field: `api_key`. You will enter your TomTom API key in the workflow Configure step (Step 14), not here.

---

### Step 4 — Create the `weather data tool`

1. Click **Create Tool Template**.
2. Enter:
   ```
   weather data tool
   ```
3. Click **Generate** → **Edit Tool File** → paste the code from:
   ```
   trafficsense-ai/tools/weather data tool.py
   ```
4. Update `requirements.txt` to include `pydantic` and `requests`.
5. Click **Save**.

---

### Step 5 — Create the `air quality tool`

1. Click **Create Tool Template**.
2. Enter:
   ```
   air quality tool
   ```
3. Click **Generate** → **Edit Tool File** → paste the code from:
   ```
   trafficsense-ai/tools/air quality tool.py
   ```
4. Update `requirements.txt` to include `pydantic` and `requests`.
5. Click **Save**.

---

### Step 6 — Verify tools in the catalog

After saving all four tools, in **Tools Catalog** you should see:
- `geocoding tool`
- `road network tool`
- `weather data tool`
- `air quality tool`

---

## Part 2 — Create the Agentic Workflow

### Step 7 — Create a new workflow

1. Click **Agentic Workflows** → **+ New Workflow**.
2. Name it:
   ```
   TrafficSense AI XX
   ```
   *(Replace `XX` with your initials.)*
3. Click **Create**.

---

### Step 8 — Configure workflow settings

1. Click **Edit Workflow** → **Configure** tab.
2. Set:

   | Setting | Value |
   |---------|-------|
   | **Conversational** | **ON** |
   | **Manager Agent** | **ON** |

   > Both must be ON. Conversational mode allows the chatbot-style interaction; Manager Agent enables parallel fan-out across the intelligence agents.

3. Click **Save**.

---

### Step 9 — Add Agent: Geocoding Agent

1. Click **Add Tasks** → **Create or Edit Agents** → **+ Create New Agent**.
2. Fill in:

   | Field | Value |
   |-------|-------|
   | **Name** | `geocoding_agent` |
   | **Role** | Geospatial Coordinator |
   | **Backstory** | You are an expert in urban geography and geospatial data. You convert city district names into precise geographic coordinates that other agents can use to query real-time data sources. |
   | **Goal** | Convert each district name provided by the user into latitude and longitude coordinates using the geocoding tool. Return all coordinates in a structured format for the parallel intelligence agents. |
   | **LLM Model** | gpt-4o (Default) |

3. Under **Add Tools**, add the `geocoding tool`.
4. Click **Save Agent**.

---

### Step 10 — Add Agent: Traffic Flow Agent

1. Click **+ Create New Agent**.
2. Fill in:

   | Field | Value |
   |-------|-------|
   | **Name** | `traffic_flow_agent` |
   | **Role** | Traffic Operations Specialist |
   | **Backstory** | You are a senior traffic operations engineer with access to real-time road network data. You monitor live traffic flow, detect congestion patterns, and identify road closures. You provide operators with clear, actionable traffic intelligence. |
   | **Goal** | For each district provided by the geocoding agent, call the road network tool to retrieve live traffic flow data including current speeds, free-flow speeds, congestion level, and any active road closures. Report findings clearly with operator notes. |
   | **LLM Model** | gpt-4o (Default) |

3. Under **Add Tools**, add the `road network tool`.
4. Click **Save Agent**.

---

### Step 11 — Add Agent: Weather Intelligence Agent

1. Click **+ Create New Agent**.
2. Fill in:

   | Field | Value |
   |-------|-------|
   | **Name** | `weather_intelligence_agent` |
   | **Role** | Meteorological Analyst |
   | **Backstory** | You are a meteorological analyst specialising in weather-traffic interaction. You retrieve current weather data and assess how conditions — rain, fog, wind, extreme heat — are likely to affect urban road networks. |
   | **Goal** | For each district, retrieve current weather conditions using the weather data tool and provide a clear assessment of how those conditions are affecting or may affect traffic flow in the area. |
   | **LLM Model** | gpt-4o (Default) |

3. Under **Add Tools**, add the `weather data tool`.
4. Click **Save Agent**.

---

### Step 12 — Add Agent: Air Quality Agent

1. Click **+ Create New Agent**.
2. Fill in:

   | Field | Value |
   |-------|-------|
   | **Name** | `air_quality_agent` |
   | **Role** | Environmental Intelligence Analyst |
   | **Backstory** | You are an environmental data analyst monitoring urban air quality in real time. You assess pollution levels and identify correlations between vehicle emissions and air quality degradation. |
   | **Goal** | For each district, retrieve current air quality data using the air quality tool and report the European AQI, key pollutant levels (PM2.5, NO2, O3), and any health or emissions advisories relevant to the current traffic situation. |
   | **LLM Model** | gpt-4o (Default) |

3. Under **Add Tools**, add the `air quality tool`.
4. Click **Save Agent**.

---

### Step 13 — Verify the agent order

In **Add Tasks**, confirm the pipeline order:
```
geocoding_agent
      ↓
traffic_flow_agent
weather_intelligence_agent
air_quality_agent
(agents 2-4 run in parallel under Manager Agent)
```

---

## Part 3 — Configure the TomTom API Key

### Step 14 — Enter UserParameters

The `road network tool` requires your TomTom API key. In Agent Studio, this is configured as a **UserParameter** at the workflow level — not hardcoded in the tool.

1. Click the **Configure** tab in the workflow editor.
2. Scroll down to **UserParameters** (or **Tool Configuration**).
3. Find the `road network tool` entry.
4. In the `api_key` field, paste your TomTom API key.
5. Click **Save**.

> **Security note:** UserParameters are stored securely in Agent Studio and are never exposed in the tool code or logs.

---

## Part 4 — Test the Workflow

### Step 15 — Navigate to the Test screen

1. Click the **Test** tab.

---

### Step 16 — Run a conversational query

In the input field, type a natural language query such as:

```
How is the traffic situation in the Marina District and Downtown right now?
```

Or try:
```
Give me a traffic briefing for Bur Dubai and Business Bay.
```

Click **Run** (or press Enter).

---

### Step 17 — Observe the parallel execution

Watch the task panel as the workflow runs:

1. **Geocoding Agent** — converts district names to coordinates (typically <5 seconds)
2. **Manager Agent** fans out to all three intelligence agents simultaneously:
   - **Traffic Flow Agent** — calls TomTom at 2 zoom levels per district
   - **Weather Intelligence Agent** — calls Open-Meteo weather API
   - **Air Quality Agent** — calls Open-Meteo air quality API
3. **Manager Agent** synthesises all three responses into a unified briefing

> **Typical runtime:** 15–30 seconds for 2 districts (parallel execution is much faster than sequential for multiple data sources).

---

### Step 18 — Review the output

A typical response looks like:

```
TRAFFICSENSE AI — DISTRICT BRIEFING
=====================================

📍 MARINA DISTRICT
Traffic: Moderate congestion — Arterial roads: 40 km/h (free flow: 49 km/h, 18.4% delay)
⚠️  ALERT: Road closure detected — monitor for diversion traffic build-up
Weather: Clear sky, 36.4°C — no weather impact on traffic flow
Air Quality: AQI 32 (Fair) — NO2 within normal range

📍 DOWNTOWN
Traffic: Moderate congestion — Arterial roads: 48 km/h (free flow: 59 km/h, 18.6% delay)
Weather: Clear sky, 36.4°C — no weather impact on traffic flow
Air Quality: AQI 28 (Good) — air quality satisfactory

OPERATOR SUMMARY
----------------
Both districts show ~18-19% travel time delay vs free-flow conditions.
Priority action: Marina District road closure requires monitoring for
knock-on congestion as diverted traffic redistributes.
```

---

### Step 19 — Try follow-up queries

Because **Conversational** mode is ON, you can continue the conversation:

```
What should operators do about the Marina closure?
```

```
Compare Marina and Downtown congestion levels.
```

```
Is the weather likely to worsen traffic in the next few hours?
```

The Manager Agent maintains conversation context across turns.

---

## Part 5 — Deploy the Workflow

### Step 20 — Deploy

1. Click the **Deploy** tab → **Deploy Workflow**.
2. Once deployed, the workflow accepts HTTP POST requests and can be integrated with city operations dashboards.

---

## Troubleshooting

| Issue | Likely cause | Fix |
|-------|-------------|-----|
| `TomTom API call failed` | API key not set or wrong | Go to Configure → UserParameters → enter your TomTom API key |
| `Quota exceeded` | Free tier (2,500 req/day) used up | Wait until the next UTC midnight for quota reset; or register a second key |
| `Location not found` from geocoding tool | District name too ambiguous | Add city/country context, e.g. "Marina, Dubai" instead of just "Marina" |
| Weather tool returns no data | Coordinates out of range | Verify geocoding output returned valid lat/lon values |
| All agents run sequentially (not in parallel) | Manager Agent is OFF | Go to Configure → set Manager Agent to ON |
| Conversation doesn't maintain context | Conversational is OFF | Go to Configure → set Conversational to ON |

---

## Files in This Lab

```
trafficsense-ai/
├── tools/
│   ├── geocoding tool.py         ← Tool 1: Nominatim geocoding (free, no key)
│   ├── road network tool.py      ← Tool 2: TomTom Traffic Flow (free key required)
│   ├── weather data tool.py      ← Tool 3: Open-Meteo weather (free, no key)
│   └── air quality tool.py       ← Tool 4: Open-Meteo air quality (free, no key)
├── requirements.txt
└── README.md                     ← This guide
```

---

## Key Learning Points

- **Parallel Fan-out pattern:** Manager Agent dispatches three intelligence agents simultaneously — critical for real-time applications where latency matters.
- **Conversational mode:** Enables multi-turn interactions; the agent maintains context across queries in the same session.
- **UserParameters:** Secrets like API keys are stored securely in Agent Studio — never hardcoded in tool files.
- **Multi-source synthesis:** The Manager Agent's LLM capability synthesises outputs from three independent data sources into a coherent, actionable briefing.
- **Free public APIs:** Open-Meteo weather and air quality are completely free and require no registration — only TomTom requires a (free) account.
- **Road closure operator logic:** When a closure is detected alongside low congestion, the tool correctly warns of emerging knock-on delays rather than falsely reporting normal flow.
