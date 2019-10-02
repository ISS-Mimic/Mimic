
//float Kp_PSARJ = 10; // Proportional Gain of PID
//float Ki_PSARJ = 2; // Integral Gain of PID
//float Kd_PSARJ = 2; // Derivative Gain of PID


void checkSerial()
{
  //digitalWrite(ledBluePin, HIGH);
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
    if (test2.substring(0, delimeter) == "SSARJ") // BCM lies to get stbd going, June 7, 2019
    {
      PSARJ = (test2.substring(delimeter + 1)).toFloat();
    }

//    else if (test2.substring(0, delimeter) == "Kp_PSARJ")
//    {
//      Kp_PSARJ = (test2.substring(delimeter + 1)).toFloat();
//    }
//    else if (test2.substring(0, delimeter) == "Ki_PSARJ")
//    {
//      Ki_PSARJ = (test2.substring(delimeter + 1)).toFloat();
//    }
//    else if (test2.substring(0, delimeter) == "Kd_PSARJ")
//    {
//      Kd_PSARJ = (test2.substring(delimeter + 1)).toFloat();
//    }

//    else if (test2.substring(0, delimeter) == "SSARJ")
//    {
//      SSARJ = (test2.substring(delimeter + 1)).toFloat();
//    }
//    else if (test2.substring(0, delimeter) == "PTRRJ")
//    {
//      PTRRJ = (test2.substring(delimeter + 1)).toFloat();
//    }
    else if (test2.substring(0, delimeter) == "STRRJ")
    {
      PTRRJ = (test2.substring(delimeter + 1)).toFloat();
    }
    else if (test2.substring(0, delimeter) == "SmartRolloverBGA")
    {
      SmartRolloverBGA = int((test2.substring(delimeter + 1)).toFloat());
    }
    else if (test2.substring(0, delimeter) == "SmartRolloverSARJ")
    {
      SmartRolloverSARJ = int((test2.substring(delimeter + 1)).toFloat());
    }        
//    else if (test2.substring(0, delimeter) == "Beta1B")
//    {
//      B1B = (test2.substring(delimeter + 1)).toFloat();
//    }
//    else if (test2.substring(0, delimeter) == "Beta1A")
//    {
//      B1A = (test2.substring(delimeter + 1)).toFloat();
//    }
    else if (test2.substring(0, delimeter) == "Beta3B") // BCM lies to get stbd going, June 7, 2019
    {
      B2B = (test2.substring(delimeter + 1)).toFloat();
    }
    else if (test2.substring(0, delimeter) == "Beta3A") // BCM lies to get stbd going, June 7, 2019
    {
      B2A = (test2.substring(delimeter + 1)).toFloat();
    }
//    else if (test2.substring(0, delimeter) == "Beta3B")
//    {
//      B3B = (test2.substring(delimeter + 1)).toFloat();
//    }
//    else if (test2.substring(0, delimeter) == "Beta3A")
//    {
//      B3A = (test2.substring(delimeter + 1)).toFloat();
//    }
    else if (test2.substring(0, delimeter) == "Beta1B")// BCM lies to get stbd going, June 7, 2019
    {
      B4B = (test2.substring(delimeter + 1)).toFloat();
    }
    else if (test2.substring(0, delimeter) == "Beta1A") // BCM lies to get stbd going, June 7, 2019
    {
      B4A = (test2.substring(delimeter + 1)).toFloat();
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
