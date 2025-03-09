from abc import ABC, abstractmethod
from typing import Dict, Any, List
from pathlib import Path

class BaseModel(ABC):
    @abstractmethod
    async def prepare_dataset(self, images: List[Path], labels: List[Path], dataset_dir: Path) -> str:
        """Prepare dataset according to model requirements"""
        pass

    @abstractmethod
    async def train(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Train the model"""
        pass

    @abstractmethod
    async def validate_data(self, images: List[Path], labels: List[Path]) -> bool:
        """Validate uploaded data"""
        pass

    @abstractmethod
    async def export_model(self, save_path: str) -> str:
        """Export trained model"""
        pass 