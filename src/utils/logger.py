import logging
import os
import sys
from datetime import datetime
from pathlib import Path

def setup_logger(name):
    """Configure and return a logger instance"""
    
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(Path(__file__).resolve().parent.parent.parent, 'logs')
    if getattr(sys, 'frozen', False):
        # If running as exe, create logs next to exe
        logs_dir = os.path.join(os.path.dirname(sys.executable), 'logs')
    
    os.makedirs(logs_dir, exist_ok=True)
    
    # Create log filename with timestamp
    log_file = os.path.join(logs_dir, f'{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    
    # Configure logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Print log file location
    print(f"Log file created at: {log_file}")
    
    return logger 