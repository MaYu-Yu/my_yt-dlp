import os
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

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class Downloader_tk(ctk.CTk):
    def __init__(self):
        super().__init__()
        icon_path = os.path.join(os.path.dirname(__file__), "ico", "i.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)
        self.title("YouTube Downloader")
        self.geometry("900x820")
        self.configure(fg_color="#0D0D0D")
        
        # 1. 初始隱藏視窗，避免環境未就緒時被操作
        self.withdraw() 

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
        # 2. 啟動環境檢查
        self.auto_setup_env()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def auto_setup_env(self):
        """檢查 yt-dlp.exe 是否存在，若無則下載，完成後顯示主介面"""
        def download_task():
            if not os.path.exists("yt-dlp.exe"):
                # 這裡可以考慮輸出到終端機提示正在初始化
                print("正在初始化環境 (下載 yt-dlp.exe)...")
                try:
                    urllib.request.urlretrieve(
                        "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe", 
                        "yt-dlp.exe"
                    )
                    print("環境初始化完成。")
                except Exception as e:
                    print(f"環境初始化失敗: {e}")
                    self.destroy() # 若下載失敗則關閉程式
                    return
            
            # 3. 使用 after 回到主線程顯示視窗，避免執行緒安全問題
            self.after(0, self.show_main_window)
        threading.Thread(target=download_task, daemon=True).start()
        
    def show_main_window(self):
        """顯示主視窗並將其移至最前端"""
        self.deiconify()
        self.attributes("-topmost", True)  # 短暫置頂確保使用者看見
        self.attributes("-topmost", False) # 隨即取消置頂，恢復正常操作
        self.write_log("環境檢查通過，程式就緒。")

    def setup_ui(self):
        ctk.CTkLabel(self, text="YOUTUBE DOWNLOADER", font=ctk.CTkFont(size=38, weight="bold"), text_color="#3498DB").pack(pady=(30, 10))
        
        self.f_main = ctk.CTkFrame(self, fg_color="#161616", corner_radius=15)
        self.f_main.pack(fill="both", padx=40, pady=10, expand=True)

        ctk.CTkLabel(self.f_main, text="--- 請點擊下方輸入框以選擇儲存根目錄 ---", font=ctk.CTkFont(size=13), text_color="#7F8C8D").pack(pady=(15, 0))
        self.ent_p = ctk.CTkEntry(self.f_main, textvariable=self.output_dir, font=ctk.CTkFont(size=16), height=45, placeholder_text="尚未選擇路徑...", justify="center")
        self.ent_p.pack(fill="x", padx=20, pady=(5, 15))
        self.ent_p.bind("<Button-1>", lambda e: self.browse_folder())
        self.ent_p.configure(state="readonly") 

        self.f_m = ctk.CTkFrame(self.f_main, fg_color="transparent")
        self.f_m.pack(fill="x", pady=10)
        modes = [("下載 MP3", "1"), ("下載影片 MP4", "2"), ("下載播放清單 MP3", "3"), ("下載播放清單 MP4", "4")]
        for t, v in modes:
            ctk.CTkRadioButton(self.f_m, text=t, variable=self.mode, value=v).pack(side="left", padx=25)

        ctk.CTkLabel(self.f_main, text="--- 請在下方欄位貼上 YouTube 影片或播放清單網址 ---", font=ctk.CTkFont(size=13), text_color="#7F8C8D").pack(pady=(15, 0))
        self.ent_u = ctk.CTkEntry(self.f_main, textvariable=self.url, placeholder_text="在此貼上網址 (例如: https://www.youtube.com/watch?v=...)", height=60, font=ctk.CTkFont(size=18), border_color="#3498DB", border_width=2, justify="center")
        self.ent_u.pack(fill="x", padx=20, pady=(5, 15))

        self.lbl_status = ctk.CTkLabel(self.f_main, text="準備完成", font=ctk.CTkFont(size=52, weight="bold"), text_color="#F1C40F")
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

        self.txt_log = ctk.CTkTextbox(self, height=130, font=ctk.CTkFont(family="Consolas", size=14), fg_color="#000000", text_color="#2ECC71")
        self.txt_log.pack(fill="both", padx=40, pady=(0, 20))

    def write_log(self, msg):
        self.txt_log.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        self.txt_log.see("end")

    def clean_temp_files(self):
        root_path = self.output_dir.get()
        if not root_path or not os.path.exists(root_path): return
        temp_patterns = ['*.part', '*.ytdl', '*.temp', '*.webm', '*.m4a', '*.mp4.part']
        for root, dirs, files in os.walk(root_path):
            for pattern in temp_patterns:
                for f in glob.glob(os.path.join(root, pattern)):
                    try: os.remove(f)
                    except: pass

    def on_closing(self):
        if self.downloading: self.stop_t()
        self.destroy()

    def browse_folder(self):
        f = filedialog.askdirectory()
        if f: self.output_dir.set(f)

    def stop_t(self):
        if self.download_proc:
            try:
                p = psutil.Process(self.download_proc.pid)
                for child in p.children(recursive=True): child.kill()
                p.kill()
            except: pass
        self.downloading = False
        self.clean_temp_files()
        self.lbl_status.configure(text="停止", text_color="#C0392B")
        self.write_log("任務已停止。")

    def start_task(self):
        url, path = self.url.get().strip(), self.output_dir.get().strip()
        
        if not path and not url:
            self.lbl_status.configure(text="請填寫資訊", text_color="#E74C3C")
            self.write_log("錯誤：請選擇儲存路徑並填入 YouTube 網址。")
            return
        if not path:
            self.lbl_status.configure(text="請選擇路徑", text_color="#E74C3C")
            self.write_log("錯誤：尚未選擇儲存根目錄。")
            return
        if not url:
            self.lbl_status.configure(text="請輸入網址", text_color="#E74C3C")
            self.write_log("錯誤：尚未輸入 YouTube 網址。")
            return

        self.downloading = True
        self.total_count = 0
        self.current_idx = 0
        self.last_logged_idx = 0
        self.is_finished_logged = False
        self.has_error = False
        self.actual_processed_count = 0 
        
        self.btn_run.configure(state="disabled")
        self.bar.set(0)
        self.lbl_status.configure(text="分析中...", text_color="#F1C40F")
        self.txt_log.delete("1.0", "end")
        
        self.write_log(f"任務啟動 | 儲存路徑: {path}")
        threading.Thread(target=self.run_process, args=(url, path.replace("\\", "/")), daemon=True).start()
        self.poll_output()

    def run_process(self, url, path):
        mode = self.mode.get()
        is_pl = mode in ["3", "4"]
        cmd = ["yt-dlp", "--newline", "--ignore-errors", "--no-overwrites"]
        if is_pl:
            tpl = f"{path}/%(uploader)s/%(playlist_title)s/%(title)s.%(ext)s"
        else:
            cmd.append("--no-playlist")
            tpl = f"{path}/%(uploader)s/%(title)s.%(ext)s"
        cmd.extend(["-o", tpl])
        if mode in ["1", "3"]: cmd += ["-x", "--audio-format", "mp3"]
        else: cmd += ["-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"]
        cmd.append(url)

        self.download_proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace', creationflags=0x08000000)
        for line in iter(self.download_proc.stdout.readline, ''):
            if not self.downloading: break
            self.msg_queue.append(line.strip())
        self.msg_queue.append("END_SIGNAL")

    def poll_output(self):
        is_pl = self.mode.get() in ["3", "4"]
        while self.msg_queue:
            line = self.msg_queue.popleft()
            if "END_SIGNAL" in line:
                # 關鍵判定：如果錯誤發生，或者是根本沒處理到任何影片
                if self.has_error or self.actual_processed_count == 0:
                    self.lbl_status.configure(text="下載失敗", text_color="#E74C3C")
                    if self.actual_processed_count == 0:
                        self.write_log("--- 任務結束：未偵測到任何有效影片內容 ---")
                    else:
                        self.write_log("--- 任務結束：過程中發生錯誤 ---")
                else:
                    self.bar.set(1)
                    self.lbl_status.configure(text="下載完成", text_color="#2ECC71")
                    self.write_log("--- 下載任務結束 ---")
                
                self.btn_run.configure(state="normal")
                self.downloading = False
                return

            if "ERROR:" in line:
                self.has_error = True
                self.write_log(f"錯誤: {line.split('ERROR: ')[-1]}")

            if "[download] Destination:" in line:
                fname = os.path.basename(line.split("Destination: ")[-1])
                self.write_log(f"開始下載: {fname}")
                self.actual_processed_count += 1 # 偵測到目的地，計數增加
            
            if "has already been downloaded" in line:
                fname = line.split("] ")[-1].split(" has")[0]
                self.write_log(f"(已存在)跳過: {fname}")
                self.actual_processed_count += 1 # 已存在也算是有處理到

            is_done_signal = "[ExtractAudio]" in line or "[Merger]" in line or "already been downloaded" in line or "100%" in line

            if is_pl:
                pl_match = re.search(r"item (\d+) of (\d+)", line, re.IGNORECASE)
                if pl_match:
                    self.current_idx, self.total_count = int(pl_match.group(1)), int(pl_match.group(2))
                    display_done = self.current_idx - 1
                    if is_done_signal:
                        display_done = self.current_idx
                        if display_done > self.last_logged_idx:
                            self.write_log(f"完成項目: {display_done} / {self.total_count}")
                            self.last_logged_idx = display_done
                    self.lbl_status.configure(text=f"{display_done} / {self.total_count}")
                    self.bar.set(display_done / self.total_count if self.total_count > 0 else 0)
            else:
                pct_match = re.search(r"(\d+\.\d+)%", line)
                if pct_match:
                    p = float(pct_match.group(1))
                    self.lbl_status.configure(text=f"{int(p)}%")
                    self.bar.set(p / 100)
                
                if not self.is_finished_logged and ("[ExtractAudio]" in line or "[Merger]" in line):
                    self.write_log("單一影片下載與處理完成。")
                    self.is_finished_logged = True
                elif not self.is_finished_logged and "already been downloaded" in line:
                    self.write_log("單一影片已存在，跳過處理。")
                    self.is_finished_logged = True

        if self.downloading:
            self.after(50, self.poll_output)

if __name__ == "__main__":
    Downloader_tk().mainloop()