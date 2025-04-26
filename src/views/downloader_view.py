import customtkinter as ctk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
from io import BytesIO
import requests
import os

class DownloaderView:
    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller
        self.setup_downloader_ui()
    
    def setup_downloader_ui(self):
        # Create main frame with modern styling
        self.downloader_frame = ctk.CTkFrame(self.parent, corner_radius=15)
        self.downloader_frame.pack(pady=20, padx=20, fill='both', expand=True)
        
        # Header with logo and title
        header_frame = ctk.CTkFrame(self.downloader_frame, fg_color="transparent")
        header_frame.pack(pady=(20, 10), padx=10, fill='x')
        
        # Logo and title
        logo_label = ctk.CTkLabel(header_frame, text="🎬", font=("Helvetica", 45))
        logo_label.pack(side='left', padx=10)
        
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(side='left', padx=10)
        ctk.CTkLabel(title_frame, text="YouTube Downloader Pro", font=("Helvetica", 26, "bold")).pack()
        ctk.CTkLabel(title_frame, text=f"Bienvenue, {self.controller.current_user}", font=("Helvetica", 14, "italic")).pack()
        
        # User stats in header
        stats_label = ctk.CTkLabel(header_frame, 
                                 text=f"📊 Téléchargements: {self.controller.get_user_download_count()}", 
                                 font=("Helvetica", 12))
        stats_label.pack(side='left', padx=20)
        
        # Theme button
        self.theme_button = ctk.CTkButton(header_frame, 
                                         text="🌙" if self.controller.appearance_mode == "light" else "☀️",
                                         command=self.controller.toggle_theme, 
                                         width=40,
                                         height=40,
                                         corner_radius=20)
        self.theme_button.pack(side='right', padx=10)
        
        # Logout button
        logout_button = ctk.CTkButton(header_frame,
                                    text="Déconnexion",
                                    command=self.controller.logout,
                                    width=100,
                                    height=40,
                                    corner_radius=10)
        logout_button.pack(side='right', padx=10)
        
        # Create tabview
        self.tabview = ctk.CTkTabview(self.downloader_frame)
        self.tabview.pack(pady=20, padx=20, fill='both', expand=True)
        
        # Add tabs
        self.download_tab = self.tabview.add("Téléchargement")
        self.dashboard_tab = self.tabview.add("Tableau de bord")
        self.profile_tab = self.tabview.add("Profil")
        
        # Setup download tab
        self.setup_download_tab()
        
        # Setup dashboard tab
        self.setup_dashboard_tab()
        
        # Setup profile tab
        self.setup_profile_tab()
    
    def setup_download_tab(self):
        # Main container with vertical layout
        main_container = ctk.CTkFrame(self.download_tab)
        main_container.pack(pady=10, padx=10, fill='both', expand=True)
        
        # Top section - Input and options
        top_section = ctk.CTkFrame(main_container, corner_radius=15)
        top_section.pack(padx=10, pady=10, fill='x')
        
        # URL input
        url_frame = ctk.CTkFrame(top_section, fg_color="transparent")
        url_frame.pack(pady=(5, 10), fill='x', padx=10)
        
        self.url_entry = ctk.CTkEntry(url_frame, 
                                    placeholder_text="Write your YouTube video link ....",
                                    height=50,
                                    width=600,
                                    corner_radius=20,
                                    font=("Helvetica", 20, "bold"))
        self.url_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        check_button = ctk.CTkButton(url_frame,
                                   text="Download",
                                   command=self.check_url,
                                   height=50,
                                   width=200,
                                   corner_radius=10,
                                   font=("Helvetica", 20, "bold"))
        check_button.pack(side='right')
        
        # Progress frame
        self.progress_frame = ctk.CTkFrame(top_section, fg_color="transparent")
        
        # Progress bar with status indicators
        progress_status_frame = ctk.CTkFrame(self.progress_frame, fg_color="transparent")
        progress_status_frame.pack(fill='x', pady=5)
        
        self.progress_status = ctk.CTkLabel(progress_status_frame, text="⏳ En attente...", font=("Helvetica", 12))
        self.progress_status.pack(side='left', padx=5)
        
        self.progress_percentage = ctk.CTkLabel(progress_status_frame, text="0%", font=("Helvetica", 12, "bold"))
        self.progress_percentage.pack(side='right', padx=5)
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, height=15, corner_radius=5)
        self.progress_bar.pack(pady=5, fill='x')
        
        # Detailed progress information
        self.progress_details_frame = ctk.CTkFrame(self.progress_frame, fg_color="transparent")
        self.progress_details_frame.pack(fill='x')
        
        self.progress_label = ctk.CTkLabel(self.progress_details_frame, text="", font=("Helvetica", 12))
        self.progress_label.pack(side='left', padx=5)
        
        self.progress_time = ctk.CTkLabel(self.progress_details_frame, text="", font=("Helvetica", 12))
        self.progress_time.pack(side='right', padx=5)
        
        # Options section
        options_card = ctk.CTkFrame(top_section, corner_radius=10)
        options_card.pack(pady=10, padx=10, fill='x')
        
        # Content type selection
        type_frame = ctk.CTkFrame(options_card, fg_color="transparent")
        type_frame.pack(pady=5, padx=10, fill='x')
        
        ctk.CTkLabel(type_frame, text="📁 Type:", font=("Helvetica", 14)).pack(side='left', padx=5)
        self.content_type = ctk.StringVar(value="Vidéo")
        type_menu = ctk.CTkOptionMenu(type_frame,
                                    variable=self.content_type,
                                    values=["Vidéo", "Audio"],
                                    command=self.on_content_type_change,
                                    width=180,
                                    height=35,
                                    corner_radius=8)
        type_menu.pack(side='left', padx=5)
        
        # Format selection
        self.format_frame = ctk.CTkFrame(options_card, fg_color="transparent")
        self.format_frame.pack(pady=5, padx=10, fill='x')
        
        ctk.CTkLabel(self.format_frame, text="🎬 Format:", font=("Helvetica", 14)).pack(side='left', padx=5)
        self.format_var = ctk.StringVar(value="----")
        self.format_menu = ctk.CTkOptionMenu(self.format_frame,
                                           variable=self.format_var,
                                           values=["----"],
                                           width=150,
                                           height=35,
                                           corner_radius=8)
        self.format_menu.pack(side='left', padx=5)
        
        # Quality selection
        self.quality_frame = ctk.CTkFrame(options_card, fg_color="transparent")
        self.quality_frame.pack(pady=5, padx=10, fill='x')
        
        ctk.CTkLabel(self.quality_frame, text="🔍 Qualité:", font=("Helvetica", 12)).pack(side='left', padx=5)
        self.quality_var = ctk.StringVar(value="----")
        self.quality_menu = ctk.CTkOptionMenu(self.quality_frame,
                                            variable=self.quality_var,
                                            values=["----"],
                                            width=150,
                                            height=35,
                                            corner_radius=8)
        self.quality_menu.pack(side='left', padx=5)
        
        # Path selection
        path_frame = ctk.CTkFrame(options_card, fg_color="transparent")
        path_frame.pack(pady=5, padx=10, fill='x')
        
        ctk.CTkLabel(path_frame, text="📂 Destination:", font=("Helvetica", 12)).pack(side='left', padx=5)
        self.path_entry = ctk.CTkEntry(path_frame,
                                     placeholder_text="Sélectionnez un dossier",
                                     height=35,
                                     corner_radius=8)
        self.path_entry.pack(side='left', padx=5, fill='x', expand=True)
        
        browse_button = ctk.CTkButton(path_frame,
                                    text="Parcourir",
                                    command=self.browse_path,
                                    width=100,
                                    height=40,
                                    corner_radius=10)
        browse_button.pack(side='left', padx=5)
        
        # Video info frame
        self.info_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        self.info_frame.pack(pady=10, padx=10, fill='both', expand=True)
    
    def setup_dashboard_tab(self):
        # Create main container
        container = ctk.CTkFrame(self.dashboard_tab, fg_color="transparent")
        container.pack(pady=20, padx=20, fill='both', expand=True)
        
        # Graphs section
        graphs_frame = ctk.CTkFrame(container, corner_radius=15)
        graphs_frame.pack(pady=10, fill='x')
        
        ctk.CTkLabel(graphs_frame, text="Statistiques", font=("Helvetica", 16, "bold")).pack(pady=10)
        
        # Create two columns for graphs
        graphs_columns = ctk.CTkFrame(graphs_frame, fg_color="transparent")
        graphs_columns.pack(pady=10, fill='x')
        
        # Downloads by type graph
        type_graph_frame = ctk.CTkFrame(graphs_columns, corner_radius=10)
        type_graph_frame.pack(side='left', padx=10, fill='both', expand=True)
        ctk.CTkLabel(type_graph_frame, text="Téléchargements par type", font=("Helvetica", 14)).pack(pady=10)
        
        # Downloads over time graph
        time_graph_frame = ctk.CTkFrame(graphs_columns, corner_radius=10)
        time_graph_frame.pack(side='left', padx=10, fill='both', expand=True)
        ctk.CTkLabel(time_graph_frame, text="Téléchargements dans le temps", font=("Helvetica", 14)).pack(pady=10)
        
        # History section
        history_frame = ctk.CTkFrame(container, corner_radius=15)
        history_frame.pack(pady=10, fill='both', expand=True)
        
        ctk.CTkLabel(history_frame, text="Historique des téléchargements", font=("Helvetica", 16, "bold")).pack(pady=10)
        
        # Create scrollable frame for history items
        self.history_scroll = ctk.CTkScrollableFrame(history_frame, fg_color="transparent")
        self.history_scroll.pack(pady=10, padx=10, fill='both', expand=True)
    
    def setup_profile_tab(self):
        # Create main container
        container = ctk.CTkFrame(self.profile_tab, fg_color="transparent")
        container.pack(pady=20, padx=20, fill='both', expand=True)
        
        # Profile info section
        profile_frame = ctk.CTkFrame(container, corner_radius=15)
        profile_frame.pack(pady=10, fill='x')
        
        ctk.CTkLabel(profile_frame, text="Informations du profil", font=("Helvetica", 16, "bold")).pack(pady=10)
        
        # Username
        username_frame = ctk.CTkFrame(profile_frame, fg_color="transparent")
        username_frame.pack(pady=5, fill='x')
        
        ctk.CTkLabel(username_frame, text="Nom d'utilisateur:", font=("Helvetica", 14)).pack(side='left', padx=5)
        self.username_label = ctk.CTkLabel(username_frame, text=self.controller.current_user, font=("Helvetica", 14))
        self.username_label.pack(side='left', padx=5)
        
        # Email
        email_frame = ctk.CTkFrame(profile_frame, fg_color="transparent")
        email_frame.pack(pady=5, fill='x')
        
        ctk.CTkLabel(email_frame, text="Email:", font=("Helvetica", 14)).pack(side='left', padx=5)
        self.email_label = ctk.CTkLabel(email_frame, text="user@example.com", font=("Helvetica", 14))
        self.email_label.pack(side='left', padx=5)
        
        # Account stats
        stats_frame = ctk.CTkFrame(container, corner_radius=15)
        stats_frame.pack(pady=10, fill='x')
        
        ctk.CTkLabel(stats_frame, text="Statistiques du compte", font=("Helvetica", 16, "bold")).pack(pady=10)
        
        # Create grid for stats
        stats_grid = ctk.CTkFrame(stats_frame, fg_color="transparent")
        stats_grid.pack(pady=10, fill='x')
        
        # Total downloads
        total_frame = ctk.CTkFrame(stats_grid, corner_radius=10)
        total_frame.pack(side='left', padx=10, fill='both', expand=True)
        ctk.CTkLabel(total_frame, text="Total des téléchargements", font=("Helvetica", 14)).pack(pady=5)
        ctk.CTkLabel(total_frame, text="0", font=("Helvetica", 24, "bold")).pack(pady=5)
        
        # Videos downloaded
        videos_frame = ctk.CTkFrame(stats_grid, corner_radius=10)
        videos_frame.pack(side='left', padx=10, fill='both', expand=True)
        ctk.CTkLabel(videos_frame, text="Vidéos", font=("Helvetica", 14)).pack(pady=5)
        ctk.CTkLabel(videos_frame, text="0", font=("Helvetica", 24, "bold")).pack(pady=5)
        
        # Audio downloaded
        audio_frame = ctk.CTkFrame(stats_grid, corner_radius=10)
        audio_frame.pack(side='left', padx=10, fill='both', expand=True)
        ctk.CTkLabel(audio_frame, text="Audio", font=("Helvetica", 14)).pack(pady=5)
        ctk.CTkLabel(audio_frame, text="0", font=("Helvetica", 24, "bold")).pack(pady=5)
        
        # Account actions
        actions_frame = ctk.CTkFrame(container, corner_radius=15)
        actions_frame.pack(pady=10, fill='x')
        
        ctk.CTkLabel(actions_frame, text="Actions", font=("Helvetica", 16, "bold")).pack(pady=10)
        
        # Buttons
        change_password = ctk.CTkButton(actions_frame,
                                      text="Changer le mot de passe",
                                      width=200,
                                      height=40,
                                      corner_radius=10)
        change_password.pack(pady=5)
        
        delete_account = ctk.CTkButton(actions_frame,
                                     text="Supprimer le compte",
                                     fg_color="red",
                                     hover_color="darkred",
                                     width=200,
                                     height=40,
                                     corner_radius=10)
        delete_account.pack(pady=5)
    
    def check_url(self):
        url = self.url_entry.get()
        if not url:
            messagebox.showerror("Erreur", "Veuillez entrer une URL YouTube valide")
            return
        
        self.controller.check_url(url)
    
    def on_content_type_change(self, choice):
        self.controller.on_content_type_change(choice)
    
    def browse_path(self):
        path = filedialog.askdirectory()
        if path:
            self.path_entry.delete(0, 'end')
            self.path_entry.insert(0, path)
    
    def update_progress(self, d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)
            speed = d.get('speed', 0)
            if total > 0:
                progress = downloaded / total
                self.progress_bar.set(progress)
                speed_mb = speed / 1024 / 1024 if speed else 0
                total_mb = total / 1024 / 1024
                downloaded_mb = downloaded / 1024 / 1024
                self.progress_label.configure(
                    text=f"Downloaded: {downloaded_mb:.1f}MB/{total_mb:.1f}MB ({progress*100:.1f}%) Speed: {speed_mb:.1f}MB/s")
        elif d['status'] == 'finished':
            self.progress_frame.pack_forget()
    
    def display_video_info(self, video_info):
        # Clear previous content
        for widget in self.info_frame.winfo_children():
            widget.destroy()
        
        # Create a card-like frame for video info
        info_card = ctk.CTkFrame(self.info_frame, corner_radius=15)
        info_card.pack(pady=10, padx=10, fill='both', expand=True)
        
        # Video thumbnail
        thumbnail_frame = ctk.CTkFrame(info_card, fg_color="transparent")
        thumbnail_frame.pack(pady=10, padx=10, fill='x')
        
        try:
            # Try to load and display thumbnail
            thumbnail_url = video_info.get('thumbnail', '')
            if thumbnail_url:
                response = requests.get(thumbnail_url)
                image = Image.open(BytesIO(response.content))
                image = image.resize((320, 180), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                
                thumbnail_label = ctk.CTkLabel(thumbnail_frame, image=photo, text="")
                thumbnail_label.image = photo
                thumbnail_label.pack()
        except Exception as e:
            print(f"Error loading thumbnail: {e}")
        
        # Video details
        details_frame = ctk.CTkFrame(info_card, fg_color="transparent")
        details_frame.pack(pady=10, padx=10, fill='x')
        
        # Title with enhanced styling
        title_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
        title_frame.pack(fill='x', pady=5)
        ctk.CTkLabel(title_frame, 
                    text=video_info.get('title', 'Unknown Title'),
                    font=("Helvetica", 18, "bold"),
                    wraplength=600).pack(anchor='w')
        
        # Channel info
        channel_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
        channel_frame.pack(fill='x', pady=5)
        ctk.CTkLabel(channel_frame,
                    text=f"👤 {video_info.get('uploader', 'Unknown Channel')}",
                    font=("Helvetica", 14)).pack(anchor='w')
        
        # Duration and views
        stats_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
        stats_frame.pack(fill='x', pady=5)
        
        duration = video_info.get('duration_string', 'Unknown')
        views = video_info.get('view_count', 'Unknown')
        
        ctk.CTkLabel(stats_frame,
                    text=f"⏱️ {duration} | 👁️ {views} views",
                    font=("Helvetica", 14)).pack(anchor='w')
        
        # Download button with enhanced styling
        download_frame = ctk.CTkFrame(info_card, fg_color="transparent")
        download_frame.pack(pady=20, padx=10, fill='x')
        
        download_button = ctk.CTkButton(download_frame,
                                      text="⬇️ Télécharger",
                                      command=lambda: self.controller.download(video_info),
                                      height=50,
                                      width=200,
                                      corner_radius=10,
                                      font=("Helvetica", 16, "bold"))
        download_button.pack(pady=10)
    
    def hide(self):
        self.downloader_frame.pack_forget() 