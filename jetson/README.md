# 🐧 Beehive Edge HMI & Tracking (Jetson 邊緣端模組)

本目錄包含 **蜜蜂進出蜂巢視覺辨識系統** 搬移至 **NVIDIA Jetson Orin Nano** 上執行的全套推論、ByteTrack 雙線追蹤與離線 PyQt5 HMI 視覺化人機介面。

---

## 🌟 介面與控制亮點

- **圓滑暖色調極簡視覺**：採用 `Quicksand` / `Nunito` / `Microsoft JhengHei UI` 圓潤字體，全域字體顯著加大 (16px ~ 38px)。
- **開啟預設靜態與二合一啟動/暫停按鈕**：`▶ 啟動推論` (綠) ↔ `⏸ 暫停推論` (黃) 單鈕切換。
- **一鍵停止與重置計數**：`🔄 停止並重置計數` 強效重置鍵。
- **純畫布拖曳校正**：移除繁瑣數字 SpinBox，直接於畫布上以滑鼠拖動 **Line A (藍)** / **Line B (綠)** 端點校正。
- **現場訓練集照片自動採樣**：第二頁面提供定時自動攝影與手動快照功能。

---

## 📂 目錄結構

```text
jetson/
├── models/                 # 模型權重檔放置區 (best.onnx, best.engine, best.pt)
├── tracking/               # 物件追蹤與進出判定算法
│   ├── bee_tracker.py      # ByteTrack 多目標追蹤與軌跡處理
│   └── line_counter.py     # 走廊雙虛擬線 Line A ↔ Line B 順序進出狀態機 (IN/OUT)
├── hmi/                    # 100% 離線 PyQt5 圓滑暖色極簡人機介面
│   ├── main_window.py      # QStackedWidget 3 頁分頁主視窗
│   ├── page_dashboard.py   # 頁面一：即時視訊與單一 Start/Pause 控制
│   ├── page_capture.py     # 頁面二：現場採樣照片存檔工具
│   ├── page_settings.py    # 頁面三：純滑鼠拖曳雙線校正頁
│   ├── video_widget.py     # 高效能 OpenCV 繪圖畫布組件
│   ├── worker_thread.py    # 獨立推論與追蹤後台線程
│   └── styles.py           # QSS 圓滑暖色調樣式表
├── utils/                  # 輔助模組
│   ├── infer_engine.py     # 統一 YOLO / ONNX / TensorRT 模型推論抽象層
│   ├── config.py           # JSON 設定檔讀寫器
│   ├── logger.py           # SQLite3 & CSV 日誌記錄器
│   └── test_video.py       # 無攝影機時之走廊模擬影片生成器
├── data/                   # 本地數據庫與設定存檔區
│   ├── config.json         # 雙線與相機劃線參數檔
│   ├── bee_logs.sqlite     # SQLite 進出歷史紀錄
│   └── bee_logs.csv        # CSV 數據備份
├── main.py                 # HMI 人機介面啟動進入點
├── jetson_deployment.md    # Jetson Orin Nano ARM64 移植部署詳細手冊
└── requirements.txt        # 邊緣端套件依賴說明
```

---

## 🚀 快速啟動

### 1. 【PC 本機測試】啟動 HMI
```cmd
cd /d d:\Bee_project\jetson && ..\.venv\Scripts\python.exe main.py
```

### 2. 【Jetson Orin Nano 部署與運作】
完整移植步驟請參閱 👉 [`jetson_deployment.md`](file:///d:/Bee_project/jetson/jetson_deployment.md)

1. 將 `jetson/` 目錄傳輸至 Jetson（如 `/home/user/Bee_project/jetson`）。
2. 在 Jetson 終端機進行 FP16 TensorRT `.engine` 模型加速轉譯：
   ```bash
   python3 -c "from ultralytics import YOLO; model = YOLO('best.onnx'); model.export(format='engine', half=True)"
   ```
3. 執行介面主程式：
   ```bash
   python3 main.py
   ```
