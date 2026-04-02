"""Basic tests for skewt-mcp."""

import numpy as np
import pytest


def test_dewpoint_from_rh():
    """Test dewpoint calculation from temperature and RH."""
    from skewt_mcp.data import _dewpoint_from_rh

    # At 100% RH, dewpoint should equal temperature
    td = _dewpoint_from_rh(20.0, 100.0)
    assert abs(td - 20.0) < 0.5

    # At 50% RH and 20°C, dewpoint ~9.3°C
    td = _dewpoint_from_rh(20.0, 50.0)
    assert 8.0 < td < 11.0

    # At very low RH
    td = _dewpoint_from_rh(30.0, 10.0)
    assert td < 0.0


def test_compute_indices():
    """Test index computation with synthetic sounding data."""
    from skewt_mcp.indices import compute_indices

    # Create a simple unstable sounding
    pressure = np.array([1000, 925, 850, 700, 500, 300, 200], dtype=float)
    temperature = np.array([30, 22, 15, 2, -18, -45, -60], dtype=float)
    dewpoint = np.array([22, 18, 10, -5, -25, -50, -65], dtype=float)
    wind_speed = np.array([5, 10, 15, 25, 35, 40, 45], dtype=float)
    wind_direction = np.array([180, 190, 200, 220, 250, 270, 280], dtype=float)

    sounding = {
        "pressure": pressure,
        "temperature": temperature,
        "dewpoint": dewpoint,
        "wind_speed": wind_speed,
        "wind_direction": wind_direction,
    }

    indices = compute_indices(sounding)

    assert "cape" in indices
    assert "cin" in indices
    assert "lcl_pressure" in indices
    assert "precipitable_water_mm" in indices
    assert indices["cape"] >= 0
    assert indices["parcel_profile"] is not None


def test_format_indices_text():
    """Test text formatting of indices."""
    from skewt_mcp.indices import format_indices_text

    indices = {
        "cape": 1500.0,
        "cin": -50.0,
        "lcl_pressure": 920.0,
        "lcl_temperature": 18.0,
        "lcl_height_m": 800.0,
        "lfc_pressure": 850.0,
        "el_pressure": 250.0,
        "precipitable_water_mm": 35.0,
        "bulk_shear_0_6km_kt": 30.0,
    }

    text = format_indices_text(indices)
    assert "CAPE: 1500.0 J/kg" in text
    assert "CIN: -50.0 J/kg" in text
    assert "LCL: 920.0 hPa" in text
    assert "PWAT: 35.0 mm" in text


def test_server_tools_list():
    """Test that server exposes the expected tools."""
    import asyncio
    from skewt_mcp.server import list_tools

    tools = asyncio.run(list_tools())
    names = [t.name for t in tools]
    assert "get_skewt" in names
    assert "get_sounding_data" in names
