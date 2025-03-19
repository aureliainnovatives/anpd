from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QMessageBox)
from PyQt6.QtCore import Qt

class PinDialog(QDialog):
    def __init__(self, action="modify", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Security Verification")
        self.setFixedWidth(300)
        self.action = action
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Message
        action_text = "modify settings" if self.action == "modify" else "close the application"
        message = QLabel(f"Enter PIN to {action_text}")
        message.setStyleSheet("font-size: 12px; margin-bottom: 10px;")
        layout.addWidget(message)
        
        # PIN input
        self.pin_input = QLineEdit()
        self.pin_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pin_input.setMaxLength(4)
        self.pin_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 14px;
            }
        """)
        layout.addWidget(self.pin_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        verify_btn = QPushButton("Verify")
        verify_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        verify_btn.clicked.connect(self.verify_pin)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(verify_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        # Set focus to PIN input
        self.pin_input.setFocus()
        
    def verify_pin(self):
        # Hardcoded PIN - you can change this to your desired PIN
        CORRECT_PIN = "5656"
        
        entered_pin = self.pin_input.text()
        if entered_pin == CORRECT_PIN:
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Incorrect PIN")
            self.pin_input.clear()
            self.pin_input.setFocus() 