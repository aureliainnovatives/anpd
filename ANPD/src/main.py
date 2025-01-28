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

def check_expiration():
    # Define the expiration date and time
    expiration_date = datetime(2025, 2, 10, 23, 59)  # Set your desired expiration date and time
    
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
    timer.start(6000)  # Check every 6 seconds

    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()