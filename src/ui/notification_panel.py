from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon
import os
from datetime import datetime, timedelta

class NotificationPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        self.setFixedWidth(300)
        self.setStyleSheet("""
            QWidget {
                background-color: #2d3748;
                border: 1px solid #1a202c;
                border-radius: 4px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Header
        header = QLabel("License Status")
        header.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        layout.addWidget(header)
        
        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #4a5568;")
        layout.addWidget(line)
        
        # Status message
        self.status_label = QLabel()
        self.status_label.setStyleSheet("""
            QLabel {
                color: #e2e8f0;
                font-size: 12px;
            }
        """)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        # Days remaining
        self.days_label = QLabel()
        self.days_label.setStyleSheet("""
            QLabel {
                color: #f6ad55;
                font-size: 12px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.days_label)
        
        # Button container for activation button and spinner
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(8)
        
        # Activate button
        self.activate_btn = QPushButton("Activate License")
        self.activate_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 3px;
                font-weight: bold;
                font-size: 12px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        button_layout.addWidget(self.activate_btn)
        
        # Loading spinner
        self.spinner = QLabel()
        self.spinner.setFixedSize(16, 16)
        self.spinner.setStyleSheet("""
            QLabel {
                background-color: transparent;
            }
        """)
        self.spinner.hide()
        button_layout.addWidget(self.spinner)
        
        layout.addWidget(button_container)
        
        # Dismiss button
        self.dismiss_btn = QPushButton("Dismiss")
        self.dismiss_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a5568;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 3px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #3a4458;
            }
        """)
        layout.addWidget(self.dismiss_btn)
        
        # Add stretch to push everything up
        layout.addStretch()
        
        # Setup spinner animation
        self.spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.current_frame = 0
        self.spinner_timer = QTimer()
        self.spinner_timer.timeout.connect(self._update_spinner)
        
    def _update_spinner(self):
        """Update spinner animation frame"""
        self.current_frame = (self.current_frame + 1) % len(self.spinner_frames)
        self.spinner.setText(self.spinner_frames[self.current_frame])
        
    def start_loading(self):
        """Start the loading animation"""
        self.activate_btn.setEnabled(False)
        self.spinner.show()
        self.spinner_timer.start(80)  # Update every 80ms
        
    def stop_loading(self):
        """Stop the loading animation"""
        self.spinner_timer.stop()
        self.spinner.hide()
        self.activate_btn.setEnabled(True)
        
    def update_status(self, expiration_date):
        """Update the notification panel with license status"""
        if not expiration_date:
            self.status_label.setText("License Error")
            self.days_label.setText("Invalid license: Missing expiration date")
            self.activate_btn.setEnabled(True)
            self.dismiss_btn.setEnabled(False)
            return

        now = datetime.now()
        minutes_remaining = int((expiration_date - now).total_seconds() / 60)
        
        if minutes_remaining <= 0:
            self.status_label.setText("Your license has expired.")
            self.days_label.setText("Please activate a new license to continue using the application.")
            self.activate_btn.setEnabled(True)
            self.dismiss_btn.setEnabled(False)
        elif minutes_remaining <= 180:  # 3 hours
            self.status_label.setText("Your license is about to expire.")
            self.days_label.setText(f"{minutes_remaining} minutes remaining")
            self.activate_btn.setEnabled(True)
            self.dismiss_btn.setEnabled(True)
        else:
            self.status_label.setText("Your license is active.")
            self.days_label.setText(f"Expires in {minutes_remaining} minutes")
            self.activate_btn.setEnabled(False)
            self.dismiss_btn.setEnabled(True)