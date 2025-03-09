from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import Dict, List, Any
import shutil
from pathlib import Path
import aiofiles
from pydantic import BaseModel

from ...config import DATASETS_DIR, TRAINED_MODELS_DIR
from ...models.yolo.trainer import YOLOTrainer
from ...models.model_registry import ModelRegistry
from ..schemas.training import TrainingRequest, TrainingResponse, UploadResponse

router = APIRouter()

@router.get("/available-models")
async def get_available_models():
    """Get list of available models"""
    return {"models": ModelRegistry.get_available_models()}

@router.post("/upload-files", response_model=UploadResponse)
async def upload_files(
    model_type: str = Form(...),
    images: List[UploadFile] = File(...),
    labels: List[UploadFile] = File(...),
):
    """Upload images and labels for training"""
    try:
        model_class = ModelRegistry.get_model(model_type)
        trainer = model_class()

        if not await trainer.validate_data(images, labels):
            raise HTTPException(status_code=400, detail="Invalid dataset format")

        # Create directories for this upload
        upload_dir = DATASETS_DIR / f"{model_type}_{Path(images[0].filename).stem}"
        upload_dir.mkdir(parents=True, exist_ok=True)

        image_paths = []
        label_paths = []

        # Save images
        for img in images:
            file_path = upload_dir / "raw_images" / img.filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(file_path, 'wb') as f:
                content = await img.read()
                await f.write(content)
            image_paths.append(file_path)

        # Save labels
        for label in labels:
            file_path = upload_dir / "raw_labels" / label.filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(file_path, 'wb') as f:
                content = await label.read()
                await f.write(content)
            label_paths.append(file_path)

        # Prepare dataset in model-specific format
        dataset_path = await trainer.prepare_dataset(image_paths, label_paths, upload_dir)

        return UploadResponse(
            status="success",
            dataset_path=str(dataset_path),
            num_files=len(image_paths)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/start-training", response_model=TrainingResponse)
async def start_training(request: TrainingRequest):
    """Start model training"""
    try:
        model_class = ModelRegistry.get_model(request.model_type)
        trainer = model_class()
        training_result = await trainer.train({
            "dataset_path": request.dataset_path,
            **request.config
        })

        if training_result["status"] == "error":
            raise HTTPException(status_code=500, detail=training_result["message"])

        model_path = await trainer.export_model(TRAINED_MODELS_DIR)

        return TrainingResponse(
            status="success",
            message="Training completed successfully",
            model_path=model_path
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 