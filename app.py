import os, sys, re
import threading
import customtkinter as ctk
from tkinter import filedialog
from datetime import datetime
import yt_dlp
import glob
from downloader import YTDownloader

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# 建立一個自訂日誌攔截器，用來將 yt-dlp 內部狀態輸出到 UI
class YtLogger:
    def __init__(self, write_log_func):
        self.write_log = write_log_func
        
    def debug(self, msg):
        if "has already been downloaded" in msg:
            try:
                # 擷取檔名：[download] <file_path> has already been downloaded
                fname = os.path.basename(msg.split("has already been downloaded")[0].replace("[download]", "").strip())
                self.write_log(f">>> [跳過] 檔案已存在: {fname}")
            except:
                self.write_log(">>> [跳過] 檔案已存在。")
        elif "ExtractAudio" in msg:
            self.write_log(">>> [處理] 轉碼 MP3 中...")
        elif "Merger" in msg:
            self.write_log(">>> [處理] 合併影音中...")
            
    def info(self, msg):
        pass
        
    def warning(self, msg):
        pass
        
    def error(self, msg):
        self.write_log(f">>> [錯誤] {msg}")

# 建立一個繼承 YTDownloader 的自訂類別，去除建立資料夾與歷史紀錄功能
class NoHistoryDownloader(YTDownloader):
    def __init__(self):
        self.base_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        self.ffmpeg_dir = os.path.join(self.base_path, "ffmpeg")
        self.ffmpeg_bin = os.path.join(self.ffmpeg_dir, "bin")
        
        self.is_stop_requested = False
        self.current_status = ""
        self.auto_setup_ffmpeg()
        
    def download(self, url, save_path, audio_only, is_playlist, custom_logger):
        os.makedirs(save_path, exist_ok=True)
        
        # 預先解析該 URL/播放清單包含哪些影片標題，用來精準比對本地檔案
        target_ext = "mp3" if audio_only else "mp4"
        
        # 使用 extract_flat 快速獲取清單資訊，而不下載檔案
        extract_opts = {
            'extract_flat': True,
            'quiet': True,
            'noplaylist': not is_playlist
        }
        
        existing_titles = set()
        # 讀取本地已存在的標題 (去除檔名中的非法字元以利比對)
        for f in os.listdir(save_path):
            if f.endswith(f".{target_ext}"):
                title_without_ext = os.path.splitext(f)[0]
                existing_titles.add(title_without_ext)

        # 核心下載設定
        opts = {
            'ffmpeg_location': self.ffmpeg_bin,
            'outtmpl': os.path.join(save_path, "%(title)s.%(ext)s"),
            'progress_hooks': [self.progress_hook],
            'logger': custom_logger,
            'quiet': False,
            'noprogress': False,
            'extract_flat': False,
            'ignoreerrors': True,
            'overwrites': False,
            'noplaylist': not is_playlist,
            'writethumbnail': True,
            'addmetadata': True,
        }

        # 加入跳過已存在檔案的過濾器 (Match Filter)
        def match_filter(info_dict, incomplete):
            title = info_dict.get('title')
            # 清理檔名中可能被替換的特殊字元
            safe_title = re.sub(r'[\\/:*?"<>|]', '_', title) if title else ""
            
            # 如果資料夾中已經有對應標題的 mp3/mp4，直接拒絕下載
            if title in existing_titles or safe_title in existing_titles:
                custom_logger.debug(f"[download] {title}.{target_ext} has already been downloaded")
                return f"檔案 {title}.{target_ext} 已存在，跳過下載"
            return None

        opts['match_filter'] = match_filter

        postprocessors = [
            {'key': 'FFmpegMetadata', 'add_chapters': True},
            {'key': 'EmbedThumbnail'},
        ]

        if audio_only:
            opts.update({'format': 'bestaudio/best'})
            postprocessors.insert(0, {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192'
            })
        else:
            opts.update({'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'})

        opts['postprocessors'] = postprocessors

        before_images = set(glob.glob(os.path.join(save_path, "*.jpg")) + 
                            glob.glob(os.path.join(save_path, "*.webp")) + 
                            glob.glob(os.path.join(save_path, "*.png")))

        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
            
        # 清理多餘的播放清單圖片
        after_images = set(glob.glob(os.path.join(save_path, "*.jpg")) + 
                           glob.glob(os.path.join(save_path, "*.webp")) + 
                           glob.glob(os.path.join(save_path, "*.png")))
                           
        for img in after_images - before_images:
            try:
                os.remove(img)
            except:
                pass

