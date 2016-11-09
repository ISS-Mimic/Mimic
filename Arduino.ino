#include <Wire.h>
#include <Stepper.h>

Stepper motor(200,4,5,6,7);

double PSARJdiff = 0.00;
double oldPSARJstep = 0.00;
boolean startup = true;
double oldangle = 0.00;
double oldPSARJ = 0.00;
double PSARJcheck = 0.00;
double PSARJstep = 0.00;
double Beta1B = 0.0;
double Beta2B = 0.0;
double Beta3B = 0.0;
double Beta4B = 0.0;
double Beta1A = 0.0;
double Beta2A = 0.0;
double Beta3A = 0.0;
double Beta4A = 0.0;
double PSARJ = 0.0;
double SSARJ = 0.0;
double PTRRJ = 0.0;
double STRRJ = 0.0;
boolean AOS = false;

void setup()
{
  Wire.begin(4);                // join i2c bus with address #4
  Wire.onReceive(receiveEvent); // register event
  Serial.begin(9600);           // start serial for output
  motor.setSpeed(10);  // 10 rpm
  startup = true;
}

void loop()
{
  delay(200);
  /*
  //delay(1000);
  //Serial.print("PSARJ ");
  //Serial.println(PSARJ);  //print the I2C received value
  Serial.print("SSARJ ");
  Serial.println(SSARJ);
  Serial.print("PTRRJ ");
  Serial.println(PTRRJ);
  Serial.print("STRRJ ");
  Serial.println(STRRJ);
  Serial.print("Beta1B ");
  Serial.println(Beta1B);
  Serial.print("Beta2B ");
  Serial.println(Beta2B);
  Serial.print("Beta3B ");
  Serial.println(Beta3B);
  Serial.print("Beta4B ");
  Serial.println(Beta4B);
  Serial.print("Beta1A ");
  Serial.println(Beta1A);
  Serial.print("Beta2A ");
  Serial.println(Beta2A);
  Serial.print("Beta3A ");
  Serial.println(Beta3A);
  Serial.print("Beta4A ");
  Serial.println(Beta4A);
  Serial.print("AOS ");
  Serial.println(AOS);

 */

  PSARJdiff = abs(PSARJ - oldPSARJ);
  Serial.print("PSARJdiff: ");
  Serial.println(PSARJdiff);
  if(startup)
  {
    oldPSARJ = PSARJ;
    PSARJstep = ((200.00/360.00)*PSARJ);
    startup = false;
    motor.step(PSARJstep);
    Serial.print("startup & step");
    Serial.println(PSARJstep);
  }
  
  if(!startup && (PSARJdiff > 1)) //check if the angle is different
  {   
    PSARJstep = ((200.00/360.00)*PSARJ);
    oldPSARJstep = ((200.00/360.00)*oldPSARJ);
    double newstep = PSARJstep - oldPSARJstep;
    motor.step(newstep);
    
    Serial.print("new step");
    Serial.println(newstep);
    oldPSARJ = PSARJ; 
  }
  
}

void receiveEvent(int howMany)
{
  String test = "";
  while(1 < Wire.available()) // loop through all but the last
  {
    char c = Wire.read(); // receive byte as a character
    test += c;
    
  }
  Serial.println(test);

  PSARJ = test.toFloat();

  //int spaceindex = test.indexOf(' ');
  //String test2 = "";
  //test2 = test.substring(spaceindex+1);
  
  //int decimalindex = test2.indexOf('.');

  /*
  if(test.substring(0,5)=="PSARJ")
  {
    PSARJ = test2.substring(0,decimalindex+2).toFloat();
  }
  if(test.substring(0,5)=="SSARJ")
  {
    SSARJ = test2.substring(0,decimalindex+2).toFloat();
  }
  if(test.substring(0,5)=="PTRRJ")
  {
    PTRRJ = test2.substring(0,decimalindex+2).toFloat();
  }  
  if(test.substring(0,5)=="STRRJ")
  {
    STRRJ = test2.substring(0,decimalindex+2).toFloat();
  }
  if(test.substring(0,6)=="Beta1B")
  {
    Beta1B = test2.substring(0,decimalindex+2).toFloat();
  }
  if(test.substring(0,6)=="Beta2B")
  {
    Beta2B = test2.substring(0,decimalindex+2).toFloat();
  }
  if(test.substring(0,6)=="Beta3B")
  {
    Beta3B = test2.substring(0,decimalindex+2).toFloat();
  }
  if(test.substring(0,6)=="Beta4B")
  {
    Beta4B = test2.substring(0,decimalindex+2).toFloat();
  }
  if(test.substring(0,6)=="Beta1A")
  {
    Beta1A = test2.substring(0,decimalindex+2).toFloat();
  }
  if(test.substring(0,6)=="Beta2A")
  {
    Beta2A = test2.substring(0,decimalindex+2).toFloat();
  }
  if(test.substring(0,6)=="Beta3A")
  {
    Beta3A = test2.substring(0,decimalindex+2).toFloat();
  }
  if(test.substring(0,6)=="Beta4A")
  {
    Beta4A = test2.substring(0,decimalindex+2).toFloat();
  }
  if(test.substring(0,3)=="AOS")
  {
    Serial.println(test);
    if(test.substring(4)=="Siqnal Acquire")
    {
      AOS = true;
      //Serial.println("AOS true!");
    }
    else
    {
      AOS = false;
      //Serial.println("AOS false!");
      //Serial.println(test);
    }
  }
  */
  
  int x = Wire.read();    // receive byte as an integer
  //Serial.println(x);         // print the integer
  //Serial.println();
  Serial.flush();
}
