from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QHBoxLayout)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QImage
import cv2
import os
from pathlib import Path
from ui.rtsp_handler import RTSPHandler
from detector import LicensePlateDetector
from .rtsp_stream_dialog import RTSPStreamDialog
from detector_worker import DetectionWorker
import json

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.detection_worker = None
        self.rtsp_handler = RTSPHandler()
        self.setWindowTitle("License Plate Detection")
        self.setMinimumSize(1000, 700)
        
        # Get project root directory
        ROOT_DIR = Path(__file__).resolve().parent.parent.parent
        
        try:
            # Load config
            config_path = os.path.join(ROOT_DIR, 'config.json')
            with open(config_path, 'r') as f:
                config = json.load(f)
                
            # Initialize detector with model path from config
            model_path = os.path.join(ROOT_DIR, config.get('model_path', 'models/NPDv1.0.pt'))
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
    # def start_detection(self):
    #     if self.is_camera:
    #         self.camera = cv2.VideoCapture(0)
    #         if not self.camera.isOpened():
    #             self.status_label.setText("Status: Error - Cannot open camera")
    #             return
    #     else:
    #         if self.video_path:
    #             self.camera = cv2.VideoCapture(self.video_path)
    #             if not self.camera.isOpened():
    #                 self.status_label.setText("Status: Error - Cannot open video source")
    #                 return
    #         else:
    #             self.status_label.setText("Status: No video source selected")
    #             return

    #     self.timer.start(30)
    #     self.detection_active = True
    #     self.status_label.setText("Status: Detection running...")


    def stop_detection(self):
        """Stop detection thread"""
        if self.detection_worker and self.detection_worker.isRunning():
            self.detection_worker.stop()
            self.detection_worker = None

        self.detection_active = False
        self.current_source = None
        self.video_label.clear()
        self.status_label.setText("Status: Detection stopped")

    # def stop_detection(self):
    #     self.timer.stop()
    #     if self.camera is not None:
    #         self.camera.release()
    #         self.camera = None
    #     self.detection_active = False
    #     self.current_source = None
    #     self.video_label.clear()
    #     self.status_label.setText("Status: Detection stopped")
        

    # def update_frame(self):
    #     ret, frame = self.camera.read()
    #     if ret:
    #         if not self.is_camera and self.camera.get(cv2.CAP_PROP_POS_FRAMES) == self.camera.get(cv2.CAP_PROP_FRAME_COUNT):
    #             self.stop_detection()
    #             self.status_label.setText("Status: Video playback completed")
    #             return

    #         frame_with_detection = self.detector.detect(frame)
    #         height, width, channel = frame_with_detection.shape
    #         bytes_per_line = 3 * width
    #         q_image = QImage(frame_with_detection.data, width, height, bytes_per_line, QImage.Format.Format_RGB888).rgbSwapped()
    #         pixmap = QPixmap.fromImage(q_image)
    #         scaled_pixmap = pixmap.scaled(self.video_label.size(), Qt.AspectRatioMode.KeepAspectRatio)
    #         self.video_label.setPixmap(scaled_pixmap)
    #     else:
    #         self.stop_detection()
    #         self.status_label.setText("Status: Error reading frame")

    # def closeEvent(self, event):
    #     self.stop_detection()
    #     event.accept()

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

# from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QHBoxLayout)
# from PyQt6.QtCore import Qt, QTimer
# from PyQt6.QtGui import QPixmap, QImage
# import cv2
# import os
# from ui.rtsp_handler import RTSPHandler
# from detector import LicensePlateDetector
# from .rtsp_stream_dialog import RTSPStreamDialog

# class MainWindow(QMainWindow):
#     def __init__(self):
#         super().__init__()
#         self.rtsp_handler = RTSPHandler()
#         self.setWindowTitle("License Plate Detection")
#         self.setMinimumSize(1000, 700)
#         self.rtsp_button = QPushButton("Connect RTSP")
#         # Initialize detector
#         self.detector = LicensePlateDetector("C:\\Users\\suraj\\OneDrive\\Desktop\\ALL DEVELPMENT\\PYTHON\\YOLO11\\models\\NPDv1.0.pt")
        
#         # Initialize video source
#         self.camera = None
#         self.video_path = None
#         self.is_camera = True
#         self.detection_active = False  # Initialize detection state


#         # Create timer for real-time video
#         self.timer = QTimer()
#         self.timer.timeout.connect(self.update_frame)
#         self.rtsp_button.clicked.connect(self.connect_rtsp)
#         # Create central widget and layouts
#         central_widget = QWidget()
#         self.setCentralWidget(central_widget)
#         main_layout = QVBoxLayout(central_widget)
#         button_layout = QHBoxLayout()
#         button_layout.addWidget(self.rtsp_button)
#         # Create UI elements
#         self.video_label = QLabel()
#         self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
#         self.video_label.setMinimumSize(800, 600)
        
#         # Create buttons
#         self.camera_button = QPushButton("Use Camera")
#         self.video_button = QPushButton("Open Video File")
#         self.start_button = QPushButton("Start Detection")
#         self.stop_button = QPushButton("Stop Detection")
#         self.stop_button.setEnabled(False)
        
#         # Status label
#         self.status_label = QLabel("Status: Ready")
        
