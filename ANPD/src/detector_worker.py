from PyQt6.QtCore import QThread, pyqtSignal
from ui.rtsp_handler import RTSPHandler
from queue import Queue, Empty
from threading import Thread
import time
import json
import os

class DetectionWorker(QThread):
    frame_ready = pyqtSignal(object)
    error = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, detector, video_source, is_camera=False):
        super().__init__()
        self.detector = detector
        self.video_source = video_source
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

    def _load_config(self):
        try:
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
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
        last_frame_time = time.time()
        
        while self.running:
            try:
                # Maintain frame rate
                current_time = time.time()
                elapsed = current_time - last_frame_time
                if elapsed < self.frame_time:
                    time.sleep(max(0, self.frame_time - elapsed))
                last_frame_time = time.time()

                # Read frame
                ret, frame = self.rtsp_handler.read_frame()
                if not ret:
                    if not self.is_camera:
                        self.running = False
                        break
                    continue

                # Add frame to queue
                if not self.frame_queue.full():
                    self.frame_queue.put(frame)
                
            except Exception as e:
                self.error.emit(f"Capture error: {str(e)}")
                time.sleep(1)
                continue

    def _process_frames(self):
        while self.running:
            try:
                frame = self.frame_queue.get(timeout=1.0)
                try:
                    frame_with_detection = self.detector.detect(frame)
                    self.frame_ready.emit(frame_with_detection)
                except Exception as e:
                    self.error.emit(f"Detection error: {str(e)}")
            except Empty:
                continue
            except Exception as e:
                self.error.emit(f"Processing error: {str(e)}")

    def run(self):
        self.running = True
        
        # Connect to RTSP stream
        if not self.rtsp_handler.connect(self.video_source):
            self.error.emit("Failed to connect to video source")
            return

        # Start threads
        self.capture_thread = Thread(target=self._capture_frames, daemon=True)
        self.process_thread = Thread(target=self._process_frames, daemon=True)
        
        self.capture_thread.start()
        self.process_thread.start()

        # Monitor threads
        while self.running:
            if not self.capture_thread.is_alive() or not self.process_thread.is_alive():
                break
            time.sleep(0.1)

        self.rtsp_handler.disconnect()
        self.finished.emit()

    def stop(self):
        self.running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=1.0)
        if self.process_thread:
            self.process_thread.join(timeout=1.0)
        self.rtsp_handler.disconnect()
        self.wait()
