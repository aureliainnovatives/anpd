from PyQt6.QtCore import QThread, pyqtSignal
import cv2
from datetime import datetime

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

    def run(self):
        self.running = True
        cap = cv2.VideoCapture(0 if self.is_camera else self.video_source)

        if not cap.isOpened():
            self.error.emit("Failed to open video source")
            return

        while self.running:
            ret, frame = cap.read()
            if not ret:
                if not self.is_camera:
                    # Video playback completed
                    self.finished.emit()
                else:
                    self.error.emit("Error reading frame")
                break

            try:
                # Process frame with detector
                frame_with_detection = self.detector.detect(frame)
                self.frame_ready.emit(frame_with_detection)
            except Exception as e:
                self.error.emit(f"Detection error: {str(e)}")
                break

        cap.release()

    def stop(self):
        self.running = False
        self.wait()