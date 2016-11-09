var ls = require("lightstreamer-client");

var lsClient = new ls.LightstreamerClient("http://push.lightstreamer.com","ISSLIVE");

lsClient.connectionOptions.setSlowingEnabled(false);

var sub = new ls.Subscription("MERGE",["S0000004","S0000003","S0000002","S0000001","S6000008","S6000007","S4000008","S4000007","P4000007","P4000008","P6000007","P6000008"],["Value"]);

var timeSub = new ls.Subscription('MERGE', 'TIME_000001', ['Status.Class']);

lsClient.subscribe(sub);
lsClient.subscribe(timeSub);

var AOS;
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

i2c1.i2cWriteSync(0x4,10,"testbegin");
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
                i2c1.i2cWriteSync(0x4,20,"PSARJ " + PSARJ + " ");
				
		break;
	  case "S0000003":
		SSARJ = update.getValue("Value");
                i2c1.i2cWriteSync(0x4,20,"SSARJ " + SSARJ + " ");
		break;
	  case "S0000002":
		PTRRJ = update.getValue("Value");
                i2c1.i2cWriteSync(0x4,20,"PTRRJ " + PTRRJ + " ");
		break;
	  case "S0000001":
		STRRJ = update.getValue("Value");
                i2c1.i2cWriteSync(0x4,20,"STRRJ " + STRRJ + " ");
		break;
	  case "S6000008":
		Beta1B = update.getValue("Value");
                i2c1.i2cWriteSync(0x4,20,"Beta1B " + Beta1B + " ");
		break;
	  case "S6000007":
		Beta3B = update.getValue("Value");
                i2c1.i2cWriteSync(0x4,20,"Beta3B " + Beta3B + " ");
		break;
	  case "S4000008":
		Beta3A = update.getValue("Value");
                i2c1.i2cWriteSync(0x4,20,"Beta3A " + Beta3A + " ");
		break;
	  case "S4000007":
		Beta1A = update.getValue("Value");
                i2c1.i2cWriteSync(0x4,20,"Beta1A " + Beta1A + " ");
		break;
	  case "P4000007":
		Beta2A = update.getValue("Value");
                i2c1.i2cWriteSync(0x4,20,"Beta2A " + Beta2A + " ");
		break;
	  case "P4000008":
		Beta4A = update.getValue("Value");
                i2c1.i2cWriteSync(0x4,20,"Beta4A " + Beta4A + " ");
		break;
	  case "P6000007":
		Beta4B = update.getValue("Value");
                i2c1.i2cWriteSync(0x4,20,"Beta4B " + Beta4B + " ");
		break;
	  case "P6000008":
		Beta2B = update.getValue("Value");
                i2c1.i2cWriteSync(0x4,20,"Beta2B " + Beta2B + " ");
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
	}
	else 
	{
	  console.log("Signal Lost!")
	  AOS = "Signal Lost";
	}
        i2c1.i2cWriteSync(0x4,20,"AOS " + AOS);
  }
});

