import cv2
import mediapipe as mp
import math

# start mediapipe hand module
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# dist calc
def calculate_distance(point1, point2):
    return math.sqrt((point2.x - point1.x) ** 2 + (point2.y - point1.y) ** 2)

# primary gesture detection func
def detect_gesture(landmarks):
    thumb_tip = landmarks[4]
    index_tip = landmarks[8]
    middle_tip = landmarks[12]
    ring_tip = landmarks[16]
    pinky_tip = landmarks[20]

    index_base = landmarks[5]
    middle_base = landmarks[9]
    ring_base = landmarks[13]
    pinky_base = landmarks[17]

    # fingers all open + spread
    is_open_palm = (
        calculate_distance(index_tip, index_base) > 0.1 and
        calculate_distance(middle_tip, middle_base) > 0.1 and
        calculate_distance(ring_tip, ring_base) > 0.1 and
        calculate_distance(pinky_tip, pinky_base) > 0.1
    )

    # fist
    is_fist = (
        calculate_distance(index_tip, index_base) < 0.05 and
        calculate_distance(middle_tip, middle_base) < 0.05 and
        calculate_distance(ring_tip, ring_base) < 0.05 and
        calculate_distance(pinky_tip, pinky_base) < 0.05
    )

    if is_open_palm:
        return "Next Song"
    elif is_fist:
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
            cv2.putText(frame, gesture, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    cv2.imshow("Moonify", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
