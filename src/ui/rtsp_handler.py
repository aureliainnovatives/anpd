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
        self.stream = None
        
    def _build_url_with_params(self, url, params):
        """Add parameters to RTSP URL to request high quality"""
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        # Update with new params
        query_params.update(params)
        # Rebuild URL with new parameters
        new_query = urlencode(query_params, doseq=True)
        return urlunparse((
            parsed.scheme, 
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment
        ))

    def connect(self, url, protocol='TCP'):
        """Connect to RTSP stream with maximum quality settings"""
        # Quality parameters to try
        quality_params = {
            'rtsp_transport': 'tcp' if protocol == 'TCP' else 'udp',
            'resolution': '1920x1080',  # Request Full HD
            'quality': '100',           # Request maximum quality
            'compression': '0',         # Request no compression
            'fps': '30',               # Request 30fps
        }
        
        rtsp_url = self._build_url_with_params(url, quality_params)
        
        # Create capture object with advanced options
        self.stream = cv2.VideoCapture()
        
        # Try different codec configurations
        codec_options = [
            cv2.VideoWriter_fourcc('H', '2', '6', '4'),  # H264
            cv2.VideoWriter_fourcc('H', '2', '6', '5'),  # H265/HEVC
            cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'),  # MJPEG
            0x7634706d,  # MP4V
        ]
        
        for codec in codec_options:
            if self.stream.isOpened():
                self.stream.release()
                
            # Set advanced capture properties
            self.stream.set(cv2.CAP_PROP_FOURCC, codec)
            self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Try to open with current codec
            if self.stream.open(rtsp_url):
                # Configure additional stream properties
                self._configure_stream_properties()
                
                # Verify stream quality
                success, frame = self.stream.read()
                if success and frame is not None:
                    height, width = frame.shape[:2]
                    print(f"Successfully connected with codec {codec}")
                    print(f"Stream resolution: {width}x{height}")
                    print(f"FPS: {self.stream.get(cv2.CAP_PROP_FPS)}")
                    return True
                    
        # If no codec worked, try one last time with default settings
        self.stream = cv2.VideoCapture(rtsp_url)
        if self.stream.isOpened():
            self._configure_stream_properties()
            return True
            
        return False

    def _configure_stream_properties(self):
        """Configure stream properties for maximum quality"""
        # Try to set maximum resolution
        resolutions = [
            (3840, 2160),  # 4K
            (2560, 1440),  # 2K
            (1920, 1080),  # Full HD
            (1280, 720),   # HD
        ]
        
        for width, height in resolutions:
            self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            
            # Verify if resolution was set
            actual_width = self.stream.get(cv2.CAP_PROP_FRAME_WIDTH)
            actual_height = self.stream.get(cv2.CAP_PROP_FRAME_HEIGHT)
            
            if actual_width == width and actual_height == height:
                print(f"Successfully set resolution to {width}x{height}")
                break

        # Additional quality settings
        quality_settings = {
            cv2.CAP_PROP_FPS: 30,                    # Target 30 FPS
            cv2.CAP_PROP_BRIGHTNESS: 100,            # Maximum brightness
            cv2.CAP_PROP_CONTRAST: 100,              # Maximum contrast
            cv2.CAP_PROP_SATURATION: 100,            # Maximum saturation
            cv2.CAP_PROP_HUE: 0,                     # Default hue
            cv2.CAP_PROP_GAIN: 100,                  # Maximum gain
            cv2.CAP_PROP_CONVERT_RGB: 1,             # Ensure RGB output
            cv2.CAP_PROP_EXPOSURE: -1,               # Auto exposure
        }
        
        for prop, value in quality_settings.items():
            self.stream.set(prop, value)

    def get_stream_info(self):
        """Get detailed stream information"""
        if not self.stream or not self.stream.isOpened():
            return None
            
        info = {
            'width': int(self.stream.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(self.stream.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': int(self.stream.get(cv2.CAP_PROP_FPS)),
            'codec': int(self.stream.get(cv2.CAP_PROP_FOURCC)),
            'brightness': self.stream.get(cv2.CAP_PROP_BRIGHTNESS),
            'contrast': self.stream.get(cv2.CAP_PROP_CONTRAST),
            'saturation': self.stream.get(cv2.CAP_PROP_SATURATION),
            'exposure': self.stream.get(cv2.CAP_PROP_EXPOSURE),
        }
        
        # Convert codec to readable format
        codec_int = info['codec']
        info['codec_name'] = ''.join([chr((codec_int >> 8 * i) & 0xFF) for i in range(4)])
        
        return info

    def read(self):
        """Read a frame from the stream"""
        if self.stream and self.stream.isOpened():
            return self.stream.read()
        return False, None
    
    def release(self):
        """Release the stream"""
        if self.stream:
            self.stream.release()
            self.stream = None
    
    def is_opened(self):
        """Check if stream is opened"""
        return self.stream is not None and self.stream.isOpened()