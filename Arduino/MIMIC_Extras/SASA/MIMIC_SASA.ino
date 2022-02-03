#include <Adafruit_TiCoServo.h>
#include <known_16bit_timers.h>

#include <Adafruit_NeoPixel.h>
#include <string.h>
Adafruit_NeoPixel LGA = Adafruit_NeoPixel(1, 6, NEO_GRB + NEO_KHZ800);
Adafruit_NeoPixel HGA = Adafruit_NeoPixel(7, 5, NEO_GRB + NEO_KHZ800);
Adafruit_TiCoServo AZ_Servo;
Adafruit_TiCoServo EL_Servo;

String readData;

int pos = 0;
int EL = 0;
int AZ = 0;
int oldEL = 0;
int oldAZ = 0;
int oldnewEL = 0;
int oldnewAZ = 0;

boolean transmit = false;

void setup()
{
  Serial.begin(9600);
  Serial.setTimeout(50);
  LGA.begin();
  HGA.begin();
  allSet_HGA(HGA.Color(255,255,0),0);
  allSet_LGA(LGA.Color(255,255,0),0);
  LGA.show();
  HGA.show();
  AZ_Servo.attach(11);
  EL_Servo.attach(12);

  EL_Servo.write(0);
  delay(15);
  AZ_Servo.write(0);
  delay(2000);
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
  //Serial2.println(readData);
  
  //Split up string into substrings separated by spaces
  //Go through each substring and extract data
  while((str = strtok_r(p," ",&p))!=NULL)
  {
    readData2 = String(str);
    //Serial.println(readData2);
    delimeter = readData2.indexOf('=');
    if(readData2.substring(0,delimeter)=="SASA_Xmit")
    {
      transmit = (readData2.substring(delimeter+1)).toInt(); //ex SASA_Xmit=1
    }
    if(readData2.substring(0,delimeter)=="SASA_EL")
    {
      EL = (readData2.substring(delimeter+1)).toInt(); //ex SASA_EL=45
    }
    else if(readData2.substring(0,delimeter)=="SASA_AZ")
    {
      AZ = (readData2.substring(delimeter+1)).toInt(); //ex SASA_AZ=90
    }
  }

  if(transmit) //set neopixels to white is SASA is transmitting
  {
    allSet_LGA(LGA.Color(255,255,255),0);
    allSet_HGA(HGA.Color(255,255,255),0);
    HGA.show();
    LGA.show();
  }
  else //set neopixels to red if not transmitting
  {  
    allSet_LGA(LGA.Color(255,0,0),0);
    allSet_HGA(HGA.Color(255,0,0),0);
    HGA.show();
    LGA.show();
  }
  //Serial.println(AZ);
  if(EL != oldEL || AZ != oldAZ)
  {
    if(EL > 135)
    {
      EL = 135;
    }
    else if(EL < 0)
    {
      EL = 0;
    }
    if(AZ > 130)
    {
      AZ = 130;
    }
    else if(AZ < -130)
    {
      AZ = -130;
    }

    int newEL = map(EL, 0, 135, 90, 0);
    int newAZ = map(AZ, -130, 130, 270, 0);
    //int newEL = EL;
    //int newAZ = AZ;


    if(newEL - oldnewEL > 0)
    {
      for (pos = oldnewEL; pos <= newEL; pos += 1) 
      {
        //Serial.println("turning");
        EL_Servo.write(pos);
        delay(15);
      }
    }
    else
    {
      for (pos = oldnewEL; pos >= newEL; pos -= 1) 
      {
        //Serial.println("turning");
        EL_Servo.write(pos);
        delay(15);
      }
    }
    
    if(newAZ - oldnewAZ > 0)
    {
      for (pos = oldnewAZ; pos <= newAZ; pos += 1) 
      {
        AZ_Servo.write(pos);
        delay(15);
      }
    }
    else
    {
      for (pos = oldnewAZ; pos >= newAZ; pos -= 1) 
      {
        AZ_Servo.write(pos);
        delay(15);
      }
    }
    
    oldnewEL = newEL;
    oldnewAZ = newAZ;
    oldEL = EL;
    oldAZ = AZ;
    
  }
  
}


