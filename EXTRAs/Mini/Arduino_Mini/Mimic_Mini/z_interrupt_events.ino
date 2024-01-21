// Read seriald data from the RasPi, telling the motors and LEDs what to do.
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
    if (test2.substring(0, delimeter) == "PSARJ")
    {
      PSARJ = (test2.substring(delimeter + 1)).toFloat();
    }
    //    else if (test2.substring(0, delimeter) == "SmartRolloverBGA")
    //    {
    //      SmartRolloverBGA = int((test2.substring(delimeter + 1)).toFloat());
    //    }
    //    else if (test2.substring(0, delimeter) == "SmartRolloverSARJ")
    //    {
    //      SmartRolloverSARJ = int((test2.substring(delimeter + 1)).toFloat());
    //    }
    //    else if (test2.substring(0, delimeter) == "NULLIFY")
    //    {
    //      NULLIFY = int((test2.substring(delimeter + 1)).toFloat());
    //    }
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

    else if (test2.substring(0, delimeter) == "MimiSetAllServos")
    {
      MimiSetAllServos_Flag = 1;
      MiniAllServoVals = (test2.substring(delimeter + 1)).toFloat();
      Serial.println("--- Setting all Mimi Servos to zero ---");
    }

    else if (test2.substring(0, delimeter) == "Mini_MidPosServos")
    {
      Mini_MidPosServos_Flag = 1;
      //      MiniAllServoVals= (test2.substring(delimeter + 1)).toFloat();
      Serial.println("--- Setting all Servos to center of travel ---");
    }

    else if (test2.substring(0, delimeter) == "Mini_MinPosServos")
    {
      Mini_MinPosServos_Flag = 1;
      //      MiniAllServoVals= (test2.substring(delimeter + 1)).toFloat();
      Serial.println("--- Setting all Servos to minimum position ---");
    }

        else if (test2.substring(0, delimeter) == "Mini_MaxPosServos")
    {
      Mini_MaxPosServos_Flag = 1;
      //      MiniAllServoVals= (test2.substring(delimeter + 1)).toFloat();
      Serial.print("--- Setting all Servos to maximum position ---");
    }
    
    else if (test2.substring(0, delimeter) == "Mini_ServosInstallPos")
    {
      Mini_ServosInstallPos_Flag = 1;
      //      MiniAllServoVals= (test2.substring(delimeter + 1)).toFloat();
      Serial.println("--- Setting BGA & SARJ servos to Min, TRRJ to Mid ---");
    }
    
    else if (test2.substring(0, delimeter) == "SSARJ")
    {
      SSARJ = (test2.substring(delimeter + 1)).toFloat();
    }
    else if (test2.substring(0, delimeter) == "PTRRJ")
    {
      PTRRJ = (test2.substring(delimeter + 1)).toFloat();
      PTRRJ = map(PTRRJ, -105, 105, 0, 180);
    }
    else if (test2.substring(0, delimeter) == "STRRJ")
    {
      STRRJ = (test2.substring(delimeter + 1)).toFloat();
      STRRJ = map(STRRJ, -105, 105, 0, 180);
    }
    else if (test2.substring(0, delimeter) == "B1B")
    {
      B1B = (test2.substring(delimeter + 1)).toFloat();
    }
    else if (test2.substring(0, delimeter) == "B1A")
    {
      B1A = (test2.substring(delimeter + 1)).toFloat();
    }
    else if (test2.substring(0, delimeter) == "B2B")
    {
      B2B = (test2.substring(delimeter + 1)).toFloat();
    }
    else if (test2.substring(0, delimeter) == "B2A")
    {
      B2A = (test2.substring(delimeter + 1)).toFloat();
    }
    else if (test2.substring(0, delimeter) == "B3B")
    {
      B3B = (test2.substring(delimeter + 1)).toFloat();
    }
    else if (test2.substring(0, delimeter) == "B3A")
    {
      B3A = (test2.substring(delimeter + 1)).toFloat();
    }
    else if (test2.substring(0, delimeter) == "B4B")
    {
      B4B = (test2.substring(delimeter + 1)).toFloat();
    }
    else if (test2.substring(0, delimeter) == "B4A")
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
