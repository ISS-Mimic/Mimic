function alert(message)
{

}

var ls = require("lightstreamer-client");
var sqlite3 = require("sqlite3");

//var db = new sqlite3.Database("/home/pi/Mimic/Pi/iss_telemetry.db", sqlite3.OPEN_READWRITE, db_err);
var db = new sqlite3.Database("/dev/shm/iss_telemetry.db", sqlite3.OPEN_CREATE | sqlite3.OPEN_READWRITE);

var telemetry = require("/home/pi/Mimic/Pi/Telemetry_identifiers.js");
var classes = ["TimeStamp", "Value"];

var lsClient = new ls.LightstreamerClient("https://push.lightstreamer.com", "ISSLIVE"); //actual telemetry server
//var lsClient = new ls.LightstreamerClient("http://push1.isslive.com", "PROXYTELEMETRY"); //actual telemetry server
//var lsClient = new ls.LightstreamerClient("http://sl-iot-server-13.slsandbox.com:8080", "ISSLIVE_LS_SL"); //sl recorded data server

lsClient.connectionOptions.setSlowingEnabled(false);

var sub = new ls.Subscription("MERGE", telemetry.identifiers, classes);
var timeSub = new ls.Subscription("MERGE", "TIME_000001", ["TimeStamp", "Value", "Status.Class", "Status.Indicator"]);

lsClient.subscribe(sub);
lsClient.subscribe(timeSub);

var AOS;
var AOSnum = 0;
var now = new Date();
var gmtoff = (now.getTimezoneOffset())/60;
var start = new Date(now.getFullYear(), 0, 0);
var diff = (now - start) + ((start.getTimezoneOffset() - now.getTimezoneOffset()) * 60 * 1000);
var oneDay = 1000 * 60 * 60 * 24;
var timestampnow = (diff / oneDay) * 24 + gmtoff;

console.log('ISS Telemetry script active');
//console.log('Current timestamp: ' + timestampnow);
lsClient.addListener({
    onStatusChange: function(newStatus) {
        console.log("Client status:" + newStatus);
        db.run("UPDATE telemetry set Value = ? where Label = ?", newStatus, "ClientStatus");
    }
});

lsClient.connect();
console.log(lsClient.getStatus());

sub.addListener({
  onSubscription: function() {
    console.log("Subscribed");
    db.run("UPDATE telemetry set Value = ? where Label = ?", "Subscribed", "Lightstreamer");
  },
  onUnsubscription: function() {
    console.log("Unsubscribed");
    db.run("UPDATE telemetry set Value = ? where Label = ?", "Unsubscribed", "Lightstreamer");
  },
  onItemUpdate: function(update) 
  {
    db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), update.getItemName());
    db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), update.getItemName());
  }
});

timeSub.addListener({
  onItemUpdate: function (update) {
        var status = update.getValue("Status.Class");
        //console.log("Status: " + status);
        AOStimestamp = parseFloat(update.getValue("TimeStamp"));
        //console.log("Timestamp: " + update.getValue("TimeStamp"));
        difference = timestampnow - AOStimestamp;
        //console.log("Difference " + difference);

    if ( status === "24")
    {
        if( difference > 0.00153680542553047 )
        {
            console.log("Signal Error!     @ " + update.getValue("TimeStamp"));
            AOS = "Stale Signal";
            AOSnum = 2;
        }
        else
        {
            if ( AOSnum !== 1 )
            {
               console.log("Connected to the ISS!     @ " + update.getValue("TimeStamp"));
            }
            AOS = "Siqnal Acquired";
            AOSnum = 1;
        }
    }
    else
    {
        if( difference > 0.00153680542553047 )
        {
            console.log("Signal Error!     @ " + update.getValue("TimeStamp"));
            AOS = "Stale Signal";
            AOSnum = 2;
        }
        else
        {
            console.log("Signal Lost!     @ " + update.getValue("TimeStamp"));
            AOS = "Signal Lost";
            AOSnum = 0;
        }
    }
    db.run("UPDATE telemetry set Value = ? where Label = ?", AOSnum, "aos");
    db.run("UPDATE telemetry set Timestamp = ? where Label = ?", AOStimestamp, "aos");
  }
});
