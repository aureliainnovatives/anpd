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

1. URL -->  rtsp://<username>:<password>@<ipaddress>:<port>/unicast/c2/s0/live
     - c2             --> camera name/id
     - s0             --> max quality (to minimize decrease the number after s. ex.s1,s2)
     - username       --> id 
     - password       --> pass
     - ipaddress      --> ip address
     - port           --> port only for rtsp protocol
     - unicast        --> protocol




--------------------------> EXE GENERATE <---------------------------------


FOR MAIN PROJECT ->

1. Open a terminal in the ANPD (Project directory).
2. install pyinstaller using pip command 
    pip install pyinstaller
3. run command : 
    pyinstaller --onefile --clean --windowed --add-data "config.json;." --add-data "models/NPDv1.0.pt;." --add-data "EasyOCR-1.7.2;EasyOCR-1.7.2" --add-data "easyocr_models;easyocr_models" --add-data "icons;icons" --hidden-import easyocr --hidden-import torch --hidden-import torchvision --hidden-import numpy --hidden-import PIL --hidden-import opencv-python --hidden-import torch.nn --hidden-import torch.backends --hidden-import torch.utils.data --hidden-import torchvision.transforms --hidden-import yaml --hidden-import scipy --hidden-import scipy.special --hidden-import sklearn src/main.py
4. In the ANPD/dist folder, a `main.exe` will be generated.
5. place config.json in same directory where exe will located.
6. Place `NPDv1.0.pt` in the `models` folder within the same directory, 
   so the folder structure will be :

            ANPD/  
            │── dist/  
            │   │── main.exe
            │   │── config.json  
            │   │── EasyOCR-1.7.2/
            │   │── easyocr_models/
            │   │── icons/
            │   │── models/  
            │   │   │── NPDv1.0.pt  


FOR RECIEVER PROJECT ->
1. Open a terminal in the ANPD Receiver (C# application) project directory.
2. run commands : 
   i.  without runtime included = dotnet build
   ii. with runtime = dotnet publish -r win-x64 --self-contained true -p:PublishSingleFile=true 
    ( Note : if the application is not included runtime then we need to install dependancies to run the application )
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
  
