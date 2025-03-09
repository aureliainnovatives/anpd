import { Component } from '@angular/core';
import { HttpClient } from '@angular/common/http';

interface TrainingConfig {
  model_type: string;
  dataset_path: string;
  config: {
    project_name: string;
    epochs: number;
    batch_size: number;
    learning_rate: number;
    optimizer: string;
    img_size?: number;
    data_yaml_path?: string;
  }
}

@Component({
  selector: 'app-upload-data',
  templateUrl: './upload-data.component.html',
  styleUrls: ['./upload-data.component.css']
})
export class UploadDataComponent {
  selectedImages: File[] = [];
  selectedLabels: File[] = [];
  trainingConfig = {
    projectName: '',
    epochs: 100,
    batchSize: 16,
    imgSize: 640,
    learningRate: 0.001,
    optimizer: 'adam'
  };
  isTraining = false;
  uploadProgress = 0;
  trainingStatus = '';
  selectedModel: string = 'yolo';  // Default to YOLO

  constructor(private http: HttpClient) {}

  onImagesSelected(event: any) {
    this.selectedImages = Array.from(event.target.files);
  }

  onLabelsSelected(event: any) {
    this.selectedLabels = Array.from(event.target.files);
  }

  async startTraining() {
    this.isTraining = true;
    this.trainingStatus = 'Uploading files...';

    try {
      // Upload files
      const formData = new FormData();
      formData.append('model_type', this.selectedModel);
      this.selectedImages.forEach(file => formData.append('images', file));
      this.selectedLabels.forEach(file => formData.append('labels', file));

      const uploadResponse = await this.http.post('http://localhost:8000/api/training/upload-files', formData).toPromise();

      this.trainingStatus = 'Starting training...';

      // Start training with model-specific config
      const trainingConfig: TrainingConfig = {
        model_type: this.selectedModel,
        dataset_path: (uploadResponse as any).dataset_path,
        config: {
          project_name: this.trainingConfig.projectName,
          epochs: this.trainingConfig.epochs,
          batch_size: this.trainingConfig.batchSize,
          learning_rate: this.trainingConfig.learningRate,
          optimizer: this.trainingConfig.optimizer
        }
      };

      // Add YOLO-specific parameters if needed
      if (this.selectedModel === 'yolo') {
        trainingConfig.config.img_size = this.trainingConfig.imgSize;
        trainingConfig.config.data_yaml_path = `${(uploadResponse as any).dataset_path}/data.yaml`;
      }

      const trainingResponse = await this.http.post('http://localhost:8000/api/training/start-training', trainingConfig).toPromise();
      
      this.trainingStatus = 'Training completed! Model saved at: ' + (trainingResponse as any).model_path;

    } catch (error: any) {
      this.trainingStatus = 'Error: ' + (error.error?.detail || error.message || 'Unknown error');
    } finally {
      this.isTraining = false;
    }
  }

  isOCRModel(): boolean {
    // Get the selected model from your service or state management
    return this.selectedModel === 'easyocr';
  }
} 