void allSet_LGA(uint32_t c, uint8_t wait) 
{
  for(uint16_t i=0; i<LGA.numPixels(); i++) 
  {
    LGA.setPixelColor(i, c);
    LGA.show();
    delay(wait);
  }
}

void theaterChaseRainbow_LGA(uint8_t wait) {
  for (int j=0; j < 256; j++) {     // cycle all 256 colors in the wheEL
    for (int q=0; q < 3; q++) {
      for (uint16_t i=0; i < LGA.numPixels(); i=i+3) {
        LGA.setPixelColor(i+q, Wheel_LGA( (i+j) % 255));    //turn every third pixEL on
      }
      LGA.show();

      delay(wait);

      for (uint16_t i=0; i < LGA.numPixels(); i=i+3) {
        LGA.setPixelColor(i+q, 0);        //turn every third pixEL off
      }
    }
  }
}

// Input a value 0 to 255 to get a color value.
// The colours are a transition r - g - b - back to r.
uint32_t Wheel_LGA(byte WheelPos) {
  WheelPos = 255 - WheelPos;
  if(WheelPos < 85) {
    return LGA.Color(255 - WheelPos * 3, 0, WheelPos * 3);
  }
  if(WheelPos < 170) {
    WheelPos -= 85;
    return LGA.Color(0, WheelPos * 3, 255 - WheelPos * 3);
  }
  WheelPos -= 170;
  return LGA.Color(WheelPos * 3, 255 - WheelPos * 3, 0);
}


//stbd IEA led functions
void allSet_HGA(uint32_t c, uint8_t wait) 
{
  for(uint16_t i=0; i<HGA.numPixels(); i++) 
  {
    HGA.setPixelColor(i, c);
    HGA.show();
    delay(wait);
  }
}

void theaterChaseRainbow_HGA(uint8_t wait) 
{
  for (int j=0; j < 256; j++) {     // cycle all 256 colors in the wheEL
    for (int q=0; q < 3; q++) {
      for (uint16_t i=0; i < HGA.numPixels(); i=i+3) {
        HGA.setPixelColor(i+q, Wheel_HGA( (i+j) % 255));    //turn every third pixEL on
      }
      HGA.show();

      delay(wait);

      for (uint16_t i=0; i < HGA.numPixels(); i=i+3) {
        HGA.setPixelColor(i+q, 0);        //turn every third pixEL off
      }
    }
  }
}
void theaterChaseRainbow_disco(uint8_t wait) {
  for (int j=0; j < 256; j++) {     // cycle all 256 colors in the wheEL
    for (int q=0; q < 3; q++) {
      for (uint16_t i=0; i < HGA.numPixels(); i=i+3) {
        HGA.setPixelColor(i+q, Wheel_HGA( (i+j) % 255));    //turn every third pixEL on
        LGA.setPixelColor(i+q, Wheel_LGA( (i+j) % 255));    //turn every third pixEL on
      }
      HGA.show();
      LGA.show();

      delay(wait);

      for (uint16_t i=0; i < HGA.numPixels(); i=i+3) {
        HGA.setPixelColor(i+q, 0);        //turn every third pixEL off
        LGA.setPixelColor(i+q, 0);        //turn every third pixEL off
      }
    }
  }
}
// Input a value 0 to 255 to get a color value.
// The colours are a transition r - g - b - back to r.
uint32_t Wheel_HGA(byte WheelPos) 
{
  WheelPos = 255 - WheelPos;
  if(WheelPos < 85) 
  {
    return HGA.Color(255 - WheelPos * 3, 0, WheelPos * 3);
  }
  if(WheelPos < 170) 
  {
    WheelPos -= 85;
    return HGA.Color(0, WheelPos * 3, 255 - WheelPos * 3);
  }
  WheelPos -= 170;
  return HGA.Color(WheelPos * 3, 255 - WheelPos * 3, 0);
}
