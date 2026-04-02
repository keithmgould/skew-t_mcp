# skewt-mcp

An MCP (Model Context Protocol) server that generates **Skew-T Log-P diagrams** from HRRR model data for any coordinates in the CONUS. Designed for pilots, paragliders, and weather nerds who use AI assistants.

## Features

- **Skew-T diagrams** with temperature, dewpoint, parcel path, wind barbs, CAPE/CIN shading, dry/moist adiabats, and mixing ratio lines
- **Computed indices**: CAPE, CIN, LCL, LFC, EL, precipitable water, 0-6 km bulk shear
- **Data source**: NOAA HRRR via Open-Meteo API (free, no API key needed), with GFS fallback
- **MCP transport**: stdio — works with Claude Desktop and any MCP client

## Installation

```bash
pip install skewt-mcp
```

Or from source:

```bash
git clone https://github.com/keithmgould/skewt-mcp
cd skewt-mcp
pip install -e .
```

## MCP Client Configuration

Add to your Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "skewt": {
      "command": "python",
      "args": ["-m", "skewt_mcp"]
    }
  }
}
```

## Tools

### `get_skewt`

Generate a Skew-T Log-P diagram for given coordinates and time.

**Parameters:**
- `latitude` (float, required) — Latitude in decimal degrees
- `longitude` (float, required) — Longitude in decimal degrees
- `forecast_hour` (int, optional) — Hour in UTC (0-23), defaults to current hour
- `date` (string, optional) — Date in YYYY-MM-DD format, defaults to today
- `model` (string, optional) — `"hrrr"` or `"gfs"`, defaults to `"hrrr"`

**Returns:** PNG image (base64) + text summary of indices

### `get_sounding_data`

Get raw sounding data as JSON for programmatic use. Same parameters as `get_skewt`.

**Returns:** JSON with pressure levels, temperatures, dewpoints, wind, and computed indices

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT
