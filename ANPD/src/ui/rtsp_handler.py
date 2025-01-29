import cv2
import time
import logging
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from collections import deque
from datetime import datetime
import os
import sys
import json
from pathlib import Path

class RTSPHandler:
    def __init__(self):
        self.cap = None
        self.frame_queue = deque(maxlen=30)
        self.last_valid_frame = None
        self.last_valid_timestamp = None
        self.error_count = 0
        self.max_error_count = 10
        self.logger = self._setup_logger()
        self.last_url = None
        
        # Load config
        self.config = self._load_config()

    def _setup_logger(self):
        logger = logging.getLogger('RTSPHandler')
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def _get_config_path(self):
        """Get the path to the config.json file."""
        if getattr(sys, 'frozen', False):  # Check if running as a bundled executable
            return os.path.join(sys._MEIPASS, 'config.json')
        else:
            return os.path.join(Path(__file__).resolve().parent.parent.parent, 'config.json')

    def _load_config(self):
        """Load the configuration file."""
        config_path = self._get_config_path()
        try:
            with open(config_path, 'r') as file:
                return json.load(file)
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}

    def connect(self, url, protocol=None):
        max_retries = 3
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                self.last_url = url
                # Configure RTSP with optimized parameters
                if 'rtsp://' in url:
                    parsed = urlparse(url)
                    query = parse_qs(parsed.query)
                    query['rtsp_transport'] = 'tcp'
                    query['buffer_size'] = '1048576'  # 1MB buffer
                    query['fflags'] = 'nobuffer'
                    query['flags'] = 'low_delay'
                    query['max_delay'] = '1000000'  # 1 second
                    query['reorder_queue_size'] = '1000000'  # Handle packet reordering
                    query['discardcorrupt'] = '1'  # Discard corrupted frames
                    query['skip_frame'] = 'nokey'  # Skip non-key frames if needed
                    query['analyzeduration'] = '1000000'  # Analyze stream duration
                    query['probesize'] = '1000000'  # Set probe size
                    url = urlunparse(parsed._replace(query=urlencode(query, doseq=True)))
                
                # Configure video capture with hardware acceleration
                self.cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
                
                # Log hardware acceleration status
                hw_accel = self.cap.get(cv2.CAP_PROP_HW_ACCELERATION)
                self.logger.info(f"Hardware acceleration status: {hw_accel} ({'enabled' if hw_accel > 0 else 'disabled'})")
                
                # Enable hardware acceleration if supported
                try:
                    if hasattr(cv2, 'VIDEO_ACCELERATION_ANY'):
                        self.cap.set(cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_ANY)
                        self.cap.set(cv2.CAP_PROP_HW_DEVICE, 0)  # Use first GPU
                    else:
                        self.logger.warning("Hardware acceleration not supported in this OpenCV version")
                except Exception as e:
                    self.logger.warning(f"Could not configure hardware acceleration: {str(e)}")
                
                # Configure H264 decoder with optimized parameters
                try:
                    if hasattr(cv2, 'VideoWriter_fourcc'):
                        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'H264'))
                    else:
                        self.logger.warning("VideoWriter_fourcc not available, using default codec")
                    
                    self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 10)  # Larger buffer for stability
                    self.cap.set(cv2.CAP_PROP_FPS, 30)
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
                except Exception as e:
                    self.logger.warning(f"Could not configure H264 decoder: {str(e)}")
                
                # Additional codec parameters for better error resilience
                try:
                    # Only set pixel format if supported
                    if hasattr(cv2, 'VIDEOIO_PIXEL_FMT_YUV420P'):
                        self.cap.set(cv2.CAP_PROP_CODEC_PIXEL_FORMAT, cv2.VIDEOIO_PIXEL_FMT_YUV420P)
                    else:
                        self.logger.warning("YUV420P pixel format not supported")
                    
                    # Set video channels if supported
                    if hasattr(cv2, 'CAP_PROP_VIDEO_TOTAL_CHANNELS'):
                        self.cap.set(cv2.CAP_PROP_VIDEO_TOTAL_CHANNELS, 3)
                    
                    # Set video stream if supported
                    if hasattr(cv2, 'CAP_PROP_VIDEO_STREAM'):
                        self.cap.set(cv2.CAP_PROP_VIDEO_STREAM, 0)
                    
                    # Set error resilience parameters if supported
                    if hasattr(cv2, 'CAP_PROP_ERROR_RESILIENCE'):
                        self.cap.set(cv2.CAP_PROP_ERROR_RESILIENCE, 1)
                    
                    # Set skip frame parameters if supported
                    if hasattr(cv2, 'CAP_PROP_SKIP_FRAME'):
                        self.cap.set(cv2.CAP_PROP_SKIP_FRAME, 0)  # Don't skip frames
                except Exception as e:
                    self.logger.warning(f"Could not set advanced codec parameters: {str(e)}")
                    self.logger.debug("Falling back to default codec settings")
                
                if not self.cap.isOpened():
                    # Fallback to default settings if initial setup fails
                    self.cap = cv2.VideoCapture(url)
                    self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)
                    
                if not self.cap.isOpened():
                    self.logger.error(f"Failed to open video capture (attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    continue
                
                # Verify initial frame read
                ret, frame = self.cap.read()
                if not ret or not self._validate_frame(frame):
                    self.logger.error(f"Failed to read initial frame (attempt {attempt + 1}/{max_retries})")
                    self.disconnect()
                    time.sleep(retry_delay)
                    continue
                
                return True
                
            except Exception as e:
                self.logger.error(f"Connection error (attempt {attempt + 1}/{max_retries}): {str(e)}")
                self.disconnect()
                time.sleep(retry_delay)
                continue
                
        self.logger.error(f"Failed to connect after {max_retries} attempts")
        return False

    def _validate_frame(self, frame):
        if frame is None:
            self.logger.debug("Frame is None")
            return False
            
        try:
            # Basic shape validation
            height, width = frame.shape[:2]
            if height <= 0 or width <= 0 or frame.size <= 0:
                self.logger.debug(f"Invalid frame dimensions: {height}x{width}")
                return False
                
            # Check for corrupted H264 frames
            try:
                # Validate frame data using mean and standard deviation
                mean, stddev = cv2.meanStdDev(frame)
                if any(v < 0 or v > 255 for v in mean):
                    self.logger.debug(f"Invalid mean values: {mean}")
                    return False
                    
                # Check for completely black or white frames
                if all(v < 10 for v in mean) or all(v > 245 for v in mean):
                    self.logger.debug(f"Potential corrupted frame: uniform color detected")
                    return False
                    
                # Check for low standard deviation (potential frozen frame)
                if all(v < 1.0 for v in stddev):
                    self.logger.debug(f"Potential frozen frame: low stddev {stddev}")
                    return False
            except Exception as e:
                self.logger.debug(f"Frame statistics check failed: {str(e)}")
                return False
                
            # Check for frame drops by comparing timestamps
            if self.last_valid_timestamp:
                current_time = datetime.now()
                time_diff = (current_time - self.last_valid_timestamp).total_seconds()
                if time_diff > 2 * (1/30):  # More than 2 frame intervals
                    self.logger.warning(f"Possible frame drop detected: {time_diff:.3f}s since last frame")
                    
            # Additional H264-specific validation
            try:
                # Check for corrupted frame headers
                if not cv2.imencode('.jpg', frame)[0]:
                    self.logger.debug("Failed to encode frame to JPEG")
                    return False
            except Exception as e:
                self.logger.debug(f"Frame encoding check failed: {str(e)}")
                return False
                
            return True
        except Exception as e:
            self.logger.warning(f"Frame validation error: {str(e)}")
            return False

    def read_frame(self):
        if not self.cap or not self.cap.isOpened():
            self.logger.warning("Video capture not initialized")
            return False, None
            
        # Check if we have a cached valid frame
        if self.error_count > 0 and self.last_valid_frame is not None:
            self.logger.debug("Returning cached frame due to recent errors")
            return True, self.last_valid_frame
            
        max_retries = 5
        retry_delay = 0.1
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Attempt to grab frame with timeout
                ret = self.cap.grab()
                if not ret:
                    last_error = "Failed to grab frame from capture"
                    self.error_count += 1
                    if self.error_count > 3:
                        self.logger.warning("Attempting to reset video capture")
                        self.disconnect()
                        self.connect(self.last_url)
                    time.sleep(retry_delay * (2 ** attempt))
                    continue
                
                # Retrieve the grabbed frame
                ret, frame = self.cap.retrieve()
                if not ret:
                    last_error = "Failed to retrieve frame from capture"
                    self.error_count += 1
                    time.sleep(retry_delay * (2 ** attempt))
                    continue
                
                # Validate the frame
                if not self._validate_frame(frame):
                    last_error = "Invalid frame data"
                    self.error_count += 1
                    # Return last valid frame if available
                    if self.last_valid_frame is not None:
                        return True, self.last_valid_frame
                    time.sleep(retry_delay * (2 ** attempt))
                    continue
                
                # Frame is valid, update state
                timestamp = datetime.now()
                self.frame_queue.append((frame, timestamp))
                self.last_valid_frame = frame
                self.last_valid_timestamp = timestamp
                self.error_count = 0
                
                # Check for frame synchronization issues
                if len(self.frame_queue) > 1:
                    prev_timestamp = self.frame_queue[-2][1]
                    frame_interval = (timestamp - prev_timestamp).total_seconds()
                    expected_interval = 1.0 / self.cap.get(cv2.CAP_PROP_FPS)
                    if abs(frame_interval - expected_interval) > expected_interval * 0.5:
                        self.logger.warning(f"Frame synchronization issue detected: interval {frame_interval:.3f}s (expected {expected_interval:.3f}s)")
                
                return True, frame
                
            except Exception as e:
                last_error = str(e)
                self.logger.error(f"Frame read error: {last_error}")
                self.error_count += 1
                if self.error_count >= self.max_error_count:
                    self.logger.error("Max error count reached, stopping capture")
                    self.disconnect()
                    return False, None
                time.sleep(retry_delay * (2 ** attempt))
                continue
                
        self.logger.warning(f"Failed to read frame after {max_retries} attempts: {last_error}")
        return False, None

    def disconnect(self):
        if self.cap:
            self.cap.release()

    def is_opened(self):
        return self.cap is not None and self.cap.isOpened()
