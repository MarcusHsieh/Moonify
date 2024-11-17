import serial
import time
from tkinter import Tk, Label, Frame, PhotoImage

SERIAL_PORT = '/dev/ttyS0' 
BAUD_RATE = 115200

ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
time.sleep(2) 

root = Tk()
root.title("Moonify Data Display")
root.geometry("800x480") 
root.configure(bg="black") 

try:
    bg_image = PhotoImage(file="space.png") 
    background_label = Label(root, image=bg_image)
    background_label.place(relwidth=1, relheight=1)
except:
    root.configure(bg="black")  

bright_moon_image = PhotoImage(file="fullMoon.png")
dark_moon_image = PhotoImage(file="moon.png")

frame = Frame(root, bg="#1e1e2f", bd=5)
frame.place(relx=0.5, rely=0.1, relwidth=0.9, relheight=0.8, anchor='n')

text_color = "lightblue"

song_name_label = Label(frame, text="Song Name: ", font=("Helvetica", 20), bg="#1e1e2f", fg=text_color)
artist_name_label = Label(frame, text="Artist Name: ", font=("Helvetica", 20), bg="#1e1e2f", fg=text_color)
timestamp_label = Label(frame, text="Timestamp: ", font=("Helvetica", 20), bg="#1e1e2f", fg=text_color)

moon_image_label = Label(frame, bg="#1e1e2f")
moon_image_label.pack(pady=20)

song_name_label.pack(pady=10)
artist_name_label.pack(pady=10)
timestamp_label.pack(pady=10)

def update_labels():
    if ser.in_waiting > 0:
        try:
            incoming_data = ser.readline().decode('utf-8', errors='ignore').strip()
            print("Received:", incoming_data) 

            parts = incoming_data.split('|')
            if len(parts) == 4:  
                song_name, artist_name, playback_status, timestamp = parts

                song_name_label.config(text=f"Song Name: {song_name}")
                artist_name_label.config(text=f"Artist Name: {artist_name}")
                timestamp_label.config(text=f"Timestamp: {timestamp}")

                if playback_status.lower() == "playing":
                    moon_image_label.config(image=bright_moon_image)
                else:
                    moon_image_label.config(image=dark_moon_image)
        except Exception as e:
            print("Error:", e)

    root.after(500, update_labels)

update_labels()

root.mainloop()
