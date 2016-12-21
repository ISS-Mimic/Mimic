// encoder event for the interrupt call

void rightEncoderEvent() {
  if (digitalRead(RH_ENCODER_A) == HIGH) {
    if (digitalRead(RH_ENCODER_B) == LOW) {
      rightCount++;
    } else {
      rightCount--;
    }
  } else {
    if (digitalRead(RH_ENCODER_B) == LOW) {
      rightCount--;
    } else {
      rightCount++;
    }
  }

  //  Serial.println(rightCount);
  //delay(1);
}


void receiveEvent(int howMany)
{
  String test = "";
  while (1 < Wire2.available()) // loop through all but the last
  {
    Serial.println("");
    Serial.println("Start:Received from Pi");
    char c = Wire2.read(); // receive byte as a character
    Serial.print("This is what c looks like:");
    Serial.println(c);
    test += c;
    Serial.print("Test contents:");
    Serial.println(test);
    
  }
    Serial.println("received from pi");
  Serial.println(test);
  String test2=test.substring(1);
  PSARJ = test2.toFloat();
  Serial.println(PSARJ);

  int x = Wire2.read();    // receive byte as an integer
  //Serial.println(x);         // print the integer
  //Serial.println();
  Serial.println("Inside the Wire Read loop");
  Serial.flush();
}
