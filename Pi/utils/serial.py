"""
Serial helper used by multiple screens.

The OPEN_SERIAL_PORTS list is still defined in GUI.py; we import it
dynamically so we *don’t* create a circular import at module-load time.
"""
import importlib, time, serial, os, logging

log_info  = logging.getLogger("MyLogger").info
log_error = logging.getLogger("MyLogger").error

# Cache the GUI module to prevent reloading
_GUI_MODULE = None

def _open_ports():
    global _GUI_MODULE
    if _GUI_MODULE is None:
        _GUI_MODULE = importlib.import_module("GUI")
    return getattr(_GUI_MODULE, "OPEN_SERIAL_PORTS", [])

def serialWrite(*args):
    """Writes the given bytes to every port in OPEN_SERIAL_PORTS."""
    msg = str(*args)
    log_info(f"serialWrite → {msg!r}")

    for s in _open_ports():
        if not s.is_open:
            log_error(f"Serial port {s.port} is not open.")
            continue
        try:
            s.write(msg.encode())
        except (OSError, serial.SerialException) as e:
            if getattr(e, "errno", None) == 11:   # EAGAIN
                time.sleep(0.1)
                try:
                    s.write(msg.encode())
                except Exception as retry_error:
                    log_error(f"Retry failed on {s.port}: {retry_error}")
            else:
                log_error(f"Error writing to {s.port}: {e}")
