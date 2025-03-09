import torch

YOLOV8_TRAINING_CONFIG = {
    "epochs": 100,
    "batch_size": 16,
    "img_size": 640,
    "device": "cuda" if torch.cuda.is_available() else "cpu"
} 