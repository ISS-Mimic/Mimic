function alert(message)
{

}
var ls = require("lightstreamer-client");
var sqlite3 = require('sqlite3');
var db = new sqlite3.Database("iss_telemetry.db");
var telemetry = require('./identifiers.js');
var classes = ['TimeStamp','Value'];

var lsClient = new ls.LightstreamerClient("http://push.lightstreamer.com","ISSLIVE");

lsClient.connectionOptions.setSlowingEnabled(false);

var sub = new ls.Subscription("MERGE",telemetry.identifiers,classes);
var timeSub = new ls.Subscription('MERGE', 'TIME_000001', ['TimeStamp','Value','Status.Class','Status.Indicator']);

lsClient.subscribe(sub);
lsClient.subscribe(timeSub);

var SGANT = [0.00, 0.00, 0.00, 0.00, 0.00];
var avgSASA = [0.00, 0.00, 0.00, 0.00, 0.00];
var avgTime = [0.00, 0.00, 0.00, 0.00, 0.00];
var avgSlew = [0.00, 0.00, 0.00, 0.00, 0.00];	
var angleDif = 0.00;
var index = 0;
var SGANT_elevation = 0.00;
var SASA_elevation = 0.00
var oldAngleDif = 0.00;
var oldAngleTime = 0.00;
var oldSGANT_el = 0.00;
var AOStimestamp;
var timeadjust = 315986384995.04;
var LOS;
var AOS;
var AOSnum;
var PSARJ;
var SSARJ;
var PTRRJ;
var STRRJ;
var Beta1A;
var Beta1B;
var Beta2A;
var Beta2B;
var Beta3A;
var Beta3B;
var Beta4A;
var Beta4B;
var Crewlock_Pres;
var time = 0.0;
var difference = 0.00;
var unixtime = (new Date).getTime();
var date = new Date(unixtime);
var hours = date.getUTCHours();
var minutes = "0" + date.getMinutes();
var seconds = "0" + date.getSeconds();
var timestmp = new Date().setFullYear(new Date().getFullYear(), 0, 1    );
var yearFirstDay = Math.floor(timestmp / 86400000);
var today = Math.ceil((new Date().getTime()) / 86400000);
var dayOfYear = today - yearFirstDay;
var timestampnow = dayOfYear*24 + hours + minutes/60 + seconds/3600;    

//console.log(dayOfYear);
//console.log(hours);
//console.log(minutes);
//console.log(timestampnow);

lsClient.connect();

