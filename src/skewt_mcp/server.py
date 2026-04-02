"""MCP server for Skew-T diagram generation."""

from __future__ import annotations

import asyncio
import json

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, ImageContent, Tool

from skewt_mcp.data import fetch_sounding
from skewt_mcp.indices import compute_indices, format_indices_text
from skewt_mcp.plot import render_skewt

server = Server("skewt-mcp")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_skewt",
            description=(
                "Generate a Skew-T Log-P diagram for given coordinates and time. "
                "Returns a PNG image and key thermodynamic indices (CAPE, CIN, LCL, LFC, EL, PWAT)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "latitude": {
                        "type": "number",
                        "description": "Latitude in decimal degrees",
                    },
                    "longitude": {
                        "type": "number",
                        "description": "Longitude in decimal degrees",
                    },
                    "forecast_hour": {
                        "type": "integer",
                        "description": "Hour in UTC (0-23). Defaults to current hour.",
                    },
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format. Defaults to today.",
                    },
                    "model": {
                        "type": "string",
                        "description": "Weather model. 'hrrr' (default, best for CONUS/US), 'gfs' (global), or 'ecmwf' (global, European model).",
                        "enum": ["hrrr", "gfs", "ecmwf"],
                    },
                },
                "required": ["latitude", "longitude"],
            },
        ),
        Tool(
            name="get_sounding_data",
            description=(
                "Get raw sounding data (no image) for programmatic use. "
                "Returns JSON with pressure levels, temperatures, dewpoints, wind, and computed indices."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "latitude": {
                        "type": "number",
                        "description": "Latitude in decimal degrees",
                    },
                    "longitude": {
                        "type": "number",
                        "description": "Longitude in decimal degrees",
                    },
                    "forecast_hour": {
                        "type": "integer",
                        "description": "Hour in UTC (0-23). Defaults to current hour.",
                    },
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format. Defaults to today.",
                    },
                    "model": {
                        "type": "string",
                        "description": "Weather model. 'hrrr' (default, best for CONUS/US), 'gfs' (global), or 'ecmwf' (global, European model).",
                        "enum": ["hrrr", "gfs", "ecmwf"],
                    },
                },
                "required": ["latitude", "longitude"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent | ImageContent]:
    lat = arguments["latitude"]
    lon = arguments["longitude"]
    forecast_hour = arguments.get("forecast_hour")
    date = arguments.get("date")
    model = arguments.get("model", "hrrr")

    try:
        sounding = await fetch_sounding(lat, lon, date=date, forecast_hour=forecast_hour, model=model)
    except Exception as e:
        # If HRRR fails and was requested, try GFS fallback
        if model == "hrrr":
            try:
                sounding = await fetch_sounding(lat, lon, date=date, forecast_hour=forecast_hour, model="gfs")
                sounding["model"] = "GFS (HRRR fallback)"
            except Exception as e2:
                return [TextContent(type="text", text=f"Error fetching data: {e2}")]
        else:
            return [TextContent(type="text", text=f"Error fetching data: {e}")]

    indices = compute_indices(sounding)

    if name == "get_skewt":
        png_b64 = render_skewt(sounding, indices)
        summary = format_indices_text(indices)
        return [
            ImageContent(type="image", data=png_b64, mimeType="image/png"),
            TextContent(type="text", text=summary),
        ]
    elif name == "get_sounding_data":
        result = {
            "latitude": sounding["latitude"],
            "longitude": sounding["longitude"],
            "model": sounding["model"],
            "valid_time": sounding["valid_time"],
            "pressure_hPa": sounding["pressure"].tolist(),
            "temperature_C": sounding["temperature"].tolist(),
            "dewpoint_C": sounding["dewpoint"].tolist(),
            "wind_speed_kt": sounding["wind_speed"].tolist(),
            "wind_direction_deg": sounding["wind_direction"].tolist(),
            "indices": {k: v for k, v in indices.items() if k != "parcel_profile"},
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


def main():
    """Entry point for the MCP server."""
    asyncio.run(_run())


async def _run():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    main()
