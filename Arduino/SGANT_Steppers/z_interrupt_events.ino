

void checkSerial()
{
 
  test = "";

  while (Serial.available())
  {
    test = Serial.readString();
  }
  //  Serial1.println(test);
  char sz[test.length() + 1];
  char copy[test.length() + 1];
  strcpy(sz, test.c_str());
  char *p = sz;
  char *str;
  int delimeter = 0;
  String test2 = "";

  while ((str = strtok_r(p, " ", &p)) != NULL)
  {
    test2 = String(str);
    delimeter = test2.indexOf('=');
    if (test2.substring(0, delimeter) == "SGANT_El_deg")
    {
      SGANT_El_deg = (test2.substring(delimeter + 1)).toFloat();
    }
    else if (test2.substring(0, delimeter) == "SGANT_xEl_deg")
    {
      SGANT_xEl_deg = int((test2.substring(delimeter + 1)).toFloat());
    }  
     
    else if (test2.substring(0, delimeter) == "AOS")
    {
      //Serial.println(test2);
      AOS = (test2.substring(delimeter + 1)).toFloat();
      //Serial.println(AOS);
      if (AOS == 1.00)
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
