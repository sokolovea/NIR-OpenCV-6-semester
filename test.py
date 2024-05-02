from ultralytics import YOLO

# Load a model
model = YOLO("yolov8n.pt")  # load an official detection model

# Track with the model
results = model.track(source="test_video_people.mp4", show=True) 