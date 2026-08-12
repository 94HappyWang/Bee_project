"""
ONNX Export Script for Beehive Visual Recognition System
Exports YOLO PyTorch model (.pt) to ONNX format (.onnx) optimized for Jetson Orin Nano (TensorRT)
"""

import argparse
from pathlib import Path
import torch
import onnx
import onnxruntime as ort
import numpy as np
from ultralytics import YOLO

def export_onnx(args):
    print("=" * 65)
    print("Beehive Entry/Exit Detection - ONNX Model Export")
    print("=" * 65)
    
    if args.weights is None:
        possible_weights = list(Path("runs").rglob("best.pt"))
        if possible_weights:
            weights_path = possible_weights[-1].resolve()
        else:
            weights_path = Path("runs/detect/weights/best.pt").resolve()
    else:
        weights_path = Path(args.weights).resolve()

    if not weights_path.exists():
        raise FileNotFoundError(f"[!] Error: Weights file not found at {weights_path}")
        
    output_dir = Path(args.output_dir).resolve() if args.output_dir else weights_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"[+] Input Weights: {weights_path}")
    print(f"[+] Target Opset Version: {args.opset}")
    print(f"[+] Image Size: {args.imgsz}x{args.imgsz}")
    print(f"[+] Dynamic Shape: {args.dynamic} (False recommended for max Jetson TensorRT speed)")
    print(f"[+] Graph Simplify: {args.simplify}")
    print(f"[+] Output Directory: {output_dir}")
    print("=" * 65)
    
    # Load PyTorch YOLO Model
    model = YOLO(str(weights_path))
    
    # Export to ONNX
    onnx_file_path = model.export(
        format="onnx",
        opset=args.opset,
        imgsz=(args.imgsz, args.imgsz),
        dynamic=args.dynamic,
        simplify=args.simplify,
        half=args.half
    )
    
    exported_onnx_path = Path(onnx_file_path).resolve()
    print("\n" + "=" * 65)
    print(f"[OK] Successfully exported ONNX model to: {exported_onnx_path}")
    
    # 1. ONNX Structural Verification
    print("[+] Running ONNX Checker...")
    onnx_model = onnx.load(str(exported_onnx_path))
    onnx.checker.check_model(onnx_model)
    print("    [OK] ONNX syntax and structure check PASSED!")
    
    # 2. ONNX Runtime Inference Verification
    print("[+] Running ONNX Runtime inference test...")
    session = ort.InferenceSession(str(exported_onnx_path), providers=['CPUExecutionProvider'])
    input_meta = session.get_inputs()[0]
    output_meta = session.get_outputs()[0]
    
    print(f"    - ONNX Input Name: {input_meta.name}, Shape: {input_meta.shape}, Type: {input_meta.type}")
    print(f"    - ONNX Output Name: {output_meta.name}, Shape: {output_meta.shape}, Type: {output_meta.type}")
    
    dummy_input = np.random.randn(1, 3, args.imgsz, args.imgsz).astype(np.float32)
    outputs = session.run([output_meta.name], {input_meta.name: dummy_input})
    print(f"    [OK] Test inference output shape: {outputs[0].shape}")
    print("=" * 65)
    print("[SUCCESS] ONNX Model is ready for transfer to Jetson Orin Nano for TensorRT compilation!")
    print("=" * 65)
    
    return exported_onnx_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export YOLO PyTorch model to ONNX for Jetson TensorRT")
    parser.add_argument("--weights", type=str, default=None, help="Path to PyTorch .pt model weights (Default: auto find best.pt in runs/)")
    parser.add_argument("--opset", type=int, default=17, help="ONNX opset version (12 or 17 recommended for Jetson TensorRT)")
    parser.add_argument("--imgsz", type=int, default=640, help="Input image size (width & height)")
    parser.add_argument("--dynamic", action="store_true", default=False, help="Enable dynamic input shape (Default: False for static 1x3x640x640)")
    parser.add_argument("--simplify", type=bool, default=True, help="Simplify ONNX graph")
    parser.add_argument("--half", action="store_true", default=False, help="Export in FP16 half precision")
    parser.add_argument("--output-dir", type=str, default=None, help="Directory to save exported .onnx file")
    
    args = parser.parse_args()
    export_onnx(args)
