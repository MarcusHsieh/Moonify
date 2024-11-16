void setup() {
  // serial port for UART communication
  Serial.begin(115200);

  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW); 

  Serial.println("ESP8266 UART Receiver Initialized!");
}

void loop() {
  if (Serial.available()) {
    // LED ON == DATA RECEPTION
    digitalWrite(LED_BUILTIN, HIGH);

    // read incoming data from Serial
    String incomingData = Serial.readStringUntil('\n');
    Serial.println("Received data from Python script:");
    Serial.println(incomingData);

    // should be blinking if constant data is received!
    delay(500); 
    digitalWrite(LED_BUILTIN, LOW);
  }
}
