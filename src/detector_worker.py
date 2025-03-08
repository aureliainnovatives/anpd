from PyQt6.QtCore import QThread, pyqtSignal
from ui.rtsp_handler import RTSPHandler
from queue import Queue, Empty
from threading import Thread
import time
import json
import os
from data_sender import DataSender
import sys
from pathlib import Path

class DetectionWorker(QThread):
    frame_ready = pyqtSignal(object)
    error = pyqtSignal(str)
    status_changed = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, detector, video_source, stream_config, is_camera=False):
        super().__init__()
        self.detector = detector
        self.video_source = video_source
        self.stream_config = stream_config
        self.stream_id = stream_config['id']
        self.is_camera = is_camera
        self.running = False
        self.rtsp_handler = RTSPHandler()
        
        # Load config
        self.config = self._load_config()
        
        # Configure frame buffer
        self.frame_queue = Queue(maxsize=self.config.get('video_settings', {}).get('max_queue_size', 16))
        self.capture_thread = None
        self.process_thread = None
        self.frame_time = 1/self.config.get('video_settings', {}).get('target_fps', 30)

    def _get_config_path(self):
        """Get the path to the config.json file."""
        if getattr(sys, 'frozen', False):
            # If running as exe, get config from exe directory
            return os.path.join(os.path.dirname(sys.executable), 'config.json')
        else:
            # Development mode
            return os.path.join(Path(__file__).resolve().parent.parent, 'config.json')

    def _load_config(self):
        """Load the configuration file."""
        try:
            config_path = self._get_config_path()
            
            with open(config_path, 'r') as file:
                return json.load(file)
        except Exception as e:
            print(f"Error loading config: {e}")
            return {
                'video_settings': {
                    'max_queue_size': 16,
                    'target_fps': 30,
                    'playback_speed': 1.0
                }
            }

    def _capture_frames(self):
        consecutive_errors = 0
        max_consecutive_errors = 5
        reconnect_delay = 2.0
        
        while self.running:
            try:
                if not self.rtsp_handler.is_opened():
                    self.status_changed.emit("Connecting...")
                    self.error.emit(f"Connection lost. Attempting to reconnect...")
                    if self.rtsp_handler.connect(self.video_source):
                        consecutive_errors = 0
                        self.status_changed.emit("Running")
                        continue
                    else:
                        time.sleep(reconnect_delay)
                        consecutive_errors += 1
                        if consecutive_errors >= max_consecutive_errors:
                            self.status_changed.emit("Error: Connection Failed")
                            self.error.emit("Failed to reconnect after multiple attempts")
                            break
                        continue

                ret, frame = self.rtsp_handler.read_frame()
                if not ret:
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        self.status_changed.emit("Error: No Frames")
                        self.error.emit("Failed to read frames from stream")
                        self.rtsp_handler.disconnect()
                        time.sleep(reconnect_delay)
                        if not self.rtsp_handler.connect(self.video_source):
                            self.status_changed.emit("Error: Reconnection Failed")
                            self.error.emit("Failed to reconnect to stream")
                            break
                        continue
                
                consecutive_errors = 0  # Reset error counter on success
                self.status_changed.emit("Running")
                
                if not self.frame_queue.full():
                    self.frame_queue.put(frame)
                    
            except Exception as e:
                consecutive_errors += 1
                self.error.emit(f"Capture error: {str(e)}")
                self.status_changed.emit(f"Error: {str(e)}")
                if consecutive_errors >= max_consecutive_errors:
                    self.error.emit("Too many consecutive errors, attempting to reconnect...")
                    try:
                        self.rtsp_handler.disconnect()
                        time.sleep(reconnect_delay)
                        if not self.rtsp_handler.connect(self.video_source):
                            self.error.emit("Failed to reconnect after errors")
                            break
                    except Exception as reconnect_error:
                        self.error.emit(f"Reconnection failed: {str(reconnect_error)}")
                        break
                time.sleep(1)

    def _process_frames(self):
        while self.running:
            try:
                frame = self.frame_queue.get(timeout=1.0)
                try:
                    frame_with_detection = self.detector.detect(
                        frame, 
                        detection_region=self.stream_config.get('detection_region'),
                        stream_id=self.stream_id
                    )
                    self.frame_ready.emit(frame_with_detection)
                except Exception as e:
                    self.error.emit(f"Detection error: {str(e)}")
            except Empty:
                continue
            except Exception as e:
                self.error.emit(f"Processing error: {str(e)}")

    def run(self):
        self.running = True
        rtsp_connected = False
        max_retries = 3
        retry_delay = 2.0
        
        for attempt in range(max_retries):
            try:
                self.status_changed.emit("Connecting...")
                
                # Connect to RTSP stream
                if not self.rtsp_handler or not self.rtsp_handler.connect(self.video_source):
                    if attempt < max_retries - 1:
                        self.status_changed.emit(f"Retrying ({attempt + 1}/{max_retries})")
                        self.error.emit(f"Failed to connect to video source, retrying... ({attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                        continue
                    else:
                        self.status_changed.emit("Error: Connection Failed")
                        self.error.emit(f"Failed to connect to video source after {max_retries} attempts")
                        return
                
                rtsp_connected = True
                self.status_changed.emit("Running")
                self.error.emit("Successfully connected to stream")

                # Start threads
                self.capture_thread = Thread(target=self._capture_frames, daemon=True)
                self.process_thread = Thread(target=self._process_frames, daemon=True)
                
                self.capture_thread.start()
                self.process_thread.start()

                # Monitor threads with improved error handling
                while self.running:
                    if not self.capture_thread.is_alive():
                        if self.running:  # Only try to reconnect if we haven't been stopped
                            self.error.emit("Capture thread stopped, attempting to restart...")
                            self.rtsp_handler.disconnect()
                            if self.rtsp_handler.connect(self.video_source):
                                self.capture_thread = Thread(target=self._capture_frames, daemon=True)
                                self.capture_thread.start()
                            else:
                                self.error.emit("Failed to restart capture thread")
                                break
                    if not self.process_thread.is_alive():
                        self.error.emit("Processing thread stopped unexpectedly")
                        break
                    time.sleep(1.0)  # Longer sleep to reduce CPU usage

                break  # Exit retry loop if we got here

            except Exception as e:
                self.error.emit(f"Worker error: {str(e)}")
                self.status_changed.emit(f"Error: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    break
            finally:
                if not self.running:
                    break

        # Cleanup
        self.running = False
        try:
            if rtsp_connected and self.rtsp_handler:
                self.rtsp_handler.disconnect()
        except Exception as e:
            print(f"Error disconnecting RTSP handler: {str(e)}")
        self.finished.emit()

    def stop(self):
        """Stop the worker and cleanup resources"""
        if not self.running:
            return
        
        try:
            # Signal threads to stop
            self.running = False
            
            # Clear the frame queue to unblock any waiting threads
            if self.frame_queue:
                try:
                    while not self.frame_queue.empty():
                        try:
                            self.frame_queue.get_nowait()
                        except:
                            break
                except:
                    pass
            
            # Wait for threads to finish with timeout
            if self.capture_thread and self.capture_thread.is_alive():
                self.capture_thread.join(timeout=0.5)
            
            if self.process_thread and self.process_thread.is_alive():
                self.process_thread.join(timeout=0.5)
            
            # Disconnect RTSP handler
            if self.rtsp_handler:
                try:
                    self.rtsp_handler.disconnect()
                except Exception as e:
                    print(f"Error disconnecting RTSP handler: {str(e)}")
                self.rtsp_handler = None
            
            # Clear references
            self.capture_thread = None
            self.process_thread = None
            self.frame_queue = None
            
        except Exception as e:
            print(f"Error stopping worker: {str(e)}")
        finally:
            # Ensure wait is called with timeout
            self.wait(1000)  # 1 second timeout

    def update_config(self, new_config):
        """Update worker configuration without restart"""
        try:
            self.stream_config = new_config
            
            # Update detection region immediately
            if self.detector:
                # Update any detector-specific settings
                if 'detection_region' in new_config:
                    self.detector.detection_region = new_config['detection_region']
                
            # Update data sender configuration if changed
            if 'data_sender' in new_config:
                sender_config = new_config['data_sender']
                if hasattr(self.detector, 'data_senders') and self.stream_id in self.detector.data_senders:
                    self.detector.data_senders[self.stream_id] = DataSender(
                        host=sender_config['host'],
                        port=sender_config['port']
                    )
                
        except Exception as e:
            self.error.emit(f"Error updating configuration: {str(e)}")
