void loop() {


  D0 = digitalRead(0);
  D1 = digitalRead(1);
  //  D2 = digitalRead(2);
  //D3 = digitalRead(3);
  D4 = digitalRead(4);
  D5 = digitalRead(5);
  //  D6 = digitalRead(6);
  //  D7 = digitalRead(7);
  //  D8 = digitalRead(8);
  //D9= digitalRead(9);
  //D10= digitalRead(10);
  D11 = digitalRead(11);
  D12 = digitalRead(12);
  //D13 = digitalRead(13);
  D14 = digitalRead(14);
  D15 = digitalRead(15);
  //  D16 = digitalRead(16);
  //  D17 = digitalRead(17);



  delay(1);
  if (Serial.available())
  {
    checkSerial();
  }

  int  debug_mode = 8;
  //  B1A = 100 + 90.0* sin(2.0 * 3.14159 * 0.01 * millis() / 1000.0);
  //  B3A = 100 + 90.0* sin(2.0 * 3.14159 * 0.01 * millis() / 1000.0);
  //  B1B = 100 + 90.0* sin(2.0 * 3.14159 * 0.01 * millis() / 1000.0);
  //  B3B = 100 + 90.0* sin(2.0 * 3.14159 * 0.01 * millis() / 1000.0);
  //  PTRRJ=104*sin(1*3.14159*0.01*millis()/1000.0);


  // ========= Servo Stuff =============================
  //map(value, fromLow, fromHigh, toLow, toHigh)
  servo_PTRRJ.write(map(PTRRJ, -115, 115, 0, 180)); // from +/- 115deg to servo command min and max.
  servo_STRRJ.write(map(STRRJ, -115, 115, 0, 180)); // from +/- 115deg to servo command min and max.
  //servo_PTRRJ.write(PTRRJ+180);
  //servo_STRRJ.write(PTRRJ+180);

  delay(1);
  //delay(10);
  //  for (i = 255; i != 0; i--) {
  //    servo_PTRRJ.write(map(i, 0, 255, 0, 180));
  //    delay(1);
  //  }
  //delay(10);
  // ==================================================

  // ============== Time measures ===================================================
  LoopStartMillis = millis();
  delta_t_millis = max(LoopStartMillis - previousMillis, 1); // ensure always equal to at least one, for later inversion
  inverse_delta_t_millis = 1 / ((float) delta_t_millis); // BCM mod 10/28/2018: for some reason, was not inverted (just = value, rather than 1/value).
  millisChPt1 = millis() - LoopStartMillis;
  // ================================================================================

  Count_B1B = myEnc1B.read(); // Feb08
  Count_B3B = myEnc3B.read();
  Count_B1A = myEnc1A.read();
  Count_B3A = myEnc3A.read();
  //  Count_PSARJ = myEncPSARJ.read();
  //  Count_SSARJ = myEncSSARJ.read();
  //   Serial.println(currentPosition); //shows you the current position in the serial monitor  // Feb08

  // ============== BGA 2A ==========================================================

  // 150 motor shaft rotations / gearbox output shaft rotation * 12 encoder counts / motor rotation  /(360 deg per /output rotation) = 150*12/360 = 5 encoder counts per output shaft degree
  Pos_B1A = float(Count_B1A) / 5;

  PosErr_B1A = B1A - Pos_B1A; // Compute Pos_B1Aition Error
  dPosErr_B1A = PosErr_B1A - PosErr_old_B1A;

  if (abs(PosErr_B1A) < 0.1) {
    PosErr_B1A = 0;
    dPosErr_B1A = 0;
    PosErr_old_B1A = 0;
    IntOld_B1A = 0;
    //Serial.println("Small2A Err");
  }

  dErrDt_B1A = dPosErr_B1A * inverse_delta_t_millis * 0.001; // For Derivative
  //IntNow_B1A = IntOld_B1A + PosErr_B1A * inverse_delta_t_millis * 0.001; // For Integrator
  IntNow_B1A = IntOld_B1A + PosErr_B1A * delta_t_millis * 0.001; // BCM mod 10/28/2018 - shoudln't be be using inverse time, but may have been why that val was not inverted above (from prior debugging?)
  IntOld_B1A = IntNow_B1A;

  // Integrator reset when error sign changes
  if (PosErr_old_B1A * PosErr_B1A <= 0) { // sign on error has changed or is zero
    IntNow_B1A = 0;
    IntOld_B1A = 0;
  }
  PosErr_old_B1A = PosErr_B1A; // For use on the next iteration

  // Calculate motor speed setpoint based on PID constants and computed params for this iteration.
  tmpSpeed_B1A = Kp_B1A * PosErr_B1A + Kd_B1A * (dErrDt_B1A) + Ki_B1A * IntNow_B1A;
  // Deadband seems to be about 40 (for 5V input to motor board);
  CmdSpeed_B1A = abs(tmpSpeed_B1A);
  if ((CmdSpeed_B1A < 40) && (CmdSpeed_B1A > 5)) { // We want a dead space at 5 counts, but want it to move for larger vals.
    CmdSpeed_B1A = 40;
  }

  CmdSpeed_B1A = max(min(CmdSpeed_B1A, 250), 0); // At least 10, at most 250.  Update as needed per motor.

  // Set motor speed
  if (tmpSpeed_B1A > 0) {
    myMotorB1A->run(FORWARD); // This command is necessary for the AdaFruit boards, requiring conditionals (rather than signed speeds taking care of direction).
  }
  else {
    myMotorB1A->run(BACKWARD);
  }
  myMotorB1A->setSpeed(CmdSpeed_B1A);// + 20);
  //=====================================================================================

  // ============== BGA 2B ==========================================================

  // 150 motor shaft rotations / gearbox output shaft rotation * 12 encoder counts / motor rotation  /(360 deg per /output rotation) = 150*12/360 = 5 encoder counts per output shaft degree
  Pos_B1B = float(Count_B1B) / 5;

  PosErr_B1B = B1B - Pos_B1B; // Compute Pos_B1Bition Error
  dPosErr_B1B = PosErr_B1B - PosErr_old_B1B;

  if (abs(PosErr_B1B) < 0.1) {
    PosErr_B1B = 0;
    dPosErr_B1B = 0;
    PosErr_old_B1B = 0;
    IntOld_B1B = 0;
    //Serial.println("Small2B Err");
  }

  dErrDt_B1B = dPosErr_B1B * inverse_delta_t_millis * 0.001; // For Derivative
  IntNow_B1B = IntOld_B1B + PosErr_B1B *  delta_t_millis * 0.001; // BCM mod 10/28/2018 - shoudln't be be using inverse time, but may have been why that val was not inverted above (from prior debugging?)
  IntOld_B1B = IntNow_B1B;

  // Integrator reset when error sign changes
  if (PosErr_old_B1B * PosErr_B1B <= 0) { // sign on error has changed or is zero
    IntNow_B1B = 0;
    IntOld_B1B = 0;
  }
  PosErr_old_B1B = PosErr_B1B; // For use on the next iteration

  // Calculate motor speed setpoint based on PID constants and computed params for this iteration.
  tmpSpeed_B1B = Kp_B1B * PosErr_B1B + Kd_B1B * (dErrDt_B1B) + Ki_B1B * IntNow_B1B;
  // Deadband seems to be about 40 (for 5V input to motor board);
  CmdSpeed_B1B = abs(tmpSpeed_B1B);
  if ((CmdSpeed_B1B < 40) && (CmdSpeed_B1B > 5)) { // We want a dead space at 5 counts, but want it to move for larger vals.
    CmdSpeed_B1B = 40;
  }

  CmdSpeed_B1B = max(min(CmdSpeed_B1B, 250), 0); // At least 10, at most 250.  Update as needed per motor.

  // Set motor speed
  if (tmpSpeed_B1B > 0) {
    myMotorB1B->run(FORWARD); // This command is necessary for the AdaFruit boards, requiring conditionals (rather than signed speeds taking care of direction).
  }
  else {
    myMotorB1B->run(BACKWARD);
  }
  myMotorB1B->setSpeed(CmdSpeed_B1B);// + 20);6+9
  //=====================================================================================

  // ============== BGA 4A ==========================================================

  // 150 motor shaft rotations / gearbox output shaft rotation * 12 encoder counts / motor rotation  /(360 deg per /output rotation) = 150*12/360 = 5 encoder counts per output shaft degree
  Pos_B3A = float(Count_B3A) / 5;

  PosErr_B3A = B3A - Pos_B3A; // Compute Pos_B3Aition Error
  dPosErr_B3A = PosErr_B3A - PosErr_old_B3A;

  if (abs(PosErr_B3A) < 0.1) {
    PosErr_B3A = 0;
    dPosErr_B3A = 0;
    PosErr_old_B3A = 0;
    IntOld_B3A = 0;
    //Serial.println("Small4A Err");
  }

  dErrDt_B3A = dPosErr_B3A * inverse_delta_t_millis * 0.001; // For Derivative
  IntNow_B3A = IntOld_B3A + PosErr_B3A *  delta_t_millis * 0.001; // BCM mod 10/28/2018 - shoudln't be be using inverse time, but may have been why that val was not inverted above (from prior debugging?)
  IntOld_B3A = IntNow_B3A;

  // Integrator reset when error sign changes
  if (PosErr_old_B3A * PosErr_B3A <= 0) { // sign on error has changed or is zero
    IntNow_B3A = 0;
    IntOld_B3A = 0;
  }
  PosErr_old_B3A = PosErr_B3A; // For use on the next iteration

  // Calculate motor speed setpoint based on PID constants and computed params for this iteration.
  tmpSpeed_B3A = Kp_B3A * PosErr_B3A + Kd_B3A * (dErrDt_B3A) + Ki_B3A * IntNow_B3A;
  // Deadband seems to be about 40 (for 5V input to motor board);
  CmdSpeed_B3A = abs(tmpSpeed_B3A);
  if ((CmdSpeed_B3A < 40) && (CmdSpeed_B3A > 5)) { // We want a dead space at 5 counts, but want it to move for larger vals.
    CmdSpeed_B3A = 40;
  }

  CmdSpeed_B3A = max(min(CmdSpeed_B3A, 250), 0); // At least 10, at most 250.  Update as needed per motor.

  // Set motor speed
  if (tmpSpeed_B3A > 0) {
    myMotorB3A->run(FORWARD); // This command is necessary for the AdaFruit boards, requiring conditionals (rather than signed speeds taking care of direction).
  }
  else {
    myMotorB3A->run(BACKWARD);
  }
  myMotorB3A->setSpeed(CmdSpeed_B3A);// + 20);
  //=====================================================================================


  //  // ============== BGA 4B ==========================================================

  // 150 motor shaft rotations / gearbox output shaft rotation * 12 encoder counts / motor rotation  /(360 deg per /output rotation) = 150*12/360 = 5 encoder counts per output shaft degree
  Pos_B3B = float(Count_B3B) / 5;

  PosErr_B3B = B3B - Pos_B3B; // Compute Pos_B3Bition Error
  dPosErr_B3B = PosErr_B3B - PosErr_old_B3B;

  if (abs(PosErr_B3B) < 0.1) {
    PosErr_B3B = 0;
    dPosErr_B3B = 0;
    PosErr_old_B3B = 0;
    IntOld_B3B = 0;
    //Serial.println("Small4B Err");
  }

  dErrDt_B3B = dPosErr_B3B * inverse_delta_t_millis * 0.001; // For Derivative
  IntNow_B3B = IntOld_B3B + PosErr_B3B * delta_t_millis * 0.001; // BCM mod 10/28/2018 - shoudln't be be using inverse time, but may have been why that val was not inverted above (from prior debugging?)
  IntOld_B3B = IntNow_B3B;

  // Integrator reset when error sign changes
  if (PosErr_old_B3B * PosErr_B3B <= 0) { // sign on error has changed or is zero
    IntNow_B3B = 0;
    IntOld_B3B = 0;
  }
  PosErr_old_B3B = PosErr_B3B; // For use on the next iteration

  // Calculate motor speed setpoint based on PID constants and computed params for this iteration.
  tmpSpeed_B3B = Kp_B3B * PosErr_B3B + Kd_B3B * (dErrDt_B3B) + Ki_B3B * IntNow_B3B;
  // Deadband seems to be about 40 (for 5V input to motor board);
  CmdSpeed_B3B = abs(tmpSpeed_B3B);
  if ((CmdSpeed_B3B < 40) && (CmdSpeed_B3B > 5)) { // We want a dead space at 5 counts, but want it to move for larger vals.
    CmdSpeed_B3B = 40;
  }

  CmdSpeed_B3B = max(min(CmdSpeed_B3B, 250), 0); // At least 0, at most 250.  Update as needed per motor.

  // Set motor speed
  if (tmpSpeed_B3B > 0) {
    myMotorB3B->run(FORWARD); // This command is necessary for the AdaFruit boards, requiring conditionals (rather than signed speeds taking care of direction).
  }
  else {
    myMotorB3B->run(BACKWARD);
  }
  myMotorB3B->setSpeed(CmdSpeed_B3B);// + 20);
  //=====================================================================================

  //  //  // ============== PSARJ    ============================================================
  //  Pos_PSARJ = float(Count_PSARJ) / (5*40/12); // / 25; // 150:1 gear ratio, 6 encoder counts per motor shaft rotation 150/6=25;  42 teeth on bull gear. T12 pinion
  //
  //  PosErr_PSARJ = PSARJ - Pos_PSARJ; // Compute Pos_PSARJition Error
  //
  //  // Kill error if error within tolerance
  //if (abs(PosErr_PSARJ)<0.5) {
  //  PosErr_PSARJ=0;
  //  IntOld_PSARJ=0;
  //  PosErr_old_PSARJ=0;
  //}
  //  dPosErr_PSARJ = PosErr_PSARJ - PosErr_old_PSARJ;
  //  dErrDt_PSARJ = dPosErr_PSARJ * inverse_delta_t_millis * 0.001; // For Derivative
  //  // IntNow_PSARJ = IntOld_PSARJ + PosErr_PSARJ * inverse_delta_t_millis * 0.001; // For Integrator
  //  IntNow_PSARJ = IntOld_PSARJ + PosErr_PSARJ * delta_t_millis * 0.001; // For Integrator; BCM mod 10/28/2018
  //
  //int sign=0;
  //
  //
  //
  //if (abs(PosErr_PSARJ) == PosErr_PSARJ){
  //  sign = 1;
  //  }
  //else{
  //  sign = -1;
  //}
  //
  //IntNow_PSARJ = min(abs(IntNow_PSARJ),70)*sign;
  //
  //  IntOld_PSARJ = IntNow_PSARJ;
  //  PosErr_old_PSARJ = PosErr_PSARJ; // For use on the next iteration
  //  // Integrator reset when error sign changes
  //  if (PosErr_old_PSARJ * PosErr_PSARJ < 0) { // sign on error has changed
  //    IntNow_PSARJ = 0;
  //    IntOld_PSARJ = 0;
  //  }
  //
  //  // Calculate motor speed setpoint based on PID constants and computed params for this iteration.
  //
  ////int sign=0;
  //if (abs(PosErr_PSARJ) == PosErr_PSARJ){
  //  sign = 1;
  //  }
  //else{
  //  sign = -1;
  //}
  //
  // int tmp_KP=sign * min(abs(PosErr_PSARJ),100);
  //
  //  tmpSpeed_PSARJ = Kp_PSARJ * tmp_KP + Kd_PSARJ * (dErrDt_PSARJ) + Ki_PSARJ * IntNow_PSARJ;
  //
  //  CmdSpeed_PSARJ=min(abs(tmpSpeed_PSARJ),255); // BCM added 10/28/2018 to limit value to 255, since expecting 8-bit integer (uint8_t).  May want to later update data type.
  //  //CmdSpeed_PSARJ = map(abs(tmpSpeed_PSARJ), 2, 250, 2, 250); // Deadband seems to be about 40 (for 5V input to motor board);
  // // CmdSpeed_PSARJ = max(min(CmdSpeed_PSARJ, 150), 0); // At least 10, at most 250.  Update as needed per motor.
  //
  //  // Set motor speed
  //  if (tmpSpeed_PSARJ < 0) {
  //    myMotorPSARJ->run(FORWARD); // This command is necessary for the AdaFruit boards, requiring conditionals (rather than signed speeds taking care of direction).
  //  }
  //  else {
  //    myMotorPSARJ->run(BACKWARD);
  //  }
  //  myMotorPSARJ->setSpeed(CmdSpeed_PSARJ);// + 20);
  //  //  //====================================================================================



  //
  //   //  // ============== SSARJ    ============================================================
  //    Pos_SSARJ = float(Count_SSARJ) / 2.5; // / 25; // 150:1 gear ratio, 6 encoder counts per motor shaft rotation 150/6=25;
  //
  //    PosErr_SSARJ = SSARJ - Pos_SSARJ; // Compute Pos_SSARJition Error
  //    dPosErr_SSARJ = PosErr_SSARJ - PosErr_old_SSARJ;
  //    dErrDt_SSARJ = dPosErr_SSARJ * inverse_delta_t_millis * 0.001; // For Derivative
  //    IntNow_SSARJ = IntOld_SSARJ + PosErr_SSARJ *  delta_t_millis * 0.001; // BCM mod 10/28/2018 - shoudln't be be using inverse time, but may have been why that val was not inverted above (from prior debugging?)
  //    IntOld_SSARJ = IntNow_SSARJ;
  //    PosErr_old_SSARJ = PosErr_SSARJ; // For use on the next iteration
  //    // Integrator reset when error sign changes
  //    if (PosErr_old_SSARJ * PosErr_SSARJ < 0) { // sign on error has changed
  //      IntNow_SSARJ = 0;
  //      IntOld_SSARJ = 0;
  //    }
  //
  //    // Calculate motor speed setpoint based on PID constants and computed params for this iteration.
  //    tmpSpeed_SSARJ = Kp_SSARJ * PosErr_SSARJ + Kd_SSARJ * (dErrDt_SSARJ) + Ki_SSARJ * IntNow_SSARJ;
  //    CmdSpeed_SSARJ = map(abs(tmpSpeed_SSARJ), 2, 250, 2, 250); // Deadband seems to be about 40 (for 5V input to motor board);
  //    CmdSpeed_SSARJ = max(min(CmdSpeed_SSARJ, 150), 0); // At least 10, at most 250.  Update as needed per motor.
  //
  //    // Set motor speed
  //    if (tmpSpeed_SSARJ < 0) {
  //      myMotorSSARJ->run(FORWARD); // This command is necessary for the AdaFruit boards, requiring conditionals (rather than signed speeds taking care of direction).
  //    }
  //    else {
  //      myMotorSSARJ->run(BACKWARD);
  //    }
  //    myMotorSSARJ->setSpeed(CmdSpeed_SSARJ);// + 20);
  //  //  //====================================================================================

  millisChPt2 = millis() - LoopStartMillis;

  //if (debug_mode==5){
  //Serial1.print("[Joint]:Cmd,Act,Err|  ");
  //Serial1.print("2A:c");
  //Serial1.print(B1A);
  //Serial1.print(",a");
  //Serial1.print(Pos_B1A);
  //Serial1.print(",e");
  //Serial1.print(PosErr_B1A);
  //
  //Serial1.print("|,  ");
  //Serial1.print("4A:c");
  //Serial1.print(B3A);
  //Serial1.print(",a");
  //Serial1.print(Pos_B3A);
  //Serial1.print(",e");
  //Serial1.print(PosErr_B3A);
  //
  //Serial1.print("|,  ");
  //Serial1.print("2B:c");
  //Serial1.print(B1B);
  //Serial1.print(",a");
  //Serial1.print(Pos_B1B);
  //Serial1.print(",e");
  //Serial1.print(PosErr_B1B);
  //
  //Serial1.print("|,  ");
  //Serial1.print("4B:c");
  //Serial1.print(B3B);
  //Serial1.print(",a");
  //Serial1.print(Pos_B3B);
  //Serial1.print(",e");
  //Serial1.print(PosErr_B3B);
  //Serial1.print("|,");
  //Serial1.println("");
  //}
  //
  //
  //
  //if (debug_mode==6){
  //Serial1.print(PosErr_B1A);
  //
  //Serial1.print(", ");
  //Serial1.print(PosErr_B3A);
  //
  //Serial1.print(", ");
  //Serial1.print(PosErr_B1B);
  //
  //Serial1.print(", ");
  //Serial1.print(PosErr_B3B);
  //Serial1.println("");
  //}

  if (debug_mode == 8) {
    Serial.print("|  ");

    Serial.print("Count_B1A: ");
    Serial.print(Count_B1A);
    Serial.print(",Count_B3A: ");
    Serial.print(Count_B3A);
    Serial.print("Count_B1B: ");
    Serial.print(Count_B1B);
    Serial.print(",Count_B3B: ");
    Serial.print(Count_B3B);
    //    Serial.print(",Count_PSARJ: ");
    //    Serial.print(Count_PSARJ);
    Serial.print(",D0:");
    Serial.print(D0);
    Serial.print(",D1:");
    Serial.print(D1);
    //    Serial.print(",D2:");
    //    Serial.print(D2);
    //    Serial.print(",D3:");
    //    Serial.print(D3);
    Serial.print(",D4:");
    Serial.print(D4);
    Serial.print(",D5: ");
    Serial.print(D5);
    //    Serial.print(",D6:");
    //    Serial.print(D6);
    //    Serial.print(",D7: ");
    //    Serial.print(D7);
    //    Serial.print(",D8:");
    //    Serial.print(D8);
    Serial.print(",D11: ");
    Serial.print(D11);
    Serial.print(",D12: ");
    Serial.print(D12);
    //    Serial.print(",D13: ");
    //  Serial.print(D13);
    Serial.print(",D14: ");
    Serial.print(D14);
    Serial.print(",D15: ");
    Serial.print(D15);
    //    Serial.print(",D16: ");
    //    Serial.print(D16);
    //    Serial.print(",D17: ");
    //    Serial.print(D17);

    //    Serial.print("  Count_SSARJ: ");
    //    Serial.print(Count_SSARJ);
    Serial.print("| PosErrs ");
    Serial.print(PosErr_B1A);
    Serial.print(", ");
    Serial.print(PosErr_B3A);
    Serial.print(", ");
    Serial.print(PosErr_B1B);
    Serial.print(", ");
    Serial.print(PosErr_B3B);
    //    Serial.print(", ");
    //    Serial.print(PosErr_PSARJ);
    //
    //    Serial.print(", ");
    //    Serial.print("Integer Mtr Spd Cmd to Shield(PortSrj):");
    //    Serial.print(CmdSpeed_PSARJ);
    //Serial.print(PosErr_SSARJ);
    Serial.println("|  ");

    //
    // LCD =======================================
    // text display tests
    display.setTextSize(1);
    display.setTextColor(WHITE);
    display.setCursor(0, 0);
    display.setTextColor(BLACK, WHITE); // 'inverted' text
    display.println("Jnt|-ERR-|-CMD-|-ACT-");

    //   display.println("3600.0|3600.0|3600.0");
    //     float d=12345.6789;
    //tostrf(floatVar, minStringWidthIncDecimalPoint, numVarsAfterDecimal, charBuf);


    //int sensorValue = analogRead(A0);
    //String stringThree = "I want " + sensorValue;
    //  String temp="1A:" + PosErr_B1A + "|" + Count_B3B;
    //
    //dtostrf(PosErr_B1A, 4, 1, dtostrfbuffer);
    //sendBuffer
    //  sprintf(sendBuffer, "X%dY%dT", first, second);
    //  display.print("1A:");
    //  dtostrf(PosErr_B1A, 4, 1, dtostrfbuffer);

    //Goal is "1A:[PosErr]|[PosCmd]|[ActPos]
    display.setTextColor(WHITE, BLACK);
    display.print("1A:");
    dtostrf(PosErr_B1A, 5, 1, dtostrfbuffer);
    display.print( dtostrfbuffer);
    display.print("|");
    dtostrf(B1A, 5, 1, dtostrfbuffer); //Cmd Pos
    display.print( dtostrfbuffer);
    display.print("|");
    dtostrf(Pos_B1A, 5, 1, dtostrfbuffer);
    display.println( dtostrfbuffer);

    display.setTextColor(BLACK, WHITE); // 'inverted' text
    display.print("3A:");
    dtostrf(PosErr_B3A, 5, 1, dtostrfbuffer);
    display.print( dtostrfbuffer);
    display.print("|");
    dtostrf(B3A, 5, 1, dtostrfbuffer); //Cmd Pos
    display.print( dtostrfbuffer);
    display.print("|");
    dtostrf(Pos_B3A, 5, 1, dtostrfbuffer);
    display.println( dtostrfbuffer);

    display.setTextColor(WHITE, BLACK);
    display.print("1B:");
    dtostrf(PosErr_B1B, 5, 1, dtostrfbuffer);
    display.print( dtostrfbuffer);
    display.print("|");
    dtostrf(B1B, 5, 1, dtostrfbuffer); //Cmd Pos
    display.print( dtostrfbuffer);
    display.print("|");
    dtostrf(Pos_B1B, 5, 1, dtostrfbuffer);
    display.println( dtostrfbuffer);

    display.setTextColor(BLACK, WHITE); // 'inverted' text
    display.print("3B:");
    dtostrf(PosErr_B3B, 5, 1, dtostrfbuffer);
    display.print( dtostrfbuffer);
    display.print("|");
    dtostrf(B3B, 5, 1, dtostrfbuffer); //Cmd Pos
    display.print( dtostrfbuffer);
    display.print("|");
    dtostrf(Pos_B3B, 5, 1, dtostrfbuffer);
    display.println( dtostrfbuffer);

    //    display.setTextColor(WHITE, BLACK);
    //    display.print("SS:");
    //    dtostrf(PosErr_SSARJ, 5, 1, dtostrfbuffer);
    //    display.print( dtostrfbuffer);
    //    display.print("|");
    //    dtostrf(SSARJ, 5, 1, dtostrfbuffer); //Cmd Pos
    //    display.print( dtostrfbuffer);
    //    display.print("|");
    //    dtostrf(Pos_SSARJ, 5, 1, dtostrfbuffer);
    //    display.println( dtostrfbuffer);

    //
    //    display.setTextColor(BLACK, WHITE); // 'inverted' text
    //    display.print("PS:");
    //    dtostrf(PosErr_PSARJ, 5, 1, dtostrfbuffer);
    //    display.print( dtostrfbuffer);
    //    display.print("|");
    //    dtostrf(PSARJ, 5, 1, dtostrfbuffer); //Cmd Pos
    //    display.print( dtostrfbuffer);
    //    display.print("|");
    //    dtostrf(Pos_PSARJ, 5, 1, dtostrfbuffer);
    //    display.println( dtostrfbuffer);
    //
    //// PID vals
    //    display.print("Kpid:");
    //    dtostrf(Kp_PSARJ, 3, 0, dtostrfbuffer);
    //    display.print( dtostrfbuffer);
    //    display.print(",");
    //    dtostrf(Ki_PSARJ, 3, 0, dtostrfbuffer);
    //    display.print( dtostrfbuffer);
    //    display.print(",");
    //   dtostrf(Kd_PSARJ, 3, 0, dtostrfbuffer);
    //    display.print( dtostrfbuffer);
    //    display.print(",Mtr:");
    //    dtostrf(CmdSpeed_PSARJ, 3, 0, dtostrfbuffer);
    //    display.println( dtostrfbuffer);
    // end PID vals
    //float Kp_PSARJ = 10; // Proportional Gain of PID
    //float Ki_PSARJ = 2; // Integral Gain of PID
    //float Kd_PSARJ = 2; // Derivative Gain of PID


    //    display.print(",PSMtrSpdU8bot:");
    //    dtostrf(CmdSpeed_PSARJ, 5, 1, dtostrfbuffer);
    //    display.println( dtostrfbuffer);



    display.setTextColor(WHITE, BLACK);
    display.print("STJ:");
    dtostrf(STRRJ, 6, 1, dtostrfbuffer);
    display.print( dtostrfbuffer);


    display.setTextColor(BLACK, WHITE); // 'inverted' text
    display.print("|PTJ:");
    dtostrf(PTRRJ, 6, 1, dtostrfbuffer);
    display.println( dtostrfbuffer);
    //
    //
    ////
    ////   // display.print(",");
    ////
    ////     display.println("4. Hello, world!");
    ////      display.println("5. Hello, world!");
    ////       display.println("6. Hello, world!");
    ////        display.println("7. Hello, world!");
    ////              display.println("8. Hello, world!");
    ////       display.println("9. Hello, world!");
    ////        display.println("10. Hello, world!");
    //
    //
    display.display();
    //delay(10);
    display.clearDisplay();
    //
    //  // LCD =======================================
  }








  previousMillis = LoopStartMillis;

  millisChPt6 = millis() - LoopStartMillis;

  delay(3);
}
