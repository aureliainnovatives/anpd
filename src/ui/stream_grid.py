from PyQt6.QtWidgets import (QWidget, QGridLayout, QSizePolicy, 
                            QScrollArea, QFrame, QVBoxLayout, QLabel)
from PyQt6.QtCore import Qt
from .stream_widget import StreamWidget
from PyQt6.QtWidgets import QApplication

class StreamGrid(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create scroll area
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Create widget to hold the grid
        self.grid_widget = QWidget()
        self.layout = QGridLayout(self.grid_widget)
        self.layout.setSpacing(4)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Set the grid widget as the scroll area's widget
        self.scroll_area.setWidget(self.grid_widget)
        
        # Main layout to hold the scroll area
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.scroll_area)
        
        self.streams = {}
        self.maximized_stream = None
        self.current_layout = "2x2"
        self.filtered_streams = []  # Add this to track filtered streams
        
    def add_stream(self, stream_id):
        if stream_id in self.streams:
            return self.streams[stream_id]
            
        stream_widget = StreamWidget(stream_id)
        stream_widget.maximizeClicked.connect(self._handle_maximize)
        stream_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        self.streams[stream_id] = stream_widget
        self._reorganize_grid()
        
        return stream_widget
        
    def change_layout(self, layout_type):
        self.current_layout = layout_type
        if self.maximized_stream:
            self._handle_maximize(self.maximized_stream)
        self._reorganize_grid()
        
    def _reorganize_grid(self, filter_active=False):
        try:
            streams_to_show = self.filtered_streams if filter_active else self.streams.values()
            
            if not streams_to_show:
                if filter_active:
                    if not hasattr(self, 'no_results_label'):
                        self.no_results_label = QLabel("No matching streams found")
                        self.no_results_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        self.no_results_label.setStyleSheet("""
                            QLabel {
                                color: #666666;
                                font-size: 14px;
                                padding: 20px;
                            }
                        """)
                        self.layout.addWidget(self.no_results_label, 0, 0, 1, 1)
                    self.no_results_label.show()
                return

            if hasattr(self, 'no_results_label'):
                self.no_results_label.hide()

            # Get layout dimensions
            rows, cols = map(int, self.current_layout.split('x'))
            
            # Calculate sizes with proper spacing
            grid_spacing = 16
            scrollbar_width = 20
            self.layout.setSpacing(grid_spacing)
            self.layout.setContentsMargins(grid_spacing, grid_spacing, grid_spacing, grid_spacing)
            
            # Calculate stream sizes accounting for scrollbar and spacing
            available_width = self.scroll_area.width() - (cols + 1) * grid_spacing - scrollbar_width
            stream_width = max(320, available_width // cols)
            
            # Calculate height to maintain 4:3 aspect ratio for video plus space for header and status
            video_height = int(stream_width * 0.75)  # 4:3 aspect ratio
            total_height = video_height + 80  # Add space for header and status
            
            # Set grid widget width to match scroll area
            self.grid_widget.setFixedWidth(self.scroll_area.width() - scrollbar_width)
            
            # Update layout
            for widget in self.streams.values():
                widget.hide()
                widget.setParent(None)

            for idx, widget in enumerate(streams_to_show):
                row = idx // cols
                col = idx % cols
                widget.setMinimumSize(320, 240)
                widget.setMaximumSize(1920, 1080)
                widget.setFixedSize(stream_width, total_height)
                self.layout.addWidget(widget, row, col)
                widget.show()

            # Update grid widget minimum height
            num_visible = len(streams_to_show)
            actual_rows = (num_visible + cols - 1) // cols
            min_height = actual_rows * total_height + (actual_rows + 1) * grid_spacing
            self.grid_widget.setMinimumHeight(min_height)

        except Exception as e:
            print(f"Error in _reorganize_grid: {str(e)}")
        
    def _handle_maximize(self, stream_widget):
        if self.maximized_stream == stream_widget:
            # Restore grid layout
            self.maximized_stream = None
            stream_widget.is_maximized = False  
            self._reorganize_grid()
        else:
            # Maximize selected stream
            self.maximized_stream = stream_widget
            stream_widget.is_maximized = True
            
            # Hide other streams
            for widget in self.streams.values():
                if widget != stream_widget:
                    widget.hide()
            
            # Show maximized stream
            stream_widget.setFixedSize(self.width(), self.width() * 3 // 4)
            self.layout.addWidget(stream_widget, 0, 0)
            
    def get_stream(self, stream_id):
        return self.streams.get(stream_id)
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Reorganize grid when scroll area is resized
        self._reorganize_grid()

    def remove_stream(self, stream_id):
        """Remove a stream widget from the grid"""
        try:
            if stream_id in self.streams:
                # Get the widget to remove
                widget = self.streams[stream_id]
                
                # If this is the maximized stream, restore grid first
                if self.maximized_stream == widget:
                    self.maximized_stream = None
                
                # Remove from layout first
                self.layout.removeWidget(widget)
                
                # Disconnect all signals with error handling
                try:
                    widget.settingsClicked.disconnect()
                except Exception:
                    pass
                try:
                    widget.maximizeClicked.disconnect()
                except Exception:
                    pass
                try:
                    widget.deleteClicked.disconnect()
                except Exception:
                    pass
                
                # Hide the widget
                widget.hide()
                
                # Remove from streams dictionary
                del self.streams[stream_id]
                
                # Remove from filtered streams if present
                if widget in self.filtered_streams:
                    self.filtered_streams.remove(widget)
                
                # Schedule widget for deletion
                widget.deleteLater()
                
                # Process events to ensure widget cleanup
                QApplication.processEvents()
                
                # Show all remaining streams
                for remaining_widget in self.streams.values():
                    remaining_widget.show()
                
                # Reorganize remaining streams
                self._reorganize_grid()
                
        except Exception as e:
            print(f"Error removing stream {stream_id}: {str(e)}")

    def clear_all_streams(self):
        """Clear all streams and their resources"""
        try:
            # Hide all streams first
            for widget in self.streams.values():
                widget.hide()
                widget.setParent(None)
            
            # Clear the streams dictionary
            self.streams.clear()
            self.filtered_streams.clear()
            
            # Reset layout
            while self.layout.count():
                item = self.layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                
        except Exception as e:
            print(f"Error clearing streams: {str(e)}") 