from PyQt6.QtCore import QThread, pyqtSignal
import cv2
from datetime import datetime
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
        self.frame_queue = Queue(maxsize=4)  # Optimized for CPU
        self.capture_thread = None
        self.process_thread = None


        try:

              # Get settings from config
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
            with open(config_path, 'r') as file:
                    self.config = json.load(file)

            video_settings = self.config.get('video_settings', {})
            self.target_fps = video_settings.get('target_fps', 30)
            self.playback_speed = video_settings.get('playback_speed', 1.0)
            self.frame_time = (1/self.target_fps) / self.playback_speed  # Adjust frame time based on speed

        except Exception as e:
            print(f"Error loading config: {e}")
            # Default values if config fails
            self.target_fps = 30
            self.playback_speed = 1.0
            self.frame_time = 1/self.target_fps


    def _capture_frames(self):

        last_frame_time = time.time()
        while self.running:
            if not self.rtsp_handler.is_opened():
                self.error.emit("Stream connection lost")
                break


            if not self.is_camera:
                current_time = time.time()
                elapsed = current_time - last_frame_time
                if elapsed < self.frame_time:
                    time.sleep(self.frame_time - elapsed)
                last_frame_time = time.time()
                

            ret, frame = self.rtsp_handler.read_frame()
            if ret:
                if self.frame_queue.full():
                    # Drop oldest frame if queue is full
                    try:
                        self.frame_queue.get_nowait()
                    except Queue.Empty:
                        pass
                self.frame_queue.put(frame)
            else:
             if not self.is_camera:
                self.running = False
                break
            time.sleep(0.001)  # Small delay to prevent CPU overload

    def _process_frames(self):
        while self.running:
            try:
                frame = self.frame_queue.get(timeout=1.0)  # 1 second timeout
                try:
                    frame_with_detection = self.detector.detect(frame)
                    self.frame_ready.emit(frame_with_detection)
                except Exception as e:
                    self.error.emit(f"Detection error: {str(e)}")
            except Empty:
                continue  # No frame available, continue waiting
            except Exception as e:
                self.error.emit(f"Processing error: {str(e)}")
            time.sleep(0.001)  # Small delay to prevent CPU overload

    def run(self):
        self.running = True
        
        # Connect to the video source
        if not self.rtsp_handler.connect(self.video_source):
            self.error.emit("Failed to connect to video source")
            return

        # Start capture and processing threads
        self.capture_thread = Thread(target=self._capture_frames)
        self.process_thread = Thread(target=self._process_frames)
        
        self.capture_thread.start()
        self.process_thread.start()

        # Wait for threads to complete
        self.capture_thread.join()
        self.process_thread.join()

        self.rtsp_handler.disconnect()
        self.finished.emit()

    def stop(self):
        self.running = False
        if self.capture_thread:
            self.capture_thread.join()
        if self.process_thread:
            self.process_thread.join()
        self.rtsp_handler.disconnect()
        self.wait()
