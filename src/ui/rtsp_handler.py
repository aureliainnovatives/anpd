# import cv2

# class RTSPHandler:
#     def __init__(self):
#         self.stream = None
        
#     def connect(self, url, protocol='TCP'):
#         """Connect to RTSP stream with high quality settings"""
#         # Modify URL based on protocol choice
#         if protocol == 'TCP':
#             # Force TCP transport by appending rtsp_transport=tcp
#             if '?' in url:
#                 rtsp_url = f"{url}&rtsp_transport=tcp"
#             else:
#                 rtsp_url = f"{url}?rtsp_transport=tcp"
#         else:
#             rtsp_url = url
            
#         # Create capture object
#         self.stream = cv2.VideoCapture(rtsp_url)
        
#         if self.stream.isOpened():
#             # Configure for maximum quality
#             self.stream.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('H', '2', '6', '4'))
#             self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 0)  # Disable frame buffering
            
#             # Try to set maximum resolution if camera supports it
#             current_width = self.stream.get(cv2.CAP_PROP_FRAME_WIDTH)
#             current_height = self.stream.get(cv2.CAP_PROP_FRAME_HEIGHT)
            
#             print(f"Stream resolution: {current_width}x{current_height}")
            
#             # Try to get the highest possible quality
#             self.stream.set(cv2.CAP_PROP_FPS, 30)  # Request 30fps
            
#             return True
#         return False
    
#     def read(self):
#         """Read a frame from the stream"""
#         if self.stream and self.stream.isOpened():
#             return self.stream.read()
#         return False, None
    
#     def release(self):
#         """Release the stream"""
#         if self.stream:
#             self.stream.release()
#             self.stream = None
    
#     def is_opened(self):
#         """Check if stream is opened"""
#         return self.stream is not None and self.stream.isOpened()
    
#     def get_resolution(self):
#         """Get current stream resolution"""
#         if self.stream:
#             width = int(self.stream.get(cv2.CAP_PROP_FRAME_WIDTH))
#             height = int(self.stream.get(cv2.CAP_PROP_FRAME_HEIGHT))
#             fps = int(self.stream.get(cv2.CAP_PROP_FPS))
#             return width, height, fps
#         return None, None, None



import cv2
import subprocess
import time
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

class RTSPHandler:
    def __init__(self):
        self.cap = None

    def connect(self, url, protocol=None):
        try:
            self.cap = cv2.VideoCapture(url)
            # Add these optimizations for better streaming
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize buffer size
            self.cap.set(cv2.CAP_PROP_FPS, 30)       # Set FPS
            # self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('H', '2', '6', '4'))
            return self.cap.isOpened()
        except Exception as e:
            print(f"Connection error: {str(e)}")
            return False

    # def read_frame(self):
    #     if self.cap and self.cap.isOpened():
    #         return self.cap.read()
    #     return False, None
    def read_frame(self):
        if not self.cap or not self.cap.isOpened():
            return False, None
            
        max_retries = 3
        for _ in range(max_retries):
            ret, frame = self.cap.read()
            if ret:
                return True, frame
            time.sleep(0.1)  # Short delay before retry
            
        # If we get here, reading failed after retries
        return False, None


    def disconnect(self):
        if self.cap:
            self.cap.release()

    def is_opened(self):
        return self.cap is not None and self.cap.isOpened()

  
            