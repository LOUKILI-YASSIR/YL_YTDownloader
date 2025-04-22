import customtkinter as ctk
from pymongo import MongoClient
import os
import bcrypt
import yt_dlp
from tkinter import messagebox, filedialog
from datetime import datetime, timedelta
from PIL import Image, ImageTk
from io import BytesIO
import requests
from threading import Thread
import webbrowser
import subprocess
import shutil
import time
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus.flowables import PageBreak
import pandas as pd
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Téléchargeur YouTube")
        # Définir la fenêtre en plein écran
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.geometry(f"{screen_width}x{screen_height}")
        
        # Définir le mode d'apparence et le thème
        self.appearance_mode = "dark"
        ctk.set_appearance_mode(self.appearance_mode)
        ctk.set_default_color_theme("blue")
        
        # Connexion MongoDB
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['youtube_downloader']
        self.users = self.db['users']
        
        # Initialize download paths
        self.video_path = os.path.join(os.getcwd(), 'video')
        self.audio_path = os.path.join(os.getcwd(), 'audio')
        os.makedirs(self.video_path, exist_ok=True)
        os.makedirs(self.audio_path, exist_ok=True)
        
        self.current_user = None
        self.setup_login_ui()
    
    def setup_login_ui(self):
        self.login_frame = ctk.CTkFrame(self)
        self.login_frame.pack(pady=20, padx=20, fill='both', expand=True)
        
        # Bouton de thème
        self.theme_button = ctk.CTkButton(self.login_frame, text="🌙 Mode Sombre" if self.appearance_mode == "light" else "☀️ Mode Clair",
                                         command=self.toggle_theme, width=120)
        self.theme_button.pack(pady=5, padx=10, anchor="ne")

        ctk.CTkLabel(self.login_frame, text="Connexion", font=("Helvetica", 18, "bold")).pack(pady=12, padx=10)
        
        # Cadre pour les entrées
        entry_frame = ctk.CTkFrame(self.login_frame)
        entry_frame.pack(pady=12, padx=10, fill='x')
        
        # Nom d'utilisateur avec validation
        username_frame = ctk.CTkFrame(entry_frame)
        username_frame.pack(pady=5, fill='x')
        ctk.CTkLabel(username_frame, text="Nom d'utilisateur:", width=120).pack(side='left', padx=5)
        self.username_entry = ctk.CTkEntry(username_frame, placeholder_text="Nom d'utilisateur", width=250)
        self.username_entry.pack(side='left', padx=5, fill='x', expand=True)
        
        # Mot de passe avec validation
        password_frame = ctk.CTkFrame(entry_frame)
        password_frame.pack(pady=5, fill='x')
        ctk.CTkLabel(password_frame, text="Mot de passe:", width=120).pack(side='left', padx=5)
        self.password_entry = ctk.CTkEntry(password_frame, placeholder_text="Mot de passe", show="*", width=250)
        self.password_entry.pack(side='left', padx=5, fill='x', expand=True)
        
        # Option Se souvenir de moi
        remember_frame = ctk.CTkFrame(entry_frame)
        remember_frame.pack(pady=5, fill='x')
        self.remember_var = ctk.BooleanVar(value=False)
        self.remember_checkbox = ctk.CTkCheckBox(remember_frame, text="Se souvenir de moi", variable=self.remember_var)
        self.remember_checkbox.pack(side='left', padx=5)
        
        # Boutons
        button_frame = ctk.CTkFrame(self.login_frame)
        button_frame.pack(pady=12, padx=10)
        
        ctk.CTkButton(button_frame, text="Se connecter", command=self.login, width=120).pack(side='left', padx=5)
        ctk.CTkButton(button_frame, text="S'inscrire", command=self.show_register, width=120).pack(side='left', padx=5)
        
        # Lien mot de passe oublié
        forgot_frame = ctk.CTkFrame(self.login_frame)
        forgot_frame.pack(pady=5)
        forgot_button = ctk.CTkButton(forgot_frame, text="Mot de passe oublié?", command=self.show_forgot_password, 
                                    fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"))
        forgot_button.pack()
    
    def setup_register_ui(self):
        self.register_frame = ctk.CTkFrame(self)
        self.register_frame.pack(pady=20, padx=20, fill='both', expand=True)
        
        # Bouton de thème
        self.theme_button = ctk.CTkButton(self.register_frame, text="🌙 Mode Sombre" if self.appearance_mode == "light" else "☀️ Mode Clair",
                                         command=self.toggle_theme, width=120)
        self.theme_button.pack(pady=5, padx=10, anchor="ne")

        ctk.CTkLabel(self.register_frame, text="Inscription", font=("Helvetica", 18, "bold")).pack(pady=12, padx=10)
        
        # Cadre pour les entrées
        entry_frame = ctk.CTkFrame(self.register_frame)
        entry_frame.pack(pady=12, padx=10, fill='x')
        
        # Nom d'utilisateur avec validation
        username_frame = ctk.CTkFrame(entry_frame)
        username_frame.pack(pady=5, fill='x')
        ctk.CTkLabel(username_frame, text="Nom d'utilisateur:", width=150).pack(side='left', padx=5)
        self.reg_username = ctk.CTkEntry(username_frame, placeholder_text="Nom d'utilisateur", width=250)
        self.reg_username.pack(side='left', padx=5, fill='x', expand=True)
        
        # Email
        email_frame = ctk.CTkFrame(entry_frame)
        email_frame.pack(pady=5, fill='x')
        ctk.CTkLabel(email_frame, text="Email:", width=150).pack(side='left', padx=5)
        self.reg_email = ctk.CTkEntry(email_frame, placeholder_text="Email", width=250)
        self.reg_email.pack(side='left', padx=5, fill='x', expand=True)
        
        # Mot de passe avec validation
        password_frame = ctk.CTkFrame(entry_frame)
        password_frame.pack(pady=5, fill='x')
        ctk.CTkLabel(password_frame, text="Mot de passe:", width=150).pack(side='left', padx=5)
        self.reg_password = ctk.CTkEntry(password_frame, placeholder_text="Mot de passe", show="*", width=250)
        self.reg_password.pack(side='left', padx=5, fill='x', expand=True)
        
        # Confirmation du mot de passe
        confirm_frame = ctk.CTkFrame(entry_frame)
        confirm_frame.pack(pady=5, fill='x')
        ctk.CTkLabel(confirm_frame, text="Confirmer le mot de passe:", width=150).pack(side='left', padx=5)
        self.reg_confirm = ctk.CTkEntry(confirm_frame, placeholder_text="Confirmer le mot de passe", show="*", width=250)
        self.reg_confirm.pack(side='left', padx=5, fill='x', expand=True)
        
        # Indicateur de force du mot de passe
        self.password_strength_frame = ctk.CTkFrame(entry_frame)
        self.password_strength_frame.pack(pady=5, fill='x')
        ctk.CTkLabel(self.password_strength_frame, text="Force du mot de passe:", width=150).pack(side='left', padx=5)
        self.password_strength_bar = ctk.CTkProgressBar(self.password_strength_frame, width=250)
        self.password_strength_bar.pack(side='left', padx=5)
        self.password_strength_bar.set(0)
        self.password_strength_label = ctk.CTkLabel(self.password_strength_frame, text="Faible")
        self.password_strength_label.pack(side='left', padx=5)
        
        # Lier l'événement de changement de mot de passe
        self.reg_password.bind("<KeyRelease>", self.check_password_strength)
        
        # Boutons
        button_frame = ctk.CTkFrame(self.register_frame)
        button_frame.pack(pady=12, padx=10)
        
        ctk.CTkButton(button_frame, text="S'inscrire", command=self.register, width=120).pack(side='left', padx=5)
        ctk.CTkButton(button_frame, text="Retour à la connexion", command=self.show_login, width=150).pack(side='left', padx=5)
    
    def setup_downloader_ui(self):
        self.downloader_frame = ctk.CTkFrame(self)
        self.downloader_frame.pack(pady=20, padx=20, fill='both', expand=True)
        
        # Bouton de thème
        self.theme_button = ctk.CTkButton(self.downloader_frame, text="🌙 Mode Sombre" if self.appearance_mode == "light" else "☀️ Mode Clair",
                                         command=self.toggle_theme, width=120)
        self.theme_button.pack(pady=5, padx=10, anchor="ne")
        
        # Message de bienvenue et onglets
        ctk.CTkLabel(self.downloader_frame, text=f"Bienvenue {self.current_user}", font=("Helvetica", 20, "bold")).pack(pady=(20,10), padx=10)
        
        # Créer la vue par onglets
        self.tabview = ctk.CTkTabview(self.downloader_frame)
        self.tabview.pack(pady=10, padx=10, fill='both', expand=True)
        
        # Ajouter les onglets
        self.tabview.add("Téléchargement")
        self.tabview.add("Tableau de bord")
        
        # Onglet Téléchargement
        download_frame = self.tabview.tab("Téléchargement")
        
        self.url_entry = ctk.CTkEntry(download_frame, placeholder_text="URL YouTube", width=400)
        self.url_entry.pack(pady=(20,10), padx=10)
        
        # Sélection du type de contenu
        content_type_frame = ctk.CTkFrame(download_frame)
        content_type_frame.pack(pady=5, padx=10, fill='x')
        ctk.CTkLabel(content_type_frame, text="Type de contenu:").pack(side='left', padx=5)
        self.content_type = ctk.CTkOptionMenu(content_type_frame, values=["Vidéo", "Audio", "Transcription"], command=self.on_content_type_change)
        self.content_type.pack(side='left', padx=5)
        
        # Transcription options frame (initially hidden)
        self.transcription_frame = ctk.CTkFrame(download_frame)
        self.transcription_language = ctk.StringVar(value="en")
        self.transcription_format = ctk.StringVar(value="pdf")
        
        # Options de transcription
        options_frame = ctk.CTkFrame(download_frame)
        options_frame.pack(pady=5, padx=10, fill='x')
        
        # Sélection de la langue
        ctk.CTkLabel(options_frame, text="Langue:").pack(side='left', padx=5)
        self.language_values = {"Anglais": "en", "Français": "fr", "Espagnol": "es", "Allemand": "de", "Italien": "it"}
        self.language_menu = ctk.CTkOptionMenu(options_frame, variable=self.transcription_language,
                                          values=list(self.language_values.keys()),
                                          command=self.on_language_change)
        self.language_menu.pack(side='left', padx=5)
        
        # Sélection du format
        ctk.CTkLabel(options_frame, text="Format:").pack(side='left', padx=5)
        self.format_values = {"PDF": "pdf", "Word": "docx"}
        self.format_menu_trans = ctk.CTkOptionMenu(options_frame, variable=self.transcription_format,
                                                values=list(self.format_values.keys()),
                                                command=self.on_format_change)
        self.format_menu_trans.pack(side='left', padx=5)
        
        # Sélection du format vidéo/audio
        self.format_frame = ctk.CTkFrame(download_frame)
        self.format_frame.pack(pady=5, padx=10, fill='x')
        ctk.CTkLabel(self.format_frame, text="Format:").pack(side='left', padx=5)
        self.format_var = ctk.StringVar(value="")
        self.format_menu = ctk.CTkOptionMenu(self.format_frame, variable=self.format_var)
        self.format_menu.pack(side='left', padx=5)
        
        # Sélection de la qualité
        self.quality_frame = ctk.CTkFrame(download_frame)
        self.quality_frame.pack(pady=5, padx=10, fill='x')
        ctk.CTkLabel(self.quality_frame, text="Qualité:").pack(side='left', padx=5)
        self.quality_var = ctk.StringVar(value="")
        self.quality_menu = ctk.CTkOptionMenu(self.quality_frame, variable=self.quality_var)
        self.quality_menu.pack(side='left', padx=5)
        
        # Sélection du chemin avec bouton parcourir
        path_frame = ctk.CTkFrame(download_frame)
        path_frame.pack(pady=5, padx=10, fill='x')
        ctk.CTkLabel(path_frame, text="Enregistrer sous:").pack(side='left', padx=5)
        self.path_entry = ctk.CTkEntry(path_frame, width=300)
        self.path_entry.pack(side='left', padx=5)
        self.path_entry.insert(0, self.video_path)
        ctk.CTkButton(path_frame, text="Parcourir", command=self.browse_path, width=70).pack(side='left', padx=5)
        
        # Cadre pour la miniature et les informations
        self.info_frame = ctk.CTkFrame(download_frame)
        self.info_frame.pack(pady=10, padx=10, fill='x')
        
        # Cadre de progression
        self.progress_frame = ctk.CTkFrame(download_frame)
        self.progress_frame.pack(pady=10, padx=10, fill='x')
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.progress_bar.set(0)
        self.progress_label = ctk.CTkLabel(self.progress_frame, text="")
        self.progress_frame.pack_forget()
        
        button_frame = ctk.CTkFrame(download_frame)
        button_frame.pack(pady=10, padx=10)
        
        ctk.CTkButton(button_frame, text="Vérifier l'URL", command=self.check_url, width=120).pack(side='left', padx=5)
        ctk.CTkButton(button_frame, text="Télécharger", command=self.download, width=120).pack(side='left', padx=5)
        
        # Onglet Tableau de bord
        dashboard_frame = self.tabview.tab("Tableau de bord")
        self.setup_dashboard(dashboard_frame)
        
        # Bouton de déconnexion en bas
        ctk.CTkButton(self.downloader_frame, text="Déconnexion", command=self.logout, width=120).pack(pady=10, padx=10)
    
    def show_register(self):
        self.login_frame.pack_forget()
        self.setup_register_ui()
    
    def show_login(self):
        if hasattr(self, 'register_frame'):
            self.register_frame.pack_forget()
        self.setup_login_ui()
    
    def register(self):
        username = self.reg_username.get()
        email = self.reg_email.get()
        password = self.reg_password.get()
        confirm = self.reg_confirm.get()
        
        # Validation des entrées
        if not username or not email or not password or not confirm:
            messagebox.showerror("Erreur", "Tous les champs sont obligatoires")
            return
            
        if password != confirm:
            messagebox.showerror("Erreur", "Les mots de passe ne correspondent pas")
            return
        
        # Validation de l'email avec une expression régulière simple
        import re
        email_pattern = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
        if not email_pattern.match(email):
            messagebox.showerror("Erreur", "Format d'email invalide")
            return
        
        # Vérification de l'unicité du nom d'utilisateur et de l'email
        if self.users.find_one({"username": username}):
            messagebox.showerror("Erreur", "Ce nom d'utilisateur existe déjà")
            return
            
        if self.users.find_one({"email": email}):
            messagebox.showerror("Erreur", "Cet email est déjà utilisé")
            return
        
        # Vérification de la force du mot de passe
        if len(password) < 8:
            messagebox.showerror("Erreur", "Le mot de passe doit contenir au moins 8 caractères")
            return
        
        # Hachage et enregistrement
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        self.users.insert_one({
            "username": username, 
            "email": email,
            "password": hashed,
            "created_at": datetime.now(),
            "last_login": None
        })
        messagebox.showinfo("Succès", "Inscription réussie")
        self.show_login()
    
    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        # Validation des entrées
        if not username or not password:
            messagebox.showerror("Erreur", "Veuillez remplir tous les champs")
            return
        
        # Recherche de l'utilisateur par nom d'utilisateur ou email
        user = self.users.find_one({"$or": [{"username": username}, {"email": username}]})
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            self.current_user = user["username"]
            
            # Mise à jour de la dernière connexion
            self.users.update_one({"_id": user["_id"]}, {"$set": {"last_login": datetime.now()}})
            
            # Enregistrement de la session si demandé
            if hasattr(self, 'remember_var') and self.remember_var.get():
                self.save_session(user["username"])
            
            self.login_frame.pack_forget()
            self.setup_downloader_ui()
        else:
            messagebox.showerror("Erreur", "Identifiants invalides")
            
    def save_session(self, username):
        # Enregistrement de la session dans un fichier local
        session_file = os.path.join(os.getcwd(), ".session")
        with open(session_file, "w") as f:
            f.write(username)
            
    def load_session(self):
        # Chargement de la session depuis un fichier local
        session_file = os.path.join(os.getcwd(), ".session")
        if os.path.exists(session_file):
            with open(session_file, "r") as f:
                username = f.read().strip()
                if username:
                    user = self.users.find_one({"username": username})
                    if user:
                        self.current_user = username
                        self.login_frame.pack_forget()
                        self.setup_downloader_ui()
                        return True
        return False
        
    def show_forgot_password(self):
        # Masquer le cadre de connexion
        self.login_frame.pack_forget()
        
        # Créer le cadre de récupération de mot de passe
        self.forgot_frame = ctk.CTkFrame(self)
        self.forgot_frame.pack(pady=20, padx=20, fill='both', expand=True)
        
        # Bouton de thème
        self.theme_button = ctk.CTkButton(self.forgot_frame, text="🌙 Mode Sombre" if self.appearance_mode == "light" else "☀️ Mode Clair",
                                         command=self.toggle_theme, width=120)
        self.theme_button.pack(pady=5, padx=10, anchor="ne")

        ctk.CTkLabel(self.forgot_frame, text="Récupération de mot de passe", font=("Helvetica", 18, "bold")).pack(pady=12, padx=10)
        
        # Instructions
        ctk.CTkLabel(self.forgot_frame, text="Entrez votre email pour recevoir un code de validation").pack(pady=12, padx=10)
        
        # Champ email
        self.recovery_email = ctk.CTkEntry(self.forgot_frame, placeholder_text="Email", width=300)
        self.recovery_email.pack(pady=12, padx=10)
        
        # Boutons
        button_frame = ctk.CTkFrame(self.forgot_frame)
        button_frame.pack(pady=12, padx=10)
        
        ctk.CTkButton(button_frame, text="Envoyer", command=self.send_recovery_email, width=120).pack(side='left', padx=5)
        ctk.CTkButton(button_frame, text="Retour", command=self.back_to_login, width=120).pack(side='left', padx=5)
    
    def send_recovery_email(self):
        email = self.recovery_email.get()
        
        if not email:
            messagebox.showerror("Erreur", "Veuillez entrer votre email")
            return
            
        # Vérifier si l'email existe dans la base de données
        user = self.users.find_one({"email": email})
        if not user:
            messagebox.showerror("Erreur", "Aucun compte associé à cet email")
            return
        
        # Générer un code de validation à 6 chiffres
        import random
        validation_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        
        # Stocker le code dans la base de données avec une expiration
        expiration = datetime.now() + timedelta(minutes=15)  # Code valide 15 minutes
        self.users.update_one({"_id": user["_id"]}, {"$set": {"reset_code": validation_code, "reset_expiry": expiration}})
        
        # Dans une application réelle, envoyez un email avec le code
        # Pour cette démo, nous affichons le code (simulant l'envoi d'email)
        messagebox.showinfo("Succès", f"Un code de validation a été envoyé à {email}\n\nCode: {validation_code}")
        
        # Afficher l'écran de validation du code
        self.show_code_validation(user["_id"])
    
    def show_code_validation(self, user_id):
        # Masquer le cadre précédent
        self.forgot_frame.pack_forget()
        
        # Créer le cadre de validation du code
        self.validation_frame = ctk.CTkFrame(self)
        self.validation_frame.pack(pady=20, padx=20, fill='both', expand=True)
        
        # Bouton de thème
        self.theme_button = ctk.CTkButton(self.validation_frame, text="🌙 Mode Sombre" if self.appearance_mode == "light" else "☀️ Mode Clair",
                                         command=self.toggle_theme, width=120)
        self.theme_button.pack(pady=5, padx=10, anchor="ne")

        ctk.CTkLabel(self.validation_frame, text="Validation du code", font=("Helvetica", 18, "bold")).pack(pady=12, padx=10)
        
        # Instructions
        ctk.CTkLabel(self.validation_frame, text="Entrez le code de validation reçu par email").pack(pady=12, padx=10)
        
        # Champ code
        self.validation_code = ctk.CTkEntry(self.validation_frame, placeholder_text="Code à 6 chiffres", width=300)
        self.validation_code.pack(pady=12, padx=10)
        
        # Stocker l'ID utilisateur pour la validation
        self.reset_user_id = user_id
        
        # Boutons
        button_frame = ctk.CTkFrame(self.validation_frame)
        button_frame.pack(pady=12, padx=10)
        
        ctk.CTkButton(button_frame, text="Valider", command=self.validate_code, width=120).pack(side='left', padx=5)
        ctk.CTkButton(button_frame, text="Retour", command=self.back_to_forgot, width=120).pack(side='left', padx=5)
    
    def validate_code(self):
        code = self.validation_code.get()
        
        if not code or len(code) != 6:
            messagebox.showerror("Erreur", "Veuillez entrer un code à 6 chiffres")
            return
        
        # Vérifier le code dans la base de données
        user = self.users.find_one({"_id": self.reset_user_id})
        if not user or "reset_code" not in user or user["reset_code"] != code:
            messagebox.showerror("Erreur", "Code de validation incorrect")
            return
        
        # Vérifier si le code n'a pas expiré
        if datetime.now() > user["reset_expiry"]:
            messagebox.showerror("Erreur", "Le code de validation a expiré. Veuillez recommencer.")
            self.back_to_forgot()
            return
        
        # Afficher l'écran de changement de mot de passe
        self.show_password_reset()
    
    def show_password_reset(self):
        # Masquer le cadre précédent
        self.validation_frame.pack_forget()
        
        # Créer le cadre de réinitialisation du mot de passe
        self.reset_frame = ctk.CTkFrame(self)
        self.reset_frame.pack(pady=20, padx=20, fill='both', expand=True)
        
        # Bouton de thème
        self.theme_button = ctk.CTkButton(self.reset_frame, text="🌙 Mode Sombre" if self.appearance_mode == "light" else "☀️ Mode Clair",
                                         command=self.toggle_theme, width=120)
        self.theme_button.pack(pady=5, padx=10, anchor="ne")

        ctk.CTkLabel(self.reset_frame, text="Réinitialisation du mot de passe", font=("Helvetica", 18, "bold")).pack(pady=12, padx=10)
        
        # Cadre pour les entrées
        entry_frame = ctk.CTkFrame(self.reset_frame)
        entry_frame.pack(pady=12, padx=10, fill='x')
        
        # Nouveau mot de passe
        password_frame = ctk.CTkFrame(entry_frame)
        password_frame.pack(pady=5, fill='x')
        ctk.CTkLabel(password_frame, text="Nouveau mot de passe:", width=150).pack(side='left', padx=5)
        self.new_password = ctk.CTkEntry(password_frame, placeholder_text="Nouveau mot de passe", show="*", width=250)
        self.new_password.pack(side='left', padx=5, fill='x', expand=True)
        
        # Confirmation du nouveau mot de passe
        confirm_frame = ctk.CTkFrame(entry_frame)
        confirm_frame.pack(pady=5, fill='x')
        ctk.CTkLabel(confirm_frame, text="Confirmer le mot de passe:", width=150).pack(side='left', padx=5)
        self.confirm_password = ctk.CTkEntry(confirm_frame, placeholder_text="Confirmer le mot de passe", show="*", width=250)
        self.confirm_password.pack(side='left', padx=5, fill='x', expand=True)
        
        # Boutons
        button_frame = ctk.CTkFrame(self.reset_frame)
        button_frame.pack(pady=12, padx=10)
        
        ctk.CTkButton(button_frame, text="Réinitialiser", command=self.reset_password, width=120).pack(side='left', padx=5)
        ctk.CTkButton(button_frame, text="Annuler", command=self.back_to_login, width=120).pack(side='left', padx=5)
    
    def reset_password(self):
        new_password = self.new_password.get()
        confirm = self.confirm_password.get()
        
        # Validation des entrées
        if not new_password or not confirm:
            messagebox.showerror("Erreur", "Veuillez remplir tous les champs")
            return
            
        if new_password != confirm:
            messagebox.showerror("Erreur", "Les mots de passe ne correspondent pas")
            return
        
        # Vérification de la force du mot de passe
        if len(new_password) < 8:
            messagebox.showerror("Erreur", "Le mot de passe doit contenir au moins 8 caractères")
            return
        
        # Hachage et mise à jour du mot de passe
        hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        self.users.update_one({"_id": self.reset_user_id}, {
            "$set": {"password": hashed},
            "$unset": {"reset_code": "", "reset_expiry": ""}
        })
        
        messagebox.showinfo("Succès", "Votre mot de passe a été réinitialisé avec succès")
        self.back_to_login()
    
    def back_to_forgot(self):
        if hasattr(self, 'validation_frame'):
            self.validation_frame.pack_forget()
        self.show_forgot_password()
        
    def back_to_login(self):
        if hasattr(self, 'forgot_frame'):
            self.forgot_frame.pack_forget()
        self.setup_login_ui()
        
    def check_password_strength(self, event):
        password = self.reg_password.get()
        strength = 0
        feedback = "Faible"
        
        if len(password) >= 8:
            strength += 0.25
        if any(c.isdigit() for c in password):
            strength += 0.25
        if any(c.isupper() for c in password):
            strength += 0.25
        if any(not c.isalnum() for c in password):
            strength += 0.25
            
        if strength <= 0.25:
            feedback = "Très faible"
        elif strength <= 0.5:
            feedback = "Faible"
        elif strength <= 0.75:
            feedback = "Moyen"
        else:
            feedback = "Fort"
            
        self.password_strength_bar.set(strength)
        self.password_strength_label.configure(text=feedback)
    
    def toggle_theme(self):
        self.appearance_mode = "light" if self.appearance_mode == "dark" else "dark"
        ctk.set_appearance_mode(self.appearance_mode)
        if hasattr(self, 'theme_button'):
            self.theme_button.configure(text="🌙 Mode Sombre" if self.appearance_mode == "light" else "☀️ Mode Clair")
            
    def on_language_change(self, language_name):
        # Mettre à jour la valeur de la variable avec le code de langue correspondant
        self.transcription_language.set(self.language_values[language_name])
    
    def on_format_change(self, format_name):
        # Mettre à jour la valeur de la variable avec le code de format correspondant
        self.transcription_format.set(self.format_values[format_name])

    def logout(self):
        self.current_user = None
        self.downloader_frame.pack_forget()
        self.setup_login_ui()
    
    def setup_dashboard(self, frame):
        # Créer les graphiques de statistiques
        stats_frame = ctk.CTkFrame(frame)
        stats_frame.pack(pady=10, padx=10, fill='x')
        
        # Graphique des téléchargements par jour
        downloads_per_day = self.get_downloads_per_day()
        self.create_bar_chart(stats_frame, "Téléchargements par jour", downloads_per_day)
        
        # Graphique des types de contenu
        content_types = self.get_content_type_stats()
        self.create_pie_chart(stats_frame, "Types de contenu", content_types)
        
        # Historique des téléchargements
        ctk.CTkLabel(frame, text="Historique des téléchargements", font=("Helvetica", 16, "bold")).pack(pady=(20,10), padx=10)
        
        # Créer un cadre défilable pour l'historique
        self.history_frame = ctk.CTkScrollableFrame(frame, height=400)
        self.history_frame.pack(pady=10, padx=10, fill='both', expand=True)
        
        # Charger et afficher l'historique des téléchargements
        self.load_download_history()
    
    def get_downloads_per_day(self):
        # Obtenir les statistiques de téléchargement par jour pour l'utilisateur actuel
        pipeline = [
            {"$match": {"username": self.current_user}},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}},
            {"$limit": 7}
        ]
        result = list(self.db['downloads'].aggregate(pipeline))
        return {item['_id']: item['count'] for item in result}
    
    def get_content_type_stats(self):
        # Obtenir les statistiques des types de contenu pour l'utilisateur actuel
        pipeline = [
            {"$match": {"username": self.current_user}},
            {"$group": {
                "_id": "$type",
                "count": {"$sum": 1}
            }}
        ]
        result = list(self.db['downloads'].aggregate(pipeline))
        return {item['_id']: item['count'] for item in result}
    
    def create_bar_chart(self, parent, title, data):
        # Créer un graphique à barres
        chart_frame = ctk.CTkFrame(parent)
        chart_frame.pack(pady=10, padx=10, fill='x')
        
        ctk.CTkLabel(chart_frame, text=title, font=("Helvetica", 14, "bold")).pack(pady=5)
        
        max_value = max(data.values()) if data else 1
        for date, count in data.items():
            bar_frame = ctk.CTkFrame(chart_frame)
            bar_frame.pack(pady=2, fill='x')
            
            ctk.CTkLabel(bar_frame, text=date, width=100).pack(side='left', padx=5)
            bar = ctk.CTkProgressBar(bar_frame, width=200)
            bar.pack(side='left', padx=5)
            bar.set(count/max_value)
            ctk.CTkLabel(bar_frame, text=str(count)).pack(side='left', padx=5)
    
    def create_pie_chart(self, parent, title, data):
        # Créer un graphique circulaire simple
        chart_frame = ctk.CTkFrame(parent)
        chart_frame.pack(pady=10, padx=10, fill='x')
        
        ctk.CTkLabel(chart_frame, text=title, font=("Helvetica", 14, "bold")).pack(pady=5)
        
        total = sum(data.values())
        for type_name, count in data.items():
            percentage = (count/total) * 100 if total > 0 else 0
            item_frame = ctk.CTkFrame(chart_frame)
            item_frame.pack(pady=2, fill='x')
            
            ctk.CTkLabel(item_frame, text=type_name, width=100).pack(side='left', padx=5)
            bar = ctk.CTkProgressBar(item_frame, width=200)
            bar.pack(side='left', padx=5)
            bar.set(percentage/100)
            ctk.CTkLabel(item_frame, text=f"{percentage:.1f}% ({count})").pack(side='left', padx=5)
    
    def load_download_history(self):
        # Effacer les éléments existants de l'historique
        for widget in self.history_frame.winfo_children():
            widget.destroy()
        
        # Obtenir l'historique des téléchargements depuis MongoDB
        history = self.db['downloads'].find({"username": self.current_user}).sort("timestamp", -1)
        
        for item in history:
            item_frame = ctk.CTkFrame(self.history_frame)
            item_frame.pack(pady=10, padx=5, fill='x')
            
            # Créer le cadre gauche pour la miniature
            left_frame = ctk.CTkFrame(item_frame)
            left_frame.pack(side='left', padx=5, pady=5)
            
            # Charger et afficher la miniature
            try:
                response = requests.get(item.get('thumbnail_url', ''))
                img = Image.open(BytesIO(response.content))
                img = img.resize((120, 90), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                thumbnail_label = ctk.CTkLabel(left_frame, image=photo, text="")
                thumbnail_label.image = photo
                thumbnail_label.pack()
            except:
                # Si le chargement de la miniature échoue, afficher un espace réservé
                ctk.CTkLabel(left_frame, text="Pas de miniature", width=120, height=90).pack()
            
            # Créer le cadre droit pour les informations et les boutons
            right_frame = ctk.CTkFrame(item_frame)
            right_frame.pack(side='left', fill='both', expand=True, padx=5, pady=5)
            
            # Étiquettes d'information
            ctk.CTkLabel(right_frame, text=f"Titre: {item['title']}").pack(anchor='w')
            ctk.CTkLabel(right_frame, text=f"Type: {item['type']}").pack(anchor='w')
            ctk.CTkLabel(right_frame, text=f"Format: {item.get('format', 'N/A')}").pack(anchor='w')
            if item['type'] == 'Vidéo':
                ctk.CTkLabel(right_frame, text=f"Qualité: {item.get('quality', 'N/A')}").pack(anchor='w')
            elif item['type'] == 'Transcription':
                ctk.CTkLabel(right_frame, text=f"Langue: {item.get('language', 'N/A')}").pack(anchor='w')
            ctk.CTkLabel(right_frame, text=f"Taille: {item.get('filesize', 'N/A')} Mo").pack(anchor='w')
            ctk.CTkLabel(right_frame, text=f"Téléchargé le: {item['timestamp'].strftime('%d/%m/%Y %H:%M:%S')}").pack(anchor='w')
            
            # Créer le cadre des boutons
            button_frame = ctk.CTkFrame(right_frame)
            button_frame.pack(anchor='w', pady=(5,0))
            
            # Bouton pour ouvrir dans YouTube
            ctk.CTkButton(
                button_frame,
                text="Ouvrir dans YouTube",
                command=lambda url=item['url']: self.open_youtube(url),
                width=120
            ).pack(side='left', padx=5)
            
            # Bouton pour ouvrir le fichier local (uniquement si le fichier existe)
            file_path = os.path.join(
                self.video_path if item['type'] == 'Vidéo' else self.audio_path,
                f"{item['title']}.{item.get('format', 'mp4')}"
            )
            if os.path.exists(file_path):
                ctk.CTkButton(
                    button_frame,
                    text="Ouvrir le fichier",
                    command=lambda path=file_path: self.open_local_file(path),
                    width=120
                ).pack(side='left', padx=5)
                
                # Ajouter le bouton de transcription pour les fichiers vidéo
                if item['type'] == 'Vidéo':
                    ctk.CTkButton(
                        button_frame,
                        text="Générer la transcription",
                        command=lambda video=item: self.generate_transcription(video),
                        width=120
                    ).pack(side='left', padx=5)

    def generate_transcription(self, video):
        # Create a dialog for transcription options
        dialog = ctk.CTkToplevel(self)
        dialog.title("Transcription Options")
        dialog.geometry("300x200")
        
        # Language selection
        ctk.CTkLabel(dialog, text="Language:").pack(pady=5)
        language_var = ctk.StringVar(value="en")
        language_menu = ctk.CTkOptionMenu(dialog, variable=language_var,
                                        values=["en", "fr", "es", "de", "it"])
        language_menu.pack(pady=5)
        
        # Format selection
        ctk.CTkLabel(dialog, text="Format:").pack(pady=5)
        format_var = ctk.StringVar(value="pdf")
        format_menu = ctk.CTkOptionMenu(dialog, variable=format_var,
                                      values=["pdf", "docx"])
        format_menu.pack(pady=5)
        
        # Generate button
        ctk.CTkButton(
            dialog,
            text="Generate",
            command=lambda: self.start_transcription(
                video,
                language_var.get(),
                format_var.get(),
                dialog
            )
        ).pack(pady=20)

    def start_transcription(self, video, language, format_type, dialog):
        # TODO: Implement actual transcription generation
        messagebox.showinfo("Info", f"Starting transcription in {language} to {format_type} format")
        dialog.destroy()

    def open_youtube(self, url):
        import webbrowser
        webbrowser.open(url)
    
    def open_local_file(self, path):
        import subprocess
        subprocess.Popen(['explorer', path], shell=True)
    
    def on_content_type_change(self, choice):
        # Réinitialiser les options précédentes
        for widget in self.format_frame.master.winfo_children():
            if isinstance(widget, ctk.CTkFrame) and widget != self.format_frame and widget != self.quality_frame:
                widget.pack_forget()
        
        # Définir les valeurs par défaut pour les sélecteurs
        url_exists = bool(self.url_entry.get().strip())
        
        if choice == "Vidéo":
            self.path_entry.delete(0, 'end')
            self.path_entry.insert(0, self.video_path)
            
            # Afficher le cadre de format
            self.format_frame.pack(pady=5, padx=10, fill='x')
            
            # Configurer les valeurs du format vidéo
            video_formats = ["mp4", "webm", "mkv", "avi"]
            self.format_var.set(video_formats[0] if url_exists else "----")
            self.format_menu.configure(values=video_formats if url_exists else ["----"])
            
            # Afficher le cadre de qualité
            self.quality_frame.pack(pady=5, padx=10, fill='x')
            
            # Configurer les valeurs de qualité vidéo
            video_qualities = ["1080p", "720p", "480p", "360p", "240p", "144p"]
            self.quality_var.set(video_qualities[0] if url_exists else "----")
            self.quality_menu.configure(values=video_qualities if url_exists else ["----"])
            
        elif choice == "Audio":
            self.path_entry.delete(0, 'end')
            self.path_entry.insert(0, self.audio_path)
            
            # Afficher le cadre de format
            self.format_frame.pack(pady=5, padx=10, fill='x')
            
            # Configurer les valeurs du format audio
            audio_formats = ["mp3", "wav", "aac", "m4a", "opus"]
            self.format_var.set(audio_formats[0] if url_exists else "----")
            self.format_menu.configure(values=audio_formats if url_exists else ["----"])
            
            # Masquer le cadre de qualité
            self.quality_frame.pack_forget()
            
        else:  # Transcription
            # Créer un nouveau cadre pour les options de transcription
            trans_options_frame = ctk.CTkFrame(self.format_frame.master)
            trans_options_frame.pack(pady=5, padx=10, fill='x')
            
            # Sélection de la langue
            lang_frame = ctk.CTkFrame(trans_options_frame)
            lang_frame.pack(pady=5, fill='x')
            ctk.CTkLabel(lang_frame, text="Langue:", width=80).pack(side='left', padx=5)
            
            # Configurer les valeurs de langue
            language_display = list(self.language_values.keys())
            self.language_menu = ctk.CTkOptionMenu(lang_frame, 
                                              variable=self.transcription_language,
                                              values=language_display if url_exists else ["----"],
                                              command=self.on_language_change)
            if not url_exists:
                self.transcription_language.set("----")
            self.language_menu.pack(side='left', padx=5)
            
            # Sélection du format
            format_frame = ctk.CTkFrame(trans_options_frame)
            format_frame.pack(pady=5, fill='x')
            ctk.CTkLabel(format_frame, text="Format:", width=80).pack(side='left', padx=5)
            
            # Configurer les valeurs de format
            format_display = list(self.format_values.keys())
            self.format_menu_trans = ctk.CTkOptionMenu(format_frame, 
                                                    variable=self.transcription_format,
                                                    values=format_display if url_exists else ["----"],
                                                    command=self.on_format_change)
            if not url_exists:
                self.transcription_format.set("----")
            self.format_menu_trans.pack(side='left', padx=5)
            
            # Masquer les cadres de format et qualité vidéo/audio
            self.format_frame.pack_forget()
            self.quality_frame.pack_forget()
    
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
    
    def check_url(self):
        url = self.url_entry.get()
        if not url:
            messagebox.showerror("Erreur", "Veuillez entrer une URL YouTube valide")
            return

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True
        }
        
        # Show progress frame and reset
        self.progress_frame.pack(pady=5, padx=10, fill='x')
        self.progress_bar.pack(pady=5, fill='x')
        self.progress_label.configure(text="Loading video information...")
        self.progress_label.pack(pady=2)
        self.progress_bar.set(0)
        
        def fetch_info():
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    self.after(0, lambda: self.process_video_info(info))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Erreur", f"Impossible de récupérer les informations de la vidéo : {str(e)}\nVérifiez que l'URL est correcte et que votre connexion internet fonctionne."))
                self.after(0, lambda: self.progress_frame.pack_forget())
        
        Thread(target=fetch_info).start()
    
    def process_video_info(self, info):
        try:
            # Clear previous info
            for widget in self.info_frame.winfo_children():
                widget.destroy()
            
            # Display thumbnail
            if 'thumbnail' in info:
                try:
                    response = requests.get(info['thumbnail'])
                    img = Image.open(BytesIO(response.content))
                    img = img.resize((200, 150), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    thumbnail_label = ctk.CTkLabel(self.info_frame, image=photo, text="")
                    thumbnail_label.image = photo
                    thumbnail_label.pack(pady=5)
                except Exception as e:
                    print(f"Error loading thumbnail: {e}")
            
            # Display video information
            ctk.CTkLabel(self.info_frame, text=info.get('title', 'Unknown Title')).pack(pady=2)
            duration = info.get('duration')
            if duration:
                minutes = duration // 60
                seconds = duration % 60
                ctk.CTkLabel(self.info_frame, text=f"Duration: {minutes}:{seconds:02d}").pack(pady=2)
            
            self.progress_frame.pack_forget()
            
            if self.content_type.get() == "Video":
                # Define available video formats
                video_formats = ["mp4", "webm", "mkv", "avi"]
                # Get available video qualities
                qualities = set()
                format_info = {}
                
                for f in info['formats']:
                    if 'height' in f and f.get('vcodec', 'none') != 'none':
                        height = str(f['height'])
                        qualities.add(height)
                        if height not in format_info:
                            format_info[height] = []
                        format_info[height].append({
                            'format_id': f['format_id'],
                            'ext': f['ext'],
                            'vcodec': f.get('vcodec', 'unknown'),
                            'filesize': f.get('filesize', 0)
                        })
                
                if not qualities:
                    messagebox.showerror("Erreur", "Aucun format vidéo compatible n'a été trouvé pour cette URL. Essayez une autre vidéo.")
                    return
                
                # Sort qualities in descending order
                qualities = sorted(list(qualities), key=int, reverse=True)
                
                # Configure format and quality menus
                self.format_menu.configure(values=video_formats)
                self.format_var.set("mp4")
                
                self.quality_menu.configure(values=[f"{q}p" for q in qualities])
                self.quality_var.set(f"{qualities[0]}p")
                
                # Store format info for later use
                self._format_info = format_info
            else:
                # Define available audio formats
                audio_formats = ["mp3", "m4a", "wav", "aac"]
                # Get available audio qualities
                qualities = set()
                format_info = {}
                
                for f in info['formats']:
                    if f.get('acodec', 'none') != 'none' and f.get('vcodec', 'none') == 'none':
                        abr = str(int(float(f.get('abr', 0))))
                        if abr != '0':
                            qualities.add(abr)
                            if abr not in format_info:
                                format_info[abr] = []
                            format_info[abr].append({
                                'format_id': f['format_id'],
                                'ext': f['ext'],
                                'acodec': f.get('acodec', 'unknown'),
                                'filesize': f.get('filesize', 0)
                            })
                
                if not qualities:
                    messagebox.showerror("Erreur", "Aucun format audio compatible n'a été trouvé pour cette URL. Essayez une autre vidéo.")
                    return
                
                # Sort qualities in descending order
                qualities = sorted(list(qualities), key=int, reverse=True)
                
                # Configure format and quality menus
                self.format_menu.configure(values=audio_formats)
                self.format_var.set("mp3")
                
                self.quality_menu.configure(values=[f"{q}kbps" for q in qualities])
                self.quality_var.set(f"{qualities[0]}kbps")
                
                # Store format info for later use
                self._format_info = format_info
            
            messagebox.showinfo("Success", "Video information loaded successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error processing video info: {str(e)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error processing video info: {str(e)}")
    
    def format_size(self, size_bytes):
        """Convertit les octets en format lisible (KB, MB, GB)"""
        if size_bytes == 0 or not size_bytes:
            return "0B"
        
        size_names = ("B", "KB", "MB", "GB", "TB")
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024
            i += 1
        
        return f"{size_bytes:.2f}{size_names[i]}"
    
    def download(self):
        url = self.url_entry.get()
        if not url:
            messagebox.showerror("Erreur", "Veuillez entrer une URL YouTube valide")
            return
        
        if not self.quality_var.get() or not hasattr(self, '_format_info'):
            messagebox.showerror("Erreur", "Veuillez d'abord vérifier l'URL")
            return

        # Afficher le cadre de progression
        self.progress_frame.pack(pady=5, padx=10, fill='x')
        self.progress_bar.pack(pady=5, fill='x')
        self.progress_label.configure(text="Préparation du téléchargement...")
        self.progress_label.pack(pady=2)
        self.progress_bar.set(0)
        
        def download_thread():
            try:
                download_path = self.path_entry.get()
                content_type = self.content_type.get()
                target_format = self.format_var.get()
                quality = self.quality_var.get().replace('p', '').replace('kbps', '')
                
                # Find best matching format for selected quality
                format_info = self._format_info.get(quality, [])
                if not format_info:
                    self.after(0, lambda: messagebox.showerror("Error", "Selected quality is not available"))
                    return
                    
                # Sort formats by filesize to get best quality
                format_info.sort(key=lambda x: x.get('filesize', 0), reverse=True)
                best_format = format_info[0]
                
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'format': f'{best_format["format_id"]}+bestaudio' if content_type == "Video" else best_format["format_id"],
                    'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
                    'progress_hooks': [self.update_progress],
                    'postprocessors': []
                }
                
                # Add format conversion if needed
                if best_format['ext'] != target_format:
                    if content_type == "Video":
                        ydl_opts['postprocessors'].append({
                            'key': 'FFmpegVideoConvertor',
                            'preferedformat': target_format,
                        })
                    else:
                        ydl_opts['postprocessors'].append({
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': target_format,
                            'preferredquality': quality,
                        })

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url)
                    
                    # Calculate file size in MB
                    file_path = os.path.join(download_path, f"{info.get('title', 'video')}.{target_format}")
                    filesize = round(os.path.getsize(file_path) / (1024 * 1024), 2) if os.path.exists(file_path) else 'N/A'
                    
                    # Save download history
                    self.db['downloads'].insert_one({
                        "username": self.current_user,
                        "title": info.get('title', 'video'),
                        "type": content_type,
                        "quality": self.quality_var.get(),
                        "url": url,
                        "timestamp": datetime.now(),
                        "thumbnail_url": info.get('thumbnail', ''),
                        "format": target_format,
                        "filesize": filesize,
                        "language": self.transcription_language.get() if content_type == "Transcription" else None
                    })
                    
                    self.after(0, lambda: self.load_download_history())
                    self.after(0, lambda: messagebox.showinfo("Success", "Download completed successfully!"))
                    
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", f"Error during download: {str(e)}"))
            finally:
                self.after(0, lambda: self.progress_frame.pack_forget())
        
        Thread(target=download_thread).start()

if __name__ == "__main__":
    app = App()
    app.mainloop()
