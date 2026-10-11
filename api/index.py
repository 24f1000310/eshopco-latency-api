import json
from pathlib import Path

import numpy as np
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Access-Control-Allow-Origin"],
)

# Load the dataset
# q-vercel-latency.json must be inside the api folder,
# alongside index.py.
DATA_FILE = Path(__file__).resolve().parent / "q-vercel-latency.json"

with open(DATA_FILE, "r", encoding="utf-8") as file:
    DATA = json.load(file)


@app.get("/")
async def health_check():
    return {"status": "ok"}


@app.post("/")
@app.post("/api")
async def calculate_metrics(request: Request):
    try:
        body = await request.json()

        if not isinstance(body, dict):
            return JSONResponse(
                status_code=400,
                content={"error": "Request body must be a JSON object"},
            )

        regions = body.get("regions", [])
        threshold = float(body.get("threshold_ms", 180))

        if not isinstance(regions, list):
            return JSONResponse(
                status_code=400,
                content={"error": "'regions' must be a list"},
            )

        result = {}

        for region in regions:
            rows = [
                row for row in DATA
                if row["region"] == region
            ]

            if not rows:
                result[region] = {
                    "avg_latency": 0,
                    "p95_latency": 0,
                    "avg_uptime": 0,
                    "breaches": 0,
                }
                continue

            latencies = [
                float(row["latency_ms"]) for row in rows
            ]

            uptimes = [
                float(row["uptime_pct"]) for row in rows
            ]

            result[region] = {
                "avg_latency": float(np.mean(latencies)),
                "p95_latency": float(np.percentile(latencies, 95)),
                "avg_uptime": float(np.mean(uptimes)),
                "breaches": sum(
                    latency > threshold
                    for latency in latencies
                ),
            }

        return result

    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid request or dataset format"},
        )


@app.options("/api")
@app.options("/")
async def options_handler():
    return JSONResponse(
        content={"status": "ok"},
    )
