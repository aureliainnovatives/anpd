import torch

FASTER_RCNN_TRAINING_CONFIG = {
    "epochs": 100,
    "batch_size": 16,
    "learning_rate": 0.001,
    "backbone": "resnet50",
    "anchor_sizes": ((32,), (64,), (128,), (256,), (512,)),
    "device": "cuda" if torch.cuda.is_available() else "cpu"
} 