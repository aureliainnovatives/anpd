import cv2
import os
from ultralytics import YOLO
import easyocr
from datetime import datetime
import json  # Add this import
from pathlib import Path
from data_sender import DataSender  # Add this import
import sys

def _get_config_path():
    """Get the path to the config.json file."""
    if getattr(sys, 'frozen', False):  # Check if running as a bundled executable
        return os.path.join(sys._MEIPASS, 'config.json')
    else:
        return os.path.join(Path(__file__).resolve().parent.parent, 'config.json')

class LicensePlateDetector:
    def __init__(self, model_path=None):
        # Load config using the new method
        config_path = _get_config_path()
        with open(config_path) as f:
            config = json.load(f)
        
        # Get model path from config
       # model_path = self._get_model_path(config.get('model_path', 'models/NPDv1.0.pt'))  # Use model path from config
        if getattr(sys, 'frozen', False):  # Check if running as a bundled executable
            model_path = os.path.join(sys._MEIPASS, 'NPDv1.0.pt')
        else:
            model_path = os.path.join(Path(__file__).resolve().parent.parent, 'models', 'NPDv1.0.pt')  # Use the model path from the script's directory
        print(f"Using model path: {model_path}")  # Debugging output
        
        # Load detection region config
        self.detection_region = None
        self._load_detection_region()
        
        # Ensure model file exists
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        # Get device from config
        self.device = self._get_device()
        
        # Initialize YOLO model with selected device
        self.model = YOLO(model_path)
        self.model.to(self.device)
        
        # Initialize EasyOCR with GPU if available
        self.reader = easyocr.Reader(['en'], gpu=self.device != 'cpu')
        
        print(f"Using device: {self.device}")
        
        self.class_names = ['license_plate']
        
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
        print(f"Model device: {next(self.model.parameters()).device}")
        
        # Load config using the new method
        config_path = _get_config_path()
        with open(config_path) as f:
            config = json.load(f)
        self.data_sender = DataSender(host=config['host'], port=config['port'])  # Set host and port from config

    def _get_model_path(self, model_name):
        """Get the path to the model file."""
        if getattr(sys, 'frozen', False):  # Check if running as a bundled executable
            return os.path.join(sys._MEIPASS, 'models', model_name)  # Ensure it points to the correct directory
        else:
            return os.path.join(Path(__file__).resolve().parent.parent, 'models', model_name)

    def _get_device(self):
        """Determine the best available device based on config and system capabilities"""
        try:
            import torch
            # Check config first
            with open(os.path.join(Path(__file__).resolve().parent.parent, 'config.json')) as f:
                config = json.load(f)
                preferred_device = config.get('device', 'cuda').lower()
                
                if preferred_device == 'cuda' and torch.cuda.is_available():
                    return 'cuda'
                elif preferred_device == 'mps' and torch.backends.mps.is_available():
                    return 'mps'
                return 'cpu'
        except Exception as e:
            print(f"Error determining device: {e}")
            return 'cpu'

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

    def save_plate(self, plate_image, full_image, plate_text, confidence, x1, y1, x2, y2):
        """Save plate image, full vehicle image and details if not saved or if confidence is higher"""
        if not plate_text or confidence < 0.5:  # Skip low confidence or empty readings
            return False
            
        clean_text = self._clean_plate_number(plate_text)
        
        # Check if we already have this plate with better or equal confidence
        if clean_text in self.saved_plates:
            if confidence <= self.saved_plates[clean_text]:
                return False
        
        # Generate unique identifier using timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_filename = f"{clean_text}_{timestamp}"
        
        # Save files
        plate_img_path = os.path.join(self.output_dir, f"{base_filename}_plate.jpg")    
        vehicle_img_path = os.path.join(self.output_dir, f"{base_filename}_vehicle.jpg")
        txt_path = os.path.join(self.output_dir, f"{base_filename}.txt")
        
        # Save plate image
        cv2.imwrite(plate_img_path, plate_image)
        
        # Save detection area image with detection box
        if self.detection_region:
            # Get detection region coordinates
            frame_height, frame_width = full_image.shape[:2]
            region_x1 = int(self.detection_region['x1'] * frame_width)
            region_y1 = int(self.detection_region['y1'] * frame_height)
            region_x2 = int(self.detection_region['x2'] * frame_width)
            region_y2 = int(self.detection_region['y2'] * frame_height)
            
            # Crop to detection region
            detection_area = full_image[region_y1:region_y2, region_x1:region_x2]
            
            # Draw detection box relative to region
            rel_x1 = x1 - region_x1
            rel_y1 = y1 - region_y1
            rel_x2 = x2 - region_x1
            rel_y2 = y2 - region_y1
            cv2.rectangle(detection_area, (rel_x1, rel_y1), (rel_x2, rel_y2), (0, 255, 0), 2)
            cv2.imwrite(vehicle_img_path, detection_area)
        else:
            # If no detection region, save full frame with box
            vehicle_image = full_image.copy()
            cv2.rectangle(vehicle_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.imwrite(vehicle_img_path, vehicle_image)
        
        # Save text file
        with open(txt_path, 'w') as f:
            f.write(f"Plate Number: {plate_text}\n")
            f.write(f"Confidence: {confidence:.2f}\n")
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Plate Image: {os.path.basename(plate_img_path)}\n")
            f.write(f"Vehicle Image: {os.path.basename(vehicle_img_path)}\n")
            f.write(f"Detection Coordinates: x1={x1}, y1={y1}, x2={x2}, y2={y2}\n")
        
        # Send data to the specified port
        self.data_sender.send_data(vehicle_img_path, plate_img_path, txt_path)
        
        # Update confidence in our tracking dictionary
        self.saved_plates[clean_text] = confidence
        print(f"{'Updated' if clean_text in self.saved_plates else 'Saved new'} plate: {clean_text} (Confidence: {confidence:.2f})")
        return True

    def _load_detection_region(self):
        """Load and validate detection region from config"""
        try:
            # Use the correct config path resolution method
            config_path = _get_config_path()
            with open(config_path) as f:
                config = json.load(f)
                region_config = config.get('detection_region', {})
                if region_config.get('enabled', False):
                    self.detection_region = {
                        'x1': region_config['x1'],
                        'y1': region_config['y1'],
                        'x2': region_config['x2'],
                        'y2': region_config['y2']
                    }
        except Exception as e:
            print(f"Error loading detection region: {e}")
            self.detection_region = None

    def _is_within_region(self, x, y, frame_width, frame_height):
        """Check if coordinates are within detection region"""
        if not self.detection_region:
            return True
            
        # Convert percentage coordinates to pixel values
        x1 = int(self.detection_region['x1'] * frame_width)
        y1 = int(self.detection_region['y1'] * frame_height)
        x2 = int(self.detection_region['x2'] * frame_width)
        y2 = int(self.detection_region['y2'] * frame_height)
        
        return x1 <= x <= x2 and y1 <= y <= y2

    def detect(self, frame):
        # Mark all existing plates as potentially missing
        for key in self.plate_records:
            text, conf, missing = self.plate_records[key]
            self.plate_records[key] = (text, conf, missing + 1)
        
        # Get frame dimensions
        frame_height, frame_width = frame.shape[:2]
        
        # Draw detection region border if enabled
        if self.detection_region:
            # Convert percentage coordinates to pixel values
            x1 = int(self.detection_region['x1'] * frame_width)
            y1 = int(self.detection_region['y1'] * frame_height)
            x2 = int(self.detection_region['x2'] * frame_width)
            y2 = int(self.detection_region['y2'] * frame_height)
            
            # Draw green rectangle around detection region
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        # Run detection
        results = self.model(frame, conf=0.25 , verbose=False)
        
        # Process results
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # Get coordinates
                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                
                # Calculate center for region check
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                
                # Skip if detection is outside region
                if not self._is_within_region(center_x, center_y, frame_width, frame_height):
                    continue
                
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
                        # Try to save the plate and vehicle image
                        self.save_plate(plate_region, frame, text, ocr_conf, x1, y1, x2, y2)
                        
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