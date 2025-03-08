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
from PyQt6.QtWidgets import QApplication, QMessageBox
from datetime import datetime
from PyQt6.QtCore import QTimer
import os
import json
from pathlib import Path
from ui.splash_screen import SplashScreen
import time
from PyQt6.QtGui import QIcon

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
    expiration_date = datetime(2025, 3, 19, 23, 59)
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
    from ui.main_window import MainWindow
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
            
        # Import heavy modules
        splash.update_progress(20, "Loading core components...")
        app.processEvents()
        MainWindow = load_heavy_imports()
        
        # Create main window instance
        splash.update_progress(40, "Creating main window...")
        app.processEvents()
        window = MainWindow()
        
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
    return os.path.join(Path(__file__).resolve().parent.parent, 'icons', 'app_icon.ico')

def main():
    app = QApplication(sys.argv)
    
    # Set application icon using ico file
    app_icon = QIcon(get_icon_path())
    app.setWindowIcon(app_icon)
    QApplication.setWindowIcon(app_icon)
    
    try:
        # Check expiration before showing splash
        if check_expiration(use_gui=True):
            sys.exit(1)
        
        # Create and show splash screen immediately
        splash = SplashScreen()
        splash.show()
        app.processEvents()
        
        # Small delay to ensure splash is visible
        time.sleep(0.1)
        
        # Initialize app and get main window
        window = initialize_app(splash)
        
        # Setup expiration check timer
        timer = QTimer()
        timer.timeout.connect(lambda: check_expiration(use_gui=True))
        timer.start(10000)
        
        # Show main window and close splash
        window.show()
        splash.finish(window)
        
        sys.exit(app.exec())
        
    except Exception as e:
        QMessageBox.critical(None, "Initialization Error", 
                           f"Failed to initialize application: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()