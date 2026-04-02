"""Render Skew-T Log-P diagrams using MetPy and matplotlib."""

from __future__ import annotations

import base64
import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import metpy.calc as mpcalc
import numpy as np
from metpy.plots import SkewT
from metpy.units import units


def render_skewt(sounding: dict, indices: dict) -> str:
    """Render a Skew-T diagram and return base64-encoded PNG.

    Args:
        sounding: Dict from data.fetch_sounding
        indices: Dict from indices.compute_indices

    Returns:
        Base64-encoded PNG string
    """
    p = sounding["pressure"] * units.hPa
    T = sounding["temperature"] * units.degC
    Td = sounding["dewpoint"] * units.degC
    ws = sounding["wind_speed"] * units.knots
    wd = sounding["wind_direction"] * units.degrees
    prof = indices["parcel_profile"]

    u, v = mpcalc.wind_components(ws, wd)

    fig = plt.figure(figsize=(10, 10))
    skew = SkewT(fig, rotation=45)

    # Plot temperature and dewpoint profiles
    skew.plot(p, T, "r", linewidth=2, label="Temperature")
    skew.plot(p, Td, "g", linewidth=2, label="Dewpoint")

    # Parcel path
    skew.plot(p, prof, "k--", linewidth=1.5, label="Parcel")

    # Wind barbs — fixed column just outside the right edge of the plot
    skew.plot_barbs(p, u, v, xloc=1.05, length=6)

    # CAPE / CIN shading
    try:
        skew.shade_cape(p, T, prof, alpha=0.3)
    except Exception:
        pass
    try:
        skew.shade_cin(p, T, prof, alpha=0.3)
    except Exception:
        pass

    # Background lines
    skew.plot_dry_adiabats(linewidth=0.5, alpha=0.4)
    skew.plot_moist_adiabats(linewidth=0.5, alpha=0.4)
    skew.plot_mixing_lines(linewidth=0.5, alpha=0.4)

    # Axis limits
    skew.ax.set_ylim(1050, 200)
    skew.ax.set_xlim(-40, 50)

    # Title
    title = (
        f"Skew-T Log-P — {sounding['model']} "
        f"({sounding['latitude']:.2f}, {sounding['longitude']:.2f})\n"
        f"Valid: {sounding['valid_time']} UTC"
    )
    plt.title(title, fontsize=13, fontweight="bold", loc="left")

    # Indices text box
    from skewt_mcp.indices import format_indices_text
    text = format_indices_text(indices)
    skew.ax.text(
        0.02, 0.02, text,
        transform=skew.ax.transAxes,
        fontsize=8,
        verticalalignment="bottom",
        fontfamily="monospace",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="white", alpha=0.85, edgecolor="gray"),
    )

    plt.legend(loc="upper left", fontsize=9)
    plt.tight_layout()

    # Encode to base64 PNG
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("ascii")
