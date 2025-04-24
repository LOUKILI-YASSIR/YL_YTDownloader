import os
import yt_dlp
import threading
import queue
import time
from datetime import datetime
from pymongo import MongoClient
from customtkinter import CTkFrame, CTkLabel, CTkProgressBar
from tkinter import messagebox

class DownloadManager:
    def __init__(self, app):
        self.app = app
        self.client = MongoClient(os.getenv('MONGODB_URI'))
        self.db = self.client['youtube_downloader']
        self.downloads = self.db['downloads']
        self.download_queue = queue.Queue()
        self.current_download = None
        self.download_thread = None
        self.stop_download = False
        
    def start_download(self, url, content_type, format_type, quality, progress_callback):
        if self.current_download:
            messagebox.showwarning("Warning", "A download is already in progress")
            return
            
        self.stop_download = False
        self.download_thread = threading.Thread(
            target=self._download,
            args=(url, content_type, format_type, quality, progress_callback)
        )
        self.download_thread.start()
        
    def _download(self, url, content_type, format_type, quality, progress_callback):
        try:
            # Configure download options
            ydl_opts = {
                'format': self._get_format_string(content_type, format_type, quality),
                'outtmpl': os.path.join(
                    os.getenv('DOWNLOAD_PATH', 'downloads'),
                    '%(title)s.%(ext)s'
                ),
                'progress_hooks': [lambda d: self._progress_hook(d, progress_callback)],
                'postprocessors': []
            }
            
            # Add post-processing options
            if content_type == "Audio":
                ydl_opts['postprocessors'].append({
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': format_type,
                    'preferredquality': quality.replace('kbps', '')
                })
                
            # Start download
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                # Save download record
                self._save_download_record(info, content_type, format_type, quality)
                
                progress_callback(1.0, "Download completed")
                
        except Exception as e:
            progress_callback(0.0, f"Error: {str(e)}")
            messagebox.showerror("Error", f"Download failed: {str(e)}")
        finally:
            self.current_download = None
            
    def _get_format_string(self, content_type, format_type, quality):
        if content_type == "Video":
            return f"bestvideo[height<={quality.replace('p', '')}]+bestaudio/best[height<={quality.replace('p', '')}]"
        elif content_type == "Audio":
            return "bestaudio/best"
        else:  # Playlist
            return "best"
            
    def _progress_hook(self, d, progress_callback):
        if self.stop_download:
            raise Exception("Download stopped by user")
            
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)
            speed = d.get('speed', 0)
            
            if total > 0:
                progress = downloaded / total
                speed_mb = speed / 1024 / 1024 if speed else 0
                progress_callback(progress, f"Downloading: {progress*100:.1f}% ({speed_mb:.1f} MB/s)")
                
        elif d['status'] == 'finished':
            progress_callback(1.0, "Processing...")
            
    def _save_download_record(self, info, content_type, format_type, quality):
        download_record = {
            'user_id': self.app.current_user['_id'],
            'title': info.get('title', 'Unknown'),
            'url': info.get('webpage_url', ''),
            'content_type': content_type,
            'format': format_type,
            'quality': quality,
            'duration': info.get('duration', 0),
            'filesize': info.get('filesize', 0),
            'thumbnail': info.get('thumbnail', ''),
            'download_date': datetime.now(),
            'status': 'completed'
        }
        
        self.downloads.insert_one(download_record)
        
    def stop_current_download(self):
        if self.current_download:
            self.stop_download = True
            messagebox.showinfo("Info", "Download stopped")
            
    def get_download_history(self, user_id, limit=10):
        return list(self.downloads.find(
            {'user_id': user_id},
            sort=[('download_date', -1)],
            limit=limit
        ))
        
    def get_download_stats(self, user_id):
        stats = {
            'total_downloads': self.downloads.count_documents({'user_id': user_id}),
            'total_videos': self.downloads.count_documents({
                'user_id': user_id,
                'content_type': 'Video'
            }),
            'total_audio': self.downloads.count_documents({
                'user_id': user_id,
                'content_type': 'Audio'
            }),
            'total_playlists': self.downloads.count_documents({
                'user_id': user_id,
                'content_type': 'Playlist'
            }),
            'total_size': sum(d.get('filesize', 0) for d in self.downloads.find({'user_id': user_id}))
        }
        
        return stats
        
    def clear_download_history(self, user_id):
        self.downloads.delete_many({'user_id': user_id})
        
    def export_download_history(self, user_id, format='csv'):
        downloads = self.get_download_history(user_id, limit=None)
        
        if format == 'csv':
            import csv
            filename = f"download_history_{user_id}.csv"
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'Title', 'URL', 'Content Type', 'Format',
                    'Quality', 'Duration', 'File Size', 'Download Date'
                ])
                for d in downloads:
                    writer.writerow([
                        d['title'], d['url'], d['content_type'],
                        d['format'], d['quality'], d['duration'],
                        d['filesize'], d['download_date']
                    ])
        elif format == 'json':
            import json
            filename = f"download_history_{user_id}.json"
            with open(filename, 'w') as f:
                json.dump(downloads, f, default=str)
                
        return filename 