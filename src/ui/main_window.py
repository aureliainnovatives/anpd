from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QHBoxLayout, QMessageBox, QToolBar, QInputDialog, QMenu, QSizePolicy, QLineEdit, QApplication, QDialog)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QImage, QIcon
import os
from pathlib import Path
from ui.rtsp_handler import RTSPHandler
from detector import LicensePlateDetector
from .rtsp_stream_dialog import RTSPStreamDialog
from detector_worker import DetectionWorker
from .stream_grid import StreamGrid
from data_sender import DataSender
import json
import sys
from utils.logger import setup_logger
from .pin_dialog import PinDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.logger = setup_logger('MainWindow')
        self.logger.info("Initializing Main Window")
        
        # Set window icon using ico file
        if getattr(sys, 'frozen', False):
            icon_path = os.path.join(sys._MEIPASS, 'icons', 'app_icon.ico')
        else:
            icon_path = os.path.join(Path(__file__).resolve().parent.parent.parent, 'icons', 'app_icon.ico')
        
        app_icon = QIcon(icon_path)
        self.setWindowIcon(app_icon)
        QApplication.instance().setWindowIcon(app_icon)
        
        # Update window title
        self.setWindowTitle("ANPD VISION")
        self.setMinimumSize(1200, 800)
        
        # Load only essential config
        self.config = self._load_config()
        
        # Create toolbar before initializing UI
        self._create_toolbar()
        
        # Initialize UI components
        self._init_ui()
        
        # Initialize other attributes but don't load heavy components yet
        self.detection_workers = {}
        self.detector = None  # Will be initialized later in initialize_detector()
        
    def _create_toolbar(self):
        """Create main toolbar"""
        self.toolbar = QToolBar()
        self.toolbar.setMovable(False)
        self.toolbar.setStyleSheet("""
            QToolBar {
                background-color: #000000;
                border: none;
                padding: 0px;
                spacing: 15px;
                min-height: 40px;
                max-height: 40px;
            }
        """)
        self.addToolBar(self.toolbar)
        
        # Create a container widget for better alignment
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(16, 0, 16, 0)
        container_layout.setSpacing(15)
        
        # Left section
        left_section = QHBoxLayout()
        left_section.setSpacing(15)
        
        # Add product name label
        product_label = QLabel("ANPD VISION")
        product_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 16px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        left_section.addWidget(product_label)
        
        # Add Stream button
        add_stream_btn = QPushButton("+ Add Stream")
        add_stream_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 0px 16px;
                border-radius: 3px;
                font-weight: bold;
                font-size: 12px;
                min-height: 28px;
                max-height: 28px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        add_stream_btn.clicked.connect(self._add_new_stream)
        left_section.addWidget(add_stream_btn)

        # Add Layout button
        layout_btn = QPushButton("⧉ Layout")
        layout_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a5568;
                color: white;
                border: none;
                padding: 0px 16px;
                border-radius: 3px;
                font-weight: bold;
                font-size: 12px;
                min-height: 28px;
                max-height: 28px;
            }
            QPushButton:hover {
                background-color: #3a4458;
            }
            QPushButton::menu-indicator {
                width: 0px;  /* This removes the dropdown arrow */
            }
        """)
        
        # Create layout menu with styling
        layout_menu = QMenu(self)
        layout_menu.setStyleSheet("""
            QMenu {
                background-color: #2d3748;
                border: 1px solid #1a202c;
                border-radius: 3px;
                padding: 4px;
            }
            QMenu::item {
                padding: 4px 16px;
                color: white;
                border-radius: 2px;
                font-size: 12px;
            }
            QMenu::item:selected {
                background-color: #4a5568;
            }
        """)
        
        layouts = ["2x2", "2x3"]
        for layout in layouts:
            action = layout_menu.addAction(layout)
            action.triggered.connect(lambda checked, l=layout: self._change_layout(l))
        
        layout_btn.setMenu(layout_menu)
        left_section.addWidget(layout_btn)
        
        # Add left section to main layout
        container_layout.addLayout(left_section)
        
        # Center section with search
        center_section = QHBoxLayout()
        center_section.setSpacing(0)
        
        # Create search container with fixed width
        search_container = QWidget()
        search_container.setFixedWidth(300)  # Increased fixed width
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(0)
        
        # Create search box with improved styling
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search")
        self.search_box.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #cbd5e0;
                border-radius: 4px;
                padding: 4px 28px;
                padding-left: 10px;
                font-size: 12px;
                min-height: 22px;
                max-height: 22px;
            }
            QLineEdit:focus {
                border-color: #3498db;
                outline: none;
                background-color: #ffffff;
            }
            QLineEdit::placeholder {
                color: #a0aec0;
            }
        """)
        
        # Add search icon
        search_icon = QIcon(os.path.join(self._get_icons_dir(), 'search.png'))
        search_action = self.search_box.addAction(search_icon, QLineEdit.ActionPosition.LeadingPosition)
        
        # Add clear button
        clear_icon = QIcon(os.path.join(self._get_icons_dir(), 'close.png'))
        clear_action = self.search_box.addAction(clear_icon, QLineEdit.ActionPosition.TrailingPosition)
        clear_action.triggered.connect(self.search_box.clear)
        self.search_box.textChanged.connect(
            lambda text: clear_action.setVisible(bool(text))
        )
        clear_action.setVisible(False)
        
        # Connect search functionality
        self.search_box.textChanged.connect(self._filter_streams)
        
        # Add search box to layout
        search_layout.addWidget(self.search_box)
        
        # Create a container for the count label with fixed positioning
        count_container = QWidget()
        count_container.setFixedSize(120, 28)  # Increased width to accommodate text
        
        # Add search count label with absolute positioning
        self.search_count_label = QLabel(count_container)
        self.search_count_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 11px;
                padding: 0px 8px;
                background-color: #4a5568;
                border-radius: 2px;
                margin-left: 8px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        self.search_count_label.hide()
        self.search_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Position the count label absolutely
        self.search_count_label.setGeometry(0, 4, 110, 20)  # Increased width
        
        # Initialize with total count display
        total_streams = len(self.config['streams'])
        self.search_count_label.setText(f"Total {total_streams}")  # Show total initially
        self.search_count_label.show()
        
        # Add containers to center section
        center_section.addWidget(search_container)
        center_section.addWidget(count_container)
        
        # Add center section to main layout with stretches for centering
        container_layout.addStretch(1)
        container_layout.addLayout(center_section)
        container_layout.addStretch(1)
        
        # Right section
        right_section = QHBoxLayout()
        
        # Add company label
        company_label = QLabel("An AI Product by Aurelia Innovatives Pvt. Ltd.")
        company_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 12px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        right_section.addWidget(company_label)
        
        # Add right section to main layout
        container_layout.addLayout(right_section)

        # Add the container to the toolbar
        self.toolbar.addWidget(container)

    def _add_new_stream(self):
        """Handle adding a new stream"""
        try:
            # Get the highest existing stream number
            existing_streams = [int(s['id'].replace('stream', '')) 
                              for s in self.config['streams'] 
                              if s['id'].startswith('stream')]
            new_stream_num = max(existing_streams, default=0) + 1
            new_stream_id = f"stream{new_stream_num}"
            
            # Create initial stream config
            new_stream = {
                "id": new_stream_id,
                "rtsp_url": "",
                "enabled": False,
                "detection_region": {
                    "enabled": True,
                    "x1": 0.4,
                    "y1": 0.3,
                    "x2": 0.7,
                    "y2": 0.8
                },
                "data_sender": {
                    "host": "localhost",
                    "port": 8080 + new_stream_num
                }
            }
            
            # Create and show settings dialog
            dialog = RTSPStreamDialog(self, new_stream_id)
            # Temporarily add the new stream config for the dialog
            self.config['streams'].append(new_stream)
            
            if dialog.exec():
                settings = dialog.get_settings()
                if settings and settings['url']:  # Ensure URL is provided
                    # Update stream config with dialog settings
                    new_stream['rtsp_url'] = settings['url']
                    new_stream['enabled'] = True
                    new_stream['detection_region'] = settings['detection_region']
                    new_stream['data_sender'] = settings['data_sender']
                    
                    # Add to UI
                    stream_widget = self.stream_grid.add_stream(new_stream_id)
                    stream_widget.settingsClicked.connect(self._show_stream_settings)
                    stream_widget.disableAllClicked.connect(self._disable_all)
                    
                    # Update stream information display
                    stream_widget.update_stream_info(new_stream)
                    
                    # Save config
                    self._save_config()
                    
                    # Automatically start the new stream
                    self._start_stream(new_stream_id, new_stream)
                else:
                    # Remove the stream config if no URL provided
                    self.config['streams'].remove(new_stream)
                    QMessageBox.warning(self, "Warning", "Stream URL is required to add a new stream.")
            else:
                # Remove the stream config if dialog was cancelled
                self.config['streams'].remove(new_stream)
            
        except Exception as e:
            self.logger.error(f"Error adding new stream: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to add new stream: {str(e)}")
        
    def initialize_detector(self):
        """Initialize the detector - called during splash screen"""
        try:
            if getattr(sys, 'frozen', False):
                # If running as exe
                model_path = os.path.join(os.path.dirname(sys.executable), 'models', 'NPDv1.0.pt')
            else:
                # If running as script
                model_path = os.path.join(Path(__file__).resolve().parent.parent.parent, 
                                        self.config.get('model_path', 'models/NPDv1.0.pt'))
            
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model file not found: {model_path}")
            
            self.detector = LicensePlateDetector(model_path)
        except Exception as e:
            self.logger.error(f"Failed to initialize detector: {str(e)}")
            raise
            
    def load_streams(self):
        """Load stream configurations - called during splash screen"""
        try:
            streams = self.config.get('streams', [])
            for stream_config in streams:
                stream_id = stream_config['id']
                stream_widget = self.stream_grid.add_stream(stream_id)
                
                # Connect signals
                stream_widget.settingsClicked.connect(self._show_stream_settings)
                stream_widget.disableAllClicked.connect(self._disable_all)
                
                # Update stream widget with config before starting
                stream_widget.update_stream_info(stream_config)
                
                # Only start stream if both enabled flags are true and has URL
                if (stream_config.get('enabled', True) and 
                    stream_config.get('detection_region', {}).get('enabled', True) and 
                    stream_config.get('rtsp_url')):
                    self._start_stream(stream_id, stream_config)
                else:
                    # Ensure disabled state is shown
                    stream_widget.update_disable_all_state(True)
                    stream_widget.set_status("Stream & Detection Stopped")

        except Exception as e:
            self.logger.error(f"Failed to load streams: {str(e)}")
            raise
        
    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create stream grid
        self.stream_grid = StreamGrid()
        main_layout.addWidget(self.stream_grid)
        
        # Status bar
        self.status_label = QLabel("Status: Ready")
        main_layout.addWidget(self.status_label)

    def _load_config(self):
        config_path = self._get_config_path()
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            return {}
            
    def _load_streams_from_config(self):
        """Initialize streams from config"""
        streams = self.config.get('streams', [])
        for stream_config in streams:
            stream_id = stream_config['id']
            stream_widget = self.stream_grid.add_stream(stream_id)
            
            # Connect signals
            stream_widget.settingsClicked.connect(self._show_stream_settings)
            stream_widget.disableAllClicked.connect(self._disable_all)
            
            # If enabled in config, start the stream
            if stream_config.get('enabled') and stream_config.get('rtsp_url'):
                self._start_stream(stream_id, stream_config)
                
    def _verify_pin(self, action="modify"):
        """Verify PIN before allowing settings modification or application closure"""
        dialog = PinDialog(action, self)
        return dialog.exec() == QDialog.DialogCode.Accepted

    def _show_stream_settings(self, stream_id):
        """Show settings dialog for stream"""
        # Verify PIN before showing settings
        if not self._verify_pin("modify"):
            return
        
        try:
            dialog = RTSPStreamDialog(self, stream_id)
            
            if dialog.exec():
                settings = dialog.get_settings()
                if settings:  # Check if settings are valid
                    # Update config
                    stream_config = next((s for s in self.config['streams'] 
                                        if s['id'] == stream_id), None)
                    
                    if stream_config:
                        # Store old settings in case we need to revert
                        old_settings = stream_config.copy()
                        
                        try:
                            # Update stream configuration
                            stream_config['rtsp_url'] = settings['url']
                            stream_config['enabled'] = bool(settings['url'])
                            stream_config['detection_region'] = settings['detection_region']
                            stream_config['data_sender'] = settings['data_sender']
                            
                            # Save config first
                            self._save_config()
                            
                            # Get the stream widget
                            stream_widget = self.stream_grid.get_stream(stream_id)
                            if stream_widget:
                                # Update stream widget display
                                stream_widget.update_stream_info(stream_config)
                                
                                # If RTSP URL changed, restart the stream
                                if old_settings.get('rtsp_url') != settings['url']:
                                    # Stop the old stream first
                                    if stream_id in self.detection_workers:
                                        worker = self.detection_workers[stream_id]
                                        # Disconnect all signals before stopping
                                        try:
                                            worker.frame_ready.disconnect()
                                            worker.error.disconnect()
                                            worker.status_changed.disconnect()
                                            worker.finished.disconnect()
                                        except Exception:
                                            pass
                                        
                                        # Stop the worker in a non-blocking way
                                        QTimer.singleShot(0, lambda: self._stop_stream(stream_id))
                                        
                                        # Start new stream after a short delay
                                        if settings['url']:
                                            QTimer.singleShot(1000, lambda: self._start_stream(stream_id, stream_config))
                                else:
                                    # If only detection region or data sender changed, update without restart
                                    if stream_id in self.detection_workers:
                                        worker = self.detection_workers[stream_id]
                                        worker.update_config(stream_config)
                            
                        except Exception as e:
                            # Revert changes if something goes wrong
                            stream_config.update(old_settings)
                            self._save_config()
                            self.logger.error(f"Error updating stream {stream_id}: {str(e)}")
                            if stream_widget:
                                stream_widget.set_status(f"Error: {str(e)}")
                            
        except Exception as e:
            self.logger.error(f"Error showing settings dialog: {str(e)}")

    def _disable_all(self, stream_id):
        """Toggle stream and detection state"""
        try:
            # Get the stream widget and config
            stream_widget = self.stream_grid.get_stream(stream_id)
            stream_config = next((s for s in self.config['streams'] 
                                if s['id'] == stream_id), None)
            
            if not stream_config:
                return

            # Get current state
            is_currently_enabled = stream_config.get('enabled', True) and \
                                 stream_config.get('detection_region', {}).get('enabled', True)
            
            # Verify PIN before any state change (both stop and start)
            if not self._verify_pin("modify"):
                return
            
            if is_currently_enabled:
                # Disable everything
                if stream_id in self.detection_workers:
                    self._stop_stream(stream_id)

                stream_config['enabled'] = False
                stream_config['detection_region']['enabled'] = False
                stream_widget.set_status("Stream & Detection Disabled")
                
                # Update UI to show stopped state
                stream_widget.update_disable_all_state(True)
            else:
                # Enable everything
                stream_config['enabled'] = True
                stream_config['detection_region']['enabled'] = True
                
                # Start the stream if URL exists
                if stream_config.get('rtsp_url'):
                    self._start_stream(stream_id, stream_config)
                
                stream_widget.set_status("Stream & Detection Enabled")
                
                # Update UI to show running state
                stream_widget.update_disable_all_state(False)

            # Update config file
            self._save_config()

        except Exception as e:
            self.logger.error(f"Error toggling stream and detection {stream_id}: {str(e)}")
            # Reset button state on error
            stream_widget.update_disable_all_state(not is_currently_enabled)

    def _start_stream(self, stream_id, stream_config):
        """Start detection worker for stream with improved error handling"""
        if stream_id in self.detection_workers:
            return
        
        stream_widget = self.stream_grid.get_stream(stream_id)
        if not stream_widget:
            return
        
        try:
            # Update stream information display
            stream_widget.update_stream_info(stream_config)
            
            # Validate RTSP URL before creating worker
            if not stream_config.get('rtsp_url'):
                raise ValueError("No RTSP URL provided")
            
            worker = DetectionWorker(
                detector=self.detector,
                video_source=stream_config['rtsp_url'],
                stream_config=stream_config,
                is_camera=False
            )
            
            # Connect signals with error handling
            worker.frame_ready.connect(
                lambda frame: self._handle_frame_update(stream_id, frame),
                Qt.ConnectionType.QueuedConnection
            )
            worker.error.connect(
                lambda err: self._handle_stream_error(stream_id, err),
                Qt.ConnectionType.QueuedConnection
            )
            worker.status_changed.connect(
                lambda status: stream_widget.set_status(status),
                Qt.ConnectionType.QueuedConnection
            )
            worker.finished.connect(
                lambda: self._handle_stream_finished(stream_id),
                Qt.ConnectionType.QueuedConnection
            )
            
            self.detection_workers[stream_id] = worker
            worker.start()
            stream_widget.set_status("Connecting...")
            
        except Exception as e:
            self.logger.error(f"Failed to start stream {stream_id}: {str(e)}")
            stream_widget.set_status(f"Error: {str(e)}")

    def _handle_frame_update(self, stream_id, frame):
        """Handle frame updates with error checking"""
        try:
            stream_widget = self.stream_grid.get_stream(stream_id)
            if stream_widget:
                stream_widget.update_frame(frame)
        except Exception as e:
            self.logger.error(f"Error updating frame for stream {stream_id}: {str(e)}")
            self._handle_stream_error(stream_id, str(e))

    def _handle_stream_error(self, stream_id, error):
        """Handle stream errors with immediate UI update"""
        self.logger.error(f"Stream {stream_id} error: {error}")
        try:
            stream_widget = self.stream_grid.get_stream(stream_id)
            if stream_widget:
                stream_widget.set_status(f"Error: {error}")
        except Exception as e:
            self.logger.error(f"Error handling stream error: {str(e)}")

    def _handle_stream_finished(self, stream_id):
        """Handle stream completion"""
        self._stop_stream(stream_id)
        
    def closeEvent(self, event):
        """Clean up resources when closing"""
        try:
            # Verify PIN before closing
            if not self._verify_pin("close"):
                event.ignore()
                return
            
            # Show closing message
            QMessageBox.information(self, "Closing", "Application is shutting down, please wait...")
            
            # Process events to show the message
            QApplication.processEvents()
            
            # Stop all streams with timeout
            for stream_id in list(self.detection_workers.keys()):
                try:
                    self.logger.info(f"Stopping stream {stream_id}")
                    worker = self.detection_workers[stream_id]
                    
                    # Disconnect signals first
                    try:
                        worker.frame_ready.disconnect()
                        worker.error.disconnect()
                        worker.finished.disconnect()
                    except Exception:
                        pass  # Ignore if already disconnected
                    
                    # Stop the worker
                    worker.stop()
                    
                    # Wait with timeout
                    if not worker.wait(3000):  # 3 second timeout
                        self.logger.warning(f"Force terminating worker for stream {stream_id}")
                        worker.terminate()
                        worker.wait()
                    
                    del self.detection_workers[stream_id]
                    self.logger.info(f"Successfully stopped stream {stream_id}")
                    
                except Exception as e:
                    self.logger.error(f"Error stopping stream {stream_id}: {str(e)}")
            
            # Clear detector resources
            if hasattr(self, 'detector'):
                self.detector = None
            
            # Clear stream grid
            self.stream_grid.clear_all_streams()
            
            # Process any remaining events
            QApplication.processEvents()
            
            event.accept()
            
        except Exception as e:
            self.logger.error(f"Error during application shutdown: {str(e)}")
            event.accept()  # Force accept even if there's an error

    def _get_config_path(self):
        """Get the path to the config.json file."""
        if getattr(sys, 'frozen', False):  # Check if running as a bundled executable
            #return os.path.join(sys._MEIPASS, 'config.json')
            return os.path.join(os.path.dirname(sys.executable), 'config.json')
        else:
            return os.path.join(Path(__file__).resolve().parent.parent.parent, 'config.json')

    def _save_config(self):
        """Save current configuration to file"""
        config_path = self._get_config_path()
        try:
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")

    def _change_layout(self, layout):
        """Change the stream grid layout"""
        try:
            self.stream_grid.change_layout(layout)
            self.logger.info(f"Changed grid layout to {layout}")
        except Exception as e:
            self.logger.error(f"Error changing layout: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to change layout: {str(e)}")

    def _filter_streams(self, search_text):
        """Filter streams based on search text"""
        try:
            search_text = search_text.lower().strip()
            
            # Update filtered streams list
            filtered_streams = []
            for stream_id, stream_widget in self.stream_grid.streams.items():
                stream_config = next((s for s in self.config['streams'] if s['id'] == stream_id), None)
                if not stream_config:
                    continue

                searchable_text = f"{stream_id} {stream_config.get('rtsp_url', '')}".lower()
                if not search_text or search_text in searchable_text:
                    filtered_streams.append(stream_widget)

            # Update the filtered streams list in grid
            self.stream_grid.filtered_streams = filtered_streams

            # Update count label with context-aware text
            total_streams = len(self.stream_grid.streams)
            visible_count = len(filtered_streams)
            
            if search_text:
                self.search_count_label.setText(f"Found {visible_count}/{total_streams}")
            else:
                self.search_count_label.setText(f"Total {total_streams}")

            self.search_count_label.show()

            # Reorganize grid only if needed
            self.stream_grid._reorganize_grid(filter_active=bool(search_text))

        except Exception as e:
            self.logger.error(f"Error in filter_streams: {str(e)}")

    def showEvent(self, event):
        """Override showEvent to set focus to search box"""
        super().showEvent(event)
        # Set focus to search box after a short delay
        QTimer.singleShot(100, lambda: self.search_box.setFocus())

    def _stop_stream(self, stream_id):
        """Stop detection worker for stream"""
        try:
            if stream_id in self.detection_workers:
                worker = self.detection_workers[stream_id]
                
                # Set running flag to False first
                worker.running = False
                
                # Stop the worker in a non-blocking way
                def cleanup():
                    try:
                        worker.stop()
                        worker.wait(1000)  # Wait with timeout
                        del self.detection_workers[stream_id]
                    except Exception as e:
                        self.logger.error(f"Error cleaning up worker: {str(e)}")
                
                # Execute cleanup in a non-blocking way
                QTimer.singleShot(0, cleanup)
                
                # Update stream widget status
                stream_widget = self.stream_grid.get_stream(stream_id)
                if stream_widget:
                    stream_widget.set_status("Stopped")
                
        except Exception as e:
            self.logger.error(f"Error stopping stream {stream_id}: {str(e)}")

    def _get_icons_dir(self):
        if getattr(sys, 'frozen', False):
            return os.path.join(sys._MEIPASS, 'icons')
        return os.path.join(Path(__file__).resolve().parent.parent.parent, 'icons')

