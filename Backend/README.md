# AI Model Training Backend

## Project Structure
Backend/
├── app/
│ ├── models/
│ │ ├── init.py
│ │ ├── base_model.py # Abstract base class for all models
│ │ ├── model_registry.py # Central registry for all models
│ │ ├── yolo/
│ │ │ ├── init.py
│ │ │ ├── trainer.py # YOLO implementation
│ │ │ └── utils.py
│ │ └── faster_rcnn/ # Example of adding new model
│ │ ├── init.py
│ │ └── trainer.py
│ ├── api/
│ │ ├── init.py
│ │ ├── endpoints/
│ │ │ ├── init.py
│ │ │ └── training.py # API endpoints for training
│ │ └── schemas/
│ │ ├── init.py
│ │ └── training.py # Pydantic models for requests/responses
│ ├── config/
│ │ ├── init.py # Base paths and configurations
│ │ └── model_configs/
│ │ ├── yolo_config.py # YOLO-specific settings
│ │ └── faster_rcnn_config.py
│ └── main.py # FastAPI application entry point
├── models/
│ └── trained/ # Directory for saved models
├── datasets/ # Directory for uploaded datasets
├── requirements.txt # Project dependencies
└── README.md # This file

## Understanding YOLO Training Parameters

### 1. Epochs (How many times to practice?)
Think of epochs like practice sessions:
- If epochs = 50, the model will practice with your images 50 times
- More practice (higher epochs):
  - ✅ Better accuracy
  - ❌ Takes longer to train
  - ❌ Might memorize instead of learn
- Recommended values:
  - Quick training: 30-50 epochs
  - Good results: 100 epochs
  - Best results: 150-200 epochs

### 2. Batch Size (How many images at once?)
Like studying multiple flashcards at once:
- If batch_size = 16, model looks at 16 images simultaneously
- Larger batch size:
  - ✅ Faster training
  - ❌ Needs more computer memory
- Recommended values:
  - For most computers: 16
  - Limited memory: 8
  - Powerful GPU: 32 or 64

### 3. Image Size (How detailed should the model look?)
Like looking at a picture up close or from far away:
- If img_size = 640, images will be 640x640 pixels
- Larger size:
  - ✅ Better at finding small objects
  - ❌ Slower training
  - ❌ Needs more memory
- Recommended values:
  - Standard: 640x640
  - Small objects: 832x832
  - Fast training: 416x416

### Quick Reference Guide

| If you want... | Epochs | Batch Size | Image Size |
|----------------|--------|------------|------------|
| Fast Training  | 50     | 32         | 416        |
| Balanced      | 100    | 16         | 640        |
| Best Accuracy | 150    | 8          | 832        |

### Tips for Best Results
1. Start with the balanced settings
2. If training is too slow:
   - Reduce image size
   - Increase batch size
3. If accuracy is poor:
   - Increase epochs
   - Decrease batch size
   - Increase image size
