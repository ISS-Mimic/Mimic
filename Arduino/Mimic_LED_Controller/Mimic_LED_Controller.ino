#include <Adafruit_NeoPixel.h>

Adafruit_NeoPixel stbdIEA = Adafruit_NeoPixel(24, 6, NEO_GRB);
Adafruit_NeoPixel portIEA = Adafruit_NeoPixel(24, 5, NEO_GRB);

int port_LEDs_4A[] = {0, 1, 2, 3, 4, 5};
int port_LEDs_2A[] = {6, 7, 8, 9, 10, 11};
int port_LEDs_4B[] = {12, 13, 14, 15, 16, 17};
int port_LEDs_2B[] = {18, 19, 20, 21, 22, 23};

int stbd_LEDs_3A[] = {0, 1, 2, 3, 4, 5};
int stbd_LEDs_1A[] = {6, 7, 8, 9, 10, 11};
int stbd_LEDs_3B[] = {12, 13, 14, 15, 16, 17};
int stbd_LEDs_1B[] = {18, 19, 20, 21, 22, 23};


double port_voltages[4] = {0,0,0,0}; // 2A, 4A, 2B, 4B
double stbd_voltages[4] = {0,0,0,0}; // 1A, 3A, 1B, 3B

double prev_port_voltages[4] = {0, 0, 0, 0};
double prev_stbd_voltages[4] = {0, 0, 0, 0};

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

  // Update LEDs for each array on the port side
  updateLEDs(portIEA, port_LEDs_2A, 6, port_voltages[0], prev_port_voltages[0]);
  updateLEDs(portIEA, port_LEDs_4A, 6, port_voltages[1], prev_port_voltages[1]);
  updateLEDs(portIEA, port_LEDs_2B, 6, port_voltages[2], prev_port_voltages[2]);
  updateLEDs(portIEA, port_LEDs_4B, 6, port_voltages[3], prev_port_voltages[3]);

  // Update LEDs for each array on the starboard side
  updateLEDs(stbdIEA, stbd_LEDs_1A, 6, stbd_voltages[0], prev_stbd_voltages[0]);
  updateLEDs(stbdIEA, stbd_LEDs_3A, 6, stbd_voltages[1], prev_stbd_voltages[1]);
  updateLEDs(stbdIEA, stbd_LEDs_1B, 6, stbd_voltages[2], prev_stbd_voltages[2]);
  updateLEDs(stbdIEA, stbd_LEDs_3B, 6, stbd_voltages[3], prev_stbd_voltages[3]);


  if (Disco) 
  {
    theaterChaseRainbow(portIEA, stbdIEA, 100);
  }
  Disco = false;
}

void updateLEDs(Adafruit_NeoPixel &strip, int* ledArray, int arraySize, double state, double &prevState) 
{
    if (state != prevState) 
    {
        uint32_t color = setColorBasedOnState(state);
        for (int i = 0; i < arraySize; i++) 
        {
            strip.setPixelColor(ledArray[i], color);
        }
        strip.show();
        prevState = state;
    }
}

uint32_t setColorBasedOnState(double arrayState) 
{
  if(arrayState == 1.00) 
  {
    return portIEA.Color(111, 0, 0); // Red
  } 
  else if(arrayState == 2.00) 
  {
    return portIEA.Color(0, 0, 111); // Blue
  } 
  else if(arrayState == 3.00) 
  {
    return portIEA.Color(111, 111, 111); // White
  } 
  else 
  {
    return portIEA.Color(111, 30, 22); // Orange
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
      else if (key.startsWith("V")) 
      {
        int voltageIndex = key.substring(1,2).toInt(); // Extract the index after "Voltage"
        switch (voltageIndex) 
        {
          case 1:
            if(key.endsWith("A"))
            {
              //1A
              stbd_voltages[0] = value.toFloat();
            }
            else
            {
              //1B
              stbd_voltages[2] = value.toFloat();
            }
            break;
          case 2:
            if(key.endsWith("A"))
            {
              //2A
              port_voltages[0] = value.toFloat();
            }
            else
            {
              //2B
              port_voltages[2] = value.toFloat();
            }
            break;
          case 3:
            if(key.endsWith("A"))
            {
              //3A
              stbd_voltages[1] = value.toFloat();
            }
            else
            {
              //3B
              stbd_voltages[3] = value.toFloat();
            }
            break;
          case 4:
            if(key.endsWith("A"))
            {
              //4A
              port_voltages[1] = value.toFloat();
            }
            else
            {
              //4B
              port_voltages[3] = value.toFloat();
            }
            break;
          default:
            break;
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
