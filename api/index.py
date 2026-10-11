import json
from pathlib import Path

import numpy as np
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()

# Enable CORS for the assignment checker
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the dataset.
# This assumes q-vercel-latency.json is inside the api folder.
DATA_FILE = Path(__file__).resolve().parent / "q-vercel-latency.json"

with open(DATA_FILE, "r", encoding="utf-8") as f:
    DATA = json.load(f)


@app.get("/")
async def health_check():
    return {"status": "ok"}


@app.options("/api")
async def options_api():
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        },
    )


@app.post("/")
@app.post("/api")
async def calculate_metrics(request: Request):
    try:
        body = await request.json()

        regions = body.get("regions", [])
        threshold = float(body.get("threshold_ms", 180))

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
                    latency > threshold for latency in latencies
                ),
            }

        return result

    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid request or dataset format"},
        )
