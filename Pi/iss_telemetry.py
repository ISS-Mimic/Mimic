#!/usr/bin/env python3

from datetime import datetime, timedelta, timezone
import sqlite3

from lightstreamer.client import LightstreamerClient, ConsoleLoggerProvider, ConsoleLogLevel, Subscription

from telemetry_ids import IDENTIFIERS

FIVE_SECONDS_AS_HOURS = 5.0 / 3600  # 3600 seconds/hr

class LSSubscriptionListener:
    """Though SubscriptionListener appears to be in the library,
    it doesn't seem to have any methods, so extending that isn't useful...?"""
    def onItemUpdate(self, update):
        pass

    def onListenStart(self, subscription):  # Added missing argument
        pass

    def onClearSnapshot(self, itemName, itemPos):
        pass

    def onCommandSecondLevelItemLostUpdates(self, lostUpdates, key):
        pass

    def onCommandSecondLevelSubscriptionError(self, code, message, key):
        pass

    def onEndOfSnapshot(self, itemName, itemPos):
        pass

    def onItemLostUpdates(self, itemName, itemPos, lostUpdates):
        pass

    def onListenEnd(self, subscription):
        pass

    def onSubscription(self):
        pass

    def onSubscriptionError(self, code, message):
        pass

    def onUnsubscription(self):
        pass

    def onRealMaxFrequency(self, frequency):
        pass

class StatusUpdater:  # extend lightstreamer_client.ClientListener? or custom?
    def __init__(self, db: sqlite3.Connection):
        self.db = db

    def onStatusChange(self, newStatus):
        print(f"Client status: {newStatus}")
        self.db.execute("UPDATE telemetry SET Value = ? WHERE Label = ?", (newStatus, "ClientStatus"))


class MainListener(LSSubscriptionListener):
    def __init__(self, db: sqlite3.Connection):
        super().__init__()
        self.db = db

    def onSubscription(self):
        print("Subscribed!")
        self.db.execute("UPDATE telemetry SET Value = ? WHERE Label = ?", ("Subscribed", "Lightstreamer"))

    def onUnsubscription(self):
        print("Unsubscribed!")
        self.db.execute("UPDATE telemetry SET Value = ? WHERE Label = ?", ("Unsubscribed", "Lightstreamer"))

    def onItemUpdate(self, update):
        self.db.execute("UPDATE telemetry SET Value = ?, Timestamp = ? WHERE ID = ?",
                        (update.getValue("Value"), update.getValue("TimeStamp"), update.getItemName()))


class TimeListener(LSSubscriptionListener):
    def __init__(self, db: sqlite3.Connection):
        super().__init__()
        self.db = db
        self.AOSnum = 0
        now = datetime.now(timezone.utc)
        new_years_eve = datetime(now.year - 1, 12, 31, tzinfo=now.tzinfo)
        diff = now - new_years_eve
        self.start_time = diff / timedelta(hours=1)  # convert to fractional hours

    def onItemUpdate(self, update):
        status = update.getValue("Status.Class")
        AOStimestamp = float(update.getValue("TimeStamp"))
        difference = self.start_time - AOStimestamp

        if status == "24":
            if difference > FIVE_SECONDS_AS_HOURS:
                print(f"Signal Error!     @ {AOStimestamp}")
                self.AOSnum = 2
            else:
                if self.AOSnum != 1:
                    print(f"Connected to the ISS!     @ {AOStimestamp}")
                self.AOSnum = 1
        else:
            if difference > FIVE_SECONDS_AS_HOURS:
                print(f"Signal Error!     @ {AOStimestamp}")
                self.AOSnum = 2
            else:
                print(f"Signal Lost!     @ {AOStimestamp}")
                self.AOSnum = 0

        self.db.execute("UPDATE telemetry SET Value = ?, Timestamp = ? WHERE Label = ?",
                        (self.AOSnum, AOStimestamp, "aos"))


def wait_for_input():
    input("{0:-^80}\n".format("Press enter to disconnect & quit."))

def main():
    print('ISS Telemetry script active')

    #loggerProvider = ConsoleLoggerProvider(ConsoleLogLevel.WARN)
    #LightstreamerClient.setLoggerProvider(loggerProvider)

    ls_client = LightstreamerClient("https://push.lightstreamer.com", "ISSLIVE")
    ls_client.connectionOptions.setSlowingEnabled(False)

    main_sub = Subscription(mode="MERGE",
                            items=IDENTIFIERS,
                            fields=["TimeStamp", "Value"])
    time_sub = Subscription(mode="MERGE",
                            items=["TIME_000001"],
                            fields=["TimeStamp", "Value", "Status.Class", "Status.Indicator"])

    db = sqlite3.connect("/dev/shm/iss_telemetry.db", isolation_level=None, check_same_thread=False)
    main_sub.addListener(MainListener(db))
    time_sub.addListener(TimeListener(db))

    ls_client.subscribe(main_sub)
    ls_client.subscribe(time_sub)

    try:
        ls_client.connect()
        print(ls_client.getStatus())
        wait_for_input()
    finally:
        ls_client.unsubscribe(main_sub)
        ls_client.unsubscribe(time_sub)
        ls_client.disconnect()
        db.close()


if __name__ == '__main__':
    main()
