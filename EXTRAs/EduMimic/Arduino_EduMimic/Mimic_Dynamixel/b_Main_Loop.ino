void loop() {

  delay(1);
  if (Serial.available())
  {
    checkSerial();
  }
  delay(1);

  // This sets the commanded position of each motor in the model, telling it to got to the position from ISS.
  dxl.setGoalPosition(DXL_ID_B1A, B1A, UNIT_DEGREE);
  dxl.setGoalPosition(DXL_ID_B3A, B3A, UNIT_DEGREE);
  dxl.setGoalPosition(DXL_ID_B1B, B1B, UNIT_DEGREE);
  dxl.setGoalPosition(DXL_ID_B3B, B3B, UNIT_DEGREE);
  dxl.setGoalPosition(DXL_ID_B2B, B2B, UNIT_DEGREE);
  dxl.setGoalPosition(DXL_ID_B4B, B4B, UNIT_DEGREE);
  dxl.setGoalPosition(DXL_ID_B2A, B2A, UNIT_DEGREE);
  dxl.setGoalPosition(DXL_ID_B4A, B4A, UNIT_DEGREE);
  dxl.setGoalPosition(DXL_ID_PSARJ, PSARJ, UNIT_DEGREE);
  dxl.setGoalPosition(DXL_ID_SSARJ, SSARJ, UNIT_DEGREE);


  // This retrieves the actual position of each motor in the model.  It should be very, very close to the above command unless a motor is jammed.
  B1A_PosAct = dxl.getPresentPosition(DXL_ID_B1A, UNIT_DEGREE);
  B3A_PosAct = dxl.getPresentPosition(DXL_ID_B3A, UNIT_DEGREE);
  B1B_PosAct = dxl.getPresentPosition(DXL_ID_B1B, UNIT_DEGREE);
  B3B_PosAct = dxl.getPresentPosition(DXL_ID_B3B, UNIT_DEGREE);
  B2B_PosAct = dxl.getPresentPosition(DXL_ID_B2B, UNIT_DEGREE);
  B4B_PosAct = dxl.getPresentPosition(DXL_ID_B4B, UNIT_DEGREE);
  B2A_PosAct = dxl.getPresentPosition(DXL_ID_B2A, UNIT_DEGREE);
  B4A_PosAct = dxl.getPresentPosition(DXL_ID_B4A, UNIT_DEGREE);
  PSARJ_PosAct = dxl.getPresentPosition(DXL_ID_PSARJ, UNIT_DEGREE);
  SSARJ_PosAct = dxl.getPresentPosition(DXL_ID_SSARJ, UNIT_DEGREE);



  // This retrieves the actual current of each motor in the model.  It be close to zero other than when the motor is moving. If not, motors is likely jammed.
  B1A_Cur = dxl.getPresentCurrent(DXL_ID_B1A, UNIT_MILLI_AMPERE);
  B3A_Cur = dxl.getPresentCurrent(DXL_ID_B3A, UNIT_MILLI_AMPERE);
  B1B_Cur = dxl.getPresentCurrent(DXL_ID_B1B, UNIT_MILLI_AMPERE);
  B3B_Cur = dxl.getPresentCurrent(DXL_ID_B3B, UNIT_MILLI_AMPERE);
  B2B_Cur = dxl.getPresentCurrent(DXL_ID_B2B, UNIT_MILLI_AMPERE);
  B4B_Cur = dxl.getPresentCurrent(DXL_ID_B4B, UNIT_MILLI_AMPERE);
  B2A_Cur = dxl.getPresentCurrent(DXL_ID_B2A, UNIT_MILLI_AMPERE);
  B4A_Cur = dxl.getPresentCurrent(DXL_ID_B4A, UNIT_MILLI_AMPERE);
  PSARJ_Cur = dxl.getPresentCurrent(DXL_ID_PSARJ, UNIT_MILLI_AMPERE);
  SSARJ_Cur = dxl.getPresentCurrent(DXL_ID_SSARJ, UNIT_MILLI_AMPERE);

  // Tells us if motor is enabled (so will receive current)
  B1A_TqStat = dxl.getTorqueEnableStat(DXL_ID_B1A);
  B3A_TqStat = dxl.getTorqueEnableStat(DXL_ID_B3A);
  B1B_TqStat = dxl.getTorqueEnableStat(DXL_ID_B1B);
  B3B_TqStat = dxl.getTorqueEnableStat(DXL_ID_B3B);
  B2B_TqStat = dxl.getTorqueEnableStat(DXL_ID_B2B);
  B4B_TqStat = dxl.getTorqueEnableStat(DXL_ID_B4B);
  B2A_TqStat = dxl.getTorqueEnableStat(DXL_ID_B2A);
  B4A_TqStat = dxl.getTorqueEnableStat(DXL_ID_B4A);
  PSARJ_TqStat = dxl.getTorqueEnableStat(DXL_ID_PSARJ);
  SSARJ_TqStat = dxl.getTorqueEnableStat(DXL_ID_SSARJ);


  // TRRJ commands are +/- 180 degrees (from ISS), so scaling differently than BGAs and SARJs, which are 0-360 deg.

  pulselen_PTRRJ = map(PTRRJ, 0, 360, SERVOMIN, SERVOMAX);
  pulselen_STRRJ = map(STRRJ, 0, 360,  SERVOMIN, SERVOMAX);


  //  pwm.setPWM(servonum_B1A, 0, pulselen_B1A);
  //  pwm.setPWM(servonum_B3A, 0, pulselen_B3A);
  //  pwm.setPWM(servonum_B1B, 0, pulselen_B1B);
  //  pwm.setPWM(servonum_B3B, 0, pulselen_B3B);
  //
  //  pwm.setPWM(servonum_B2B, 0, pulselen_B2B);
  //  pwm.setPWM(servonum_B4B, 0, pulselen_B4B);
  //  pwm.setPWM(servonum_B2A, 0, pulselen_B2A);
  //  pwm.setPWM(servonum_B4A, 0, pulselen_B4A);
  //
  //  pwm.setPWM(servonum_PSARJ, 0, pulselen_PSARJ);
  //  pwm.setPWM(servonum_SSARJ, 0, pulselen_SSARJ);
  pwm.setPWM(servonum_PTRRJ, 0, pulselen_PTRRJ);
  pwm.setPWM(servonum_STRRJ, 0, pulselen_STRRJ);




  //
  Serial.println(" ---------------------------------------------------");
  Serial.print("B1A   cmd | act | TqE | Cur: ");   Serial.print(B1A);   Serial.print(" | "); Serial.print( B1A_PosAct);  Serial.print(" | "); Serial.print( B1A_TqStat);  Serial.print(" | ");  Serial.println( B1A_Cur);
  Serial.print("B3A   cmd | act | TqE | Cur: ");   Serial.print(B3A);   Serial.print(" | "); Serial.print( B3A_PosAct);  Serial.print(" | "); Serial.print( B3A_TqStat);  Serial.print(" | ");  Serial.println( B3A_Cur);
  Serial.print("B1B   cmd | act | TqE | Cur: ");   Serial.print(B1B);   Serial.print(" | "); Serial.print( B1B_PosAct);  Serial.print(" | "); Serial.print( B1B_TqStat);  Serial.print(" | ");  Serial.println( B1B_Cur);
  Serial.print("B3B   cmd | act | TqE | Cur: ");   Serial.print(B3B);   Serial.print(" | "); Serial.print( B3B_PosAct);  Serial.print(" | "); Serial.print( B3B_TqStat);  Serial.print(" | ");  Serial.println( B3B_Cur);
  Serial.print("B2B   cmd | act | TqE | Cur: ");   Serial.print(B2B);   Serial.print(" | "); Serial.print( B2B_PosAct);  Serial.print(" | "); Serial.print( B2B_TqStat);  Serial.print(" | ");  Serial.println( B2B_Cur);
  Serial.print("B4B   cmd | act | TqE | Cur: ");   Serial.print(B4B);   Serial.print(" | "); Serial.print( B4B_PosAct);  Serial.print(" | "); Serial.print( B4B_TqStat);  Serial.print(" | ");  Serial.println( B4B_Cur);
  Serial.print("B2A   cmd | act | TqE | Cur: ");   Serial.print(B2A);   Serial.print(" | "); Serial.print( B2A_PosAct);  Serial.print(" | "); Serial.print( B2A_TqStat);  Serial.print(" | ");  Serial.println( B2A_Cur);
  Serial.print("B4A   cmd | act | TqE | Cur: ");   Serial.print(B4A);   Serial.print(" | "); Serial.print( B4A_PosAct);  Serial.print(" | "); Serial.print( B4A_TqStat);  Serial.print(" | ");  Serial.println( B4A_Cur);
  Serial.print("PSARJ cmd | act | TqE | Cur: ");   Serial.print(PSARJ); Serial.print(" | "); Serial.print( PSARJ_PosAct); Serial.print(" | "); Serial.print( PSARJ_TqStat); Serial.print(" | ");; Serial.println( PSARJ_Cur);
  Serial.print("SSARJ cmd | act | TqE | Cur: ");   Serial.print(SSARJ); Serial.print(" | "); Serial.print( SSARJ_PosAct); Serial.print(" | "); Serial.print( SSARJ_TqStat); Serial.print(" | ");; Serial.println( SSARJ_Cur);

  //  Serial.print("SSARJ: ");  Serial.print(SSARJ); Serial.print(" | "); Serial.println( pulselen_SSARJ);
  Serial.print("PTRRJ: ");  Serial.print(PTRRJ); Serial.print(" | "); Serial.println( pulselen_PTRRJ);
  Serial.print("STRRJ: ");  Serial.print(STRRJ); Serial.print(" | "); Serial.println( pulselen_STRRJ);


  //  pwm.setPWM(servonum, 0, pulselen);

  delay(10);

  //  // ============== Time measures ===================================================
  //  LoopStartMillis = millis();
  //  delta_t_millis = max(LoopStartMillis - previousMillis, 1); // ensure always equal to at least one, for later inversion
  //  inverse_delta_t_millis = 1 / ((float) delta_t_millis); // BCM mod 10/28/2018: for some reason, was not inverted (just = value, rather than 1/value).
  //  millisChPt1 = millis() - LoopStartMillis;
  //  // ================================================================================

}
