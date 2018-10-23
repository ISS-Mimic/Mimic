
void checkSerial()
{
  //digitalWrite(ledBluePin, HIGH);
  test = "";
  
  while(Serial.available())  
  {
    test = Serial.readString();
  }
 Serial1.println(test);
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
      B1B = (test2.substring(delimeter+1)).toFloat();
    }
    else if(test2.substring(0,delimeter)=="Beta1A")
    {
      B1A = (test2.substring(delimeter+1)).toFloat();
    }
    else if(test2.substring(0,delimeter)=="Beta2B")
    {
      B2B = (test2.substring(delimeter+1)).toFloat();
    }
    else if(test2.substring(0,delimeter)=="Beta2A")
    {
      B2A = signflip*(test2.substring(delimeter+1)).toFloat();
    }
    else if(test2.substring(0,delimeter)=="Beta3B")
    {
      B3B = (test2.substring(delimeter+1)).toFloat();
    }
    else if(test2.substring(0,delimeter)=="Beta3A")
    {
      B3A = (test2.substring(delimeter+1)).toFloat();
    }
    else if(test2.substring(0,delimeter)=="Beta4B")
    {
      B4B =  signflip*(test2.substring(delimeter+1)).toFloat();
    }
    else if(test2.substring(0,delimeter)=="Beta4A")
    {
      B4A = (test2.substring(delimeter+1)).toFloat();
    }
    else if(test2.substring(0,delimeter)=="AOS")
    {
      //Serial.println(test2);
      AOS = (test2.substring(delimeter+1)).toFloat();
      //Serial.println(AOS);
      if(AOS == 1.00)
      {
        //digitalWrite(ledGreenPin, HIGH);
      }
      else
      {
        //digitalWrite(ledRedPin, HIGH);
      }
    }
  }
  
}
