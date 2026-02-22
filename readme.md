# YouTube Downloader (GUI)

一款使用 Python + `yt-dlp` + `ffmpeg` 製作的圖形化 YouTube 下載工具，支援下載影片、MP3 音樂，以及播放清單批次下載，並具備進度條與日誌顯示。

---

## ✨ 功能特色

* 🎬 下載單一影片 (MP4)
* 🎵 下載單一影片音訊 (MP3)
* 📃 批次下載播放清單 (MP4 / MP3)
* 📊 即時下載進度顯示
* 🧾 即時日誌輸出
* 🧹 一鍵停止並清理暫存檔
* 🖥️ 直覺式 GUI 介面（CustomTkinter）
* ⚙️ 自動初始化下載 `yt-dlp.exe`

---

## 🧰 使用技術

* Python 3
* yt-dlp
* FFmpeg
* CustomTkinter
* psutil
* threading + subprocess

---
## 可以直接執行YT_Downloader.exe檔案 或者 按照以下步驟使用python來使用

## 📦 安裝需求

### 1️⃣ 安裝 FFmpeg

請先安裝 FFmpeg 並放在資料夾內：

* Windows: https://ffmpeg.org/download.html


### 2️⃣ 安裝 Python 套件

```bash
pip install -r requirements.txt
```

## 🚀 執行程式

```bash
python app.py
```

首次啟動時，程式會自動下載 `yt-dlp.exe`（Windows）。

---

## 📂 輸出檔案結構

### 單一影片下載

```
輸出資料夾/
└── 上傳者名稱/
    └── 影片標題.mp4
```

### 播放清單下載

```
輸出資料夾/
└── 上傳者名稱/
    └── 播放清單名稱/
        ├── 影片1.mp4
        ├── 影片2.mp4
        └── ...
```

---

## 🎛️ 模式說明

| 模式         | 功能         |
| ---------- | ---------- |
| 下載 MP3     | 下載單一影片音訊   |
| 下載影片 MP4   | 下載單一影片     |
| 下載播放清單 MP3 | 批次下載播放清單音訊 |
| 下載播放清單 MP4 | 批次下載播放清單影片 |

---

## 🛑 停止下載

按下「停止並清理」會：

* 強制終止 yt-dlp 與 ffmpeg 子程序
* 刪除 `.part` / `.temp` 等暫存檔案

---

## 🧠 運作流程

1. 啟動程式
2. 自動檢查並下載 `yt-dlp.exe`
3. 選擇輸出資料夾
4. 貼上 YouTube 影片或播放清單網址
5. 選擇下載模式
6. 開始下載並顯示進度與日誌

---

## ⚠️ 注意事項

* 請確保已安裝 `ffmpeg`
* 某些影片可能因版權限制無法下載
* 播放清單下載速度取決於影片數量與網路狀況

---

## 🧩 打包為 EXE（Windows）

建議使用 PyInstaller：

```bash
pyinstaller --noconfirm --onefile --windowed --icon="ico/i.ico" --add-data "ico;ico/" --add-data "venv/Lib/site-packages/customtkinter;customtkinter/" --name "YT_Downloader" "app.py"
```

輸出檔案位於：

```
dist/app.exe
```

---

## 📜 License

MIT License

---

## 🙌 貢獻

歡迎提出 Issue 或 Pull Request 改進此工具！

---

## ⭐ Support

如果這個專案對你有幫助，歡迎給個 Star ⭐
