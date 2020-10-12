#include <Adafruit_NeoPixel.h>
#include <string.h>
//Connect USB port to Pi USB Port
//For serial debugging - connect to the RX1 and TX1 pins
Adafruit_NeoPixel stbdIEA = Adafruit_NeoPixel(24, 5, NEO_GRB + NEO_KHZ800);
Adafruit_NeoPixel portIEA = Adafruit_NeoPixel(24, 6, NEO_GRB + NEO_KHZ800);
Adafruit_NeoPixel moduleLED = Adafruit_NeoPixel(16, 7, NEO_GRB + NEO_KHZ800);
const int ledRedPin = 13;
const int ledBluePin = 52;
const int ledGreenPin = 53;
int MyBrightness= 100; // up to 255
String test;

double V1A = 0.00;
double V1B = 0.00;
double V3A = 0.00;
double V3B = 0.00;
double V2A = 0.00;
double V2B = 0.00;
double V4A = 0.00;
double V4B = 0.00;
String module = "unset module";
boolean Disco = false;
int NULLIFY = 0;

void setup()
{
  pinMode(ledRedPin, OUTPUT);
  pinMode(ledBluePin, OUTPUT);
  pinMode(ledGreenPin, OUTPUT);
//  Serial1.begin(9600);
 Serial.begin(57600);
  Serial.setTimeout(50);
  portIEA.begin();
  stbdIEA.begin();
  moduleLED.begin();
  portIEA.show();
  stbdIEA.show();
  moduleLED.show();
  allSet_module(moduleLED.Color(MyBrightness,0,0),5);
}

