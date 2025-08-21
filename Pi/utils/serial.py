"""
Serial helper used by multiple screens.

The OPEN_SERIAL_PORTS list is still defined in GUI.py; we import it
dynamically so we *don’t* create a circular import at module-load time.
"""
import time, serial, os, logging

log_info  = logging.getLogger("MyLogger").info
log_error = logging.getLogger("MyLogger").error

def _open_ports():
    """Get serial ports from the running app instead of importing GUI."""
    try:
        from kivy.app import App
        app = App.get_running_app()
        if app and hasattr(app, 'OPEN_SERIAL_PORTS'):
            return app.OPEN_SERIAL_PORTS
        return []
    except Exception as e:
        log_error(f"Could not get serial ports: {e}")
        return []

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
