from os import environ
from pathlib import Path
import time
from twisted.internet.defer import inlineCallbacks
from twisted.internet.task import LoopingCall
from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
import sqlite3
from utils.logger import log_info, log_error

# Every TDRS that can relay for the ISS. Only the first two found connected are
# stored (TDRS1/TDRS2 columns); screens without art for one still show its label.
TDRS_IDS = [12, 11, 10, 13, 6, 7, 8]

# SCAN Now publishes every ~3 s. If nothing arrives for this long the feed is
# down, so clear the active TDRS instead of showing the last one forever (#695).
STALE_AFTER_S = 30

def _db_path(db_name: str) -> str:
    """Same location rules as GUI.py / database_initialize.py."""
    shm_dir = Path('/dev/shm')
    if shm_dir.is_dir():
        return str(shm_dir / db_name)
    data_dir = Path.home() / '.mimic_data'
    data_dir.mkdir(parents=True, exist_ok=True)
    return str(data_dir / db_name)

# Database connection
conn = sqlite3.connect(_db_path('tdrs.db'), isolation_level=None)
c = conn.cursor()


def update_active_tdrs(msg, tdrs_id, active_tdrs):
    """
    Updates the ActiveTDRS list based on the provided message and TDRS ID.

    :param msg: The incoming message with TDRS data.
    :param tdrs_id: The TDRS ID to check.
    :param active_tdrs: The current list of active TDRS IDs.
    :return: Updated timestamp if found, otherwise None.
    """
    tdrs_key = f'TDRS-{tdrs_id}'
    tdrs_data = msg.get(tdrs_key, {}).get('connected', {}).get('ISS')
    if tdrs_data:
        timestamp = tdrs_data.get('Time_Tag', 0)
        if active_tdrs[0] == 0:
            active_tdrs[0] = tdrs_id
        elif active_tdrs[1] == 0:
            active_tdrs[1] = tdrs_id
        return timestamp
    return None


def update_database(active_tdrs, timestamp):
    """
    Updates the database with the active TDRS IDs and timestamp.

    :param active_tdrs: List of active TDRS IDs.
    :param timestamp: Timestamp to update.
    """
    try:
        #log_info(f"Updating database with active TDRS: {active_tdrs}, timestamp: {timestamp}")
        c.execute("UPDATE tdrs SET TDRS1 = ?", (active_tdrs[0],))
        c.execute("UPDATE tdrs SET TDRS2 = ?", (active_tdrs[1],))
        c.execute("UPDATE tdrs SET Timestamp = ?", (timestamp,))
        conn.commit()
        #log_info("Database updated successfully")
    except Exception as e:
        log_error(f"Error updating database: {e}")
        raise


def clear_active_tdrs(reason: str) -> None:
    """Mark no TDRS as active (feed stale, disconnected or shutting down)."""
    try:
        update_database([0, 0], 0)
        log_info(f"Cleared active TDRS: {reason}")
    except Exception:
        pass  # update_database already logged it


class Component(ApplicationSession):
    _last_msg = None
    _cleared = False
    _watchdog = None

    def _check_stale(self):
        if self._cleared:
            return
        if self._last_msg is None or time.monotonic() - self._last_msg > STALE_AFTER_S:
            clear_active_tdrs(f"no SCAN Now data for {STALE_AFTER_S}s")
            self._cleared = True

    def onLeave(self, details):
        clear_active_tdrs(f"left WAMP session ({details.reason})")
        if self._watchdog and self._watchdog.running:
            self._watchdog.stop()
        super().onLeave(details)

    @inlineCallbacks
    def onJoin(self, details):
        """Handles joining the WAMP session."""
        log_info(f"Successfully joined WAMP session")
        self._last_msg = time.monotonic()
        self._watchdog = LoopingCall(self._check_stale)
        self._watchdog.start(5, now=False)

        def onevent(msg):
            """Processes incoming messages and updates the database."""
            try:
                #log_info(f"Received TDRS message")
                active_tdrs = [0, 0]
                timestamp = 0

                for tdrs_id in TDRS_IDS:
                    ts = update_active_tdrs(msg, tdrs_id, active_tdrs)
                    if ts:
                        timestamp = ts

                #log_info(f"Active TDRS: {active_tdrs}, Timestamp: {timestamp}")
                update_database(active_tdrs, timestamp)
                self._last_msg = time.monotonic()
                self._cleared = False

            except Exception as e:
                log_error(f"Error processing TDRS status message: {e}", exc_info=True)

        #log_info("Subscribing to TDRS activity channel")
        yield self.subscribe(onevent, u'gov.nasa.gsfc.scan_now.sn.activity')
        #log_info("Successfully subscribed to TDRS activity channel")


if __name__ == '__main__':
    try:
        log_info("Starting TDRS check application")
        # Updated URL with port 8443
        url = environ.get("AUTOBAHN_DEMO_ROUTER", "wss://scan-now.gsfc.nasa.gov:8443/messages")
        realm = u"sn_now"
        
        log_info(f"Connecting to WAMP router: {url}")
        log_info(f"WAMP realm: {realm}")

        runner = ApplicationRunner(url, realm)
        log_info("Starting WAMP application runner")
        try:
            runner.run(Component)
        finally:
            # Connection lost or SIGTERM from the GUI: don't leave a stale TDRS behind
            clear_active_tdrs("TDRScheck exiting")
        
    except Exception as e:
        log_error(f"Fatal error in TDRS check application: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
