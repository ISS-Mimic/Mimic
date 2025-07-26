"""
Pi.Screens package
Collects *all* Kivy Screen subclasses used by the Mimic GUI.

Each import is wrapped in a try/except so the package remains usable while you
migrate files incrementally from GUI.py into Pi/Screens/.
Delete the try/except once the module exists.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Core / navigation screens (already migrated)
# ---------------------------------------------------------------------------
from .mainscreen          import MainScreen
from .manualcontrol       import ManualControlScreen

# ---------------------------------------------------------------------------
# Simple “placeholder” screens you said you’ll migrate next
# ---------------------------------------------------------------------------
try:
    from .cdh_screen      import CDH_Screen
except ImportError:
    # still lives in GUI.py
    pass

try:
    from .led_screen      import LED_Screen
except ImportError:
    pass

try:
    from .playback_screen import Playback_Screen
except ImportError:
    pass

try:
    from .settings_screen import Settings_Screen
except ImportError:
    pass

try:
    from .mimic_screen    import MimicScreen
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Truss / telemetry / science screens  (add as you extract)
# ---------------------------------------------------------------------------
for _name in (
    "ISS_Screen",
    "Orbit_Screen", "Orbit_Pass", "Orbit_Data",
    "EPS_Screen",
    "CT_Screen", "CT_SASA_Screen", "CT_UHF_Screen",
    "CT_Camera_Screen", "CT_SGANT_Screen",
    "ECLSS_Screen", "ECLSS_WRM_Screen", "ECLSS_IATCS_Screen",
    "GNC_Screen", "TCS_Screen",
    "EVA_US_Screen", "EVA_RS_Screen", "EVA_Main_Screen",
    "EVA_Pictures",
    "RS_Screen", "RS_Dock_Screen",
    "Crew_Screen",
    "MSS_MT_Screen",
    "VV_Screen", "VV_Image",
    "Science_Screen", "Science_EXT_Screen",
    "Science_INT_Screen", "Science_NRAL_Screen", "Science_JEF_Screen",
    "USOS_Screen",
    "Robo_Screen", "SSRMS_Screen", "SPDM1_Screen",
):
    try:
        globals()[_name] = __import__(f".{_name.lower()}", globals(), locals(), [_name], 1).__dict__[_name]
    except (ImportError, KeyError):
        # Module or class not migrated yet
        pass

# ---------------------------------------------------------------------------
# Build __all__ from whatever successfully imported
# ---------------------------------------------------------------------------
__all__ = [name for name in (
    "MainScreen",
    "ManualControlScreen",
    "CDH_Screen",
    "LED_Screen",
    "Playback_Screen",
    "Settings_Screen",
    "MimicScreen",
    "ISS_Screen",
    "Orbit_Screen", "Orbit_Pass", "Orbit_Data",
    "EPS_Screen",
    "CT_Screen", "CT_SASA_Screen", "CT_UHF_Screen",
    "CT_Camera_Screen", "CT_SGANT_Screen",
    "ECLSS_Screen", "ECLSS_WRM_Screen", "ECLSS_IATCS_Screen",
    "GNC_Screen", "TCS_Screen",
    "EVA_US_Screen", "EVA_RS_Screen", "EVA_Main_Screen",
    "EVA_Pictures",
    "RS_Screen", "RS_Dock_Screen",
    "Crew_Screen",
    "MSS_MT_Screen",
    "VV_Screen", "VV_Image",
    "Science_Screen", "Science_EXT_Screen",
    "Science_INT_Screen", "Science_NRAL_Screen", "Science_JEF_Screen",
    "USOS_Screen",
    "Robo_Screen", "SSRMS_Screen", "SPDM1_Screen",
) if name in globals()]
