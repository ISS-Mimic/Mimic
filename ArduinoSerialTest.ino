#include <string.h>

const int ledPin = 13;
String test;

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
double AOS = 0.00;

void setup()
{
  pinMode(ledPin, OUTPUT);
  Serial.begin(9600);
  Serial1.begin(115200);
  Serial1.setTimeout(50);
}

void loop()
{
  digitalWrite(ledPin, LOW);
  if(Serial1.available())
  {
    checkSerial();
  }
}
void checkSerial()
{
  digitalWrite(ledPin, HIGH);
  test = "";
  
  while(Serial1.available())  
  {
    test = Serial1.readString();
  }

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
    if(test2.substring(0,delimeter)=="PSARJ")
    {
      PSARJ = (test2.substring(delimeter+1)).toFloat();
    }  
    else if(test2.substring(0,delimeter)=="SSARJ")
    {
      SSARJ = (test2.substring(delimeter+1)).toFloat();
    }  
    else if(test2.substring(0,delimeter)=="PTRRJ")
    {
      PTRRJ = (test2.substring(delimeter+1)).toFloat();
    } 
    else if(test2.substring(0,delimeter)=="STRRJ")
    {
      STRRJ = (test2.substring(delimeter+1)).toFloat();
    } 
    else if(test2.substring(0,delimeter)=="Beta1B")
    {
      Beta1B = (test2.substring(delimeter+1)).toFloat();
    }
    else if(test2.substring(0,delimeter)=="Beta1A")
    {
      Beta1A = (test2.substring(delimeter+1)).toFloat();
    }
    else if(test2.substring(0,delimeter)=="Beta2B")
    {
      Beta2B = (test2.substring(delimeter+1)).toFloat();
    }
    else if(test2.substring(0,delimeter)=="Beta2A")
    {
      Beta2A = (test2.substring(delimeter+1)).toFloat();
    }
    else if(test2.substring(0,delimeter)=="Beta3B")
    {
      Beta3B = (test2.substring(delimeter+1)).toFloat();
    }
    else if(test2.substring(0,delimeter)=="Beta3A")
    {
      Beta3A = (test2.substring(delimeter+1)).toFloat();
    }
    else if(test2.substring(0,delimeter)=="Beta4B")
    {
      Beta4B = (test2.substring(delimeter+1)).toFloat();
    }
    else if(test2.substring(0,delimeter)=="Beta4A")
    {
      Beta4A = (test2.substring(delimeter+1)).toFloat();
    }
    else if(test2.substring(0,delimeter)=="AOS")
    {
      AOS = (test2.substring(delimeter+1)).toFloat();
    }
  }
}
