# 🐝 YOLO Model Server (PC 訓練端模組)

本目錄包含 **蜜蜂進出蜂巢視覺辨識系統** 的 PC 模型訓練、數據集處理與 ONNX 導出相關程式碼與設定。

---

## 📂 目錄結構

```text
yolo_server/
├── dataset/                # Roboflow 蜜蜂數據集與驗證腳本
│   ├── data.yaml           # YOLO 數據集類別設定檔
│   ├── verify_dataset.py   # 資料集數量與格式自動整理工具
│   ├── download_roboflow.py# Roboflow 自動下載工具
│   ├── images/             # train/val/test 影像檔
│   └── labels/             # train/val/test 標註檔
├── training/               # YOLOv26 訓練與模型導出腳本
│   ├── train.py            # YOLO 訓練主程式 (預設 yolo26s.pt, batch=32, epochs=100)
│   ├── export_onnx.py      # 導出 Jetson TensorRT 相容 best.onnx 腳本
│   ├── check_env.py        # CUDA GPU 環境檢查
│   ├── best.onnx           # 訓練完成導出之 ONNX 權重檔
│   └── best.pt             # PyTorch 原生最佳權重檔
├── runs/                   # 訓練歷程數據與權重記錄
├── yolo26n.pt              # YOLOv26 Nano 預訓練權重
├── yolo26s.pt              # YOLOv26 Small 預訓練權重
└── requirements.txt        # PC 訓練端套件需求
```

---

## 🚀 操作流程

### 1. 資料集整理與驗證
```powershell
..\.venv\Scripts\python.exe dataset/verify_dataset.py
```

### 2. 開始模型訓練 (PC CUDA GPU)
```powershell
..\.venv\Scripts\python.exe training/train.py --model yolo26s.pt --epochs 100 --batch 32
```

### 3. 導出 ONNX 權重檔 (準備傳輸至 Jetson)
```powershell
..\.venv\Scripts\python.exe training/export_onnx.py
```

導出的 `best.onnx` 會自動複製傳輸至 `../jetson/models/best.onnx`！
