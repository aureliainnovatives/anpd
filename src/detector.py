import cv2
import os
from ultralytics import YOLO
import easyocr
from datetime import datetime
import json  # Add this import
from pathlib import Path
from data_sender import DataSender  # Add this import
import sys
from utils.logger import setup_logger
import urllib.request
import socket
import ssl
import numpy as np
import time

def _get_config_path():
    """Get the path to the config.json file."""
    if getattr(sys, 'frozen', False):  # Check if running as a bundled executable
        return os.path.join(sys._MEIPASS, 'config.json')
    else:
        return os.path.join(Path(__file__).resolve().parent.parent, 'config.json')

class LicensePlateDetector:
    def __init__(self, model_path=None):
        # Initialize logger
        self.logger = setup_logger('LicensePlateDetector')
        self.logger.info("Initializing License Plate Detector")
        
        try:
            # Load config using the new method
            config_path = _get_config_path()
            self.logger.debug(f"Loading config from: {config_path}")
            with open(config_path) as f:
                self.config = json.load(f)  # Store config as instance variable
            
            # Get model path from config
            if getattr(sys, 'frozen', False):
                model_path = os.path.join(sys._MEIPASS, 'NPDv1.0.pt')
            else:
                model_path = os.path.join(Path(__file__).resolve().parent.parent, 'models', 'NPDv1.0.pt')
            self.logger.info(f"Using model path: {model_path}")
            
            # Load detection region config
            self.detection_region = None
            self._load_detection_region()
            
            # Ensure model file exists
            if not os.path.exists(model_path):
                self.logger.error(f"Model file not found: {model_path}")
                raise FileNotFoundError(f"Model file not found: {model_path}")
            
            # Get device from config
            self.device = self._get_device()
            self.logger.info(f"Using device: {self.device}")
            
            # Initialize YOLO model with selected device
            try:
                self.logger.debug("Initializing YOLO model")
                self.model = YOLO(model_path)
                self.model.to(self.device)
            except Exception as e:
                self.logger.error(f"Error initializing YOLO model: {str(e)}")
                raise
            
            # Initialize EasyOCR with error handling
            try:
                self.logger.debug("Initializing EasyOCR in offline mode")
                
                # Get the EasyOCR model directory path
                if getattr(sys, 'frozen', False):
                    # If running as exe
                    easyocr_path = os.path.join(sys._MEIPASS, 'EasyOCR-1.7.2')
                    model_storage_directory = os.path.join(sys._MEIPASS, 'easyocr_models')
                else:
                    # If running as script
                    easyocr_path = os.path.join(Path(__file__).resolve().parent.parent, 'EasyOCR-1.7.2')
                    model_storage_directory = os.path.join(Path(__file__).resolve().parent.parent, 'easyocr_models')
                
                # Verify model files exist
                required_files = ['craft_mlt_25k.pth', 'english_g2.pth']
                for file in required_files:
                    file_path = os.path.join(model_storage_directory, file)
                    if not os.path.exists(file_path):
                        raise FileNotFoundError(f"Required model file not found: {file_path}")
                
                # Initialize EasyOCR with offline settings
                self.reader = easyocr.Reader(
                    ['en'],
                    gpu=self.device != 'cpu',
                    model_storage_directory=model_storage_directory,
                    download_enabled=False  # Disable online model download
                )
                
                self.logger.info("EasyOCR initialized successfully in offline mode")
            
            except Exception as e:
                self.logger.error(f"Error initializing EasyOCR: {str(e)}")
                if isinstance(e, RuntimeError) and "CUDA" in str(e):
                    self.logger.error("CUDA error detected in EasyOCR - may need to check GPU memory or CUDA configuration")
                elif isinstance(e, FileNotFoundError):
                    self.logger.error(f"Model file not found. Please run prepare_models.py first")
                raise
            
            # Rest of initialization...
            self.logger.info("License Plate Detector initialized successfully")
            
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
            
            # Dictionary to store data senders for each stream
            self.data_senders = {}
            
            # Initialize data senders for each stream
            for stream in self.config.get('streams', []):
                if stream.get('enabled') and 'data_sender' in stream:
                    stream_id = stream['id']
                    sender_config = stream['data_sender']
                    self.data_senders[stream_id] = DataSender(
                        host=sender_config['host'],
                        port=sender_config['port']
                    )
                    self.logger.info(f"Initialized data sender for stream {stream_id}: {sender_config['host']}:{sender_config['port']}")

        except Exception as e:
            self.logger.error(f"Failed to initialize License Plate Detector: {str(e)}")
            raise

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
            config_path = _get_config_path()
            with open(config_path) as f:
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
            self.logger.debug(f"Starting OCR for location {location_key}")
            self.logger.debug(f"Plate image shape: {plate_image.shape}")
            
            # Get OCR logging settings from config
            config_path = _get_config_path()
            with open(config_path) as f:
                config = json.load(f)
            ocr_logging = config.get('ocr_settings', {}).get('logging', {})
            
            # Log image details if debug is enabled
            if ocr_logging.get('include_image_debug', False):
                mean_brightness = np.mean(plate_image)
                std_brightness = np.std(plate_image)
                self.logger.debug(f"Image statistics - Mean brightness: {mean_brightness:.2f}, Std: {std_brightness:.2f}")
            
            # Time the OCR operation
            start_time = time.time()
            results = self.reader.readtext(plate_image)
            ocr_time = time.time() - start_time
            
            self.logger.debug(f"OCR completed in {ocr_time:.3f} seconds")
            self.logger.debug(f"Raw OCR results: {results}")
            
            if results:
                # Get the text with highest confidence
                best_result = max(results, key=lambda x: x[2])
                text = best_result[1]
                confidence = best_result[2]
                
                # Log all results above threshold
                log_threshold = ocr_logging.get('log_confidence_threshold', 0.3)
                for bbox, txt, conf in results:
                    if conf >= log_threshold:
                        self.logger.info(f"OCR Result - Text: {txt}, Confidence: {conf:.3f}, Bbox: {bbox}")
                
                # Update plate records
                if location_key in self.plate_records:
                    old_text, old_conf, _ = self.plate_records[location_key]
                    if old_conf > confidence:
                        self.logger.debug(f"Keeping previous better result: {old_text} ({old_conf:.3f}) vs new: {text} ({confidence:.3f})")
                        text, confidence = old_text, old_conf
                    else:
                        self.logger.debug(f"Using new better result: {text} ({confidence:.3f}) vs old: {old_text} ({old_conf:.3f})")
                
                self.plate_records[location_key] = (text, confidence, 0)
                self.logger.info(f"Final OCR result - Location: {location_key}, Text: {text}, Confidence: {confidence:.3f}")
                return text, confidence
            else:
                self.logger.warning(f"No text detected in plate image at location {location_key}")
                
        except Exception as e:
            self.logger.error(f"OCR Error: {str(e)}", exc_info=True)
            if isinstance(e, RuntimeError) and "CUDA" in str(e):
                self.logger.error("CUDA error detected in EasyOCR - may need to check GPU memory or CUDA configuration")
            elif "model file" in str(e).lower():
                self.logger.error("Error loading EasyOCR model files - check if model files exist in the correct location")
        return None, 0.0

    def save_plate(self, plate_image, full_image, plate_text, confidence, x1, y1, x2, y2, stream_id=None):
        """Save plate image, full vehicle image and details if not saved or if confidence is higher"""
        if not plate_text or confidence < 0.5:  # Skip low confidence or empty readings
            return False
            
        try:
            clean_text = self._clean_plate_number(plate_text)
            
            # Create stream-specific directory
            if stream_id:
                stream_dir = os.path.join(self.output_dir, stream_id)
                os.makedirs(stream_dir, exist_ok=True)
                
                # Create plate-specific directory within stream directory
                plate_dir = os.path.join(stream_dir, clean_text)
                os.makedirs(plate_dir, exist_ok=True)
            else:
                plate_dir = self.output_dir
            
            # Generate unique identifier using timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Save files in plate-specific directory
            plate_img_path = os.path.join(plate_dir, f"{timestamp}_plate.jpg")    
            vehicle_img_path = os.path.join(plate_dir, f"{timestamp}_vehicle.jpg")
            txt_path = os.path.join(plate_dir, f"{timestamp}.txt")
            
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
            
            # Get or create data sender for this stream
            if stream_id:
                self.logger.debug(f"Processing data for stream {stream_id}")
                if stream_id in self.data_senders:
                    self.logger.info(f"Sending data for stream {stream_id}")
                    try:
                        self.data_senders[stream_id].send_data(vehicle_img_path, plate_img_path, txt_path)
                        self.logger.info(f"Successfully sent data for stream {stream_id}")
                    except Exception as e:
                        self.logger.error(f"Failed to send data for stream {stream_id}: {str(e)}")
                else:
                    self.logger.warning(f"No data sender found for stream {stream_id}")
                    # Try to create data sender if it doesn't exist
                    stream_config = next((s for s in self.config.get('streams', []) if s['id'] == stream_id), None)
                    if stream_config and 'data_sender' in stream_config:
                        sender_config = stream_config['data_sender']
                        self.data_senders[stream_id] = DataSender(
                            host=sender_config['host'],
                            port=sender_config['port']
                        )
                        self.logger.info(f"Created new data sender for stream {stream_id}")
                        # Try sending with new sender
                        self.data_senders[stream_id].send_data(vehicle_img_path, plate_img_path, txt_path)
            else:
                self.logger.warning("No stream_id provided for data sending")
            
            # Update confidence in our tracking dictionary
            self.saved_plates[clean_text] = confidence
            self.logger.info(f"{'Updated' if clean_text in self.saved_plates else 'Saved new'} plate: {clean_text} (Confidence: {confidence:.2f})")
            return True
            
        except Exception as e:
            self.logger.error(f"Error in save_plate: {str(e)}")
            return False

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

    def detect(self, frame, detection_region=None, stream_id=None):
        """
        Detect license plates in the frame
        Args:
            frame: The input frame
            detection_region: Dictionary containing detection region parameters
            stream_id: ID of the stream being processed
        """
        # Make a copy of the frame for drawing
        display_frame = frame.copy()
        
        # Get frame dimensions
        frame_height, frame_width = frame.shape[:2]
        
        # Use provided detection region or fallback to default
        current_detection_region = detection_region or self.detection_region
        
        # Draw and apply detection region if enabled
        if current_detection_region and current_detection_region.get('enabled', True):
            try:
                # Convert percentage coordinates to pixel values
                x1 = int(current_detection_region['x1'] * frame_width)
                y1 = int(current_detection_region['y1'] * frame_height)
                x2 = int(current_detection_region['x2'] * frame_width)
                y2 = int(current_detection_region['y2'] * frame_height)
                
                # Ensure x2 > x1 and y2 > y1
                if x2 <= x1:
                    x1, x2 = x2, x1
                if y2 <= y1:
                    y1, y2 = y2, y1
                
                # Draw the complete rectangle with individual lines to ensure all sides are visible
                # Top line
                cv2.line(display_frame, (x1, y1), (x2, y1), (0, 255, 0), 2)
                # Right line
                cv2.line(display_frame, (x2, y1), (x2, y2), (0, 255, 0), 2)
                # Bottom line
                cv2.line(display_frame, (x2, y2), (x1, y2), (0, 255, 0), 2)
                # Left line
                cv2.line(display_frame, (x1, y2), (x1, y1), (0, 255, 0), 2)
                
                # Create mask for detection region
                mask = np.zeros(frame.shape[:2], dtype=np.uint8)
                cv2.rectangle(mask, (x1, y1), (x2, y2), 255, -1)
                
                # Apply mask to frame for detection
                detection_frame = cv2.bitwise_and(frame, frame, mask=mask)
                
            except Exception as e:
                self.logger.error(f"Error applying detection region: {str(e)}")
                detection_frame = frame
        else:
            detection_frame = frame
        
        # Run detection
        results = self.model(detection_frame, conf=0.25, verbose=False)
        
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
                if current_detection_region and current_detection_region.get('enabled', True):
                    region_x1 = int(current_detection_region['x1'] * frame_width)
                    region_y1 = int(current_detection_region['y1'] * frame_height)
                    region_x2 = int(current_detection_region['x2'] * frame_width)
                    region_y2 = int(current_detection_region['y2'] * frame_height)
                    
                    if not (region_x1 <= center_x <= region_x2 and region_y1 <= center_y <= region_y2):
                        continue
                
                # Draw detection rectangle on the display frame
                cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                # Extract license plate region
                plate_region = frame[y1:y2, x1:x2]
                
                # Create label
                label = f'License Plate {box.conf[0]:.2f}'
                
                # Draw label background
                text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)[0]
                cv2.rectangle(display_frame, 
                            (x1, y1 - text_size[1] - 10), 
                            (x1 + text_size[0], y1), 
                            (0, 255, 0), 
                            -1)
                
                # Draw label text
                cv2.putText(display_frame, 
                           label, 
                           (x1, y1 - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 
                           0.9, 
                           (0, 0, 0), 
                           2)
                
                # Perform OCR if plate region exists
                if plate_region.size > 0:
                    text, ocr_conf = self.read_plate(plate_region, self.get_location_key(center_x, center_y))
                    if text:
                        # Try to save the plate and vehicle image - pass stream_id here
                        self.save_plate(plate_region, frame, text, ocr_conf, x1, y1, x2, y2, stream_id=stream_id)
                        
                        # Display the text on frame
                        plate_text = f"Plate: {text} (Conf: {ocr_conf:.2f})"
                        cv2.putText(display_frame, plate_text, (x1, y2 + 25),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        # Remove plates that have been missing for too many frames
        keys_to_remove = [
            key for key, (_, _, missing) in self.plate_records.items()
            if missing > self.max_missing_frames
        ]
        for key in keys_to_remove:
            del self.plate_records[key]

        return display_frame