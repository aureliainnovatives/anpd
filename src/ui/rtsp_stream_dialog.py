from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox, QMessageBox, QGroupBox, QFormLayout, QDoubleSpinBox)
import json  # Add this import
from pathlib import Path
import os
import sys

def _get_config_path():
    """Get the path to the config.json file."""
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), 'config.json')
    else:
        return os.path.join(Path(__file__).resolve().parent.parent.parent, 'config.json')

class RTSPStreamDialog(QDialog):
    def __init__(self, parent=None, stream_id=None):
        super().__init__(parent)
        self.stream_id = stream_id
        self.config = parent.config
        
        # Get stream config
        self.stream_config = next((s for s in self.config['streams'] 
                                 if s['id'] == stream_id), None)
        
        self.setWindowTitle(f"Stream Settings - {stream_id}")
        self.setMinimumWidth(600)  # Set minimum width
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)  # Add spacing between elements
        
        # Create horizontal layout for groups
        groups_layout = QHBoxLayout()
        groups_layout.setSpacing(15)  # Add spacing between groups
        
        # Left column - RTSP URL and Data Sender
        left_column = QVBoxLayout()
        left_column.setSpacing(10)
        
        # RTSP URL Group
        url_group = QGroupBox("RTSP URL")
        url_layout = QVBoxLayout()
        url_layout.setContentsMargins(10, 10, 10, 10)  # Add padding
        self.url_input = QLineEdit()
        if self.stream_config:
            self.url_input.setText(self.stream_config.get('rtsp_url', ''))
        url_layout.addWidget(self.url_input)
        url_group.setLayout(url_layout)
        left_column.addWidget(url_group)
        
        # Data Sender Group
        sender_group = QGroupBox("C# Application Settings")
        sender_layout = QFormLayout()
        sender_layout.setContentsMargins(10, 10, 10, 10)  # Add padding
        
        # Host input
        self.host_input = QLineEdit()
        if self.stream_config and 'data_sender' in self.stream_config:
            self.host_input.setText(self.stream_config['data_sender'].get('host', 'localhost'))
        else:
            self.host_input.setText('localhost')
        sender_layout.addRow("Host:", self.host_input)
        
        # Port input
        self.port_input = QLineEdit()
        if self.stream_config and 'data_sender' in self.stream_config:
            self.port_input.setText(str(self.stream_config['data_sender'].get('port', 8080)))
        else:
            self.port_input.setText('8080')
        sender_layout.addRow("Port:", self.port_input)
        
        sender_group.setLayout(sender_layout)
        left_column.addWidget(sender_group)
        
        # Add left column to groups layout
        groups_layout.addLayout(left_column)
        
        # Right column - Detection Region
        # Detection Region Group
        region_group = QGroupBox("Detection Region")
        region_layout = QVBoxLayout()
        region_layout.setContentsMargins(10, 10, 10, 10)  # Add padding
        
        # Enable/disable detection region
        self.region_enabled = QCheckBox("Enable Detection Region")
        if self.stream_config and 'detection_region' in self.stream_config:
            self.region_enabled.setChecked(self.stream_config['detection_region'].get('enabled', True))
        else:
            self.region_enabled.setChecked(True)
        region_layout.addWidget(self.region_enabled)
        
        # Region coordinates
        coord_layout = QFormLayout()
        coord_layout.setSpacing(10)  # Add spacing between form rows
        self.coord_inputs = {}
        
        for coord in ['x1', 'y1', 'x2', 'y2']:
            spinbox = QDoubleSpinBox()
            spinbox.setRange(0.0, 1.0)
            spinbox.setSingleStep(0.1)
            spinbox.setDecimals(2)
            spinbox.setFixedWidth(100)  # Set fixed width for spinboxes
            if self.stream_config and 'detection_region' in self.stream_config:
                spinbox.setValue(self.stream_config['detection_region'].get(coord, 0.0))
            self.coord_inputs[coord] = spinbox
            coord_layout.addRow(f"{coord.upper()}:", spinbox)
        
        region_layout.addLayout(coord_layout)
        region_group.setLayout(region_layout)
        
        # Add right column to groups layout
        groups_layout.addWidget(region_group)
        
        # Add groups layout to main layout
        main_layout.addLayout(groups_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 0)  # Add top margin
        save_button = QPushButton("Save")
        save_button.setFixedWidth(100)  # Set fixed width for buttons
        save_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.setFixedWidth(100)  # Set fixed width for buttons
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()  # Add stretch to push buttons to the right
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        main_layout.addLayout(button_layout)
        
    def get_settings(self):
        """Get the dialog settings"""
        try:
            # Validate port number
            port = int(self.port_input.text())
            if port < 1 or port > 65535:
                raise ValueError("Port must be between 1 and 65535")
                
            return {
                'url': self.url_input.text(),
                'data_sender': {
                    'host': self.host_input.text(),
                    'port': port
                },
                'detection_region': {
                    'enabled': self.region_enabled.isChecked(),
                    'x1': self.coord_inputs['x1'].value(),
                    'y1': self.coord_inputs['y1'].value(),
                    'x2': self.coord_inputs['x2'].value(),
                    'y2': self.coord_inputs['y2'].value()
                }
            }
        except ValueError as e:
            QMessageBox.critical(self, "Invalid Input", str(e))
            return None