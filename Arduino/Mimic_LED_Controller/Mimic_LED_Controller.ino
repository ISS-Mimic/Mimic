#include <FastLED.h>

// LED strip configuration
#define NUM_LEDS 48  // Total LEDs (24 per side)
#define DATA_PIN 5   // Port side
#define DATA_PIN2 6  // Starboard side

// Global brightness control (0-255)
uint8_t masterBrightness = 64;  // Start at 25% brightness to prevent brownout

// LED arrays
CRGB portLEDs[24];  // Port side
CRGB stbdLEDs[24];  // Starboard side

// LED group definitions - keep the same pixel mappings
int port_LEDs_4A[] = {0, 1, 2, 3, 4, 5};    // Port side, 4A array
int port_LEDs_2A[] = {6, 7, 8, 9, 10, 11};  // Port side, 2A array
int port_LEDs_4B[] = {12, 13, 14, 15, 16, 17}; // Port side, 4B array
int port_LEDs_2B[] = {18, 19, 20, 21, 22, 23}; // Port side, 2B array

int stbd_LEDs_3A[] = {0, 1, 2, 3, 4, 5};    // Starboard side, 3A array
int stbd_LEDs_1A[] = {6, 7, 8, 9, 10, 11};  // Starboard side, 1A array
int stbd_LEDs_3B[] = {12, 13, 14, 15, 16, 17}; // Starboard side, 3B array
int stbd_LEDs_1B[] = {18, 19, 20, 21, 22, 23}; // Starboard side, 1B array

// Color structure and lookup table
struct Color {
  const char* name;
  uint8_t r, g, b;
};

// Comprehensive color palette - easy to add new colors
const Color colorTable[] = {
  {"Red", 255, 0, 0},
  {"Green", 0, 255, 0}, 
  {"Blue", 0, 0, 255},
  {"White", 255, 255, 255},
  {"Yellow", 255, 255, 0},
  {"Magenta", 255, 0, 255},
  {"Cyan", 0, 255, 255},
  {"Orange", 255, 165, 0},
  {"Purple", 128, 0, 128},
  {"Pink", 255, 192, 203},
  {"Lime", 0, 255, 0},
  {"Teal", 0, 128, 128},
  {"Indigo", 75, 0, 130},
  {"Violet", 238, 130, 238},
  {"Gold", 255, 215, 0},
  {"Silver", 192, 192, 192},
  {"Brown", 165, 42, 42},
  {"Gray", 128, 128, 128},
  {"Off", 0, 0, 0},
  {"Black", 0, 0, 0}
};

const int NUM_COLORS = sizeof(colorTable) / sizeof(colorTable[0]);

// Animation and pattern states
boolean discoMode = false;
boolean pulseMode = false;
boolean chaseMode = false;
boolean rainbowMode = false;

// Animation timing (non-blocking)
unsigned long lastAnimationUpdate = 0;
unsigned long lastDiscoUpdate = 0;
unsigned long lastPulseUpdate = 0;
unsigned long lastChaseUpdate = 0;
unsigned long lastRainbowUpdate = 0;

// Animation parameters
int animationStep = 0;
int pulseBrightness = 0;
boolean pulseIncreasing = true;
int chasePosition = 0;
int rainbowHue = 0;

void setup() 
{
  Serial.begin(9600);
  Serial.setTimeout(50);
  
  // Initialize FastLED
  FastLED.addLeds<WS2812B, DATA_PIN, GRB>(portLEDs, 24);
  FastLED.addLeds<WS2812B, DATA_PIN2, GRB>(stbdLEDs, 24);
  
  // Set global brightness
  FastLED.setBrightness(masterBrightness);
  
  // Set all LEDs to off initially
  setAllLEDs("Off");
  
  // Test: turn on first LED of each side to verify hardware is working
  Serial.println(F("Testing hardware - turning on first LED of each side"));
  portLEDs[0] = CRGB::Red;
  stbdLEDs[0] = CRGB::Blue;
  FastLED.show();
  delay(1000);
  
  // Turn them off
  portLEDs[0] = CRGB::Black;
  stbdLEDs[0] = CRGB::Black;
  FastLED.show();
  
  Serial.println(F("Mimic LED Controller Ready (FastLED)"));
}

