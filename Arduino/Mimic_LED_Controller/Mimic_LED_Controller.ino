#include <Adafruit_NeoPixel.h>
#include <string.h>
//Connect USB port to Pi USB Port
//For serial debugging - connect to the RX1 and TX1 pins
Adafruit_NeoPixel stbdIEA = Adafruit_NeoPixel(24, 5, NEO_GRB + NEO_KHZ800);
Adafruit_NeoPixel portIEA = Adafruit_NeoPixel(24, 6, NEO_GRB + NEO_KHZ800);
Adafruit_NeoPixel moduleLED = Adafruit_NeoPixel(16, 7, NEO_GRB + NEO_KHZ800);

String readData;

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
  Serial.begin(9600);
  Serial.setTimeout(50);
  portIEA.begin();
  stbdIEA.begin();
  moduleLED.begin();
  allSet_stbdIEA(stbdIEA.Color(0,255,0),0);
  allSet_portIEA(portIEA.Color(0,255,0),0);
  portIEA.show();
  stbdIEA.show();
  allSet_module(moduleLED.Color(255,0,0),5);
  moduleLED.show();
}

void loop()
{
  //Process any incoming serial data
  readData = "";
  if(Serial.available() > 0)
  {
    readData = Serial.readString();
  }
  delay(100);
  Serial.flush();
  
  char sz[readData.length() + 1];
  char copy[readData.length() + 1];
  strcpy(sz, readData.c_str());  
  char *p = sz;
  char *str;
  int delimeter = 0;
  String readData2 = ""; 
  Serial2.println(readData);
  
  //Split up string into substrings separated by spaces
  //Go through each substring and extract data
  while((str = strtok_r(p," ",&p))!=NULL)
  {
    readData2 = String(str);
    //Serial.println(readData2);
    delimeter = readData2.indexOf('=');
    if(readData2.substring(0,delimeter)=="Disco")
    {
      Disco = true; 
    }
    else if (readData2.substring(0, delimeter) == "NULLIFY")
    {
      NULLIFY = int((readData2.substring(delimeter + 1)).toFloat());
    }
    if(readData2.substring(0,delimeter)=="V2A")
    {
      V2A = (readData2.substring(delimeter+1)).toFloat();
    }
    else if(readData2.substring(0,delimeter)=="V2B")
    {
      V2B = (readData2.substring(delimeter+1)).toFloat();
    }
    else if(readData2.substring(0,delimeter)=="V4A")
    {
      V4A = (readData2.substring(delimeter+1)).toFloat();
    }
    else if(readData2.substring(0,delimeter)=="V4B")
    {
      V4B = (readData2.substring(delimeter+1)).toFloat();
    }
    else if(readData2.substring(0,delimeter)=="V1A")
    {
      V1A = (readData2.substring(delimeter+1)).toFloat();
    }
    else if(readData2.substring(0,delimeter)=="V1B")
    {
      V1B = (readData2.substring(delimeter+1)).toFloat();
    }
    else if(readData2.substring(0,delimeter)=="V3A")
    {
      V3A = (readData2.substring(delimeter+1)).toFloat();
    }
    else if(readData2.substring(0,delimeter)=="V3B")
    {
      V3B = (readData2.substring(delimeter+1)).toFloat();
    }
    //module Selection
    else if(readData2.substring(0,delimeter)=="ISS")
    {
      module = String((readData2.substring(delimeter+1)));
    }
  }

  module.trim(); //trim whitespace off serial data

  if(module == "SM")
  {
    moduleLED.setPixelColor(0, moduleLED.Color(255,255,255));
  }
  else if(module == "FGB")
  {
    moduleLED.setPixelColor(1, moduleLED.Color(255,255,255));
  }
  else if(module == "Node1")
  {
    moduleLED.setPixelColor(2, moduleLED.Color(255,255,255));
  }
  else if(module == "Node2")
  {
    moduleLED.setPixelColor(6, moduleLED.Color(255,255,255));
  }
  else if(module == "Node3")
  {
    moduleLED.setPixelColor(4, moduleLED.Color(255,255,255));
  }
  else if(module == "AL")
  {
    moduleLED.setPixelColor(3, moduleLED.Color(255,255,255));
  }
  else if(module == "USL")
  {
    moduleLED.setPixelColor(5, moduleLED.Color(255,255,255));
  }
  else if(module == "Col")
  {
    moduleLED.setPixelColor(7, moduleLED.Color(255,255,255));
  }
  else if(module == "JEM")
  {
    moduleLED.setPixelColor(8, moduleLED.Color(255,255,255));
  }
  else
  {
    allSet_module(moduleLED.Color(0,0,0),0);
  }
  moduleLED.show();
  
  if(V2A < 151.5)
  {
    portIEA.setPixelColor(0, portIEA.Color(255,0,0));
    portIEA.setPixelColor(1, portIEA.Color(255,0,0));
    portIEA.setPixelColor(2, portIEA.Color(255,0,0));
    portIEA.setPixelColor(3, portIEA.Color(255,0,0));
    portIEA.setPixelColor(4, portIEA.Color(255,0,0));
    portIEA.setPixelColor(5, portIEA.Color(255,0,0));
    portIEA.show();
  }
  else if(V2A > 160)
  {
    portIEA.setPixelColor(0, portIEA.Color(255,255,255));
    portIEA.setPixelColor(1, portIEA.Color(255,255,255));
    portIEA.setPixelColor(2, portIEA.Color(255,255,255));
    portIEA.setPixelColor(3, portIEA.Color(255,255,255));
    portIEA.setPixelColor(4, portIEA.Color(255,255,255));
    portIEA.setPixelColor(5, portIEA.Color(255,255,255));
    portIEA.show();
  }
  else
  {
    portIEA.setPixelColor(0, portIEA.Color(0,0,255));
    portIEA.setPixelColor(1, portIEA.Color(0,0,255));
    portIEA.setPixelColor(2, portIEA.Color(0,0,255));
    portIEA.setPixelColor(3, portIEA.Color(0,0,255));
    portIEA.setPixelColor(4, portIEA.Color(0,0,255));
    portIEA.setPixelColor(5, portIEA.Color(0,0,255));
    portIEA.show();
  }
  
  if(V4A < 151.5)
  {
    portIEA.setPixelColor(6, portIEA.Color(255,0,0));
    portIEA.setPixelColor(7, portIEA.Color(255,0,0));
    portIEA.setPixelColor(8, portIEA.Color(255,0,0));
    portIEA.setPixelColor(9, portIEA.Color(255,0,0));
    portIEA.setPixelColor(10, portIEA.Color(255,0,0));
    portIEA.setPixelColor(11, portIEA.Color(255,0,0));
    portIEA.show();
  }
  else if(V4A > 160)
  {
    portIEA.setPixelColor(6, portIEA.Color(255,255,255));
    portIEA.setPixelColor(7, portIEA.Color(255,255,255));
    portIEA.setPixelColor(8, portIEA.Color(255,255,255));
    portIEA.setPixelColor(9, portIEA.Color(255,255,255));
    portIEA.setPixelColor(10, portIEA.Color(255,255,255));
    portIEA.setPixelColor(11, portIEA.Color(255,255,255));
    portIEA.show();
  }
  else
  {
    portIEA.setPixelColor(6, portIEA.Color(0,0,255));
    portIEA.setPixelColor(7, portIEA.Color(0,0,255));
    portIEA.setPixelColor(8, portIEA.Color(0,0,255));
    portIEA.setPixelColor(9, portIEA.Color(0,0,255));
    portIEA.setPixelColor(10, portIEA.Color(0,0,255));
    portIEA.setPixelColor(11, portIEA.Color(0,0,255));
    portIEA.show();
  }

  if(V4B < 151.5)
  {
    portIEA.setPixelColor(12, portIEA.Color(255,0,0));
    portIEA.setPixelColor(13, portIEA.Color(255,0,0));
    portIEA.setPixelColor(14, portIEA.Color(255,0,0));
    portIEA.setPixelColor(15, portIEA.Color(255,0,0));
    portIEA.setPixelColor(16, portIEA.Color(255,0,0));
    portIEA.setPixelColor(17, portIEA.Color(255,0,0));
    portIEA.show();
  }
  else if(V4B > 160)
  {
    portIEA.setPixelColor(12, portIEA.Color(255,255,255));
    portIEA.setPixelColor(13, portIEA.Color(255,255,255));
    portIEA.setPixelColor(14, portIEA.Color(255,255,255));
    portIEA.setPixelColor(15, portIEA.Color(255,255,255));
    portIEA.setPixelColor(16, portIEA.Color(255,255,255));
    portIEA.setPixelColor(17, portIEA.Color(255,255,255));
    portIEA.show();
  }
  else
  {
    portIEA.setPixelColor(12, portIEA.Color(0,0,255));
    portIEA.setPixelColor(13, portIEA.Color(0,0,255));
    portIEA.setPixelColor(14, portIEA.Color(0,0,255));
    portIEA.setPixelColor(15, portIEA.Color(0,0,255));
    portIEA.setPixelColor(16, portIEA.Color(0,0,255));
    portIEA.setPixelColor(17, portIEA.Color(0,0,255));
    portIEA.show();
  }

  if(V2B < 151.5)
  {
    portIEA.setPixelColor(18, portIEA.Color(255,0,0));
    portIEA.setPixelColor(19, portIEA.Color(255,0,0));
    portIEA.setPixelColor(20, portIEA.Color(255,0,0));
    portIEA.setPixelColor(21, portIEA.Color(255,0,0));
    portIEA.setPixelColor(22, portIEA.Color(255,0,0));
    portIEA.setPixelColor(23, portIEA.Color(255,0,0));
    portIEA.show();
  }
  else if(V2B > 160)
  {
    portIEA.setPixelColor(18, portIEA.Color(255,255,255));
    portIEA.setPixelColor(19, portIEA.Color(255,255,255));
    portIEA.setPixelColor(20, portIEA.Color(255,255,255));
    portIEA.setPixelColor(21, portIEA.Color(255,255,255));
    portIEA.setPixelColor(22, portIEA.Color(255,255,255));
    portIEA.setPixelColor(23, portIEA.Color(255,255,255));
    portIEA.show();
  }
  else
  {
    portIEA.setPixelColor(18, portIEA.Color(0,0,255));
    portIEA.setPixelColor(19, portIEA.Color(0,0,255));
    portIEA.setPixelColor(20, portIEA.Color(0,0,255));
    portIEA.setPixelColor(21, portIEA.Color(0,0,255));
    portIEA.setPixelColor(22, portIEA.Color(0,0,255));
    portIEA.setPixelColor(23, portIEA.Color(0,0,255));
    portIEA.show();
  }
  if(V1A < 151.5)
  {
    stbdIEA.setPixelColor(0, stbdIEA.Color(255,0,0));
    stbdIEA.setPixelColor(1, stbdIEA.Color(255,0,0));
    stbdIEA.setPixelColor(2, stbdIEA.Color(255,0,0));
    stbdIEA.setPixelColor(3, stbdIEA.Color(255,0,0));
    stbdIEA.setPixelColor(4, stbdIEA.Color(255,0,0));
    stbdIEA.setPixelColor(5, stbdIEA.Color(255,0,0));
    stbdIEA.show();
  }
  else if(V1A > 160)
  {
    stbdIEA.setPixelColor(0, stbdIEA.Color(255,255,255));
    stbdIEA.setPixelColor(1, stbdIEA.Color(255,255,255));
    stbdIEA.setPixelColor(2, stbdIEA.Color(255,255,255));
    stbdIEA.setPixelColor(3, stbdIEA.Color(255,255,255));
    stbdIEA.setPixelColor(4, stbdIEA.Color(255,255,255));
    stbdIEA.setPixelColor(5, stbdIEA.Color(255,255,255));
    stbdIEA.show();
  }
  else
  {
    stbdIEA.setPixelColor(0, stbdIEA.Color(0,0,255));
    stbdIEA.setPixelColor(1, stbdIEA.Color(0,0,255));
    stbdIEA.setPixelColor(2, stbdIEA.Color(0,0,255));
    stbdIEA.setPixelColor(3, stbdIEA.Color(0,0,255));
    stbdIEA.setPixelColor(4, stbdIEA.Color(0,0,255));
    stbdIEA.setPixelColor(5, stbdIEA.Color(0,0,255));
    stbdIEA.show();
  }
  
  if(V3A < 151.5)
  {
    stbdIEA.setPixelColor(6, stbdIEA.Color(255,0,0));
    stbdIEA.setPixelColor(7, stbdIEA.Color(255,0,0));
    stbdIEA.setPixelColor(8, stbdIEA.Color(255,0,0));
    stbdIEA.setPixelColor(9, stbdIEA.Color(255,0,0));
    stbdIEA.setPixelColor(10, stbdIEA.Color(255,0,0));
    stbdIEA.setPixelColor(11, stbdIEA.Color(255,0,0));
    stbdIEA.show();
  }
  else if(V3A > 160)
  {
    stbdIEA.setPixelColor(6, stbdIEA.Color(255,255,255));
    stbdIEA.setPixelColor(7, stbdIEA.Color(255,255,255));
    stbdIEA.setPixelColor(8, stbdIEA.Color(255,255,255));
    stbdIEA.setPixelColor(9, stbdIEA.Color(255,255,255));
    stbdIEA.setPixelColor(10, stbdIEA.Color(255,255,255));
    stbdIEA.setPixelColor(11, stbdIEA.Color(255,255,255));
    stbdIEA.show();
  }
  else
  {
    stbdIEA.setPixelColor(6, stbdIEA.Color(0,0,255));
    stbdIEA.setPixelColor(7, stbdIEA.Color(0,0,255));
    stbdIEA.setPixelColor(8, stbdIEA.Color(0,0,255));
    stbdIEA.setPixelColor(9, stbdIEA.Color(0,0,255));
    stbdIEA.setPixelColor(10, stbdIEA.Color(0,0,255));
    stbdIEA.setPixelColor(11, stbdIEA.Color(0,0,255));
    stbdIEA.show();
  }

  if(V3B < 151.5)
  {
    stbdIEA.setPixelColor(12, stbdIEA.Color(255,0,0));
    stbdIEA.setPixelColor(13, stbdIEA.Color(255,0,0));
    stbdIEA.setPixelColor(14, stbdIEA.Color(255,0,0));
    stbdIEA.setPixelColor(15, stbdIEA.Color(255,0,0));
    stbdIEA.setPixelColor(16, stbdIEA.Color(255,0,0));
    stbdIEA.setPixelColor(17, stbdIEA.Color(255,0,0));
    stbdIEA.show();
  }
  else if(V3B > 160)
  {
    stbdIEA.setPixelColor(12, stbdIEA.Color(255,255,255));
    stbdIEA.setPixelColor(13, stbdIEA.Color(255,255,255));
    stbdIEA.setPixelColor(14, stbdIEA.Color(255,255,255));
    stbdIEA.setPixelColor(15, stbdIEA.Color(255,255,255));
    stbdIEA.setPixelColor(16, stbdIEA.Color(255,255,255));
    stbdIEA.setPixelColor(17, stbdIEA.Color(255,255,255));
    stbdIEA.show();
  }
  else
  {
    stbdIEA.setPixelColor(12, stbdIEA.Color(0,0,255));
    stbdIEA.setPixelColor(13, stbdIEA.Color(0,0,255));
    stbdIEA.setPixelColor(14, stbdIEA.Color(0,0,255));
    stbdIEA.setPixelColor(15, stbdIEA.Color(0,0,255));
    stbdIEA.setPixelColor(16, stbdIEA.Color(0,0,255));
    stbdIEA.setPixelColor(17, stbdIEA.Color(0,0,255));
    stbdIEA.show();
  }

  if(V1B < 151.5)
  {
    stbdIEA.setPixelColor(18, stbdIEA.Color(255,0,0));
    stbdIEA.setPixelColor(19, stbdIEA.Color(255,0,0));
    stbdIEA.setPixelColor(20, stbdIEA.Color(255,0,0));
    stbdIEA.setPixelColor(21, stbdIEA.Color(255,0,0));
    stbdIEA.setPixelColor(22, stbdIEA.Color(255,0,0));
    stbdIEA.setPixelColor(23, stbdIEA.Color(255,0,0));
    stbdIEA.show();
  }
  else if(V1B > 160)
  {
    stbdIEA.setPixelColor(18, stbdIEA.Color(255,255,255));
    stbdIEA.setPixelColor(19, stbdIEA.Color(255,255,255));
    stbdIEA.setPixelColor(20, stbdIEA.Color(255,255,255));
    stbdIEA.setPixelColor(21, stbdIEA.Color(255,255,255));
    stbdIEA.setPixelColor(22, stbdIEA.Color(255,255,255));
    stbdIEA.setPixelColor(23, stbdIEA.Color(255,255,255));
    stbdIEA.show();
  }
  else
  {
    stbdIEA.setPixelColor(18, stbdIEA.Color(0,0,255));
    stbdIEA.setPixelColor(19, stbdIEA.Color(0,0,255));
    stbdIEA.setPixelColor(20, stbdIEA.Color(0,0,255));
    stbdIEA.setPixelColor(21, stbdIEA.Color(0,0,255));
    stbdIEA.setPixelColor(22, stbdIEA.Color(0,0,255));
    stbdIEA.setPixelColor(23, stbdIEA.Color(0,0,255));
    stbdIEA.show();
  }
  if(Disco)
  {
    theaterChaseRainbow_disco(50);
  }
  Disco = false;
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
        moduleLED.setPixelColor(i+q, Wheel_Module( (i+j) % 255));    //turn every third pixel on
      }
      moduleLED.show();

      delay(wait);

      for (uint16_t i=0; i < moduleLED.numPixels(); i=i+3) {
        moduleLED.setPixelColor(i+q, 0);        //turn every third pixel off
      }
    }
  }
}

