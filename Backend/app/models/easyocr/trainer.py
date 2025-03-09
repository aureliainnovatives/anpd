from ..base_model import BaseModel
from ...config import DATASETS_DIR, TRAINED_MODELS_DIR
import easyocr
import torch
from pathlib import Path
import yaml
import shutil

class EasyOCRTrainer(BaseModel):
    def __init__(self):
        self.model = None
        self.training_results = None
        self.project_dir = None

    async def validate_data(self, images, labels):
        """Validate image and label pairs for OCR training"""
        if not images or not labels:
            return False
            
        # Check if we have matching image-label pairs
        image_names = {Path(img.filename).stem for img in images}
        label_names = {Path(label.filename).stem for label in labels}
        
        return bool(image_names.intersection(label_names))

    async def prepare_dataset(self, images, labels, dataset_dir):
        """Prepare dataset for EasyOCR training"""
        train_dir = dataset_dir / 'train'
        val_dir = dataset_dir / 'val'
        
        for dir_path in [train_dir, val_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Create dataset structure required by EasyOCR
        for img, label in zip(images, labels):
            # Copy images and labels to training directory using filename
            shutil.copy(str(img.file.fileno()), str(train_dir / img.filename))
            shutil.copy(str(label.file.fileno()), str(train_dir / label.filename))

        return str(dataset_dir)

    async def train(self, config):
        """Train EasyOCR model"""
        try:
            # Initialize EasyOCR with custom parameters
            reader = easyocr.Reader(['en'])  # Initialize with English
            
            training_params = {
                'learning_rate': config.get('learning_rate', 0.001),
                'num_epochs': config.get('epochs', 100),
                'batch_size': config.get('batch_size', 32),
                'optimizer': config.get('optimizer', 'adam'),
                'dataset_path': config['dataset_path']
            }

            # Train the model
            self.model = reader.train(
                data_path=training_params['dataset_path'],
                lr=training_params['learning_rate'],
                num_epochs=training_params['num_epochs'],
                batch_size=training_params['batch_size'],
                optimizer=training_params['optimizer']
            )

            return {
                "status": "success",
                "metrics": {
                    "epochs_completed": training_params['num_epochs']
                }
            }

        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    async def export_model(self, save_path):
        """Export trained OCR model"""
        if not self.model:
            raise ValueError("No trained model available to export")

        try:
            # Save the model
            model_path = Path(save_path) / "easyocr_model.pth"
            torch.save(self.model.state_dict(), str(model_path))
            return str(model_path)
        except Exception as e:
            raise Exception(f"Failed to export model: {str(e)}") 