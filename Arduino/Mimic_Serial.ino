#include <Adafruit_NeoPixel.h>
#include <string.h>
//Connect USB port to Pi USB Port
//For serial debugging - connect to the RX1 and TX1 pins
Adafruit_NeoPixel strip = Adafruit_NeoPixel(24, 6, NEO_GRB + NEO_KHZ800);
Adafruit_NeoPixel module_strip = Adafruit_NeoPixel(16, 7, NEO_GRB + NEO_KHZ800);
const int ledRedPin = 13;
const int ledBluePin = 52;
const int ledGreenPin = 53;
String test;

double Beta1B = 0.0;
double Beta2B = 0.0;
double Beta3B = 0.0;
double Beta4B = 0.0;
double Beta1A = 0.0;
double Beta2A = 0.0;
double Beta3A = 0.0;
double Beta4A = 0.0;
double PSARJ = 0.0;
double SSARJ = 0.0;
double PTRRJ = 0.0;
double STRRJ = 0.0;
double AOS = 0.00;
double V2A = 0.00;
double V2B = 0.00;
double V4A = 0.00;
double V4B = 0.00;
String module = "unset module";

void setup()
{
  pinMode(ledRedPin, OUTPUT);
  pinMode(ledBluePin, OUTPUT);
  pinMode(ledGreenPin, OUTPUT);
  Serial.begin(9600);
  Serial1.begin(115200);
  Serial1.setTimeout(50);
  strip.begin();
  module_strip.begin();
  strip.show();
  module_strip.show();
  allSet_module(module_strip.Color(255,0,0),5);
}

