import os
import easyocr
from pathlib import Path
import shutil
import urllib.request
import ssl

def download_models():
    print("Downloading EasyOCR models...")
    
    # Create models directory
    models_dir = os.path.join(Path(__file__).parent, 'easyocr_models')
    os.makedirs(models_dir, exist_ok=True)
    
    # Configure SSL context to handle certificate issues
    ssl_context = ssl._create_unverified_context()
    
    # Model URLs
    model_urls = {
        'craft_mlt_25k.pth': 'https://github.com/JaidedAI/EasyOCR/releases/download/pre-v1.1.6/craft_mlt_25k.pth',
        'english_g2.pth': 'https://github.com/JaidedAI/EasyOCR/releases/download/v1.3/english_g2.pth'
    }
    
    # Download models
    for model_name, url in model_urls.items():
        model_path = os.path.join(models_dir, model_name)
        if not os.path.exists(model_path):
            print(f"Downloading {model_name}...")
            try:
                with urllib.request.urlopen(url, context=ssl_context) as response:
                    with open(model_path, 'wb') as f:
                        f.write(response.read())
                print(f"Successfully downloaded {model_name}")
            except Exception as e:
                print(f"Error downloading {model_name}: {str(e)}")
                continue
        else:
            print(f"{model_name} already exists, skipping download")
    
    # Verify downloads
    required_files = ['craft_mlt_25k.pth', 'english_g2.pth']
    missing_files = []
    for file in required_files:
        if not os.path.exists(os.path.join(models_dir, file)):
            missing_files.append(file)
    
    if missing_files:
        print(f"\nWarning: Following files are missing: {missing_files}")
    else:
        print("\nAll required model files downloaded successfully")
    
    # Initialize EasyOCR to verify models
    try:
        reader = easyocr.Reader(['en'], model_storage_directory=models_dir)
        print("\nEasyOCR initialization successful - models verified")
    except Exception as e:
        print(f"\nError verifying models with EasyOCR: {str(e)}")
    
    print(f"\nModels directory: {models_dir}")
    print(f"EasyOCR directory: {os.path.join(Path(__file__).parent, 'EasyOCR-1.7.2')}")

if __name__ == "__main__":
    download_models()