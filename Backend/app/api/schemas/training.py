from pydantic import BaseModel
from typing import List, Optional, Dict

class TrainingConfig(BaseModel):
    project_name: str
    dataset_path: str
    num_classes: int
    class_names: List[str]
    epochs: Optional[int] = None
    batch_size: Optional[int] = None
    img_size: Optional[int] = None

class TrainingRequest(BaseModel):
    """Request schema for model training"""
    model_type: str
    dataset_path: str
    config: Dict

class TrainingResponse(BaseModel):
    """Response schema for model training"""
    status: str
    message: str
    model_path: Optional[str] = None

class UploadResponse(BaseModel):
    """Response schema for file uploads"""
    status: str
    dataset_path: str
    num_files: int 