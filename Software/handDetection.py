import cv2
import mediapipe as mp
import math
from collections import deque
from spotify_auth import sp
import threading
import requests
import numpy as np
import time
import serial

# serial communication w/ ESP32
SERIAL_PORT = 'COM3'
BAUD_RATE = 115200
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
time.sleep(2)

# start mediapipe hand module
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# swipe detection
index_position_log = deque(maxlen=5)  
flick_speed_threshold = 0.3

# confirmation logs
gesture_log = deque(maxlen=15)
last_action = "No Gesture"
last_action_time = 0 
cooldown_time = 1

# caching song info and album art
cached_song_title = None
cached_artist_name = None
cached_playback_status = None
cached_album_art_image = None
cached_timestamp = 0
current_song_id = None
last_big_update_time = 0
last_small_update_time = 0
api_call_interval_small = 1 # sec

# dist calc
def calculate_distance(point1, point2):
    return math.sqrt((point2.x - point1.x) ** 2 + (point2.y - point1.y) ** 2)

# primary gesture detection func
def detect_gesture(landmarks):
    global index_position_log

    # for pinch
    thumb_tip = landmarks[4]
    index_tip = landmarks[8]
    thumb_index_distance = calculate_distance(thumb_tip, index_tip)

    # pinch threshold
    is_play_pause = thumb_index_distance < 0.05

    # index detection for swipe
    current_index_x = index_tip.x
    index_position_log.append(current_index_x)

    # swipe gestures
    if len(index_position_log) >= 2:
        speed = max(index_position_log) - min(index_position_log)
        # print(f"Index X-coordinates: {list(index_position_log)}")
        # print(f"Calculated Speed: {speed}")

        if abs(speed) > flick_speed_threshold:
            if index_position_log.index(max(index_position_log)) > index_position_log.index(min(index_position_log)):
                # print("RIGHT")
                return "Next Song"
            else:
                # print("LEFT")
                return "Previous Song"

    if is_play_pause:
        return "Pause/Play"
    else:
        return "No Gesture"

# ESP32 data sending function
def send_to_esp32(data):
    if ser.is_open:
        ser.write(data.encode('utf-8'))
        print("Sent to ESP32:", data)

# spotify playback functions
def next_song():
    threading.Thread(target=sp.next_track).start()
    print("EXECUTE NEXT SONG")
    big_update()

def previous_song():
    threading.Thread(target=sp.previous_track).start()
    print("EXECUTE PREVIOUS SONG")
    big_update()

def pause_play():
    def toggle_playback():
        playback = sp.current_playback()
        if playback and playback['is_playing']:
            print("PAUSE PLAYBACK")
            sp.pause_playback()
            cached_playback_status = "Paused"
        else:
            print("START PLAYBACK")
            sp.start_playback()
            cached_playback_status = "Playing"
        small_update_playback_status()
    threading.Thread(target=toggle_playback).start()
    small_update_playback_status()

# big update (song name, artist, playback status, album art)
def big_update():
    def fetch_big_update():
        global cached_song_title, cached_artist_name, cached_playback_status, cached_album_art_image
        playback = sp.current_playback()
        if playback and playback['item']:
            song_title = playback['item']['name']
            artist_name = playback['item']['artists'][0]['name']
            is_playing = playback['is_playing']
            album_art_url = playback['item']['album']['images'][0]['url']
            playback_status = "Playing" if is_playing else "Paused"
            data_to_send = f"{song_title}|{artist_name}|{playback_status}\n"
            send_to_esp32(data_to_send)

            # fetch album art
            response = requests.get(album_art_url)
            if response.status_code == 200:
                img_array = np.frombuffer(response.content, np.uint8)
                cached_album_art_image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            cached_song_title = song_title
            cached_artist_name = artist_name
            cached_playback_status = playback_status
        else:
            cached_song_title = "No Song"
            cached_artist_name = "No Artist"
            cached_playback_status = "Stopped"
            cached_album_art_image = None
    threading.Thread(target=fetch_big_update).start()

