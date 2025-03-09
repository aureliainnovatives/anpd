import yaml
import shutil
from pathlib import Path
from typing import Dict, Any, List
import torch
from ultralytics import YOLO
from ...models.base_model import BaseModel
from ...config.model_configs.yolo_config import YOLOV8_TRAINING_CONFIG
from .utils import validate_yolo_dataset, prepare_data_yaml

class YOLOTrainer(BaseModel):
    def __init__(self):
        self.model = None
        self.training_results = None
        self.project_dir = None

    async def validate_data(self, images: List[Path], labels: List[Path]) -> bool:
        """Validate image and label pairs"""
        if not images or not labels:
            return False
            
        # Check if we have matching image-label pairs
        image_names = {img.stem for img in images}
        label_names = {label.stem for label in labels}
        
        return bool(image_names.intersection(label_names))

    async def prepare_dataset(self, images: List[Path], labels: List[Path], dataset_dir: Path) -> str:
        """Organize files into YOLO format"""
        # Create YOLO directory structure
        train_img_dir = dataset_dir / 'images/train'
        val_img_dir = dataset_dir / 'images/val'
        train_label_dir = dataset_dir / 'labels/train'
        val_label_dir = dataset_dir / 'labels/val'
        
        for dir_path in [train_img_dir, val_img_dir, train_label_dir, val_label_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Split data into train/val (80/20 split)
        from sklearn.model_selection import train_test_split
        train_images, val_images = train_test_split(images, test_size=0.2, random_state=42)
        
        # Copy files to appropriate directories
        for img in train_images:
            shutil.copy(str(img), str(train_img_dir / img.name))
            label = next(l for l in labels if l.stem == img.stem)
            shutil.copy(str(label), str(train_label_dir / label.name))
            
        for img in val_images:
            shutil.copy(str(img), str(val_img_dir / img.name))
            label = next(l for l in labels if l.stem == img.stem)
            shutil.copy(str(label), str(val_label_dir / label.name))

        # Create data.yaml
        data_yaml = {
            'train': str(train_img_dir),
            'val': str(val_img_dir),
            'nc': self._get_num_classes(labels),
            'names': self._get_class_names(labels)
        }
        
        yaml_path = dataset_dir / 'data.yaml'
        with open(yaml_path, 'w') as f:
            yaml.dump(data_yaml, f)
            
        return str(dataset_dir)

    def _get_num_classes(self, labels: List[Path]) -> int:
        """Extract number of classes from labels"""
        classes = set()
        for label_file in labels:
            with open(label_file) as f:
                for line in f:
                    class_id = int(line.split()[0])
                    classes.add(class_id)
        return len(classes)

    def _get_class_names(self, labels: List[Path]) -> List[str]:
        """Get class names (using indices as names if not specified)"""
        num_classes = self._get_num_classes(labels)
        return [f'class_{i}' for i in range(num_classes)]

    async def train(self, config: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Let user choose model size
            model_size = config.get("model_size", "n")  # default to nano
            model_path = f'yolov8{model_size}.pt'
            
            # Initialize model
            self.model = YOLO(model_path)

            # Get absolute path for project directory
            project_dir = Path.cwd() / "runs" / "detect" / config["project_name"]
            
            # Training
            results = self.model.train(
                data=config["dataset_path"] + '/data.yaml',
                epochs=config.get("epochs", YOLOV8_TRAINING_CONFIG["epochs"]),
                imgsz=config.get("img_size", YOLOV8_TRAINING_CONFIG["img_size"]),
                batch=config.get("batch_size", YOLOV8_TRAINING_CONFIG["batch_size"]),
                name=config["project_name"],
                project="runs/detect"  # Specify project directory
            )

            self.training_results = results
            # Store the project directory for export
            self.project_dir = project_dir
            
            return {
                "status": "success",
                "metrics": results.results_dict
            }

        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    async def export_model(self, save_path: str) -> str:
        if not self.model or not self.training_results:
            raise ValueError("No trained model available to export")

        try:
            # Use best.pt from the training directory
            weights_dir = self.project_dir / "weights"
            best_model = weights_dir / "best.pt"
            
            if not best_model.exists():
                raise FileNotFoundError(f"Trained model not found at {best_model}")

            # Copy to the specified save location
            final_path = Path(save_path) / f"{self.training_results.name}_best.pt"
            shutil.copy(str(best_model), str(final_path))
            
            return str(final_path)
        except Exception as e:
            raise Exception(f"Failed to export model: {str(e)}") 