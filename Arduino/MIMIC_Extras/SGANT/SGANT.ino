#include <Adafruit_NeoPixel.h>
#include <Servo.h>
#include <string.h>

//Connect USB port to Pi USB Port

Adafruit_NeoPixel strip = Adafruit_NeoPixel(16, 6, NEO_GRB + NEO_KHZ800);
Servo XEL_servo;
Servo EL_servo;
const int ledBluePin = 13;
String test;
int EL = 0;
int XEL = 0;
boolean Transmit = false;
int pos = 0;
int pos2 = 0;

void setup()
{
  pinMode(ledBluePin, OUTPUT);
  Serial.begin(9600);
  Serial.setTimeout(50);
  strip.begin();
}

void loop()
{
  digitalWrite(ledBluePin, LOW);

  if(Serial.available())
  {
    checkSerial();
  }

  if(Transmit)
  {
    allSet(strip.Color(50,50,50),10);
    strip.show();
  }
  else
  {
    allSet(strip.Color(50,0,0),10);
    strip.show();
  }
  
  EL_servo.attach(10);
  XEL_servo.attach(9);
  for (int x = pos; x <= EL; x += 1) 
  {
    EL_servo.write(x);
    delay(15);
  }
  for (int y = pos2; y <= XEL; y += 1) 
  {
    XEL_servo.write(y);
    delay(15);
  }
  pos = EL;
  pos2 = XEL;
  EL_servo.detach();
  XEL_servo.detach();
}

void checkSerial()
{
  digitalWrite(ledBluePin, HIGH);
  test = "";
  
  while(Serial.available())  
  {
    test = Serial.readString();
  }
  //Serial1.println(test);
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
    if(test2.substring(0,delimeter)=="SGANT_El_deg")
    {
      EL = (test2.substring(delimeter+1)).toInt();
    }  
    else if(test2.substring(0,delimeter)=="SGANT_xEl_deg")
    {
      XEL = (test2.substring(delimeter+1)).toInt();
    }  
    else if(test2.substring(0,delimeter)=="SGANT_Transmit")
    {
      Transmit = (test2.substring(delimeter+1)).toInt();
    }
  }
}
void allSet(uint32_t c, uint8_t wait) 
{
  for(uint16_t i=0; i<strip.numPixels(); i++) 
  {
    strip.setPixelColor(i, c);
    strip.show();
    delay(wait);
  }
}
