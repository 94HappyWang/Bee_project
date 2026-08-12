"""
Roboflow Dataset Downloader & Setup Helper for Beehive Visual Recognition System
Target Dataset: awadh-ai/bee-zidej (Roboflow Universe)
"""

import argparse
import os
import shutil
import zipfile
from pathlib import Path
import yaml

def setup_from_zip(zip_path, target_dataset_dir="dataset"):
    zip_p = Path(zip_path).resolve()
    target_p = Path(target_dataset_dir).resolve()
    
    print("=" * 65)
    print(f"[+] Extracting local Roboflow ZIP: {zip_p}")
    print("=" * 65)
    
    if not zip_p.exists():
        raise FileNotFoundError(f"[!] Error: Zip file not found at {zip_p}")
        
    extract_temp = target_p / "_temp_extract"
    if extract_temp.exists():
        shutil.rmtree(extract_temp)
    extract_temp.mkdir(parents=True, exist_ok=True)
    
    with zipfile.ZipFile(zip_p, 'r') as zip_ref:
        zip_ref.extractall(extract_temp)
        
    print("[+] Zip extracted. Re-organizing into standard YOLO dataset structure...")
    
    # Roboflow zip structure usually contains: train/, valid/, test/, data.yaml
    subsets_map = {'train': 'train', 'valid': 'val', 'val': 'val', 'test': 'test'}
    
    for rf_subset, target_subset in subsets_map.items():
        sub_dir = extract_temp / rf_subset
        if sub_dir.exists():
            img_src = sub_dir / "images"
            lbl_src = sub_dir / "labels"
            
            img_dst = target_p / "images" / target_subset
            lbl_dst = target_p / "labels" / target_subset
            
            img_dst.mkdir(parents=True, exist_ok=True)
            lbl_dst.mkdir(parents=True, exist_ok=True)
            
            # Copy images
            if img_src.exists():
                for f in img_src.glob("*"):
                    shutil.copy2(f, img_dst / f.name)
            elif sub_dir.exists():
                for f in sub_dir.glob("*"):
                    if f.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                        shutil.copy2(f, img_dst / f.name)
                        
            # Copy labels
            if lbl_src.exists():
                for f in lbl_src.glob("*"):
                    shutil.copy2(f, lbl_dst / f.name)
            elif sub_dir.exists():
                for f in sub_dir.glob("*"):
                    if f.suffix.lower() == '.txt':
                        shutil.copy2(f, lbl_dst / f.name)
                        
    # Copy data.yaml if exists
    rf_yaml = extract_temp / "data.yaml"
    if rf_yaml.exists():
        with open(rf_yaml, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # Update relative paths in data.yaml
        data['path'] = '../dataset'
        data['train'] = 'images/train'
        data['val'] = 'images/val'
        if 'test' in data:
            data['test'] = 'images/test'
            
        with open(target_p / "data.yaml", 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False)
        print(f"[+] Updated data.yaml classes: {data.get('names')}")
        
    # Clean up temp
    shutil.rmtree(extract_temp)
    print("\n[✔] Dataset extracted and organized successfully into dataset/")
    print("=" * 65)

def download_from_api(api_key, version=1, target_dataset_dir="dataset"):
    from roboflow import Roboflow
    
    print("=" * 65)
    print(f"[+] Downloading 'awadh-ai/bee-zidej' (v{version}) via Roboflow API...")
    print("=" * 65)
    
    rf = Roboflow(api_key=api_key)
    project = rf.workspace("awadh-ai").project("bee-zidej")
    dataset = project.version(version).download("yolov8", location=target_dataset_dir)
    
    target_p = Path(target_dataset_dir).resolve()
    # Normalize data.yaml path
    yaml_file = target_p / "data.yaml"
    if yaml_file.exists():
        with open(yaml_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        data['path'] = '../dataset'
        data['train'] = 'images/train'
        data['val'] = 'images/val'
        with open(yaml_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False)
            
    print("\n[✔] Roboflow API download completed!")
    print("=" * 65)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download or setup Roboflow dataset 'bee-zidej'")
    parser.add_argument("--api-key", type=str, default=None, help="Roboflow API Key to download directly via API")
    parser.add_argument("--version", type=int, default=1, help="Roboflow dataset version (Default: 1)")
    parser.add_argument("--zip-path", type=str, default=None, help="Path to locally downloaded Roboflow dataset .zip file")
    
    args = parser.parse_args()
    
    if args.api_key:
        download_from_api(args.api_key, args.version)
    elif args.zip_path:
        setup_from_zip(args.zip_path)
    else:
        print("[!] Please provide either --api-key <YOUR_KEY> OR --zip-path <PATH_TO_ZIP>")
