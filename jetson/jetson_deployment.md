# NVIDIA Jetson Orin Nano 邊緣部署與移植指南

本指南說明如何將 **jetson/ (Module 2 HMI)** 資料夾從開發 PC 打包傳輸至 **NVIDIA Jetson Orin Nano** 邊緣裝置並順利啟動運行。

---

## 📦 步驟一：打包與傳輸 jetson/ 模組

請將 PC 端的 `Bee_project/jetson` 資料夾傳輸至 Jetson（建議放置於 `/home/<username>/Bee_project/jetson`）。

> ⚠️ **注意事項**：**請勿將 PC 端的 `.venv` 虛擬環境資料夾複製過去**！因為 Windows 端的 Python 二進位檔無法在 Linux ARM64 上執行。

### 傳輸方式建議 (二選一)：
1. **方式 A：使用隨身碟 / 外接硬碟**：
   - 複製 `Bee_project/jetson` 資料夾至隨身碟。
2. **方式 B：使用 SSH / SCP 指令 (網域傳輸)**：
   在 PC 端的 PowerShell 執行：
   ```powershell
   scp -r d:\Bee_project\jetson user@<jetson_ip>:/home/user/Bee_project/
   ```

---

## 🛠️ 步驟二：Jetson Orin Nano 環境安裝與虛擬環境建置

在 Jetson 的 Terminal 終端機中執行：

### 1. 安裝 Linux 系統基礎套件
```bash
sudo apt update
sudo apt install -y python3-pip python3-venv python3-pyqt5 libsqlite3-dev
```

### 2. 建置獨立 `.venv` 虛擬環境 (使用 `--system-site-packages` 以共用 Jetson TensorRT/PyTorch 庫)
```bash
cd ~/Bee_project/jetson

# 建立 Linux ARM64 專屬虛擬環境
python3 -m venv --system-site-packages .venv

# 啟動虛擬環境
source .venv/bin/activate
```

### 3. 安裝 Python 套件依賴
```bash
pip install --upgrade pip
pip install ultralytics opencv-python Pillow PyYAML tqdm
```

---

## ⚡ 步驟三：轉譯最佳化 TensorRT `.engine` 推論模型

將 PC 端訓練好的 `best.onnx` (或 `best.pt`) 放置於 `jetson/models/` 或 `jetson/` 目錄下，在 Jetson 上執行轉譯：

```bash
cd ~/Bee_project/jetson
source .venv/bin/activate

# 將 ONNX 模型轉譯為 Jetson Orin Nano FP16 加速引擎 best.engine
python3 -c "from ultralytics import YOLO; model = YOLO('best.onnx'); model.export(format='engine', half=True)"
```
轉譯完成後，會產生 `best.engine`，推論速度可提升數倍並大幅降低耗電！

---

## 📹 步驟四：相機設定與 HMI 啟動

### 1. 相機設定 (USB 相機 / Jetson CSI 相機)
- **USB 相機**：預設輸入 `"0"` (`/dev/video0`) 即可。
- **CSI 鏡頭 (GStreamer Pipeline)**：若使用 Jetson 板載 CSI 鏡頭，可在【設定頁面】將相機來源改為：
  ```text
  nvarguscamerasrc ! video/x-raw(memory:NVMM), width=1920, height=1080, format=NV12, framerate=30/1 ! nvvidconv ! video/x-raw, format=BGRx ! videoconvert ! video/x-raw, format=BGR ! appsink drop=1
  ```

### 2. 啟動 Module 2 HMI 介面
在 Jetson 終端機執行：

```bash
cd ~/Bee_project/jetson
source .venv/bin/activate
python3 main.py
```

---

## 💡 實用小技巧：開機自動啟動 HMI 服務

若希望 Jetson 架設在蜂巢旁開機自動執行 HMI：

1. 建立啟動腳本 `run_bee.sh`：
   ```bash
   #!/bin/bash
   cd /home/user/Bee_project/jetson
   source .venv/bin/activate
   export DISPLAY=:0
   python3 main.py
   ```
2. 設定執行權限：`chmod +x run_bee.sh`
3. 將其加入 Ubuntu 的 `Startup Applications` (開機自動啟動應用程式) 即可。