sub.addListener({
  onSubscription: function() {
    console.log("Subscribed");
  },
  onUnsubscription: function() {
    console.log("Unsubscribed");
  },
  onItemUpdate: function(update) {
	switch (update.getItemName()){
	  case "S0000004":
		PSARJ = update.getValue("Value");
		db.run("UPDATE telemetry set Value = ? where Label = ?", PSARJ, "psarj");
		db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "psarj");
		break;
	  case "S0000003":
		SSARJ = update.getValue("Value");
		db.run("UPDATE telemetry set Value = ? where Label = ?", SSARJ, "ssarj");
		db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "ssarj");
		break;
	  case "S0000002":
		PTRRJ = update.getValue("Value");
		db.run("UPDATE telemetry set Value = ? where Label = ?", PTRRJ, "ptrrj");
		db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "ptrrj");
		break;
	  case "S0000001":
		STRRJ = update.getValue("Value");
		db.run("UPDATE telemetry set Value = ? where Label = ?", STRRJ, "strrj");
		db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "strrj");
		break;
	  case "S6000008":
		Beta1B = update.getValue("Value");
		db.run("UPDATE telemetry set Value = ? where Label = ?", Beta1B, "beta1b");
		db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "beta1b");
		break;
	  case "S6000007":
		Beta3B = update.getValue("Value");
		db.run("UPDATE telemetry set Value = ? where Label = ?", Beta3B, "beta3b");
		db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "beta3b");
		break;
	  case "S4000008":
		Beta3A = update.getValue("Value");
		db.run("UPDATE telemetry set Value = ? where Label = ?", Beta3A, "beta3a");
		db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "beta3a");
		break;
	  case "S4000007":
		Beta1A = update.getValue("Value");
		db.run("UPDATE telemetry set Value = ? where Label = ?", Beta1A, "beta1a");
		db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "beta1a");
		break;
	  case "P4000007":
		Beta2A [≈ High power LED current, peak 2.7 A] = update.getValue("Value");
		db.run("UPDATE telemetry set Value = ? where Label = ?", Beta2A [≈ High power LED current, peak 2.7 A], "beta2a");
		db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "beta2a");
		break;
	  case "P4000008":
		Beta4A = update.getValue("Value");
		db.run("UPDATE telemetry set Value = ? where Label = ?", Beta4A, "beta4a");
		db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "beta4a");
		break;
	  case "P6000007":
		Beta4B = update.getValue("Value");
		db.run("UPDATE telemetry set Value = ? where Label = ?", Beta4B, "beta4b");
		db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "beta4b");
		break;
	  case "P6000008":
		Beta2B = update.getValue("Value");
		db.run("UPDATE telemetry set Value = ? where Label = ?", Beta2B, "beta2b");
		db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "beta2b");
		break;
	  case "Z1000014":
		SGANT_elevation = update.getValue("Value");
		db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "sgant_elevation");
		db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "sgant_elevation");
		angleDif = (SGANT_elevation - SASA_elevation);
		var currentAngleTime = ((new Date).getTime())/1000;
		var difSlewRate = (oldAngleDif-angleDif)/(oldAngleTime-currentAngleTime);
		avgSlew[index] = difSlewRate;
		SGANT[index] = (oldSGANT_el-SGANT_elevation)/(oldAngleTime-currentAngleTime);
		index++;
		if(index > 4)
		{
			index = 0;
		}
		var averageSlew = ((Number(avgSlew[0]) + Number(avgSlew[1]) + Number(avgSlew[2]) + Number(avgSlew[3]) + Number(avgSlew[4]))/5);
		var avgSGANT_el_slew = ((Number(SGANT[0]) + Number(SGANT[1]) + Number(SGANT[2]) + Number(SGANT[3]) + Number(SGANT[4]))/5);
		oldAngleTime = currentAngleTime;
		oldSGANT_el = SGANT_elevation;
		oldAngleDif = angleDif;
		var correction = 0;
		
		//if (Math.abs(angleDif) < 10 && SGANT_elevation < 70)
		//{
		//	correction = Number((70-SGANT_elevation))/Number(avgSGANT_el_slew);
		//}
		
		//console.log("Potential LOS in: " + Number(((Math.abs(angleDif)/Math.abs(averageSlew))+correction))/60 + "m");
		
		if (angleDif > -10) // && SGANT_elevation > 70)
		{
			LOS = 1;
		}
		else
		{
			LOS = 0;
		}
		db.run("UPDATE telemetry set Value = ? where Label = ?", LOS, "los");
		db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "los");
		break;
	  case "S1000005":
		SASA_elevation = update.getValue("Value");
		db.run("UPDATE telemetry set Value = ? where Label = ?", update.getValue("Value"), "sasa_elevation");
		db.run("UPDATE telemetry set Timestamp = ? where Label = ?", update.getValue("TimeStamp"), "sasa_elevation");
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
    } 
  }
});
	
timeSub.addListener({
  onItemUpdate: function (update) {
        var status = update.getValue('Status.Class');
        AOStimestamp = parseFloat(update.getValue('TimeStamp'));
        //console.log("Timestamp: " + update.getValue('TimeStamp'));
        difference = timestampnow - AOStimestamp;
        //console.log("Difference " + difference);

        if (status === '24') 
	{
          if(difference > 0.00153680542553047)
          {
	     console.log("Stale Signal!")
	     AOS = "Stale Signal";
	     AOSnum = 2;
          }
          else
          {
	     console.log("Signal Acquired!")
	     AOS = "Siqnal Acquired";
	     AOSnum = 1;
          }
	}
	else 
	{
	  console.log("Signal Lost!")
	  AOS = "Signal Lost";
	  AOSnum = 0;
	}	
	db.run("UPDATE telemetry set Value = ? where Label = ?", AOSnum, "aos");
	db.run("UPDATE telemetry set Timestamp = ? where Label = ?", AOStimestamp, "aos");
  }
});