void loop() 
{
  // Check for serial commands (non-blocking)
  if (Serial.available()) 
  {
    checkSerial();
  }

  // Handle animations (non-blocking)
  unsigned long currentTime = millis();
  
  if (discoMode) {
    updateDiscoAnimation(currentTime);
  }
  
  if (pulseMode) {
    updatePulseAnimation(currentTime);
  }
  
  if (chaseMode) {
    updateChaseAnimation(currentTime);
  }
  
  if (rainbowMode) {
    updateRainbowAnimation(currentTime);
  }
  
  // Heartbeat every 10 seconds
  static unsigned long lastHeartbeat = 0;
  if (currentTime - lastHeartbeat > 10000) {
    lastHeartbeat = currentTime;
  }
}

void checkSerial() 
{
  if (!Serial.available()) return;
  
  // Wait longer for the full command to arrive
  delay(50);
  
  // Read the command
  char buffer[64];  // Increased buffer size
  int bufferIndex = 0;
  
  // Read all available characters
  while (Serial.available() && bufferIndex < 63) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      break;
    }
    buffer[bufferIndex++] = c;
  }
  
  buffer[bufferIndex] = '\0';
  
  if (bufferIndex == 0) return;
  
  // Debug: show what we received
  Serial.print(F("Received: '"));
  Serial.print(buffer);
  Serial.println(F("'"));
  
  // Parse command
  if (strncmp(buffer, "LED_", 4) == 0) {
    Serial.println(F("Processing LED command"));
    parseLEDCommand(buffer);
  } else if (strncmp(buffer, "PATTERN_", 8) == 0) {
    parsePatternCommand(buffer);
  } else if (strncmp(buffer, "ANIMATE_", 8) == 0) {
    parseAnimationCommand(buffer);
  } else if (strncmp(buffer, "BRIGHTNESS_", 11) == 0) {
    parseBrightnessCommand(buffer);
  } else if (strcmp(buffer, "DISCO") == 0) {
    discoMode = true;
    pulseMode = false;
    chaseMode = false;
    rainbowMode = false;
    Serial.println(F("Disco mode ON"));
  } else if (strcmp(buffer, "RESET") == 0) {
    resetAllLEDs();
    Serial.println(F("Reset complete"));
  } else if (strcmp(buffer, "STATUS") == 0) {
    printStatus();
  } else if (strcmp(buffer, "HELP") == 0) {
    printHelp();
  } else if (strcmp(buffer, "TEST") == 0) {
    Serial.println(F("Running TEST command"));
    parseLEDCommand("LED_1A=Red");
  } else if (strcmp(buffer, "RED") == 0) {
    Serial.println(F("Setting all LEDs to RED"));
    setAllLEDs("Red");
  } else if (strcmp(buffer, "OFF") == 0) {
    Serial.println(F("Turning all LEDs OFF"));
    setAllLEDs("Off");
  }
}

