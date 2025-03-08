from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QMenu, QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QRect, QTimer, QRectF
from PyQt6.QtGui import QPixmap, QImage, QIcon, QColor, QPainter, QPen, QConicalGradient
import cv2
import os
from pathlib import Path
import sys
from urllib.parse import urlparse
import math

class LoadingSpinner(QWidget):
    def __init__(self, parent=None, centerOnParent=True):
        super().__init__(parent)
        
        self.centerOnParent = centerOnParent
        self.setFixedSize(64, 64)  # Larger size for better visibility
        self.angle = 0
        
        # Animation settings
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)
        self.timer.setInterval(16)  # ~60 FPS for smooth animation
        
        # Appearance settings
        self.color = QColor("#FFFFFF")  # White color
        self.pen_width = 3
        self.arc_length = 280  # Leave a small gap
        self.hide()
        
    def rotate(self):
        self.angle = (self.angle - 8) % 360  # Negative for clockwise rotation
        self.update()
        
    def start(self):
        self.show()
        if self.centerOnParent and self.parentWidget():
            self.centerOnParentWidget()
        self.timer.start()
        
    def stop(self):
        self.timer.stop()
        self.hide()
            
    def centerOnParentWidget(self):
        if self.parentWidget():
            parent = self.parentWidget()
            px = int((parent.width() - self.width()) / 2)
            py = int((parent.height() - self.height()) / 2)
            self.move(px, py)
            
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Create gradient for the arc
        gradient = QConicalGradient(self.width()/2, self.height()/2, self.angle)
        gradient.setColorAt(0, QColor(255, 255, 255, 255))  # Solid white
        gradient.setColorAt(0.7, QColor(255, 255, 255, 255))  # Solid white
        gradient.setColorAt(1, QColor(255, 255, 255, 0))  # Transparent
        
        # Setup pen with gradient
        pen = QPen()
        pen.setWidth(self.pen_width)
        pen.setBrush(gradient)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        
        # Calculate rect for arc
        rect = QRectF(
            self.pen_width,
            self.pen_width,
            self.width() - 2*self.pen_width,
            self.height() - 2*self.pen_width
        )
        
        # Draw the arc
        painter.drawArc(rect, self.angle * 16, self.arc_length * 16)

