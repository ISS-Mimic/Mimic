#include <Adafruit_NeoPixel.h>
#include <string.h>

#define Pin_1A 6
#define Pin_1B 7
#define Pin_3A 8
#define Pin_3B 9
Adafruit_NeoPixel channel_1A = Adafruit_NeoPixel(6, Pin_1A, NEO_GRB + NEO_KHZ800);
Adafruit_NeoPixel channel_1B = Adafruit_NeoPixel(6, Pin_1B, NEO_GRB + NEO_KHZ800);
Adafruit_NeoPixel channel_3A = Adafruit_NeoPixel(6, Pin_3A, NEO_GRB + NEO_KHZ800);
Adafruit_NeoPixel channel_3B = Adafruit_NeoPixel(6, Pin_3B, NEO_GRB + NEO_KHZ800);

double minimum = 30;
double maximum = 70;
double ratio;
double current1A = 0.0;
double current1B = 0.0;
double current3A = 0.0;
double current3B = 0.0;
String test;
boolean sparkle = false;
unsigned long sparkletime = 0.0;

void setup() 
{
  channel_1A.begin(); 
  channel_1B.begin();
  channel_3A.begin();
  channel_3B.begin();
  channel_1A.setBrightness(155); 
  channel_1B.setBrightness(155);
  channel_3A.setBrightness(155);
  channel_3B.setBrightness(155);
  channel_1A.show();
  channel_1B.show();
  channel_3A.show();
  channel_3B.show();
//  Serial.begin(9600);
  Serial.begin(115200);
  Serial.setTimeout(50);
}

void loop() 
{
  if(Serial.available())
  {
    checkSerial();
  }
  if(millis()-sparkletime > 5000)
  {
    sparkle = true;
    sparkletime = millis();
  }
  else
  {
    sparkle = false;
  }
  mapRGB(current1A,1,sparkle);
  mapRGB(current1B,2,sparkle);
  mapRGB(current3A,3,sparkle);
  mapRGB(current3B,4,sparkle);
}

void mapRGB(float value, int strip, boolean sparkle)
{
  int b = 0;
  int r = 0;
  int g = 0;
  ratio = 2*(value-minimum)/(maximum-minimum);
  b = (int)(max(0,255*(1-ratio)));
  r = (int)(max(0,255*(ratio-1)));
  g = (255-b-r);
  if(strip==1)
  {
    if(sparkle)
    {
      set1A(channel_1A.Color(r/10,g/10,b/10),10);  
    }
    else
    {
      set1A(channel_1A.Color(r,g,b),10);
    }
  }
  else if(strip==2)
  {
    if(sparkle)
    {
      set1B(channel_1B.Color(r/10,g/10,b/10),10);  
    }
    else
    {
      set1B(channel_1B.Color(r,g,b),10);
    }
  }
  else if(strip==3)
  {
    if(sparkle)
    {
      set3A(channel_3A.Color(r/10,g/10,b/10),10);  
    }
    else
    {
      set3A(channel_3A.Color(r,g,b),10);
    }
  }
  else if(strip==4)
  {
    if(sparkle)
    {
      set3B(channel_3B.Color(r/10,g/10,b/10),10);  
    }
    else
    {
      set3B(channel_3B.Color(r,g,b),10);
    }
  }
}

void checkSerial()
{
  test = "";
  
  while(Serial.available())  
  {
    test = Serial.readString();
  }
  //Serial.println(test);
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
    if(test2.substring(0,delimeter)=="Current1A")
    {
      current1A = (test2.substring(delimeter+1)).toFloat();
      current1A = abs(current1A);
    }  
    else if(test2.substring(0,delimeter)=="Current1B")
    {
      current1B = (test2.substring(delimeter+1)).toFloat();
      current1B = abs(current1B);
    }  
    else if(test2.substring(0,delimeter)=="Current3A")
    {
      current3A = (test2.substring(delimeter+1)).toFloat();
      current3A = abs(current3A);
    } 
    else if(test2.substring(0,delimeter)=="Current3B")
    {
      current3B = (test2.substring(delimeter+1)).toFloat();
      current3B = abs(current3B);
    }
  }
  //Serial.println(current1A);
  //Serial.println(current1B);
  //Serial.println(current3A);
  //Serial.println(current3B);
}

void set1A(uint32_t c, uint8_t wait) 
{
  for(uint16_t i=0; i<channel_1A.numPixels(); i++) 
  {
    channel_1A.setPixelColor(i, c);
    channel_1A.show();  
    delay(wait);
  }
}
void set1B(uint32_t c, uint8_t wait) 
{
  for(uint16_t i=0; i<channel_1B.numPixels(); i++) 
  {
    channel_1B.setPixelColor(i, c);
    channel_1B.show();  
    delay(wait);
  }
}
void set3A(uint32_t c, uint8_t wait) 
{
  for(uint16_t i=0; i<channel_3A.numPixels(); i++) 
  {
    channel_3A.setPixelColor(i, c);
    channel_3A.show();  
    delay(wait);
  }
}
void set3B(uint32_t c, uint8_t wait) 
{
  for(uint16_t i=0; i<channel_3B.numPixels(); i++) 
  {
    channel_3B.setPixelColor(i, c);
    channel_3B.show();  
    delay(wait);
  }
}
