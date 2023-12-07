#include <Adafruit_NeoPixel.h>

Adafruit_NeoPixel stbdIEA = Adafruit_NeoPixel(24, 6, NEO_GRB);
Adafruit_NeoPixel portIEA = Adafruit_NeoPixel(24, 5, NEO_GRB);

double voltages[4][2] = 
{
  {0.00, 0.00}, // V1A, V1B
  {0.00, 0.00}, // V2A, V2B
  {0.00, 0.00}, // V3A, V3B
  {0.00, 0.00}  // V4A, V4B
};

boolean Disco = false;
int NULLIFY = 0;

void setup() 
{
  Serial.begin(9600);
  Serial.setTimeout(50);
  portIEA.begin();
  stbdIEA.begin();
  portIEA.show();
  stbdIEA.show();
}

void loop() 
{
  if (Serial.available()) 
  {
    checkSerial();
  }

  updateLEDs(portIEA, 0);
  updateLEDs(portIEA, 6);
  updateLEDs(portIEA, 12);
  updateLEDs(portIEA, 18);
  updateLEDs(stbdIEA, 0);
  updateLEDs(stbdIEA, 6);
  updateLEDs(stbdIEA, 12);
  updateLEDs(stbdIEA, 18);

  if (Disco) 
  {
    theaterChaseRainbow(portIEA, stbdIEA, 100);
  }
  Disco = false;
}

void updateLEDs(Adafruit_NeoPixel &strip, int startIndex) 
{
  double voltageA = voltages[startIndex / 6][0];
  double voltageB = voltages[startIndex / 6][1];

  for (int i = startIndex; i < startIndex + 6; i++) 
  {
    setColorBasedOnVoltage(strip, i, voltageA, voltageB);
  }

  strip.show();
}

void setColorBasedOnVoltage(Adafruit_NeoPixel &strip, int index, double voltageA, double voltageB) 
{
  if (voltageA < 151.5) 
  {
    strip.setPixelColor(index, strip.Color(111, 0, 0));
  } 
  else if (voltageA > 160) 
  {
    strip.setPixelColor(index, strip.Color(111, 111, 111));
  } 
  else 
  {
    strip.setPixelColor(index, strip.Color(0, 0, 111));
  }
}

void checkSerial() 
{
  String receivedData = Serial.readStringUntil('\n');

  char buffer[receivedData.length() + 1];
  strcpy(buffer, receivedData.c_str());

  char *token;
  char *remainder;
  token = strtok_r(buffer, " ", &remainder);

  while (token != NULL) 
  {
    String dataString(token);
    int delimiterIndex = dataString.indexOf('=');

    if (delimiterIndex != -1) 
    {
      String key = dataString.substring(0, delimiterIndex);
      String value = dataString.substring(delimiterIndex + 1);
      if (key == "Disco") 
      {
        Disco = true;
      } 
      else if (key == "NULLIFY") 
      {
        NULLIFY = value.toInt();
        Serial.println("Got the NULL cmd over Serial...");
      } 
      else if (key.startsWith("V")) 
      {
        int voltageIndex = key.substring(1).toInt(); // Extract the index after "Voltage"
        if (voltageIndex >= 1 && voltageIndex <= 4) 
        {
          int subIndex = key.endsWith("A") ? 0 : 1; // Determine whether it's A or B voltage
          voltages[voltageIndex - 1][subIndex] = value.toFloat(); // Update the voltage array
        }
      }
    }
    token = strtok_r(NULL, " ", &remainder);
  }
}

void theaterChaseRainbow(Adafruit_NeoPixel &strip1, Adafruit_NeoPixel &strip2, uint8_t wait) 
{
  uint16_t numPixels = strip1.numPixels();

  for (int j = 0; j < 256; j++) 
  { // cycle all 256 colors in the wheel
    for (uint16_t i = 0; i < numPixels; i = i + 3) 
    {
      strip1.setPixelColor(i + j % 3, Wheel(strip1, (i + j) % 255)); // turn every third pixel on for strip1
      strip2.setPixelColor(i + j % 3, Wheel(strip2, (i + j) % 255)); // turn every third pixel on for strip2
    }
    strip1.show();
    strip2.show();
    delay(wait);

    for (uint16_t i = 0; i < numPixels; i = i + 3) 
    {
      strip1.setPixelColor(i + j % 3, 0); // turn every third pixel off for strip1
      strip2.setPixelColor(i + j % 3, 0); // turn every third pixel off for strip2
    }
  }
}

uint32_t Wheel(Adafruit_NeoPixel &strip, byte WheelPos)
{
  WheelPos = 255 - WheelPos;
  if (WheelPos < 85) 
  {
    return strip.Color(255 - WheelPos * 3, 0, WheelPos * 3);
  }
  if (WheelPos < 170) 
  {
    WheelPos -= 85;
    return strip.Color(0, WheelPos * 3, 255 - WheelPos * 3);
  }
  WheelPos -= 170;
  return strip.Color(WheelPos * 3, 255 - WheelPos * 3, 0);
}
