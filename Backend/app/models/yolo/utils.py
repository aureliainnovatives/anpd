from typing import List, Dict
from pathlib import Path
import yaml
import shutil
from ...config.model_configs.yolo_config import YOLOV8_TRAINING_CONFIG

def validate_yolo_dataset(images: List[Path], labels: List[Path]) -> bool:
    """Validate YOLO format dataset"""
    if not images or not labels:
        return False
        
    # Check if we have matching image-label pairs
    image_names = {img.stem for img in images}
    label_names = {label.stem for label in labels}
    
    return bool(image_names.intersection(label_names))

def prepare_data_yaml(train_path: Path, val_path: Path, num_classes: int, class_names: List[str]) -> str:
    """Create YOLO data.yaml file"""
    data = {
        'train': str(train_path),
        'val': str(val_path),
        'nc': num_classes,
        'names': class_names
    }
    
    yaml_path = train_path.parent.parent / 'data.yaml'
    with open(yaml_path, 'w') as f:
        yaml.dump(data, f)
        
    return str(yaml_path)

async def validate_yolo_dataset(dataset_path: str) -> bool:
    """Validate YOLO dataset structure"""
    path = Path(dataset_path)
    required_dirs = ['images/train', 'images/val', 'labels/train', 'labels/val']
    
    try:
        # Check if all required directories exist
        for dir_path in required_dirs:
            if not (path / dir_path).exists():
                return False
                
        # Check if there are matching image and label files
        for split in ['train', 'val']:
            images = set(f.stem for f in (path / f'images/{split}').glob('*.*'))
            labels = set(f.stem for f in (path / f'labels/{split}').glob('*.txt'))
            
            if not images or not labels:
                return False
                
            if not images.intersection(labels):
                return False
                
        return True
    except Exception:
        return False

async def prepare_data_yaml(
    dataset_path: str,
    num_classes: int,
    class_names: List[str]
) -> str:
    """Create data.yaml file for training"""
    dataset_path = Path(dataset_path)
    
    data_yaml = YOLOV8_TRAINING_CONFIG["data_yaml_template"].format(
        train_path=str(dataset_path / 'images/train'),
        val_path=str(dataset_path / 'images/val'),
        test_path=str(dataset_path / 'images/val'),
        num_classes=num_classes,
        class_names=class_names
    )
    
    yaml_path = dataset_path / 'data.yaml'
    with open(yaml_path, 'w') as f:
        f.write(data_yaml)
        
    return str(yaml_path) 