import customtkinter as ctk
from views.login_view import LoginView
from views.downloader_view import DownloaderView
from models.database import Database
from controllers.download_controller import DownloadController
import os
import json

class AppController:
    def __init__(self):
        # Initialize the main window
        self.root = ctk.CTk()
        self.root.title("YouTube Downloader Pro")
        self.root.geometry("1200x800")
        
        # Set appearance mode
        self.appearance_mode = "light"
        ctk.set_appearance_mode(self.appearance_mode)
        
        # Initialize database and controllers
        self.db = Database()
        self.download_controller = DownloadController(self.db)
        
        # Current user state
        self.current_user = None
        
        # Initialize views
        self.login_view = LoginView(self.root, self)
        self.downloader_view = None
        
        # Start with login view
        self.show_login()
    
    def show_login(self):
        if self.downloader_view:
            self.downloader_view.hide()
        self.login_view.show()
    
    def show_downloader(self):
        self.login_view.hide()
        if not self.downloader_view:
            self.downloader_view = DownloaderView(self.root, self)
        self.downloader_view.show()
    
    def login(self, username, password):
        success, message = self.db.login_user(username, password)
        if success:
            self.current_user = username
            self.show_downloader()
        return success, message
    
    def register(self, username, email, password):
        success, message = self.db.register_user(username, email, password)
        return success, message
    
    def logout(self):
        self.current_user = None
        self.show_login()
    
    def toggle_theme(self):
        self.appearance_mode = "dark" if self.appearance_mode == "light" else "light"
        ctk.set_appearance_mode(self.appearance_mode)
        if self.downloader_view:
            self.downloader_view.theme_button.configure(
                text="🌙" if self.appearance_mode == "light" else "☀️"
            )
    
    def check_url(self, url):
        success, result = self.download_controller.check_url(url)
        if success:
            self.downloader_view.display_video_info(result)
        else:
            messagebox.showerror("Erreur", result)
    
    def download(self, video_info):
        content_type = self.downloader_view.content_type.get()
        format_type = self.downloader_view.format_var.get()
        quality = self.downloader_view.quality_var.get()
        download_path = self.downloader_view.path_entry.get()
        
        if not download_path:
            messagebox.showerror("Erreur", "Veuillez sélectionner un dossier de destination")
            return
        
        self.download_controller.download(
            video_info['url'],
            content_type,
            format_type,
            quality,
            download_path,
            self.current_user,
            self.downloader_view.update_progress
        )
    
    def on_content_type_change(self, choice):
        self.download_controller.on_content_type_change(choice)
    
    def get_user_download_count(self):
        return self.db.get_user_download_count(self.current_user)
    
    def run(self):
        self.root.mainloop() 