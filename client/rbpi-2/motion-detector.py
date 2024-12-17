import cv2
from picamera2 import Picamera2
from datetime import datetime
from socket_client import send_event_to_server


def detect_motion(place_detected):
    picam2 = Picamera2()
    picam2.configure(picam2.create_preview_configuration(main={"size": (640, 480)}))
    picam2.start()

    detection_counter = 0
    previous_frame = None
    last_seen_at = datetime.now()
    is_first_detection = True
    try:
        while True:
            frame = picam2.capture_array()
            # Convert the frame to grayscale
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray_frame = cv2.GaussianBlur(
                gray_frame, (21, 21), 0
            )  # Blur to reduce noise

            # Initialize the previous frame if it's None
            if previous_frame is None:
                previous_frame = gray_frame
                continue

            # Compute the absolute difference between the current frame and the previous frame
            frame_diff = cv2.absdiff(previous_frame, gray_frame)
            _, thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)
            thresh = cv2.dilate(thresh, None, iterations=2)

            # Find contours in the threshold image
            contours, _ = cv2.findContours(
                thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            # Loop over the contours
            for contour in contours:
                if cv2.contourArea(contour) < 500:
                    continue
                (x, y, w, h) = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                detection_counter += 1

                # If detection happens for more than 10 frames
                if detection_counter > 10:
                    print("Adding detection event")
                    print(place_detected)

                    # Only log events with a min of difference
                    seen_at = datetime.now()
                    if (seen_at - last_seen_at).seconds > 60:
                        send_event_to_server(
                            {"location": place_detected, "timestamp": str(seen_at)}
                        )
                        last_seen_at = seen_at
                    if is_first_detection:
                        send_event_to_server(
                            {"location": place_detected, "timestamp": str(seen_at)}
                        )
                        last_seen_at = seen_at
                        is_first_detection = False

                    detection_counter = 0

            cv2.imshow("Cat Detection", frame)
            previous_frame = gray_frame

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:
        picam2.stop()
        cv2.destroyAllWindows()


detect_motion("2nd floor")
