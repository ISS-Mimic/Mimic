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
from .main                import MainScreen
from .manualcontrol       import ManualControlScreen

#from .playback_screen     import Playback_Screen
#from .iss_screen          import ISS_Screen
#from .settings_screen     import Settings_Screen
#from .mimic_screen        import MimicScreen
#from .rs_dock_screen      import RS_Dock_Screen

from .cdh_screen.py				import CDH_Screen
from .crew_screen.py			import Crew_Screen
from .ct_camera_screen.py		import CT_Camera_Screen
from .ct_sasa_screen.py			import CT_SASA_Screen
from .ct_screen.py				import CT_Screen
from .ct_sgant_screen.py		import CT_SGANT_Screen
from .ct_uhf_screen.py			import CT_UHF_Screen
from .eclss_iatcs_screen.py		import ECLSS_IATCS_Screen
from .eclss_screen.py			import ECLSS_Screen
from .eclss_wrm_screen.py		import ECLSS_WRM_Screen
from .eps_screen.py				import EPS_Screen
from .eva_emu_screen.py			import EVA_EMU_Screen
from .eva_main_screen.py		import EVA_Main_Screen
from .eva_pictures.py			import EVA_Pictures
from .eva_rs_screen.py			import EVA_RS_Screen
from .eva_us_screen.py			import EVA_US_Screen
from .gnc_screen.py				import GNC_Screen
from .led_screen.py				import LED_Screen
from .mss_mt_screen.py			import MSS_MT_Screen
from .orbit_data.py				import Orbit_Data
from .orbit_pass.py				import Orbit_Pass
from .orbit_screen.py			import Orbit_Screen
from .robo_screen.py			import Robo_Screen
from .rs_screen.py				import RS_Screen
from .science_ext_screen.py		import Science_EXT_Screen
from .science_int_screen.py		import Science_INT_Screen
from .science_jef_screen.py		import Science_JEF_Screen
from .science_nral_screen.py	import Science_NRAL_Screen
from .science_screen.py			import Science_Screen
from .spdm_screen.py			import SPDM_Screen
from .ssrms_screen.py			import SSRMS_Screen
from .tcs_screen.py				import TCS_Screen
from .usos_screen.py			import USOS_Screen
from .vv_image.py				import VV_Image
from .vv_screen.py				import VV_Screen
