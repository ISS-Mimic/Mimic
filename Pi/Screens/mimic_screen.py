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
from utils.serial import serialWrite            # we’ll keep using this, but ensure newline here

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
            f"B1A={self._f(vals.get('B1A'))}",
            f"B1B={self._f(vals.get('B1B'))}",
            f"B2A={self._f(vals.get('B2A'))}",
            f"B2B={self._f(vals.get('B2B'))}",
            f"B3A={self._f(vals.get('B3A'))}",
            f"B3B={self._f(vals.get('B3B'))}",
            f"B4A={self._f(vals.get('B4A'))}",
            f"B4B={self._f(vals.get('B4B'))}",
            f"AOS={self._i(vals.get('AOS', 0))}",
            # keep these available for other Arduinos that use them
            f"Sgnt_el={self._f(vals.get('Sgnt_el'))}",
            f"Sgnt_xel={self._f(vals.get('Sgnt_xel'))}",
            f"Sgnt_xmit={self._i(vals.get('Sgnt_xmit', 0))}",
            f"SASA_Xmit={self._i(vals.get('SASA_Xmit', 0))}",
            f"SASA_AZ={self._f(vals.get('SASA_AZ'))}",
            f"SASA_EL={self._f(vals.get('SASA_EL'))}",
        ]
        if leds:
            # include only when present/changed
            for k in ("LED_1A", "LED_1B", "LED_2A", "LED_2B", "LED_3A", "LED_3B", "LED_4A", "LED_4B"):
                if k in leds:
                    tokens.append(f"{k}={leds[k]}")
        return " ".join(tokens)

    # ------------------------------ UI binding ------------------------------

    def mimic_transmit(self, value: bool) -> None:
        """
        Bound in KV.  True → transmit; False → idle.
        """
        App.get_running_app().mimicbutton = bool(value)  # keep UI truthful
        if value:
            self.start_mimic_telemetry()
        else:
            self.stop_mimic_telemetry()
        log_info(f"Start Mimic Telemetry: {value}")

    def start_mimic_telemetry(self):
        """Start mimic telemetry transmission (non-blocking, paced)."""
        try:
            if self._mimic_active:
                log_info("Mimic telemetry already active")
                return

            if not Path(self._db_path).exists():
                log_error(f"Telemetry database not found: {self._db_path}")
                return

            self._mimic_active = True
            # kick off dynamic schedule loop immediately (no fixed-interval Clock)
            self._schedule_next(0.0)
            log_info("Mimic telemetry started")

        except Exception as exc:
            log_error(f"Failed to start mimic telemetry: {exc}")

    def stop_mimic_telemetry(self):
        """Stop mimic telemetry transmission."""
        try:
            if not self._mimic_active:
                return

            self._mimic_active = False

            if self._mimic_event is not None:
                self._mimic_event.cancel()
                self._mimic_event = None

            # single-line RESET; Arduino readStringUntil('\n') expects newline
            self._write_line("RESET")
            App.get_running_app().mimicbutton = False
            log_info("Mimic telemetry stopped")

        except Exception as exc:
            log_error(f"Failed to stop mimic telemetry: {exc}")

    # ------------------------------ DB read & LED logic ------------------------------

    def _read_vals_from_db(self) -> dict:
        """
        Lightweight fresh read each tick (or as often as you like).
        """
        vals = {}
        try:
            conn = sqlite3.connect(self._db_path)
            cur = conn.cursor()
            cur.execute(self._sql_select, self._sql_ids)
            for db_id, value in cur.fetchall():
                for token, wanted in self._telemetry_mapping.items():
                    if db_id == wanted:
                        vals[token] = value
                        break
            conn.close()
        except Exception as exc:
            log_error(f"DB read failed: {exc}")

        # defaults to avoid KeyError in packet build
        for k in ('PSARJ','SSARJ','PTRRJ','STRRJ',
                  'B1A','B1B','B2A','B2B','B3A','B3B','B4A','B4B',
                  'AOS','Sgnt_el','Sgnt_xel','Sgnt_xmit','SASA_Xmit','SASA_AZ','SASA_EL'):
            vals.setdefault(k, 0)

        return vals

    def _get_voltage_color(self, voltage):
        if float(voltage) < 151.5:
            return "Blue"      # Discharging
        elif float(voltage) < 160.0:
            return "Yellow"    # Charging
        else:
            return "White"     # Fully charged

    def _compute_leds(self, vals: dict) -> dict:
        """
        Derive LED_* tokens from voltages. Returned as strings (e.g., 'Blue').
        We only add them to the packet when they changed (via ChangeGate).
        """
        leds = {}
        try:
            leds["LED_1A"] = self._get_voltage_color(vals.get("V1A", 0))
            leds["LED_1B"] = self._get_voltage_color(vals.get("V1B", 0))
            leds["LED_2A"] = self._get_voltage_color(vals.get("V2A", 0))
            leds["LED_2B"] = self._get_voltage_color(vals.get("V2B", 0))
            leds["LED_3A"] = self._get_voltage_color(vals.get("V3A", 0))
            leds["LED_3B"] = self._get_voltage_color(vals.get("V3B", 0))
            leds["LED_4A"] = self._get_voltage_color(vals.get("V4A", 0))
            leds["LED_4B"] = self._get_voltage_color(vals.get("V4B", 0))
        except Exception as exc:
            log_error(f"LED compute failed: {exc}")
        return leds

    # ------------------------------ dynamic pacing loop ------------------------------

    def _schedule_next(self, delay: float):
        # cancel old event if any and schedule next one-shot tick
        if self._mimic_event is not None:
            self._mimic_event.cancel()
        self._mimic_event = Clock.schedule_once(self._tick, max(0.0, delay))

    def _tick(self, _dt):
        if not self._mimic_active:
            return

        # 1) read current values
        vals = self._read_vals_from_db()
        leds = self._compute_leds(vals)

        # 2) change gating
        now = time.monotonic()
        should_send, q_vals, q_leds = self._gate.filter(now, vals, leds)

        # 3) build & send single line (with newline)
        if should_send:
            # Ensure we have valid LED values (not None)
            if q_leds is None:
                q_leds = leds  # Use current LED values if gate returned None
            
            # Debug: Log what we're sending
            log_info(f"Mimic Screen: Sending - Vals: {q_vals}, LEDs: {q_leds}")
            
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
            log_error(f"Failed to start telemetry procs: {exc}")
            app.p = app.TDRSproc = app.VVproc = app.crewproc = None

    def killproc(self, *_):
        """
        Stops helper processes and flips mimicbutton → False.
        Runs when EXIT is pressed or when ScreenManager leaves MimicScreen.
        """
        app = App.get_running_app()

        try:
            if hasattr(app, "db_cursor"):
                app.db_cursor.execute(
                    "INSERT OR IGNORE INTO telemetry "
                    "VALUES('Lightstreamer', '0', 'Unsubscribed', '0', 0)"
                )
        except Exception as exc:
            log_error(f"DB write failed: {exc}")

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

    def on_leave(self):
        pass
