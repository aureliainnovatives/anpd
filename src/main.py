# import sys
# from ui.main_window import MainWindow
# from PyQt6.QtWidgets import QApplication

# def main():
#     app = QApplication(sys.argv)
#     window = MainWindow()
#     window.show()
#     sys.exit(app.exec())

# if __name__ == "__main__":
#     main()


import sys
from ui.main_window import MainWindow
from PyQt6.QtWidgets import QApplication, QMessageBox
from datetime import datetime
from PyQt6.QtCore import QTimer  # Import QTimer for periodic checks
import os
import json
from pathlib import Path

def _get_config_path():
    """Get the path to the config.json file."""
    if getattr(sys, 'frozen', False):  # Check if running as a bundled executable
        return os.path.join(sys._MEIPASS, 'config.json')
    else:
        return os.path.join(Path(__file__).resolve().parent.parent.parent, 'config.json')

# Load config
config_path = _get_config_path()
try:
    with open(config_path, 'r') as f:
        config = json.load(f)
except Exception as e:
    print(f"Error loading config: {e}")

def show_expiration_message():
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setWindowTitle("Application Expired")
    msg.setText("This application has expired and can no longer be used.")
    msg.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg.exec()

def check_expiration(use_gui=False):
    expiration_date = datetime(2025, 4, 25, 23, 59)
    if datetime.now() > expiration_date:
        if use_gui:
            show_expiration_message()
            QApplication.quit()
        else:
            print("Application has expired. Please contact support.", file=sys.stderr)
            sys.exit(1)
        return True
    return False

def main():
    app = QApplication(sys.argv)  # Create QApplication first
    
    # Now safe to use GUI elements
    if check_expiration(use_gui=True):
        sys.exit(1)
    
    window = MainWindow()
    
    timer = QTimer()
    timer.timeout.connect(lambda: check_expiration(use_gui=True))
    timer.start(10000)

    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()