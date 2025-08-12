#include <Adafruit_NeoPixel.h>

// NeoPixel strips for port and starboard sides
Adafruit_NeoPixel portIEA = Adafruit_NeoPixel(24, 5, NEO_GRB);
Adafruit_NeoPixel stbdIEA = Adafruit_NeoPixel(24, 6, NEO_GRB);

// LED group definitions - keep the same pixel mappings
int port_LEDs_4A[] = {0, 1, 2, 3, 4, 5};    // Port side, 4A array
int port_LEDs_2A[] = {6, 7, 8, 9, 10, 11};  // Port side, 2A array
int port_LEDs_4B[] = {12, 13, 14, 15, 16, 17}; // Port side, 4B array
int port_LEDs_2B[] = {18, 19, 20, 21, 22, 23}; // Port side, 2B array

int stbd_LEDs_3A[] = {0, 1, 2, 3, 4, 5};    // Starboard side, 3A array
int stbd_LEDs_1A[] = {6, 7, 8, 9, 10, 11};  // Starboard side, 1A array
int stbd_LEDs_3B[] = {12, 13, 14, 15, 16, 17}; // Starboard side, 3B array
int stbd_LEDs_1B[] = {18, 19, 20, 21, 22, 23}; // Starboard side, 1B array

// Color structure and lookup table - store strings in PROGMEM
struct Color {
  const char* name;
  uint8_t r, g, b;
};