# small update (timestamp + natural song change)
def monitor_song():
    def fetch_monitoring_data():
        global cached_timestamp, current_song_id
        playback = sp.current_playback()
        if playback and playback['progress_ms']:
            new_timestamp = playback['progress_ms'] // 1000
            new_song_id = playback['item']['id']
            
            # FOR NATURAL SONG CHANGE
            # if song ID changes and timestamp is 0
            if new_timestamp == 0 and new_song_id != current_song_id:
                big_update()

            # update cached values
            cached_timestamp = new_timestamp
            current_song_id = new_song_id
            
            # UNCOMMENT THIS TO SHOW LED BLINKING ON SONG CHANGE + PLAYBACK STATUS
            # send_to_esp32(f"Timestamp: {cached_timestamp}\n") 
    threading.Thread(target=fetch_monitoring_data).start()

# small update (playback status)
def small_update_playback_status():
    def fetch_status():
        global cached_playback_status
        playback = sp.current_playback()
        if playback:
            playback_status = "Playing" if playback['is_playing'] else "Paused"
            cached_playback_status = playback_status
            send_to_esp32(f"Status: {cached_playback_status}\n")
    threading.Thread(target=fetch_status).start()

def get_current_song_info():
    playback = sp.current_playback()
    if playback and playback['item']:
        song_title = playback['item']['name']
        artist_name = playback['item']['artists'][0]['name']
        is_playing = playback['is_playing']
        return song_title, artist_name, "Playing" if is_playing else "Paused"
    return "No Song", "No Artist", "Stopped"

# gesture log + confirmation
def process_gesture_log():
    global last_action, last_action_time

    current_time = time.time()

    # counts
    gesture_counts = {
        "Next Song": gesture_log.count("Next Song"),
        "Previous Song": gesture_log.count("Previous Song"),
        "Pause/Play": gesture_log.count("Pause/Play")
    }

    # prevent action spam
    if current_time - last_action_time < cooldown_time:
        return "No Gesture"

    # log IFF gesture detected multiple times
    if gesture_counts["Next Song"] >= 2 and last_action != "Next Song":
        last_action = "Next Song"
        last_action_time = current_time
        next_song()
        return "Next Song Confirmed"
    elif gesture_counts["Previous Song"] >= 2 and last_action != "Previous Song":
        last_action = "Previous Song"
        last_action_time = current_time
        previous_song()
        return "Previous Song Confirmed"
    elif gesture_counts["Pause/Play"] >= 15 and last_action != "Pause/Play":
        last_action = "Pause/Play"
        last_action_time = current_time
        pause_play()
        return "Pause/Play Confirmed"
    else:
        last_action = "No Gesture"
        return "No Gesture"


def start():
    global last_small_update_time
    
    # video capture!
    cap = cv2.VideoCapture(0)

    big_update()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                # gesture detection
                gesture = detect_gesture(hand_landmarks.landmark)
                gesture_log.append(gesture)

                action = process_gesture_log()
                if action != "No Gesture":
                    print(action)
                cv2.putText(frame, action, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)

        # frequent small updates (1 sec)
        current_time = time.time()
        if current_time - last_small_update_time > api_call_interval_small:
            last_small_update_time = current_time
            monitor_song()
        
        # display current song info
        cv2.putText(frame, f"Song: {cached_song_title}", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"Artist: {cached_artist_name}", (10, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"Status: {cached_playback_status}", (10, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"Timestamp: {cached_timestamp} sec", (10, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # art
        if cached_album_art_image is not None:
            album_art_image = cv2.resize(cached_album_art_image, (100, 100))
            frame[10:110, 500:600] = album_art_image

        cv2.imshow("Moonify", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

#
#
#
#
#

if __name__ == "__main__":
    start()