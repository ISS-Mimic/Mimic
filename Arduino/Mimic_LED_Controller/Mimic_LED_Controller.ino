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

// Color structure and lookup table
struct Color {
  const char* name;
  uint8_t r, g, b;
};

// Comprehensive color palette - easy to add new colors
Color colorTable[] = {
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
  Serial.setTimeout(100);
  
  // Initialize NeoPixel strips
  portIEA.begin();
  stbdIEA.begin();
  
  // Set all LEDs to off initially
  setAllLEDs("Off");
  
  Serial.println("Mimic LED Controller Ready");
  Serial.println("Commands: LED_1A=Red, LED_2B=Blue, etc.");
  Serial.println("Patterns: PATTERN_RAINBOW, PATTERN_ALTERNATING");
  Serial.println("Animations: ANIMATE_PULSE, ANIMATE_CHASE");
  Serial.println("Special: DISCO, RESET, STATUS");
}

void loop() 
{
  // Check for serial commands
  if (Serial.available()) 
  {
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
}

void checkSerial() 
{
  String receivedData = Serial.readStringUntil('\n');
  receivedData.trim(); // Remove whitespace
  
  if (receivedData.length() == 0) return;
  
  Serial.print("Received: ");
  Serial.println(receivedData);
  
  // Parse command
  if (receivedData.startsWith("LED_")) {
    parseLEDCommand(receivedData);
  } else if (receivedData.startsWith("PATTERN_")) {
    parsePatternCommand(receivedData);
  } else if (receivedData.startsWith("ANIMATE_")) {
    parseAnimationCommand(receivedData);
  } else if (receivedData == "DISCO") {
    discoMode = true;
    pulseMode = false;
    chaseMode = false;
    Serial.println("Disco mode activated");
  } else if (receivedData == "RESET") {
    resetAllLEDs();
    Serial.println("All LEDs reset to off");
  } else if (receivedData == "STATUS") {
    printStatus();
  } else if (receivedData == "HELP") {
    printHelp();
  } else {
    Serial.print("Unknown command: ");
    Serial.println(receivedData);
  }
}

void parseLEDCommand(String command) {
  // Format: LED_1A=Red, LED_SM=Blue, etc.
  int equalsIndex = command.indexOf('=');
  if (equalsIndex == -1) {
    Serial.println("Invalid LED command format. Use: LED_GROUP=COLOR");
    return;
  }
  
  String group = command.substring(4, equalsIndex); // Remove "LED_" prefix
  String colorName = command.substring(equalsIndex + 1);
  
  // Find the color in our lookup table
  Color* color = findColor(colorName);
  if (color == NULL) {
    Serial.print("Unknown color: ");
    Serial.println(colorName);
    return;
  }
  
  // Apply color to the specified LED group
  if (group == "1A") {
    setLEDGroup(stbdIEA, stbd_LEDs_1A, 6, *color);
  } else if (group == "1B") {
    setLEDGroup(stbdIEA, stbd_LEDs_1B, 6, *color);
  } else if (group == "2A") {
    setLEDGroup(portIEA, port_LEDs_2A, 6, *color);
  } else if (group == "2B") {
    setLEDGroup(portIEA, port_LEDs_2B, 6, *color);
  } else if (group == "3A") {
    setLEDGroup(stbdIEA, stbd_LEDs_3A, 6, *color);
  } else if (group == "3B") {
    setLEDGroup(stbdIEA, stbd_LEDs_3B, 6, *color);
  } else if (group == "4A") {
    setLEDGroup(portIEA, port_LEDs_4A, 6, *color);
  } else if (group == "4B") {
    setLEDGroup(portIEA, port_LEDs_4B, 6, *color);
  } else if (group == "ALL") {
    setAllLEDs(colorName);
  } else {
    Serial.print("Unknown LED group: ");
    Serial.println(group);
    return;
  }
  
  Serial.print("Set ");
  Serial.print(group);
  Serial.print(" to ");
  Serial.println(colorName);
}

void parsePatternCommand(String command) {
  // Format: PATTERN_RAINBOW, PATTERN_ALTERNATING, etc.
  String pattern = command.substring(8); // Remove "PATTERN_" prefix
  
  if (pattern == "RAINBOW") {
    setRainbowPattern();
  } else if (pattern == "ALTERNATING") {
    setAlternatingPattern();
  } else if (pattern == "RED_ALERT") {
    setRedAlertPattern();
  } else if (pattern == "BLUE_PATTERN") {
    setBluePattern();
  } else {
    Serial.print("Unknown pattern: ");
    Serial.println(pattern);
  }
}

void parseAnimationCommand(String command) {
  // Format: ANIMATE_PULSE, ANIMATE_CHASE, etc.
  String animation = command.substring(8); // Remove "ANIMATE_" prefix
  
  if (animation == "PULSE") {
    pulseMode = true;
    discoMode = false;
    chaseMode = false;
    Serial.println("Pulse animation activated");
  } else if (animation == "CHASE") {
    chaseMode = true;
    discoMode = false;
    pulseMode = false;
    Serial.println("Chase animation activated");
  } else if (animation == "STOP") {
    discoMode = false;
    pulseMode = false;
    chaseMode = false;
    Serial.println("All animations stopped");
  } else {
    Serial.print("Unknown animation: ");
    Serial.println(animation);
  }
}

Color* findColor(String colorName) {
  for (int i = 0; i < NUM_COLORS; i++) {
    if (colorName.equalsIgnoreCase(colorTable[i].name)) {
      return &colorTable[i];
    }
  }
  return NULL;
}

void setLEDGroup(Adafruit_NeoPixel& strip, int* ledArray, int arraySize, Color color) {
  for (int i = 0; i < arraySize; i++) {
    strip.setPixelColor(ledArray[i], strip.Color(color.r, color.g, color.b));
  }
  strip.show();
}

void setAllLEDs(String colorName) {
  Color* color = findColor(colorName);
  if (color == NULL) {
    Serial.print("Unknown color: ");
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
  Serial.println("Rainbow pattern applied");
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
  Serial.println("Alternating pattern applied");
}

void setRedAlertPattern() {
  setAllLEDs("Red");
  Serial.println("Red alert pattern applied");
}

void setBluePattern() {
  setAllLEDs("Blue");
  Serial.println("Blue pattern applied");
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
  Serial.println("=== LED Controller Status ===");
  Serial.print("Disco Mode: "); Serial.println(discoMode ? "ON" : "OFF");
  Serial.print("Pulse Mode: "); Serial.println(pulseMode ? "ON" : "OFF");
  Serial.print("Chase Mode: "); Serial.println(chaseMode ? "ON" : "OFF");
  Serial.println("=============================");
}

void printHelp() {
  Serial.println("=== Available Commands ===");
  Serial.println("LED Commands:");
  Serial.println("  LED_1A=Red, LED_2B=Blue, etc.");
  Serial.println("  LED_ALL=White (set all arrays)");
  Serial.println("");
  Serial.println("Pattern Commands:");
  Serial.println("  PATTERN_RAINBOW");
  Serial.println("  PATTERN_ALTERNATING");
  Serial.println("  PATTERN_RED_ALERT");
  Serial.println("  PATTERN_BLUE_PATTERN");
  Serial.println("");
  Serial.println("Animation Commands:");
  Serial.println("  ANIMATE_PULSE");
  Serial.println("  ANIMATE_CHASE");
  Serial.println("  ANIMATE_STOP");
  Serial.println("");
  Serial.println("Special Commands:");
  Serial.println("  DISCO, RESET, STATUS, HELP");
  Serial.println("");
  Serial.println("Available Colors:");
  for (int i = 0; i < NUM_COLORS; i++) {
    Serial.print("  "); Serial.print(colorTable[i].name);
    if ((i + 1) % 5 == 0) Serial.println();
  }
  Serial.println();
  Serial.println("========================");
}
