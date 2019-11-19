
/// MIMIC!!! MIMIC!!!
// Still need to add servo stuff for TRRJs
//
// This version is just for STBD BGAs, board 78
// PSARJ is Motor 1, Encoder pins 2,5; Pin 3 not working properly on this Arduino Metro.  Updated 7/6/2019
// SSARJ is Motor 2, Encoder pins 7,8
//
//// for LCD  =============================================
//
//#include <SPI.h>
//#include <Wire.h>
//#include <Adafruit_GFX.h>
//#include <Adafruit_SSD1306.h>
//static char dtostrfbuffer[21];  // added Oct 20
//#include <avr/dtostrf.h>
//
//#define OLED_RESET 4 // likely unnecessary
//Adafruit_SSD1306 display(OLED_RESET);
//
//#define NUMFLAKES 10
//#define XPOS 0
//#define YPOS 1
//#define DELTAY 2
//
//
//#define LOGO16_GLCD_HEIGHT 16
//#define LOGO16_GLCD_WIDTH  16
//static const unsigned char PROGMEM logo16_glcd_bmp[] =
//{ B00000000, B11000000,
//  B00000001, B11000000,
//  B00000001, B11000000,
//  B00000011, B11100000,
//  B11110011, B11100000,
//  B11111110, B11111000,
//  B01111110, B11111111,
//  B00110011, B10011111,
//  B00011111, B11111100,
//  B00001101, B01110000,
//  B00011011, B10100000,
//  B00111111, B11100000,
//  B00111111, B11110000,
//  B01111100, B11110000,
//  B01110000, B01110000,
//  B00000000, B00110000 };
//// end LCD =============================================
unsigned long previousMillis = 0;
unsigned long LoopStartMillis = 0;
unsigned long  delta_t_millis = 1;
float inverse_delta_t_millis = 1;
uint8_t i;
unsigned long mytime;

int SmartRolloverBGA = 0;
int SmartRolloverSARJ = 1;
struct joints
{
  float Kp;
  float Ki;
  float Kd;
  long Count;
  float PosCmd;
  float PosAct;
  float PosErr;
  float PosErr_old;
  float tmpSpeed;
  float dErrDt;
  float dPosErr;
  float IntOld;
  float IntNow;
  int CmdSpeed;
};
joints sarj_port = {10, 1, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};
joints sarj_stbd = {10, 1, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};



void motorfnc(struct joints &myJoint) {
  
  // 150 motor shaft rotations / gearbox output shaft rotation * 12 encoder counts / motor rotation  /(360 deg per /output rotation) = 150*12/360 = 5 encoder counts per output shaft degree
 // myJoint.PosAct = float(myJoint.Count) / (5 * 42 / 12); // / 25; // 150:1 gear ratio, 6 encoder counts per motor shaft rotation 150/6=25;  42 teeth on bull gear. T12 pinion for SARJ
 myJoint.PosAct = float(myJoint.Count) / (150.694*12/360 * 42 / 12);
  // Added Aug 18, 2019 by BCM for "Smart Rollover"
  if (SmartRolloverSARJ == 1) {
    if (abs(myJoint.PosAct) > 360) {
      float tmp_raw_div = myJoint.PosAct / 360.0; // result will be 0.xx, 1.xx, 2.xx, etc.  Solve for the Y in Y.xx, then subtract from the whole.
      // we want (for example) -900.1 degrees to become something in 0..360 range.
      //(double(tmp_raw_div)-double(floor(tmp_raw_div)))*360 - from Octave check
      float tmp_pos = (float(tmp_raw_div) - float(floor(tmp_raw_div))) * 360;
      myJoint.PosAct = tmp_pos;
    }
  }  // end Added Aug 18, 2019

  myJoint.PosErr = myJoint.PosCmd - myJoint.PosAct; // raw position error  
  myJoint.dPosErr = myJoint.PosErr - myJoint.PosErr_old;
  
// Added Aug 18, 2019 by BCM for "Smart Rollover"
  if (SmartRolloverSARJ == 1) {
    if (myJoint.PosErr > 180) {
      myJoint.PosErr =myJoint.PosErr-360;
    }
    if (myJoint.PosErr <-180) {
      myJoint.PosErr = myJoint.PosErr+360;
    }
  }  // end Added Aug 18, 2019  

  if (abs(myJoint.PosErr) < 0.1) {
    myJoint.PosErr = 0;
    myJoint.dPosErr = 0;
    myJoint.PosErr_old = 0;
    myJoint.IntOld = 0;
  }

  myJoint.dErrDt = myJoint.dPosErr * inverse_delta_t_millis * 0.001; // For Derivative
  //IntNow = IntOld + PosErr * inverse_delta_t_millis * 0.001; // For Integrator
  myJoint.IntNow = myJoint.IntOld + myJoint.PosErr * delta_t_millis * 0.001; 
  myJoint.IntOld = myJoint.IntNow;

  // Integrator reset when error sign changes
  if (myJoint.PosErr_old * myJoint.PosErr <= 0) { // sign on error has changed or is zero
    myJoint.IntNow = 0;
    myJoint.IntOld = 0;
  }
  myJoint.PosErr_old = myJoint.PosErr; // For use on the next iteration

  // Calculate motor speed setpoint based on PID constants and computed params for this iteration.
  myJoint.tmpSpeed = myJoint.Kp * myJoint.PosErr + myJoint.Kd * (myJoint.dErrDt) + myJoint.Ki * myJoint.IntNow;
  // Deadband seems to be about 40 (for 5V input to motor board);
  myJoint.CmdSpeed = abs(myJoint.tmpSpeed);
  if ((myJoint.CmdSpeed < 40) && (myJoint.CmdSpeed > 5)) { // We want a dead space at 5 counts, but want it to move for larger vals.
    myJoint.CmdSpeed = 40;
  }
  myJoint.CmdSpeed = max(min(myJoint.CmdSpeed, 250), 0); // At least 10, at most 250.  Update as needed per motor.
}
void motorNULL(struct joints &myJoint) {
    myJoint.PosErr = 0;
    myJoint.dPosErr = 0;
    myJoint.PosErr_old = 0;
    myJoint.IntOld = 0;
    myJoint.IntNow = 0;
    myJoint.Count=0;
    myJoint.PosCmd=0;
    myJoint.PosAct=0;
    myJoint.CmdSpeed=0;
    myJoint.tmpSpeed=0;
}


