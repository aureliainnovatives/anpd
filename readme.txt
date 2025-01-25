AUTOMATIC NUMBER0-PLATE DETECTION


1. NPDv1.0.pt (name of this file is different on the original source)
   (third party car Licenseplate pretrained pt file)
   --> https://github.com/Muhammad-Zeerak-Khan/Automatic-License-Plate-Recognition-using-YOLOv8

2.yolo11n.pt 
  (YOLO11 pretrained pt file)

3.requirements.txt (all required libraries and packages)


-----------------------------> Usage <----------------------------- 
1. Run the application:

   python src/main.py

2. In the GUI:
   - Click "Connect RTSP" to connect to an RTSP stream or use the camera.
   - Click "Start Detection" to begin detecting license plates.
   - Click "Stop Detection" to stop the detection process.

3. Detected license plates will be displayed in the video feed, and their images and details will be saved in the `detected_plates` directory.


-----------------------------> RTSP URL <----------------------------- 

1. URL -->  rtsp://nhai:NhaiBdr$123@122.187.87.67:554/unicast/c2/s0/live
     - c2             --> camera name/id
     - s0             --> max quality (to minimize decrease the number after s. ex.s1,s2)
     - nhai           --> id 
     - NhaiBdr$123    --> pass
     - 122.187.87.67  --> ip address
     - 554            --> port only for rtsp protocol
     - unicast        --> protocol
