from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QHBoxLayout)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QImage
import os
from pathlib import Path
from ui.rtsp_handler import RTSPHandler
from detector import LicensePlateDetector
from .rtsp_stream_dialog import RTSPStreamDialog
from detector_worker import DetectionWorker
import json
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.detection_worker = None
        self.rtsp_handler = RTSPHandler()
        self.setWindowTitle("License Plate Detection")
        self.setMinimumSize(1000, 700)
        
        # Load config from the appropriate path
        config_path = self._get_config_path()
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                
            # Initialize detector with model path from config
            model_path = os.path.join(Path(__file__).resolve().parent.parent.parent, config.get('model_path', 'models/NPDv1.0.pt'))
            print(f"modelpath {model_path}")
            self.detector = LicensePlateDetector(model_path)
            
        except Exception as e:
            print(f"Error initializing application: {e}")
            raise

        self.camera = None
        self.video_path = None
        self.is_camera = False
        self.detection_active = False
        self.current_source = None  # Can be 'camera', 'video', 'rtsp'
        self.stream_visible = True  # Initialize stream visibility state

        # Add toggle visibility button
        self.toggle_visibility_button = QPushButton("Hide Stream")
        self.toggle_visibility_button.clicked.connect(self.toggle_stream_visibility)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        button_layout = QHBoxLayout()

        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(800, 600)
        
        self.camera_button = QPushButton("Use Camera")
        self.video_button = QPushButton("Open Video File")
        self.rtsp_button = QPushButton("Connect RTSP")
        
        self.status_label = QLabel("Status: Ready")
        
        button_layout.addWidget(self.camera_button)
        button_layout.addWidget(self.video_button)
        button_layout.addWidget(self.rtsp_button)
        button_layout.addWidget(self.toggle_visibility_button)
        main_layout.addWidget(self.video_label)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.status_label)

        self.camera_button.clicked.connect(lambda: self.toggle_source_and_detection('camera'))
        self.video_button.clicked.connect(lambda: self.toggle_source_and_detection('video'))
        self.rtsp_button.clicked.connect(self.connect_rtsp)

    def _get_config_path(self):
        """Get the path to the config.json file."""
        if getattr(sys, 'frozen', False):  # Check if running as a bundled executable
            return os.path.join(sys._MEIPASS, 'config.json')
        else:
            return os.path.join(Path(__file__).resolve().parent.parent.parent, 'config.json')

    def toggle_source_and_detection(self, source):
        if self.detection_active and self.current_source == source:
            self.stop_detection()
        else:
            self.stop_detection()  # Ensure previous detection is stopped
            if source == 'camera':
                self.is_camera = True
                self.video_path = None
                self.start_detection()
                self.current_source = 'camera'
            elif source == 'video':
                self.is_camera = False
                self.open_video_file()
                if self.video_path:
                    self.start_detection()
                    self.current_source = 'video'
                else:
                    self.current_source = None
            # RTSP connection is handled separately

    def connect_rtsp(self):
        dialog = RTSPStreamDialog(self)
        if dialog.exec():
            settings = dialog.get_settings()
            if settings['url']:
                self.is_camera = False
                self.video_path = settings['url']
                if self.rtsp_handler.connect(settings['url']):
                    self.start_detection()
                    self.current_source = 'rtsp'
                else:
                    self.status_label.setText("Status: Error - Cannot connect to RTSP stream")
            else:
                    self.status_label.setText("Status: Error - Cannot connect to RTSP stream")
        else:
            self.status_label.setText("Status: RTSP connection cancelled")

    def open_video_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open Video File",
            "",
            "Video Files (*.mp4 *.avi *.mkv);;All Files (*.*)"
        )
        if file_name:
            self.video_path = file_name
            self.status_label.setText(f"Status: Video selected: {os.path.basename(file_name)}")
        else:
            self.video_path = None
            self.status_label.setText("Status: No video selected")

    def start_detection(self):
        """Start detection in background thread"""
        if self.is_camera:
            source = 0
        else:
            if not self.video_path:
                self.status_label.setText("Status: No video source selected")
                return
            source = self.video_path

        # Create and start worker thread
        self.detection_worker = DetectionWorker(
            detector=self.detector,
            video_source=source,
            is_camera=self.is_camera
        )

        # Connect signals
        self.detection_worker.frame_ready.connect(self.update_frame)
        self.detection_worker.error.connect(self.handle_detection_error)
        self.detection_worker.finished.connect(self.handle_detection_finished)

        # Update UI
        self.detection_active = True
        self.status_label.setText("Status: Detection running...")
        
        # Start worker
        self.detection_worker.start()

    def stop_detection(self):
        """Stop detection thread"""
        if self.detection_worker and self.detection_worker.isRunning():
            self.detection_worker.stop()
            self.detection_worker = None

        self.detection_active = False
        self.current_source = None
        self.video_label.clear()
        self.status_label.setText("Status: Detection stopped")

    def toggle_stream_visibility(self):
        """Toggle stream visibility while keeping detection running"""
        self.stream_visible = not self.stream_visible
        if self.stream_visible:
            self.toggle_visibility_button.setText("Hide Stream")
            self.video_label.show()
        else:
            self.toggle_visibility_button.setText("Show Stream")
            self.video_label.hide()
        self.status_label.setText(f"Status: Stream {'visible' if self.stream_visible else 'hidden'}")

    def update_frame(self, frame):
        """Update frame from worker thread"""
        if self.stream_visible:
            height, width, channel = frame.shape
            bytes_per_line = 3 * width
            q_image = QImage(frame.data, width, height, bytes_per_line, 
                            QImage.Format.Format_RGB888).rgbSwapped()
            pixmap = QPixmap.fromImage(q_image)
            scaled_pixmap = pixmap.scaled(self.video_label.size(), 
                                        Qt.AspectRatioMode.KeepAspectRatio)
            self.video_label.setPixmap(scaled_pixmap)

    def handle_detection_error(self, error_message):
            """Handle errors from detection thread"""
            self.stop_detection()
            self.status_label.setText(f"Status: Error - {error_message}")

    def handle_detection_finished(self):
            """Handle detection completion"""
            self.stop_detection()
            self.status_label.setText("Status: Video playback completed")

    def closeEvent(self, event):
            """Clean up resources when closing the window"""
            self.stop_detection()
            event.accept()

