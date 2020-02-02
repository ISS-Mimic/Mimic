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
int oldEL = 0;
int oldXEL = 0;

void setup()
{
  pinMode(ledBluePin, OUTPUT);
  Serial.begin(9600);
  Serial.setTimeout(50);
  strip.begin();

  EL_servo.attach(10);
  XEL_servo.attach(9);

  EL_servo.write(map(0, -90, 90, 152, 30)); //custom mapping the servo motion to the sgant elevation motion
  XEL_servo.write(map(0, -90, 90, 28, 160)); //custom mapping the servo motion to the sgant cross elevation motion
  
  EL_servo.detach();
  XEL_servo.detach();
}

void loop()
{
  
  digitalWrite(ledBluePin, LOW);
  Serial.print("El ");
  Serial.println(EL);
  if(Serial.available())
  {
    checkSerial();
  }

  if(EL == 0 && XEL == 0)
  {
    Fire(55,120,5);
  }
  else
  {
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
  }

  if(EL != oldEL || XEL != oldXEL)
  {
    EL_servo.attach(10);
    XEL_servo.attach(9);
    
    
    int newEL = map(EL, -90, 90, 152, 30);
    int newXEL = map(XEL, -90, 90, 28, 160);
    
    EL_servo.write(newEL);
    XEL_servo.write(newXEL);
    delay(1000);
    
    EL_servo.detach();
    XEL_servo.detach();
    oldEL = EL;
    oldXEL = XEL;
  }
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
void Fire(int Cooling, int Sparking, int SpeedDelay) {
  static byte heat[60];
  int cooldown;
  
  // Step 1.  Cool down every cell a little
  for( int i = 0; i < strip.numPixels(); i++) {
    cooldown = random(0, ((Cooling * 10) / strip.numPixels()) + 2);
    
    if(cooldown>heat[i]) {
      heat[i]=0;
    } else {
      heat[i]=heat[i]-cooldown;
    }
  }
  
  // Step 2.  Heat from each cell drifts 'up' and diffuses a little
  for( int k= strip.numPixels() - 1; k >= 2; k--) {
    heat[k] = (heat[k - 1] + heat[k - 2] + heat[k - 2]) / 3;
  }
    
  // Step 3.  Randomly ignite new 'sparks' near the bottom
  if( random(255) < Sparking ) {
    int y = random(7);
    heat[y] = heat[y] + random(160,255);
    //heat[y] = random(160,255);
  }

  // Step 4.  Convert heat to LED colors
  for( int j = 0; j < strip.numPixels(); j++) {
    setPixelHeatColor(j, heat[j] );
  }

  strip.show();
  delay(SpeedDelay);
}

void setPixelHeatColor (int Pixel, byte temperature) {
  // Scale 'heat' down from 0-255 to 0-191
  byte t192 = round((temperature/255.0)*191);
 
  // calculate ramp up from
  byte heatramp = t192 & 0x3F; // 0..63
  heatramp <<= 2; // scale up to 0..252
 
  // figure out which third of the spectrum we're in:
  if( t192 > 0x80) {                     // hottest
    strip.setPixelColor(Pixel, random(0,256), random(0,256), random(0,256));
  } else if( t192 > 0x40 ) {             // middle
    strip.setPixelColor(Pixel, random(0,256), random(0,256), 0);
  } else {                               // coolest
    strip.setPixelColor(Pixel, heatramp, 0, 0);
  }
}
