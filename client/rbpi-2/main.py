import os
import cv2
import numpy as np
import tensorflow.compat.v1 as tf
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as vis_util
from datetime import datetime
from socket_client import send_event_to_server
from picamera2 import Picamera2


tf.disable_v2_behavior()

# Camera constants
IM_WIDTH = 640
IM_HEIGHT = 480

# Paths to model files
MODEL_NAME = "ssdlite_mobilenet_v2_coco_2018_05_09"
ODD_PATH = "/home/fatima/tensorflow1/models/research/object_detection/"
PATH_TO_CKPT = os.path.join(ODD_PATH, MODEL_NAME, "frozen_inference_graph.pb")
PATH_TO_LABELS = os.path.join(ODD_PATH, "data", "mscoco_label_map.pbtxt")
# Classes the object identifies
NUM_CLASSES = 90

# Load maps
label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
categories = label_map_util.convert_label_map_to_categories(
    label_map, max_num_classes=NUM_CLASSES, use_display_name=True
)
category_index = label_map_util.create_category_index(categories)

# Load the Tensorflow model into memory.
detection_graph = tf.Graph()
with detection_graph.as_default():
    od_graph_def = tf.GraphDef()
    with tf.io.gfile.GFile(PATH_TO_CKPT, "rb") as fid:
        serialized_graph = fid.read()
        od_graph_def.ParseFromString(serialized_graph)
        tf.import_graph_def(od_graph_def, name="")

    sess = tf.Session(graph=detection_graph)


# Define input and output tensors (i.e. data) for the object detection classifier

# Input tensor is the image
image_tensor = detection_graph.get_tensor_by_name("image_tensor:0")

# Output tensors are the detection boxes, scores, and classes
# Each box represents a part of the image where a particular object was detected
detection_boxes = detection_graph.get_tensor_by_name("detection_boxes:0")

# Each score represents level of confidence for each of the objects.
# The score is shown on the result image, together with the class label.
detection_scores = detection_graph.get_tensor_by_name("detection_scores:0")
detection_classes = detection_graph.get_tensor_by_name("detection_classes:0")

# Number of objects detected
num_detections = detection_graph.get_tensor_by_name("num_detections:0")

# Define places coordinates
TL_studio = (10, 10)
BR_studio = (150, int(IM_HEIGHT - 5))

TL_bedroom = (630, 10)
BR_bedroom = (500, int(IM_HEIGHT - 5))


# Detection function
def cat_detection(frame):
    is_detected = False
    place_detected = None
    
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    input_data = cv2.resize(frame, (640, 480))  # Resize to model's input size
    input_data = np.expand_dims(input_data, axis=0)  # Add batch dimension

    # Perform the actual detection by running the model with the image as input
    (boxes, scores, classes, _) = sess.run(
        [detection_boxes, detection_scores, detection_classes, num_detections],
        feed_dict={image_tensor: input_data},
    )

    # Draw the results of the detection (aka 'visulaize the results')
    vis_util.visualize_boxes_and_labels_on_image_array(
        frame,
        np.squeeze(boxes),
        np.squeeze(classes).astype(np.int32),
        np.squeeze(scores),
        category_index,
        use_normalized_coordinates=True,
        line_thickness=8,
        min_score_thresh=0.85,
    )

    # Perform cat detection (or chair for testing purposes)
    if int(classes[0][0]) == 17 or int(classes[0][0]) == 18 or int(classes[0][0]) == 62:
        # Get coordinates
        x = int(((boxes[0][0][1] + boxes[0][0][3]) / 2) * IM_WIDTH)
        y = int(((boxes[0][0][0] + boxes[0][0][2]) / 2) * IM_HEIGHT)

        # Draw a circle at center of object
        cv2.circle(frame, (x, y), 5, (75, 13, 180), -1)
        place_detected = "2nd floor"
        print(f"Coordinates: {x}, {y}")

        # Detect place
        if (
            (x > TL_studio[0])
            and (x < BR_studio[0])
            and (y > TL_studio[1])
            and (y < BR_studio[1])
        ):
            place_detected = "Studio"

        if (
            (x > BR_bedroom[0])
            and (x < TL_bedroom[0])
            and (y > TL_bedroom[1])
            and (y < BR_bedroom[1])
        ):
            place_detected = "Bedroom"

        is_detected = True

    return frame, is_detected, place_detected


# Initialize frame rate calculation
frame_rate_calc = 1
freq = cv2.getTickFrequency()
font = cv2.FONT_HERSHEY_SIMPLEX

# Initialize Picam feed
cam = Picamera2()
cam.configure(
    cam.create_preview_configuration(
        main={"size": (IM_WIDTH, IM_HEIGHT)},
        controls={"FrameDurationLimits": (200000, 200000)},
    )
)
cam.start()

detection_counter = 0
last_seen_at = datetime.now()
is_first_detection = True
while True:
    t1 = cv2.getTickCount()

    # Acquire frame and expand frame dimensions to have shape: [1, None, None, 3]
    # i.e. a single-column array, where each item in the column has the pixel RGB value
    frame = cam.capture_array()

    # Pass frame into detection function
    frame, is_detected, place_detected = cat_detection(frame)

    if is_detected:
        detection_counter += 1

    cv2.putText(
        frame,
        "FPS: {0:.2f}".format(frame_rate_calc),
        (30, 50),
        font,
        1,
        (255, 255, 0),
        2,
        cv2.LINE_AA,
    )

    # Draw places rectangles
    cv2.rectangle(frame, TL_studio, BR_studio, (255, 20, 20), 3)
    cv2.putText(frame, "Studio", (12, 50), font, 1, (255, 20, 255), 2, cv2.LINE_AA)

    cv2.rectangle(frame, TL_bedroom, BR_bedroom, (20, 20, 255), 3)
    cv2.putText(frame, "Bedroom", (502, 50), font, 1, (20, 255, 255), 3, cv2.LINE_AA)

    # All the results have been drawn on the frame, so it's time to display it.
    cv2.imshow("Object detector", frame)

    t2 = cv2.getTickCount()
    time1 = (t2 - t1) / freq
    frame_rate_calc = 1 / time1

    # Press 'q' to quit
    if cv2.waitKey(1) == ord("q"):
        break

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

cam.close()
cv2.destroyAllWindows()
