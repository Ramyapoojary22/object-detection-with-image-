from ultralytics import YOLO
import cv2

# 🔥 Use better model (more accurate than yolov8n)
model = YOLO("yolov8m.pt")   # you can use yolov8s.pt if system is slow

def detect_objects(image_path, output_path):
    results = model(image_path)

    object_counts = {}
    detected_objects = []

    CONF_THRESHOLD = 0.6   # 🔥 ignore weak predictions

    for r in results:
        boxes = r.boxes
        names = model.names

        for box in boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            label = names[cls]

            # 🚫 Skip low confidence detections
            if conf < CONF_THRESHOLD:
                continue

            # Count objects
            object_counts[label] = object_counts.get(label, 0) + 1

            # Store details
            detected_objects.append({
                "name": label,
                "confidence": round(conf * 100, 2)
            })

        # Draw bounding boxes (only high-confidence boxes will remain visually strong)
        img = r.plot()
        cv2.imwrite(output_path, img)

    # 🔥 If nothing detected
    if not object_counts:
        summary = "No clear objects detected"
    else:
        summary = ", ".join([f"{v} {k}" for k, v in object_counts.items()])

    return output_path, object_counts, detected_objects, summary