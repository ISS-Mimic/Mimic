void loop() {


  bga_3B.PosCmd = B3B; // From RasPi telemetry stream
  bga_3A.PosCmd = B3A; // From RasPi telemetry stream
  bga_1B.PosCmd = B1B; // From RasPi telemetry stream
  bga_1A.PosCmd = B1A; // From RasPi telemetry stream

  if (NULLIFY == 1) {
    digitalWrite(13, LOW);
    delay(500);
    motorNULL(bga_3B);    myEnc3B.write(0); B3B=0;

    motorNULL(bga_3A);     myEnc3A.write(0);B3A=0;

    motorNULL(bga_1B);     myEnc1B.write(0); B1B=0;
    
    motorNULL(bga_1A);    myEnc1A.write(0); B1A=0;

    digitalWrite(13, HIGH);
    digitalWrite(6, LOW);
    delay(500);
    NULLIFY = 0;
    digitalWrite(6, HIGH);

  }

  // Can likely simplify this, but need to incorporate Adafruit motor shield library commands into my motor function/struct

  motorfnc(bga_3B); // this is where it's called
  if (bga_3B.tmpSpeed > 0) {
    myMotorB3B->run(FORWARD); // This command is necessary for the AdaFruit boards, requiring conditionals (rather than signed speeds taking care of direction).
  }
  else {
    myMotorB3B->run(BACKWARD);
  }
  myMotorB3B->setSpeed(bga_3B.CmdSpeed);// + 20);

  motorfnc(bga_1B); // this is where it's called
  if (bga_1B.tmpSpeed > 0) {
    myMotorB1B->run(FORWARD); // This command is necessary for the AdaFruit boards, requiring conditionals (rather than signed speeds taking care of direction).
  }
  else {
    myMotorB1B->run(BACKWARD);
  }
  myMotorB1B->setSpeed(bga_1B.CmdSpeed);// + 20);


  motorfnc(bga_3A); // this is where it's called
  if (bga_3A.tmpSpeed > 0) {
    myMotorB3A->run(FORWARD); // This command is necessary for the AdaFruit boards, requiring conditionals (rather than signed speeds taking care of direction).
  }
  else {
    myMotorB3A->run(BACKWARD);
  }
  myMotorB3A->setSpeed(bga_3A.CmdSpeed);// + 20);


  motorfnc(bga_1A); // this is where it's called
  if (bga_1A.tmpSpeed > 0) {
    myMotorB1A->run(FORWARD); // This command is necessary for the AdaFruit boards, requiring conditionals (rather than signed speeds taking care of direction).
  }
  else {
    myMotorB1A->run(BACKWARD);
  }
  myMotorB1A->setSpeed(bga_1A.CmdSpeed);// + 20);



  D0 = digitalRead(0);
  D1 = digitalRead(1);
  D2 = digitalRead(2);
  D3 = digitalRead(3);
  //  D4 = digitalRead(4);
  //  D5 = digitalRead(5);
  //  D6 = digitalRead(6);
  D7 = digitalRead(7);
  D8 = digitalRead(8);
  //  D9= digitalRead(9);
  //  D10= digitalRead(10);
  D11 = digitalRead(11);
  D12 = digitalRead(12);
  //D13 = digitalRead(13);
  ////D14 = digitalRead(14);
  D15 = digitalRead(15);
  D16 = digitalRead(16);
  D17 = digitalRead(17);



  delay(1);
  if (Serial.available())
  {
    checkSerial();
  }

  int  debug_mode = 8;
  //  B3A = 100 + 90.0* sin(2.0 * 3.14159 * 0.01 * millis() / 1000.0);
  //  B1A = 100 + 90.0* sin(2.0 * 3.14159 * 0.01 * millis() / 1000.0);
  //  B3B = 100 + 90.0* sin(2.0 * 3.14159 * 0.01 * millis() / 1000.0);
  //  B1B = 100 + 90.0* sin(2.0 * 3.14159 * 0.01 * millis() / 1000.0);
  //  PTRRJ=104*sin(1*3.14159*0.01*millis()/1000.0);


  // ========= Servo Stuff =============================
  //map(value, fromLow, fromHigh, toLow, toHigh)
  //  servo_PTRRJ.write(map(PTRRJ, -115, 115, 0, 180)); // from +/- 115deg to servo command min and max.
  //  servo_STRRJ.write(map(STRRJ, -115, 115, 0, 180)); // from +/- 115deg to servo command min and max.
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

  bga_3B.Count = myEnc3B.read();
  bga_1B.Count = myEnc1B.read();
  bga_3A.Count = myEnc3A.read();
  bga_1A.Count = myEnc1A.read();

  millisChPt2 = millis() - LoopStartMillis;

  //if (debug_mode==5){
  //Serial1.print("[Joint]:Cmd,Act,Err|  ");
  //Serial1.print("3A:c");
  //Serial1.print(B3A);
  //Serial1.print(",a");
  //Serial1.print(Pos_B3A);
  //Serial1.print(",e");
  //Serial1.print(PosErr_B3A);
  //
  //Serial1.print("|,  ");
  //Serial1.print("1A:c");
  //Serial1.print(B1A);
  //Serial1.print(",a");
  //Serial1.print(Pos_B1A);
  //Serial1.print(",e");
  //Serial1.print(PosErr_B1A);
  //
  //Serial1.print("|,  ");
  //Serial1.print("3B:c");
  //Serial1.print(B3B);
  //Serial1.print(",a");
  //Serial1.print(Pos_B3B);
  //Serial1.print(",e");
  //Serial1.print(PosErr_B3B);
  //
  //Serial1.print("|,  ");
  //Serial1.print("1B:c");
  //Serial1.print(B1B);
  //Serial1.print(",a");
  //Serial1.print(Pos_B1B);
  //Serial1.print(",e");
  //Serial1.print(PosErr_B1B);
  //Serial1.print("|,");
  //Serial1.println("");
  //}
  //
  //
  //
  //if (debug_mode==6){
  //Serial1.print(PosErr_B3A);
  //
  //Serial1.print(", ");
  //Serial1.print(PosErr_B1A);
  //
  //Serial1.print(", ");
  //Serial1.print(PosErr_B3B);
  //
  //Serial1.print(", ");
  //Serial1.print(PosErr_B1B);
  //Serial1.println("");
  //}

  if (debug_mode == 8) {
    Serial.print("|  ");

    Serial.print("Count_B3A: ");
    Serial.print(bga_3B.Count);
    Serial.print(",Count_B1A: ");
    Serial.print(bga_1A.Count);
    Serial.print("Count_B3B: ");
    Serial.print(bga_3B.Count);
    Serial.print(",Count_B1B: ");
    Serial.print(bga_1B.Count);
    Serial.print(",SmartRolloverBGA");
    Serial.print(SmartRolloverBGA);

    //    Serial.print(",Count_PSARJ: ");
    //    Serial.print(Count_PSARJ);
    //    Serial.print(",Count_SSARJ: ");
    //    Serial.print(Count_SSARJ);

    Serial.print(",D0:");
    Serial.print(D0);
    Serial.print(",D1:");
    Serial.print(D1);
    Serial.print(",D2:");
    Serial.print(D2);
    Serial.print(",D3:");
    Serial.print(D3);
    //    Serial.print(",D4:");
    //    Serial.print(D4);
    //    Serial.print(",D5: ");
    //    Serial.print(D5);
    //    Serial.print(",D6:");
    //    Serial.print(D6);
    Serial.print(",D7: ");
    Serial.print(D7);
    Serial.print(",D8:");
    Serial.print(D8);

    //    Serial.print(",D9: ");
    //    Serial.print(D9);
    //        Serial.print(",D10:");
    //        Serial.print(D10);

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
    Serial.print(",D16: ");
    Serial.print(D16);
    Serial.print(",D17: ");
    Serial.print(D17);

    Serial.print("| PosErrs ");
    Serial.print(bga_3B.PosErr);
    Serial.print(", ");
    Serial.print(bga_1A.PosErr);
    Serial.print(", ");
    Serial.print(bga_3B.PosErr);
    Serial.print(", ");
    Serial.print(bga_1B.PosErr);
    //    Serial.print(", ");
    //    Serial.print(PosErr_PSARJ);
    //    Serial.print(", ");
    //    Serial.print(PosErr_SSARJ);
    //
    //    Serial.print(", ");
    //    Serial.print("Integer Mtr Spd Cmd to Shield(PortSrj):");
    //    Serial.print(CmdSpeed_PSARJ);
    //Serial.print(PosErr_SSARJ);
    Serial.println("|  ");


    // LCD
    //
    //    //
    //      // LCD =======================================
    //      // text display tests
    //      display.setTextSize(1);
    //      display.setTextColor(WHITE);
    //      display.setCursor(0,0);
    //      display.setTextColor(BLACK, WHITE); // 'inverted' text
    //      display.println("Jnt|-ERR-|-CMD-|-ACT-");
    //
    //    //   display.println("3600.0|3600.0|3600.0");
    //    //     float d=12345.6789;
    //        //tostrf(floatVar, minStringWidthIncDecimalPoint, numVarsAfterDecimal, charBuf);
    //
    //
    //        //int sensorValue = analogRead(A0);
    //      //String stringThree = "I want " + sensorValue;
    //    //  String temp="3A:" + PosErr_B3A + "|" + Count_B1B;
    //    //
    //    //dtostrf(PosErr_B3A, 4, 1, dtostrfbuffer);
    //    //sendBuffer
    //    //  sprintf(sendBuffer, "X%dY%dT", first, second);
    //      //  display.print("3A:");
    //      //  dtostrf(PosErr_B3A, 4, 1, dtostrfbuffer);
    //
    //      //Goal is "3A:[PosErr]|[PosCmd]|[ActPos]
    //      display.setTextColor(WHITE, BLACK);
    //    display.print("3A:");
    //    dtostrf(PosErr_B3A, 5, 1, dtostrfbuffer);
    //    display.print( dtostrfbuffer);
    //    display.print("|");
    //    dtostrf(B3A, 5, 1, dtostrfbuffer); //Cmd Pos
    //    display.print( dtostrfbuffer);
    //    display.print("|");
    //    dtostrf(Pos_B3A, 5, 1, dtostrfbuffer);
    //    display.println( dtostrfbuffer);
    //
    //     display.setTextColor(BLACK, WHITE); // 'inverted' text
    //    display.print("1A:");
    //    dtostrf(PosErr_B1A, 5, 1, dtostrfbuffer);
    //    display.print( dtostrfbuffer);
    //    display.print("|");
    //    dtostrf(B1A, 5, 1, dtostrfbuffer); //Cmd Pos
    //    display.print( dtostrfbuffer);
    //    display.print("|");
    //    dtostrf(Pos_B1A, 5, 1, dtostrfbuffer);
    //    display.println( dtostrfbuffer);
    //
    //    display.setTextColor(WHITE, BLACK);
    //    display.print("3B:");
    //    dtostrf(PosErr_B3B, 5, 1, dtostrfbuffer);
    //    display.print( dtostrfbuffer);
    //    display.print("|");
    //    dtostrf(B3B, 5, 1, dtostrfbuffer); //Cmd Pos
    //    display.print( dtostrfbuffer);
    //    display.print("|");
    //    dtostrf(Pos_B3B, 5, 1, dtostrfbuffer);
    //    display.println( dtostrfbuffer);
    //
    //     display.setTextColor(BLACK, WHITE); // 'inverted' text
    //    display.print("1B:");
    //    dtostrf(PosErr_B1B, 5, 1, dtostrfbuffer);
    //    display.print( dtostrfbuffer);
    //    display.print("|");
    //    dtostrf(B1B, 5, 1, dtostrfbuffer); //Cmd Pos
    //    display.print( dtostrfbuffer);
    //    display.print("|");
    //    dtostrf(Pos_B1B, 5, 1, dtostrfbuffer);
    //    display.println( dtostrfbuffer);
    //
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
    ////
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
    ////
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
    //// end PID vals
    //    //float Kp_PSARJ = 10; // Proportional Gain of PID
    ////float Ki_PSARJ = 2; // Integral Gain of PID
    ////float Kd_PSARJ = 2; // Derivative Gain of PID
    //
    //
    ////    display.print(",PSMtrSpdU8bot:");
    ////    dtostrf(CmdSpeed_PSARJ, 5, 1, dtostrfbuffer);
    ////    display.println( dtostrfbuffer);
    //
    //
    //
    ////    display.setTextColor(WHITE, BLACK);
    ////    display.print("STJ:");
    ////    dtostrf(STRRJ, 6, 1, dtostrfbuffer);
    ////    display.print( dtostrfbuffer);
    ////
    ////
    ////    display.setTextColor(BLACK, WHITE); // 'inverted' text
    ////    display.print("|PTJ:");
    ////    dtostrf(PTRRJ, 6, 1, dtostrfbuffer);
    ////    display.println( dtostrfbuffer);
    //    //
    //    //
    //    ////
    //    ////   // display.print(",");
    //    ////
    //    ////     display.println("4. Hello, world!");
    //    ////      display.println("5. Hello, world!");
    //    ////       display.println("6. Hello, world!");
    //    ////        display.println("7. Hello, world!");
    //    ////              display.println("8. Hello, world!");
    //    ////       display.println("9. Hello, world!");
    //    ////        display.println("10. Hello, world!");
    //    //
    //    //
    //      display.display();
    //      //delay(10);
    //      display.clearDisplay();
    //    //
    //    //  // LCD =======================================
  }
  //
  //
  //
  //




  previousMillis = LoopStartMillis;

  millisChPt6 = millis() - LoopStartMillis;

  delay(3);
}
