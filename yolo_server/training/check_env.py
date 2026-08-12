"""
Environment Check Script for Beehive Visual Recognition System (Module 1: YOLO Training)
"""

import sys
import os

def check_environment():
    print("=" * 60)
    print("Beehive Entry/Exit Detection - Module 1 Environment Check")
    print("=" * 60)
    
    # 1. Python Version
    print(f"[+] Python Version: {sys.version.split()[0]}")
    
    # 2. PyTorch & CUDA Check
    try:
        import torch
        print(f"[+] PyTorch Version: {torch.__version__}")
        cuda_available = torch.cuda.is_available()
        print(f"[+] CUDA Available: {cuda_available}")
        
        if cuda_available:
            device_count = torch.cuda.device_count()
            print(f"[+] CUDA Device Count: {device_count}")
            for i in range(device_count):
                device_name = torch.cuda.get_device_name(i)
                total_mem_gb = torch.cuda.get_device_properties(i).total_memory / (1024**3)
                print(f"    - GPU [{i}]: {device_name} ({total_mem_gb:.2f} GB VRAM)")
        else:
            print("    [!] WARNING: CUDA is NOT available to PyTorch! Training will fall back to CPU.")
    except ImportError:
        print("[!] ERROR: PyTorch ('torch') is not installed!")

    # 3. Ultralytics Check
    try:
        import ultralytics
        print(f"[+] Ultralytics Version: {ultralytics.__version__}")
    except ImportError:
        print("[!] ERROR: 'ultralytics' package is not installed! Please run: pip install ultralytics")

    # 4. Torchvision Check
    try:
        import torchvision
        print(f"[+] Torchvision Version: {torchvision.__version__}")
    except ImportError:
        print("[!] Torchvision is not installed or unavailable.")

    # 5. ONNX Check
    try:
        import onnx
        print(f"[+] ONNX Version: {onnx.__version__}")
    except ImportError:
        print("[!] Note: 'onnx' package is not installed (recommended for exporting ONNX models).")

    # 6. OpenCV Check
    try:
        import cv2
        print(f"[+] OpenCV Version: {cv2.__version__}")
    except ImportError:
        print("[!] OpenCV ('opencv-python') is not installed.")

    # 7. PyYAML Check
    try:
        import yaml
        print(f"[+] PyYAML Version: {yaml.__version__}")
    except ImportError:
        print("[!] PyYAML ('pyyaml') is not installed.")

    print("=" * 60)

if __name__ == "__main__":
    check_environment()
