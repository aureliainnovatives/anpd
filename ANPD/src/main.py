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
from PyQt6.QtWidgets import QApplication
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

def check_expiration():
    # Define the expiration date and time
    expiration_date = datetime(2025, 2, 15, 23, 59)  # Set your desired expiration date and time
    
    # Check if the current date and time is past the expiration date
    if datetime.now() > expiration_date:
        print("This application has expired and cannot be run.")
        QApplication.quit()  # Exit the application if expired

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    
    # Set up a timer to check expiration every minute (60000 milliseconds)
    timer = QTimer()
    timer.timeout.connect(check_expiration)
    timer.start(20000)  # Check every 6 seconds

    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()