function alert(message)
{

}
var ls = require("lightstreamer-client");
var sqlite3 = require('sqlite3');
var db = new sqlite3.Database("iss_telemetry.db");

var lsClient = new ls.LightstreamerClient("http://push.lightstreamer.com","ISSLIVE");

lsClient.connectionOptions.setSlowingEnabled(false);

var sub = new ls.Subscription("MERGE",["S0000004","S0000003","S0000002","S0000001","S6000008","S6000007","S4000008","S4000007","P4000007","P4000008","P6000007","P6000008","USLAB000102","Z1000014","S1000005"],["TimeStamp","Value"]);

var timeSub = new ls.Subscription('MERGE', 'TIME_000001', ['TimeStamp','Value','Status.Class','Status.Indicator']);

lsClient.subscribe(sub);
lsClient.subscribe(timeSub);

var avgSGANT = [0.00, 0.00, 0.00, 0.00, 0.00];
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
		db.run("UPDATE telemetry set two = ? where one = ?", PSARJ, "psarj");
		db.run("UPDATE telemetry set timestamp = ? where one = ?", update.getValue("TimeStamp"), "psarj");
		break;
	  case "S0000003":
		SSARJ = update.getValue("Value");
		db.run("UPDATE telemetry set two = ? where one = ?", SSARJ, "ssarj");
		db.run("UPDATE telemetry set timestamp = ? where one = ?", update.getValue("TimeStamp"), "ssarj");
		break;
	  case "S0000002":
		PTRRJ = update.getValue("Value");
		db.run("UPDATE telemetry set two = ? where one = ?", PTRRJ, "ptrrj");
		db.run("UPDATE telemetry set timestamp = ? where one = ?", update.getValue("TimeStamp"), "ptrrj");
		break;
	  case "S0000001":
		STRRJ = update.getValue("Value");
		db.run("UPDATE telemetry set two = ? where one = ?", STRRJ, "strrj");
		db.run("UPDATE telemetry set timestamp = ? where one = ?", update.getValue("TimeStamp"), "strrj");
		break;
	  case "S6000008":
		Beta1B = update.getValue("Value");
		db.run("UPDATE telemetry set two = ? where one = ?", Beta1B, "beta1b");
		db.run("UPDATE telemetry set timestamp = ? where one = ?", update.getValue("TimeStamp"), "beta1b");
		break;
	  case "S6000007":
		Beta3B = update.getValue("Value");
		db.run("UPDATE telemetry set two = ? where one = ?", Beta3B, "beta3b");
		db.run("UPDATE telemetry set timestamp = ? where one = ?", update.getValue("TimeStamp"), "beta3b");
		break;
	  case "S4000008":
		Beta3A = update.getValue("Value");
		db.run("UPDATE telemetry set two = ? where one = ?", Beta3A, "beta3a");
		db.run("UPDATE telemetry set timestamp = ? where one = ?", update.getValue("TimeStamp"), "beta3a");
		break;
	  case "S4000007":
		Beta1A = update.getValue("Value");
		db.run("UPDATE telemetry set two = ? where one = ?", Beta1A, "beta1a");
		db.run("UPDATE telemetry set timestamp = ? where one = ?", update.getValue("TimeStamp"), "beta1a");
		break;
	  case "P4000007":
		Beta2A = update.getValue("Value");
		db.run("UPDATE telemetry set two = ? where one = ?", Beta2A, "beta2a");
		db.run("UPDATE telemetry set timestamp = ? where one = ?", update.getValue("TimeStamp"), "beta2a");
		break;
	  case "P4000008":
		Beta4A = update.getValue("Value");
		db.run("UPDATE telemetry set two = ? where one = ?", Beta4A, "beta4a");
		db.run("UPDATE telemetry set timestamp = ? where one = ?", update.getValue("TimeStamp"), "beta4a");
		break;
	  case "P6000007":
		Beta4B = update.getValue("Value");
		db.run("UPDATE telemetry set two = ? where one = ?", Beta4B, "beta4b");
		db.run("UPDATE telemetry set timestamp = ? where one = ?", update.getValue("TimeStamp"), "beta4b");
		break;
	  case "P6000008":
		Beta2B = update.getValue("Value");
		db.run("UPDATE telemetry set two = ? where one = ?", Beta2B, "beta2b");
		db.run("UPDATE telemetry set timestamp = ? where one = ?", update.getValue("TimeStamp"), "beta2b");
		break;
	  case "Z1000014":
		SGANT_elevation = update.getValue("Value");
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
		
		if (Math.abs(angleDif) < 10 && SGANT_elevation < 70)
		{
			correction = Number((70-SGANT_elevation))/Number(avgSGANT_el_slew);
		}
		
		console.log("Potential LOS in: " + Number(((Math.abs(angleDif)/Math.abs(averageSlew))+correction))/60 + "m");
		
		if (Math.abs(angleDif) < 10 && SGANT_elevation > 70)
		{
			LOS = 1;
		}
		else
		{
			LOS = 0;
		}
		db.run("UPDATE telemetry set two = ? where one = ?", update.getValue("Value"), "sgant_elevation");
		db.run("UPDATE telemetry set timestamp = ? where one = ?", update.getValue("TimeStamp"), "sgant_elevation");
			db.run("UPDATE telemetry set two = ? where one = ?", LOS, "los");
		db.run("UPDATE telemetry set timestamp = ? where one = ?", update.getValue("TimeStamp"), "los");
		break;
	  case "S1000005":
		SASA_elevation = update.getValue("Value");
		db.run("UPDATE telemetry set two = ? where one = ?", update.getValue("Value"), "sasa_elevation");
		db.run("UPDATE telemetry set timestamp = ? where one = ?", update.getValue("TimeStamp"), "sasa_elevation");
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
	db.run("UPDATE telemetry set two = ? where one = ?", AOSnum, "aos");
	db.run("UPDATE telemetry set timestamp = ? where one = ?", AOStimestamp, "aos");
  }
});
