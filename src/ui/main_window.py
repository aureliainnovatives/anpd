# import sys
# import os
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel
# from PyQt6.QtCore import Qt, QTimer
# from PyQt6.QtGui import QPixmap, QImage
# import cv2
# from detector import LicensePlateDetector


# class MainWindow(QMainWindow):
#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle("Real-time License Plate Detection")
#         self.setMinimumSize(800, 600)

#         # Initialize detector
#         # self.detector = LicensePlateDetector("yolo11n.pt")  # Update with your model path
#         model_path = "models/license_plate_detector.pt"  # Update with your model path
#         self.detector = LicensePlateDetector(model_path)
#         # Initialize camera
#         self.camera = cv2.VideoCapture(0)
        
#         # Create timer for real-time video
#         self.timer = QTimer()
#         self.timer.timeout.connect(self.update_frame)
        
#         # Create central widget and layout
#         central_widget = QWidget()
#         self.setCentralWidget(central_widget)
#         layout = QVBoxLayout(central_widget)

#         # Create UI elements
#         self.video_label = QLabel()
#         self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
#         self.start_button = QPushButton("Start Detection")
#         self.stop_button = QPushButton("Stop Detection")
#         self.stop_button.setEnabled(False)
        
#         # Add widgets to layout
#         layout.addWidget(self.video_label)
#         layout.addWidget(self.start_button)
#         layout.addWidget(self.stop_button)

#         # Connect signals
#         self.start_button.clicked.connect(self.start_detection)
#         self.stop_button.clicked.connect(self.stop_detection)

#     def start_detection(self):
#         self.timer.start(30)  # Update every 30ms (approximately 33 fps)
#         self.start_button.setEnabled(False)
#         self.stop_button.setEnabled(True)

#     def stop_detection(self):
#         self.timer.stop()
#         self.start_button.setEnabled(True)
#         self.stop_button.setEnabled(False)

#     def update_frame(self):
#         ret, frame = self.camera.read()
#         if ret:
#             # Detect license plates
#             frame_with_detection = self.detector.detect(frame)
            
#             # Convert frame to Qt format
#             height, width, channel = frame_with_detection.shape
#             bytes_per_line = 3 * width
#             q_image = QImage(frame_with_detection.data, width, height, bytes_per_line, 
#                            QImage.Format.Format_RGB888).rgbSwapped()
#             pixmap = QPixmap.fromImage(q_image)
#             scaled_pixmap = pixmap.scaled(self.video_label.size(), 
#                                         Qt.AspectRatioMode.KeepAspectRatio)
#             self.video_label.setPixmap(scaled_pixmap)

#     def closeEvent(self, event):
#         # Clean up resources when closing the window
#         self.camera.release()
#         event.accept()




