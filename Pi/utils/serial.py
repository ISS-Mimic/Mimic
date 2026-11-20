"""
Serial helper used by multiple screens.

The OPEN_SERIAL_PORTS list is still defined in GUI.py; we import it
dynamically so we *don’t* create a circular import at module-load time.
"""
import time, serial, os

from utils.logger import log_info, log_error

# serialWrite runs on the Kivy UI thread, so it must never block for long.
#
# pyserial 3.5 with write_timeout=0 ("non-blocking") does NOT return when the
# kernel TX buffer is full: os.write raises EAGAIN, pyserial swallows it and
# retries in a tight loop forever, freezing the GUI. That happens whenever an
# Arduino stops reading (reset, brown-out, firmware hang). So every port gets
# a short finite write timeout (GUI.py: SERIAL_WRITE_TIMEOUT), and we skip a
# port entirely while its output queue is backed up.
# Must exceed the wire time of the longest line we send: the Uno's USB-serial
# path only buffers ~64 bytes, so a ~200-byte telemetry line takes ~210 ms
# at 9600 bps and a shorter timeout cuts it off mid-line.
WRITE_TIMEOUT = 0.5          # seconds; worst-case block per port per write
MAX_OUT_WAITING = 512        # bytes queued before we consider the port stalled

RETRY_AFTER = 2.0            # seconds to skip a port after it stops accepting data

# port name -> monotonic time before which we don't try writing again.
# Not every driver reports out_waiting (ptys report 0), so a write timeout
# also marks the port stalled; one log line per stall, not per write.
_stalled_until = {}

def _open_ports():
    """Get serial ports from GUI module."""
    try:
        # Import GUI module to get OPEN_SERIAL_PORTS
        import GUI
        if hasattr(GUI, 'OPEN_SERIAL_PORTS'):
            return GUI.OPEN_SERIAL_PORTS
        return []
    except Exception as e:
        log_error(f"Could not get serial ports: {e}")
        return []

def _mark_stalled(s, reason: str) -> None:
    if s.port not in _stalled_until:
        log_error(f"Serial port {s.port} is not reading data ({reason}); "
                  f"skipping writes and retrying every {RETRY_AFTER:.0f}s")
    _stalled_until[s.port] = time.monotonic() + RETRY_AFTER

def _port_is_stalled(s) -> bool:
    """True if we should skip writing to this port right now."""
    until = _stalled_until.get(s.port)
    if until is not None and time.monotonic() < until:
        return True
    try:
        waiting = s.out_waiting
    except Exception:
        waiting = 0          # can't tell; the bounded write will decide
    if waiting > MAX_OUT_WAITING:
        _mark_stalled(s, f"{waiting} bytes queued")
        return True
    return False

def drain_input(ports=None) -> None:
    """
    Discard whatever the Arduinos have sent us.

    Nothing in Mimic reads serial input, but the sketches print continuously
    (~170 B/s). Once the Pi's ~4 KB receive buffer is full, the Uno's
    USB-serial chip stops accepting data from us too: writes stall, and at
    exit the kernel waits 30 s trying to send what's queued.
    """
    for s in list(ports if ports is not None else _open_ports()):
        try:
            if s.is_open:
                s.reset_input_buffer()
        except Exception:
            pass             # unplugged mid-call; the hot-plug handler cleans up

def close_ports(ports=None) -> None:
    """Discard pending I/O and close every port (fast exit, no 30 s drain)."""
    for s in list(ports if ports is not None else _open_ports()):
        try:
            s.reset_input_buffer()
            s.reset_output_buffer()
            s.close()
        except Exception:
            pass

def _mark_ok(s) -> None:
    if _stalled_until.pop(s.port, None) is not None:
        log_info(f"Serial port {s.port} is accepting data again")

def serialWrite(*args):
    """Writes the given bytes to every port in OPEN_SERIAL_PORTS."""
    msg = str(*args)
    log_info(f"serialWrite → {msg!r}")
    data = msg.encode()

    for s in list(_open_ports()):     # copy: hot-plug thread may modify the list
        if not s.is_open:
            log_error(f"Serial port {s.port} is not open.")
            continue
        if _port_is_stalled(s):
            continue
        try:
            s.reset_input_buffer()   # keep the receive side from backing up (see drain_input)
        except Exception:
            pass
        # Guard against ports opened with write_timeout=0 (see note above)
        if not s.write_timeout:
            s.write_timeout = WRITE_TIMEOUT
        try:
            s.write(data)
            _mark_ok(s)
        except serial.SerialTimeoutException:
            _mark_stalled(s, "write timed out")
        except (OSError, serial.SerialException) as e:
            log_error(f"Error writing to {s.port}: {e}")
