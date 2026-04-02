# skewt-mcp

MCP server that generates Skew-T Log-P diagrams from weather model data (HRRR, GFS, ECMWF) via the Open-Meteo API. Built for pilots, paragliders, and weather enthusiasts using AI assistants.

## Project Structure

```
src/skewt_mcp/
  server.py    # MCP server: tool registration, request handling, stdio transport
  data.py      # Async data fetching from Open-Meteo API, dewpoint computation
  indices.py   # Thermodynamic index calculations (CAPE, CIN, LCL, etc.) via MetPy
  plot.py      # Skew-T diagram rendering with MetPy/matplotlib, returns base64 PNG
  __init__.py  # Exports main()
  __main__.py  # python -m entry point
tests/
  test_basic.py
```

## Tech Stack

- Python 3.10+, built with Hatchling
- Key deps: mcp (≥1.0), metpy (≥1.5), matplotlib, numpy, httpx
- Testing: pytest

## Commands

- Install: `pip install -e ".[dev]"`
- Run: `python -m skewt_mcp`
- Test: `pytest`

## MCP Tools Exposed

1. **get_skewt** - Returns Skew-T diagram PNG (base64) + text summary
2. **get_sounding_data** - Returns raw JSON sounding data + indices

Both accept: latitude, longitude, forecast_hour, date, model

## Key Patterns

- Async I/O throughout (httpx for API calls)
- HRRR → GFS automatic fallback on error
- MetPy units library for dimensional consistency
- 19 pressure levels (1000–200 hPa)
- Wind barbs rendered on separate log-P axis alongside the Skew-T chart