from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QHBoxLayout)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QImage
import cv2
import os
from ui.rtsp_handler import RTSPHandler
from detector import LicensePlateDetector
from .rtsp_stream_dialog import RTSPStreamDialog



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.rtsp_handler = RTSPHandler()
        self.setWindowTitle("License Plate Detection")
        self.setMinimumSize(1000, 700)
        self.rtsp_button = QPushButton("Connect RTSP")
        # Initialize detector
        self.detector = LicensePlateDetector("C:\\Users\\suraj\\OneDrive\\Desktop\\ALL DEVELPMENT\\PYTHON\\YOLO11\\models\\license_plate_detector.pt")
        
        # Initialize video source
        self.camera = None
        self.video_path = None
        self.is_camera = True
       

        # Create timer for real-time video
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.rtsp_button.clicked.connect(self.connect_rtsp)
        # Create central widget and layouts
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.rtsp_button)
        # Create UI elements
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(800, 600)
        
        # Create buttons
        self.camera_button = QPushButton("Use Camera")
        self.video_button = QPushButton("Open Video File")
        self.start_button = QPushButton("Start Detection")
        self.stop_button = QPushButton("Stop Detection")
        self.stop_button.setEnabled(False)
        
        # Status label
        self.status_label = QLabel("Status: Ready")
        
        # Add widgets to layouts
        main_layout.addWidget(self.video_label)
        button_layout.addWidget(self.camera_button)
        button_layout.addWidget(self.video_button)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.status_label)

        # Connect signals
        self.camera_button.clicked.connect(self.use_camera)
        self.video_button.clicked.connect(self.open_video_file)
        self.start_button.clicked.connect(self.start_detection)
        self.stop_button.clicked.connect(self.stop_detection)


    def connect_rtsp(self):
        """Open RTSP stream connection dialog"""
        dialog = RTSPStreamDialog(self)
        if dialog.exec():
            settings = dialog.get_settings()
            if settings['url']:
                self.is_camera = False
                self.video_path = settings['url']
                
                # Try to connect to the stream
                if self.rtsp_handler.connect(settings['url'], settings['protocol']):
                    # Get detailed stream information
                    stream_info = self.rtsp_handler.get_stream_info()
                    if stream_info:
                        info_text = (
                            f"Status: RTSP stream connected\n"
                            f"URL: {settings['url']}\n"
                            f"Resolution: {stream_info['width']}x{stream_info['height']}\n"
                            f"FPS: {stream_info['fps']}\n"
                            f"Codec: {stream_info['codec_name']}\n"
                            f"Protocol: {settings['protocol']}"
                        )
                        self.status_label.setText(info_text)
                    self.start_button.setEnabled(True)
                else:
                    self.status_label.setText("Status: Error - Cannot connect to RTSP stream")
    # def connect_rtsp(self):
    # # """Open RTSP stream connection dialog"""
    #     dialog = RTSPStreamDialog(self)
    #     if dialog.exec():
    #         rtsp_url = dialog.get_url()
    #         if rtsp_url:
    #             self.is_camera = False
    #             self.video_path = rtsp_url
    #             self.status_label.setText(f"Status: RTSP stream selected: {rtsp_url}")
    #             self.start_button.setEnabled(True)
    
    def use_camera(self):
        """Switch to camera input"""
        self.is_camera = True
        self.video_path = None
        self.status_label.setText("Status: Camera selected")
        self.start_button.setEnabled(True)

    def open_video_file(self):
        """Open a video file"""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open Video File",
            "",
            "Video Files (*.mp4 *.avi *.mkv);;All Files (*.*)"
        )
        if file_name:
            self.is_camera = False
            self.video_path = file_name
            self.status_label.setText(f"Status: Video selected: {os.path.basename(file_name)}")
            self.start_button.setEnabled(True)

    def start_detection(self):
        """Start detection on either camera or video"""
        if self.is_camera:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                self.status_label.setText("Status: Error - Cannot open camera")
                return
        else:
            if self.video_path:
                self.camera = cv2.VideoCapture(self.video_path)
                if not self.camera.isOpened():
                    self.status_label.setText("Status: Error - Cannot open video file")
                    return
        
        self.timer.start(30)  # Update every 30ms
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.camera_button.setEnabled(False)
        self.video_button.setEnabled(False)
        self.status_label.setText("Status: Detection running...")

    def stop_detection(self):
        """Stop detection and release resources"""
        self.timer.stop()
        if self.camera is not None:
            self.camera.release()
        
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.camera_button.setEnabled(True)
        self.video_button.setEnabled(True)
        self.video_label.clear()
        self.status_label.setText("Status: Detection stopped")

    def update_frame(self):
        """Update frame from camera/video"""
        ret, frame = self.camera.read()
        
        if ret:
            # For video files, check if we've reached the end
            if not self.is_camera and self.camera.get(cv2.CAP_PROP_POS_FRAMES) == self.camera.get(cv2.CAP_PROP_FRAME_COUNT):
                self.stop_detection()
                self.status_label.setText("Status: Video playback completed")
                return
            
            # Detect license plates
            frame_with_detection = self.detector.detect(frame)
            
            # Convert frame to Qt format
            height, width, channel = frame_with_detection.shape
            bytes_per_line = 3 * width
            q_image = QImage(frame_with_detection.data, width, height, bytes_per_line,QImage.Format.Format_RGB888).rgbSwapped()
            
            # Scale the image to fit the label while maintaining aspect ratio
            pixmap = QPixmap.fromImage(q_image)
            scaled_pixmap = pixmap.scaled(self.video_label.size(), 
                                        Qt.AspectRatioMode.KeepAspectRatio)
            self.video_label.setPixmap(scaled_pixmap)
        else:
            self.stop_detection()
            self.status_label.setText("Status: Error reading frame")

    def closeEvent(self, event):
        """Clean up resources when closing the window"""
        self.stop_detection()
        event.accept()