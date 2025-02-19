from PyQt6.QtWidgets import QSplashScreen, QProgressBar, QVBoxLayout, QWidget, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QPainter, QColor, QLinearGradient
import os
import sys
from pathlib import Path

class ModernProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QProgressBar {
                background-color: #F0F0F0;
                border: none;
                border-radius: 2px;
                height: 3px;
                text-align: center;
            }
            
            QProgressBar::chunk {
                background: #007BFF;
                border-radius: 2px;
            }
        """)
        self.setTextVisible(False)

class SplashScreen(QSplashScreen):
    def __init__(self):
        # Create a pixmap for the splash background
        pixmap = QPixmap(400, 200)  # Slightly increased height
        pixmap.fill(Qt.GlobalColor.white)
        super().__init__(pixmap)
        
        # Create layout widget
        layout_widget = QWidget(self)
        layout = QVBoxLayout(layout_widget)
        layout.setContentsMargins(30, 30, 30, 30)  # Increased padding
        layout.setSpacing(10)  # Adjusted spacing
        
        # Add product name and title
        product_name = QLabel("ANPD VISION")
        product_name.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: bold;
                color: #2c3e50;
                font-family: 'Segoe UI', Arial, sans-serif;
                padding-bottom: 5px;
            }
        """)
        product_name.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(product_name)
        
        # Add subtitle
        title = QLabel("Automatic License Plate Detection")
        title.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #7f8c8d;
                font-family: 'Segoe UI', Arial, sans-serif;
                margin-bottom: 10px;
            }
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(title)
        
        # Add spacer for better vertical alignment
        layout.addSpacing(10)
        
        # Progress container with improved styling
        progress_container = QWidget()
        progress_layout = QVBoxLayout(progress_container)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(8)  # Increased spacing
        
        # Progress header with better alignment
        progress_header = QWidget()
        header_layout = QHBoxLayout(progress_header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)  # Increased spacing
        
        # Modern progress bar
        self.progress_bar = ModernProgressBar()
        header_layout.addWidget(self.progress_bar, stretch=1)  # Added stretch
        
        # Percentage label with improved styling
        self.percentage_label = QLabel("0%")
        self.percentage_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #2c3e50;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
                min-width: 45px;
            }
        """)
        header_layout.addWidget(self.percentage_label)
        
        progress_layout.addWidget(progress_header)
        
        # Status label with improved styling
        self.status_label = QLabel("Initializing...")
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #7f8c8d;
                font-family: 'Segoe UI', Arial, sans-serif;
                padding: 0px 2px;  /* Added horizontal padding */
                background: transparent;  /* Ensure transparent background */
            }
        """)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        progress_layout.addWidget(self.status_label)
        
        layout.addWidget(progress_container)
        
        # Position the layout widget
        layout_widget.setGeometry(0, 0, 400, 200)
        
        # Set window style
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        
    def update_progress(self, value, status=""):
        """Update progress bar value and status text"""
        self.progress_bar.setValue(value)
        self.percentage_label.setText(f"{value}%")
        if status:
            self.status_label.setText(status)
        self.repaint()
        
    def paintEvent(self, event):
        """Custom paint event to add shadow and border"""
        super().paintEvent(event)
        painter = QPainter(self)
        
        # Draw white background with rounded corners
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor("#FFFFFF"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 8, 8)
        
        # Draw subtle border
        painter.setPen(QColor("#E0E0E0"))
        painter.drawRoundedRect(0, 0, self.width() - 1, self.height() - 1, 8, 8) 