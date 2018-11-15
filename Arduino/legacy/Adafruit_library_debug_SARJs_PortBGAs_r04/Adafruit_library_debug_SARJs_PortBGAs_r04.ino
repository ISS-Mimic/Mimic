// This is where the bug was posted to Adafruit Forum:
// https://forums.adafruit.com/viewtopic.php?f=63&t=142763
// Hall Effect sensor powered by the board's 3.3V pin (within spec of the sensor),
// and two output signals from the Hall sensor fed to digital pins 6 & 7.

// Board #2: Pin #3 never shows a digital toggler.  
// Board #3: Pin pair 4,5 doesn't work.

#include <Encoder.h>

Encoder myEnc_1(0, 1);//  
//Encoder myEnc_2(2, 3);
Encoder myEnc_3(4, 5);
Encoder myEnc_4(6, 7);

//Encoder myEnc_5(8, 9);
//Encoder myEnc_6(10, 11);
Encoder myEnc_7(11, 12);
// library suggests skipping 13 since tied to board LED, but trying it here anyway
Encoder myEnc_8(14, 15); //AKA analog pins A0, A1
Encoder myEnc_9(16, 17); //AKA analog pins A2, A3

//Encoder myEnc_10(28, 29);
// skipping pins A4,A5 since Motor Shield V2.3 ties these to SCL,SDA

int Count_E1 = 0;
//int Count_E2 = 0;
int Count_E3 = 0;
int Count_E4 = 0;
//int Count_E5 = 0;
//int Count_E6 = 0;
int Count_E7 = 0;
int Count_E8 = 0;
int Count_E9 = 0;
//int Count_E10 = 0;

int D0 = 0;
int D1 = 0;
//int D2 = 0;
//int D3 = 0;
int D4 = 0;
int D5 = 0;
int D6 = 0;
int D7 = 0;
//int D8 = 0;
//int D9 = 0;
//int D10 = 0;
int D11 = 0;
int D12 = 0;
int D13 = 0;

int D14 = 0;
int D15 = 0;
int D16 = 0;
int D17 = 0;


//int D28 = 0;
//int D29 = 0;

void setup() {

  Serial.begin(9600);
  Serial.setTimeout(50);

}

void loop() {
  Count_E1 = myEnc_1.read(); 
//  Count_E2 = myEnc_2.read();
  Count_E3 = myEnc_3.read();
  Count_E4 = myEnc_4.read();
//  Count_E5 = myEnc_5.read();
//  Count_E6 = myEnc_6.read();
  Count_E7 = myEnc_7.read();
  Count_E8 = myEnc_8.read();
  Count_E9 = myEnc_9.read();
//  Count_E10 = myEnc_10.read();

  D0 = digitalRead(0);
  D1 = digitalRead(1);
//  D2 = digitalRead(2);
//  D3 = digitalRead(3);
  D4 = digitalRead(4);
  D5 = digitalRead(5);
  D6 = digitalRead(6);
  D7 = digitalRead(7);
//  D8 = digitalRead(8);
//  D9 = digitalRead(9);
//  D10 = digitalRead(10);
  D11 = digitalRead(11);
  D12 = digitalRead(12);
  D13 = digitalRead(13);

  D14 = digitalRead(14);
  D15 = digitalRead(15);
  D16 = digitalRead(16);
  D17 = digitalRead(17);

//  D28 = digitalRead(28);
//  D29 = digitalRead(29);


  Serial.print("E1:");
  Serial.print( Count_E1);
//  Serial.print(",E2:");
//  Serial.print( Count_E2);
  Serial.print(",E3:");
  Serial.print( Count_E3);
  Serial.print(",E4:");
  Serial.print( Count_E4);

//  Serial.print(",E5:");
//  Serial.print( Count_E5);
//  Serial.print(",E6:");
//  Serial.print( Count_E6);
  Serial.print(",E7:");
  Serial.print( Count_E7);
  Serial.print(",E8:");
  Serial.print( Count_E8);
  Serial.print(",E9:");
  Serial.print( Count_E9);
  Serial.print(",E10:");
//  Serial.print( Count_E10);


  Serial.print(",D0:");
  Serial.print( D0);
  Serial.print(",D1:");
  Serial.print( D1);
//  Serial.print(",D2:");
//  Serial.print( D2);
//
//  Serial.print("D3: ");
//  Serial.print( D3);
  Serial.print(",D4:");
  Serial.print( D4);
  Serial.print(",D5:");
  Serial.print( D5);
  Serial.print(",D6:");

  Serial.print( D6);
  Serial.print(",D7:");
  Serial.print( D7);
//  Serial.print(",D8: ");
//  Serial.print( D8);
//
//  Serial.print("D9:");
//  Serial.print( D9);
//  Serial.print(",D10:");
//  Serial.print( D10);
  Serial.print(",D11:");
  Serial.print( D11);
  Serial.print(",D12:");
  Serial.print( D12);
  Serial.print(",D13:");
  Serial.print( D13);

  Serial.print(",D14:");
  Serial.print( D14);
  Serial.print(",D15:");
  Serial.print( D15);
  Serial.print(",D16:");
  Serial.print( D16);
  Serial.print(",D17:");
  Serial.print( D17);


//
//  Serial.print(",D28:");
//  Serial.print( D28);
//  Serial.print(",D29:");
//  Serial.print( D29);
  Serial.println("");
  delay(10);

}
