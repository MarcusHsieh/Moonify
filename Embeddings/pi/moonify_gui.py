import serial
import time
from tkinter import Tk, Label

SERIAL_PORT = '/dev/serial0' 
BAUD_RATE = 115200

ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
time.sleep(2)


root = Tk()
root.title("ESP8266 LED Blink Indicator")
root.geometry("300x200")
root.configure(bg="black")

status_label = Label(root, text="LED Status: OFF", font=("Helvetica", 24), fg="red", bg="black")
status_label.pack(pady=50)

def update_indicator():
    if ser.in_waiting > 0:
        try:
            incoming_data = ser.readline().decode('utf-8', errors='ignore').strip()
            print("Received:", incoming_data) 

            if "Delivery success" in incoming_data:
                status_label.config(text="LED Status: ON", fg="green")
                root.after(100, lambda: status_label.config(text="LED Status: OFF", fg="red"))  
            elif "Bytes received" in incoming_data:
                status_label.config(text="LED Status: ON", fg="green")
                root.after(100, lambda: status_label.config(text="LED Status: OFF", fg="red"))  
        except Exception as e:
            print("Error:", e)

    root.after(100, update_indicator)

update_indicator()

root.mainloop()