class StreamWidget(QFrame):
    """Widget for displaying individual RTSP stream with controls"""
    
    settingsClicked = pyqtSignal(str)  # Signal to show settings dialog
    maximizeClicked = pyqtSignal(object)  # Signal when maximize button clicked
    disableAllClicked = pyqtSignal(str)  # Signal to disable stream and detection
    
    def __init__(self, stream_id, parent=None):
        super().__init__(parent)
        self.stream_id = stream_id
        self.is_maximized = False
        self.is_display_enabled = True
        self.is_all_disabled = False
        self.loading_spinner = None
        self.current_layout = "2x2"
        
        # Set initial frame style
        self.setStyleSheet("""
            QFrame {
                border: 2px solid #f44336;
                border-radius: 4px;
                background-color: #ffffff;
                padding: 0px;
            }
            QLabel, QPushButton {
                border: none;
            }
        """)
        
        self._init_ui()
        # Don't set any initial status - will be set by update_stream_info
        self.update_layout_style(self.current_layout)
        
    def _init_ui(self):
        # Main layout with proper spacing
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Header section
        header_container = QVBoxLayout()
        header_container.setSpacing(4)
        header_container.setContentsMargins(0, 0, 0, 8)
        
        # Top row with title and controls
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        
        # Stream title and details
        title_container = QVBoxLayout()
        title_container.setSpacing(1)
        title_container.setContentsMargins(0, 0, 0, 0)
        
        # Main title (Stream ID)
        self.title_label = QLabel(f"Stream {self.stream_id}")
        self.title_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 13px;
                color: #2c3e50;
            }
        """)
        title_container.addWidget(self.title_label)
        
        # Stream URL with fixed width
        self.url_label = QLabel()
        self.url_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #7f8c8d;
                padding: 0px;
                margin: 0px;
            }
        """)
        self.url_label.setMaximumWidth(300)
        self.url_label.setMinimumWidth(200)
        title_container.addWidget(self.url_label)
        
        top_row.addLayout(title_container)
        top_row.addStretch()
        
        # Control buttons
        if getattr(sys, 'frozen', False):
            icons_dir = os.path.join(sys._MEIPASS, 'icons')
        else:
            icons_dir = os.path.join(Path(__file__).resolve().parent.parent.parent, 'icons')

        # Control buttons
        self.settings_btn = QPushButton()
        self.settings_btn.setIcon(QIcon(os.path.join(icons_dir, 'settings.png')))
        self.settings_btn.setIconSize(QSize(16, 16))
        self.settings_btn.setToolTip("Stream Settings")
        self.settings_btn.clicked.connect(
            lambda: self.settingsClicked.emit(self.stream_id))
            
        # Add display toggle button
        self.display_toggle_btn = QPushButton()
        # Set initial icon based on display state (reversed logic)
        icon_name = 'eye-off.png' if not self.is_display_enabled else 'eye.png'
        self.display_toggle_btn.setIcon(QIcon(os.path.join(icons_dir, icon_name)))
        self.display_toggle_btn.setIconSize(QSize(16, 16))
        self.display_toggle_btn.setToolTip("Hide Stream Display" if self.is_display_enabled else "Show Stream Display")
        self.display_toggle_btn.clicked.connect(self._toggle_display)
        
        self.maximize_btn = QPushButton()
        self.maximize_btn.setIcon(QIcon(os.path.join(icons_dir, 'maximize.png')))
        self.maximize_btn.setIconSize(QSize(16, 16))
        self.maximize_btn.setToolTip("Maximize/Restore")
        self.maximize_btn.clicked.connect(self._on_maximize)
        
        # Replace delete button with two disable buttons
        self.disable_all_btn = QPushButton()
        self.disable_all_btn.setIcon(QIcon(os.path.join(self._get_icons_dir(), 'stop.png')))
        self.disable_all_btn.setIconSize(QSize(16, 16))
        self.disable_all_btn.setToolTip("Disable Stream & Detection")
        self.disable_all_btn.clicked.connect(self._toggle_disable_all)
        self.disable_all_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid #cccccc;
                padding: 4px;
                border-radius: 4px;
                background-color: #f8f9fa;
                min-width: 28px;
                min-height: 28px;
            }
            QPushButton:hover {
                background-color: #ffebee;
                border-color: #f44336;
            }
            QPushButton:pressed {
                background-color: #ffcdd2;
                border-color: #e53935;
            }
            QPushButton:checked {
                background-color: #f44336;
                border-color: #d32f2f;
            }
        """)
        self.disable_all_btn.setCheckable(True)  # Make it toggleable
        
        # Update button style
        button_style = """
            QPushButton {
                border: 1px solid #cccccc;
                padding: 2px;
                border-radius: 3px;
                background-color: #f8f9fa;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
                border-color: #6c757d;
            }
            QPushButton:disabled {
                background-color: #e9ecef;
                border-color: #dee2e6;
                color: #adb5bd;
                opacity: 0.5;
            }
        """

        # Set initial button style
        for btn in [self.settings_btn, self.display_toggle_btn, 
                    self.maximize_btn, self.disable_all_btn]:
            btn.setStyleSheet(button_style)
            
        # Add spacing between buttons
        top_row.setSpacing(6)  # Add space between buttons
        
        top_row.addWidget(self.settings_btn)
        top_row.addWidget(self.display_toggle_btn)
        top_row.addWidget(self.maximize_btn)
        top_row.addWidget(self.disable_all_btn)
        
        header_container.addLayout(top_row)
        
        # Create a container for video and status
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(4)  # Space between video and status
        
        # Video display area with fixed aspect ratio
        video_container = QWidget()
        video_container.setMinimumSize(320, 240)
        video_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        video_layout = QVBoxLayout(video_container)
        video_layout.setContentsMargins(0, 0, 0, 0)
        video_layout.setSpacing(0)
        
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("""
            QLabel {
                background-color: #000000;
                min-width: 320px;
                min-height: 240px;
            }
        """)
        self.video_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # Force the video label to expand to its container
        self.video_label.setMinimumSize(320, 240)
        video_layout.addWidget(self.video_label, 1)  # Give it stretch factor of 1
        
        # Update spinner container setup with absolute positioning
        self.spinner_container = QWidget(self.video_label)
        self.spinner_container.setStyleSheet("background-color: rgba(0, 0, 0, 0.5);")
        self.spinner_container.hide()
        
        # Create loading spinner with fixed position
        self.loading_spinner = LoadingSpinner(self.spinner_container)
        
        # Calculate center position
        def center_spinner():
            spinner_x = (self.video_label.width() - self.loading_spinner.width()) // 2
            spinner_y = (self.video_label.height() - self.loading_spinner.height()) // 2
            self.loading_spinner.move(spinner_x, spinner_y)
        
        # Initial centering
        self.loading_spinner.show()  # Temporarily show to get correct size
        center_spinner()
        self.loading_spinner.hide()
        
        def on_container_resize():
            self.spinner_container.setGeometry(0, 0, 
                                             self.video_label.width(),
                                             self.video_label.height())
            center_spinner()
        
        # Connect resize event
        self.video_label.resizeEvent = lambda e: on_container_resize()
        
        # Status section
        status_container = QWidget()
        status_container.setFixedHeight(24)  # Slightly reduced height
        status_container.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-radius: 4px;
            }
        """)
        
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(8, 2, 8, 2)
        status_layout.setSpacing(8)
        
        self.status_indicator = QFrame()
        self.status_indicator.setFixedSize(8, 8)
        self.status_indicator.setStyleSheet("""
            QFrame {
                background-color: #9e9e9e;
                border-radius: 4px;
            }
        """)
        
        self.status_label = QLabel("")  # Initialize with empty status
        self.status_label.setStyleSheet("""
            QLabel {
                color: #333333;
                font-size: 11px;
            }
        """)
        
        status_layout.addWidget(self.status_indicator)
        status_layout.addWidget(self.status_label, 1)
        
        # Add video and status to content container
        content_layout.addWidget(video_container, 1)
        content_layout.addWidget(status_container)
        
        # Add all components to main layout
        layout.addLayout(header_container)
        layout.addWidget(content_container, 1)
        
    def _toggle_display(self):
        """Toggle stream display on/off"""
        self.is_display_enabled = not self.is_display_enabled
        
        # Update icon based on new state
        icon_name = 'eye-off.png' if not self.is_display_enabled else 'eye.png'
        self.display_toggle_btn.setIcon(QIcon(os.path.join(self._get_icons_dir(), icon_name)))
        
        # Update tooltip
        self.display_toggle_btn.setToolTip("Hide Stream Display" if self.is_display_enabled else "Show Stream Display")
        
        # Clear the video label if display is disabled
        if not self.is_display_enabled:
            # Show display disabled message with icon
            self.video_label.setStyleSheet("""
                QLabel {
                    background-color: #f8f9fa;
                    min-width: 320px;
                    min-height: 240px;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                }
            """)
            status_text = f"""
                <div style='text-align: center;'>
                    <img src='{os.path.join(self._get_icons_dir(), 'displaystopped.png')}' width='75' height='75'/>
                    <p style='margin-top: 10px; color: #6c757d; font-size: 14px;'>
                        Stream Display Disabled<br>
                        <span style='font-size: 12px; color: #adb5bd;'>Click the eye button to show stream</span>
                    </p>
                </div>
            """
            self.video_label.setText(status_text)
        else:
            # Reset video label style for video display
            self.video_label.setStyleSheet("""
                QLabel {
                    background-color: #000000;
                    min-width: 320px;
                    min-height: 240px;
                }
            """)
            self.video_label.clear()
        
    def _on_maximize(self):
        self.is_maximized = not self.is_maximized
        self.maximizeClicked.emit(self)
        
        # Update icon based on state
        icon_path = os.path.join(self._get_icons_dir(),
                                'minimize.png' if self.is_maximized else 'maximize.png')
        self.maximize_btn.setIcon(QIcon(icon_path))
        
    def update_frame(self, frame):
        """Update the displayed frame"""
        # Don't update frame if stream is disabled
        if self.is_all_disabled:
            return

        if not self.is_display_enabled:
            return
        
        try:
            if frame is not None:
                height, width, channel = frame.shape
                bytes_per_line = 3 * width
                q_image = QImage(frame.data, width, height, bytes_per_line, 
                               QImage.Format.Format_RGB888).rgbSwapped()
                pixmap = QPixmap.fromImage(q_image)
                
                # Scale pixmap to fit widget while maintaining aspect ratio
                widget_size = self.video_label.size()
                if widget_size.width() > 0 and widget_size.height() > 0:  # Ensure valid size
                    if not pixmap.isNull():  # Add check for null pixmap
                        scaled_pixmap = pixmap.scaled(
                            widget_size,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        )
                        
                        # Center the scaled pixmap in the label
                        self.video_label.setPixmap(scaled_pixmap)
                        
                        # Ensure spinner container matches video size
                        if hasattr(self, 'spinner_container'):
                            self.spinner_container.setGeometry(0, 0, 
                                                             widget_size.width(),
                                                             widget_size.height())
        except Exception as e:
            print(f"Error updating frame: {str(e)}")
        
    def resizeEvent(self, event):
        """Handle widget resize events"""
        super().resizeEvent(event)
        # Force update of video label size
        if hasattr(self, 'video_label') and self.video_label.pixmap() and not self.video_label.pixmap().isNull():
            current_pixmap = self.video_label.pixmap()
            scaled_pixmap = current_pixmap.scaled(
                self.video_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            if not scaled_pixmap.isNull():
                self.video_label.setPixmap(scaled_pixmap)
        
        # Update spinner container size
        if hasattr(self, 'spinner_container'):
            self.spinner_container.setGeometry(self.video_label.rect())
        
    def set_status(self, status):
        """Update the status text, indicator, and widget border"""
        self.status_label.setText(status)
        
        # Update status based on stream state
        if self.is_all_disabled:
            self.status_label.setText("Stream & Detection Stopped")
            self.status_indicator.setStyleSheet("""
                QFrame {
                    background-color: #f44336;  /* Red */
                    border-radius: 4px;
                }
            """)
            return

        if "connecting" in status.lower():
            # Yellow for connecting
            self.spinner_container.setGeometry(0, 0, 
                                             self.video_label.width(),
                                             self.video_label.height())
            self.spinner_container.show()
            self.loading_spinner.start()
            self.status_indicator.setStyleSheet("""
                QFrame {
                    background-color: #ffc107;  /* Yellow */
                    border-radius: 4px;
                }
            """)
            # Yellow border
            self.setStyleSheet("""
                QFrame {
                    border: 2px solid #ffc107;
                    border-radius: 4px;
                    background-color: #ffffff;
                    padding: 0px;
                }
                QLabel, QPushButton {
                    border: none;
                }
            """)
        elif "error" in status.lower():
            # Red for error
            self.spinner_container.hide()
            self.loading_spinner.stop()
            self.status_indicator.setStyleSheet("""
                QFrame {
                    background-color: #f44336;  /* Red */
                    border-radius: 4px;
                }
            """)
            self.setStyleSheet("""
                QFrame {
                    border: 2px solid #f44336;
                    border-radius: 4px;
                    background-color: #ffffff;
                    padding: 0px;
                }
                QLabel, QPushButton {
                    border: none;
                }
            """)
        else:
            # Green for running/normal state
            self.spinner_container.hide()
            self.loading_spinner.stop()
            self.status_indicator.setStyleSheet("""
                QFrame {
                    background-color: #4caf50;  /* Green */
                    border-radius: 4px;
                }
            """)
            # Normal border
            self.setStyleSheet("""
                QFrame {
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                    background-color: #ffffff;
                    padding: 0px;
                }
                QLabel, QPushButton {
                    border: none;
                }
            """)

    def _get_icons_dir(self):
        """Helper method to get icons directory path"""
        if getattr(sys, 'frozen', False):
            return os.path.join(sys._MEIPASS, 'icons')
        return os.path.join(Path(__file__).resolve().parent.parent.parent, 'icons')

    def update_stream_info(self, stream_config):
        """Update stream information display"""
        if stream_config:
            # Get and format RTSP URL for display
            rtsp_url = stream_config.get('rtsp_url', '')
            if rtsp_url:
                # Mask credentials in URL for display
                parsed = urlparse(rtsp_url)
                if parsed.username or parsed.password:
                    masked_url = f"{parsed.scheme}://*****@{parsed.hostname}{parsed.path}"
                else:
                    masked_url = rtsp_url
                    
                # Truncate if too long
                if len(masked_url) > 65:
                    masked_url = masked_url[:62] + "..."
            else:
                masked_url = "No URL configured"
                
            # Get host and port from data_sender config
            host = stream_config.get('data_sender', {}).get('host', 'N/A')
            port = stream_config.get('data_sender', {}).get('port', 'N/A')
            
            # Format details text with both URL and IP/TMS info
            details = f"URL: {masked_url}\nIP: {host}  |  TMS Port: {port}"
            self.url_label.setText(details)
            
            # Update label style to ensure proper display
            self.url_label.setStyleSheet("""
                QLabel {
                    font-size: 11px;
                    color: #7f8c8d;
                    padding: 0px;
                    margin: 0px;
                }
            """)

            # Check stream state and update status immediately
            if not stream_config.get('enabled', True):
                self.update_disable_all_state(True)
                self.set_status("Stream & Detection Stopped")
            elif not stream_config.get('rtsp_url'):
                self.set_status("No URL Configured")
            else:
                self.set_status("Waiting...")  # Only show waiting if enabled and has URL

    def setVisible(self, visible):
        """Override setVisible to handle visibility changes more efficiently"""
        if self.isVisible() == visible:
            return
        super().setVisible(visible)
        
    def show(self):
        """Override show to handle showing more efficiently"""
        if self.isVisible():
            return
        super().show()
        
    def hide(self):
        """Override hide to handle hiding more efficiently"""
        if not self.isVisible():
            return
        super().hide()

    def update_layout_style(self, layout_type):
        """Update widget style based on layout type"""
        self.current_layout = layout_type
        
        # Define sizes based on layout
        button_size = QSize(25, 25) if layout_type == "2x3" else QSize(32, 32)
        icon_size = QSize(16, 16) if layout_type == "2x3" else QSize(20, 20)
        
        # Update font sizes
        title_font_size = "11px" if layout_type == "2x3" else "13px"
        url_font_size = "10px" if layout_type == "2x3" else "11px"
        status_font_size = "10px" if layout_type == "2x3" else "11px"
        
        # Update button sizes
        for btn in [self.settings_btn, self.display_toggle_btn, 
                   self.maximize_btn, self.disable_all_btn]:
            btn.setFixedSize(button_size)
            btn.setIconSize(icon_size)
        
        # Update title label style
        self.title_label.setStyleSheet(f"""
            QLabel {{
                font-weight: bold;
                font-size: {title_font_size};
                color: #2c3e50;
            }}
        """)
        
        # Update URL label style
        self.url_label.setStyleSheet(f"""
            QLabel {{
                font-size: {url_font_size};
                color: #7f8c8d;
                padding: 0px;
                margin: 0px;
            }}
        """)
        
        # Update status label style
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: #333333;
                font-size: {status_font_size};
            }}
        """)

    def _toggle_disable_all(self):
        # Don't toggle button state here, let MainWindow control it
        self.disableAllClicked.emit(self.stream_id)
        # Reset button state to match current state
        self.disable_all_btn.setChecked(self.is_all_disabled)

    def update_disable_all_state(self, is_disabled):
        """Update the button state and display after verification"""
        self.is_all_disabled = is_disabled
        self.disable_all_btn.setChecked(is_disabled)
        
        # Update display toggle button state
        self.display_toggle_btn.setEnabled(not is_disabled)
        
        if is_disabled:
            # Update button to show "play" state
            self.disable_all_btn.setIcon(QIcon(os.path.join(self._get_icons_dir(), 'play.png')))
            self.disable_all_btn.setToolTip("Enable Stream & Detection")
            
            # Force display off when stream is disabled
            self.is_display_enabled = False
            self.display_toggle_btn.setIcon(QIcon(os.path.join(self._get_icons_dir(), 'eye-off.png')))
            self.display_toggle_btn.setToolTip("Display disabled while stream is stopped")
            
            # Show stopped status with icons
            self.video_label.clear()
            self.video_label.setStyleSheet("""
                QLabel {
                    background-color: #f8f9fa;
                    min-width: 320px;
                    min-height: 240px;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                }
            """)
            status_text = f"""
                <div style='text-align: center;'>
                    <img src='{os.path.join(self._get_icons_dir(), 'detection-off.png')}' width='75' height='75'/>
                    <p style='margin-top: 10px; color: #6c757d; font-size: 14px;'>
                        Stream and Detection Stopped<br>
                        <span style='font-size: 12px; color: #adb5bd;'>Click the button to resume</span>
                    </p>
                </div>
            """
            self.video_label.setText(status_text)
        else:
            # Update button to show "stop" state
            self.disable_all_btn.setIcon(QIcon(os.path.join(self._get_icons_dir(), 'stop.png')))
            self.disable_all_btn.setToolTip("Disable Stream & Detection")
            
            # Automatically enable stream display when stream is enabled
            self.is_display_enabled = True
            self.display_toggle_btn.setIcon(QIcon(os.path.join(self._get_icons_dir(), 'eye.png')))
            self.display_toggle_btn.setToolTip("Hide Stream Display")
            
            # Reset video label for video display
            self.video_label.setStyleSheet("""
                QLabel {
                    background-color: #000000;
                    min-width: 320px;
                    min-height: 240px;
                }
            """)
            self.video_label.clear() 