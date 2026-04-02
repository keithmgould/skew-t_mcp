"""Fetch pressure-level sounding data from Open-Meteo API."""

from __future__ import annotations

import httpx
import numpy as np
from datetime import datetime, timezone

PRESSURE_LEVELS = [
    1000, 975, 950, 925, 900, 850, 800, 750, 700,
    650, 600, 550, 500, 450, 400, 350, 300, 250, 200,
]

OPEN_METEO_BASE = "https://api.open-meteo.com/v1"


def _build_pressure_vars(levels: list[int]) -> list[str]:
    """Build the list of pressure-level variable names for the API."""
    variables = []
    for level in levels:
        variables.extend([
            f"temperature_{level}hPa",
            f"relative_humidity_{level}hPa",
            f"wind_speed_{level}hPa",
            f"wind_direction_{level}hPa",
        ])
    return variables


async def fetch_sounding(
    latitude: float,
    longitude: float,
    date: str | None = None,
    forecast_hour: int | None = None,
    model: str = "hrrr",
) -> dict:
    """Fetch sounding data from Open-Meteo.

    Returns a dict with keys:
        pressure: np.ndarray (hPa)
        temperature: np.ndarray (°C)
        dewpoint: np.ndarray (°C)
        wind_speed: np.ndarray (knots)
        wind_direction: np.ndarray (degrees)
        valid_time: str
        model: str
        latitude: float
        longitude: float
        surface_pressure: float (hPa)
    """
    now = datetime.now(timezone.utc)
    if date is None:
        date = now.strftime("%Y-%m-%d")

    pressure_vars = _build_pressure_vars(PRESSURE_LEVELS)

    # Choose API endpoint based on model
    # - "hrrr" (default): Open-Meteo's best-available blend (includes HRRR for CONUS)
    # - "gfs": GFS global model
    # - "ecmwf": ECMWF IFS global model
    MODEL_ENDPOINTS = {
        "hrrr": f"{OPEN_METEO_BASE}/forecast",
        "gfs": f"{OPEN_METEO_BASE}/gfs",
        "ecmwf": f"{OPEN_METEO_BASE}/ecmwf",
    }
    endpoint = MODEL_ENDPOINTS.get(model, MODEL_ENDPOINTS["hrrr"])
    model_params = {}

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ",".join(pressure_vars + [
            "temperature_2m",
            "relative_humidity_2m",
            "wind_speed_10m",
            "wind_direction_10m",
            "surface_pressure",
        ]),
        "start_date": date,
        "end_date": date,
        "timezone": "UTC",
        **model_params,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(endpoint, params=params)
        resp.raise_for_status()
        data = resp.json()

    hourly = data["hourly"]
    times = hourly["time"]

    # Pick the requested hour (UTC) or nearest to current hour
    if forecast_hour is not None:
        target_idx = min(forecast_hour, len(times) - 1)
    else:
        current_hour = now.hour
        target_idx = min(current_hour, len(times) - 1)

    valid_time = times[target_idx]

    # Extract profiles
    temperatures = []
    dewpoints = []
    wind_speeds = []
    wind_directions = []
    valid_pressures = []

    for level in PRESSURE_LEVELS:
        t = hourly.get(f"temperature_{level}hPa")
        rh = hourly.get(f"relative_humidity_{level}hPa")
        ws = hourly.get(f"wind_speed_{level}hPa")
        wd = hourly.get(f"wind_direction_{level}hPa")

        if t is None or rh is None:
            continue

        t_val = t[target_idx]
        rh_val = rh[target_idx]
        ws_val = ws[target_idx] if ws else 0
        wd_val = wd[target_idx] if wd else 0

        if t_val is None or rh_val is None:
            continue

        # Compute dewpoint from T and RH using Magnus formula
        td = _dewpoint_from_rh(t_val, rh_val)

        valid_pressures.append(level)
        temperatures.append(t_val)
        dewpoints.append(td)
        # Open-Meteo gives wind speed in km/h, convert to knots
        wind_speeds.append((ws_val or 0) * 0.539957)
        wind_directions.append(wd_val or 0)

    # Surface data
    sfc_pressure = hourly.get("surface_pressure", [1013.25])[target_idx] or 1013.25

    return {
        "pressure": np.array(valid_pressures, dtype=float),
        "temperature": np.array(temperatures, dtype=float),
        "dewpoint": np.array(dewpoints, dtype=float),
        "wind_speed": np.array(wind_speeds, dtype=float),
        "wind_direction": np.array(wind_directions, dtype=float),
        "valid_time": valid_time,
        "model": model.upper(),
        "latitude": data.get("latitude", latitude),
        "longitude": data.get("longitude", longitude),
        "surface_pressure": sfc_pressure,
    }


def _dewpoint_from_rh(temp_c: float, rh: float) -> float:
    """Compute dewpoint from temperature (°C) and relative humidity (%).

    Uses the Magnus formula.
    """
    if rh <= 0:
        rh = 0.1
    a = 17.27
    b = 237.7
    gamma = (a * temp_c) / (b + temp_c) + np.log(rh / 100.0)
    return (b * gamma) / (a - gamma)
