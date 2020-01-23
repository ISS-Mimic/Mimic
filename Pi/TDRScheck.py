from os import environ
from twisted.internet.defer import inlineCallbacks
from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
import sqlite3
# or: from autobahn.asyncio.wamp import ApplicationSession

conn = sqlite3.connect('/dev/shm/tdrs.db')
conn.isolation_level = None
c = conn.cursor()

class Component(ApplicationSession):
    @inlineCallbacks
    def onJoin(self, details):
        # listening for the corresponding message from the "backend"
        # (any session that .publish()es to this topic).
        def onevent(msg):
            ActiveTDRS = [0,0]
            Timestamp = 0
            try:
                msg['TDRS-12']['connected']['ISS']
            except Exception:
                pass
            else:
                Timestamp = msg['TDRS-12']['connected']['ISS']['Time_Tag']
                if ActiveTDRS[0] == 0:
                    ActiveTDRS[0] = 12
                elif ActiveTDRS[0] > 0:
                    ActiveTDRS[1] = 12
                else:
                    ActiveTDRS[0] = 0

            try:
                msg['TDRS-11']['connected']['ISS']
            except Exception:
                pass
            else:
                Timestamp = msg['TDRS-11']['connected']['ISS']['Time_Tag']
                if ActiveTDRS[0] == 0:
                    ActiveTDRS[0] = 11
                elif ActiveTDRS[0] > 0:
                    ActiveTDRS[1] = 11
                else:
                    ActiveTDRS[0] = 0

            try:
                msg['TDRS-10']['connected']['ISS']
            except Exception:
                pass
            else:
                Timestamp = msg['TDRS-10']['connected']['ISS']['Time_Tag']
                if ActiveTDRS[0] == 0:
                    ActiveTDRS[0] = 10
                elif ActiveTDRS[0] > 0:
                    ActiveTDRS[1] = 10
                else:
                    ActiveTDRS[0] = 0

            try:
                Timestamp = msg['TDRS-6']['connected']['ISS']['Time_Tag']
                msg['TDRS-6']['connected']['ISS']
            except Exception:
                pass
            else:
                if ActiveTDRS[0] == 0:
                    ActiveTDRS[0] = 6
                elif ActiveTDRS[0] > 0:
                    ActiveTDRS[1] = 6
                else:
                    ActiveTDRS[0] = 0
            
            try:
                msg['TDRS-7']['connected']['ISS']
            except Exception:
                pass
            else:
                Timestamp = msg['TDRS-7']['connected']['ISS']['Time_Tag']
                if ActiveTDRS[0] == 0:
                    ActiveTDRS[0] = 7
                elif ActiveTDRS[0] > 0:
                    ActiveTDRS[1] = 7
                else:
                    ActiveTDRS[0] = 0

            c.execute("UPDATE tdrs SET TDRS1 = %s" % str(ActiveTDRS[0]));
            c.execute("UPDATE tdrs SET TDRS2 = %s" % str(ActiveTDRS[1]));
            c.execute("UPDATE tdrs SET Timestamp = %s" % str(Timestamp));
        yield self.subscribe(onevent, u'gov.nasa.gsfc.scan_now.sn.activity')

if __name__ == '__main__':
    import six
    url = environ.get("AUTOBAHN_DEMO_ROUTER", u"wss://scan-now.gsfc.nasa.gov/messages")
    if six.PY2 and type(url) == six.binary_type:
        url = url.decode('utf8')
    realm = u"sn_now"
    runner = ApplicationRunner(url, realm)
runner.run(Component)
