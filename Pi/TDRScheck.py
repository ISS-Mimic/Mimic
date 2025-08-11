from os import environ
from twisted.internet.defer import inlineCallbacks
from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
import sqlite3
from utils.logger import log_info, log_error

# Database connection
conn = sqlite3.connect('/dev/shm/tdrs.db', isolation_level=None)
c = conn.cursor()


def update_active_tdrs(msg, tdrs_id, active_tdrs):
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
        log_error(f"Error in update_active_tdrs for TDRS-{tdrs_id}: {e}")
        return None


def update_database(active_tdrs, timestamp):
    """
    Updates the database with the active TDRS IDs and timestamp.

    :param active_tdrs: List of active TDRS IDs.
    :param timestamp: Timestamp to update.
    """
    try:
        log_info(f"Updating database with active TDRS: {active_tdrs}, timestamp: {timestamp}")
        c.execute("UPDATE tdrs SET TDRS1 = ?", (active_tdrs[0],))
        c.execute("UPDATE tdrs SET TDRS2 = ?", (active_tdrs[1],))
        c.execute("UPDATE tdrs SET Timestamp = ?", (timestamp,))
        conn.commit()
        log_info("Database updated successfully")
    except Exception as e:
        log_error(f"Error updating database: {e}")
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
                log_info(f"Received message: {type(msg)}")
                active_tdrs = [0, 0]
                timestamp = 0

                for tdrs_id in [12, 11, 10, 6, 7]:
                    ts = update_active_tdrs(msg, tdrs_id, active_tdrs)
                    if ts:
                        timestamp = ts

                log_info(f"Active TDRS: {active_tdrs}, Timestamp: {timestamp}")
                update_database(active_tdrs, timestamp)

            except Exception as e:
                log_error(f"Error processing TDRS status message: {e}")
                import traceback
                traceback.print_exc()

        log_info("Subscribing to TDRS activity channel")
        try:
            yield self.subscribe(onevent, u'gov.nasa.gsfc.scan_now.sn.activity')
            log_info("Successfully subscribed to TDRS activity channel")
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

        runner = ApplicationRunner(url, realm)
        log_info("Starting WAMP application runner")
        runner.run(Component)
        
    except Exception as e:
        log_error(f"Fatal error in TDRS check application: {e}")
        import traceback
        traceback.print_exc()
        exit(1)