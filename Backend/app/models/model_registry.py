from typing import Dict, Type, List
from .base_model import BaseModel
from .yolo.trainer import YOLOTrainer
from .easyocr.trainer import EasyOCRTrainer
from .faster_rcnn.trainer import FasterRCNNTrainer
# Import new model trainers here

class ModelRegistry:
    _models: Dict[str, Type[BaseModel]] = {
        "yolo": YOLOTrainer,
        "easyocr": EasyOCRTrainer,
        "faster_rcnn": FasterRCNNTrainer,
        # Add new models here
        # "faster_rcnn": FasterRCNNTrainer,
    }

    @classmethod
    def get_model(cls, model_type: str) -> Type[BaseModel]:
        if model_type not in cls._models:
            raise ValueError(f"Unsupported model type: {model_type}")
        return cls._models[model_type]

    @classmethod
    def register_model(cls, name: str, model_class: Type[BaseModel]):
        cls._models[name] = model_class

    @classmethod
    def get_available_models(cls) -> List[str]:
        return list(cls._models.keys()) 