#include <Encoder.h>

#include <Adafruit_MotorShield.h>
#include "utility/Adafruit_MS_PWMServoDriver.h"
#include <string.h>
#include <Servo.h>
Servo servo_PTRRJ;
Servo servo_STRRJ;

// Create the motor shield object with the default I2C address
//Adafruit_MotorShield AFMS = Adafruit_MotorShield(0x60);  // Check ID
Adafruit_MotorShield AFMS2 = Adafruit_MotorShield(0x61); // Check ID

// Or, create it with a different I2C address (say for stacking)
// Adafruit_MotorShield AFMS = Adafruit_MotorShield(0x61);

// Select which 'port' M1, M2, M3 or M4. In this case, M1,2,4
//Adafruit_DCMotor *myMotorB2A = AFMS.getMotor(1);
//Adafruit_DCMotor *myMotorB4A = AFMS.getMotor(2);
//Adafruit_DCMotor *myMotorB2B = AFMS.getMotor(3);
//Adafruit_DCMotor *myMotorB4B = AFMS.getMotor(4);

Adafruit_DCMotor *myMotorPSARJ = AFMS2.getMotor(1);
Adafruit_DCMotor *myMotorSSARJ = AFMS2.getMotor(2);




//Encoder myEnc2A(0, 1);
//Encoder myEnc4A(2, 3); // was 4,5 but motor was oozing, digital pins were toggleing, but count wasn't incrementing (interrupt prob?) 
//// Pins 9, 10 are used by Servos.
//// Odd issues with Pins 2-4.
//// Pin 13 is nominally used by LED and general guidance from encoder library is to avoid it.
//Encoder myEnc2B(7, 8); // BCM changed from 6,7 to 7,8 on Nov 15, 2018
//Encoder myEnc4B(11, 12);

Encoder myEncPSARJ(5,2);//2, 5);// BCM July 1, 2019: Pin 3 appears burned out on this Metro, so switching from Pin 3 to 4.  Not sure yet if this interupt conflicts with any others. 
Encoder myEncSSARJ(8,7);//7, 8);

// Per here, Analog pins on Metro M0 are also digtial IO. https://learn.adafruit.com/adafruit-metro-m0-express-designed-for-circuitpython/pinouts
// From here, A1 is digital 15, A2 is 16, A3 is 17, A4 is 18, A5 is 19. http://www.pighixxx.net/portfolio_tags/pinout-2/#prettyPhoto[gallery1368]/0/


int D0 = 0;
int D1 = 0;
int D2 =0;
int D3 =0;
int D4 = 0;
int D5 = 0;
int D6 = 0;
int D7 = 0;
int D8 =0;
int D9 =0;
int D10=0;
int D11 = 0;
int D12 = 0;
int D13=0;
int D14 = 0;
int D15 = 0;
int D16 = 0;
int D17 = 0;

void setup() {


  ////// for LCD  =============================================
  ////
  ////
  //  // by default, we'll generate the high voltage from the 3.3v line internally! (neat!)
  //  display.begin(SSD1306_SWITCHCAPVCC, 0x3C);  // initialize with the I2C addr 0x3D (for the 128x64)
  //  // init done
  //
  //  // Show image buffer on the display hardware.
  //  // Since the buffer is intialized with an Adafruit splashscreen
  //  // internally, this will display the splashscreen.
  //  display.display();
  //  delay(2000);
  //
  //  // Clear the buffer.
  //  display.clearDisplay();
  //
  //// end for LCD  =========================================


  // Set some pins to high, just for convenient connection to power Hall Effect Sensors - can't, per above use of these pins
  pinMode(13, OUTPUT);
  digitalWrite(13, HIGH);
  pinMode(6, OUTPUT);
  digitalWrite(6, HIGH);
  //pinMode(A1, OUTPUT);
  //digitalWrite(A1, HIGH);
  //pinMode(A2, OUTPUT);
  //digitalWrite(A2, HIGH);

  // Attach a servo to dedicated pins 9,10.  Note that all shields in the stack will have these as common, so can connect to any.
    servo_PTRRJ.attach(9);
    servo_STRRJ.attach(10);
//  AFMS.begin(200);  // I set this at 200 previously to reduce audible buzz.
  AFMS2.begin(200);  // I set this at 200 previously to reduce audible buzz.

  Serial.begin(9600);
  //Serial3.begin(115200);          //Serial1 is connected to the RasPi
  Serial.setTimeout(50);
  // Serial1.begin(9600);

}
