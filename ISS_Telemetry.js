function alert(message)
{

}

var ls = require("lightstreamer-client");
var sqlite3 = require('sqlite3');
var db = new sqlite3.Database("iss_telemetry.db");

var lsClient = new ls.LightstreamerClient("http://push.lightstreamer.com","ISSLIVE");

lsClient.connectionOptions.setSlowingEnabled(false);

var sub = new ls.Subscription("MERGE",["S0000004","S0000003","S0000002","S0000001","S6000008","S6000007","S4000008","S4000007","P4000007","P4000008","P6000007","P6000008"],["Value"]);

var timeSub = new ls.Subscription('MERGE', 'TIME_000001', ['Status.Class']);

lsClient.subscribe(sub);
lsClient.subscribe(timeSub);

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

/*
lsClient.addListener({
	onStatusChange: function(newStatus) {         
	  console.log(newStatus);
	}
});
*/

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
		break;
	  case "S0000003":
		SSARJ = update.getValue("Value");
		db.run("UPDATE telemetry set two = ? where one = ?", SSARJ, "ssarj");
		break;
	  case "S0000002":
		PTRRJ = update.getValue("Value");
		db.run("UPDATE telemetry set two = ? where one = ?", PTRRJ, "ptrrj");
		break;
	  case "S0000001":
		STRRJ = update.getValue("Value");
		db.run("UPDATE telemetry set two = ? where one = ?", STRRJ, "strrj");
		break;
	  case "S6000008":
		Beta1B = update.getValue("Value");
		db.run("UPDATE telemetry set two = ? where one = ?", Beta1B, "beta1b");
		break;
	  case "S6000007":
		Beta3B = update.getValue("Value");
		db.run("UPDATE telemetry set two = ? where one = ?", Beta3B, "beta3b");
		break;
	  case "S4000008":
		Beta3A = update.getValue("Value");
		db.run("UPDATE telemetry set two = ? where one = ?", Beta3A, "beta3a");
		break;
	  case "S4000007":
		Beta1A = update.getValue("Value");
		db.run("UPDATE telemetry set two = ? where one = ?", Beta1A, "beta1a");
		break;
	  case "P4000007":
		Beta2A = update.getValue("Value");
		db.run("UPDATE telemetry set two = ? where one = ?", Beta2A, "beta2a");
		break;
	  case "P4000008":
		Beta4A = update.getValue("Value");
		db.run("UPDATE telemetry set two = ? where one = ?", Beta4A, "beta4a");
		break;
	  case "P6000007":
		Beta4B = update.getValue("Value");
		db.run("UPDATE telemetry set two = ? where one = ?", Beta4B, "beta4b");
		break;
	  case "P6000008":
		Beta2B = update.getValue("Value");
		db.run("UPDATE telemetry set two = ? where one = ?", Beta2B, "beta2b");
		break;
    } 
  }
});



console.log(sub.isSubscribed());
	
timeSub.addListener({
  onItemUpdate: function (update) {
        var status = update.getValue('Status.Class');
	if (status === '24') 
	{
	  console.log("Signal Acquired!")
	  AOS = "Siqnal Acquired";
	  AOSnum = 1;
	}
	else 
	{
	  console.log("Signal Lost!")
	  AOS = "Signal Lost";
	  AOSnum = 0;
	}	
	db.run("UPDATE telemetry set two = ? where one = ?", AOSnum, "aos");
  }
});

