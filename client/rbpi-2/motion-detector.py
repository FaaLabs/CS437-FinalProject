import cv2
from picamera2 import Picamera2


def detect_motion():
    picam2 = Picamera2()
    picam2.configure(picam2.create_preview_configuration(main={"size": (640, 480)}))
    picam2.start()

    previous_frame = None
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
                print("Motion detected!")

            cv2.imshow("Motion Detection", frame)
            previous_frame = gray_frame

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:
        picam2.stop()
        cv2.destroyAllWindows()

detect_motion()
