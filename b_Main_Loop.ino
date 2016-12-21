void loop() {


  // === DELETE THIS!  JUST FOR TESTING!!! =====
  //PSARJ=millis()*.0005;
  //PSARJ = 90 * sin(0.0005 * millis() * 0.001 * 180 / 3.14159);
  // === DELETE THIS!  JUST FOR TESTING!!! =====

  LoopStartMillis = millis();
  delta_t_millis = max(LoopStartMillis - previousMillis, 1); // ensure always equal to at least one, for later inversion
  inverse_delta_t_millis = (float) delta_t_millis;

  Pos = float(rightCount) / 2.5; // / 25; // 150:1 gear ratio, 6 encoder counts per motor shaft rotation 150/6=25;

  PosErr = PSARJ - Pos; // Compute Position Error
  dPosErr = PosErr - PosErr_old;

  dErr_dt = dPosErr * inverse_delta_t_millis * 0.001; // For Derivative

  Int_Now = Int_Old + PosErr * inverse_delta_t_millis * 0.001; // For Integrator
  Int_Old = Int_Now;
  millisChPt1 = millis() - LoopStartMillis;
  // Integrator reset when error sign changes
  if (PosErr_old * PosErr < 0) { // sign has changed
    Int_Now = 0;
    Int_Old = 0;
  }

  tmpSpeed = Kp * PosErr + Kd * (dErr_dt) + Ki * Int_Now;
  tmpSpeed2 = map(abs(tmpSpeed), 2, 250, 40, 250); // Deadband seems to be about 40 (for 5V input to motor board);
  CmdSpeed = max(min(abs(tmpSpeed2), 250), 10); // At least 10, at most 200
  millisChPt2 = millis() - LoopStartMillis;
  //  if (abs(PosErr) > 10) {
  //    CmdSpeed = 100;
  //  }

  if (tmpSpeed < 0) {
    myMotor->run(FORWARD);
    // motor.setSpeed(CmdSpeed);// + 20);
    myMotor->setSpeed(abs(CmdSpeed));// + 20);
    MyFlag = 1;
    // delay(2);
  }

  if (tmpSpeed > 0) {
    myMotor->run(BACKWARD);
    // motor.setSpeed(CmdSpeed);
    myMotor->setSpeed(abs(CmdSpeed));
    MyFlag = 2;
    //  delay(2);
  }

  delay(10);
  // motor.run(RELEASE);

  // delay(5);

  // targetCount = 1000 + 1 * 50 * millis() / 1000;
  // targetCount = PSARJ;

  //Serial.print("release");
  //motor.run(RELEASE);

  if (1) {
    response = ""; // empty it
    response += " | rghtCnt ";
    response += rightCount;
    response += " | Pos ";
    response += Pos;
    response += " | PSARJ:";
    response += PSARJ;
    response += " | PsErr:";
    response += PosErr;
    response += " | MyFlag";
    response += MyFlag;
    response += " |||CmdSpd:";
    response += CmdSpeed;
    response += " |||PSARJ:";
    response += PSARJ;
    millisChPt3 = millis() - LoopStartMillis;
    response += " |||delta_t_millis:";
    response += delta_t_millis;
    //    response+= " |||inv_delta_t_mlis:";
    //response+= inverse_delta_t_millis;
    response += "|millis";
    response += LoopStartMillis;
    response += " ||**|Int_Now:";

    response += "|C1:";
    response += millisChPt1;
    response += "|C2:";
    response += millisChPt2;
    response += "|C3:";
    response += millisChPt3;

    response += "|C4:";
    response += millisChPt4;
    response += "|C5:";
    response += millisChPt5;
    response += "|C6:";
    response += millisChPt6;
    response += "LED:";
    response += LEDstatus;
    millisChPt4 = millis() - LoopStartMillis;
    Serial.println(response);
    millisChPt5 = millis() - LoopStartMillis;
  }


  previousMillis = LoopStartMillis;
  PosErr_old = PosErr;
  millisChPt6 = millis() - LoopStartMillis;
//  if (LEDstatus = 0) {
//    digitalWrite(13, HIGH);
//    LEDstatus = 1;
//  } else {
//    digitalWrite(13, LOW);
//    LEDstatus = 0;
//  }


}
