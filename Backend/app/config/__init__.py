from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATASETS_DIR = BASE_DIR / "datasets"
TRAINED_MODELS_DIR = BASE_DIR / "models/trained"

# Import all model configs
from .model_configs.yolo_config import YOLOV8_TRAINING_CONFIG
from .model_configs.faster_rcnn_config import FASTER_RCNN_TRAINING_CONFIG

# Create required directories
DATASETS_DIR.mkdir(parents=True, exist_ok=True)
TRAINED_MODELS_DIR.mkdir(parents=True, exist_ok=True) 