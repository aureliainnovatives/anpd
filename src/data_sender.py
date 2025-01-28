import socket
import os
import struct  # Import struct for packing data
import json  # Import json for serializing header

class DataSender:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def send_data(self, vehicle_image_path, plate_image_path, txt_path):
        try:
            # Create a socket connection
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
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

        except Exception as e:
            print(f"Error sending data: {e}") 