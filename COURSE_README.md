# Cloudera Agent Studio — Hands-On Labs

**Course:** DSCI-275 · Agentic AI with Cloudera Agent Studio  
**Organization:** Cloudera Education  
**Maintainer:** Sanket Mote (sanketmote05@gmail.com)

---

## Repository Contents

This repository contains the tool code and step-by-step lab guides for two Hands-On Labs (HOLs) in the DSCI-275 course. Each lab demonstrates a different agentic workflow pattern using Cloudera Agent Studio.

```
hol-repo/
├── cliniqai/                 ← Lab 1: CliniqAI (Healthcare)
│   ├── tools/
│   │   ├── csv reader tool.py
│   │   └── fda drug api tool.py
│   ├── data/
│   │   └── patients.csv
│   ├── requirements.txt
│   └── README.md             ← Step-by-step lab guide
│
├── trafficsense-ai/          ← Lab 2: TrafficSense AI (Smart City)
│   ├── tools/
│   │   ├── geocoding tool.py
│   │   ├── road network tool.py
│   │   ├── weather data tool.py
│   │   └── air quality tool.py
│   ├── requirements.txt
│   └── README.md             ← Step-by-step lab guide
│
└── README.md                 ← This file
```

---

## Lab 1 — CliniqAI

**Pattern:** Sequential Pipeline  
**Domain:** Healthcare  
**Agents:** 5 (no Manager Agent, not Conversational)

CliniqAI reads a patient CSV file, enriches records with live FDA adverse-event data for each medication, generates structured clinical assessments, and writes a PDF summary report.

**APIs used:**
- FDA OpenFDA Drug Adverse Events — free, no key required
- Cloudera built-in "Write to Shared PDF" tool

**→ [Start Lab 1](cliniqai/README.md)**

---

## Lab 2 — TrafficSense AI

**Pattern:** Parallel Fan-out  
**Domain:** Smart City / Urban Mobility  
**Agents:** 4 (Manager Agent ON, Conversational ON)

TrafficSense AI accepts natural language queries about city districts and fans out parallel agents to gather live traffic flow, weather, and air quality data, then synthesises a unified operator briefing.

**APIs used:**
- TomTom Traffic Flow v4 — free tier (2,500 req/day), **API key required**
- Open-Meteo Weather — free, no key
- Open-Meteo Air Quality — free, no key
- Nominatim/OpenStreetMap Geocoding — free, no key

**Prerequisite:** Register for a free TomTom API key at [developer.tomtom.com](https://developer.tomtom.com/user/register) before starting Lab 2.

**→ [Start Lab 2](trafficsense-ai/README.md)**

---

## Important: Tool Naming Convention

> **Cloudera Agent Studio requires tool names to use spaces, not underscores.**

All tool files in this repository are named with spaces (e.g. `csv reader tool.py`, `road network tool.py`) to match the names you will enter in Agent Studio. This is intentional.

When creating a tool in Agent Studio, enter the name exactly as the file is named — with spaces.

---

## Agentic Workflow Patterns

| Pattern | When to use | Example |
|---------|------------|---------|
| **Sequential Pipeline** | Each step depends on the previous step's output | CliniqAI — load CSV → enrich with FDA data → assess → report |
| **Parallel Fan-out** | Multiple independent data sources queried simultaneously | TrafficSense — traffic + weather + air quality in parallel |
| **Conversational + Manager** | Multi-turn dialogue; complex orchestration | TrafficSense — operator chatbot with context |

---

## Getting Started

1. Clone or download this repository.
2. Open the lab guide for the lab you are starting (`cliniqai/README.md` or `trafficsense-ai/README.md`).
3. Follow the numbered steps. Each step corresponds to a UI action in Cloudera Agent Studio.
4. Copy tool code from the `tools/` directory into Agent Studio as directed by the guide.

No local Python environment is needed — all code runs inside Cloudera Agent Studio.

---

## Support

For issues with Cloudera Agent Studio, contact your instructor or the Cloudera Education support team.

For TomTom API issues, see [developer.tomtom.com/support](https://developer.tomtom.com/support).
