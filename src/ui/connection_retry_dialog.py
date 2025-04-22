from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, 
                             QPushButton, QWidget, QHBoxLayout)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QFont
import time

class ConnectionRetryDialog(QDialog):
    retry_complete = pyqtSignal(bool, str)  # Signal to emit result (success, message)
    
    def __init__(self, parent=None, max_retries=3, retry_interval=2):
        super().__init__(parent)
        self.max_retries = max_retries
        self.retry_interval = retry_interval
        self.current_retry = 0
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Server Connection")
        self.setFixedSize(300, 220)  # Adjusted size to match screenshot
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
        
        # Set background color and border
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 10px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 25, 20, 25)  # Adjusted margins
        layout.setSpacing(15)  # Reduced spacing between elements
        
        # Title label
        title_label = QLabel("Connecting to Server")
        title_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 15px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Status label
        self.status_label = QLabel("Connection failed")  # Default text
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #e74c3c;
                font-size: 13px;
                font-family: 'Segoe UI', Arial;
            }
        """)
        layout.addWidget(self.status_label)
        
        # Retry count label
        self.retry_label = QLabel(f"Attempt 1 of {self.max_retries}")
        self.retry_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.retry_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 12px;
                font-family: 'Segoe UI', Arial;
                margin-top: -5px;
            }
        """)
        layout.addWidget(self.retry_label)
        
        layout.addSpacing(10)  # Add space before button
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_button.setFixedSize(120, 32)  # Adjusted button size
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #f5f6f7;
                color: #e74c3c;
                border: none;
                border-radius: 16px;
                font-size: 13px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial;
            }
            QPushButton:hover {
                background-color: #e74c3c;
                color: white;
            }
            QPushButton:pressed {
                background-color: #c0392b;
            }
        """)
        self.cancel_button.clicked.connect(self.reject)
        layout.addWidget(self.cancel_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
    def paintEvent(self, event):
        """Custom paint event to draw shadows and rounded corners"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw shadow
        painter.setPen(Qt.PenStyle.NoPen)
        for i in range(10):
            color = QColor(0, 0, 0, 3)  # Lighter shadow
            painter.setBrush(color)
            painter.drawRoundedRect(i, i, self.width()-2*i, self.height()-2*i, 10, 10)
        
        # Draw white background
        painter.setBrush(QColor(255, 255, 255))
        painter.drawRoundedRect(5, 5, self.width()-10, self.height()-10, 10, 10)
        
    def start_retry_sequence(self, retry_function):
        """Start the retry sequence with the given function"""
        self.retry_function = retry_function
        self.current_retry = 0
        self._try_connection()
        
    def _try_connection(self):
        """Attempt a connection"""
        self.current_retry += 1
        self.retry_label.setText(f"Attempt {self.current_retry} of {self.max_retries}")
        self.status_label.setText("Connecting...")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #34495e;
                font-size: 13px;
                font-family: 'Segoe UI', Arial;
            }
        """)
        
        # Try the connection after a short delay
        QTimer.singleShot(100, self._execute_retry)
        
    def _execute_retry(self):
        """Execute the retry function"""
        try:
            success = self.retry_function()
            if success:
                self.status_label.setText("Connection successful!")
                self.status_label.setStyleSheet("""
                    QLabel {
                        color: #27ae60;
                        font-size: 13px;
                        font-family: 'Segoe UI', Arial;
                    }
                """)
                QTimer.singleShot(500, lambda: self.retry_complete.emit(True, "Connected successfully"))
                QTimer.singleShot(1000, self.accept)
            else:
                self._handle_retry_failure()
        except Exception as e:
            self._handle_retry_failure(str(e))
            
    def _handle_retry_failure(self, error_message=None):
        """Handle a failed retry attempt"""
        if self.current_retry < self.max_retries:
            self.status_label.setText("Connection failed")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #e74c3c;
                    font-size: 13px;
                    font-family: 'Segoe UI', Arial;
                }
            """)
            QTimer.singleShot(self.retry_interval * 1000, self._try_connection)
        else:
            self.status_label.setText("Connection failed")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #e74c3c;
                    font-size: 13px;
                    font-family: 'Segoe UI', Arial;
                }
            """)
            self.retry_complete.emit(False, "Failed to connect after maximum retries")
            QTimer.singleShot(1000, self.reject) 