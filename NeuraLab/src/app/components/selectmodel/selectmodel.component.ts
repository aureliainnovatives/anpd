import { Component } from '@angular/core';
import { Router } from '@angular/router';

interface ModelCard {
  id: string;
  title: string;
  description: string;
  imageUrl: string;
  details: string[];
  category: string;
  selected: boolean;
}

@Component({
  selector: 'app-selectmodel',
  templateUrl: './selectmodel.component.html',
  styleUrl: './selectmodel.component.css'
})
export class SelectmodelComponent {
  loading: boolean = false;
  error: string = '';
  modelCards: ModelCard[] = [
    {
      id: 'yolo',
      title: 'YOLO (You Only Look Once)',
      description: 'Real-time object detection model for computer vision',
      imageUrl: 'assets/model-images/YOLO.png',
      details: [
        'Best for object detection tasks',
        'Real-time processing capability',
        'High accuracy in diverse scenarios'
      ],
      category: 'Computer Vision',
      selected: false
    },
    {
      id: 'easyocr',
      title: 'EasyOCR',
      description: 'Ready-to-use OCR with 80+ supported languages',
      imageUrl: 'assets/model-images/easyocr.jpeg',
      details: [
        'Text detection and recognition',
        'Multiple language support',
        'Custom training capability'
      ],
      category: 'Computer Vision',
      selected: false
    },
    {
      id: 'ChatGPT',
      title: 'ChatGPT',
      description: 'Deep residual learning for image recognition',
      imageUrl: 'assets/model-images/ChatGPTT.png',
      details: [
        'Image classification',
        'Feature extraction',
        'Transfer learning support'
      ],
      category: 'Computer Vision',
      selected: false
    },

    // Add more models as needed
  ];

  // Group models by category
  get modelsByCategory() {
    const grouped = new Map<string, ModelCard[]>();
    this.modelCards.forEach(card => {
      if (!grouped.has(card.category)) {
        grouped.set(card.category, []);
      }
      grouped.get(card.category)?.push(card);
    });
    return grouped;
  }

  constructor(private router: Router) {}

  toggleCardSelection(card: ModelCard) {
    // Deselect all cards first
    this.modelCards.forEach(c => c.selected = false);
    // Select the clicked card
    card.selected = true;
  }

  continueToDataUpload() {
    const selectedCard = this.modelCards.find(card => card.selected);
    if (selectedCard && (selectedCard.id === 'yolo' || selectedCard.id === 'easyocr')) {
      this.router.navigate(['/upload-data']);
    } else if (selectedCard) {
      alert('Currently, only YOLO and EasyOCR models are supported.');
    }
  }

  get isYoloSelected(): boolean {
    return this.modelCards.some(card => card.selected && (card.id === 'yolo' || card.id === 'easyocr'));
  }
}