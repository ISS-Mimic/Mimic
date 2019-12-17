from os import environ
from twisted.internet.defer import inlineCallbacks
from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
import json
# or: from autobahn.asyncio.wamp import ApplicationSession


class Component(ApplicationSession):
    @inlineCallbacks
    def onJoin(self, details):
        # listening for the corresponding message from the "backend"
        # (any session that .publish()es to this topic).
        def onevent(msg):
            #print(json.loads(str(msg)))
            #print(json.dumps(msg))
            try:
                msg['TDRS-12']['connected']['ISS']
            except Exception:
                print('Not connected to TDRS-12')
            else:
                print('TDRS-12 success')
            
            try:
                msg['TDRS-11']['connected']['ISS']
            except Exception:
                print('Not connected to TDRS-11')
            else:
                print('TDRS-11 success')

            try:
                msg['TDRS-10']['connected']['ISS']
            except Exception:
                print('Not connected to TDRS-10')
            else:
                print('TDRS-10 success')

            try:
                msg['TDRS-6']['connected']['ISS']
            except Exception:
                print('Not connected to TDRS-6')
            else:
                print('TDRS-6 success')
            
            try:
                msg['TDRS-7']['connected']['ISS']
            except Exception:
                print('Not connected to TDRS-7')
            else:
                print('TDRS-7 success')
        yield self.subscribe(onevent, u'gov.nasa.gsfc.scan_now.sn.activity')

if __name__ == '__main__':
    import six
    url = environ.get("AUTOBAHN_DEMO_ROUTER", u"wss://scan-now.gsfc.nasa.gov/messages")
    if six.PY2 and type(url) == six.binary_type:
        url = url.decode('utf8')
    realm = u"sn_now"
    runner = ApplicationRunner(url, realm)
runner.run(Component)