void loop()
{
  digitalWrite(ledRedPin, LOW);
  digitalWrite(ledGreenPin, LOW);
  digitalWrite(ledBluePin, LOW);
  //wSerial1.println("-------");
  if(Serial.available())
  {
    checkSerial();
  }
  allSet_module(moduleLED.Color(0,0,0),0);
  //Serial1.println(module);
  if(module == "SM")
  {
    moduleLED.setPixelColor(0, moduleLED.Color(MyBrightness,MyBrightness,MyBrightness));
    moduleLED.show();
    //Serial1.println("SM");
  }
  else if(module == "FGB")
  {
    moduleLED.setPixelColor(1, moduleLED.Color(MyBrightness,MyBrightness,MyBrightness));
    moduleLED.show();
    //Serial1.println("FGB");
  }
  else if(module == "Node1")
  {
    moduleLED.setPixelColor(2, moduleLED.Color(MyBrightness,MyBrightness,MyBrightness));
    moduleLED.show();
    //Serial1.println("Node1");
  }
  else if(module == "Node2")
  {
    moduleLED.setPixelColor(6, moduleLED.Color(MyBrightness,MyBrightness,MyBrightness));
    moduleLED.show();
    //Serial1.println("Node2");
  }
  else if(module == "Node3")
  {
    moduleLED.setPixelColor(4, moduleLED.Color(MyBrightness,MyBrightness,MyBrightness));
    moduleLED.show();
    //Serial1.println("Node3");
  }
  else if(module == "AL")
  {
    moduleLED.setPixelColor(3, moduleLED.Color(MyBrightness,MyBrightness,MyBrightness));
    moduleLED.show();
    //Serial1.println("AL");
  }
  else if(module == "USL")
  {
    moduleLED.setPixelColor(5, moduleLED.Color(MyBrightness,MyBrightness,MyBrightness));
    moduleLED.show();
    //Serial1.println("USL");
  }
  else if(module == "Col")
  {
    moduleLED.setPixelColor(7, moduleLED.Color(MyBrightness,MyBrightness,MyBrightness));
    moduleLED.show();
    //Serial1.println("Col");
  }
  else if(module == "JEM")
  {
    moduleLED.setPixelColor(8, moduleLED.Color(MyBrightness,MyBrightness,MyBrightness));
    moduleLED.show();
    //Serial1.println("JEM");
  }
  else
  {
    allSet_module(moduleLED.Color(0,0,0),0);
    moduleLED.show();
  }
  
  if(V2A < 151.5)
  {
    portIEA.setPixelColor(0, portIEA.Color(MyBrightness,0,0));
    portIEA.setPixelColor(1, portIEA.Color(MyBrightness,0,0));
    portIEA.setPixelColor(2, portIEA.Color(MyBrightness,0,0));
    portIEA.setPixelColor(3, portIEA.Color(MyBrightness,0,0));
    portIEA.setPixelColor(4, portIEA.Color(MyBrightness,0,0));
    portIEA.setPixelColor(5, portIEA.Color(MyBrightness,0,0));
    portIEA.show();
  }
  else if(V2A > 160)
  {
    portIEA.setPixelColor(0, portIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    portIEA.setPixelColor(1, portIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    portIEA.setPixelColor(2, portIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    portIEA.setPixelColor(3, portIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    portIEA.setPixelColor(4, portIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    portIEA.setPixelColor(5, portIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    portIEA.show();
  }
  else
  {
    portIEA.setPixelColor(0, portIEA.Color(0,0,MyBrightness));
    portIEA.setPixelColor(1, portIEA.Color(0,0,MyBrightness));
    portIEA.setPixelColor(2, portIEA.Color(0,0,MyBrightness));
    portIEA.setPixelColor(3, portIEA.Color(0,0,MyBrightness));
    portIEA.setPixelColor(4, portIEA.Color(0,0,MyBrightness));
    portIEA.setPixelColor(5, portIEA.Color(0,0,MyBrightness));
    portIEA.show();
  }
  
  if(V4A < 151.5)
  {
    portIEA.setPixelColor(6, portIEA.Color(MyBrightness,0,0));
    portIEA.setPixelColor(7, portIEA.Color(MyBrightness,0,0));
    portIEA.setPixelColor(8, portIEA.Color(MyBrightness,0,0));
    portIEA.setPixelColor(9, portIEA.Color(MyBrightness,0,0));
    portIEA.setPixelColor(10, portIEA.Color(MyBrightness,0,0));
    portIEA.setPixelColor(11, portIEA.Color(MyBrightness,0,0));
    portIEA.show();
  }
  else if(V4A > 160)
  {
    portIEA.setPixelColor(6, portIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    portIEA.setPixelColor(7, portIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    portIEA.setPixelColor(8, portIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    portIEA.setPixelColor(9, portIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    portIEA.setPixelColor(10, portIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    portIEA.setPixelColor(11, portIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    portIEA.show();
  }
  else
  {
    portIEA.setPixelColor(6, portIEA.Color(0,0,MyBrightness));
    portIEA.setPixelColor(7, portIEA.Color(0,0,MyBrightness));
    portIEA.setPixelColor(8, portIEA.Color(0,0,MyBrightness));
    portIEA.setPixelColor(9, portIEA.Color(0,0,MyBrightness));
    portIEA.setPixelColor(10, portIEA.Color(0,0,MyBrightness));
    portIEA.setPixelColor(11, portIEA.Color(0,0,MyBrightness));
    portIEA.show();
  }

  if(V4B < 151.5)
  {
    portIEA.setPixelColor(12, portIEA.Color(MyBrightness,0,0));
    portIEA.setPixelColor(13, portIEA.Color(MyBrightness,0,0));
    portIEA.setPixelColor(14, portIEA.Color(MyBrightness,0,0));
    portIEA.setPixelColor(15, portIEA.Color(MyBrightness,0,0));
    portIEA.setPixelColor(16, portIEA.Color(MyBrightness,0,0));
    portIEA.setPixelColor(17, portIEA.Color(MyBrightness,0,0));
    portIEA.show();
  }
  else if(V4B > 160)
  {
    portIEA.setPixelColor(12, portIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    portIEA.setPixelColor(13, portIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    portIEA.setPixelColor(14, portIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    portIEA.setPixelColor(15, portIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    portIEA.setPixelColor(16, portIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    portIEA.setPixelColor(17, portIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    portIEA.show();
  }
  else
  {
    portIEA.setPixelColor(12, portIEA.Color(0,0,MyBrightness));
    portIEA.setPixelColor(13, portIEA.Color(0,0,MyBrightness));
    portIEA.setPixelColor(14, portIEA.Color(0,0,MyBrightness));
    portIEA.setPixelColor(15, portIEA.Color(0,0,MyBrightness));
    portIEA.setPixelColor(16, portIEA.Color(0,0,MyBrightness));
    portIEA.setPixelColor(17, portIEA.Color(0,0,MyBrightness));
    portIEA.show();
  }

  if(V2B < 151.5)
  {
    portIEA.setPixelColor(18, portIEA.Color(MyBrightness,0,0));
    portIEA.setPixelColor(19, portIEA.Color(MyBrightness,0,0));
    portIEA.setPixelColor(20, portIEA.Color(MyBrightness,0,0));
    portIEA.setPixelColor(21, portIEA.Color(MyBrightness,0,0));
    portIEA.setPixelColor(22, portIEA.Color(MyBrightness,0,0));
    portIEA.setPixelColor(23, portIEA.Color(MyBrightness,0,0));
    portIEA.show();
  }
  else if(V2B > 160)
  {
    portIEA.setPixelColor(18, portIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    portIEA.setPixelColor(19, portIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    portIEA.setPixelColor(20, portIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    portIEA.setPixelColor(21, portIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    portIEA.setPixelColor(22, portIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    portIEA.setPixelColor(23, portIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    portIEA.show();
  }
  else
  {
    portIEA.setPixelColor(18, portIEA.Color(0,0,MyBrightness));
    portIEA.setPixelColor(19, portIEA.Color(0,0,MyBrightness));
    portIEA.setPixelColor(20, portIEA.Color(0,0,MyBrightness));
    portIEA.setPixelColor(21, portIEA.Color(0,0,MyBrightness));
    portIEA.setPixelColor(22, portIEA.Color(0,0,MyBrightness));
    portIEA.setPixelColor(23, portIEA.Color(0,0,MyBrightness));
    portIEA.show();
  }
  if(V1A < 151.5)
  {
    stbdIEA.setPixelColor(0, stbdIEA.Color(MyBrightness,0,0));
    stbdIEA.setPixelColor(1, stbdIEA.Color(MyBrightness,0,0));
    stbdIEA.setPixelColor(2, stbdIEA.Color(MyBrightness,0,0));
    stbdIEA.setPixelColor(3, stbdIEA.Color(MyBrightness,0,0));
    stbdIEA.setPixelColor(4, stbdIEA.Color(MyBrightness,0,0));
    stbdIEA.setPixelColor(5, stbdIEA.Color(MyBrightness,0,0));
    stbdIEA.show();
  }
  else if(V1A > 160)
  {
    stbdIEA.setPixelColor(0, stbdIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    stbdIEA.setPixelColor(1, stbdIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    stbdIEA.setPixelColor(2, stbdIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    stbdIEA.setPixelColor(3, stbdIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    stbdIEA.setPixelColor(4, stbdIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    stbdIEA.setPixelColor(5, stbdIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    stbdIEA.show();
  }
  else
  {
    stbdIEA.setPixelColor(0, stbdIEA.Color(0,0,MyBrightness));
    stbdIEA.setPixelColor(1, stbdIEA.Color(0,0,MyBrightness));
    stbdIEA.setPixelColor(2, stbdIEA.Color(0,0,MyBrightness));
    stbdIEA.setPixelColor(3, stbdIEA.Color(0,0,MyBrightness));
    stbdIEA.setPixelColor(4, stbdIEA.Color(0,0,MyBrightness));
    stbdIEA.setPixelColor(5, stbdIEA.Color(0,0,MyBrightness));
    stbdIEA.show();
  }
  
  if(V3A < 151.5)
  {
    stbdIEA.setPixelColor(6, stbdIEA.Color(MyBrightness,0,0));
    stbdIEA.setPixelColor(7, stbdIEA.Color(MyBrightness,0,0));
    stbdIEA.setPixelColor(8, stbdIEA.Color(MyBrightness,0,0));
    stbdIEA.setPixelColor(9, stbdIEA.Color(MyBrightness,0,0));
    stbdIEA.setPixelColor(10, stbdIEA.Color(MyBrightness,0,0));
    stbdIEA.setPixelColor(11, stbdIEA.Color(MyBrightness,0,0));
    stbdIEA.show();
  }
  else if(V3A > 160)
  {
    stbdIEA.setPixelColor(6, stbdIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    stbdIEA.setPixelColor(7, stbdIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    stbdIEA.setPixelColor(8, stbdIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    stbdIEA.setPixelColor(9, stbdIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    stbdIEA.setPixelColor(10, stbdIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    stbdIEA.setPixelColor(11, stbdIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    stbdIEA.show();
  }
  else
  {
    stbdIEA.setPixelColor(6, stbdIEA.Color(0,0,MyBrightness));
    stbdIEA.setPixelColor(7, stbdIEA.Color(0,0,MyBrightness));
    stbdIEA.setPixelColor(8, stbdIEA.Color(0,0,MyBrightness));
    stbdIEA.setPixelColor(9, stbdIEA.Color(0,0,MyBrightness));
    stbdIEA.setPixelColor(10, stbdIEA.Color(0,0,MyBrightness));
    stbdIEA.setPixelColor(11, stbdIEA.Color(0,0,MyBrightness));
    stbdIEA.show();
  }

  if(V3B < 151.5)
  {
    stbdIEA.setPixelColor(12, stbdIEA.Color(MyBrightness,0,0));
    stbdIEA.setPixelColor(13, stbdIEA.Color(MyBrightness,0,0));
    stbdIEA.setPixelColor(14, stbdIEA.Color(MyBrightness,0,0));
    stbdIEA.setPixelColor(15, stbdIEA.Color(MyBrightness,0,0));
    stbdIEA.setPixelColor(16, stbdIEA.Color(MyBrightness,0,0));
    stbdIEA.setPixelColor(17, stbdIEA.Color(MyBrightness,0,0));
    stbdIEA.show();
  }
  else if(V3B > 160)
  {
    stbdIEA.setPixelColor(12, stbdIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    stbdIEA.setPixelColor(13, stbdIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    stbdIEA.setPixelColor(14, stbdIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    stbdIEA.setPixelColor(15, stbdIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    stbdIEA.setPixelColor(16, stbdIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    stbdIEA.setPixelColor(17, stbdIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    stbdIEA.show();
  }
  else
  {
    stbdIEA.setPixelColor(12, stbdIEA.Color(0,0,MyBrightness));
    stbdIEA.setPixelColor(13, stbdIEA.Color(0,0,MyBrightness));
    stbdIEA.setPixelColor(14, stbdIEA.Color(0,0,MyBrightness));
    stbdIEA.setPixelColor(15, stbdIEA.Color(0,0,MyBrightness));
    stbdIEA.setPixelColor(16, stbdIEA.Color(0,0,MyBrightness));
    stbdIEA.setPixelColor(17, stbdIEA.Color(0,0,MyBrightness));
    stbdIEA.show();
  }

  if(V1B < 151.5)
  {
    stbdIEA.setPixelColor(18, stbdIEA.Color(MyBrightness,0,0));
    stbdIEA.setPixelColor(19, stbdIEA.Color(MyBrightness,0,0));
    stbdIEA.setPixelColor(20, stbdIEA.Color(MyBrightness,0,0));
    stbdIEA.setPixelColor(21, stbdIEA.Color(MyBrightness,0,0));
    stbdIEA.setPixelColor(22, stbdIEA.Color(MyBrightness,0,0));
    stbdIEA.setPixelColor(23, stbdIEA.Color(MyBrightness,0,0));
    stbdIEA.show();
  }
  else if(V1B > 160)
  {
    stbdIEA.setPixelColor(18, stbdIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    stbdIEA.setPixelColor(19, stbdIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    stbdIEA.setPixelColor(20, stbdIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    stbdIEA.setPixelColor(21, stbdIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    stbdIEA.setPixelColor(22, stbdIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    stbdIEA.setPixelColor(23, stbdIEA.Color(MyBrightness,MyBrightness,MyBrightness));
    stbdIEA.show();
  }
  else
  {
    stbdIEA.setPixelColor(18, stbdIEA.Color(0,0,MyBrightness));
    stbdIEA.setPixelColor(19, stbdIEA.Color(0,0,MyBrightness));
    stbdIEA.setPixelColor(20, stbdIEA.Color(0,0,MyBrightness));
    stbdIEA.setPixelColor(21, stbdIEA.Color(0,0,MyBrightness));
    stbdIEA.setPixelColor(22, stbdIEA.Color(0,0,MyBrightness));
    stbdIEA.setPixelColor(23, stbdIEA.Color(0,0,MyBrightness));
    stbdIEA.show();
  }
  if(Disco)
  {
    theaterChaseRainbow_portIEA(50);
    theaterChaseRainbow_stbdIEA(50);
  }
  Disco = false;
}
void checkSerial()
{
  digitalWrite(ledBluePin, HIGH);
  test = "";
  
  while(Serial.available() > 0)  
  {
    test = Serial.readStringUntil('\n');
    //test = Serial.readString();
  }
//  Serial1.println(test);
  
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
    if(test2.substring(0,delimeter)=="Disco")
    {
      Disco = true; 
    }
    else if (test2.substring(0, delimeter) == "NULLIFY")
    {
      NULLIFY = int((test2.substring(delimeter + 1)).toFloat());
          Serial.println(" Got the NULL cmd over Serial...");
    }
    if(test2.substring(0,delimeter)=="V2A")
    {
      V2A = (test2.substring(delimeter+1)).toFloat();
    }
    else if(test2.substring(0,delimeter)=="V2B")
    {
      V2B = (test2.substring(delimeter+1)).toFloat();
    }
    else if(test2.substring(0,delimeter)=="V4A")
    {
      V4A = (test2.substring(delimeter+1)).toFloat();
    }
    else if(test2.substring(0,delimeter)=="V4B")
    {
      V4B = (test2.substring(delimeter+1)).toFloat();
    }
    else if(test2.substring(0,delimeter)=="V1A")
    {
      V1A = (test2.substring(delimeter+1)).toFloat();
    }
    else if(test2.substring(0,delimeter)=="V1B")
    {
      V1B = (test2.substring(delimeter+1)).toFloat();
    }
    else if(test2.substring(0,delimeter)=="V3A")
    {
      V3A = (test2.substring(delimeter+1)).toFloat();
    }
    else if(test2.substring(0,delimeter)=="V3B")
    {
      V3B = (test2.substring(delimeter+1)).toFloat();
    }
    //module Selection
    else if(test2.substring(0,delimeter)=="ISS")
    {
      //Serial1.println("----Module!------");
      module = (test2.substring(delimeter+1));
    }
  }
//  Serial1.println();
}

//module led functions
void allSet_module(uint32_t c, uint8_t wait) {
  for(uint16_t i=0; i<moduleLED.numPixels(); i++) 
  {
    moduleLED.setPixelColor(i, c);
    moduleLED.show();
    delay(wait);
  }
}
void theaterChaseRainbow_Module(uint8_t wait) {
  for (int j=0; j < 256; j++) {     // cycle all 256 colors in the wheel
    for (int q=0; q < 3; q++) {
      for (uint16_t i=0; i < moduleLED.numPixels(); i=i+3) {
        moduleLED.setPixelColor(i+q, Wheel_Module( (i+j) % MyBrightness));    //turn every third pixel on
      }
      moduleLED.show();

      delay(wait);

      for (uint16_t i=0; i < moduleLED.numPixels(); i=i+3) {
        moduleLED.setPixelColor(i+q, 0);        //turn every third pixel off
      }
    }
  }
}

// Input a value 0 to MyBrightness to get a color value.
// The colours are a transition r - g - b - back to r.
uint32_t Wheel_Module(byte WheelPos) {
  WheelPos = MyBrightness - WheelPos;
  if(WheelPos < 85) {
    return moduleLED.Color(MyBrightness - WheelPos * 3, 0, WheelPos * 3);
  }
  if(WheelPos < 170) {
    WheelPos -= 85;
    return moduleLED.Color(0, WheelPos * 3, MyBrightness - WheelPos * 3);
  }
  WheelPos -= 170;
  return moduleLED.Color(WheelPos * 3, MyBrightness - WheelPos * 3, 0);
}

//port IEA led functions
void allSet_portIEA(uint32_t c, uint8_t wait) {
  for(uint16_t i=0; i<portIEA.numPixels(); i++) 
  {
    portIEA.setPixelColor(i, c);
    portIEA.show();
    delay(wait);
  }
}

void theaterChaseRainbow_portIEA(uint8_t wait) {
  for (int j=0; j < 256; j++) {     // cycle all 256 colors in the wheel
    for (int q=0; q < 3; q++) {
      for (uint16_t i=0; i < portIEA.numPixels(); i=i+3) {
        portIEA.setPixelColor(i+q, Wheel_portIEA( (i+j) % MyBrightness));    //turn every third pixel on
      }
      portIEA.show();

      delay(wait);

      for (uint16_t i=0; i < portIEA.numPixels(); i=i+3) {
        portIEA.setPixelColor(i+q, 0);        //turn every third pixel off
      }
    }
  }
}

// Input a value 0 to MyBrightness to get a color value.
// The colours are a transition r - g - b - back to r.
uint32_t Wheel_portIEA(byte WheelPos) {
  WheelPos = MyBrightness - WheelPos;
  if(WheelPos < 85) {
    return portIEA.Color(MyBrightness - WheelPos * 3, 0, WheelPos * 3);
  }
  if(WheelPos < 170) {
    WheelPos -= 85;
    return portIEA.Color(0, WheelPos * 3, MyBrightness - WheelPos * 3);
  }
  WheelPos -= 170;
  return portIEA.Color(WheelPos * 3, MyBrightness - WheelPos * 3, 0);
}


//stbd IEA led functions
void allSet_stbdIEA(uint32_t c, uint8_t wait) {
  for(uint16_t i=0; i<stbdIEA.numPixels(); i++) 
  {
    stbdIEA.setPixelColor(i, c);
    stbdIEA.show();
    delay(wait);
  }
}

void theaterChaseRainbow_stbdIEA(uint8_t wait) {
  for (int j=0; j < 256; j++) {     // cycle all 256 colors in the wheel
    for (int q=0; q < 3; q++) {
      for (uint16_t i=0; i < stbdIEA.numPixels(); i=i+3) {
        stbdIEA.setPixelColor(i+q, Wheel_stbdIEA( (i+j) % MyBrightness));    //turn every third pixel on
      }
      stbdIEA.show();

      delay(wait);

      for (uint16_t i=0; i < stbdIEA.numPixels(); i=i+3) {
        stbdIEA.setPixelColor(i+q, 0);        //turn every third pixel off
      }
    }
  }
}

// Input a value 0 to MyBrightness to get a color value.
// The colours are a transition r - g - b - back to r.
uint32_t Wheel_stbdIEA(byte WheelPos) {
  WheelPos = MyBrightness - WheelPos;
  if(WheelPos < 85) {
    return stbdIEA.Color(MyBrightness - WheelPos * 3, 0, WheelPos * 3);
  }
  if(WheelPos < 170) {
    WheelPos -= 85;
    return stbdIEA.Color(0, WheelPos * 3, MyBrightness - WheelPos * 3);
  }
  WheelPos -= 170;
  return stbdIEA.Color(WheelPos * 3, MyBrightness - WheelPos * 3, 0);
}
