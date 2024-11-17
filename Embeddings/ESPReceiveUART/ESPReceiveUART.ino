void setup() {
  // built-in serial port
  Serial.begin(115200);

  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);

  Serial.println("ESP8266 UART Receiver Initialized");
}

void loop() {
  if (Serial.available()) {
    // LED ON == DATA RECEPTION
    digitalWrite(LED_BUILTIN, HIGH);

    // read incoming data from Serial
    String incomingData = Serial.readStringUntil('\n');
    Serial.println("Received data from Python script:");
    Serial.println(incomingData);

    // parse data
    int delimiter1 = incomingData.indexOf('|');
    int delimiter2 = incomingData.indexOf('|', delimiter1 + 1);
    int delimiter3 = incomingData.indexOf('|', delimiter2 + 1);
    int delimiter4 = incomingData.indexOf('|', delimiter3 + 1);

    // extract info
    String songName = incomingData.substring(0, delimiter1);
    String artistName = incomingData.substring(delimiter1 + 1, delimiter2);
    String albumURL = incomingData.substring(delimiter2 + 1, delimiter3);
    String playbackStatus = incomingData.substring(delimiter3 + 1, delimiter4);
    String timestamp = incomingData.substring(delimiter4 + 1);

    // output data (debugging)
    Serial.println("Song Name: " + songName);
    Serial.println("Artist Name: " + artistName);
    Serial.println("Album URL: " + albumURL);
    Serial.println("Playback Status: " + playbackStatus);
    Serial.println("Timestamp: " + timestamp);

    delay(500);
    digitalWrite(LED_BUILTIN, LOW);
  }
}
