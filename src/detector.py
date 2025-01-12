
import cv2
import os
from ultralytics import YOLO
import easyocr
from datetime import datetime
import json  # Add this import
import torch
import platform
import sys
from pathlib import Path


class LicensePlateDetector:
    def __init__(self, model_path=None):
        # If no specific model provided, use the license plate model

        ROOT_DIR = Path(__file__).resolve().parent.parent

        if torch.cuda.is_available():
            device = 'cuda'
        elif platform.system() == 'Darwin' and hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            device = 'mps'  # For Apple Silicon
        else:
            device = 'cpu'
            
        print(f"Using device: {device}")

        config_path = os.path.join(ROOT_DIR, 'config.json')
        with open(config_path) as config_file:
            config = json.load(config_file)
        
        if model_path is None or model_path == "yolov8n.pt":
            # Use absolute path for model
            model_path = os.path.join(ROOT_DIR, config['model_path'])
            
        self.model = YOLO(model_path)
        self.class_names = ['license_plate']
        self.reader = easyocr.Reader(['en'])
        
        # Dictionary to store best plates by location
        self.plate_records = {}  # Format: {location_key: (text, confidence, frames_missing)}
        self.location_threshold = 50  # Pixel distance to consider same plate
        self.max_missing_frames = 10  # Number of frames before removing a plate record
        
        # Create output directory and tracking dictionary
        self.output_dir = "detected_plates"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Dictionary to track saved plates with their confidence scores
        self.saved_plates = {}  # Format: {plate_number: confidence}
        self._load_existing_plates()

    def _load_existing_plates(self):
        """Load existing plate numbers and their confidence from the output directory"""
        for filename in os.listdir(self.output_dir):
            if filename.endswith('.txt'):
                txt_path = os.path.join(self.output_dir, filename)
                try:
                    with open(txt_path, 'r') as f:
                        lines = f.readlines()
                        plate_number = lines[0].split(': ')[1].strip()
                        confidence = float(lines[1].split(': ')[1].strip())
                        self.saved_plates[plate_number] = confidence
                except:
                    continue

    def _clean_plate_number(self, plate_text):
        """Clean and standardize the plate number"""
        cleaned = ''.join(plate_text.split()).upper()
        cleaned = ''.join(c for c in cleaned if c.isalnum())
        return cleaned

    def get_location_key(self, x, y):
        """Generate a location key for a given x,y coordinate"""
        return f"{x//self.location_threshold}_{y//self.location_threshold}"

    def read_plate(self, plate_image, location_key):
        """Perform OCR on the plate image"""
        try:
            results = self.reader.readtext(plate_image)
            if results:
                # Get the text with highest confidence
                best_result = max(results, key=lambda x: x[2])
                text = best_result[1]
                confidence = best_result[2]
                
                # Update plate records
                if location_key in self.plate_records:
                    old_text, old_conf, _ = self.plate_records[location_key]
                    if old_conf > confidence:
                        text, confidence = old_text, old_conf
                
                self.plate_records[location_key] = (text, confidence, 0)
                return text, confidence
                
        except Exception as e:
            print(f"OCR Error: {e}")
        return None, 0.0

    def save_plate(self, plate_image, plate_text, confidence):
        """Save plate image and details if not saved or if confidence is higher"""
        if not plate_text or confidence < 0.5:  # Skip low confidence or empty readings
            return False
            
        clean_text = self._clean_plate_number(plate_text)
        
        # Check if we already have this plate with better or equal confidence
        if clean_text in self.saved_plates:
            if confidence <= self.saved_plates[clean_text]:
                return False
        
        # Save or update files
        img_filename = f"{clean_text}.jpg"
        txt_filename = f"{clean_text}.txt"
        img_path = os.path.join(self.output_dir, img_filename)
        txt_path = os.path.join(self.output_dir, txt_filename)
        
        # Save files
        cv2.imwrite(img_path, plate_image)
        with open(txt_path, 'w') as f:
            f.write(f"Plate Number: {plate_text}\n")
            f.write(f"Confidence: {confidence:.2f}\n")
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Update confidence in our tracking dictionary
        self.saved_plates[clean_text] = confidence
        print(f"{'Updated' if clean_text in self.saved_plates else 'Saved new'} plate: {clean_text} (Confidence: {confidence:.2f})")
        return True

    def detect(self, frame):
        # Mark all existing plates as potentially missing
        for key in self.plate_records:
            text, conf, missing = self.plate_records[key]
            self.plate_records[key] = (text, conf, missing + 1)
        
        # Run detection
        results = self.model(frame, conf=0.25)
        
        # Process results
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # Get coordinates
                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                
                # Get confidence
                conf = float(box.conf[0])
                
                # Calculate center for location tracking
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                location_key = self.get_location_key(center_x, center_y)
                
                # Draw rectangle around license plate
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                # Extract license plate region
                plate_region = frame[y1:y2, x1:x2]
                
                # Create label
                label = f'License Plate {conf:.2f}'
                
                # Draw label background
                text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)[0]
                cv2.rectangle(frame, 
                            (x1, y1 - text_size[1] - 10), 
                            (x1 + text_size[0], y1), 
                            (0, 255, 0), 
                            -1)
                
                # Draw label text
                cv2.putText(frame, 
                           label, 
                           (x1, y1 - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 
                           0.9, 
                           (0, 0, 0), 
                           2)
                
                # Perform OCR if plate region exists
                if plate_region.size > 0:
                    text, ocr_conf = self.read_plate(plate_region, location_key)
                    if text:
                        # Try to save the plate
                        self.save_plate(plate_region, text, ocr_conf)
                        
                        # Display the text on frame
                        plate_text = f"Plate: {text} (Conf: {ocr_conf:.2f})"
                        cv2.putText(frame, plate_text, (x1, y2 + 25),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        # Remove plates that have been missing for too many frames
        keys_to_remove = [
            key for key, (_, _, missing) in self.plate_records.items()
            if missing > self.max_missing_frames
        ]
        for key in keys_to_remove:
            del self.plate_records[key]

        return frame