void parseLEDCommand(const char* command) {
  Serial.print(F("Parsing LED command: '"));
  Serial.print(command);
  Serial.println(F("'"));
  
  const char* equalsPos = strchr(command, '=');
  if (equalsPos == NULL) {
    Serial.println(F("No '=' found in command"));
    return;
  }
  
  int groupLen = equalsPos - command - 4;
  if (groupLen <= 0) {
    Serial.println(F("Invalid group length"));
    return;
  }
  
  char group[8];
  strncpy(group, command + 4, groupLen);
  group[groupLen] = '\0';
  
  const char* colorName = equalsPos + 1;
  
  Serial.print(F("Group: '"));
  Serial.print(group);
  Serial.print(F("', Color: '"));
  Serial.print(colorName);
  Serial.println(F("'"));
  
  // Find the color in our lookup table
  Color* color = findColor(colorName);
  if (color == NULL) {
    Serial.println(F("Color not found"));
    return;
  }
  
  Serial.print(F("Found color - R:"));
  Serial.print(color->r);
  Serial.print(F(" G:"));
  Serial.print(color->g);
  Serial.print(F(" B:"));
  Serial.println(color->b);
  
  // Apply color to the specified LED group
  if (strcmp(group, "1A") == 0) {
    Serial.println(F("Setting 1A LEDs"));
    setLEDGroup(stbdLEDs, stbd_LEDs_1A, 6, *color);
  } else if (strcmp(group, "1B") == 0) {
    Serial.println(F("Setting 1B LEDs"));
    setLEDGroup(stbdLEDs, stbd_LEDs_1B, 6, *color);
  } else if (strcmp(group, "2A") == 0) {
    Serial.println(F("Setting 2A LEDs"));
    setLEDGroup(portLEDs, port_LEDs_2A, 6, *color);
  } else if (strcmp(group, "2B") == 0) {
    Serial.println(F("Setting 2B LEDs"));
    setLEDGroup(portLEDs, port_LEDs_2B, 6, *color);
  } else if (strcmp(group, "3A") == 0) {
    Serial.println(F("Setting 3A LEDs"));
    setLEDGroup(stbdLEDs, stbd_LEDs_3A, 6, *color);
  } else if (strcmp(group, "3B") == 0) {
    Serial.println(F("Setting 3B LEDs"));
    setLEDGroup(stbdLEDs, stbd_LEDs_3B, 6, *color);
  } else if (strcmp(group, "4A") == 0) {
    Serial.println(F("Setting 4A LEDs"));
    setLEDGroup(portLEDs, port_LEDs_4A, 6, *color);
  } else if (strcmp(group, "4B") == 0) {
    Serial.println(F("Setting 4B LEDs"));
    setLEDGroup(portLEDs, port_LEDs_4B, 6, *color);
  } else if (strcmp(group, "ALL") == 0) {
    Serial.println(F("Setting ALL LEDs"));
    setAllLEDs(colorName);
  } else {
    Serial.print(F("Unknown group: "));
    Serial.println(group);
  }
}

void parsePatternCommand(const char* command) {
  const char* pattern = command + 8;
  
  if (strcmp(pattern, "RAINBOW") == 0) {
    setRainbowPattern();
  } else if (strcmp(pattern, "ALTERNATING") == 0) {
    setAlternatingPattern();
  } else if (strcmp(pattern, "RED_ALERT") == 0) {
    setRedAlertPattern();
  } else if (strcmp(pattern, "BLUE_PATTERN") == 0) {
    setBluePattern();
  }
}

void parseAnimationCommand(const char* command) {
  const char* animation = command + 8;
  
  if (strcmp(animation, "PULSE") == 0) {
    pulseMode = true;
    discoMode = false;
    chaseMode = false;
    rainbowMode = false;
  } else if (strcmp(animation, "CHASE") == 0) {
    chaseMode = true;
    discoMode = false;
    pulseMode = false;
    rainbowMode = false;
  } else if (strcmp(animation, "DISCO") == 0) {
    discoMode = true;
    pulseMode = false;
    chaseMode = false;
    rainbowMode = false;
  } else if (strcmp(animation, "STOP") == 0) {
    discoMode = false;
    pulseMode = false;
    chaseMode = false;
    rainbowMode = false;
  }
}

void parseBrightnessCommand(const char* command) {
  const char* brightness = command + 11;
  
  if (strcmp(brightness, "25") == 0) {
    setGlobalBrightness(64);  // 25% of 255
  } else if (strcmp(brightness, "50") == 0) {
    setGlobalBrightness(128); // 50% of 255
  } else if (strcmp(brightness, "75") == 0) {
    setGlobalBrightness(192); // 75% of 255
  } else if (strcmp(brightness, "100") == 0) {
    setGlobalBrightness(255); // 100% of 255
  }
}

Color* findColor(const char* colorName) {
  if (colorName == NULL || strlen(colorName) == 0) {
    return NULL;
  }
  
  for (int i = 0; i < NUM_COLORS; i++) {
    const char* tableColor = colorTable[i].name;
    
    if (strcmp(colorName, tableColor) == 0) {
      return (Color*)&colorTable[i];
    }
  }
  
  return NULL;
}

void setLEDGroup(CRGB* ledArray, int* ledIndices, int arraySize, Color color) {
  for (int i = 0; i < arraySize; i++) {
    ledArray[ledIndices[i]] = CRGB(color.r, color.g, color.b);
  }
  FastLED.show();
}

