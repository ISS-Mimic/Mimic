from __future__ import annotations

from pathlib import Path
import pathlib
import subprocess
from subprocess import Popen
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty
from kivy.lang import Builder
from kivy.app import App
import sqlite3
import time
from math import isfinite
from kivy.clock import Clock

from ._base import MimicBase                    # gives mimic_directory + signalcolor
from utils.logger import log_info, log_error
from utils.serial import serialWrite            # we'll keep using this, but ensure newline here

# -- load KV that sits next to this file -------------------------------------
kv_path = pathlib.Path(__file__).with_name("MimicScreen.kv")
Builder.load_file(str(kv_path))


class _ChangeGate:
    """
    Quantizes angles and only allows a send when something changed
    (or on heartbeat). Greatly reduces bandwidth at 9600 bps.
    """
    def __init__(self, angle_step: float = 0.1, heartbeat_s: float = 1.0):
        self.prev: dict[str, object] = {}
        self.angle_step = angle_step
        self.heartbeat_s = heartbeat_s
        self._last_sent = 0.0

    def _q(self, v):
        try:
            fv = float(v)
            if not isfinite(fv):
                return 0.0
            return round(fv / self.angle_step) * self.angle_step
        except Exception:
            return 0.0

    def _qi(self, v):
        try:
            return int(round(float(v)))
        except Exception:
            return 0

    def filter(self, now: float, vals: dict, leds: dict | None = None):
        """
        Returns (should_send: bool, q_vals: dict, q_leds: dict|None)
        """
        q_vals = {}
        for k, v in vals.items():
            # Angle-like signals get quantized; flags/ints passed through
            if k.endswith("ARJ") or k.endswith("RRJ") or (k and k[0] == "B"):
                q_vals[k] = self._q(v)
            else:
                q_vals[k] = v

        q_leds = {}
        if leds:
            for k, v in leds.items():
                q_leds[k] = "" if v is None else str(v)

        composite = {**q_vals, **q_leds}
        changed = any(self.prev.get(k) != composite[k] for k in composite)
        heartbeat_due = (now - self._last_sent) >= self.heartbeat_s

        if changed or heartbeat_due:
            self.prev = composite
            self._last_sent = now
            return True, q_vals, (q_leds if leds else None)
        return False, q_vals, (q_leds if leds else None)


