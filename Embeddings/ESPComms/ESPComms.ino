#include <ESP8266WiFi.h>
#include <espnow.h>

// Bool to contain message send success.
bool success;
int counter = 0;
// Message contents. 
String contents = "Hello World! This is Jus!";

// Incoming String.
String incoming;

// Address of the node receiving the message. 
uint8_t recieverAddress[] = {0x8c, 0xce, 0x4e, 0xe2, 0xc9,0x62};

// Struct to contain the message. Struct should not be more than 250 bytes in total. 
struct struct_msg{
  String strmsg;
};

struct_msg incomingMsg;

// Callback funcion that prints success status.
void dataSent(uint8_t *mac_addr, uint8_t sendStatus) {
  Serial.print("Last Packet Send Status: ");
  if (sendStatus == 0){
    Serial.println("Delivery success");
    counter++;
    Serial.println(counter);
  }
  else { 
    Serial.println("Delivery fail");
  }
}

// Callback function that prings # of bytes recieved and stores the message in a local variable.
void dataRecieved(uint8_t * mac, uint8_t *incomingData, uint8_t len) {
  memcpy(&incomingMsg, incomingData, sizeof(incomingMsg));
  Serial.print("Bytes received: ");
  Serial.println(len);
  incoming = incomingMsg.strmsg;
}


void setup() {
  pinMode(LED_BUILTIN, OUTPUT);

  // Initializes the board to run with a baud rate of 115200.
  Serial.begin(115200);
  // Sets device as a wifi station. 
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  // Ensures initialization of ESP-NOW.
  if (esp_now_init() != 0) {
    Serial.println("Error initializing ESP-NOW");
    return;
  }
  
  esp_now_set_self_role(ESP_NOW_ROLE_COMBO);

  // Registers a callback function for when data is sent successfully. 
  esp_now_register_send_cb(dataSent);

  esp_now_add_peer(recieverAddress, ESP_NOW_ROLE_COMBO, 1, NULL, 0);

  // Registers a callback fucntion for when data is received successfully.
  esp_now_register_recv_cb(dataRecieved);
}

void loop() {
  // put your main code here, to run repeatedly:
  esp_now_send(recieverAddress, (uint8_t *) &contents, sizeof(contents));

  Serial.println("Incoming String");
  Serial.print(incoming);

  digitalWrite(LED_BUILTIN, HIGH);  // turn the LED on (HIGH is the voltage level)
  delay(50);                      
  digitalWrite(LED_BUILTIN, LOW);   // turn the LED off by making the voltage LOW
  delay(50); 

}
