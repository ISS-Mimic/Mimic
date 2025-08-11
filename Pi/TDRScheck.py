from os import environ
from twisted.internet.defer import inlineCallbacks
from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
from twisted.internet import reactor
import sqlite3
from utils.logger import log_info, log_error

# Database connection - cross-platform path handling
import os
from pathlib import Path

log_info("Starting TDRS check script")

# Try Pi path first, then Windows path
tdrs_db_path = Path('/dev/shm/tdrs.db')
if not tdrs_db_path.parent.exists():
    log_info("SHM path not available, using fallback path")
    tdrs_db_path = Path.home() / '.mimic_data' / 'tdrs.db'
    tdrs_db_path.parent.mkdir(exist_ok=True)
    log_info(f"Created fallback directory: {tdrs_db_path.parent}")

log_info(f"TDRS database path: {tdrs_db_path}")

def initialize_database():
    """Initialize the TDRS database table."""
    try:
        log_info("Initializing TDRS database table")
        conn = sqlite3.connect(str(tdrs_db_path), isolation_level=None)
        c = conn.cursor()
        
        c.execute("CREATE TABLE IF NOT EXISTS tdrs (TDRS1 TEXT, TDRS2 TEXT, Timestamp TEXT)")
        c.execute("INSERT OR IGNORE INTO tdrs VALUES(?, ?, ?)", ('0', '0', '0'))
        conn.commit()
        conn.close()
        log_info("TDRS database initialized successfully")
        
    except sqlite3.Error as e:
        log_error(f"SQLite error during database initialization: {e}")
        raise
    except Exception as e:
        log_error(f"Unexpected error during database initialization: {e}")
        raise

# Initialize the database at startup
initialize_database()


def update_active_tdrs(msg, tdrs_id, active_tdrs):
    log_info(f"Updating active TDRS for TDRS-{tdrs_id}")
    """
    Updates the ActiveTDRS list based on the provided message and TDRS ID.

    :param msg: The incoming message with TDRS data.
    :param tdrs_id: The TDRS ID to check.
    :param active_tdrs: The current list of active TDRS IDs.
    :return: Updated timestamp if found, otherwise None.
    """
    try:
        tdrs_key = f'TDRS-{tdrs_id}'
        tdrs_data = msg.get(tdrs_key, {}).get('connected', {}).get('ISS')
        
        if tdrs_data:
            timestamp = tdrs_data.get('Time_Tag', 0)
            log_info(f"TDRS-{tdrs_id} is connected to ISS with timestamp: {timestamp}")
            
            if active_tdrs[0] == 0:
                active_tdrs[0] = tdrs_id
                log_info(f"TDRS-{tdrs_id} assigned to slot 1")
            elif active_tdrs[1] == 0:
                active_tdrs[1] = tdrs_id
                log_info(f"TDRS-{tdrs_id} assigned to slot 2")
            else:
                log_info(f"TDRS-{tdrs_id} is connected but no available slots")
            
            return timestamp
        else:
            log_info(f"TDRS-{tdrs_id} is not connected to ISS")
            return None
            
    except Exception as e:
        log_error(f"Error updating active TDRS for TDRS-{tdrs_id}: {e}")
        return None


def update_database(active_tdrs, timestamp):
    log_info(f"Updating database with active TDRS: {active_tdrs}, timestamp: {timestamp}")
    """
    Updates the database with the active TDRS IDs and timestamp.

    :param active_tdrs: List of active TDRS IDs.
    :param timestamp: Timestamp to update.
    """
    try:
        log_info(f"Updating database with active TDRS: {active_tdrs}, timestamp: {timestamp}")
        
        conn = sqlite3.connect(str(tdrs_db_path), isolation_level=None)
        c = conn.cursor()
        
        c.execute("UPDATE tdrs SET TDRS1 = ?", (active_tdrs[0],))
        c.execute("UPDATE tdrs SET TDRS2 = ?", (active_tdrs[1],))
        c.execute("UPDATE tdrs SET Timestamp = ?", (timestamp,))
        
        conn.commit()
        conn.close()
        log_info("Database updated successfully")
        
    except sqlite3.Error as e:
        log_error(f"SQLite error updating database: {e}")
        raise
    except Exception as e:
        log_error(f"Unexpected error updating database: {e}")
        raise


class Component(ApplicationSession):
    def onConnect(self):
        """Called when the client connects to the WAMP router."""
        log_info("Connected to WAMP router")
        
    def onDisconnect(self):
        """Called when the client disconnects from the WAMP router."""
        log_info("Disconnected from WAMP router")
        
    def onConnectFailure(self, reason):
        """Called when the connection to the WAMP router fails."""
        log_error(f"Failed to connect to WAMP router: {reason}")
        
    @inlineCallbacks
    def onJoin(self, details):
        """Handles joining the WAMP session."""
        log_info(f"Successfully joined WAMP session: {details}")

        def onevent(msg):
            """Processes incoming messages and updates the database."""
            try:
                log_info(f"Received message: {type(msg)} - {msg}")
                log_info("Processing incoming TDRS status message")
                active_tdrs = [0, 0]
                timestamp = 0

                for tdrs_id in [12, 11, 10, 6, 7]:
                    ts = update_active_tdrs(msg, tdrs_id, active_tdrs)
                    if ts:
                        timestamp = ts

                log_info(f"Active TDRS summary: {active_tdrs}, Timestamp: {timestamp}")
                
                # Only update database if we have meaningful data
                if active_tdrs != [0, 0] or timestamp != 0:
                    update_database(active_tdrs, timestamp)
                else:
                    log_info("No active TDRS data to update in database")
                
            except Exception as e:
                log_error(f"Error processing TDRS status message: {e}")
                import traceback
                traceback.print_exc()

        log_info("Subscribing to TDRS activity channel")
        try:
            yield self.subscribe(onevent, u'gov.nasa.gsfc.scan_now.sn.activity')
            log_info("Successfully subscribed to TDRS activity channel")
            
            # Set up periodic status check
            def status_check():
                log_info("TDRS check script is running and monitoring for messages...")
                reactor.callLater(60, status_check)  # Check every 60 seconds
            
            reactor.callLater(10, status_check)  # Start first check after 10 seconds
            
        except Exception as e:
            log_error(f"Failed to subscribe to TDRS activity channel: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    try:
        import six
        log_info("Starting TDRS check application")

        # Updated URL with port 8443
        url = environ.get("AUTOBAHN_DEMO_ROUTER", u"wss://scan-now.gsfc.nasa.gov:8443/messages")
        if six.PY2 and isinstance(url, six.binary_type):
            url = url.decode('utf8')
        realm = u"sn_now"
        
        log_info(f"Connecting to WAMP router: {url}")
        log_info(f"WAMP realm: {realm}")

        # Add connection timeout
        runner = ApplicationRunner(url, realm)
        log_info("Starting WAMP application runner")
        
        # Set a timeout for the connection
        def connection_timeout():
            log_error("Connection timeout - WAMP router not responding")
            reactor.stop()
        
        reactor.callLater(30, connection_timeout)  # 30 second timeout
        
        runner.run(Component)
        
    except Exception as e:
        log_error(f"Fatal error in TDRS check application: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