class MimicScreen(MimicBase):
    log_info("MimicScreen loaded")
    """
    Live ISS telemetry hub.
    Starts / stops iss_telemetry.py and TDRScheck.py, toggled by a
    'Mimic' button in the GUI.
    Now includes optimized single-line, paced serial writes for Arduino at 9600 bps.
    """

    # ======= wire/throughput parameters (NO Arduino changes required) =======
    _BAUD = 9600
    _SAFETY = 0.15         # extra headroom on pacing
    _BASE_HZ = 5           # UI tick target; actual wire pacing enforces 9600
    _ANGLE_STEP = 0.1      # deg
    _HEARTBEAT_S = 1.0     # resend latest state once per second (recovery)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._mimic_active = False
        self._mimic_event = None         # dynamic schedule_once handle
        self._db_path = "/dev/shm/iss_telemetry.db"
        self._gate = _ChangeGate(angle_step=self._ANGLE_STEP, heartbeat_s=self._HEARTBEAT_S)
        
        # static mapping from Arduino tokens -> DB IDs
        self._telemetry_mapping = {
            'PSARJ': 'S0000004',      # psarj
            'SSARJ': 'S0000003',      # ssarj
            'PTRRJ': 'S0000002',      # ptrrj
            'STRRJ': 'S0000001',      # strrj
            'B1B': 'S6000008',        # beta1b
            'B1A': 'S4000007',        # beta1a
            'B2B': 'P6000008',        # beta2b
            'B2A': 'P4000007',        # beta2a
            'B3B': 'S6000007',        # beta3b
            'B3A': 'S4000008',        # beta3a
            'B4B': 'P6000007',        # beta4b
            'B4A': 'P4000008',        # beta4a
            'AOS': 'AOS',             # aos
            'V1A': 'S4000001',        # voltage_1a
            'V2A': 'P4000001',        # voltage_2a
            'V3A': 'S4000004',        # voltage_3a
            'V4A': 'P4000004',        # voltage_4a
            'V1B': 'S6000004',        # voltage_1b
            'V2B': 'P6000004',        # voltage_2b
            'V3B': 'S6000001',        # voltage_3b
            'V4B': 'P6000001',        # voltage_4b
            'Sgnt_el': 'Z1000014',    # sgant_elevation
            'Sgnt_xel': 'Z1000015',   # sgant_xel
            'Sgnt_xmit': 'Z1000013',  # kuband_transmit
            'SASA_Xmit': 'S1000009',  # sasa1_status
            'SASA_AZ': 'S1000004',    # sasa1_azimuth
            'SASA_EL': 'S1000005'     # sasa1_elevation
        }

        # prebuilt SQL
        ids = list(self._telemetry_mapping.values())
        placeholders = ",".join("?" for _ in ids)
        self._sql_select = f"SELECT ID, Value FROM telemetry WHERE ID IN ({placeholders})"
        self._sql_ids = ids

    # ------------------------------ helpers: writer/pacing/format ------------------------------

    def _write_line(self, line: str):
        """
        Ensure newline termination and call serialWrite once per update.
        serialWrite ultimately writes to all open ports (as in your code).
        """
        if not line.endswith("\n"):
            line = line + "\n"
        try:
            serialWrite(line)
        except Exception as e:
            log_error(f"serialWrite failed: {e}")

    @staticmethod
    def _line_bytes(line: str) -> int:
        # ASCII, plus newline already appended
        return len(line.encode("ascii", "ignore"))

    def _min_gap(self, n_bytes: int) -> float:
        """
        Compute the minimum on-the-wire time for this payload at 9600,
        assuming 10 bits/byte (start + 8 data + stop) plus safety margin.
        """
        bits = n_bytes * 10
        seconds = bits / self._BAUD
        return seconds * (1.0 + self._SAFETY)

    @staticmethod
    def _f(v, places: int = 1) -> str:
        try:
            return f"{float(v):.{places}f}"
        except Exception:
            return f"{0.0:.{places}f}"

    @staticmethod
    def _i(v) -> str:
        try:
            return str(int(round(float(v))))
        except Exception:
            return "0"

    def _build_packet(self, vals: dict, leds: dict | None) -> str:
        """
        Single space-separated KEY=VALUE line; Arduino reads with readStringUntil('\n').
        Include LED_* tokens only if present (other sketches may use them).
        """
        tokens = [
            f"PSARJ={self._f(vals.get('PSARJ'))}",
            f"SSARJ={self._f(vals.get('SSARJ'))}",
            f"PTRRJ={self._f(vals.get('PTRRJ'))}",
            f"STRRJ={self._f(vals.get('STRRJ'))}",
            f"B1B={self._f(vals.get('B1B'))}",
            f"B1A={self._f(vals.get('B1A'))}",
            f"B2B={self._f(vals.get('B2B'))}",
            f"B2A={self._f(vals.get('B2A'))}",
            f"B3B={self._f(vals.get('B3B'))}",
            f"B3A={self._f(vals.get('B3A'))}",
            f"B4B={self._f(vals.get('B4B'))}",
            f"B4A={self._f(vals.get('B4A'))}",
            f"AOS={self._i(vals.get('AOS'))}",
            f"V1A={self._f(vals.get('V1A'))}",
            f"V2A={self._f(vals.get('V2A'))}",
            f"V3A={self._f(vals.get('V3A'))}",
            f"V4A={self._f(vals.get('V4A'))}",
            f"V1B={self._f(vals.get('V1B'))}",
            f"V2B={self._f(vals.get('V2B'))}",
            f"V3B={self._f(vals.get('V3B'))}",
            f"V4B={self._f(vals.get('V4B'))}",
            f"Sgnt_el={self._f(vals.get('Sgnt_el'))}",
            f"Sgnt_xel={self._f(vals.get('Sgnt_xel'))}",
            f"Sgnt_xmit={self._i(vals.get('Sgnt_xmit'))}",
            f"SASA_Xmit={self._i(vals.get('SASA_Xmit'))}",
            f"SASA_AZ={self._f(vals.get('SASA_AZ'))}",
            f"SASA_EL={self._f(vals.get('SASA_EL'))}"
        ]

        # Add LED tokens if present
        if leds:
            for k, v in leds.items():
                if v is not None:
                    tokens.append(f"LED_{k}={v}")

        return " ".join(tokens)

    def _schedule_next(self, delay: float):
        """Schedule the next update tick."""
        if self._mimic_event:
            self._mimic_event.cancel()
        self._mimic_event = Clock.schedule_once(self._update, delay)

    def _update(self, dt):
        """Main update loop: read DB, filter, send if changed."""
        if not self._mimic_active:
            return

        try:
            # Read current values from database
            app = App.get_running_app()
            if not hasattr(app, "db_cursor"):
                log_error("No database cursor available")
                self._schedule_next(1.0 / self._BASE_HZ)
                return

            app.db_cursor.execute(self._sql_select, self._sql_ids)
            rows = app.db_cursor.fetchall()

            # Build current values dict
            vals = {}
            for row in rows:
                if len(row) >= 2:
                    vals[row[0]] = row[1]

            # Map DB IDs back to Arduino tokens
            reverse_mapping = {v: k for k, v in self._telemetry_mapping.items()}
            arduino_vals = {}
            for db_id, value in vals.items():
                if db_id in reverse_mapping:
                    arduino_vals[reverse_mapping[db_id]] = value

            # Get LED values (if any)
            leds = None
            if hasattr(app, 'led_values'):
                leds = app.led_values

            # Apply change gate filtering
            should_send, q_vals, q_leds = self._gate.filter(time.time(), arduino_vals, leds)

            if should_send:
                if q_leds is None:
                    q_leds = leds  # Use current LED values if gate returned None
                
                # Debug: Log what we're sending
                log_info(f"Mimic Screen: Sending - Vals: {q_vals}, LEDs: {q_leds}")
                
                # Show Arduino transmit animation (handled by GUI.py)
                # The transmit animation will be shown by GUI.py's updateArduinoCount method
                
                line = self._build_packet(q_vals, q_leds)
                # estimate wire time to pace the *next* tick safely at 9600
                nb = self._line_bytes(line + "\n")
                min_gap = self._min_gap(nb)
                self._write_line(line)
                # schedule the next tick as the larger of: pacing or base UI period
                self._schedule_next(max(min_gap, 1.0 / self._BASE_HZ))
            else:
                # nothing changed; schedule base UI period
                self._schedule_next(1.0 / self._BASE_HZ)

        except Exception as exc:
            log_error(f"Update loop failed: {exc}")
            self._schedule_next(1.0 / self._BASE_HZ)

    # ------------------------------ background procs (unchanged) ------------------------------

    def startproc(self) -> None:
        log_info(f"Start Proc")
        """
        Launches the collector scripts in the background.
        Keeps Popen handles on the App instance so MainScreen EXIT can kill them.
        """
        app  = App.get_running_app()
        base = Path(self.mimic_directory) / "Mimic" / "Pi"

        log_info("Starting telemetry subprocesses")

        iss_telemetry_path = base / "iss_telemetry.py"
        tdrscheck_path = base / "TDRScheck.py"
        vvcheck_path = base / "VVcheck.py"
        checkcrew_path = base / "checkCrew.py"

        if not iss_telemetry_path.exists():
            log_error(f"iss_telemetry.py not found at {iss_telemetry_path}")
            return
        if not tdrscheck_path.exists():
            log_error(f"TDRScheck.py not found at {tdrscheck_path}")
            return
        if not vvcheck_path.exists():
            log_error(f"VVcheck.py not found at {vvcheck_path}")
            return
        if not checkcrew_path.exists():
            log_error(f"checkCrew.py not found at {checkcrew_path}")
            return

        try:
            app.p = Popen(
                ["python", str(iss_telemetry_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            log_info(f"Started iss_telemetry.py (PID: {app.p.pid})")

            app.TDRSproc = Popen(
                ["python", str(tdrscheck_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            log_info(f"Started TDRScheck.py (PID: {app.TDRSproc.pid})")

            app.VVproc = Popen(
                ["python", str(vvcheck_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            log_info(f"Started VVcheck.py (PID: {app.VVproc.pid})")

            app.crewproc = Popen(
                ["python", str(checkcrew_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            log_info(f"Started checkCrew.py (PID: {app.crewproc.pid})")

            if app.p.poll() is not None:
                _, stderr = app.p.communicate()
                log_error(f"iss_telemetry.py failed to start: {stderr}")
                app.p = None

            if app.TDRSproc.poll() is not None:
                _, stderr = app.TDRSproc.communicate()
                log_error(f"TDRScheck.py failed to start: {stderr}")
                app.TDRSproc = None

            if app.VVproc.poll() is not None:
                _, stderr = app.VVproc.communicate()
                log_error(f"VVcheck.py failed to start: {stderr}")
                app.VVproc = None

            if app.crewproc.poll() is not None:
                _, stderr = app.crewproc.communicate()
                log_error(f"checkCrew.py failed to start: {stderr}")
                app.crewproc = None

        except Exception as exc:
            log_error(f"Failed to start subprocesses: {exc}")

    def killproc(self) -> None:
        log_info(f"Kill Proc")
        """
        Terminates all background processes.
        """
        app = App.get_running_app()

        for name in ("p", "TDRSproc", "VVproc", "crewproc"):
            proc = getattr(app, name, None)
            if not proc:
                continue
            try:
                proc.terminate(); proc.wait(timeout=3)
                log_info(f"{name} terminated.")
            except Exception as exc:
                log_error(f"Failed to kill {name}: {exc}")
            finally:
                setattr(app, name, None)

        app.mimicbutton = False

    def on_pre_leave(self):
        log_info("Leaving mimic screen")

    def on_enter(self):
        """Called when entering the screen."""
        pass
    
    def on_leave(self):
        """Called when leaving the screen."""
        # Get the screen manager to see where we're going
        app = App.get_running_app()
        screen_manager = app.root
        
        # Check if we're going to a main screen or a subscreen
        current_screen = screen_manager.current if screen_manager else None
        print(f"DEBUG: on_leave called, current_screen: {current_screen}")
        
        if current_screen is 'main':
            print(f"DEBUG: Going to main screen '{current_screen}', stopping transmission")
            # Stop mimic transmission and inform GUI.py
            if self._mimic_active:
                self._mimic_active = False
                if self._mimic_event:
                    self._mimic_event.cancel()
                    self._mimic_event = None
                
                # Inform GUI.py about transmission status
                if hasattr(app, 'set_mimic_transmission_status'):
                    app.set_mimic_transmission_status(False)
        else:
            print(f"DEBUG: Going to subscreen '{current_screen}', keeping transmission running")
            # Don't stop transmission for subscreens
    

    # ------------------------------ mimic button handlers ------------------------------

    def mimic_transmit(self, start: bool):
        """
        Toggle mimic transmission on/off.
        Called by the mimic button in the KV file.
        """
        if start:
            if not self._mimic_active:
                log_info("Starting mimic transmission")
                self._mimic_active = True
                
                # Inform GUI.py about transmission status
                app = App.get_running_app()
                if hasattr(app, 'set_mimic_transmission_status'):
                    app.set_mimic_transmission_status(True)
                
                self._update(0)  # Start immediately
        else:
            if self._mimic_active:
                log_info("Stopping mimic transmission")
                self._mimic_active = False
                
                # Inform GUI.py about transmission status
                app = App.get_running_app()
                if hasattr(app, 'set_mimic_transmission_status'):
                    app.set_mimic_transmission_status(False)
                
                if self._mimic_event:
                    self._mimic_event.cancel()
                    self._mimic_event = None
    

