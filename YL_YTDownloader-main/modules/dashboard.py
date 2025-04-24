import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
from datetime import datetime, timedelta
from customtkinter import CTkFrame, CTkLabel, CTkButton, CTkScrollableFrame
from tkinter import messagebox

class Dashboard:
    def __init__(self, app):
        self.app = app
        self.client = app.client
        self.db = app.db
        self.downloads = app.db['downloads']
        
    def setup_stats(self, parent):
        # Create stats container
        stats_container = CTkFrame(parent)
        stats_container.pack(fill="x", padx=10, pady=10)
        
        # Get user stats
        stats = self.app.download_manager.get_download_stats(self.app.current_user['_id'])
        
        # Create stats grid
        stats_grid = CTkFrame(stats_container)
        stats_grid.pack(fill="x", padx=10, pady=10)
        
        # Total downloads
        total_frame = CTkFrame(stats_grid)
        total_frame.pack(side="left", padx=5, fill="x", expand=True)
        CTkLabel(total_frame, text="Total Downloads", font=("Helvetica", 14, "bold")).pack()
        CTkLabel(total_frame, text=str(stats['total_downloads']), font=("Helvetica", 24)).pack()
        
        # Videos
        videos_frame = CTkFrame(stats_grid)
        videos_frame.pack(side="left", padx=5, fill="x", expand=True)
        CTkLabel(videos_frame, text="Videos", font=("Helvetica", 14, "bold")).pack()
        CTkLabel(videos_frame, text=str(stats['total_videos']), font=("Helvetica", 24)).pack()
        
        # Audio
        audio_frame = CTkFrame(stats_grid)
        audio_frame.pack(side="left", padx=5, fill="x", expand=True)
        CTkLabel(audio_frame, text="Audio", font=("Helvetica", 14, "bold")).pack()
        CTkLabel(audio_frame, text=str(stats['total_audio']), font=("Helvetica", 24)).pack()
        
        # Playlists
        playlists_frame = CTkFrame(stats_grid)
        playlists_frame.pack(side="left", padx=5, fill="x", expand=True)
        CTkLabel(playlists_frame, text="Playlists", font=("Helvetica", 14, "bold")).pack()
        CTkLabel(playlists_frame, text=str(stats['total_playlists']), font=("Helvetica", 24)).pack()
        
        # Total size
        size_frame = CTkFrame(stats_grid)
        size_frame.pack(side="left", padx=5, fill="x", expand=True)
        CTkLabel(size_frame, text="Total Size", font=("Helvetica", 14, "bold")).pack()
        CTkLabel(size_frame, text=self._format_size(stats['total_size']), font=("Helvetica", 24)).pack()
        
        # Create charts
        self._create_downloads_chart(stats_container)
        self._create_content_type_chart(stats_container)
        
    def _create_downloads_chart(self, parent):
        # Get download data for last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        pipeline = [
            {
                "$match": {
                    "user_id": self.app.current_user['_id'],
                    "download_date": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$download_date"}},
                    "count": {"$sum": 1}
                }
            },
            {
                "$sort": {"_id": 1}
            }
        ]
        
        data = list(self.downloads.aggregate(pipeline))
        
        # Create figure
        fig, ax = plt.subplots(figsize=(8, 4))
        dates = [d['_id'] for d in data]
        counts = [d['count'] for d in data]
        
        ax.plot(dates, counts, marker='o')
        ax.set_title('Downloads Last 30 Days')
        ax.set_xlabel('Date')
        ax.set_ylabel('Downloads')
        plt.xticks(rotation=45)
        
        # Add to tkinter
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x", padx=10, pady=10)
        
    def _create_content_type_chart(self, parent):
        # Get content type distribution
        pipeline = [
            {
                "$match": {"user_id": self.app.current_user['_id']}
            },
            {
                "$group": {
                    "_id": "$content_type",
                    "count": {"$sum": 1}
                }
            }
        ]
        
        data = list(self.downloads.aggregate(pipeline))
        
        # Create figure
        fig, ax = plt.subplots(figsize=(8, 4))
        types = [d['_id'] for d in data]
        counts = [d['count'] for d in data]
        
        ax.pie(counts, labels=types, autopct='%1.1f%%')
        ax.set_title('Content Type Distribution')
        
        # Add to tkinter
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x", padx=10, pady=10)
        
    def setup_history(self, parent):
        # Create history container
        history_container = CTkFrame(parent)
        history_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Get download history
        history = self.app.download_manager.get_download_history(self.app.current_user['_id'])
        
        # Create scrollable frame
        scroll_frame = CTkScrollableFrame(history_container)
        scroll_frame.pack(fill="both", expand=True)
        
        # Add history items
        for item in history:
            self._create_history_item(scroll_frame, item)
            
    def _create_history_item(self, parent, item):
        # Create item frame
        item_frame = CTkFrame(parent)
        item_frame.pack(fill="x", padx=5, pady=5)
        
        # Title
        CTkLabel(item_frame, text=item['title'], font=("Helvetica", 14, "bold")).pack(anchor="w")
        
        # Details
        details_frame = CTkFrame(item_frame)
        details_frame.pack(fill="x")
        
        # Content type and format
        CTkLabel(details_frame, 
                text=f"Type: {item['content_type']} | Format: {item['format']} | Quality: {item['quality']}").pack(side="left")
        
        # Date
        CTkLabel(details_frame, 
                text=item['download_date'].strftime("%Y-%m-%d %H:%M")).pack(side="right")
        
        # Actions
        actions_frame = CTkFrame(item_frame)
        actions_frame.pack(fill="x")
        
        # Open button
        CTkButton(actions_frame, text="Open", 
                 command=lambda: self._open_download(item)).pack(side="left", padx=5)
        
        # Delete button
        CTkButton(actions_frame, text="Delete", 
                 command=lambda: self._delete_download(item)).pack(side="left", padx=5)
        
    def _open_download(self, item):
        # Get file path
        file_path = os.path.join(
            os.getenv('DOWNLOAD_PATH', 'downloads'),
            f"{item['title']}.{item['format']}"
        )
        
        if os.path.exists(file_path):
            os.startfile(file_path)
        else:
            messagebox.showerror("Error", "File not found")
            
    def _delete_download(self, item):
        if messagebox.askyesno("Confirm", "Delete this download?"):
            self.downloads.delete_one({'_id': item['_id']})
            self.setup_history(self.app.dashboard_tab)
            
    def _format_size(self, size_bytes):
        """Format size in bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB" 