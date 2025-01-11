
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,QLineEdit, QPushButton, QComboBox, QCheckBox)
from PyQt6.QtCore import Qt
import json  # Add this import

class RTSPStreamDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("RTSP Stream Connection")
        self.setMinimumWidth(500)

        with open('../config.json') as config_file:  # Load config
            config = json.load(config_file)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Add URL input
        url_layout = QHBoxLayout()
        url_label = QLabel("RTSP URL:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("rtsp://username:password@ip:port/stream")
        self.url_input.setText(config['rtsp_url'])  # Set RTSP URL from config
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        
        # Add quality settings
        quality_layout = QHBoxLayout()
        
        # Protocol selection
        protocol_label = QLabel("Transport Protocol:")
        self.protocol_combo = QComboBox()
        self.protocol_combo.addItems(["TCP"])
        self.protocol_combo.setCurrentText("TCP")  # TCP is more reliable for quality
        quality_layout.addWidget(protocol_label)
        quality_layout.addWidget(self.protocol_combo)
        
        # Add buttons
        button_layout = QHBoxLayout()
        self.connect_button = QPushButton("Connect")
        self.cancel_button = QPushButton("Cancel")
        button_layout.addWidget(self.connect_button)
        button_layout.addWidget(self.cancel_button)
        
        # Add layouts to main layout
        layout.addLayout(url_layout)
        layout.addLayout(quality_layout)
        layout.addLayout(button_layout)
        
        # Connect signals
        self.connect_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
    
    def get_settings(self):
        """Returns dictionary of all stream settings"""
        return {
            'url': self.url_input.text().strip(),
            'protocol': self.protocol_combo.currentText()
        }