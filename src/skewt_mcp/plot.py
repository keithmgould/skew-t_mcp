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

    # Wind barbs — independent axes with matching log-P scale
    pos = skew.ax.get_position()
    ax_barbs = fig.add_axes([pos.x1 + 0.02, pos.y0, 0.08, pos.height])
    ax_barbs.set_yscale("log")
    ax_barbs.set_ylim(skew.ax.get_ylim())  # match skew-T exactly
    ax_barbs.yaxis.set_visible(False)
    ax_barbs.xaxis.set_visible(False)
    ax_barbs.set_xlim(-1.5, 1.5)
    ax_barbs.patch.set_visible(False)
    for spine in ax_barbs.spines.values():
        spine.set_visible(False)

    # Thin barbs using even spacing in log-pressure space
    p_mag = np.array([x.magnitude for x in p])
    # Only include levels within the plot range
    mask = (p_mag >= 200) & (p_mag <= 1050)
    valid_idx = np.where(mask)[0]
    
    log_p = np.log(p_mag)
    barb_idx = [valid_idx[0]]
    for i in valid_idx[1:]:
        if abs(log_p[i] - log_p[barb_idx[-1]]) >= 0.065:
            barb_idx.append(i)

    bp = p_mag[barb_idx]
    bu = np.array([u[i].magnitude for i in barb_idx])
    bv = np.array([v[i].magnitude for i in barb_idx])
    ax_barbs.barbs(
        np.zeros_like(bp), bp, bu, bv,
        length=6, clip_on=True, pivot="tip",
        linewidth=0.8,
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

    skew.ax.legend(loc="upper left", fontsize=9)

    # Encode to base64 PNG
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("ascii")
