# skewt-mcp — MCP Server for Skew-T Diagrams

## What This Is

An MCP (Model Context Protocol) server that generates Skew-T Log-P diagrams from HRRR model data for any coordinates in the CONUS. Designed for pilots, paragliders, and weather nerds who use AI assistants.

## Architecture

- **Data Source:** NOAA HRRR model via Open-Meteo API (free, no key needed)
  - Open-Meteo serves HRRR pressure-level data: temperature, humidity, wind at multiple pressure levels
  - Fallback: GFS if HRRR unavailable
- **Rendering:** Python with MetPy + matplotlib
- **MCP Transport:** stdio (standard MCP protocol)
- **Language:** Python (MetPy is Python-only)

## MCP Tools to Expose

### 1. `get_skewt`
Generate a Skew-T diagram for given coordinates and time.

**Parameters:**
- `latitude` (float, required) — Latitude in decimal degrees
- `longitude` (float, required) — Longitude in decimal degrees  
- `forecast_hour` (int, optional, default: current nearest hour) — Hour in local time (0-23)
- `date` (string, optional, default: today) — Date in YYYY-MM-DD format
- `model` (string, optional, default: "hrrr") — Weather model: "hrrr" or "gfs"

**Returns:**
- PNG image (base64 encoded) of the Skew-T diagram
- Key indices as text: CAPE, CIN, LCL pressure/height, LFC, EL, precipitable water
- Wind shear summary

### 2. `get_sounding_data`
Get raw sounding data (no image) for programmatic use.

**Parameters:** Same as get_skewt

**Returns:**
- JSON with pressure levels, temperatures, dewpoints, wind speed/direction
- Computed indices (CAPE, CIN, LCL, etc.)

## Data Flow

1. MCP client calls `get_skewt` with lat/lon/time
2. Server fetches pressure-level data from Open-Meteo API:
   - Levels: 1000, 975, 950, 925, 900, 850, 800, 750, 700, 650, 600, 550, 500, 450, 400, 350, 300, 250, 200 hPa
   - Variables per level: temperature, relative_humidity, windspeed, winddirection
   - Also: surface pressure, 2m temp, 2m RH, 10m wind
3. Compute dewpoints from T + RH
4. Render Skew-T using MetPy's SkewT class
5. Calculate indices (CAPE, CIN, LCL, etc.) using MetPy
6. Return base64 PNG + text summary

## Skew-T Rendering Details

The diagram should include:
- Temperature profile (red line)
- Dewpoint profile (green line) 
- Parcel path (black dashed)
- Wind barbs on right side
- CAPE shading (red, semi-transparent)
- CIN shading (blue, semi-transparent)
- Dry adiabats (thin, light)
- Moist adiabats (thin, light)
- Mixing ratio lines (thin, light)
- Title with location, model, valid time
- Key indices in text box on diagram

## Package Structure

```
skewt-mcp/
├── README.md
├── pyproject.toml          # Package config, entry point
├── src/
│   └── skewt_mcp/
│       ├── __init__.py
│       ├── server.py       # MCP server (stdio transport)
│       ├── data.py         # Open-Meteo data fetching
│       ├── plot.py         # Skew-T rendering with MetPy
│       └── indices.py      # Meteorological calculations
└── tests/
    └── test_basic.py
```

## MCP Server Setup

Use the `mcp` Python SDK (`pip install mcp`). Example pattern:

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server

server = Server("skewt-mcp")

@server.tool()
async def get_skewt(latitude: float, longitude: float, ...):
    ...
```

## Installation (for users)

```bash
# Install
pip install skewt-mcp
# Or from source
git clone https://github.com/keithmgould/skewt-mcp
cd skewt-mcp && pip install -e .

# Configure in MCP client (e.g. Claude Desktop)
# Add to claude_desktop_config.json:
{
  "mcpServers": {
    "skewt": {
      "command": "python",
      "args": ["-m", "skewt_mcp"]
    }
  }
}
```

## Dependencies

- `mcp` — MCP Python SDK
- `metpy` — Meteorological calculations + Skew-T plotting
- `matplotlib` — Rendering
- `numpy` — Array operations
- `httpx` or `urllib` — HTTP client for Open-Meteo API

## Open Source

- License: MIT
- Repo: github.com/keithmgould/skewt-mcp (or a new org)
