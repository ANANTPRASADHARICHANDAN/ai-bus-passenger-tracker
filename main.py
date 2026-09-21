import cv2
import os
import requests
from ultralytics import YOLO

# ============================================================
# BUS PASSENGER & SEAT MONITORING SYSTEM (WITH API SYNC)
# ============================================================

DJANGO_API_URL = "http://127.0.0.1:8000/api/update-telemetry/"

possible_videos = ["busCamera.mp4"]
VIDEO_PATH = next((v for v in possible_videos if os.path.exists(v)), "busCamera.mp4")

MODEL_PATH = "yolov8n.pt"
CONFIDENCE = 0.35

EXTERIOR_1_START, EXTERIOR_1_END = 0.0, 6.3
INTERIOR_1_START, INTERIOR_1_END = 6.3, 11.3
EXTERIOR_2_START, EXTERIOR_2_END = 11.3, 16.5
INTERIOR_2_START, INTERIOR_2_END = 16.5, 19.5

DOOR_X1, DOOR_X2 = 250, 1150
LINE_Y = 580  

# Capacity Configuration
TOTAL_SEATS = 24
BASE_PASSENGERS = 23  

print("==========================================")
print(f"Loading YOLO model ({MODEL_PATH})...")
model = YOLO(MODEL_PATH)

cap = cv2.VideoCapture(VIDEO_PATH)
if not cap.isOpened():
    print(f"ERROR: Cannot open video file: {VIDEO_PATH}")
    exit()

fps = cap.get(cv2.CAP_PROP_FPS)

previous_y_positions = {}
boarding_ids = set()
deboarding_ids = set()

last_sent_state = None  # To track when to send data to Django
frame_number = 0

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    current_time = frame_number / fps
    exterior_1 = EXTERIOR_1_START <= current_time <= EXTERIOR_1_END
    
    results = model.track(frame, persist=True, tracker="bytetrack.yaml", classes=[0], conf=CONFIDENCE, verbose=False)

    if len(results) > 0 and results[0].boxes is not None and results[0].boxes.id is not None:
        boxes = results[0].boxes.xyxy.cpu().numpy()
        track_ids = results[0].boxes.id.int().cpu().tolist()

        for box, track_id in zip(boxes, track_ids):
            x1, y1, x2, y2 = map(int, box)
            foot_x, foot_y = int((x1 + x2) / 2), int(y2)

            if exterior_1 and DOOR_X1 <= foot_x <= DOOR_X2:
                if track_id in previous_y_positions:
                    prev_y = previous_y_positions[track_id]

                    if prev_y < LINE_Y and foot_y >= LINE_Y:
                        deboarding_ids.add(track_id)
                    elif prev_y > LINE_Y and foot_y <= LINE_Y:
                        boarding_ids.add(track_id)

                previous_y_positions[track_id] = foot_y

            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
            cv2.circle(frame, (foot_x, foot_y), 5, (0, 255, 255), -1)

    # Calculate metrics
    total_boarding = len(boarding_ids)
    total_deboarding = len(deboarding_ids)
    net_passengers_inside = max(0, BASE_PASSENGERS + total_boarding - total_deboarding)
    
    # REMOVED max(0) so available seats can go negative when overloaded
    available_seats = TOTAL_SEATS - net_passengers_inside

    # ============================================================
    # TRANSMIT DATA TO DJANGO BACKEND
    # ============================================================
    current_state = (total_boarding, total_deboarding)
    
    # Only send an HTTP request if the passenger counts have changed
    if current_state != last_sent_state:
        payload = {
            "boarding": total_boarding,
            "deboarding": total_deboarding,
            "inside": net_passengers_inside,
            "available": available_seats,
            "is_full": net_passengers_inside >= TOTAL_SEATS
        }
        try:
            # Send data to your running Django server
            response = requests.post(DJANGO_API_URL, json=payload, timeout=0.5)
            if response.status_code == 200:
                last_sent_state = current_state
                print(f"--> Syncing to Django: {payload}")
            else:
                print(f"--> Django Rejected Data: {response.text}")
        except requests.exceptions.RequestException:
            pass # Fail silently so the video playback doesn't freeze

    # Visual Dashboard Overlay
    cv2.rectangle(frame, (15, 15), (550, 270), (0, 0, 0), -1)
    cv2.putText(frame, f"BOARDING: {total_boarding}", (30, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(frame, f"DEBOARDING: {total_deboarding}", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    cv2.putText(frame, f"PASSENGERS INSIDE: {net_passengers_inside} / {TOTAL_SEATS}", (30, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    cv2.putText(frame, f"AVAILABLE SEATS: {available_seats}", (30, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # DRIVER ALERT LOGIC (WITH OVERLOAD WARNING)
    if net_passengers_inside > TOTAL_SEATS:
        # Solid red box to aggressively warn the driver
        cv2.rectangle(frame, (20, 190), (530, 260), (0, 0, 255), -1) 
        cv2.putText(frame, "CRITICAL: BUS OVERLOADED!", (30, 225), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(frame, f"REMOVE {net_passengers_inside - TOTAL_SEATS} PASSENGER(S)", (30, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    elif net_passengers_inside == TOTAL_SEATS:
        cv2.putText(frame, "ALERT: BUS FULL!", (30, 210), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
        cv2.putText(frame, "DO NOT ALLOW BOARDING", (30, 245), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    else:
        cv2.putText(frame, "STATUS: BOARDING ALLOWED", (30, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    if exterior_1:
        cv2.line(frame, (DOOR_X1, LINE_Y), (DOOR_X2, LINE_Y), (0, 255, 0), 3)

    cv2.imshow("Bus Driver Dashboard View", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    frame_number += 1

cap.release()
cv2.destroyAllWindows()