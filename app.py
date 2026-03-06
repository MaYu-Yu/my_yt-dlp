import os, sys
import subprocess
import threading
import customtkinter as ctk
from tkinter import filedialog
import urllib.request
from datetime import datetime
import re
import psutil
import glob
from collections import deque
import shutil

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class Downloader_tk(ctk.CTk):
    def __init__(self):
        super().__init__()
        # 修正 1：透過類別內的 get_base_path 獲取路徑以設定圖標
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
        self.download_proc = None
        self.downloading = False
        self.msg_queue = deque()
        
        self.total_count = 0 
        self.current_idx = 0
        self.last_logged_idx = 0
        self.is_finished_logged = False
        self.has_error = False
        self.actual_processed_count = 0 

        self.setup_ui()
        self.auto_setup_env()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    @staticmethod
    def get_base_path():
        """獲取程式執行的實際目錄 (解決 PyInstaller onefile 路徑問題)"""
        if getattr(sys, 'frozen', False):
            # 如果是打包後的 exe，傳回 exe 所在的資料夾
            return os.path.dirname(sys.executable)
        else:
            # 如果是開發環境的 .py
            return os.path.dirname(os.path.abspath(__file__))

    def write_log(self, msg):
        """日誌顯示"""
        if isinstance(msg, bytes):
            msg = msg.decode('utf-8', errors='replace')
        
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
        self.write_log(">>> [環境] 開始初始化建置程序...")

        def download_task():
            # 修正 2：使用 self.get_base_path()
            base_path = self.get_base_path()
            ytdlp_path = os.path.join(base_path, "yt-dlp.exe")
            ffmpeg_zip = os.path.join(base_path, "ffmpeg-master-latest-win64-gpl.zip")
            ffmpeg_dir = os.path.join(base_path, "ffmpeg")

            try:
                if not os.path.exists(ytdlp_path):
                    self.write_log(">>> [環境] 正在下載 yt-dlp.exe...")
                    urllib.request.urlretrieve("https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe", ytdlp_path)
                
                if not os.path.exists(ffmpeg_dir):
                    self.write_log(">>> [環境] 正在下載 ffmpeg...")
                    if not os.path.exists(ffmpeg_zip):
                        ffmpeg_url = "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
                        urllib.request.urlretrieve(ffmpeg_url, ffmpeg_zip)
                    
                    self.write_log(">>> [環境] 正在執行解壓縮...")
                    subprocess.run(["tar", "-xf", ffmpeg_zip], cwd=base_path, shell=True, creationflags=0x08000000)
                    
                    extracted_folder = os.path.join(base_path, "ffmpeg-master-latest-win64-gpl")
                    if os.path.exists(extracted_folder):
                        if os.path.exists(ffmpeg_dir): shutil.rmtree(ffmpeg_dir)
                        os.rename(extracted_folder, ffmpeg_dir)
                    if os.path.exists(ffmpeg_zip): os.remove(ffmpeg_zip)
                
                self.write_log(">>> [系統] 環境建置完成。")
                self.after(0, lambda: self.lbl_status.configure(text="準備完成", text_color="#F1C40F"))
                self.after(0, lambda: self.toggle_ui_state("normal"))
            except Exception as e:
                self.write_log(f">>> [錯誤] 初始化失敗: {e}")

        threading.Thread(target=download_task, daemon=True).start()

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

    def clean_temp_files(self):
        root_path = self.output_dir.get()
        if not root_path or not os.path.exists(root_path): return
        temp_patterns = ['*.part', '*.ytdl', '*.temp', '*.webm', '*.m4a', '*.mp4.part']
        for root, dirs, files in os.walk(root_path):
            for pattern in temp_patterns:
                for f in glob.glob(os.path.join(root, pattern)):
                    try: os.remove(f)
                    except: pass

    def stop_t(self):
        if self.download_proc:
            try:
                p = psutil.Process(self.download_proc.pid)
                for child in p.children(recursive=True): child.kill()
                p.kill()
            except: pass
        self.downloading = False
        self.clean_temp_files()
        self.lbl_status.configure(text="已停止", text_color="#C0392B")
        self.write_log(">>> [系統] 任務已手動中止。")
        self.btn_run.configure(state="normal")

    def on_closing(self):
        if self.downloading: self.stop_t()
        self.destroy()

    def start_task(self):
        url, path = self.url.get().strip(), self.output_dir.get().strip()
        if not path or not url:
            self.lbl_status.configure(text="資訊不全", text_color="#E74C3C")
            return
        self.downloading = True
        self.total_count = self.current_idx = self.last_logged_idx = self.actual_processed_count = 0 
        self.is_finished_logged = self.has_error = False
        self.btn_run.configure(state="disabled")
        self.bar.set(0)
        self.lbl_status.configure(text="分析中...", text_color="#F1C40F")
        self.txt_log.delete("1.0", "end")
        self.write_log(f">>> [系統] 任務啟動 | 儲存至: {path}")
        threading.Thread(target=self.run_process, args=(url, path.replace("\\", "/")), daemon=True).start()
        self.poll_output()

    def run_process(self, url, path):
        mode = self.mode.get()
        is_pl = mode in ["3", "4"]
        
        # 修正 3：使用 self.get_base_path() 定位 EXE 旁邊的組件
        base_path = self.get_base_path()
        ffmpeg_bin_path = os.path.join(base_path, "ffmpeg", "bin")
        ytdlp_exe_path = os.path.join(base_path, "yt-dlp.exe")
        
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        cmd = [ytdlp_exe_path, "--newline", "--encoding", "utf-8", "--ignore-errors", "--no-overwrites", "--ffmpeg-location", ffmpeg_bin_path]
        
        if is_pl: tpl = f"{path}/%(uploader)s/%(playlist_title)s/%(title)s.%(ext)s"
        else:
            cmd.append("--no-playlist")
            tpl = f"{path}/%(uploader)s/%(title)s.%(ext)s"
        cmd.extend(["-o", tpl])
        
        if mode in ["1", "3"]: cmd += ["-x", "--audio-format", "mp3"]
        else: cmd += ["-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"]
        cmd.append(url)

        self.download_proc = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            text=True, 
            encoding='utf-8', 
            errors='replace', 
            env=env,
            creationflags=0x08000000
        )
        
        for line in iter(self.download_proc.stdout.readline, ''):
            if not self.downloading: break
            self.msg_queue.append(line.strip())
        self.msg_queue.append("END_SIGNAL")

    def poll_output(self):
        is_pl = self.mode.get() in ["3", "4"]
        while self.msg_queue:
            line = self.msg_queue.popleft()
            if "END_SIGNAL" in line:
                if self.has_error or self.actual_processed_count == 0:
                    self.lbl_status.configure(text="下載失敗", text_color="#E74C3C")
                else:
                    self.bar.set(1)
                    self.lbl_status.configure(text="下載完成", text_color="#2ECC71")
                    self.write_log(f">>> [完成] 任務成功處理。")
                self.btn_run.configure(state="normal")
                self.downloading = False
                return

            if "ERROR:" in line:
                self.has_error = True
                self.write_log(f">>> [錯誤] {line.split('ERROR: ')[-1]}")

            if "[download] Destination:" in line:
                fname = os.path.basename(line.split("Destination: ")[-1])
                self.write_log(f">>> [下載] 開始: {fname}")
                self.actual_processed_count += 1
            
            if "has already been downloaded" in line:
                fname = os.path.basename(line.split("] ")[-1].split(" has")[0])
                self.write_log(f">>> [跳過] 檔案已存在: {fname}")
                self.actual_processed_count += 1

            if "[ExtractAudio]" in line: self.write_log(">>> [處理] 轉碼 MP3 中...")
            if "[Merger]" in line: self.write_log(">>> [處理] 合併影音中...")

            is_done_signal = "[ExtractAudio]" in line or "[Merger]" in line or "already been downloaded" in line or "100%" in line

            if is_pl:
                pl_match = re.search(r"item (\d+) of (\d+)", line, re.IGNORECASE)
                if pl_match:
                    self.current_idx, self.total_count = int(pl_match.group(1)), int(pl_match.group(2))
                    display_done = self.current_idx - (0 if is_done_signal else 1)
                    if display_done > self.last_logged_idx:
                        self.write_log(f">>> [進度] 播放清單項目: {display_done} / {self.total_count}")
                        self.last_logged_idx = display_done
                    self.lbl_status.configure(text=f"{display_done} / {self.total_count}")
                    self.bar.set(display_done / self.total_count if self.total_count > 0 else 0)
            else:
                pct_match = re.search(r"(\d+\.\d+)%", line)
                if pct_match:
                    p = float(pct_match.group(1))
                    self.lbl_status.configure(text=f"{int(p)}%")
                    self.bar.set(p / 100)

        if self.downloading:
            self.after(50, self.poll_output)

if __name__ == "__main__":
    Downloader_tk().mainloop()
