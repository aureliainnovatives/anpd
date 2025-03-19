from PyQt6.QtWidgets import QSplashScreen, QProgressBar, QVBoxLayout, QWidget, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QPainter, QColor, QLinearGradient, QFont
import os
import sys
from pathlib import Path

class ModernProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(8)  # Set fixed height for the progress bar
        self.setStyleSheet("""
            QProgressBar {
                background-color: #F5F5F5;
                border: none;
                border-radius: 4px;
                height: 8px;
                text-align: center;
                margin: 0px;
                padding: 0px;
            }
            
            QProgressBar::chunk {
                background: #000000;
                border-radius: 4px;
            }
        """)
        self.setTextVisible(False)

class SplashScreen(QSplashScreen):
    def __init__(self, version="v1.2.5"):
        # Create a white background pixmap with extra space for anti-aliasing
        pixmap = QPixmap(400, 220)
        pixmap.fill(Qt.GlobalColor.transparent)  # Make it transparent initially
        super().__init__(pixmap)
        
        # Set window style and attributes
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)  # Enable transparency
        
        # Create main widget and layout
        self.layout_widget = QWidget(self)
        self.layout_widget.setObjectName("mainContainer")
        self.layout_widget.setStyleSheet("""
            #mainContainer {
                background-color: white;
                border-radius: 4px;
            }
        """)
        layout = QVBoxLayout(self.layout_widget)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(0)  # Set to 0 to control spacing manually
        
        # Add eye icon and product name in one row
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)
        
        # Eye icon
        eye_icon = QLabel()
        eye_icon.setPixmap(QPixmap(os.path.join(self._get_icons_dir(), 'app_icon.png')).scaled(24, 24))
        header_layout.addWidget(eye_icon)
        
        # Product name with version
        product_container = QWidget()
        product_layout = QHBoxLayout(product_container)
        product_layout.setContentsMargins(0, 0, 0, 0)
        product_layout.setSpacing(4)
        
        # Product name (larger)
        name_label = QLabel("ANPD VISION")
        name_label.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: bold;
                color: #000000;
            }
        """)
        product_layout.addWidget(name_label)
        
        # Version (same line, baseline aligned)
        version_label = QLabel(version)
        version_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #000000;
                margin-top: 10px;  /* Adjust this value to align with baseline */
            }
        """)
        product_layout.addWidget(version_label, 0, Qt.AlignmentFlag.AlignBaseline)  # Changed to AlignBaseline
        product_layout.addStretch()
        
        header_layout.addWidget(product_container)
        header_layout.addStretch()
        
        layout.addWidget(header_widget)
        
        # Add subtitle with specific margin
        subtitle = QLabel("Automatic License Plate Detection System")
        subtitle.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #666666;
                margin: 0px;
                padding: 0px;
            }
        """)
        layout.addWidget(subtitle)
        layout.addSpacing(5)  # Add specific space after subtitle
        
        # Progress section container
        progress_container = QWidget()
        progress_layout = QVBoxLayout(progress_container)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(0)  # Small space between progress bar and status
        
        # Add progress bar
        self.progress_bar = ModernProgressBar()
        progress_layout.addWidget(self.progress_bar)
        
        # Status label with progress percentage
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 0, 0, 0)
        
        self.status_label = QLabel("Loading core components...")
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #666666;
            }
        """)
        status_layout.addWidget(self.status_label)
        
        # Progress percentage label (replacing please_wait_label)
        self.progress_label = QLabel("20%")  # Initial value
        self.progress_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #666666;
            }
        """)
        status_layout.addWidget(self.progress_label, alignment=Qt.AlignmentFlag.AlignRight)
        
        progress_layout.addWidget(status_widget)
        layout.addWidget(progress_container)
        
        # Set the layout widget size
        self.layout_widget.setGeometry(0, 0, 400, 220)
        
    def _get_icons_dir(self):
        if getattr(sys, 'frozen', False):
            return os.path.join(sys._MEIPASS, 'icons')
        return os.path.join(Path(__file__).resolve().parent.parent.parent, 'icons')
        
    def update_progress(self, value, status=""):
        """Update progress bar value and status text"""
        self.progress_bar.setValue(value)
        self.progress_label.setText(f"{value}%")  # Update percentage text
        if status:
            self.status_label.setText(status)
        self.repaint()
        
    def paintEvent(self, event):
        """Custom paint event to add shadow and border"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw shadow (optional)
        # painter.setPen(Qt.PenStyle.NoPen)
        # painter.setBrush(QColor(0, 0, 0, 20))
        # painter.drawRoundedRect(self.rect().adjusted(3, 3, -3, -3), 12, 12)
        
        # Draw white background with rounded corners
        painter.setBrush(QColor("#FFFFFF"))
        painter.setPen(QColor("#E0E0E0"))
        painter.drawRoundedRect(0, 0, self.width() - 1, self.height() - 1, 12, 12) 