// Input a value 0 to 255 to get a color value.
// The colours are a transition r - g - b - back to r.
uint32_t Wheel_Module(byte WheelPos) {
  WheelPos = 255 - WheelPos;
  if(WheelPos < 85) {
    return moduleLED.Color(255 - WheelPos * 3, 0, WheelPos * 3);
  }
  if(WheelPos < 170) {
    WheelPos -= 85;
    return moduleLED.Color(0, WheelPos * 3, 255 - WheelPos * 3);
  }
  WheelPos -= 170;
  return moduleLED.Color(WheelPos * 3, 255 - WheelPos * 3, 0);
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
        portIEA.setPixelColor(i+q, Wheel_portIEA( (i+j) % 255));    //turn every third pixel on
      }
      portIEA.show();

      delay(wait);

      for (uint16_t i=0; i < portIEA.numPixels(); i=i+3) {
        portIEA.setPixelColor(i+q, 0);        //turn every third pixel off
      }
    }
  }
}

// Input a value 0 to 255 to get a color value.
// The colours are a transition r - g - b - back to r.
uint32_t Wheel_portIEA(byte WheelPos) {
  WheelPos = 255 - WheelPos;
  if(WheelPos < 85) {
    return portIEA.Color(255 - WheelPos * 3, 0, WheelPos * 3);
  }
  if(WheelPos < 170) {
    WheelPos -= 85;
    return portIEA.Color(0, WheelPos * 3, 255 - WheelPos * 3);
  }
  WheelPos -= 170;
  return portIEA.Color(WheelPos * 3, 255 - WheelPos * 3, 0);
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
        stbdIEA.setPixelColor(i+q, Wheel_stbdIEA( (i+j) % 255));    //turn every third pixel on
      }
      stbdIEA.show();

      delay(wait);

      for (uint16_t i=0; i < stbdIEA.numPixels(); i=i+3) {
        stbdIEA.setPixelColor(i+q, 0);        //turn every third pixel off
      }
    }
  }
}
void theaterChaseRainbow_disco(uint8_t wait) {
  for (int j=0; j < 256; j++) {     // cycle all 256 colors in the wheel
    for (int q=0; q < 3; q++) {
      for (uint16_t i=0; i < stbdIEA.numPixels(); i=i+3) {
        stbdIEA.setPixelColor(i+q, Wheel_stbdIEA( (i+j) % 255));    //turn every third pixel on
        portIEA.setPixelColor(i+q, Wheel_portIEA( (i+j) % 255));    //turn every third pixel on
      }
      stbdIEA.show();
      portIEA.show();

      delay(wait);

      for (uint16_t i=0; i < stbdIEA.numPixels(); i=i+3) {
        stbdIEA.setPixelColor(i+q, 0);        //turn every third pixel off
        portIEA.setPixelColor(i+q, 0);        //turn every third pixel off
      }
    }
  }
}
// Input a value 0 to 255 to get a color value.
// The colours are a transition r - g - b - back to r.
uint32_t Wheel_stbdIEA(byte WheelPos) {
  WheelPos = 255 - WheelPos;
  if(WheelPos < 85) {
    return stbdIEA.Color(255 - WheelPos * 3, 0, WheelPos * 3);
  }
  if(WheelPos < 170) {
    WheelPos -= 85;
    return stbdIEA.Color(0, WheelPos * 3, 255 - WheelPos * 3);
  }
  WheelPos -= 170;
  return stbdIEA.Color(WheelPos * 3, 255 - WheelPos * 3, 0);
}
