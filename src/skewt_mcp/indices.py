"""Compute meteorological sounding indices using MetPy."""

from __future__ import annotations

import numpy as np
import metpy.calc as mpcalc
from metpy.units import units


def compute_indices(sounding: dict) -> dict:
    """Compute thermodynamic indices from sounding data.

    Returns dict with CAPE, CIN, LCL, LFC, EL, precipitable water, and wind shear.
    """
    p = sounding["pressure"] * units.hPa
    T = sounding["temperature"] * units.degC
    Td = sounding["dewpoint"] * units.degC
    ws = sounding["wind_speed"] * units.knots
    wd = sounding["wind_direction"] * units.degrees

    # Wind components
    u, v = mpcalc.wind_components(ws, wd)

    # Surface-based parcel
    prof = mpcalc.parcel_profile(p, T[0], Td[0]).to("degC")

    # CAPE / CIN
    try:
        cape, cin = mpcalc.cape_cin(p, T, Td, prof)
        cape_val = cape.magnitude
        cin_val = cin.magnitude
    except Exception:
        cape_val = 0.0
        cin_val = 0.0

    # LCL
    try:
        lcl_p, lcl_t = mpcalc.lcl(p[0], T[0], Td[0])
        lcl_p_val = lcl_p.magnitude
        lcl_t_val = lcl_t.magnitude
    except Exception:
        lcl_p_val = None
        lcl_t_val = None

    # LFC
    try:
        lfc_p, lfc_t = mpcalc.lfc(p, T, Td)
        lfc_p_val = lfc_p.magnitude
    except Exception:
        lfc_p_val = None

    # EL
    try:
        el_p, el_t = mpcalc.el(p, T, Td)
        el_p_val = el_p.magnitude
    except Exception:
        el_p_val = None

    # Precipitable water
    try:
        pw = mpcalc.precipitable_water(p, Td)
        pw_val = pw.to("mm").magnitude
    except Exception:
        pw_val = None

    # Bulk wind shear 0-6 km (approximate using pressure levels)
    try:
        # Find levels near surface and ~500 hPa (~5.5 km)
        u_shear, v_shear = mpcalc.bulk_shear(p, u, v, depth=6000 * units.meter)
        shear_mag = np.sqrt(u_shear**2 + v_shear**2).to("knots").magnitude
    except Exception:
        shear_mag = None

    # LCL height in meters AGL (approximate)
    lcl_height_m = None
    if lcl_p_val is not None:
        try:
            sfc_p = p[0]
            lcl_height_m = float(mpcalc.pressure_to_height_std(lcl_p).to("meter").magnitude
                                 - mpcalc.pressure_to_height_std(sfc_p).to("meter").magnitude)
        except Exception:
            pass

    return {
        "cape": round(cape_val, 1),
        "cin": round(cin_val, 1),
        "lcl_pressure": round(lcl_p_val, 1) if lcl_p_val is not None else None,
        "lcl_temperature": round(lcl_t_val, 1) if lcl_t_val is not None else None,
        "lcl_height_m": round(lcl_height_m, 0) if lcl_height_m is not None else None,
        "lfc_pressure": round(lfc_p_val, 1) if lfc_p_val is not None else None,
        "el_pressure": round(el_p_val, 1) if el_p_val is not None else None,
        "precipitable_water_mm": round(pw_val, 1) if pw_val is not None else None,
        "bulk_shear_0_6km_kt": round(shear_mag, 1) if shear_mag is not None else None,
        "parcel_profile": prof,
    }


def format_indices_text(indices: dict) -> str:
    """Format indices as a human-readable text summary."""
    lines = []
    lines.append(f"CAPE: {indices['cape']} J/kg")
    lines.append(f"CIN: {indices['cin']} J/kg")
    if indices["lcl_pressure"] is not None:
        lcl_h = f" ({int(indices['lcl_height_m'])} m AGL)" if indices["lcl_height_m"] is not None else ""
        lines.append(f"LCL: {indices['lcl_pressure']} hPa{lcl_h}")
    if indices["lfc_pressure"] is not None:
        lines.append(f"LFC: {indices['lfc_pressure']} hPa")
    else:
        lines.append("LFC: N/A")
    if indices["el_pressure"] is not None:
        lines.append(f"EL: {indices['el_pressure']} hPa")
    else:
        lines.append("EL: N/A")
    if indices["precipitable_water_mm"] is not None:
        lines.append(f"PWAT: {indices['precipitable_water_mm']} mm")
    if indices["bulk_shear_0_6km_kt"] is not None:
        lines.append(f"0-6 km Shear: {indices['bulk_shear_0_6km_kt']} kt")
    return "\n".join(lines)
