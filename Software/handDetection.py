import cv2
import mediapipe as mp
import math
from collections import deque
from spotify_auth import sp
import threading
import requests
import numpy as np
import time

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


# caching song info and album art
cached_song_title = None
cached_artist_name = None
cached_playback_status = None
cached_album_art_image = None
cached_timestamp = 0
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
    threading.Thread(target=toggle_playback).start()

# big update (song name, artist, playback status, album art)
def big_update():
    global cached_song_title, cached_artist_name, cached_playback_status, cached_album_art_image
    playback = sp.current_playback()
    if playback and playback['item']:
        song_title = playback['item']['name']
        artist_name = playback['item']['artists'][0]['name']
        is_playing = playback['is_playing']
        album_art_url = playback['item']['album']['images'][0]['url']

        cached_song_title = song_title
        cached_artist_name = artist_name
        cached_playback_status = "Playing" if is_playing else "Paused"

        # fetch album art
        response = requests.get(album_art_url)
        if response.status_code == 200:
            img_array = np.frombuffer(response.content, np.uint8)
            cached_album_art_image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    else:
        cached_song_title = "No Song"
        cached_artist_name = "No Artist"
        cached_playback_status = "Stopped"
        cached_album_art_image = None

# small update (timestamp)
def small_update_timestamp():
    global cached_timestamp
    playback = sp.current_playback()
    if playback and playback['progress_ms']:
        cached_timestamp = playback['progress_ms'] // 1000

# small update (playback status)
def small_update_playback_status():
    global cached_playback_status
    playback = sp.current_playback()
    if playback:
        cached_playback_status = "Playing" if playback['is_playing'] else "Paused"

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
    global last_action

    # counts
    gesture_counts = {
        "Next Song": gesture_log.count("Next Song"),
        "Previous Song": gesture_log.count("Previous Song"),
        "Pause/Play": gesture_log.count("Pause/Play")
    }

    # log IFF gesture detected multiple times
    if gesture_counts["Next Song"] >= 2 and last_action != "Next Song":
        last_action = "Next Song"
        next_song()
        return "Next Song Confirmed"
    elif gesture_counts["Previous Song"] >= 2 and last_action != "Previous Song":
        last_action = "Previous Song"
        previous_song()
        return "Previous Song Confirmed"
    elif gesture_counts["Pause/Play"] >= 15 and last_action != "Pause/Play":
        last_action = "Pause/Play"
        pause_play()
        return "Pause/Play Confirmed"
    elif gesture_counts["Next Song"] < 2 and gesture_counts["Previous Song"] < 2 and gesture_counts["Pause/Play"] < 15:
        last_action = "No Gesture"  # no special gesture detected => reset last action 
    else:
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
                print(action)
                cv2.putText(frame, action, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)

        # frequent small updates
        current_time = time.time()
        if current_time - last_small_update_time > api_call_interval_small:
            last_small_update_time = current_time
            small_update_timestamp()
        
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

if __name__ == "__main__":
    start()