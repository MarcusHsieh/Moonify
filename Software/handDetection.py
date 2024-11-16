import cv2
import mediapipe as mp
import math
from collections import deque
from spotify_auth import sp
import threading

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

def previous_song():
    threading.Thread(target=sp.previous_track).start()
    print("EXECUTE PREVIOUS SONG")

def pause_play():
    def toggle_playback():
        playback = sp.current_playback()
        if playback and playback['is_playing']:
            print("PAUSE PLAYBACK")
            sp.pause_playback()
        else:
            print("START PLAYBACK")
            sp.start_playback()
    threading.Thread(target=toggle_playback).start()

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

# video capture!
cap = cv2.VideoCapture(0)

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

    cv2.imshow("Moonify", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
