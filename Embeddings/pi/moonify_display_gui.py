import serial
import time
from tkinter import Tk, Label, Frame, PhotoImage

# Configure serial port (adjust "/dev/ttyS0" if using a different port)
SERIAL_PORT = '/dev/serial0'  # Use '/dev/ttyUSB0' if connected via USB
BAUD_RATE = 115200

# Initialize serial connection
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
time.sleep(2)  # Wait for the connection to initialize

# Setup the GUI using Tkinter
root = Tk()
root.title("Moonify Data Display")
root.geometry("800x480")  # Adjust based on your screen resolution
root.configure(bg="black")  # Space theme with a black background

# Load a background image or create a gradient effect
try:
    bg_image = PhotoImage(file="path_to_your_space_background.png")  # Add your space-themed image here
    background_label = Label(root, image=bg_image)
    background_label.place(relwidth=1, relheight=1)
except:
    root.configure(bg="black")  # Fallback to a solid black background if no image is found

# Create a frame with a semi-transparent background
frame = Frame(root, bg="#1e1e2f", bd=5)
frame.place(relx=0.5, rely=0.1, relwidth=0.9, relheight=0.8, anchor='n')

# Space-themed text color
text_color = "lightblue"

# Labels to display the data with a space theme
song_name_label = Label(frame, text="Song Name: ", font=("Helvetica", 20), bg="#1e1e2f", fg=text_color)
artist_name_label = Label(frame, text="Artist Name: ", font=("Helvetica", 20), bg="#1e1e2f", fg=text_color)
playback_status_label = Label(frame, text="Playback Status: ", font=("Helvetica", 20), bg="#1e1e2f", fg=text_color)
timestamp_label = Label(frame, text="Timestamp: ", font=("Helvetica", 20), bg="#1e1e2f", fg=text_color)

# Pack the labels onto the GUI with some padding
song_name_label.pack(pady=10)
artist_name_label.pack(pady=10)
playback_status_label.pack(pady=10)
timestamp_label.pack(pady=10)

def update_labels():
    # Read data from the serial port
    if ser.in_waiting > 0:
        try:
            incoming_data = ser.readline().decode('utf-8', errors='ignore').strip()
            print("Received:", incoming_data)  # For debugging

            # Parse the incoming data using '|' as the delimiter
            parts = incoming_data.split('|')
            if len(parts) == 4:  # Adjusted to expect 4 parts
                song_name, artist_name, playback_status, timestamp = parts

                # Update the labels with the new data
                song_name_label.config(text=f"Song Name: {song_name}")
                artist_name_label.config(text=f"Artist Name: {artist_name}")
                playback_status_label.config(text=f"Playback Status: {playback_status}")
                timestamp_label.config(text=f"Timestamp: {timestamp}")
        except Exception as e:
            print("Error:", e)

    # Schedule the function to run again after 500 ms
    root.after(500, update_labels)

# Start the update loop
update_labels()

# Run the GUI loop
root.mainloop()
