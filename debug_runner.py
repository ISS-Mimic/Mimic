import os
import runpy
import traceback


print("debug_runner: preparing to run GUI.py")
os.environ.setdefault("MIMIC_CONSOLE_LOGGING", "1")

try:
    runpy.run_path("Pi/GUI.py", run_name="__main__")
    print("debug_runner: run_path returned normally")
except SystemExit as exc:
    print("SystemExit:", exc)
except Exception:
    traceback.print_exc()

