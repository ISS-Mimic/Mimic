"""
Pi.Screens package
Collects all Kivy Screen subclasses.

Add or remove imports as you migrate files.  Keep names in __all__ so
`from Screens import FooScreen` works everywhere.
"""

from __future__ import annotations

# ── core screens (already migrated) ─────────────────────────────────────────
from .main                import MainScreen
from .manualcontrol       import ManualControlScreen

# ── simple / placeholder screens ────────────────────────────────────────────
from .cdh_screen          import CDH_Screen
from .crew_screen         import Crew_Screen
from .ct_camera_screen    import CT_Camera_Screen
from .ct_sasa_screen      import CT_SASA_Screen
from .ct_screen           import CT_Screen
from .ct_sgant_screen     import CT_SGANT_Screen
from .ct_uhf_screen       import CT_UHF_Screen
from .eclss_iatcs_screen  import ECLSS_IATCS_Screen
from .eclss_screen        import ECLSS_Screen
from .eclss_wrm_screen    import ECLSS_WRM_Screen
from .eps_screen          import EPS_Screen
from .eva_emu_screen      import EVA_EMU_Screen
from .eva_main_screen     import EVA_Main_Screen
from .eva_pictures        import EVA_Pictures
from .eva_rs_screen       import EVA_RS_Screen
from .eva_us_screen       import EVA_US_Screen
from .gnc_screen          import GNC_Screen
from .led_screen          import LED_Screen
from .mss_mt_screen       import MSS_MT_Screen
from .orbit_data          import Orbit_Data
from .orbit_pass          import Orbit_Pass
from .orbit_screen        import Orbit_Screen
from .robo_screen         import Robo_Screen
from .rs_screen           import RS_Screen
from .science_ext_screen  import Science_EXT_Screen
from .science_int_screen  import Science_INT_Screen
from .science_jef_screen  import Science_JEF_Screen
from .science_nral_screen import Science_NRAL_Screen
from .science_screen      import Science_Screen
from .spdm_screen         import SPDM_Screen
from .ssrms_screen        import SSRMS_Screen
from .tcs_screen          import TCS_Screen
from .usos_screen         import USOS_Screen
from .vv_image            import VV_Image
from .vv_screen           import VV_Screen

# ── build __all__ so “from Screens import …” works everywhere ───────────────
__all__ = [
    # core
    "MainScreen", "ManualControlScreen",
    # placeholders (add/remove as needed)
    "CDH_Screen", "Crew_Screen", "CT_Camera_Screen", "CT_SASA_Screen",
    "CT_Screen", "CT_SGANT_Screen", "CT_UHF_Screen",
    "ECLSS_IATCS_Screen", "ECLSS_Screen", "ECLSS_WRM_Screen",
    "EPS_Screen", "EVA_EMU_Screen", "EVA_Main_Screen", "EVA_Pictures",
    "EVA_RS_Screen", "EVA_US_Screen", "GNC_Screen", "LED_Screen",
    "MSS_MT_Screen", "Orbit_Data", "Orbit_Pass", "Orbit_Screen",
    "Robo_Screen", "RS_Screen", "Science_EXT_Screen", "Science_INT_Screen",
    "Science_JEF_Screen", "Science_NRAL_Screen", "Science_Screen",
    "SPDM_Screen", "SSRMS_Screen", "TCS_Screen", "USOS_Screen",
    "VV_Image", "VV_Screen",
]