void setAllLEDs(const char* colorName) {
  Color* color = findColor(colorName);
  if (color == NULL) return;
  
  // Set all LED groups to the specified color
  setLEDGroup(stbdLEDs, stbd_LEDs_1A, 6, *color);
  setLEDGroup(stbdLEDs, stbd_LEDs_1B, 6, *color);
  setLEDGroup(portLEDs, port_LEDs_2A, 6, *color);
  setLEDGroup(portLEDs, port_LEDs_2B, 6, *color);
  setLEDGroup(stbdLEDs, stbd_LEDs_3A, 6, *color);
  setLEDGroup(stbdLEDs, stbd_LEDs_3B, 6, *color);
  setLEDGroup(portLEDs, port_LEDs_4A, 6, *color);
  setLEDGroup(portLEDs, port_LEDs_4B, 6, *color);
  
  FastLED.show();
}

void setRainbowPattern() {
  setLEDGroup(stbdLEDs, stbd_LEDs_1A, 6, colorTable[0]);  // Red
  setLEDGroup(stbdLEDs, stbd_LEDs_1B, 6, colorTable[1]);  // Green
  setLEDGroup(portLEDs, port_LEDs_2A, 6, colorTable[2]);  // Blue
  setLEDGroup(portLEDs, port_LEDs_2B, 6, colorTable[3]);  // White
  setLEDGroup(stbdLEDs, stbd_LEDs_3A, 6, colorTable[4]);  // Yellow
  setLEDGroup(stbdLEDs, stbd_LEDs_3B, 6, colorTable[5]);  // Magenta
  setLEDGroup(portLEDs, port_LEDs_4A, 6, colorTable[6]);  // Cyan
  setLEDGroup(portLEDs, port_LEDs_4B, 6, colorTable[7]);  // Orange
}

void setAlternatingPattern() {
  setLEDGroup(stbdLEDs, stbd_LEDs_1A, 6, colorTable[0]);  // Red
  setLEDGroup(stbdLEDs, stbd_LEDs_1B, 6, colorTable[2]);  // Blue
  setLEDGroup(portLEDs, port_LEDs_2A, 6, colorTable[0]);  // Red
  setLEDGroup(portLEDs, port_LEDs_2B, 6, colorTable[2]);  // Blue
  setLEDGroup(stbdLEDs, stbd_LEDs_3A, 6, colorTable[0]);  // Red
  setLEDGroup(stbdLEDs, stbd_LEDs_3B, 6, colorTable[2]);  // Blue
  setLEDGroup(portLEDs, port_LEDs_4A, 6, colorTable[0]);  // Red
  setLEDGroup(portLEDs, port_LEDs_4B, 6, colorTable[2]);  // Blue
}

void setRedAlertPattern() {
  setAllLEDs("Red");
}

void setBluePattern() {
  setAllLEDs("Blue");
}

void resetAllLEDs() {
  setAllLEDs("Off");
  discoMode = false;
  pulseMode = false;
  chaseMode = false;
  rainbowMode = false;
}

void setGlobalBrightness(uint8_t brightness) {
  masterBrightness = brightness;
  FastLED.setBrightness(masterBrightness);
  FastLED.show();
}

// ===== NON-BLOCKING ANIMATIONS =====

void updateDiscoAnimation(unsigned long currentTime) {
  if (currentTime - lastDiscoUpdate > 100) {  // Update every 100ms
    // Random disco colors
    for (int i = 0; i < 24; i++) {
      portLEDs[i] = CHSV(random8(), 255, 255);
      stbdLEDs[i] = CHSV(random8(), 255, 255);
    }
    FastLED.show();
    lastDiscoUpdate = currentTime;
  }
}

void updatePulseAnimation(unsigned long currentTime) {
  if (currentTime - lastPulseUpdate > 50) {  // Update every 50ms
    if (pulseIncreasing) {
      pulseBrightness += 5;
      if (pulseBrightness >= 255) {
        pulseBrightness = 255;
        pulseIncreasing = false;
      }
    } else {
      pulseBrightness -= 5;
      if (pulseBrightness <= 0) {
        pulseBrightness = 0;
        pulseIncreasing = true;
      }
    }
    
    // Apply brightness to all LEDs
    for (int i = 0; i < 24; i++) {
      portLEDs[i] = CRGB(pulseBrightness, pulseBrightness, pulseBrightness);
      stbdLEDs[i] = CRGB(pulseBrightness, pulseBrightness, pulseBrightness);
    }
    FastLED.show();
    lastPulseUpdate = currentTime;
  }
}

