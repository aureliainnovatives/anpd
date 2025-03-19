import socket
import os
import struct  # Import struct for packing data
import json  # Import json for serializing header
from utils.logger import setup_logger

class DataSender:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.logger = setup_logger('DataSender')
        self.logger.info(f"Initialized DataSender for {host}:{port}")

    def send_data(self, vehicle_image_path, plate_image_path, txt_path):
        try:
            self.logger.info(f"Attempting to send data to {self.host}:{self.port}")
            # Create a socket connection
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                self.logger.debug(f"Connecting to {self.host}:{self.port}")
                s.connect((self.host, self.port))
                
                # Prepare the files to send
                files = [
                    (vehicle_image_path, "image/jpeg"),  # Assuming JPEG format
                    (plate_image_path, "image/jpeg"),
                    (txt_path, "text/plain")
                ]
                
                # Create a header with file metadata
                header = []
                for file_path, file_type in files:
                    file_size = os.path.getsize(file_path)
                    file_name = os.path.basename(file_path)
                    header.append({"Name": file_name, "Size": file_size, "Type": file_type})

                # Serialize header to JSON
                header_json = json.dumps(header).encode('utf-8')
                header_length = struct.pack('!I', len(header_json))  # Network byte order for header length

                # Send header length and header
                s.sendall(header_length)
                s.sendall(header_json)

                # Send each file
                for file_path, _ in files:
                    with open(file_path, 'rb') as f:
                        file_data = f.read()
                        s.sendall(file_data)
                
                self.logger.info(f"Successfully sent data to {self.host}:{self.port}")

        except Exception as e:
            self.logger.error(f"Error sending data to {self.host}:{self.port}: {str(e)}")
            raise 