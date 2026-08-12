"""
YOLO Training Script for Beehive Visual Recognition System
Optimized for NVIDIA GeForce RTX 5070 Ti (16GB VRAM)
"""

import argparse
import os
from pathlib import Path
import torch
from ultralytics import YOLO

def train_yolo(args):
    print("=" * 65)
    print("Beehive Entry/Exit Detection - YOLO Model Training")
    print("=" * 65)
    
    # Check GPU availability
    device = '0' if torch.cuda.is_available() else 'cpu'
    if device == '0':
        gpu_name = torch.cuda.get_device_name(0)
        vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        print(f"[+] Hardware Accelerator: {gpu_name} ({vram_gb:.2f} GB VRAM)")
    else:
        print("[!] WARNING: CUDA GPU not detected! Training will run on CPU.")
        
    dataset_yaml = Path(args.data).resolve()
    if not dataset_yaml.exists():
        raise FileNotFoundError(f"[!] Error: Dataset configuration file not found at {dataset_yaml}")
        
    print(f"[+] Dataset Config: {dataset_yaml}")
    print(f"[+] Base Model: {args.model}")
    print(f"[+] Image Size: {args.imgsz}")
    print(f"[+] Batch Size: {args.batch}")
    print(f"[+] Target Epochs: {args.epochs}")
    print(f"[+] Workers: {args.workers}")
    print(f"[+] AMP (Mixed Precision): {args.amp}")
    print("=" * 65)
    
    # Initialize YOLO Model
    model = YOLO(args.model)
    
    # Start Training
    results = model.train(
        data=str(dataset_yaml),
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        device=device,
        workers=args.workers,
        amp=args.amp,
        patience=args.patience,
        save=True,
        save_period=10,
        project=args.project,
        name=args.name,
        exist_ok=True,
        lr0=args.lr0,
        lrf=args.lrf,
        plots=True,
        val=True
    )
    
    print("\n" + "=" * 65)
    print("[OK] Training Completed!")
    print(f"[+] Best weights saved at: {Path(args.project) / args.name / 'weights' / 'best.pt'}")
    print(f"[+] Last weights saved at: {Path(args.project) / args.name / 'weights' / 'last.pt'}")
    print("=" * 65)
    
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YOLO Training for Beehive Recognition System")
    parser.add_argument("--data", type=str, default="dataset/data.yaml", help="Path to data.yaml file")
    parser.add_argument("--model", type=str, default="yolo26s.pt", help="Initial weights path or model spec (e.g. yolo26s.pt, yolo26n.pt, yolo26m.pt)")
    parser.add_argument("--epochs", type=int, default=100, help="Number of training epochs")
    parser.add_argument("--batch", type=int, default=32, help="Batch size (tuned for 16GB VRAM)")
    parser.add_argument("--imgsz", type=int, default=640, help="Input image size (640 or 1280 for higher detail)")
    parser.add_argument("--workers", type=int, default=8, help="Dataloader workers")
    parser.add_argument("--patience", type=int, default=30, help="Early stopping patience epochs")
    parser.add_argument("--amp", type=bool, default=True, help="Use Automatic Mixed Precision (AMP)")
    parser.add_argument("--lr0", type=float, default=0.01, help="Initial learning rate")
    parser.add_argument("--lrf", type=float, default=0.01, help="Final learning rate ratio")
    parser.add_argument("--project", type=str, default="runs", help="Save directory project name")
    parser.add_argument("--name", type=str, default="detect", help="Save directory run name")
    
    args = parser.parse_args()
    train_yolo(args)
