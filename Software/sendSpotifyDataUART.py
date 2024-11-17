import serial
import time

# serial port and baud rate configuration
SERIAL_PORT = 'COM3' 
BAUD_RATE = 115200

# serial communication
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
time.sleep(2)  

# Sample Spotify data
song_name = "Song Title"
artist_name = "Artist Name"
album_url = "http://example.com/image.jpg"
playback_status = "Playing"
timestamp = 123  # sec

# format data into single string
data_to_send = f"{song_name}|{artist_name}|{album_url}|{playback_status}|{timestamp}\n"

try:
    while True:
        # send formatted Spotify data over UART
        ser.write(data_to_send.encode('utf-8'))
        print("Sent data:", data_to_send)

        # CHECK IF ESP8266 OUTPUTS ANYTHING
        raw_data = ser.readline()
        try:
            incoming_data = raw_data.decode('utf-8', errors='ignore').strip()
            if incoming_data:
                print("Received from ESP8266:", incoming_data)
        except UnicodeDecodeError:
            print("Received undecodable data:", raw_data)

        time.sleep(1)
except KeyboardInterrupt:
    print("Stopped by user")
finally:
    ser.close()