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

    # Axis limits (set before barbs so they can match)
    skew.ax.set_ylim(1050, 200)
    skew.ax.set_xlim(-40, 50)

    # Wind barbs — one per major pressure level, interpolated from sounding data
    barb_levels = np.array([1000, 900, 800, 700, 600, 500, 400, 300, 200], dtype=float)
    p_mag = p.magnitude
    bu = np.interp(barb_levels, p_mag[::-1], np.array([x.magnitude for x in u])[::-1])
    bv = np.interp(barb_levels, p_mag[::-1], np.array([x.magnitude for x in v])[::-1])

    # Separate non-skewed axis for wind barbs
    pos = skew.ax.get_position()
    ax_barbs = fig.add_axes([pos.x1, pos.y0, 0.08, pos.height])
    ax_barbs.set_yscale("log")
    ax_barbs.set_ylim(1050, 200)
    ax_barbs.yaxis.set_visible(False)
    ax_barbs.xaxis.set_visible(False)
    ax_barbs.set_xlim(0, 1)
    ax_barbs.patch.set_visible(False)
    for spine in ax_barbs.spines.values():
        spine.set_visible(False)

    # Offset x per barb so the visual center stays aligned.
    # pivot="tip" anchors the tip at (x, y). The staff extends in the
    # wind-from direction, so positive u pushes the staff LEFT, negative
    # u pushes it RIGHT. Shift x to compensate.
    wind_angle = np.arctan2(-bu, -bv)  # direction wind comes FROM
    x_offset = -np.sin(wind_angle) * 0.18  # staff extends this way; counter it
    bx = 0.5 + x_offset

    ax_barbs.barbs(
        bx, barb_levels, bu, bv,
        length=6, clip_on=False, linewidth=0.8,
    )

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

    # Title
    title = (
        f"Skew-T Log-P — {sounding['model']} "
        f"({sounding['latitude']:.2f}, {sounding['longitude']:.2f}) — "
        f"Valid: {sounding['valid_time']} UTC"
    )
    skew.ax.set_title(title, fontsize=13, fontweight="bold", loc="left")

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

    skew.ax.legend(loc="upper left", fontsize=9)

    # Encode to base64 PNG
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("ascii")
