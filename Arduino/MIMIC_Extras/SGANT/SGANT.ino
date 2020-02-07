#include <FastLED.h>
#include <Servo.h>
#include <string.h>

#define NUM_LEDS 32
#define DATA_PIN 6
#define BRIGHTNESS  200
#define FRAMES_PER_SECOND 60
CRGBPalette16 gPal;
CRGB leds[NUM_LEDS];
//Connect USB port to Pi USB Port

//Adafruit_NeoPixel strip = Adafruit_NeoPixel(32, 6, NEO_GRB + NEO_KHZ800);
Servo XEL_servo;
Servo EL_servo;
bool gReverseDirection = false;
const int ledBluePin = 13;
String test;
int EL = 0;
int XEL = 0;
boolean Transmit = false;
int pos = 0;
int pos2 = 0;
int oldEL = 0;
int oldXEL = 0;
int oldnewEL = 0;
int oldnewXEL = 0;
int index = 0;

uint32_t stickone[] = {0,1,2,3,4,5,6,7};
uint32_t sticktwo[] = {15,14,13,12,11,10,9,8};
uint32_t stickthree[] = {16,17,18,19,20,21,22,23};
uint32_t stickfour[] = {31,30,29,28,27,26,25,24};

int fadeAmount = 255;  // Set the amount to fade I usually do 5, 10, 15, 20, 25 etc even up to 255.
int brightness = 0;

void setup()
{
  pinMode(ledBluePin, OUTPUT);
  Serial.begin(9600);
  Serial.setTimeout(50);
  FastLED.addLeds<NEOPIXEL, DATA_PIN>(leds, NUM_LEDS);
  gPal = CRGBPalette16( CRGB::Black, CRGB::Red, CRGB::Yellow, CRGB::White);
  allSet(CRGB::Black);
  //strip.begin();

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
  random16_add_entropy( random());
  //Serial.print("El ");
  //Serial.println(EL);
  if(Serial.available())
  {
    checkSerial();
  }

  if(EL == 0 && XEL == 0)
  {
    Fire2012WithPalette(); // run simulation frame, using palette colors
    FastLED.show(); // display this frame
    FastLED.delay(1000 / FRAMES_PER_SECOND);
  }
  else
  {
    if(Transmit)
    {
      //allSet(CRGB::Black);
      leds[stickone[index]] = CRGB::White;
      leds[sticktwo[index]] = CRGB::White;
      leds[stickthree[index]] = CRGB::White;
      leds[stickfour[index]] = CRGB::White;
      leds[stickone[index]].fadeLightBy(brightness);
      leds[sticktwo[index]].fadeLightBy(brightness);
      leds[stickthree[index]].fadeLightBy(brightness);
      leds[stickfour[index]].fadeLightBy(brightness);
      
      //allSet(strip.Color(50,50,50),10);
      FastLED.show();
      delay(100);
      index++;
      if(index >= 8)
      {
        index = 0;
        brightness = brightness + fadeAmount;
        // reverse the direction of the fading at the ends of the fade: 
        if(brightness == 0 || brightness == 255)
        {
          fadeAmount = -fadeAmount ; 
        } 
      }
      //Serial.println("Transmitting");
    }
    else
    {
      //Serial.println("Not Transmitting");
      allSet(CRGB::Red);
      //allSet(strip.Color(50,0,0),10);
      FastLED.show();
    }
  }

  if(EL != oldEL || XEL != oldXEL)
  {
    if(EL > 120)
    {
      EL = 120;
    }
    else if(EL < -120)
    {
      EL = -120;
    }
    if(XEL > 65)
    {
      XEL = 65;
    }
    else if(XEL < -65)
    {
      XEL = -65;
    }
    Serial.print("Sending EL ");
    Serial.println(EL);
    Serial.print("Sending XEL ");
    Serial.println(XEL);
    EL_servo.attach(10);
    XEL_servo.attach(9);
    
    int newEL = map(EL, -90, 90, 152, 30);
    int newXEL = map(XEL, -90, 90, 28, 160);

    if(newEL - oldnewEL > 10)
    {
      for (pos = oldnewEL; pos <= newEL; pos += 1) 
      {
        EL_servo.write(pos);
        delay(15);
      }
    }
    else
    {
      EL_servo.write(newEL);
    }
    
    if(newXEL - oldnewXEL > 10)
    {
      for (pos = oldnewXEL; pos <= newXEL; pos += 1) 
      {
        XEL_servo.write(pos);
        delay(15);
      }
    }
    else
    {
      XEL_servo.write(newXEL);
    }
    
    delay(1000);
    
    EL_servo.detach();
    XEL_servo.detach();
    oldnewEL = newEL;
    oldnewXEL = newXEL;
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
void allSet(uint32_t c)
{
  for(int dot=0; dot<NUM_LEDS; dot++)
  {
    leds[dot] = c;
    //pixels.setPixelColor(i,c);
  }
  FastLED.show();
}
// COOLING: How much does the air cool as it rises?
// Less cooling = taller flames.  More cooling = shorter flames.
// Default 55, suggested range 20-100 
#define COOLING  55

// SPARKING: What chance (out of 255) is there that a new spark will be lit?
// Higher chance = more roaring fire.  Lower chance = more flickery fire.
// Default 120, suggested range 50-200.
#define SPARKING 120


void Fire2012WithPalette()
{
// Array of temperature readings at each simulation cell
  static byte heat[NUM_LEDS];

  // Step 1.  Cool down every cell a little
    for( int i = 0; i < NUM_LEDS; i++) {
      heat[i] = qsub8( heat[i],  random8(0, ((COOLING * 10) / NUM_LEDS) + 2));
    }
  
    // Step 2.  Heat from each cell drifts 'up' and diffuses a little
    for( int k= NUM_LEDS - 1; k >= 2; k--) {
      heat[k] = (heat[k - 1] + heat[k - 2] + heat[k - 2] ) / 3;
    }
    
    // Step 3.  Randomly ignite new 'sparks' of heat near the bottom
    if( random8() < SPARKING ) {
      int y = random8(7);
      heat[y] = qadd8( heat[y], random8(160,255) );
    }

    // Step 4.  Map from heat cells to LED colors
    for( int j = 0; j < NUM_LEDS; j++) {
      // Scale the heat value from 0-255 down to 0-240
      // for best results with color palettes.
      byte colorindex = scale8( heat[j], 240);
      CRGB color = ColorFromPalette( gPal, colorindex);
      int pixelnumber;
      if( gReverseDirection ) {
        pixelnumber = (NUM_LEDS-1) - j;
      } else {
        pixelnumber = j;
      }
      leds[pixelnumber] = color;
    }
}