class Downloader_tk(ctk.CTk):
    def __init__(self):
        super().__init__()
        base_path = self.get_base_path()
        icon_path = os.path.join(base_path, "ico", "i.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)
            
        self.title("YouTube Downloader")
        self.geometry("900x820")
        self.configure(fg_color="#0D0D0D")
        
        self.output_dir = ctk.StringVar()
        self.url = ctk.StringVar()
        self.mode = ctk.StringVar(value="1")
        self.downloading = False
        
        self.DL = None

        self.setup_ui()
        self.auto_setup_env()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    @staticmethod
    def get_base_path():
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        else:
            return os.path.dirname(os.path.abspath(__file__))

    def write_log(self, msg):
        self.after(0, lambda: self._write_log_internal(msg))
        
    def _write_log_internal(self, msg):
        self.txt_log.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        self.txt_log.see("end")

    def toggle_ui_state(self, state):
        self.btn_run.configure(state=state)
        self.btn_stop.configure(state=state)
        self.ent_u.configure(state=state)
        for child in self.f_m.winfo_children():
            if isinstance(child, ctk.CTkRadioButton):
                child.configure(state=state)
        if state == "disabled":
            self.ent_p.configure(state="disabled")
        else:
            self.ent_p.configure(state="readonly")
            
    def auto_setup_env(self):
        self.toggle_ui_state("disabled")
        self.lbl_status.configure(text="環境建置中...", text_color="#C0392B")
        self.write_log(">>> [環境] 開始初始化建置程序(FFmpeg檢查) 請稍後...")

        def setup_task():
            try:
                # 改用無歷史紀錄版本的自訂 Downloader
                self.DL = NoHistoryDownloader() 
                self.write_log(">>> [系統] 環境建置完成。")
                self.after(0, lambda: self.lbl_status.configure(text="準備完成", text_color="#F1C40F"))
                self.after(0, lambda: self.toggle_ui_state("normal"))
            except Exception as e:
                self.write_log(f">>> [錯誤] 初始化失敗: {e}")

        threading.Thread(target=setup_task, daemon=True).start()

    def setup_ui(self):
        ctk.CTkLabel(self, text="YOUTUBE DOWNLOADER", font=ctk.CTkFont(size=38, weight="bold"), text_color="#3498DB").pack(pady=(30, 10))
        self.f_main = ctk.CTkFrame(self, fg_color="#161616", corner_radius=15)
        self.f_main.pack(fill="both", padx=40, pady=10, expand=True)
        ctk.CTkLabel(self.f_main, text="--- 儲存目錄 ---", font=ctk.CTkFont(size=13), text_color="#7F8C8D").pack(pady=(15, 0))
        self.ent_p = ctk.CTkEntry(self.f_main, textvariable=self.output_dir, font=ctk.CTkFont(size=16), height=45, justify="center")
        self.ent_p.pack(fill="x", padx=20, pady=(5, 15))
        self.ent_p.bind("<Button-1>", lambda e: self.browse_folder())
        self.ent_p.configure(state="readonly") 
        self.f_m = ctk.CTkFrame(self.f_main, fg_color="transparent")
        self.f_m.pack(fill="x", pady=10)
        modes = [("音樂 MP3", "1"), ("影片 MP4", "2"), ("播放清單 MP3", "3"), ("播放清單 MP4", "4")]
        for t, v in modes:
            ctk.CTkRadioButton(self.f_m, text=t, variable=self.mode, value=v).pack(side="left", padx=25)
        self.ent_u = ctk.CTkEntry(self.f_main, textvariable=self.url, placeholder_text="在此貼上 YouTube 網址...", height=60, font=ctk.CTkFont(size=18), border_color="#3498DB", border_width=2, justify="center")
        self.ent_u.pack(fill="x", padx=20, pady=(5, 15))
        self.lbl_status = ctk.CTkLabel(self.f_main, text="初始化中", font=ctk.CTkFont(size=52, weight="bold"), text_color="#F1C40F")
        self.lbl_status.pack(pady=(20, 5))
        self.bar = ctk.CTkProgressBar(self.f_main, height=30, progress_color="#3498DB", fg_color="#2C3E50")
        self.bar.set(0)
        self.bar.pack(fill="x", padx=25, pady=20)
        self.f_btn = ctk.CTkFrame(self, fg_color="transparent")
        self.f_btn.pack(pady=20)
        self.btn_run = ctk.CTkButton(self.f_btn, text="開始執行", width=220, height=60, font=ctk.CTkFont(size=22, weight="bold"), command=self.start_task)
        self.btn_run.pack(side="left", padx=15)
        self.btn_stop = ctk.CTkButton(self.f_btn, text="停止並清理", fg_color="#C0392B", width=220, height=60, font=ctk.CTkFont(size=22, weight="bold"), command=self.stop_t)
        self.btn_stop.pack(side="left", padx=15)
        self.txt_log = ctk.CTkTextbox(self, height=130, font=ctk.CTkFont(family="Microsoft JhengHei UI", size=14), fg_color="#000000", text_color="#2ECC71")
        self.txt_log.pack(fill="both", padx=40, pady=(0, 20))

    def browse_folder(self):
        if self.btn_run.cget("state") == "disabled": return 
        f = filedialog.askdirectory()
        if f: self.output_dir.set(f)

    def stop_t(self):
        if self.DL and self.downloading:
            self.DL.is_stop_requested = True
            
        self.downloading = False
        self.lbl_status.configure(text="已停止", text_color="#C0392B")
        self.write_log(">>> [系統] 任務已手動中止。")
        self.btn_run.configure(state="normal")
        
        save_path = self.output_dir.get().strip()
        if self.DL and save_path:
            threading.Thread(target=self.DL.cleanup_temp_files, args=(save_path,), daemon=True).start()

    def on_closing(self):
        if self.downloading: self.stop_t()
        self.destroy()

    def start_task(self):
        url, path = self.url.get().strip(), self.output_dir.get().strip()
        if not path or not url:
            self.lbl_status.configure(text="資訊不全", text_color="#E74C3C")
            return
            
        self.downloading = True
        self.btn_run.configure(state="disabled")
        self.bar.set(0)
        self.lbl_status.configure(text="準備下載...", text_color="#F1C40F")
        self.txt_log.delete("1.0", "end")
        self.write_log(f">>> [系統] 任務啟動 | 儲存至: {path}")
        
        threading.Thread(target=self.run_process, args=(url, path.replace("\\", "/")), daemon=True).start()

    def update_ui_progress(self, pct):
        if not self.downloading: return
        self.bar.set(pct)
        self.lbl_status.configure(text=f"{int(pct*100)}%")

    def run_process(self, url, path):
        mode = self.mode.get()
        audio_only = mode in ["1", "3"]
        is_playlist = mode in ["3", "4"]  # 判定是否為播放清單模式[cite: 3]
        
        logger = YtLogger(self.write_log)
        
        def custom_hook(d):
            if self.DL.is_stop_requested:
                raise Exception("USER_STOP")
                
            status = d.get('status')
            if status == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 1)
                downloaded = d.get('downloaded_bytes', 0)
                if total > 0:
                    pct = downloaded / total
                    self.after(0, lambda p=pct: self.update_ui_progress(p))
                    
            elif status == 'finished':
                fname = os.path.basename(d.get('filename', ''))
                self.after(0, lambda f=fname: self.write_log(f">>> [下載完成] {f}, 正在處理..."))

        try:
            self.DL.is_stop_requested = False
            self.DL.progress_hook = custom_hook
            
            # 直接呼叫覆寫後的 download()
            self.DL.download(url, path, audio_only, is_playlist, logger)
            
            if not self.DL.is_stop_requested:
                self.after(0, self.finish_success)
                
        except Exception as e:
            if "USER_STOP" in str(e) or self.DL.is_stop_requested:
                self.after(0, lambda: self.write_log(">>> [系統] 下載已被終止"))
            else:
                self.after(0, lambda err=str(e): self.finish_error(err))
        finally:
            self.downloading = False
            self.DL.is_stop_requested = False

    def finish_success(self):
        self.bar.set(1)
        self.lbl_status.configure(text="全部完成", text_color="#2ECC71")
        self.write_log(">>> [完成] 所有任務成功處理。")
        self.btn_run.configure(state="normal")

    def finish_error(self, err_msg):
        self.lbl_status.configure(text="下載失敗", text_color="#E74C3C")
        self.write_log(f">>> [錯誤] {err_msg}")
        self.btn_run.configure(state="normal")

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    
    Downloader_tk().mainloop()