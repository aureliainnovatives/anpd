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
from PyQt6.QtWidgets import QApplication, QMessageBox, QDialog
from datetime import datetime
from PyQt6.QtCore import QTimer, Qt
import os
import json
from pathlib import Path
from ui.splash_screen import SplashScreen
import time
from PyQt6.QtGui import QIcon
from utils.license_manager import LicenseManager
import tkinter as tk
from tkinter import messagebox
from ui.connection_retry_dialog import ConnectionRetryDialog
from ui.main_window import MainWindow  # Import MainWindow at the top

# Only import what's needed immediately
def _get_config_path():
    """Get the path to the config.json file."""
    if getattr(sys, 'frozen', False):
        # Always use config from exe directory
        return os.path.join(os.path.dirname(sys.executable), 'config.json')
    else:
        # Development mode
        return os.path.join(Path(__file__).resolve().parent.parent, 'config.json')

def show_expiration_message():
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setWindowTitle("Application Expired")
    msg.setText("This application has expired and is no longer accessible. Please contact the administrator for assistance.")
    msg.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg.exec()

def check_expiration(use_gui=False):
    expiration_date = datetime(2025, 8, 19, 23, 59)
    if datetime.now() > expiration_date:
        if use_gui:
            show_expiration_message()
            QApplication.quit()
        else:
            print("Application has expired. Please contact support.", file=sys.stderr)
            sys.exit(1)
        return True
    return False

def load_heavy_imports():
    """Load heavy imports and return them"""
    return MainWindow

def initialize_app(splash):
    """Initialize application components with progress updates"""
    try:
        app = QApplication.instance()
        
        # Update splash immediately
        splash.update_progress(5, "Loading configuration...")
        app.processEvents()
        
        # Load config
        config_path = _get_config_path()
        with open(config_path, 'r') as f:
            config = json.load(f)
            
        # Create main window instance
        splash.update_progress(40, "Creating main window...")
        app.processEvents()
        window = MainWindow()  # Create MainWindow directly since it's imported at the top
        
        # Initialize detector and models
        splash.update_progress(60, "Initializing detection models...")
        app.processEvents()
        window.initialize_detector()
        
        # Load stream configurations
        splash.update_progress(80, "Loading stream configurations...")
        app.processEvents()
        window.load_streams()
        
        # Final setup
        splash.update_progress(100, "Ready!")
        app.processEvents()
        
        return window
        
    except Exception as e:
        splash.update_progress(100, f"Error: {str(e)}")
        app.processEvents()
        raise e

def get_icon_path():
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, 'icons', 'app_icon.ico')
    else:
        return os.path.join(Path(__file__).resolve().parent.parent, 'icons', 'app_icon.ico')

def show_error_and_exit(message):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setWindowTitle("Error")
    msg.setText(message)
    msg.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg.exec()
    sys.exit(1)

def main():
    try:
        app = QApplication(sys.argv)
        
        # Set application icon using ico file
        app_icon = QIcon(get_icon_path())
        app.setWindowIcon(app_icon)
        QApplication.setWindowIcon(app_icon)
        
        # Initialize license manager
        license_manager = LicenseManager()
        
        # First check if we have a valid license
        is_valid, message = license_manager.verify_license()
        
        # Check for expired license first
        if not is_valid and "expired" in message.lower():
            QMessageBox.warning(None, "License Expired", 
                "Your license has expired. The application will now close.\nPlease contact the administrator to activate the application.")
            return
            
        if is_valid:
            print("License verified successfully:", message)
        else:
            # Show connection retry dialog for device registration
            retry_dialog = ConnectionRetryDialog(max_retries=3, retry_interval=3)
            retry_dialog.retry_complete.connect(
                lambda success, msg: show_error_and_exit(msg) if not success else None
            )
            retry_dialog.show()
            retry_dialog.start_retry_sequence(license_manager.register_device)
            
            if retry_dialog.exec() != QDialog.DialogCode.Accepted:
                show_error_and_exit("Failed to register device with license server")
            
            # Show license window if invalid
            if not license_manager.check_license():
                show_error_and_exit("License validation failed")
        
        # Only show splash screen and continue if license is valid
        splash = SplashScreen()
        splash.show()
        
        # Initialize app and get main window
        window = initialize_app(splash)
        
        # Show main window and close splash screen
        window.show()
        splash.finish(window)
        
        sys.exit(app.exec())
        
    except Exception as e:
        show_error_and_exit(f"Application initialization error: {str(e)}")

if __name__ == "__main__":
    main()