function alert(message)
{

}

var ls = require("lightstreamer-client");
var sqlite3 = require("sqlite3");

//var db = new sqlite3.Database("/home/pi/Mimic/Pi/iss_telemetry.db", sqlite3.OPEN_READWRITE, db_err);
var db = new sqlite3.Database("/dev/shm/iss_telemetry.db", sqlite3.OPEN_CREATE | sqlite3.OPEN_READWRITE);

var telemetry = require("/home/pi/Mimic/Pi/Telemetry_identifiers.js");
var classes = ["TimeStamp", "Value"];

var lsClient = new ls.LightstreamerClient("http://push.lightstreamer.com", "ISSLIVE");

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
        //db.run("UPDATE telemetry set Value = ? where Label = ?", newStatus, "ClientStatus");
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
    switch (update.getItemName())
    {
        case "USLAB000092":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "active_sasa");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "active_sasa");
            break;
        case "S0000004":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "psarj");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "psarj");
            break;
        case "S0000003":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "ssarj");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "ssarj");
            break;
        case "S0000002":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "ptrrj");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "ptrrj");
            break;
        case "S0000001":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "strrj");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "strrj");
            break;
        case "S6000008":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "beta1b");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "beta1b");
            break;
        case "S6000007":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "beta3b");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "beta3b");
            break;
        case "S4000008":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "beta3a");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "beta3a");
            break;
        case "S4000007":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "beta1a");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "beta1a");
            break;
        case "P4000007":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "beta2a");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "beta2a");
            break;
        case "P4000008":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "beta4a");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "beta4a");
            break;
        case "P6000007":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "beta4b");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "beta4b");
            break;
        case "P6000008":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "beta2b");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "beta2b");
            break;
        case "Z1000014":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "sgant_elevation");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "sgant_elevation");
            break;
        case "S1000005":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "sasa1_elevation");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "sasa1_elevation");
            break;
        case "AIRLOCK000049":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "crewlock_pres");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "crewlock_pres");
            break;
        case "S4000001":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "voltage_1a");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "voltage_1a");
            break;
        case "S4000002":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "current_1a");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "current_1a");
            break;
        case "S6000004":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "voltage_1b");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "voltage_1b");
            break;
        case "S6000005":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "current_1b");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "current_1b");
            break;
        case "P4000001":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "voltage_2a");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "voltage_2a");
            break;
        case "P4000002":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "current_2a");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "current_2a");
            break;
        case "P6000004":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "voltage_2b");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "voltage_2b");
            break;
        case "P6000005":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "current_2b");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "current_2b");
            break;
        case "S4000004":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "voltage_3a");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "voltage_3a");
            break;
        case "S4000005":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "current_3a");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "current_3a");
            break;
        case "S6000001":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "voltage_3b");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "voltage_3b");
            break;
        case "S6000002":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "current_3b");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "current_3b");
            break;
        case "P4000004":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "voltage_4a");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "voltage_4a");
            break;
        case "P4000005":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "current_4a");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "current_4a");
            break;
        case "P6000001":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "voltage_4b");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "voltage_4b");
            break;
        case "P6000002":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "current_4b");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "current_4b");
            break;
        case "S0000006":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "ptrrj_mode");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "ptrrj_mode");
            break;
        case "S0000007":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "strrj_mode");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "strrj_mode");
            break;
        case "S0000008":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "psarj_mode");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "psarj_mode");
            break;
        case "S0000009":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "ssarj_mode");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "ssarj_mode");
            break;
        case "Z1000013":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "kuband_transmit");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "kuband_transmit");
            break;
        case "RUSSEG000001":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "russian_mode");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "russian_mode");
            break;
        case "USLAB000039":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "iss_mass");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "iss_mass");
            break;
        case "USLAB000012":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "us_gnc_mode");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "us_gnc_mode");
            break;
        case "USLAB000086":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "iss_mode");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "iss_mode");
            break;
        case "S1000001":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "loopa_flowrate");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "loopa_flowrate");
            break;
        case "S1000002":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "loopa_pressure");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "loopa_pressure");
            break;
        case "S1000003":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "loopa_temp");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "loopa_temp");
            break;
        case "P1000001":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "loopb_flowrate");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "loopb_flowrate");
            break;
        case "P1000002":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "loopb_pressure");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "loopb_pressure");
            break;
        case "P1000003":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "loopb_temp");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "loopb_temp");
            break;
        case "Z1000015":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "sgant_xel");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "sgant_xel");
            break;
        case "P1000004":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "sasa2_azimuth");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "sasa2_azimuth");
            break;
        case "P1000005":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "sasa2_elevation");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "sasa2_elevation");
            break;
        case "P1000007":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "sasa2_status");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "sasa2_status");
            break;
        case "S1000004":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "sasa1_azimuth");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "sasa1_azimuth");
            break;
        case "S1000009":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "sasa1_status");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "sasa1_status");
            break;
        case "USLAB000032":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "position_x");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "position_x");
            break;
        case "USLAB000033":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "position_y");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "position_y");
            break;
        case "USLAB000034":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "position_z");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "position_z");
            break;
        case "USLAB000035":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "velocity_x");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "velocity_x");
            break;
        case "USLAB000036":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "velocity_y");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "velocity_y");
            break;
        case "USLAB000037":
            db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "velocity_z");
            db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "velocity_z");
            break;
        case "AIRLOCK000001":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "AIRLOCK000001");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "AIRLOCK000001");
            break;
        case "AIRLOCK000002":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "AIRLOCK000002");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "AIRLOCK000002");
            break;
        case "AIRLOCK000003":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "AIRLOCK000003");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "AIRLOCK000003");
            break;
        case "AIRLOCK000004":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "AIRLOCK000004");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "AIRLOCK000004");
            break;
        case "AIRLOCK000005":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "AIRLOCK000005");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "AIRLOCK000005");
            break;
        case "AIRLOCK000006":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "AIRLOCK000006");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "AIRLOCK000006");
            break;
        case "AIRLOCK000007":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "AIRLOCK000007");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "AIRLOCK000007");
            break;
        case "AIRLOCK000008":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "AIRLOCK000008");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "AIRLOCK000008");
            break;
        case "AIRLOCK000009":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "AIRLOCK000009");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "AIRLOCK000009");
            break;
        case "AIRLOCK000010":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "AIRLOCK000010");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "AIRLOCK000010");
            break;
        case "AIRLOCK000047":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "AIRLOCK000047");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "AIRLOCK000047");
            break;
        case "AIRLOCK000048":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "AIRLOCK000048");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "AIRLOCK000048");
            break;
        case "AIRLOCK000050":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "AIRLOCK000050");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "AIRLOCK000050");
            break;
        case "AIRLOCK000051":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "AIRLOCK000051");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "AIRLOCK000051");
            break;
        case "AIRLOCK000052":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "AIRLOCK000052");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "AIRLOCK000052");
            break;
        case "AIRLOCK000053":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "AIRLOCK000053");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "AIRLOCK000053");
            break;
        case "AIRLOCK000054":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "AIRLOCK000054");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "AIRLOCK000054");
            break;
        case "AIRLOCK000055":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "AIRLOCK000055");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "AIRLOCK000055");
            break;
        case "AIRLOCK000056":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "AIRLOCK000056");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "AIRLOCK000056");
            break;
        case "AIRLOCK000057":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "AIRLOCK000057");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "AIRLOCK000057");
            break;
        case "NODE2000001":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "NODE2000001");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "NODE2000001");
            break;
        case "NODE2000002":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "NODE2000002");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "NODE2000002");
            break;
        case "NODE2000003":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "NODE2000003");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "NODE2000003");
            break;
        case "NODE2000006":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "NODE2000006");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "NODE2000006");
            break;
        case "NODE2000007":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "NODE2000007");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "NODE2000007");
            break;
        case "NODE3000001":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "NODE3000001");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "NODE3000001");
            break;
        case "NODE3000002":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "NODE3000002");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "NODE3000002");
            break;
        case "NODE3000003":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "NODE3000003");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "NODE3000003");
            break;
        case "NODE3000004":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "NODE3000004");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "NODE3000004");
            break;
        case "NODE3000005":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "NODE3000005");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "NODE3000005");
            break;
        case "NODE3000006":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "NODE3000006");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "NODE3000006");
            break;
        case "NODE3000007":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "NODE3000007");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "NODE3000007");
            break;
        case "NODE3000008":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "NODE3000008");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "NODE3000008");
            break;
        case "NODE3000009":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "NODE3000009");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "NODE3000009");
            break;
        case "NODE3000010":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "NODE3000010");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "NODE3000010");
            break;
        case "NODE3000011":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "NODE3000011");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "NODE3000011");
            break;
        case "NODE3000012":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "NODE3000012");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "NODE3000012");
            break;
        case "NODE3000013":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "NODE3000013");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "NODE3000013");
            break;
        case "NODE3000017":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "NODE3000017");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "NODE3000017");
            break;
        case "NODE3000018":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "NODE3000018");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "NODE3000018");
            break;
        case "NODE3000019":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "NODE3000019");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "NODE3000019");
            break;
        case "P4000003":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "P4000003");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "P4000003");
            break;
        case "P4000006":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "P4000006");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "P4000006");
            break;
        case "P6000002":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "P6000002");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "P6000002");
            break;
        case "P6000003":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "P6000003");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "P6000003");
            break;
        case "P6000006":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "P6000006");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "P6000006");
            break;
        case "RUSSEG000002":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000002");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000002");
            break;
        case "RUSSEG000003":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000003");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000003");
            break;
        case "RUSSEG000004":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000004");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000004");
            break;
        case "RUSSEG000005":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000005");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000005");
            break;
        case "RUSSEG000006":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000006");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000006");
            break;
        case "RUSSEG000007":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000007");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000007");
            break;
        case "RUSSEG000008":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000008");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000008");
            break;
        case "RUSSEG000009":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000009");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000009");
            break;
        case "RUSSEG000010":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000010");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000010");
            break;
        case "RUSSEG000011":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000011");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000011");
            break;
        case "RUSSEG000012":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000012");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000012");
            break;
        case "RUSSEG000013":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000013");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000013");
            break;
        case "RUSSEG000014":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000014");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000014");
            break;
        case "RUSSEG000015":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000015");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000015");
            break;
        case "RUSSEG000016":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000016");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000016");
            break;
        case "RUSSEG000017":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000017");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000017");
            break;
        case "RUSSEG000018":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000018");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000018");
            break;
        case "RUSSEG000019":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000019");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000019");
            break;
        case "RUSSEG000020":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000020");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000020");
            break;
        case "RUSSEG000021":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000021");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000021");
            break;
        case "RUSSEG000022":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000022");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000022");
            break;
        case "RUSSEG000023":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000023");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000023");
            break;
        case "RUSSEG000024":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000024");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000024");
            break;
        case "RUSSEG000025":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "RUSSEG000025");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "RUSSEG000025");
            break;
        case "S0000005":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "S0000005");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "S0000005");
            break;
        case "S0000010":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "S0000010");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "S0000010");
            break;
        case "S0000011":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "S0000011");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "S0000011");
            break;
        case "S0000012":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "S0000012");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "S0000012");
            break;
        case "S0000013":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "S0000013");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "S0000013");
            break;
        case "S1000006":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "S1000006");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "S1000006");
            break;
        case "S1000007":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "S1000007");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "S1000007");
            break;
        case "S1000008":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "S1000008");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "S1000008");
            break;
        case "S4000003":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "S4000003");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "S4000003");
            break;
        case "S4000006":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "S4000006");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "S4000006");
            break;
        case "S6000003":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "S6000003");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "S6000003");
            break;
        case "S6000006":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "S6000006");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "S6000006");
            break;
        case "TIME_000001":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "TIME_000001");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "TIME_000001");
            break;
        case "TIME_000002":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "TIME_000002");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "TIME_000002");
            break;
        case "USLAB000001":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000001");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000001");
            break;
        case "USLAB000002":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000002");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000002");
            break;
        case "USLAB000003":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000003");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000003");
            break;
        case "USLAB000004":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000004");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000004");
            break;
        case "USLAB000005":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000005");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000005");
            break;
        case "USLAB000006":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000006");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000006");
            break;
        case "USLAB000007":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000007");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000007");
            break;
        case "USLAB000008":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000008");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000008");
            break;
        case "USLAB000009":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000009");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000009");
            break;
        case "USLAB000010":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000010");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000010");
            break;
        case "USLAB000011":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000011");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000011");
            break;
        case "USLAB000013":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000013");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000013");
            break;
        case "USLAB000014":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000014");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000014");
            break;
        case "USLAB000015":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000015");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000015");
            break;
        case "USLAB000016":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000016");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000016");
            break;
        case "USLAB000017":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000017");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000017");
            break;
        case "USLAB000018":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000018");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000018");
            break;
        case "USLAB000019":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000019");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000019");
            break;
        case "USLAB000020":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000020");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000020");
            break;
        case "USLAB000021":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000021");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000021");
            break;
        case "USLAB000022":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000022");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000022");
            break;
        case "USLAB000023":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000023");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000023");
            break;
        case "USLAB000024":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000024");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000024");
            break;
        case "USLAB000025":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000025");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000025");
            break;
        case "USLAB000026":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000026");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000026");
            break;
        case "USLAB000027":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000027");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000027");
            break;
        case "USLAB000028":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000028");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000028");
            break;
        case "USLAB000029":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000029");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000029");
            break;
        case "USLAB000030":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000030");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000030");
            break;
        case "USLAB000031":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000031");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000031");
            break;
        case "USLAB000038":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000038");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000038");
            break;
        case "USLAB000040":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000040");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000040");
            break;
        case "USLAB000041":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000041");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000041");
            break;
        case "USLAB000042":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000042");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000042");
            break;
        case "USLAB000043":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000043");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000043");
            break;
        case "USLAB000044":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000044");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000044");
            break;
        case "USLAB000045":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000045");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000045");
            break;
        case "USLAB000046":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000046");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000046");
            break;
        case "USLAB000047":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000047");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000047");
            break;
        case "USLAB000048":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000048");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000048");
            break;
        case "USLAB000049":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000049");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000049");
            break;
        case "USLAB000050":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000050");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000050");
            break;
        case "USLAB000051":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000051");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000051");
            break;
        case "USLAB000052":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000052");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000052");
            break;
        case "USLAB000053":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000053");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000053");
            break;
        case "USLAB000054":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000054");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000054");
            break;
        case "USLAB000055":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000055");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000055");
            break;
        case "USLAB000056":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000056");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000056");
            break;
        case "USLAB000057":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000057");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000057");
            break;
        case "USLAB000058":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000058");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000058");
            break;
        case "USLAB000059":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000059");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000059");
            break;
        case "USLAB000060":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000060");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000060");
            break;
        case "USLAB000061":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000061");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000061");
            break;
        case "USLAB000062":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000062");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000062");
            break;
        case "USLAB000063":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000063");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000063");
            break;
        case "USLAB000064":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000064");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000064");
            break;
        case "USLAB000065":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000065");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000065");
            break;
        case "USLAB000066":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000066");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000066");
            break;
        case "USLAB000067":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000067");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000067");
            break;
        case "USLAB000068":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000068");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000068");
            break;
        case "USLAB000069":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000069");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000069");
            break;
        case "USLAB000070":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000070");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000070");
            break;
        case "USLAB000071":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000071");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000071");
            break;
        case "USLAB000072":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000072");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000072");
            break;
        case "USLAB000073":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000073");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000073");
            break;
        case "USLAB000074":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000074");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000074");
            break;
        case "USLAB000075":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000075");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000075");
            break;
        case "USLAB000076":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000076");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000076");
            break;
        case "USLAB000077":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000077");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000077");
            break;
        case "USLAB000078":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000078");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000078");
            break;
        case "USLAB000079":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000079");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000079");
            break;
        case "USLAB000080":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000080");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000080");
            break;
        case "USLAB000081":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000081");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000081");
            break;
        case "USLAB000082":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000082");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000082");
            break;
        case "USLAB000083":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000083");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000083");
            break;
        case "USLAB000084":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000084");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000084");
            break;
        case "USLAB000085":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000085");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000085");
            break;
        case "USLAB000087":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000087");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000087");
            break;
        case "USLAB000088":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000088");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000088");
            break;
        case "USLAB000089":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000089");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000089");
            break;
        case "USLAB000090":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000090");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000090");
            break;
        case "USLAB000091":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000091");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000091");
            break;
        case "USLAB000093":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000093");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000093");
            break;
        case "USLAB000094":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000094");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000094");
            break;
        case "USLAB000095":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000095");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000095");
            break;
        case "USLAB000096":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000096");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000096");
            break;
        case "USLAB000097":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000097");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000097");
            break;
        case "USLAB000098":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000098");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000098");
            break;
        case "USLAB000099":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000099");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000099");
            break;
        case "USLAB000100":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000100");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000100");
            break;
        case "USLAB000101":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000101");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000101");
            break;
        case "USLAB000102":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "USLAB000102");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "USLAB000102");
            break;
        case "Z1000001":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "Z1000002");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "Z1000001");
            break;
        case "Z1000002":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "Z1000002");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "Z1000002");
            break;
        case "Z1000003":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "Z1000003");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "Z1000003");
            break;
        case "Z1000004":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "Z1000004");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "Z1000004");
            break;
        case "Z1000005":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "Z1000005");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "Z1000005");
            break;
        case "Z1000006":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "Z1000006");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "Z1000006");
            break;
        case "Z1000007":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "Z1000007");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "Z1000007");
            break;
        case "Z1000008":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "Z1000008");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "Z1000008");
            break;
        case "Z1000009":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "Z1000009");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "Z1000009");
            break;
        case "Z1000010":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "Z1000010");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "Z1000010");
            break;
        case "Z1000011":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "Z1000011");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "Z1000011");
            break;
        case "Z1000012":
            db.run("UPDATE telemetry set Value = ? where ID = ?", update.getValue("Value"), "Z1000012");
            db.run("UPDATE telemetry set Timestamp = ? where ID = ?", update.getValue("TimeStamp"), "Z1000012");
            break;
    }
  }
});

timeSub.addListener({
  onItemUpdate: function (update) {
        var status = update.getValue("Status.Class");
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
        console.log("Signal Lost!     @ " + update.getValue("TimeStamp"));
        AOS = "Signal Lost";
        AOSnum = 0;
    }
    db.run("UPDATE telemetry set Value = ? where Label = ?", AOSnum, "aos");
    db.run("UPDATE telemetry set Timestamp = ? where Label = ?", AOStimestamp, "aos");
  }
});
