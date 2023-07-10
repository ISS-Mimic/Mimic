void loop() {

  delay(1);
  if (Serial.available())
  {
    checkSerial();
  }
  delay(1);

  if (MimiSetAllServos_Flag == 1)
  {
    MimiSetAllServos_Flag = 0;
    B1A = MiniAllServoVals;
    B3A = MiniAllServoVals;
    B1B = MiniAllServoVals;
    B3B = MiniAllServoVals;

    B2B = MiniAllServoVals;
    B4B = MiniAllServoVals;
    B2A = MiniAllServoVals;
    B4A = MiniAllServoVals;

    PSARJ = MiniAllServoVals;
    SSARJ = MiniAllServoVals;
    
    // biasing TRRJ commands, since they use +/- 180 deg commands, unlike BGAs & SARJ which use 0-360 deg commands.
    PTRRJ = MiniAllServoVals-180; 
    STRRJ = MiniAllServoVals-180;
  }

  if (Mini_MidPosServos_Flag == 1)
  {
    Mini_MidPosServos_Flag = 0;
    B1A = 180;
    B3A = 180;
    B1B = 180;
    B3B = 180;

    B2B = 180;
    B4B = 180;
    B2A = 180;
    B4A = 180;

    PSARJ = 180;
    SSARJ = 180;
    
    // TRRJ cmds use +/- 105 deg commands, unlike BGAs & SARJ which use 0-360 deg commands.
    PTRRJ = 90; 
    STRRJ = 90;
  }

    if (Mini_MaxPosServos_Flag == 1)
  {
    Mini_MaxPosServos_Flag = 0;
    B1A = 360;
    B3A = 360;
    B1B = 360;
    B3B = 360;

    B2B = 360;
    B4B = 360;
    B2A = 360;
    B4A = 360;

    PSARJ = 360;
    SSARJ = 360;
    
    // TRRJ cmds use +/- 105 deg commands, unlike BGAs & SARJ which use 0-360 deg commands.
    PTRRJ = 180; 
    STRRJ = 180;
  }

   if (Mini_MinPosServos_Flag == 1)
  {
    Mini_MinPosServos_Flag = 0;
    B1A = 0;
    B3A = 0;
    B1B = 0;
    B3B = 0;

    B2B = 0;
    B4B = 0;
    B2A = 0;
    B4A = 0;

    PSARJ = 0;
    SSARJ = 0;
    
    // TRRJ cmds use +/- 105 deg commands, unlike BGAs & SARJ which use 0-360 deg commands. 
    PTRRJ = 0; 
    STRRJ = 0;
  }




   if (Mini_ServosInstallPos_Flag == 1)
  {
    Mini_ServosInstallPos_Flag = 0;
    B1A = 0;
    B3A = 0;
    B1B = 0;
    B3B = 0;

    B2B = 0;
    B4B = 0;
    B2A = 0;
    B4A = 0;

    PSARJ = 0;
    SSARJ = 0;
    
    // TRRJ cmds use +/- 105 deg commands, unlike BGAs & SARJ which use 0-360 deg commands. 
    //**Switching to 300 deg motors, so setting midpoint pos a bit. May require tweaking
    PTRRJ = 180; 
    STRRJ = 180;
  }



  // servonum_B2B = 1;

  pulselen_B1A = map(B1A, 0, 360, SERVOMIN, SERVOMAX);
  pulselen_B3A = map(B3A, 0, 360, SERVOMIN, SERVOMAX);
  pulselen_B1B = map(B1B, 0, 360, SERVOMIN, SERVOMAX);
  pulselen_B3B = map(B3B, 0, 360, SERVOMIN, SERVOMAX);

  pulselen_B2B = map(B2B, 0, 360, SERVOMIN, SERVOMAX);
  pulselen_B4B = map(B4B, 0, 360, SERVOMIN, SERVOMAX);
  pulselen_B2A = map(B2A, 0, 360, SERVOMIN, SERVOMAX);
  pulselen_B4A = map(B4A, 0, 360, SERVOMIN, SERVOMAX);

  pulselen_PSARJ = map(PSARJ, 0, 360, SERVOMIN, SERVOMAX);
  pulselen_SSARJ = map(SSARJ, 0, 360, SERVOMIN, SERVOMAX);
  
  // TRRJ commands are +/- 180 degrees (from ISS), so scaling differently than BGAs and SARJs, which are 0-360 deg.
  pulselen_PTRRJ = map(PTRRJ, 0, 360, SERVOMIN, SERVOMAX); 
  pulselen_STRRJ = map(STRRJ, 0, 360,  SERVOMIN, SERVOMAX);


  pwm.setPWM(servonum_B1A, 0, pulselen_B1A);
  pwm.setPWM(servonum_B3A, 0, pulselen_B3A);
  pwm.setPWM(servonum_B1B, 0, pulselen_B1B);
  pwm.setPWM(servonum_B3B, 0, pulselen_B3B);

  pwm.setPWM(servonum_B2B, 0, pulselen_B2B);
  pwm.setPWM(servonum_B4B, 0, pulselen_B4B);
  pwm.setPWM(servonum_B2A, 0, pulselen_B2A);
  pwm.setPWM(servonum_B4A, 0, pulselen_B4A);

  pwm.setPWM(servonum_PSARJ, 0, pulselen_PSARJ);
  pwm.setPWM(servonum_SSARJ, 0, pulselen_SSARJ);
  pwm.setPWM(servonum_PTRRJ, 0, pulselen_PTRRJ);
  pwm.setPWM(servonum_STRRJ, 0, pulselen_STRRJ);



  Serial.print("B1A: ");  Serial.print(B1A); Serial.print(" | "); Serial.println( pulselen_B1A); 
  Serial.print("B3A: ");  Serial.print(B3A); Serial.print(" | "); Serial.println( pulselen_B3A);
  Serial.print("B1B: ");  Serial.print(B1B); Serial.print(" | "); Serial.println( pulselen_B1B);
  Serial.print("B3B: ");  Serial.print(B3B); Serial.print(" | "); Serial.println( pulselen_B3B);

  Serial.print("B2B: ");  Serial.print(B2B); Serial.print(" | "); Serial.println( pulselen_B2B);
  Serial.print("B4B: ");  Serial.print(B4B); Serial.print(" | "); Serial.println( pulselen_B4B);
  Serial.print("B2A: ");  Serial.print(B2A); Serial.print(" | "); Serial.println( pulselen_B2A);
  Serial.print("B4A: ");  Serial.print(B4A); Serial.print(" | "); Serial.println( pulselen_B4A);

  Serial.print("PSARJ: ");  Serial.print(PSARJ); Serial.print(" | "); Serial.println( pulselen_PSARJ);
  Serial.print("SSARJ: ");  Serial.print(SSARJ); Serial.print(" | "); Serial.println( pulselen_SSARJ);
  Serial.print("PTRRJ: ");  Serial.print(PTRRJ); Serial.print(" | "); Serial.println( pulselen_PTRRJ);
  Serial.print("STRRJ: ");  Serial.print(STRRJ); Serial.print(" | "); Serial.println( pulselen_STRRJ);


  //  pwm.setPWM(servonum, 0, pulselen);

  delay(500);

  //  // ============== Time measures ===================================================
  //  LoopStartMillis = millis();
  //  delta_t_millis = max(LoopStartMillis - previousMillis, 1); // ensure always equal to at least one, for later inversion
  //  inverse_delta_t_millis = 1 / ((float) delta_t_millis); // BCM mod 10/28/2018: for some reason, was not inverted (just = value, rather than 1/value).
  //  millisChPt1 = millis() - LoopStartMillis;
  //  // ================================================================================

}
