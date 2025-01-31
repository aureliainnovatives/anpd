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




--------------------------> EXE GENERATE <---------------------------------


FOR MAIN PROJECT ->

1. Open a terminal in the ANPD (Project directory).
2. install pyinstaller using pip command 
    pip install pyinstaller
2. run command : 
    pyinstaller --onefile --clean --windowed --add-data "config.json;." --add-data "models/NPDv1.0.pt;." src/main.py  
3. In the ANPD/dist folder, a `main.exe` will be generated.
4. place config.json in same directory where exe will located.
5. Place `NPDv1.0.pt` in the `models` folder within the same directory, 
   so the folder structure will be :

            ANPD/  
            │── dist/  
            │   │── main.exe
            │   │── config.json  
            │   │── models/  
            │   │   │── NPDv1.0.pt  


FOR RECIEVER PROJECT ->
1. Open a terminal in the ANPD Receiver (C# application) project directory.
2. run command : 
    dotnet build 
3. In the `bin/debug/net9.0` folder, a `.exe` file and some other files like `.dll`, `.pdb`, and `.json` will be generated.
4. Place `config.json` in same directory where `.exe`  and other files will located.
5. so the folder structure will be :

            ANPD_Receiver/  
            │── bin/  
            │   │── Debug/  
            │   │   │── net9.0/  
            │   │   │   │── Receiver.exe  
            │   │   │   │── config.json  
            │   │   │   │── OtherDependency.dll  
            │   │   │   │── DebugSymbols.pdb  
            │   │   │   │── Settings.json 
            │── Program.cs  
            │── config.json
  