#         # Add widgets to layouts
#         main_layout.addWidget(self.video_label)
#         button_layout.addWidget(self.camera_button)
#         button_layout.addWidget(self.video_button)
#         button_layout.addWidget(self.start_button)
#         button_layout.addWidget(self.stop_button)
#         main_layout.addLayout(button_layout)
#         main_layout.addWidget(self.status_label)

#         # Connect signals
#         self.camera_button.clicked.connect(self.use_camera)
#         self.video_button.clicked.connect(self.open_video_file)
#         self.start_button.clicked.connect(self.start_detection)
#         self.stop_button.clicked.connect(self.stop_detection)


#     def connect_rtsp(self):
#         """Open RTSP stream connection dialog"""
#         dialog = RTSPStreamDialog(self)
#         if dialog.exec():
#             settings = dialog.get_settings()
#             if settings['url']:
#                 self.is_camera = False
#                 self.video_path = settings['url']
                
#                 # Try to connect to the stream
#                 if self.rtsp_handler.connect(settings['url'], settings['protocol']):
#                     # Get detailed stream information
#                     stream_info = self.rtsp_handler.get_stream_info()
#                     if stream_info:
#                         info_text = (
#                             f"Status: RTSP stream connected\n"
#                             f"URL: {settings['url']}\n"
#                             f"Resolution: {stream_info['width']}x{stream_info['height']}\n"
#                             f"FPS: {stream_info['fps']}\n"
#                             f"Codec: {stream_info['codec_name']}\n"
#                             f"Protocol: {settings['protocol']}"
#                         )
#                         self.status_label.setText(info_text)
#                         # self.start_detection()  
#                         self.toggle_detection()  # Start or stop detection

#                     # self.start_button.setEnabled(True)
#                 else:
#                     self.status_label.setText("Status: Error - Cannot connect to RTSP stream")
    
#     def use_camera(self):
#         """Switch to camera input"""
#         self.is_camera = True
#         self.video_path = None
#         self.status_label.setText("Status: Camera selected")
#         # self.start_button.setEnabled(True)
#         # self.start_detection()  
#         self.toggle_detection()

        
#     def open_video_file(self):
#         """Open a video file"""
#         file_name, _ = QFileDialog.getOpenFileName(
#             self,
#             "Open Video File",
#             "",
#             "Video Files (*.mp4 *.avi *.mkv);;All Files (*.*)"
#         )
#         if file_name:
#             self.is_camera = False
#             self.video_path = file_name
#             self.status_label.setText(f"Status: Video selected: {os.path.basename(file_name)}")
#             # self.start_detection() 
#             # self.start_button.setEnabled(True)
#             self.toggle_detection()

#     def start_detection(self):
#         """Start detection on either camera or video"""
#         if self.is_camera:
#             self.camera = cv2.VideoCapture(0)
#             if not self.camera.isOpened():
#                 self.status_label.setText("Status: Error - Cannot open camera")
#                 return
#         else:
#             if self.video_path:
#                 self.camera = cv2.VideoCapture(self.video_path)
#                 if not self.camera.isOpened():
#                     self.status_label.setText("Status: Error - Cannot open video file")
#                     return
        
#         self.timer.start(30)  # Update every 30ms
#         self.start_button.setEnabled(False)
#         self.stop_button.setEnabled(True)
#         self.camera_button.setEnabled(False)
#         self.video_button.setEnabled(False)
#         self.status_label.setText("Status: Detection running...")

#     def stop_detection(self):
#         """Stop detection and release resources"""
#         self.timer.stop()
#         if self.camera is not None:
#             self.camera.release()
        
#         self.start_button.setEnabled(True)
#         self.stop_button.setEnabled(False)
#         self.camera_button.setEnabled(True)
#         self.video_button.setEnabled(True)
#         self.video_label.clear()
#         self.status_label.setText("Status: Detection stopped")

#     def update_frame(self):
#         """Update frame from camera/video"""
#         ret, frame = self.camera.read()
        
#         if ret:
#             # For video files, check if we've reached the end
#             if not self.is_camera and self.camera.get(cv2.CAP_PROP_POS_FRAMES) == self.camera.get(cv2.CAP_PROP_FRAME_COUNT):
#                 self.stop_detection()
#                 self.status_label.setText("Status: Video playback completed")
#                 return
            
#             # Detect license plates
#             frame_with_detection = self.detector.detect(frame)
            
#             # Convert frame to Qt format
#             height, width, channel = frame_with_detection.shape
#             bytes_per_line = 3 * width
#             q_image = QImage(frame_with_detection.data, width, height, bytes_per_line,QImage.Format.Format_RGB888).rgbSwapped()
            
#             # Scale the image to fit the label while maintaining aspect ratio
#             pixmap = QPixmap.fromImage(q_image)
#             scaled_pixmap = pixmap.scaled(self.video_label.size(), 
#                                         Qt.AspectRatioMode.KeepAspectRatio)
#             self.video_label.setPixmap(scaled_pixmap)
#         else:
#             self.stop_detection()
#             self.status_label.setText("Status: Error reading frame")

#     # def closeEvent(self, event):
#     #     """Clean up resources when closing the window"""
#     #     self.stop_detection()
#     #     event.accept()

#     def toggle_detection(self):
#         """Toggle detection on and off"""
#         if self.detection_active:
#             self.stop_detection()  # Stop detection
#             self.status_label.setText("Status: Detection stopped")
#         else:
#             self.start_detection()  # Start detection
#             self.status_label.setText("Status: Detection started")
#         self.detection_active = not self.detection_active  # Toggle state
