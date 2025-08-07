from os import environ
from twisted.internet.defer import inlineCallbacks
from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
import sqlite3

# Database connection - cross-platform path handling
import os
from pathlib import Path

# Try Pi path first, then Windows path
tdrs_db_path = Path('/dev/shm/tdrs.db')
if not tdrs_db_path.parent.exists():
    tdrs_db_path = Path.home() / '.mimic_data' / 'tdrs.db'
    tdrs_db_path.parent.mkdir(exist_ok=True)

conn = sqlite3.connect(str(tdrs_db_path), isolation_level=None)
c = conn.cursor()

# Initialize database if it doesn't exist
c.execute("CREATE TABLE IF NOT EXISTS tdrs (TDRS1 TEXT, TDRS2 TEXT, Timestamp TEXT)")
c.execute("INSERT OR IGNORE INTO tdrs VALUES(?, ?, ?)", ('0', '0', '0'))
conn.commit()


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
    #print(active_tdrs)
    c.execute("UPDATE tdrs SET TDRS1 = ?", (active_tdrs[0],))
    c.execute("UPDATE tdrs SET TDRS2 = ?", (active_tdrs[1],))
    c.execute("UPDATE tdrs SET Timestamp = ?", (timestamp,))


class Component(ApplicationSession):
    @inlineCallbacks
    def onJoin(self, details):
        """Handles joining the WAMP session."""

        def onevent(msg):
            """Processes incoming messages and updates the database."""
            active_tdrs = [0, 0]
            timestamp = 0

            for tdrs_id in [12, 11, 10, 6, 7]:
                ts = update_active_tdrs(msg, tdrs_id, active_tdrs)
                if ts:
                    timestamp = ts

            #print(f"Active TDRS: {active_tdrs}, Timestamp: {timestamp}")
            update_database(active_tdrs, timestamp)

        yield self.subscribe(onevent, u'gov.nasa.gsfc.scan_now.sn.activity')


if __name__ == '__main__':
    import six

    # Updated URL with port 8443
    url = environ.get("AUTOBAHN_DEMO_ROUTER", u"wss://scan-now.gsfc.nasa.gov:8443/messages")
    if six.PY2 and isinstance(url, six.binary_type):
        url = url.decode('utf8')
    realm = u"sn_now"

    runner = ApplicationRunner(url, realm)
    runner.run(Component)
