"""
Dataset Verification Script for Beehive Visual Recognition System
Checks YOLO format structure, image-label pairing, and label format validity.
"""

import os
import glob
from pathlib import Path
import yaml
import cv2

def verify_dataset(dataset_dir="dataset"):
    dataset_path = Path(dataset_dir)
    yaml_file = dataset_path / "data.yaml"
    
    print("=" * 65)
    print("Beehive Recognition System - Dataset Verification")
    print("=" * 65)
    
    if not yaml_file.exists():
        print(f"[!] ERROR: {yaml_file} not found!")
        return False
        
    with open(yaml_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        
    print(f"[+] Loaded data.yaml successfully.")
    print(f"    - Classes: {config.get('names', {})}")
    
    subsets = ['train', 'val']
    valid_exts = {'.jpg', '.jpeg', '.png', '.bmp'}
    
    all_ok = True
    
    for subset in subsets:
        img_dir = dataset_path / "images" / subset
        lbl_dir = dataset_path / "labels" / subset
        
        img_dir.mkdir(parents=True, exist_ok=True)
        lbl_dir.mkdir(parents=True, exist_ok=True)
        
        images = [f for f in img_dir.glob("*") if f.suffix.lower() in valid_exts]
        labels = list(lbl_dir.glob("*.txt"))
        
        print(f"\n--- Checking Subset: [{subset.upper()}] ---")
        print(f"[+] Found {len(images)} images in {img_dir.relative_to(dataset_path.parent)}")
        print(f"[+] Found {len(labels)} label files in {lbl_dir.relative_to(dataset_path.parent)}")
        
        if len(images) == 0:
            print(f"    [!] WARNING: No images found in {img_dir}. Please add training/validation images.")
            all_ok = False
            continue
            
        img_stems = {img.stem: img for img in images}
        lbl_stems = {lbl.stem: lbl for lbl in labels}
        
        missing_labels = set(img_stems.keys()) - set(lbl_stems.keys())
        orphan_labels = set(lbl_stems.keys()) - set(img_stems.keys())
        
        if missing_labels:
            print(f"    [!] WARNING: {len(missing_labels)} images missing corresponding .txt label files.")
        if orphan_labels:
            print(f"    [!] WARNING: {len(orphan_labels)} label files have no matching image.")
            
        paired_count = len(set(img_stems.keys()) & set(lbl_stems.keys()))
        print(f"    [OK] Successfully paired image-label pairs: {paired_count}/{len(images)}")
        
        # Verify a sample of label files for valid YOLO format (class x_center y_center width height)
        invalid_labels = 0
        for stem, lbl_path in lbl_stems.items():
            if stem not in img_stems:
                continue
            with open(lbl_path, 'r', encoding='utf-8') as lf:
                lines = lf.readlines()
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split()
                    if len(parts) != 5:
                        invalid_labels += 1
                        break
                    try:
                        cls_id = int(parts[0])
                        coords = [float(x) for x in parts[1:]]
                        if not all(0.0 <= c <= 1.0 for c in coords):
                            invalid_labels += 1
                            break
                    except ValueError:
                        invalid_labels += 1
                        break
                        
        if invalid_labels > 0:
            print(f"    [!] WARNING: Found {invalid_labels} label files with invalid YOLO format or unnormalized coordinates!")
            all_ok = False
            
    print("\n" + "=" * 65)
    if all_ok:
        print("[OK] Dataset structure & validation passed!")
    else:
        print("[!] Dataset check completed with warnings. Please add images/labels into dataset/.")
    print("=" * 65)
    return all_ok

if __name__ == "__main__":
    verify_dataset()
