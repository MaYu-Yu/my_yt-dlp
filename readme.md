# YouTube Downloader (MP3 & MP4)

這個專案提供一個簡單的批次檔工具，使用 `yt-dlp` 下載 YouTube 的影片或音樂，並依作者與播放清單自動整理資料夾。

---

## 1. 安裝與設定

1. 先執行 `setup.bat` 安裝必要檔案，例如 `yt-dlp.exe`。  
2. 完成後，就可以使用 `download.bat` 來下載 YouTube 影片或音樂。

---

## 2. 使用 `download.bat` 教學

1. 執行 `download.bat`。  
2. 系統會詢問 **下載資料夾**，請輸入完整路徑（例如 `D:\Code\yd-dlp\output`）。  
   - 如果輸入空值或無效路徑，系統會要求重新輸入。  
3. 選擇下載模式：
    1. Single Video MP3

    2. Single Video MP4

    3. Playlist MP3

    4. Playlist MP4
    - 在任意輸入提示輸入 `exit` 可以回到選單。  
4. 輸入 YouTube 的影片或播放清單 URL（同樣可以輸入 `exit` 返回選單）。  
5. 下載開始，程式會自動：
- 單一影片 → 建立作者資料夾，檔案存於作者資料夾內  
  ```
  <下載資料夾>/mp3/作者名稱/影片名稱.mp3
  <下載資料夾>/mp4/作者名稱/影片名稱.mp4
  ```
- 播放清單 → 建立作者資料夾，再在裡面建立播放清單名稱資料夾，存放影片  
  ```
  <下載資料夾>/mp3/作者名稱/播放清單名稱/編號 - 影片名稱.mp3
  <下載資料夾>/mp4/作者名稱/播放清單名稱/編號 - 影片名稱.mp4
  ```
6. 下載完成後自動回到模式選單，可繼續下載其他影片或播放清單。

---

## 3. 程式介紹

這個專案主要使用 **批次檔 (.bat)** 搭配 `yt-dlp` 完成 YouTube 下載功能。  
功能特色：

- 支援單一影片或整個播放清單下載。  
- 可選 MP3（音樂）或 MP4（影片）格式。  
- 自動依作者與播放清單整理資料夾。  
- 嵌入影片封面與 metadata。  
- 自動跳過已存在的檔案。  
- 完全循環操作，隨時可輸入 `exit` 回到選單。  
- 批次檔中會檢查下載資料夾是否存在，避免輸入無效路徑。

程式主要流程：

1. 設定下載資料夾與檢查有效性。  
2. 選擇下載模式（MP3 / MP4，單一影片 / 播放清單）。  
3. 輸入 YouTube URL。  
4. 依選擇模式設定 `yt-dlp` 的下載指令與輸出路徑。  
5. 執行下載並回到主選單。

---

## 4. 參考

本專案的下載核心與批次檔指令參考自：

- [yt-dlp 官方 GitHub](https://github.com/yt-dlp/yt-dlp)
- [yt-dlp 官方 FFmpeg GitHub](https://github.com/yt-dlp/FFmpeg-Builds/releases)
- [yt-dlp 官方執行檔 GitHub](https://github.com/yt-dlp/yt-dlp/releases/latest/download/)

---

## 5. 注意事項

- 下載 YouTube 影片請遵守當地法律與 YouTube 使用條款。  
- 確保已安裝 ffmpeg（可選，但建議安裝以支援轉檔與嵌入封面）。
