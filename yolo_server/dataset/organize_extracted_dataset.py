"""
Script to organize Roboflow dataset files extracted into root directory back into dataset/
"""

import os
import shutil
import glob
from pathlib import Path
import yaml

def organize_dataset():
    root = Path("d:/Bee_project")
    dataset = root / "dataset"
    
    print("=" * 65)
    print("Organizing Roboflow extracted files into dataset/...")
    print("=" * 65)
    
    # Mapping folders
    folder_map = {
        'train': 'train',
        'valid': 'val',
        'val': 'val',
        'test': 'test'
    }
    
    # 1. Process image and label directories
    for src_name, dst_name in folder_map.items():
        src_dir = root / src_name
        if src_dir.exists() and src_dir.is_dir():
            img_src = src_dir / "images"
            lbl_src = src_dir / "labels"
            
            img_dst = dataset / "images" / dst_name
            lbl_dst = dataset / "labels" / dst_name
            
            img_dst.mkdir(parents=True, exist_ok=True)
            lbl_dst.mkdir(parents=True, exist_ok=True)
            
            if img_src.exists():
                count = 0
                for f in img_src.glob("*"):
                    shutil.move(str(f), str(img_dst / f.name))
                    count += 1
                print(f"[+] Moved {count} images from {src_name}/images to dataset/images/{dst_name}")
                
            if lbl_src.exists():
                count = 0
                for f in lbl_src.glob("*"):
                    shutil.move(str(f), str(lbl_dst / f.name))
                    count += 1
                print(f"[+] Moved {count} labels from {src_name}/labels to dataset/labels/{dst_name}")
                
            # Remove empty src_dir
            shutil.rmtree(src_dir)
            print(f"[+] Removed empty folder: {src_name}")
            
    # 2. Process root data.yaml from Roboflow
    root_yaml = root / "data.yaml"
    dataset_yaml = dataset / "data.yaml"
    
    names_map = {0: 'bee'}
    
    if root_yaml.exists():
        with open(root_yaml, 'r', encoding='utf-8') as f:
            yaml_data = yaml.safe_load(f)
            
        if 'names' in yaml_data:
            if isinstance(yaml_data['names'], list):
                names_map = {i: name for i, name in enumerate(yaml_data['names'])}
            elif isinstance(yaml_data['names'], dict):
                names_map = yaml_data['names']
                
        root_yaml.unlink()
        print("[+] Processed root data.yaml and removed duplicate file.")
        
    # Write updated dataset/data.yaml
    data_yaml_content = {
        'path': '../dataset',
        'train': 'images/train',
        'val': 'images/val',
        'names': names_map
    }
    
    if (dataset / "images" / "test").exists() and any((dataset / "images" / "test").iterdir()):
        data_yaml_content['test'] = 'images/test'
        
    with open(dataset_yaml, 'w', encoding='utf-8') as f:
        yaml.dump(data_yaml_content, f, default_flow_style=False)
        
    print(f"[+] Updated {dataset_yaml} with classes: {names_map}")
    
    # 3. Clean up leftover readme files in root
    for readme in ["README.dataset.txt", "README.roboflow.txt"]:
        rf_file = root / readme
        if rf_file.exists():
            rf_file.unlink()
            print(f"[+] Cleaned up root file: {readme}")
            
    print("\n" + "=" * 65)
    print("[OK] Dataset organization completed successfully!")
    print("=" * 65)

if __name__ == "__main__":
    organize_dataset()
