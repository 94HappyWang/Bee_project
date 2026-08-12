# NVIDIA Jetson Orin Nano 邊緣部署與 GitHub 自動同步指南

本指南說明如何透過 **GitHub** 將專案同步至 **NVIDIA Jetson Orin Nano** 邊緣裝置，並完成環境設定、TensorRT 模型轉譯與 HMI 人機介面啟動。

---

## 📦 步驟一：透過 GitHub Clone 取得最新程式碼

在 Jetson Orin Nano 上的 Terminal 終端機執行：

```bash
# 1. 複製 GitHub 儲存庫
cd ~
git clone https://github.com/<your-github-username>/Bee_project.git

# 2. 進入 jetson 邊緣端目錄
cd ~/Bee_project/jetson
```

> 💡 **日後更新版**：如果在 PC 端修改了程式碼並 `git push` 到 GitHub，只需在 Jetson 端執行：
> ```bash
> cd ~/Bee_project
> git pull origin main
> ```

---

## 🛠️ 步驟二：Jetson Orin Nano 環境安裝與虛擬環境建置

在 Jetson 終端機中執行：

### 1. 安裝 Linux 系統基礎套件
```bash
sudo apt update
sudo apt install -y python3-pip python3-venv python3-pyqt5 libsqlite3-dev
```

### 2. 建置獨立 `.venv` 虛擬環境 (使用 `--system-site-packages` 以共用 JetPack TensorRT/PyTorch 庫)
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
pip install -r requirements.txt
```

---

## ⚡ 步驟三：轉譯最佳化 TensorRT `.engine` 推論模型

模型檔已整合於 `jetson/models/best.onnx`。在 Jetson 上執行 FP16 轉譯命令：

```bash
cd ~/Bee_project/jetson
source .venv/bin/activate

# 將 ONNX 模型轉譯為 Jetson Orin Nano FP16 加速引擎 best.engine
python3 -c "from ultralytics import YOLO; model = YOLO('models/best.onnx'); model.export(format='engine', half=True)"
```
轉譯完成後，會產生 `models/best.engine`，推論速度可提升數倍並大幅降低硬體功耗！

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
