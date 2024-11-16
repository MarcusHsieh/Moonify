import cv2
import mediapipe as mp
import math

# start mediapipe hand module
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# swipe detection
previous_x = None
swipe_threshold = 0.1

# dist calc
def calculate_distance(point1, point2):
    return math.sqrt((point2.x - point1.x) ** 2 + (point2.y - point1.y) ** 2)

# primary gesture detection func
def detect_gesture(landmarks):
    global previous_x

    # for pinch
    thumb_tip = landmarks[4]
    index_tip = landmarks[8]
    thumb_index_distance = calculate_distance(thumb_tip, index_tip)

    # pinch threshold
    is_play_pause = thumb_index_distance < 0.05

    # wrist detection for swipe
    current_x = landmarks[0].x

    # swipe gestures
    if previous_x is None:
        previous_x = current_x
        return "No Gesture"

    if current_x - previous_x > swipe_threshold:
        previous_x = current_x
        return "Swipe Right (Next Song)"
    elif previous_x - current_x > swipe_threshold:
        previous_x = current_x
        return "Swipe Left (Previous Song)"
    
    previous_x = current_x

    if is_play_pause:
        return "Pause/Play"
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
            cv2.putText(frame, gesture, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)

    cv2.imshow("Moonify", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