// Comprehensive color palette - easy to add new colors
const Color colorTable[] PROGMEM = {
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
unsigned long lastAnimationUpdate = 0;
int animationStep = 0;

void setup() 
{
  Serial.begin(9600);
  Serial.setTimeout(50); // Reduce timeout to save memory
  
  // Initialize NeoPixel strips
  portIEA.begin();
  stbdIEA.begin();
  
  // Set all LEDs to off initially
  setAllLEDs("Off");
  
  Serial.println(F("Mimic LED Controller Ready"));
  Serial.println(F("Commands: LED_1A=Red, LED_2B=Blue, etc."));
  Serial.println(F("Patterns: PATTERN_RAINBOW, PATTERN_ALTERNATING"));
  Serial.println(F("Animations: ANIMATE_PULSE, ANIMATE_CHASE"));
  Serial.println(F("Special: DISCO, RESET, STATUS, TEST"));
  Serial.println(F("Send 'TEST' to verify communication"));
}

void loop() 
{
  // Check for serial commands
  if (Serial.available()) 
  {
    Serial.println(F("Serial data available!"));
    checkSerial();
  }

  // Handle animations
  if (discoMode) {
    theaterChaseRainbow(100);
  } else if (pulseMode) {
    pulseAllLEDs(50);
  } else if (chaseMode) {
    chasePattern(100);
  }
  
  // Heartbeat every 10 seconds (reduced frequency to save memory)
  static unsigned long lastHeartbeat = 0;
  if (millis() - lastHeartbeat > 10000) {
    Serial.println(F("Arduino heartbeat"));
    lastHeartbeat = millis();
  }
}

void checkSerial() 
{
  if (!Serial.available()) return;
  
  Serial.println(F("Starting to read serial data..."));
  
  // Read one character at a time to see what we're getting
  char buffer[32]; // Fixed size buffer instead of String
  int bufferIndex = 0;
  
  while (Serial.available() && bufferIndex < 31) {
    char c = Serial.read();
    Serial.print(F("Read char: '"));
    Serial.print(c);
    Serial.print(F("' (ASCII: "));
    Serial.print((int)c);
    Serial.println(F(")"));
    
    if (c == '\n' || c == '\r') {
      break;
    }
    buffer[bufferIndex++] = c;
  }
  
  buffer[bufferIndex] = '\0'; // Null terminate
  
  Serial.print(F("Final received data: '"));
  Serial.print(buffer);
  Serial.print(F("' (length: "));
  Serial.print(bufferIndex);
  Serial.println(F(")"));
  
  if (bufferIndex == 0) {
    Serial.println(F("Received empty string, ignoring"));
    return;
  }
  
  // Parse command
  if (strncmp(buffer, "LED_", 4) == 0) {
    parseLEDCommand(buffer);
  } else if (strncmp(buffer, "PATTERN_", 8) == 0) {
    parsePatternCommand(buffer);
  } else if (strncmp(buffer, "ANIMATE_", 8) == 0) {
    parseAnimationCommand(buffer);
  } else if (strcmp(buffer, "DISCO") == 0) {
    discoMode = true;
    pulseMode = false;
    chaseMode = false;
    Serial.println(F("Disco mode activated"));
  } else if (strcmp(buffer, "RESET") == 0) {
    resetAllLEDs();
    Serial.println(F("All LEDs reset to off"));
  } else if (strcmp(buffer, "STATUS") == 0) {
    printStatus();
  } else if (strcmp(buffer, "HELP") == 0) {
    printHelp();
  } else if (strcmp(buffer, "TEST") == 0) {
    Serial.println(F("TEST command received - Arduino is responsive!"));
    Serial.println(F("Testing LED_1A=Red..."));
    parseLEDCommand("LED_1A=Red");
  } else {
    Serial.print(F("Unknown command: '"));
    Serial.print(buffer);
    Serial.println(F("'"));
  }
}

void parseLEDCommand(const char* command) {
  // Format: LED_1A=Red, LED_SM=Blue, etc.
  Serial.print(F("Parsing LED command: '"));
  Serial.print(command);
  Serial.println(F("'"));
  
  const char* equalsPos = strchr(command, '=');
  if (equalsPos == NULL) {
    Serial.println(F("Invalid LED command format. Use: LED_GROUP=COLOR"));
    return;
  }
  
  int groupLen = equalsPos - command - 4; // Remove "LED_" prefix
  if (groupLen <= 0) {
    Serial.println(F("Invalid group name"));
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
    Serial.print(F("Unknown color: "));
    Serial.println(colorName);
    return;
  }
  
  // Apply color to the specified LED group
  if (strcmp(group, "1A") == 0) {
    setLEDGroup(stbdIEA, stbd_LEDs_1A, 6, *color);
  } else if (strcmp(group, "1B") == 0) {
    setLEDGroup(stbdIEA, stbd_LEDs_1B, 6, *color);
  } else if (strcmp(group, "2A") == 0) {
    setLEDGroup(portIEA, port_LEDs_2A, 6, *color);
  } else if (strcmp(group, "2B") == 0) {
    setLEDGroup(portIEA, port_LEDs_2B, 6, *color);
  } else if (strcmp(group, "3A") == 0) {
    setLEDGroup(stbdIEA, stbd_LEDs_3A, 6, *color);
  } else if (strcmp(group, "3B") == 0) {
    setLEDGroup(stbdIEA, stbd_LEDs_3B, 6, *color);
  } else if (strcmp(group, "4A") == 0) {
    setLEDGroup(portIEA, port_LEDs_4A, 6, *color);
  } else if (strcmp(group, "4B") == 0) {
    setLEDGroup(portIEA, port_LEDs_4B, 6, *color);
  } else if (strcmp(group, "ALL") == 0) {
    setAllLEDs(colorName);
  } else {
    Serial.print(F("Unknown LED group: "));
    Serial.println(group);
    return;
  }
  
  Serial.print(F("Set "));
  Serial.print(group);
  Serial.print(F(" to "));
  Serial.println(colorName);
}

void parsePatternCommand(const char* command) {
  // Format: PATTERN_RAINBOW, PATTERN_ALTERNATING, etc.
  const char* pattern = command + 8; // Remove "PATTERN_" prefix
  
  if (strcmp(pattern, "RAINBOW") == 0) {
    setRainbowPattern();
  } else if (strcmp(pattern, "ALTERNATING") == 0) {
    setAlternatingPattern();
  } else if (strcmp(pattern, "RED_ALERT") == 0) {
    setRedAlertPattern();
  } else if (strcmp(pattern, "BLUE_PATTERN") == 0) {
    setBluePattern();
  } else {
    Serial.print(F("Unknown pattern: "));
    Serial.println(pattern);
  }
}

void parseAnimationCommand(const char* command) {
  // Format: ANIMATE_PULSE, ANIMATE_CHASE, etc.
  const char* animation = command + 8; // Remove "ANIMATE_" prefix
  
  if (strcmp(animation, "PULSE") == 0) {
    pulseMode = true;
    discoMode = false;
    chaseMode = false;
    Serial.println(F("Pulse animation activated"));
  } else if (strcmp(animation, "CHASE") == 0) {
    chaseMode = true;
    discoMode = false;
    pulseMode = false;
    Serial.println(F("Chase animation activated"));
  } else if (strcmp(animation, "STOP") == 0) {
    discoMode = false;
    pulseMode = false;
    chaseMode = false;
    Serial.println(F("All animations stopped"));
  } else {
    Serial.print(F("Unknown animation: "));
    Serial.println(animation);
  }
}

Color* findColor(const char* colorName) {
  // Check for empty string
  if (colorName == NULL || strlen(colorName) == 0) {
    Serial.println(F("ERROR: Empty color name received!"));
    return NULL;
  }
  
  Serial.print(F("Looking for color: '"));
  Serial.print(colorName);
  Serial.print(F("' (length: "));
  Serial.print(strlen(colorName));
  Serial.println(F(")"));
  
  for (int i = 0; i < NUM_COLORS; i++) {
    const char* tableColor = (const char*)pgm_read_word(&colorTable[i].name);
    
    Serial.print(F("  Comparing with: '"));
    Serial.print(tableColor);
    Serial.print(F("' (length: "));
    Serial.print(strlen(tableColor));
    Serial.print(F(") - Match: "));
    Serial.println(strcmp(colorName, tableColor) == 0 ? F("YES") : F("NO"));
    
    if (strcmp(colorName, tableColor) == 0) {
      Serial.print(F("Found color: "));
      Serial.println(tableColor);
      return (Color*)&colorTable[i];
    }
  }
  
  Serial.println(F("Color not found!"));
  return NULL;
}

void setLEDGroup(Adafruit_NeoPixel& strip, int* ledArray, int arraySize, Color color) {
  for (int i = 0; i < arraySize; i++) {
    strip.setPixelColor(ledArray[i], strip.Color(color.r, color.g, color.b));
  }
  strip.show();
}

void setAllLEDs(const char* colorName) {
  Color* color = findColor(colorName);
  if (color == NULL) {
    Serial.print(F("Unknown color: "));
    Serial.println(colorName);
    return;
  }
  
  // Set all LED groups to the specified color
  setLEDGroup(stbdIEA, stbd_LEDs_1A, 6, *color);
  setLEDGroup(stbdIEA, stbd_LEDs_1B, 6, *color);
  setLEDGroup(portIEA, port_LEDs_2A, 6, *color);
  setLEDGroup(portIEA, port_LEDs_2B, 6, *color);
  setLEDGroup(stbdIEA, stbd_LEDs_3A, 6, *color);
  setLEDGroup(stbdIEA, stbd_LEDs_3B, 6, *color);
  setLEDGroup(portIEA, port_LEDs_4A, 6, *color);
  setLEDGroup(portIEA, port_LEDs_4B, 6, *color);
}

void setRainbowPattern() {
  // Set each array to a different color
  setLEDGroup(stbdIEA, stbd_LEDs_1A, 6, colorTable[0]);  // Red
  setLEDGroup(stbdIEA, stbd_LEDs_1B, 6, colorTable[1]);  // Green
  setLEDGroup(portIEA, port_LEDs_2A, 6, colorTable[2]);  // Blue
  setLEDGroup(portIEA, port_LEDs_2B, 6, colorTable[3]);  // White
  setLEDGroup(stbdIEA, stbd_LEDs_3A, 6, colorTable[4]);  // Yellow
  setLEDGroup(stbdIEA, stbd_LEDs_3B, 6, colorTable[5]);  // Magenta
  setLEDGroup(portIEA, port_LEDs_4A, 6, colorTable[6]);  // Cyan
  setLEDGroup(portIEA, port_LEDs_4B, 6, colorTable[7]);  // Orange
  Serial.println(F("Rainbow pattern applied"));
}

void setAlternatingPattern() {
  // Alternate between two colors
  setLEDGroup(stbdIEA, stbd_LEDs_1A, 6, colorTable[0]);  // Red
  setLEDGroup(stbdIEA, stbd_LEDs_1B, 6, colorTable[2]);  // Blue
  setLEDGroup(portIEA, port_LEDs_2A, 6, colorTable[0]);  // Red
  setLEDGroup(portIEA, port_LEDs_2B, 6, colorTable[2]);  // Blue
  setLEDGroup(stbdIEA, stbd_LEDs_3A, 6, colorTable[0]);  // Red
  setLEDGroup(stbdIEA, stbd_LEDs_3B, 6, colorTable[2]);  // Blue
  setLEDGroup(portIEA, port_LEDs_4A, 6, colorTable[0]);  // Red
  setLEDGroup(portIEA, port_LEDs_4B, 6, colorTable[2]);  // Blue
  Serial.println(F("Alternating pattern applied"));
}

void setRedAlertPattern() {
  setAllLEDs("Red");
  Serial.println(F("Red alert pattern applied"));
}

void setBluePattern() {
  setAllLEDs("Blue");
  Serial.println(F("Blue pattern applied"));
}

void resetAllLEDs() {
  setAllLEDs("Off");
  discoMode = false;
  pulseMode = false;
  chaseMode = false;
}

void pulseAllLEDs(int delayMs) {
  static int brightness = 0;
  static boolean increasing = true;
  
  if (millis() - lastAnimationUpdate > delayMs) {
    if (increasing) {
      brightness += 5;
      if (brightness >= 255) {
        brightness = 255;
        increasing = false;
      }
    } else {
      brightness -= 5;
      if (brightness <= 0) {
        brightness = 0;
        increasing = true;
      }
    }
    
    // Apply brightness to all LEDs
    for (int i = 0; i < 24; i++) {
      portIEA.setPixelColor(i, portIEA.Color(brightness, brightness, brightness));
      stbdIEA.setPixelColor(i, stbdIEA.Color(brightness, brightness, brightness));
    }
    portIEA.show();
    stbdIEA.show();
    
    lastAnimationUpdate = millis();
  }
}

void chasePattern(int delayMs) {
  if (millis() - lastAnimationUpdate > delayMs) {
    // Clear all LEDs
    portIEA.clear();
    stbdIEA.clear();
    
    // Set one LED in each array to white
    int chasePos = animationStep % 6;
    
    portIEA.setPixelColor(port_LEDs_4A[chasePos], portIEA.Color(255, 255, 255));
    portIEA.setPixelColor(port_LEDs_2A[chasePos], portIEA.Color(255, 255, 255));
    portIEA.setPixelColor(port_LEDs_4B[chasePos], portIEA.Color(255, 255, 255));
    portIEA.setPixelColor(port_LEDs_2B[chasePos], portIEA.Color(255, 255, 255));
    
    stbdIEA.setPixelColor(stbd_LEDs_3A[chasePos], stbdIEA.Color(255, 255, 255));
    stbdIEA.setPixelColor(stbd_LEDs_1A[chasePos], stbdIEA.Color(255, 255, 255));
    stbdIEA.setPixelColor(stbd_LEDs_3B[chasePos], stbdIEA.Color(255, 255, 255));
    stbdIEA.setPixelColor(stbd_LEDs_1B[chasePos], stbdIEA.Color(255, 255, 255));
    
    portIEA.show();
    stbdIEA.show();
    
    animationStep++;
    lastAnimationUpdate = millis();
  }
}

void theaterChaseRainbow(int wait) {
  static int j = 0;
  static unsigned long lastUpdate = 0;
  
  if (millis() - lastUpdate > wait) {
    for (uint16_t i = 0; i < 24; i = i + 3) {
      portIEA.setPixelColor(i + j % 3, Wheel(portIEA, (i + j) % 255));
      stbdIEA.setPixelColor(i + j % 3, Wheel(stbdIEA, (i + j) % 255));
    }
    portIEA.show();
    stbdIEA.show();
    
    for (uint16_t i = 0; i < 24; i = i + 3) {
      portIEA.setPixelColor(i + j % 3, 0);
      stbdIEA.setPixelColor(i + j % 3, 0);
    }
    
    j++;
    lastUpdate = millis();
  }
}

uint32_t Wheel(Adafruit_NeoPixel& strip, byte WheelPos) {
  WheelPos = 255 - WheelPos;
  if (WheelPos < 85) {
    return strip.Color(255 - WheelPos * 3, 0, WheelPos * 3);
  }
  if (WheelPos < 170) {
    WheelPos -= 85;
    return strip.Color(0, WheelPos * 3, 255 - WheelPos * 3);
  }
  WheelPos -= 170;
  return strip.Color(WheelPos * 3, 255 - WheelPos * 3, 0);
}

void printStatus() {
  Serial.println(F("=== LED Controller Status ==="));
  Serial.print(F("Disco Mode: ")); Serial.println(discoMode ? F("ON") : F("OFF"));
  Serial.print(F("Pulse Mode: ")); Serial.println(pulseMode ? F("ON") : F("OFF"));
  Serial.print(F("Chase Mode: ")); Serial.println(chaseMode ? F("ON") : F("OFF"));
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
  Serial.println(F("  ANIMATE_STOP"));
  Serial.println();
  Serial.println(F("Special Commands:"));
  Serial.println(F("  DISCO, RESET, STATUS, HELP"));
  Serial.println();
  Serial.println(F("Available Colors:"));
  for (int i = 0; i < NUM_COLORS; i++) {
    const char* colorName = (const char*)pgm_read_word(&colorTable[i].name);
    Serial.print(F("  ")); Serial.print(colorName);
    if ((i + 1) % 5 == 0) Serial.println();
  }
  Serial.println();
  Serial.println(F("========================"));
}
