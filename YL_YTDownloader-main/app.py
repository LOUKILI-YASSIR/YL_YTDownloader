import os
import sys
import customtkinter as ctk
from dotenv import load_dotenv
from modules.auth import AuthManager
from modules.downloader import DownloadManager
from modules.dashboard import Dashboard
from modules.profile import ProfileManager
from modules.utils import setup_logging, load_config

class YouTubeDownloader(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Load environment variables and configuration
        load_dotenv()
        self.config = load_config()
        
        # Setup logging
        self.logger = setup_logging()
        
        # Initialize managers
        self.auth_manager = AuthManager(self)
        self.download_manager = DownloadManager(self)
        self.dashboard = Dashboard(self)
        self.profile_manager = ProfileManager(self)
        
        # Configure window
        self.title("YouTube Downloader Pro")
        self.geometry("1200x800")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Initialize UI
        self.setup_ui()
        
    def setup_ui(self):
        # Create main container
        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create tab view
        self.tab_view = ctk.CTkTabview(self.main_container)
        self.tab_view.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add tabs
        self.download_tab = self.tab_view.add("Download")
        self.dashboard_tab = self.tab_view.add("Dashboard")
        self.profile_tab = self.tab_view.add("Profile")
        
        # Setup each tab
        self.setup_download_tab()
        self.setup_dashboard_tab()
        self.setup_profile_tab()
        
    def setup_download_tab(self):
        # URL input
        url_frame = ctk.CTkFrame(self.download_tab)
        url_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(url_frame, text="Video URL:").pack(side="left", padx=5)
        self.url_entry = ctk.CTkEntry(url_frame, width=400)
        self.url_entry.pack(side="left", padx=5)
        
        # Content type selection
        type_frame = ctk.CTkFrame(self.download_tab)
        type_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(type_frame, text="Content Type:").pack(side="left", padx=5)
        self.content_type = ctk.CTkOptionMenu(type_frame, values=["Video", "Audio", "Playlist"])
        self.content_type.pack(side="left", padx=5)
        
        # Format selection
        format_frame = ctk.CTkFrame(self.download_tab)
        format_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(format_frame, text="Format:").pack(side="left", padx=5)
        self.format_var = ctk.StringVar(value="mp4")
        self.format_menu = ctk.CTkOptionMenu(format_frame, variable=self.format_var, values=["mp4", "webm", "mkv"])
        self.format_menu.pack(side="left", padx=5)
        
        # Quality selection
        quality_frame = ctk.CTkFrame(self.download_tab)
        quality_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(quality_frame, text="Quality:").pack(side="left", padx=5)
        self.quality_var = ctk.StringVar(value="720p")
        self.quality_menu = ctk.CTkOptionMenu(quality_frame, variable=self.quality_var, values=["1080p", "720p", "480p", "360p"])
        self.quality_menu.pack(side="left", padx=5)
        
        # Download button
        download_button = ctk.CTkButton(self.download_tab, text="Download", command=self.start_download)
        download_button.pack(pady=10)
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(self.download_tab)
        self.progress_bar.pack(fill="x", padx=10, pady=10)
        self.progress_bar.set(0)
        
        # Status label
        self.status_label = ctk.CTkLabel(self.download_tab, text="")
        self.status_label.pack(pady=5)
        
    def setup_dashboard_tab(self):
        # Statistics frame
        stats_frame = ctk.CTkFrame(self.dashboard_tab)
        stats_frame.pack(fill="x", padx=10, pady=10)
        
        # Add statistics widgets
        self.dashboard.setup_stats(stats_frame)
        
        # Download history
        history_frame = ctk.CTkFrame(self.dashboard_tab)
        history_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add history widgets
        self.dashboard.setup_history(history_frame)
        
    def setup_profile_tab(self):
        # Profile info frame
        info_frame = ctk.CTkFrame(self.profile_tab)
        info_frame.pack(fill="x", padx=10, pady=10)
        
        # Add profile widgets
        self.profile_manager.setup_profile_info(info_frame)
        
        # Settings frame
        settings_frame = ctk.CTkFrame(self.profile_tab)
        settings_frame.pack(fill="x", padx=10, pady=10)
        
        # Add settings widgets
        self.profile_manager.setup_settings(settings_frame)
        
    def start_download(self):
        url = self.url_entry.get()
        content_type = self.content_type.get()
        format_type = self.format_var.get()
        quality = self.quality_var.get()
        
        if not url:
            self.status_label.configure(text="Please enter a valid URL")
            return
            
        self.download_manager.start_download(
            url=url,
            content_type=content_type,
            format_type=format_type,
            quality=quality,
            progress_callback=self.update_progress
        )
        
    def update_progress(self, progress, status):
        self.progress_bar.set(progress)
        self.status_label.configure(text=status)

if __name__ == "__main__":
    app = YouTubeDownloader()
    app.mainloop() 