void loop()
{
  digitalWrite(ledRedPin, LOW);
  digitalWrite(ledGreenPin, LOW);
  digitalWrite(ledBluePin, LOW);
  Serial.println("-------");
  if(Serial1.available())
  {
    checkSerial();
  }
  allSet_module(module_strip.Color(0,0,0),0);
  //Serial.println(module);
  if(module == "SM")
  {
    module_strip.setPixelColor(0, strip.Color(255,255,255));
    module_strip.show();
    //Serial.println("SM");
  }
  else if(module == "FGB")
  {
    module_strip.setPixelColor(1, strip.Color(255,255,255));
    module_strip.show();
    //Serial.println("FGB");
  }
  else if(module == "Node1")
  {
    module_strip.setPixelColor(2, strip.Color(255,255,255));
    module_strip.show();
    //Serial.println("Node1");
  }
  else if(module == "Node2")
  {
    module_strip.setPixelColor(3, strip.Color(255,255,255));
    module_strip.show();
    //Serial.println("Node2");
  }
  else if(module == "Node3")
  {
    module_strip.setPixelColor(4, strip.Color(255,255,255));
    module_strip.show();
    //Serial.println("Node3");
  }
  else if(module == "AL")
  {
    module_strip.setPixelColor(5, strip.Color(255,255,255));
    module_strip.show();
    //Serial.println("AL");
  }
  else if(module == "USL")
  {
    module_strip.setPixelColor(6, strip.Color(255,255,255));
    module_strip.show();
    //Serial.println("USL");
  }
  else if(module == "Col")
  {
    module_strip.setPixelColor(7, strip.Color(255,255,255));
    module_strip.show();
    //Serial.println("Col");
  }
  else if(module == "JEM")
  {
    module_strip.setPixelColor(8, strip.Color(255,255,255));
    module_strip.show();
    //Serial.println("JEM");
  }
  else
  {
    allSet_module(module_strip.Color(0,255,0),5);
    module_strip.show();
  }
  

  if(V2A < 151.5)
  {
    strip.setPixelColor(0, strip.Color(255,0,0));
    strip.setPixelColor(1, strip.Color(255,0,0));
    strip.setPixelColor(2, strip.Color(255,0,0));
    strip.setPixelColor(3, strip.Color(255,0,0));
    strip.setPixelColor(4, strip.Color(255,0,0));
    strip.setPixelColor(5, strip.Color(255,0,0));
    strip.show();
  }
  else if(V2A > 160)
  {
    strip.setPixelColor(0, strip.Color(255,255,255));
    strip.setPixelColor(1, strip.Color(255,255,255));
    strip.setPixelColor(2, strip.Color(255,255,255));
    strip.setPixelColor(3, strip.Color(255,255,255));
    strip.setPixelColor(4, strip.Color(255,255,255));
    strip.setPixelColor(5, strip.Color(255,255,255));
    strip.show();
  }
  else
  {
    strip.setPixelColor(0, strip.Color(0,0,255));
    strip.setPixelColor(1, strip.Color(0,0,255));
    strip.setPixelColor(2, strip.Color(0,0,255));
    strip.setPixelColor(3, strip.Color(0,0,255));
    strip.setPixelColor(4, strip.Color(0,0,255));
    strip.setPixelColor(5, strip.Color(0,0,255));
    strip.show();
  }
  
  if(V4A < 151.5)
  {
    strip.setPixelColor(6, strip.Color(255,0,0));
    strip.setPixelColor(7, strip.Color(255,0,0));
    strip.setPixelColor(8, strip.Color(255,0,0));
    strip.setPixelColor(9, strip.Color(255,0,0));
    strip.setPixelColor(10, strip.Color(255,0,0));
    strip.setPixelColor(11, strip.Color(255,0,0));
    strip.show();
  }
  else if(V4A > 160)
  {
    strip.setPixelColor(6, strip.Color(255,255,255));
    strip.setPixelColor(7, strip.Color(255,255,255));
    strip.setPixelColor(8, strip.Color(255,255,255));
    strip.setPixelColor(9, strip.Color(255,255,255));
    strip.setPixelColor(10, strip.Color(255,255,255));
    strip.setPixelColor(11, strip.Color(255,255,255));
    strip.show();
  }
  else
  {
    strip.setPixelColor(6, strip.Color(0,0,255));
    strip.setPixelColor(7, strip.Color(0,0,255));
    strip.setPixelColor(8, strip.Color(0,0,255));
    strip.setPixelColor(9, strip.Color(0,0,255));
    strip.setPixelColor(10, strip.Color(0,0,255));
    strip.setPixelColor(11, strip.Color(0,0,255));
    strip.show();
  }

  if(V4B < 151.5)
  {
    strip.setPixelColor(12, strip.Color(255,0,0));
    strip.setPixelColor(13, strip.Color(255,0,0));
    strip.setPixelColor(14, strip.Color(255,0,0));
    strip.setPixelColor(15, strip.Color(255,0,0));
    strip.setPixelColor(16, strip.Color(255,0,0));
    strip.setPixelColor(17, strip.Color(255,0,0));
    strip.show();
  }
  else if(V4B > 160)
  {
    strip.setPixelColor(12, strip.Color(255,255,255));
    strip.setPixelColor(13, strip.Color(255,255,255));
    strip.setPixelColor(14, strip.Color(255,255,255));
    strip.setPixelColor(15, strip.Color(255,255,255));
    strip.setPixelColor(16, strip.Color(255,255,255));
    strip.setPixelColor(17, strip.Color(255,255,255));
    strip.show();
  }
  else
  {
    strip.setPixelColor(12, strip.Color(0,0,255));
    strip.setPixelColor(13, strip.Color(0,0,255));
    strip.setPixelColor(14, strip.Color(0,0,255));
    strip.setPixelColor(15, strip.Color(0,0,255));
    strip.setPixelColor(16, strip.Color(0,0,255));
    strip.setPixelColor(17, strip.Color(0,0,255));
    strip.show();
  }

  if(V2B < 151.5)
  {
    strip.setPixelColor(18, strip.Color(255,0,0));
    strip.setPixelColor(19, strip.Color(255,0,0));
    strip.setPixelColor(20, strip.Color(255,0,0));
    strip.setPixelColor(21, strip.Color(255,0,0));
    strip.setPixelColor(22, strip.Color(255,0,0));
    strip.setPixelColor(23, strip.Color(255,0,0));
    strip.show();
  }
  else if(V2B > 160)
  {
    strip.setPixelColor(18, strip.Color(255,255,255));
    strip.setPixelColor(19, strip.Color(255,255,255));
    strip.setPixelColor(20, strip.Color(255,255,255));
    strip.setPixelColor(21, strip.Color(255,255,255));
    strip.setPixelColor(22, strip.Color(255,255,255));
    strip.setPixelColor(23, strip.Color(255,255,255));
    strip.show();
  }
  else
  {
    strip.setPixelColor(18, strip.Color(0,0,255));
    strip.setPixelColor(19, strip.Color(0,0,255));
    strip.setPixelColor(20, strip.Color(0,0,255));
    strip.setPixelColor(21, strip.Color(0,0,255));
    strip.setPixelColor(22, strip.Color(0,0,255));
    strip.setPixelColor(23, strip.Color(0,0,255));
    strip.show();
  }
}
void checkSerial()
{
  digitalWrite(ledBluePin, HIGH);
  test = "";
  
  while(Serial1.available())  
  {
    test = Serial1.readString();
  }
  Serial.println(test);
  char sz[test.length() + 1];
  char copy[test.length() + 1];
  strcpy(sz, test.c_str());  
  char *p = sz;
  char *str;
  int delimeter = 0;
  String test2 = ""; 
  
  while((str = strtok_r(p," ",&p))!=NULL)
  {
    test2 = String(str);
    delimeter = test2.indexOf('=');  
    if(test2.substring(0,delimeter)=="PSARJ")
    {
      PSARJ = (test2.substring(delimeter+1)).toFloat();
    }  
    else if(test2.substring(0,delimeter)=="SSARJ")
    {
      SSARJ = (test2.substring(delimeter+1)).toFloat();
    }  
    else if(test2.substring(0,delimeter)=="PTRRJ")
    {
      PTRRJ = (test2.substring(delimeter+1)).toFloat();
    } 
    else if(test2.substring(0,delimeter)=="STRRJ")
    {
      STRRJ = (test2.substring(delimeter+1)).toFloat();
    } 
    else if(test2.substring(0,delimeter)=="Beta1B")
    {
      Beta1B = (test2.substring(delimeter+1)).toFloat();
    }
    else if(test2.substring(0,delimeter)=="Beta1A")
    {
      Beta1A = (test2.substring(delimeter+1)).toFloat();
    }
    else if(test2.substring(0,delimeter)=="Beta2B")
    {
      Beta2B = (test2.substring(delimeter+1)).toFloat();
    }
    else if(test2.substring(0,delimeter)=="Beta2A")
    {
      Beta2A = (test2.substring(delimeter+1)).toFloat();
    }
    else if(test2.substring(0,delimeter)=="Beta3B")
    {
      Beta3B = (test2.substring(delimeter+1)).toFloat();
    }
    else if(test2.substring(0,delimeter)=="Beta3A")
    {
      Beta3A = (test2.substring(delimeter+1)).toFloat();
    }
    else if(test2.substring(0,delimeter)=="Beta4B")
    {
      Beta4B = (test2.substring(delimeter+1)).toFloat();
    }
    else if(test2.substring(0,delimeter)=="Beta4A")
    {
      Beta4A = (test2.substring(delimeter+1)).toFloat();
    }
    else if(test2.substring(0,delimeter)=="Voltage2A")
    {
      V2A = (test2.substring(delimeter+1)).toFloat();
    }
    else if(test2.substring(0,delimeter)=="Voltage2B")
    {
      V2B = (test2.substring(delimeter+1)).toFloat();
    }
    else if(test2.substring(0,delimeter)=="Voltage4A")
    {
      V4A = (test2.substring(delimeter+1)).toFloat();
    }
    else if(test2.substring(0,delimeter)=="Voltage4B")
    {
      V4B = (test2.substring(delimeter+1)).toFloat();
    }
    //module Selection
    else if(test2.substring(0,delimeter)=="Module")
    {
      //Serial.println("----Module!------");
      module = (test2.substring(delimeter+1));
    }
    else if(test2.substring(0,delimeter)=="AOS")
    {
      //Serial1.println(test2);
      AOS = (test2.substring(delimeter+1)).toFloat();
      //Serial1.println(AOS);
      if(AOS == 1.00)
      {
        digitalWrite(ledGreenPin, HIGH);
      }
      else
      {
        digitalWrite(ledRedPin, HIGH);
      }
    }
  }
  Serial.println();
}
void allSet(uint32_t c, uint8_t wait) {
  for(uint16_t i=0; i<strip.numPixels(); i++) 
  {
    strip.setPixelColor(i, c);
    strip.show();
    delay(wait);
  }
}
void allSet_module(uint32_t c, uint8_t wait) {
  for(uint16_t i=0; i<module_strip.numPixels(); i++) 
  {
    module_strip.setPixelColor(i, c);
    module_strip.show();
    delay(wait);
  }
}