void updateChaseAnimation(unsigned long currentTime) {
  if (currentTime - lastChaseUpdate > 100) {  // Update every 100ms
    // Clear all LEDs
    FastLED.clear();
    
    // Set one LED in each array to white
    portLEDs[port_LEDs_4A[chasePosition]] = CRGB::White;
    portLEDs[port_LEDs_2A[chasePosition]] = CRGB::White;
    portLEDs[port_LEDs_4B[chasePosition]] = CRGB::White;
    portLEDs[port_LEDs_2B[chasePosition]] = CRGB::White;
    
    stbdLEDs[stbd_LEDs_3A[chasePosition]] = CRGB::White;
    stbdLEDs[stbd_LEDs_1A[chasePosition]] = CRGB::White;
    stbdLEDs[stbd_LEDs_3B[chasePosition]] = CRGB::White;
    stbdLEDs[stbd_LEDs_1B[chasePosition]] = CRGB::White;
    
    FastLED.show();
    
    chasePosition = (chasePosition + 1) % 6;
    lastChaseUpdate = currentTime;
  }
}

void updateRainbowAnimation(unsigned long currentTime) {
  if (currentTime - lastRainbowUpdate > 50) {  // Update every 50ms
    // Rainbow wave across all LEDs
    for (int i = 0; i < 24; i++) {
      portLEDs[i] = CHSV(rainbowHue + i * 8, 255, 255);
      stbdLEDs[i] = CHSV(rainbowHue + i * 8, 255, 255);
    }
    FastLED.show();
    
    rainbowHue++;
    lastRainbowUpdate = currentTime;
  }
}

void printStatus() {
  Serial.println(F("=== LED Controller Status ==="));
  Serial.print(F("Disco Mode: ")); Serial.println(discoMode ? F("ON") : F("OFF"));
  Serial.print(F("Pulse Mode: ")); Serial.println(pulseMode ? F("ON") : F("OFF"));
  Serial.print(F("Chase Mode: ")); Serial.println(chaseMode ? F("ON") : F("OFF"));
  Serial.print(F("Rainbow Mode: ")); Serial.println(rainbowMode ? F("ON") : F("OFF"));
  Serial.print(F("Global Brightness: ")); Serial.println(masterBrightness);
  Serial.println(F("============================="));
}

void printHelp() {
  Serial.println(F("=== Available Commands ==="));
  Serial.println(F("LED Commands:"));
  Serial.println(F("  LED_1A=Red, LED_2B=Blue, etc."));
  Serial.println(F("  LED_ALL=White (set all arrays)"));
  Serial.println();
  Serial.println(F("Pattern Commands:"));
  Serial.println(F("  PATTERN_RAINBOW"));
  Serial.println(F("  PATTERN_ALTERNATING"));
  Serial.println(F("  PATTERN_RED_ALERT"));
  Serial.println(F("  PATTERN_BLUE_PATTERN"));
  Serial.println();
  Serial.println(F("Animation Commands:"));
  Serial.println(F("  ANIMATE_PULSE"));
  Serial.println(F("  ANIMATE_CHASE"));
  Serial.println(F("  ANIMATE_DISCO"));
  Serial.println(F("  ANIMATE_STOP"));
  Serial.println();
  Serial.println(F("Brightness Commands:"));
  Serial.println(F("  BRIGHTNESS_25, BRIGHTNESS_50, BRIGHTNESS_75, BRIGHTNESS_100"));
  Serial.println();
  Serial.println(F("Special Commands:"));
  Serial.println(F("  DISCO, RESET, STATUS, HELP"));
  Serial.println();
  Serial.println(F("Available Colors:"));
  for (int i = 0; i < NUM_COLORS; i++) {
    const char* colorName = colorTable[i].name;
    Serial.print(F("  ")); Serial.print(colorName);
    if ((i + 1) % 5 == 0) Serial.println();
  }
  Serial.println();
  Serial.println(F("========================"));
}
