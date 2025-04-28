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

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Téléchargeur YouTube")
        # Définir la fenêtre en plein écran
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.geometry(f"{screen_width}x{screen_height}-1-0")
        
        # Définir le mode d'apparence et le thème
        self.appearance_mode = "dark"
        ctk.set_appearance_mode(self.appearance_mode)
        ctk.set_default_color_theme("blue")
        
        # Connexion MongoDB
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['youtube_downloader']
        self.users = self.client['youtube_downloader']['users']
        
        # Initialize download paths
        self.video_path = os.path.join(os.getcwd(), 'video')
        self.audio_path = os.path.join(os.getcwd(), 'audio')
        os.makedirs(self.video_path, exist_ok=True)
        os.makedirs(self.audio_path, exist_ok=True)
        
        # Load eye icons
        self.visible_eye = ctk.CTkImage(Image.open("images/VisibleEyeIcon.jpg"), size=(20, 20))
        self.invisible_eye = ctk.CTkImage(Image.open("images/InvisibleEyeIcon.jpg"), size=(20, 20))
        
        self.current_user = None
        self.setup_login_ui()
    
    def setup_login_ui(self):
        self.login_frame = ctk.CTkFrame(self, corner_radius=15)
        self.login_frame.pack(pady=20, padx=20, fill='both', expand=True)
        
        # Header with logo and title
        header_frame = ctk.CTkFrame(self.login_frame, fg_color="transparent")
        header_frame.pack(pady=(20, 10), padx=10, fill='x')
        
        # Logo and title
        logo_label = ctk.CTkLabel(header_frame, text="🎬", font=("Helvetica", 40))
        logo_label.pack(side='left', padx=10)
        
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(side='left', padx=10)
        ctk.CTkLabel(title_frame, text="YouTube Downloader", font=("Helvetica", 24, "bold")).pack()
        ctk.CTkLabel(title_frame, text="Connectez-vous à votre compte", font=("Helvetica", 14)).pack()
        
        # Theme button
        self.theme_button = ctk.CTkButton(header_frame, 
                                         text="🌙 Mode Sombre" if self.appearance_mode == "light" else "☀️ Mode Clair",
                                         command=self.toggle_theme, 
                                         width=40,
                                         height=40,
                                         corner_radius=20)
        self.theme_button.pack(side='right', padx=10)
        
        # Main content frame
        content_frame = ctk.CTkFrame(self.login_frame, fg_color="transparent")
        content_frame.pack(pady=20, padx=20, fill='both', expand=True)
        
        # Input fields with icons
        input_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        input_frame.pack(pady=20, padx=20, fill='x')
        
        # Username field
        username_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        username_frame.pack(pady=10, fill='x')
        ctk.CTkLabel(username_frame, text="👤", font=("Helvetica", 16)).pack(side='left', padx=5)
        self.username_entry = ctk.CTkEntry(username_frame, 
                                         placeholder_text="Nom d'utilisateur ou email",
                                         width=300,
                                         height=40,
                                         corner_radius=10)
        self.username_entry.pack(side='left', padx=5, fill='x', expand=True)
        
        # Password field
        password_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        password_frame.pack(pady=10, fill='x')
        ctk.CTkLabel(password_frame, text="🔒", font=("Helvetica", 16)).pack(side='left', padx=5)
        self.password_entry = ctk.CTkEntry(password_frame, 
                                         placeholder_text="Mot de passe",
                                         show="*",
                                         width=300,
                                         height=40,
                                         corner_radius=10)
        self.password_entry.pack(side='left', padx=5, fill='x', expand=True)
        
        # Show/hide password button
        self.show_password_var = ctk.BooleanVar(value=False)
        self.show_password_button = ctk.CTkButton(password_frame,
                                                image=self.invisible_eye,
                                                command=self.toggle_password_visibility,
                                                width=40,
                                                height=40,
                                                corner_radius=10,
                                                text="")
        self.show_password_button.pack(side='left', padx=5)
        
        # Remember me checkbox
        remember_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        remember_frame.pack(pady=10, fill='x')
        self.remember_var = ctk.BooleanVar(value=False)
        self.remember_checkbox = ctk.CTkCheckBox(remember_frame, 
                                               text="Se souvenir de moi",
                                               variable=self.remember_var,
                                               font=("Helvetica", 12))
        self.remember_checkbox.pack(side='left', padx=5)
        
        # Buttons frame
        button_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        button_frame.pack(pady=20, fill='x')
        
        # Login button
        login_button = ctk.CTkButton(button_frame,
                                   text="Se connecter",
                                   command=self.login,
                                   width=200,
                                   height=40,
                                   corner_radius=10,
                                   font=("Helvetica", 14, "bold"))
        login_button.pack(pady=10)
        
        # Register button
        register_button = ctk.CTkButton(button_frame,
                                      text="S'inscrire",
                                      command=self.show_register,
                                      width=200,
                                      height=40,
                                      corner_radius=10,
                                      font=("Helvetica", 14))
        register_button.pack(pady=5)
        
        # Forgot password link
        forgot_button = ctk.CTkButton(button_frame,
                                    text="Mot de passe oublié?",
                                    command=self.show_forgot_password,
                                    fg_color="transparent",
                                    text_color=("gray10", "gray90"),
                                    hover_color=("gray70", "gray30"),
                                    font=("Helvetica", 12))
        forgot_button.pack(pady=5)
    
    def setup_register_ui(self):
        self.register_frame = ctk.CTkFrame(self, corner_radius=15)
        self.register_frame.pack(pady=20, padx=20, fill='both', expand=True)
        
        # Header with logo and title
        header_frame = ctk.CTkFrame(self.register_frame, fg_color="transparent")
        header_frame.pack(pady=(20, 10), padx=10, fill='x')
        
        # Logo and title
        logo_label = ctk.CTkLabel(header_frame, text="🎬", font=("Helvetica", 40))
        logo_label.pack(side='left', padx=10)
        
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(side='left', padx=10)
        ctk.CTkLabel(title_frame, text="YouTube Downloader", font=("Helvetica", 24, "bold")).pack()
        ctk.CTkLabel(title_frame, text="Créez votre compte", font=("Helvetica", 14)).pack()
        
        # Back button
        back_button = ctk.CTkButton(header_frame,
                                  text="←",
                                  command=self.show_login,
                                  width=40,
                                  height=40,
                                  corner_radius=20,
                                  font=("Helvetica", 16))
        back_button.pack(side='right', padx=10)
        
        # Main content frame
        content_frame = ctk.CTkFrame(self.register_frame, fg_color="transparent")
        content_frame.pack(pady=20, padx=20, fill='both', expand=True)
        
        # Input fields with icons
        input_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        input_frame.pack(pady=20, padx=20, fill='x')
        
        # Username field
        username_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        username_frame.pack(pady=10, fill='x')
        ctk.CTkLabel(username_frame, text="👤", font=("Helvetica", 16)).pack(side='left', padx=5)
        self.register_username_entry = ctk.CTkEntry(username_frame,
                                                  placeholder_text="Nom d'utilisateur",
                                                  width=300,
                                                  height=40,
                                                  corner_radius=10)
        self.register_username_entry.pack(side='left', padx=5, fill='x', expand=True)
        
        # Email field
        email_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        email_frame.pack(pady=10, fill='x')
        ctk.CTkLabel(email_frame, text="📧", font=("Helvetica", 16)).pack(side='left', padx=5)
        self.register_email_entry = ctk.CTkEntry(email_frame,
                                               placeholder_text="Email",
                                               width=300,
                                               height=40,
                                               corner_radius=10)
        self.register_email_entry.pack(side='left', padx=5, fill='x', expand=True)
        
        # Password field
        password_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        password_frame.pack(pady=10, fill='x')
        ctk.CTkLabel(password_frame, text="🔒", font=("Helvetica", 16)).pack(side='left', padx=5)
        self.register_password_entry = ctk.CTkEntry(password_frame,
                                                  placeholder_text="Mot de passe",
                                                  show="*",
                                                  width=300,
                                                  height=40,
                                                  corner_radius=10)
        self.register_password_entry.pack(side='left', padx=5, fill='x', expand=True)
        # Bind password entry to check strength on key release
        self.register_password_entry.bind("<KeyRelease>", self.check_password_strength)
        
        # Show/hide password button
        self.register_show_password_var = ctk.BooleanVar(value=False)
        self.register_show_password_button = ctk.CTkButton(password_frame,
                                                         image=self.invisible_eye,
                                                         command=self.toggle_register_password_visibility,
                                                         width=40,
                                                         height=40,
                                                         corner_radius=10,
                                                         text="")
        self.register_show_password_button.pack(side='left', padx=5)
        
        # Password confirmation field
        confirm_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        confirm_frame.pack(pady=10, fill='x')
        ctk.CTkLabel(confirm_frame, text="🔒", font=("Helvetica", 16)).pack(side='left', padx=5)
        self.register_confirm_entry = ctk.CTkEntry(confirm_frame,
                                                 placeholder_text="Confirmer le mot de passe",
                                                 show="*",
                                                 width=300,
                                                 height=40,
                                                 corner_radius=10)
        self.register_confirm_entry.pack(side='left', padx=5, fill='x', expand=True)
        
        # Show/hide confirm password button
        self.register_show_confirm_var = ctk.BooleanVar(value=False)
        self.register_show_confirm_button = ctk.CTkButton(confirm_frame,
                                                        image=self.invisible_eye,
                                                        command=self.toggle_register_confirm_visibility,
                                                        width=40,
                                                        height=40,
                                                        corner_radius=10,
                                                        text="")
        self.register_show_confirm_button.pack(side='left', padx=5)
        
        # Password strength indicator
        strength_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        strength_frame.pack(pady=5, fill='x')
        
        self.password_strength_label = ctk.CTkLabel(strength_frame,
                                                  text="Force du mot de passe: Très faible",
                                                  font=("Helvetica", 12))
        self.password_strength_label.pack(side='left', padx=5)
        
        # Password strength progress bar
        self.password_strength_bar = ctk.CTkProgressBar(strength_frame, width=300, height=10)
        self.password_strength_bar.pack(side='left', padx=5, fill='x', expand=True)
        self.password_strength_bar.set(0)  # Initial value
        
        # Buttons frame
        button_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        button_frame.pack(pady=20, fill='x')
        
        # Register button
        register_button = ctk.CTkButton(button_frame,
                                      text="S'inscrire",
                                      command=self.register,
                                      width=200,
                                      height=40,
                                      corner_radius=10,
                                      font=("Helvetica", 14, "bold"))
        register_button.pack(pady=10)
        
        # Back to login link
        back_link = ctk.CTkButton(button_frame,
                                text="Déjà un compte? Se connecter",
                                command=self.show_login,
                                fg_color="transparent",
                                text_color=("gray10", "gray90"),
                                hover_color=("gray70", "gray30"),
                                font=("Helvetica", 12))
        back_link.pack(pady=5)
    
    def show_register(self):
        self.login_frame.pack_forget()
        self.setup_register_ui()
    
    def show_login(self):
        if hasattr(self, 'register_frame'):
            self.register_frame.pack_forget()
        self.setup_login_ui()
    
    def register(self):
        username = self.register_username_entry.get()
        email = self.register_email_entry.get()
        password = self.register_password_entry.get()
        confirm = self.register_confirm_entry.get()
        
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
        password = self.register_password_entry.get()
        strength = 0
        feedback = "Faible"
        color = "#FF0000"  # Rouge par défaut (très faible)
        
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
            color = "#FF0000"  # Rouge
        elif strength <= 0.5:
            feedback = "Faible"
            color = "#FFA500"  # Orange
        elif strength <= 0.75:
            feedback = "Moyen"
            color = "#FFFF00"  # Jaune
        else:
            feedback = "Fort"
            color = "#00FF00"  # Vert
        
        # Mettre à jour le texte et la barre de progression
        self.password_strength_label.configure(text=f"Force du mot de passe: {feedback}")
        self.password_strength_bar.set(strength)  # Mettre à jour la valeur de la barre
        self.password_strength_bar.configure(progress_color=color)  # Changer la couleur
    
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
        self.create_bar_chart(stats_frame, "📊 Téléchargements par jour", downloads_per_day)
        
        # Graphique des types de contenu
        content_types = self.get_content_type_stats()
        self.create_pie_chart(stats_frame, "📈 Types de contenu", content_types)
        
        # Historique des téléchargements
        history_header = ctk.CTkFrame(frame)
        history_header.pack(pady=(20,10), padx=10, fill='x')
        
        ctk.CTkLabel(history_header, text="📋 Historique des téléchargements", 
                    font=("Helvetica", 16, "bold")).pack(side='left', padx=5)
        
        # Search bar
        search_frame = ctk.CTkFrame(history_header)
        search_frame.pack(side='right', padx=5)
        
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.filter_history())
        
        search_entry = ctk.CTkEntry(search_frame, 
                                  placeholder_text="🔍 Rechercher...",
                                  textvariable=self.search_var,
                                  width=200)
        search_entry.pack(side='left', padx=5)
        
        # Créer un cadre défilable pour l'historique
        self.history_frame = ctk.CTkScrollableFrame(frame, height=400)
        self.history_frame.pack(pady=10, padx=10, fill='both', expand=True)
        
        # Charger et afficher l'historique des téléchargements
        self.load_download_history()
    
    def filter_history(self):
        search_term = self.search_var.get().lower()
        for widget in self.history_frame.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                # Get the title label (first label in right frame)
                title_label = widget.winfo_children()[1].winfo_children()[0]
                title = title_label.cget("text").lower()
                if search_term in title:
                    widget.pack(pady=10, padx=5, fill='x')
                else:
                    widget.pack_forget()
    
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
            item_frame = ctk.CTkFrame(self.history_frame, corner_radius=10)
            item_frame.pack(pady=10, padx=5, fill='x')
            
            # Créer le cadre gauche pour la miniature
            left_frame = ctk.CTkFrame(item_frame, corner_radius=10)
            left_frame.pack(side='left', padx=5, pady=5)
            
            # Charger et afficher la miniature
            try:
                # Vérifier si la miniature est stockée dans la base de données
                if 'thumbnail' in item and item['thumbnail']:
                    img = Image.open(BytesIO(item['thumbnail']))
                    img = img.resize((120, 90), Image.Resampling.LANCZOS)
                    photo = ctk.CTkImage(light_image=img, dark_image=img, size=(120, 90))
                    thumbnail_label = ctk.CTkLabel(left_frame, image=photo, text="")
                    thumbnail_label.image = photo
                    thumbnail_label.pack()
                # Sinon, essayer de la récupérer depuis l'URL
                elif 'thumbnail_url' in item and item['thumbnail_url']:
                    response = requests.get(item['thumbnail_url'])
                    img = Image.open(BytesIO(response.content))
                    img = img.resize((120, 90), Image.Resampling.LANCZOS)
                    photo = ctk.CTkImage(light_image=img, dark_image=img, size=(120, 90))
                    thumbnail_label = ctk.CTkLabel(left_frame, image=photo, text="")
                    thumbnail_label.image = photo
                    thumbnail_label.pack()
                else:
                    raise Exception("No thumbnail available")
            except Exception as e:
                # Si le chargement de la miniature échoue, afficher un espace réservé
                ctk.CTkLabel(left_frame, text="🎥 Pas de miniature", width=120, height=90).pack()
            
            # Créer le cadre droit pour les informations et les boutons
            right_frame = ctk.CTkFrame(item_frame, corner_radius=10)
            right_frame.pack(side='left', fill='both', expand=True, padx=5, pady=5)
            
            # Étiquettes d'information avec icônes
            info_frame = ctk.CTkFrame(right_frame)
            info_frame.pack(fill='x', padx=5, pady=5)
            
            ctk.CTkLabel(info_frame, text=f"📝 Titre: {item['title']}", 
                        font=("Helvetica", 12, "bold")).pack(anchor='w', pady=2)
            
            # Afficher le canal si disponible
            if 'channel' in item and item['channel']:
                ctk.CTkLabel(info_frame, text=f"👤 Canal: {item['channel']}").pack(anchor='w', pady=2)
            
            type_icon = "🎬" if item['type'] == 'video' else "🎵" if item['type'] == 'audio' else "📄"
            ctk.CTkLabel(info_frame, text=f"{type_icon} Type: {item['type'].capitalize()}").pack(anchor='w', pady=2)
            
            format_icon = "📁" if item.get('format') else "❌"
            ctk.CTkLabel(info_frame, text=f"{format_icon} Format: {item.get('format', 'N/A')}").pack(anchor='w', pady=2)
            
            if item['type'] == 'video':
                quality_icon = "📊" if item.get('quality') else "❌"
                ctk.CTkLabel(info_frame, text=f"{quality_icon} Qualité: {item.get('quality', 'N/A')}").pack(anchor='w', pady=2)
            
            # Afficher la taille du fichier
            size_icon = "💾"
            file_size = item.get('file_size', 0)
            if file_size > 0:
                size_mb = file_size / 1024 / 1024
                ctk.CTkLabel(info_frame, text=f"{size_icon} Taille: {size_mb:.2f} MB").pack(anchor='w', pady=2)
            else:
                ctk.CTkLabel(info_frame, text=f"{size_icon} Taille: N/A").pack(anchor='w', pady=2)
            
            time_icon = "⏰"
            ctk.CTkLabel(info_frame, text=f"{time_icon} Téléchargé le: {item['timestamp'].strftime('%d/%m/%Y %H:%M:%S')}").pack(anchor='w', pady=2)
            
            # Créer le cadre des boutons
            button_frame = ctk.CTkFrame(right_frame)
            button_frame.pack(anchor='w', pady=(5,0))
            
            # Bouton pour ouvrir dans YouTube
            if 'url' in item and item['url']:
                ctk.CTkButton(
                    button_frame,
                    text="▶️ Ouvrir dans YouTube",
                    command=lambda url=item['url']: self.open_youtube(url),
                    width=150,
                    corner_radius=8
                ).pack(side='left', padx=5)
            
            # Bouton pour ouvrir le fichier local (uniquement si le fichier existe)
            file_path = os.path.join(
                self.video_path if item['type'] == 'video' else self.audio_path,
                item.get('file_path', '')
            )
            if os.path.exists(file_path):
                ctk.CTkButton(
                    button_frame,
                    text="📂 Ouvrir le fichier",
                    command=lambda path=file_path: self.open_local_file(path),
                    width=150,
                    corner_radius=8
                ).pack(side='left', padx=5)
                
                # Ajouter le bouton de transcription pour les fichiers vidéo
                if item['type'] == 'Vidéo':
                    ctk.CTkButton(
                        button_frame,
                        text="📝 Générer la transcription",
                        command=lambda video=item: self.generate_transcription(video),
                        width=150,
                        corner_radius=8
                    ).pack(side='left', padx=5)

    def generate_transcription(self, video):
        # Create a dialog for transcription options
        dialog = ctk.CTkToplevel(self)
        dialog.title("Transcription Options")
        dialog.geometry("300x200-0-0")
        
        # Language selection
        ctk.CTkLabel(dialog, text="Language:").pack(pady=5)
        language_var = ctk.StringVar(value="en")
        language_menu = ctk.CTkOptionMenu(dialog, variable=language_var,
                                        values=["en", "fr", "es", "de", "it"])
        language_menu.pack(pady=5)
        
        # Format selection (now only PDF)
        ctk.CTkLabel(dialog, text="Format: PDF").pack(pady=5)
        
        # Generate button
        ctk.CTkButton(
            dialog,
            text="Generate",
            command=lambda: self.start_transcription(
                video,
                language_var.get(),
                "pdf",
                dialog
            )
        ).pack(pady=20)

    def start_transcription(self, video, language, format_type, dialog):
        try:
            # Create PDF document
            output_path = os.path.join(
                self.audio_path,
                f"{video['title']}_transcription.pdf"
            )
            
            # Create PDF with basic information
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Add title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=30
            )
            story.append(Paragraph(f"Transcription: {video['title']}", title_style))
            
            # Add video information
            info_style = ParagraphStyle(
                'CustomInfo',
                parent=styles['Normal'],
                fontSize=12,
                spaceAfter=20
            )
            story.append(Paragraph(f"Language: {language}", info_style))
            story.append(Paragraph(f"Original URL: {video['url']}", info_style))
            story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", info_style))
            
            # Add placeholder for transcription content
            story.append(Spacer(1, 20))
            story.append(Paragraph("Transcription content will be generated here...", styles['Normal']))
            
            # Build the PDF
            doc.build(story)
            
            messagebox.showinfo("Success", f"Transcription PDF generated successfully!\nSaved to: {output_path}")
            dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate transcription: {str(e)}")
        dialog.destroy()

    def open_youtube(self, url):
        import webbrowser
        webbrowser.open(url)
    
    def open_local_file(self, path):
        import subprocess
        subprocess.Popen(['explorer', path], shell=True)
    
    def on_content_type_change(self, choice):
        # If we have video info, just update the options
        if hasattr(self, '_video_info'):
            self.update_format_and_quality_options()
            return
        
        # Reset options if no URL is checked
        self.format_frame.pack(pady=5, padx=10, fill='x')
        self.quality_frame.pack(pady=5, padx=10, fill='x')
        
        # Reset selectors to default values
        self.format_var.set("---")
        self.quality_var.set("---")
        
        if choice == "Vidéo":
            self.path_entry.delete(0, 'end')
            self.path_entry.insert(0, self.video_path)
            self.format_menu.configure(values=["mp4", "webm", "mkv", "avi"])
            self.quality_menu.configure(values=["---"])
        else:  # Audio
            self.path_entry.delete(0, 'end')
            self.path_entry.insert(0, self.audio_path)
            self.format_menu.configure(values=["mp3", "wav", "aac", "m4a", "opus"])
            # Ajouter les options de qualité audio (bitrate) - de la plus haute à la plus basse
            self.quality_menu.configure(values=["320kbps", "256kbps", "192kbps", "128kbps", "96kbps"])
            # Sélectionner une qualité par défaut
            self.quality_var.set("192kbps")
    
    def browse_path(self):
        path = filedialog.askdirectory()
        if path:
            self.path_entry.delete(0, 'end')
            self.path_entry.insert(0, path)
    
    def update_progress(self, d):
        # S'assurer que tous les widgets de progression existent
        if not hasattr(self, 'progress_bar') or not self.progress_bar.winfo_exists():
            return
            
        # S'assurer que les labels de statistiques existent
        if not hasattr(self, 'stats_frame') or not self.stats_frame.winfo_exists():
            self.stats_frame = ctk.CTkFrame(self.progress_frame, fg_color="transparent")
            self.stats_frame.pack(pady=5, fill='x')
            
            # Taille du fichier
            self.size_label = ctk.CTkLabel(self.stats_frame, text="Taille: -- / --", font=("Helvetica", 11))
            self.size_label.pack(side='left', padx=10)
            
            # Vitesse de téléchargement
            self.speed_label = ctk.CTkLabel(self.stats_frame, text="Vitesse: -- MB/s", font=("Helvetica", 11))
            self.speed_label.pack(side='left', padx=10)
            
            # Temps restant
            self.eta_label = ctk.CTkLabel(self.stats_frame, text="Temps restant: --:--", font=("Helvetica", 11))
            self.eta_label.pack(side='left', padx=10)
            
            # Format de sortie
            self.format_label = ctk.CTkLabel(self.stats_frame, text="Format: --", font=("Helvetica", 11))
            self.format_label.pack(side='right', padx=10)
            
            # Status label
            self.status_label = ctk.CTkLabel(self.stats_frame, text="Status: En attente", font=("Helvetica", 11, "bold"))
            self.status_label.pack(side='right', padx=10)
        
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)
            speed = d.get('speed', 0)
            eta = d.get('eta', 0)
            filename = d.get('filename', '').split('/')[-1].split('\\')[-1]
            format_ext = filename.split('.')[-1] if '.' in filename else ''
            
            # S'assurer que la barre de progression est visible et en mode déterminé
            if not self.progress_frame.winfo_ismapped():
                self.progress_frame.pack(pady=5, padx=10, fill='x')
                self.progress_bar.configure(mode="determinate")
                self.progress_bar.pack(pady=5, fill='x')
                self.progress_label.pack(pady=2)
                self.details_label.pack(pady=2)
                self.stats_frame.pack(pady=5, fill='x')
            
            if total > 0:
                progress = downloaded / total
                self.progress_bar.set(progress)
                
                # Changer la couleur de la barre de progression en fonction du pourcentage
                progress_percent = progress*100
                if progress_percent < 30:
                    self.progress_bar.configure(progress_color="#FF5555")  # Rouge
                elif progress_percent < 60:
                    self.progress_bar.configure(progress_color="#FFAA55")  # Orange
                elif progress_percent < 90:
                    self.progress_bar.configure(progress_color="#55AAFF")  # Bleu
                else:
                    self.progress_bar.configure(progress_color="#55FF55")  # Vert
                
                speed_mb = speed / 1024 / 1024 if speed else 0
                total_mb = total / 1024 / 1024
                downloaded_mb = downloaded / 1024 / 1024
                eta_str = self.format_time(eta) if eta else "--:--"
                
                # Mettre à jour le label principal avec le pourcentage et une barre visuelle améliorée
                progress_bar_visual = "█" * int(progress_percent/5) + "░" * (20 - int(progress_percent/5))
                self.progress_label.configure(
                    text=f"Téléchargement en cours: {progress_percent:.1f}% {progress_bar_visual}")
                
                # Mettre à jour les labels détaillés avec plus d'informations
                content_type = self.content_type.get()
                format_info = f"{self.format_var.get().split(' ')[0]}" if self.format_var.get() else format_ext.upper()
                quality_info = f"{self.quality_var.get().split(' ')[0]}" if self.quality_var.get() else ""
                
                self.details_label.configure(
                    text=f"Fichier: {filename} | Type: {content_type} | Qualité: {quality_info}")
                
                # Mettre à jour les statistiques avec plus de précision
                self.size_label.configure(text=f"Taille: {downloaded_mb:.2f}MB / {total_mb:.2f}MB")
                self.speed_label.configure(text=f"Vitesse: {speed_mb:.2f}MB/s")
                self.eta_label.configure(text=f"Temps restant: {eta_str}")
                
                # Afficher le format de sortie
                if hasattr(self, 'format_label'):
                    self.format_label.configure(text=f"Format: {format_info}")
                
                # Mettre à jour le titre de la fenêtre avec le pourcentage et le nom du fichier
                self.title(f"Téléchargeur YouTube - {progress_percent:.1f}% - {filename}")
                
                # Mettre à jour le statut avec la couleur correspondante
                if progress_percent < 30:
                    status_color = "#FF5555"  # Rouge
                    status_text = "Démarrage"
                elif progress_percent < 60:
                    status_color = "#FFAA55"  # Orange
                    status_text = "En cours"
                elif progress_percent < 90:
                    status_color = "#55AAFF"  # Bleu
                    status_text = "Avancé"
                else:
                    status_color = "#55FF55"  # Vert
                    status_text = "Finalisation"
                
                self.status_label.configure(text=f"Status: {status_text}", text_color=status_color)
                
                # Stocker les informations de progression dans la base de données
                # Créer un ID de téléchargement si nécessaire
                if not hasattr(self, '_current_download_id') and hasattr(self, '_video_info'):
                    try:
                        # Créer une entrée temporaire pour suivre la progression
                        temp_entry = {
                            "username": self.current_user,
                            "video_id": self._video_info.get('id', ''),
                            "title": self._video_info.get('title', 'Unknown'),
                            "start_time": datetime.now(),
                            "status": "downloading"
                        }
                        result = self.db['download_progress'].insert_one(temp_entry)
                        self._current_download_id = result.inserted_id
                    except Exception as e:
                        print(f"Erreur lors de la création de l'entrée de progression: {e}")
                
                # Mettre à jour la progression dans la base de données
                if hasattr(self, '_current_download_id'):
                    try:
                        self.db['download_progress'].update_one(
                            {"_id": self._current_download_id},
                            {"$set": {
                                "progress": progress,
                                "progress_percent": progress_percent,
                                "downloaded": downloaded,
                                "downloaded_mb": downloaded_mb,
                                "total": total,
                                "total_mb": total_mb,
                                "speed": speed,
                                "speed_mb": speed_mb,
                                "eta": eta,
                                "eta_str": eta_str,
                                "filename": filename,
                                "format": format_info,
                                "quality": quality_info,
                                "status": "downloading",
                                "status_text": status_text,
                                "last_update": datetime.now()
                            }},
                            upsert=True
                        )
                    except Exception as e:
                        print(f"Erreur lors de la mise à jour de la progression: {e}")
                
                # Mettre à jour l'interface pour qu'elle reste réactive
                self.update_idletasks()
        elif d['status'] == 'finished':
            self.progress_bar.set(1.0)
            # Définir la couleur verte pour indiquer que le téléchargement est terminé
            self.progress_bar.configure(progress_color="#55FF55")  # Vert
            progress_bar_visual = "█" * 20  # Barre complète
            
            # Obtenir le format final
            filename = d.get('filename', '').split('/')[-1].split('\\')[-1]
            format_ext = filename.split('.')[-1].upper() if '.' in filename else ''
            total_bytes = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
            
            # Mettre à jour les labels avec les informations finales
            self.progress_label.configure(
                text=f"Téléchargement terminé! {progress_bar_visual}")
            self.details_label.configure(
                text=f"Fichier: {filename} | Format final: {format_ext}")
            
            # Mettre à jour le titre de la fenêtre
            self.title(f"Téléchargeur YouTube - Téléchargement terminé!")
            
            # Mettre à jour l'interface
            self.update_idletasks()
            self.progress_label.configure(text=f"Traitement du fichier téléchargé... {progress_bar_visual}")
            self.details_label.configure(text="Conversion et finalisation en cours...")
            self.size_label.configure(text="Taille: Terminé")
            self.speed_label.configure(text="Vitesse: --")
            self.eta_label.configure(text="Temps restant: 0:00")
            self.title("Téléchargeur YouTube - Finalisation")
            
            # Sauvegarder les informations du téléchargement dans la base de données
            if hasattr(self, '_video_info') and self.current_user:
                try:
                    # Récupérer les informations du téléchargement
                    video_info = self._video_info
                    download_format = self.format_var.get() if hasattr(self, 'format_var') else 'Unknown'
                    download_quality = self.quality_var.get() if hasattr(self, 'quality_var') else 'Unknown'
                    download_type = 'Audio' if self.content_type.get() == "Audio" else 'Vidéo'
                    
                    # Récupérer la miniature
                    thumbnail_url = video_info.get('thumbnail', '')
                    thumbnail_data = None
                    if thumbnail_url:
                        try:
                            response = requests.get(thumbnail_url, timeout=10)
                            if response.status_code == 200:
                                thumbnail_data = response.content
                        except Exception as e:
                            print(f"Erreur lors de la récupération de la miniature: {e}")
                    
                    # Chemin complet du fichier
                    file_path = d.get('filename', '')
                    
                    # Créer l'entrée dans la base de données
                    download_entry = {
                        "username": self.current_user,
                        "video_id": video_info.get('id', ''),
                        "title": video_info.get('title', 'Unknown'),
                        "channel": video_info.get('channel', 'Unknown'),
                        "duration": video_info.get('duration', 0),
                        "format": download_format.split(' ')[0] if ' ' in download_format else download_format,
                        "quality": download_quality,
                        "type": download_type,
                        "file_size": total_bytes,
                        "file_path": file_path,  # Chemin complet pour pouvoir ouvrir le fichier
                        "thumbnail": thumbnail_data,
                        "timestamp": datetime.now(),
                        "url": video_info.get('webpage_url', '')
                    }
                    
                    # Insérer dans la collection downloads
                    result = self.db['downloads'].insert_one(download_entry)
                    download_id = result.inserted_id
                    
                    # Stocker l'ID pour les mises à jour futures
                    self._current_download_id = download_id
                    
                    # Mettre à jour le statut de progression à 100%
                    self.db['download_progress'].update_one(
                        {"download_id": self._current_download_id},
                        {"$set": {
                            "progress": 1.0,
                            "status": "completed",
                            "last_update": datetime.now()
                        }},
                        upsert=True
                    )
                    
                    # Mettre à jour l'historique des téléchargements si visible
                    if hasattr(self, 'history_content_frame'):
                        self.after(1000, self.load_download_history)  # Délai pour s'assurer que la BD est mise à jour
                        
                    # Mettre à jour les statistiques du tableau de bord
                    if hasattr(self, 'total_downloads_label'):
                        self.after(1000, self.update_dashboard_stats)
                        
                except Exception as e:
                    print(f"Erreur lors de l'enregistrement de l'historique: {e}")
                    
        elif d['status'] == 'error':
            self.progress_frame.pack_forget()
            self.title("Téléchargeur YouTube")
            messagebox.showerror("Erreur", f"Erreur de téléchargement: {d.get('error')}")
            
            # Enregistrer l'erreur dans la base de données
            if hasattr(self, '_current_download_id'):
                try:
                    self.db['download_progress'].update_one(
                        {"download_id": self._current_download_id},
                        {"$set": {
                            "status": "error",
                            "error_message": d.get('error', 'Unknown error'),
                            "last_update": datetime.now()
                        }}
                    )
                except Exception as e:
                    print(f"Erreur lors de l'enregistrement de l'erreur: {e}")
    
    def format_time(self, seconds):
        """Convertit des secondes en format MM:SS"""
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours > 0:
            return f"{int(hours)}:{int(minutes):02d}:{int(seconds):02d}"
        else:
            return f"{int(minutes):02d}:{int(seconds):02d}"
    
    def check_url(self):
        url = self.url_entry.get()
        if not url:
            messagebox.showerror("Erreur", "Veuillez entrer une URL YouTube valide")
            return

        # Show progress frame and reset
        self.progress_frame.pack(pady=5, padx=10, fill='x')
        self.progress_bar.pack(pady=5, fill='x')
        self.progress_label.configure(text="Vérification de l'URL en cours...", font=("Helvetica", 12, "bold"))
        self.progress_label.pack(pady=2)
        self.progress_bar.set(0)
        
        # Initialiser les labels de détails
        self.details_label.configure(text=f"URL: {url}")
        self.size_label.configure(text="Initialisation...")
        self.speed_label.configure(text="")
        self.eta_label.configure(text="")
        self.title("Téléchargeur YouTube - Vérification d'URL")

        # Create an indeterminate progress bar for URL verification
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()
        
        def update_progress(step, total_steps=6):
            progress = step / total_steps
            # Créer une barre visuelle pour montrer la progression
            progress_bar_visual = "█" * int(progress*20) + "░" * (20 - int(progress*20))
            self.after(0, lambda: self.progress_bar.set(progress))
            self.after(0, lambda: self.progress_label.configure(
                text=f"Vérification: {progress*100:.0f}% {progress_bar_visual}"
            ))

        def fetch_info():
            try:
                # Step 1: Initialize
                update_progress(1)
                self.after(0, lambda: self.progress_label.configure(
                    text="🔄 Initialisation de la connexion... " + "█" * 3 + "░" * 17
                ))
                time.sleep(0.5)  # Small delay for visual feedback

                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': False,
                    'listformats': True  # Lister tous les formats disponibles
                }

                # Step 2: Connecting
                update_progress(2)
                self.after(0, lambda: self.progress_label.configure(
                    text="🌐 Connexion à YouTube... " + "█" * 6 + "░" * 14
                ))
                time.sleep(0.5)

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # Step 3: Extracting info
                    update_progress(3)
                    self.after(0, lambda: self.progress_label.configure(
                        text="📥 Extraction des informations... " + "█" * 10 + "░" * 10
                    ))
                    self.after(0, lambda: self.size_label.configure(text="Étape 3/6"))
                    self.after(0, lambda: self.details_label.configure(text=f"URL: {url}"))
                    info = ydl.extract_info(url, download=False)
                    
                    # Store format information
                    self._video_formats = []
                    self._audio_formats = []
                    
                    # Step 4: Processing video formats
                    update_progress(4)
                    self.after(0, lambda: self.progress_label.configure(
                        text="🎬 Analyse des formats vidéo... " + "█" * 13 + "░" * 7
                    ))
                    self.after(0, lambda: self.size_label.configure(text="Étape 4/6"))
                    
                    # Process all formats
                    for f in info['formats']:
                        if f.get('vcodec', 'none') != 'none' and f.get('height'):
                            self._video_formats.append({
                                'format_id': f['format_id'],
                                'ext': f['ext'],
                                'height': f['height'],
                                'vcodec': f.get('vcodec', 'unknown'),
                                'filesize': f.get('filesize', 0),
                                'tbr': f.get('tbr', 0)
                            })
                        elif f.get('acodec', 'none') != 'none' and f.get('abr'):
                            self._audio_formats.append({
                                'format_id': f['format_id'],
                                'ext': f['ext'],
                                'abr': f['abr'],
                                'acodec': f.get('acodec', 'unknown'),
                                'filesize': f.get('filesize', 0)
                            })
                    
                    # Step 5: Sorting formats
                    update_progress(5)
                    self.after(0, lambda: self.progress_label.configure(
                        text="📊 Organisation des formats... " + "█" * 16 + "░" * 4
                    ))
                    self.after(0, lambda: self.size_label.configure(text="Étape 5/6"))
                    
                    # Sort formats
                    self._video_formats.sort(key=lambda x: (x['height'], x.get('tbr', 0)), reverse=True)
                    self._audio_formats.sort(key=lambda x: x['abr'], reverse=True)
                    
                    # Store video info
                    self._video_info = info
                    
                    # Step 6: Finalizing
                    # Stop indeterminate progress and switch to determinate
                    self.after(0, lambda: self.progress_bar.stop())
                    self.after(0, lambda: self.progress_bar.configure(mode="determinate"))
                    self.after(0, lambda: self.progress_bar.set(1.0))
                    self.after(0, lambda: self.progress_label.configure(
                        text="✅ URL vérifiée avec succès! " + "█" * 20
                    ))
                    self.after(0, lambda: self.size_label.configure(text="Étape 6/6 - Terminé"))
                    self.after(0, lambda: self.details_label.configure(text=f"Titre: {info.get('title', 'Inconnu')}"))
                    time.sleep(0.5)
                    
                    # Process and display video info
                    self.after(0, lambda: self.process_video_info(info))
                    
            except Exception as e:
                # Stop indeterminate progress in case of error
                self.after(0, lambda: self.progress_bar.stop())
                self.after(0, lambda: self.progress_bar.configure(mode="determinate"))
                self.after(0, lambda: self.progress_label.configure(text="❌ Erreur lors de la vérification"))
                self.after(0, lambda: messagebox.showerror("Erreur", 
                    f"Impossible de récupérer les informations de la vidéo : {str(e)}\n"
                    "Vérifiez que l'URL est correcte et que votre connexion internet fonctionne."))
            finally:
                # Ne pas cacher la barre de progression en cas de succès, seulement en cas d'erreur
                if not hasattr(self, '_video_info'):
                    self.after(0, lambda: self.progress_frame.pack_forget())
        
        Thread(target=fetch_info).start()

    def process_video_info(self, info):
        try:
            # Clear previous info
            for widget in self.info_frame.winfo_children():
                widget.destroy()
            
            # Create a frame for video information
            info_container = ctk.CTkFrame(self.info_frame, fg_color="transparent")
            info_container.pack(pady=10, padx=10, fill='x')
            
            # Left side - Thumbnail
            left_frame = ctk.CTkFrame(info_container, fg_color="transparent")
            left_frame.pack(side='left', padx=10)
            
            # Display thumbnail
            if 'thumbnail' in info:
                try:
                    response = requests.get(info['thumbnail'])
                    img = Image.open(BytesIO(response.content))
                    img = img.resize((200, 150), Image.Resampling.LANCZOS)
                    photo = ctk.CTkImage(light_image=img, dark_image=img, size=(200, 150))
                    thumbnail_label = ctk.CTkLabel(left_frame, image=photo, text="")
                    thumbnail_label.image = photo
                    thumbnail_label.pack()
                except Exception as e:
                    ctk.CTkLabel(left_frame, text="🎬 Pas de miniature",
                               width=200, height=150).pack()
            
            # Right side - Information
            right_frame = ctk.CTkFrame(info_container, fg_color="transparent")
            right_frame.pack(side='left', padx=10, fill='x', expand=True)
            
            # Title with ellipsis if too long
            title = info.get('title', 'Unknown Title')
            if len(title) > 50:
                title = title[:47] + "..."
            ctk.CTkLabel(right_frame, 
                        text=title,
                        font=("Helvetica", 14, "bold")).pack(anchor='w')
            
            # Duration
            duration = info.get('duration')
            if duration:
                minutes = duration // 60
                seconds = duration % 60
                ctk.CTkLabel(right_frame, 
                           text=f"⏱️ Durée: {minutes}:{seconds:02d}",
                           font=("Helvetica", 12)).pack(anchor='w')
            
            # Channel info
            if info.get('channel'):
                ctk.CTkLabel(right_frame,
                           text=f"📺 Chaîne: {info['channel']}",
                           font=("Helvetica", 12)).pack(anchor='w')
            
            # View count if available
            if info.get('view_count'):
                view_count = "{:,}".format(info['view_count']).replace(',', ' ')
                ctk.CTkLabel(right_frame,
                           text=f"👁️ Vues: {view_count}",
                           font=("Helvetica", 12)).pack(anchor='w')
            
            # Upload date if available
            if info.get('upload_date'):
                upload_date = datetime.strptime(info['upload_date'], '%Y%m%d').strftime('%d/%m/%Y')
                ctk.CTkLabel(right_frame,
                           text=f"📅 Date: {upload_date}",
                           font=("Helvetica", 12)).pack(anchor='w')
            
            # Update options based on content type
            self.update_format_and_quality_options()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error processing video info: {str(e)}")

    def update_format_and_quality_options(self):
        content_type = self.content_type.get()
        
        # Define available formats for each type
        video_formats = {
            "mp4": "MP4 (Recommended)",
            "webm": "WebM",
            "mkv": "MKV",
            "avi": "AVI",
            "mov": "MOV (QuickTime)",
            "flv": "FLV (Flash)",
            "3gp": "3GP (Mobile)",
            "wmv": "WMV (Windows Media)"
        }
        # Tous les formats audio disponibles via ffmpeg
        audio_formats = {
            "mp3": "MP3 (Recommended)",
            "wav": "WAV (High Quality)",
            "aac": "AAC",
            "m4a": "M4A",
            "opus": "Opus",
            "flac": "FLAC (Lossless)",
            "ogg": "OGG Vorbis",
            "alac": "ALAC (Apple Lossless)",
            "mka": "MKA (Matroska Audio)",
            "wma": "WMA (Windows Media Audio)",
            "aiff": "AIFF (Audio Interchange)",
            "au": "AU (Sun Audio)",
            "amr": "AMR (Adaptive Multi-Rate)"
        }
        
        if content_type == "Vidéo":
            # Update format menu with video formats
            format_values = list(video_formats.values())
            self.format_menu.configure(values=format_values)
            self.format_var.set(format_values[0])
            
            # Filtrer les qualités vidéo pour ne garder que la taille minimale pour chaque résolution
            # Regrouper les formats par résolution
            resolution_groups = {}
            for f in self._video_formats:
                resolution = f['height']
                if resolution not in resolution_groups or f.get('filesize', float('inf')) < resolution_groups[resolution].get('filesize', float('inf')):
                    resolution_groups[resolution] = f
            
            # Créer la liste des qualités filtrées
            filtered_formats = list(resolution_groups.values())
            filtered_formats.sort(key=lambda x: x['height'], reverse=True)
            
            # Mettre à jour le menu des qualités
            qualities = []
            for f in filtered_formats:
                if f.get('filesize'):
                    size_mb = self.format_size(f.get('filesize', 0))
                    qualities.append(f"{f['height']}p ({size_mb})")
                else:
                    qualities.append(f"{f['height']}p ({f['tbr']:.1f}Mbps)")
            
            self.quality_menu.configure(values=qualities)
            self.quality_var.set(qualities[0] if qualities else "---")
            
        else:  # Audio
            # Update format menu with audio formats
            format_values = list(audio_formats.values())
            self.format_menu.configure(values=format_values)
            self.format_var.set(format_values[0])
            
            # Trier les formats audio par bitrate (du plus élevé au plus bas)
            sorted_audio_formats = sorted(self._audio_formats, key=lambda x: x['abr'], reverse=True)
            
            # Créer une liste de qualités avec des informations supplémentaires
            qualities = []
            for f in sorted_audio_formats:
                # Ajouter le bitrate avec des informations sur le codec si disponible
                bitrate = int(f['abr'])
                codec_info = f.get('acodec', '').upper()
                if f.get('filesize'):
                    size_info = self.format_size(f.get('filesize', 0))
                    qualities.append(f"{bitrate}kbps - {codec_info} ({size_info})")
                else:
                    qualities.append(f"{bitrate}kbps - {codec_info}")
            
            # Si aucun format audio n'est disponible, proposer des options standard
            if not qualities:
                qualities = ["320kbps", "256kbps", "192kbps", "128kbps", "96kbps"]
                
            self.quality_menu.configure(values=qualities)
            self.quality_var.set(qualities[0] if qualities else "---")
        
        # Store format mappings for later use
        self._format_mappings = video_formats if content_type == "Vidéo" else audio_formats
        
        # Update path
        self.path_entry.delete(0, 'end')
        self.path_entry.insert(0, self.video_path if content_type == "Vidéo" else self.audio_path)
        
        messagebox.showinfo("Success", "Video information loaded successfully")

    def format_size(self, size_bytes):
        """Convertit les octets en format lisible (KB, MB, GB)"""
        if size_bytes == 0 or not size_bytes:
            return "0B"
        
        size_names = ("B", "KB", "MB", "GB", "TB")
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024
            i += 1
        
        return f"{size_bytes:.1f}{size_names[i]}"
    
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
                
                # Get the actual format from the display name and clean it by removing any text in parentheses
                format_display = self.format_var.get().split(' ')[0].lower() if self.format_var.get() else ""
                target_format = next((k for k, v in self._format_mappings.items() if v.split(' ')[0].lower() == format_display), format_display)
                
                # Get quality without the bitrate info for videos
                quality_display = self.quality_var.get()
                if content_type == "Vidéo":
                    quality = quality_display.split(" ")[0].replace('p', '')
                else:
                    quality = quality_display.replace('kbps', '')
                
                # Find best matching format for selected quality
                format_info = self._format_info.get(quality_display.split(" ")[0], [])
                if not format_info:
                    self.after(0, lambda: messagebox.showerror("Error", "Selected quality is not available"))
                    return
                    
                # Sort formats by filesize to get best quality
                format_info.sort(key=lambda x: x.get('filesize', 0), reverse=True)
                best_format = format_info[0]
                
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'format': f'{best_format["format_id"]}+bestaudio' if content_type == "Vidéo" else best_format["format_id"],
                    'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
                    'progress_hooks': [self.update_progress],
                    'postprocessors': []
                }
                
                # Add format conversion if needed
                if best_format['ext'] != target_format:
                    if content_type == "Vidéo":
                        ydl_opts['postprocessors'].append({
                            'key': 'FFmpegVideoConvertor',
                            'preferedformat': target_format,
                        })
                        # Conserver le fichier original (ne pas supprimer le MP4)
                        ydl_opts['keepvideo'] = True
                    else:
                        ydl_opts['postprocessors'].append({
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': target_format,
                            'preferredquality': quality,
                        })
                        # Conserver le fichier audio original
                        ydl_opts['keepaudio'] = True

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
                        "quality": quality_display,
                        "url": url,
                        "timestamp": datetime.now(),
                        "thumbnail_url": info.get('thumbnail', ''),
                        "format": target_format,
                        "filesize": filesize
                    })
                    
                    self.after(0, lambda: self.load_download_history())
                    self.after(0, lambda: messagebox.showinfo("Success", "Download completed successfully!"))
                    
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", f"Error during download: {str(e)}"))
            finally:
                self.after(0, lambda: self.progress_frame.pack_forget())
        
        Thread(target=download_thread).start()

    def toggle_password_visibility(self):
        self.show_password_var.set(not self.show_password_var.get())
        if self.show_password_var.get():
            self.password_entry.configure(show="")
            self.show_password_button.configure(image=self.visible_eye)
        else:
            self.password_entry.configure(show="*")
            self.show_password_button.configure(image=self.invisible_eye)

    def toggle_register_password_visibility(self):
        self.register_show_password_var.set(not self.register_show_password_var.get())
        if self.register_show_password_var.get():
            self.register_password_entry.configure(show="")
            self.register_show_password_button.configure(image=self.visible_eye)
        else:
            self.register_password_entry.configure(show="*")
            self.register_show_password_button.configure(image=self.invisible_eye)

    def toggle_register_confirm_visibility(self):
        self.register_show_confirm_var.set(not self.register_show_confirm_var.get())
        if self.register_show_confirm_var.get():
            self.register_confirm_entry.configure(show="")
            self.register_show_confirm_button.configure(image=self.visible_eye)
        else:
            self.register_confirm_entry.configure(show="*")
            self.register_show_confirm_button.configure(image=self.invisible_eye)

    def setup_downloader_ui(self):
        # Create main frame
        self.downloader_frame = ctk.CTkFrame(self, corner_radius=15)
        self.downloader_frame.pack(pady=20, padx=20, fill='both', expand=True)
        
        # Header with logo and title
        header_frame = ctk.CTkFrame(self.downloader_frame, fg_color="transparent")
        header_frame.pack(pady=(20, 10), padx=10, fill='x')
        
        # Logo and title
        logo_label = ctk.CTkLabel(header_frame, text="🎬", font=("Helvetica", 40))
        logo_label.pack(side='left', padx=10)
        
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(side='left', padx=10)
        ctk.CTkLabel(title_frame, text="YouTube Downloader", font=("Helvetica", 24, "bold")).pack()
        ctk.CTkLabel(title_frame, text=f"Bienvenue, {self.current_user}", font=("Helvetica", 14)).pack()
        
        # Theme button
        self.theme_button = ctk.CTkButton(header_frame, 
                                         text="🌙" if self.appearance_mode == "light" else "☀️",
                                         command=self.toggle_theme, 
                                         width=40,
                                         height=40,
                                         corner_radius=20)
        self.theme_button.pack(side='right', padx=10)
        
        # Logout button
        logout_button = ctk.CTkButton(header_frame,
                                    text="Déconnexion",
                                    command=self.logout,
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
        # URL input frame with paste button
        url_frame = ctk.CTkFrame(self.download_tab, fg_color="transparent")
        url_frame.pack(pady=10, fill='x')
        
        ctk.CTkLabel(url_frame, text="URL YouTube:", font=("Helvetica", 14)).pack(side='left', padx=5)
        self.url_entry = ctk.CTkEntry(url_frame, 
                                    placeholder_text="Collez l'URL de la vidéo YouTube ici",
                                    width=400,
                                    height=40,
                                    corner_radius=10)
        self.url_entry.pack(side='left', padx=5, fill='x', expand=True)
        
        # Bouton Coller
        paste_button = ctk.CTkButton(url_frame,
                                   text="📋 Coller",
                                   command=self.paste_url,
                                   width=80,
                                   height=40,
                                   corner_radius=10)
        paste_button.pack(side='left', padx=5)
        
        # Bouton Vérifier URL
        check_button = ctk.CTkButton(url_frame,
                                   text="✓ Vérifier",
                                   command=self.check_url,
                                   width=80,
                                   height=40,
                                   corner_radius=10)
        check_button.pack(side='left', padx=5)
        
        # Options frame (contient tous les menus de sélection sur une ligne)
        options_frame = ctk.CTkFrame(self.download_tab, fg_color="transparent")
        options_frame.pack(pady=10, fill='x')
        
        # Type de contenu
        type_container = ctk.CTkFrame(options_frame, fg_color="transparent")
        type_container.pack(side='left', padx=10, fill='x', expand=True)
        ctk.CTkLabel(type_container, text="Type de contenu:", font=("Helvetica", 14)).pack(anchor='w')
        self.content_type = ctk.StringVar(value="Vidéo")
        type_menu = ctk.CTkOptionMenu(type_container,
                                    variable=self.content_type,
                                    values=["Vidéo", "Audio"],
                                    command=self.on_content_type_change,
                                    width=150,
                                    height=40,
                                    corner_radius=10)
        type_menu.pack(anchor='w', pady=(5, 0))
        
        # Format
        format_container = ctk.CTkFrame(options_frame, fg_color="transparent")
        format_container.pack(side='left', padx=10, fill='x', expand=True)
        ctk.CTkLabel(format_container, text="Format:", font=("Helvetica", 14)).pack(anchor='w')
        self.format_var = ctk.StringVar(value="----")
        self.format_menu = ctk.CTkOptionMenu(format_container,
                                           variable=self.format_var,
                                           values=["----"],
                                           width=150,
                                           height=40,
                                           corner_radius=10)
        self.format_menu.pack(anchor='w', pady=(5, 0))
        
        # Qualité
        quality_container = ctk.CTkFrame(options_frame, fg_color="transparent")
        quality_container.pack(side='left', padx=10, fill='x', expand=True)
        ctk.CTkLabel(quality_container, text="Qualité:", font=("Helvetica", 14)).pack(anchor='w')
        self.quality_var = ctk.StringVar(value="----")
        self.quality_menu = ctk.CTkOptionMenu(quality_container,
                                            variable=self.quality_var,
                                            values=["----"],
                                            width=150,
                                            height=40,
                                            corner_radius=10)
        self.quality_menu.pack(anchor='w', pady=(5, 0))
        
        # Path selection frame
        path_frame = ctk.CTkFrame(self.download_tab, fg_color="transparent")
        path_frame.pack(pady=10, fill='x')
        
        ctk.CTkLabel(path_frame, text="Dossier de destination:", font=("Helvetica", 14)).pack(side='left', padx=5)
        self.path_entry = ctk.CTkEntry(path_frame,
                                     placeholder_text="Sélectionnez un dossier",
                                     width=300,
                                     height=40,
                                     corner_radius=10)
        self.path_entry.pack(side='left', padx=5, fill='x', expand=True)
        
        browse_button = ctk.CTkButton(path_frame,
                                    text="📁 Parcourir",
                                    command=self.browse_path,
                                    width=100,
                                    height=40,
                                    corner_radius=10)
        browse_button.pack(side='left', padx=5)
        
        # Video info frame - Amélioré avec un style de carte
        self.info_frame = ctk.CTkFrame(self.download_tab, corner_radius=15)
        self.info_frame.pack(pady=15, padx=10, fill='x')
        
        # Titre pour le bloc d'info
        info_header = ctk.CTkFrame(self.info_frame, fg_color="transparent")
        info_header.pack(pady=(10, 5), padx=10, fill='x')
        ctk.CTkLabel(info_header, text="Informations sur la vidéo", font=("Helvetica", 16, "bold")).pack(side='left')
        
        # Contenu du bloc d'info (sera rempli dynamiquement)
        self.info_content = ctk.CTkFrame(self.info_frame, fg_color="transparent")
        self.info_content.pack(pady=(0, 10), padx=10, fill='x')
        
        # Boutons d'action
        action_frame = ctk.CTkFrame(self.download_tab, fg_color="transparent")
        action_frame.pack(pady=15, fill='x')
        
        # Bouton de téléchargement unifié
        download_button = ctk.CTkButton(action_frame,
                                      text="📥 Télécharger",
                                      command=self.download_content,
                                      width=300,
                                      height=45,
                                      corner_radius=10,
                                      font=("Helvetica", 14, "bold"))
        download_button.pack(padx=10, expand=True)
        
        # Progress frame - maintenant affiché en permanence sous le bouton de téléchargement
        self.progress_frame = ctk.CTkFrame(self.download_tab, corner_radius=10)
        self.progress_frame.pack(pady=10, padx=20, fill='x')  # Toujours visible
        
        # Titre pour le cadre de progression
        progress_title = ctk.CTkLabel(self.progress_frame, text="Progression du téléchargement", 
                                    font=("Helvetica", 14, "bold"))
        progress_title.pack(pady=(10, 5))
        
        # Barre de progression
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, width=400, height=15)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=5, padx=20, fill='x')
        
        # Label de progression
        self.progress_label = ctk.CTkLabel(self.progress_frame, text="En attente...", font=("Helvetica", 12, "bold"))
        self.progress_label.pack(pady=5)
        
        # Détails supplémentaires pour le téléchargement
        self.details_label = ctk.CTkLabel(self.progress_frame, text="Prêt pour le téléchargement", font=("Helvetica", 11))
        self.details_label.pack(pady=2)
        
        # Statistiques de téléchargement
        self.stats_frame = ctk.CTkFrame(self.progress_frame, fg_color="transparent")
        self.stats_frame.pack(pady=5, fill='x')
        
        # Taille téléchargée / Taille totale
        self.size_label = ctk.CTkLabel(self.stats_frame, text="Taille: -- / --", font=("Helvetica", 11))
        self.size_label.pack(side='left', padx=10)
        
        # Vitesse de téléchargement
        self.speed_label = ctk.CTkLabel(self.stats_frame, text="Vitesse: -- MB/s", font=("Helvetica", 11))
        self.speed_label.pack(side='left', padx=10)
        
        # Temps restant
        self.eta_label = ctk.CTkLabel(self.stats_frame, text="Temps restant: --:--", font=("Helvetica", 11))
        self.eta_label.pack(side='left', padx=10)
    
    def download_content(self):
        if not hasattr(self, '_video_info'):
            messagebox.showerror("Erreur", "Veuillez d'abord vérifier une URL YouTube valide")
            return
        
        # Vérifier si un format est sélectionné - correction pour permettre tous les formats audio
        if self.format_var.get() == "---" or self.quality_var.get() == "---":
            messagebox.showerror("Erreur", "Veuillez sélectionner un format et une qualité")
            return
        
        # Obtenir le chemin de destination
        output_path = self.path_entry.get()
        if not output_path:
            messagebox.showerror("Erreur", "Veuillez sélectionner un dossier de destination")
            return
            
        # Afficher le cadre de progression
        self.progress_frame.pack(pady=5, padx=10, fill='x')
        self.progress_bar.set(0)
        self.progress_label.configure(text="Préparation du téléchargement...")
        
        # S'assurer que tous les labels de progression existent
        if not hasattr(self, 'details_label') or not self.details_label.winfo_exists():
            self.details_label = ctk.CTkLabel(self.progress_frame, text="Initialisation...", font=("Helvetica", 11))
            self.details_label.pack(pady=2)
        else:
            self.details_label.configure(text="Initialisation...")
            
        # S'assurer que le cadre de statistiques existe
        if not hasattr(self, 'stats_frame') or not self.stats_frame.winfo_exists():
            self.stats_frame = ctk.CTkFrame(self.progress_frame, fg_color="transparent")
            self.stats_frame.pack(pady=5, fill='x')
            
            # Taille du fichier
            self.size_label = ctk.CTkLabel(self.stats_frame, text="Taille: -- / --", font=("Helvetica", 11))
            self.size_label.pack(side='left', padx=10)
            
            # Vitesse de téléchargement
            self.speed_label = ctk.CTkLabel(self.stats_frame, text="Vitesse: -- MB/s", font=("Helvetica", 11))
            self.speed_label.pack(side='left', padx=10)
            
            # Temps restant
            self.eta_label = ctk.CTkLabel(self.stats_frame, text="Temps restant: --:--", font=("Helvetica", 11))
            self.eta_label.pack(side='left', padx=10)
        else:
            self.size_label.configure(text="Taille: -- / --")
            self.speed_label.configure(text="Vitesse: -- MB/s")
            self.eta_label.configure(text="Temps restant: --:--")
            
        self.title("Téléchargeur YouTube - Préparation")
        
        content_type = self.content_type.get()
        # Nettoyer le format sélectionné en supprimant tout texte entre parenthèses
        selected_format = self.format_var.get().split(' ')[0].lower() if self.format_var.get() else ""
        selected_quality = self.quality_var.get()
        
        # Configurer les options de téléchargement selon le type de contenu
        if content_type == "Vidéo":
            # Extraire le format cible à partir de la sélection de l'utilisateur (sans le texte entre parenthèses)
            format_display = self.format_var.get().split(' ')[0].lower() if self.format_var.get() else ""
            target_format = format_display if format_display else "mp4"
            
            # Trouver la qualité vidéo sélectionnée
            format_id = None
            selected_resolution = selected_quality.split(' ')[0] if selected_quality else ""
            
            # Chercher le format exact correspondant à la résolution demandée
            for fmt in self._video_formats:
                if str(fmt['height']) + 'p' == selected_resolution and fmt['ext'] == "mp4":
                    format_id = fmt['format_id']
                    break
            
            if not format_id:
                # Si la qualité exacte n'est pas disponible en MP4, prendre la meilleure qualité disponible
                # Extraire uniquement la valeur numérique de la résolution (sans le 'p')
                resolution = selected_resolution.replace('p', '') if selected_resolution else '720'
                ydl_opts = {
                    'format': f'bestvideo[height<={resolution}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                    'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
                    'progress_hooks': [self.update_progress],
                }
            else:
                ydl_opts = {
                    'format': format_id,
                    'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
                    'progress_hooks': [self.update_progress],
                }
            
            # Ajouter un post-processeur pour convertir au format cible si différent de MP4
            if target_format != "mp4":
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': target_format,
                }]
                # Option pour conserver ou non le fichier original
                ydl_opts['keepvideo'] = True
                
            download_type = "vidéo"
        else:  # Audio
            # Extraire le format cible à partir de la sélection de l'utilisateur
            # Nettoyer le format pour obtenir uniquement le code (mp3, wav, etc.)
            format_display = self.format_var.get().split(' ')[0].lower() if self.format_var.get() else ""
            target_format = format_display if format_display else "mp3"
            
            # Extraire la qualité audio (bitrate) à partir de la sélection de l'utilisateur
            # Prendre seulement la partie numérique du bitrate (avant kbps et sans les informations supplémentaires)
            quality = selected_quality.split('kbps')[0].strip() if 'kbps' in selected_quality else '192'
            
            # Configuration pour l'audio
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
                'progress_hooks': [self.update_progress],
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': target_format,  # Utiliser directement le format cible
                    'preferredquality': quality,
                }],
                # Ne pas conserver le fichier original pour éviter la confusion
                'keepaudio': False
            }
                
            download_type = "audio"
        
        # Mettre à jour les informations de la barre de progression
        self.progress_bar.set(0)
        self.progress_bar.configure(mode="determinate")  # Assurer que la barre est en mode déterminé
        progress_bar_visual = "░" * 20  # Barre vide au début
        self.progress_label.configure(text=f"Préparation du téléchargement {download_type}... {progress_bar_visual}")
        self.details_label.configure(text=f"Format: {target_format.upper()}, Qualité: {selected_quality}")
        
        # S'assurer que la barre de progression est visible
        self.progress_frame.pack(pady=5, padx=10, fill='x')
        self.progress_bar.pack(pady=5, fill='x')
        self.progress_label.pack(pady=2)
        self.details_label.pack(pady=2)
        self.stats_frame.pack(pady=5, fill='x')
        
        # Afficher un indicateur visuel que le téléchargement va commencer
        for i in range(5):
            self.progress_bar.set((i+1)/5 * 0.1)  # Remplir jusqu'à 10% pour indiquer l'initialisation
            self.update()
            time.sleep(0.1)
        
        # Lancer le téléchargement dans un thread séparé
        def download_thread():
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([self._video_info['webpage_url']])
                
                # Afficher un message de succès
                self.after(0, lambda: messagebox.showinfo("Succès", f"Téléchargement {download_type} terminé avec succès!"))
            except Exception as e:
                error_message = f"Erreur lors du téléchargement {download_type}: {str(e)}"
                self.after(0, lambda error=error_message: messagebox.showerror("Erreur", error))
        
        # Démarrer le thread de téléchargement
        thread = Thread(target=download_thread)
        thread.daemon = True
        thread.start()
    
    def setup_dashboard_tab(self):
        # Create main container
        container = ctk.CTkFrame(self.dashboard_tab, fg_color="transparent")
        container.pack(pady=20, padx=20, fill='both', expand=True)
        
        # Stats summary section
        summary_frame = ctk.CTkFrame(container, corner_radius=15)
        summary_frame.pack(pady=10, fill='x')
        
        ctk.CTkLabel(summary_frame, text="Résumé des téléchargements", font=("Helvetica", 16, "bold")).pack(pady=10)
        
        # Create stats cards row
        stats_row = ctk.CTkFrame(summary_frame, fg_color="transparent")
        stats_row.pack(pady=10, fill='x')
        
        # Total downloads card
        total_card = ctk.CTkFrame(stats_row, corner_radius=10)
        total_card.pack(side='left', padx=10, fill='both', expand=True)
        ctk.CTkLabel(total_card, text="Total", font=("Helvetica", 14, "bold")).pack(pady=5)
        self.total_downloads_label = ctk.CTkLabel(total_card, text="0", font=("Helvetica", 24))
        self.total_downloads_label.pack(pady=5)
        
        # Video downloads card
        video_card = ctk.CTkFrame(stats_row, corner_radius=10)
        video_card.pack(side='left', padx=10, fill='both', expand=True)
        ctk.CTkLabel(video_card, text="Vidéos", font=("Helvetica", 14, "bold")).pack(pady=5)
        self.video_downloads_label = ctk.CTkLabel(video_card, text="0", font=("Helvetica", 24))
        self.video_downloads_label.pack(pady=5)
        
        # Audio downloads card
        audio_card = ctk.CTkFrame(stats_row, corner_radius=10)
        audio_card.pack(side='left', padx=10, fill='both', expand=True)
        ctk.CTkLabel(audio_card, text="Audio", font=("Helvetica", 14, "bold")).pack(pady=5)
        self.audio_downloads_label = ctk.CTkLabel(audio_card, text="0", font=("Helvetica", 24))
        self.audio_downloads_label.pack(pady=5)
        
        # Storage usage card
        storage_card = ctk.CTkFrame(stats_row, corner_radius=10)
        storage_card.pack(side='left', padx=10, fill='both', expand=True)
        ctk.CTkLabel(storage_card, text="Espace utilisé", font=("Helvetica", 14, "bold")).pack(pady=5)
        self.storage_usage_label = ctk.CTkLabel(storage_card, text="0 MB", font=("Helvetica", 24))
        self.storage_usage_label.pack(pady=5)
        
        # History section with search and filter
        history_frame = ctk.CTkFrame(container, corner_radius=15)
        history_frame.pack(pady=10, fill='both', expand=True)
        
        # History header with title and search
        history_header = ctk.CTkFrame(history_frame, fg_color="transparent")
        history_header.pack(pady=10, padx=10, fill='x')
        
        ctk.CTkLabel(history_header, text="Historique des téléchargements", font=("Helvetica", 16, "bold")).pack(side='left')
        
        # Search and filter section
        search_frame = ctk.CTkFrame(history_header, fg_color="transparent")
        search_frame.pack(side='right')
        
        # Search entry
        self.search_entry = ctk.CTkEntry(search_frame, 
                                       placeholder_text="Rechercher...",
                                       width=200,
                                       height=30,
                                       corner_radius=10)
        self.search_entry.pack(side='left', padx=5)
        self.search_entry.bind("<Return>", lambda event: self.load_download_history())
        
        # Filter dropdown for type
        self.filter_var = ctk.StringVar(value="Tous")
        filter_menu = ctk.CTkOptionMenu(search_frame,
                                      variable=self.filter_var,
                                      values=["Tous", "Vidéo", "Audio"],
                                      command=lambda _: self.load_download_history(),
                                      width=100,
                                      height=30,
                                      corner_radius=10)
        filter_menu.pack(side='left', padx=5)
        
        # Date filter
        self.date_filter_var = ctk.StringVar(value="Toutes les dates")
        date_filter_menu = ctk.CTkOptionMenu(search_frame,
                                           variable=self.date_filter_var,
                                           values=["Toutes les dates", "Aujourd'hui", "Cette semaine", "Ce mois", "Cette année"],
                                           command=lambda _: self.load_download_history(),
                                           width=120,
                                           height=30,
                                           corner_radius=10)
        date_filter_menu.pack(side='left', padx=5)
        
        # Clear filters button
        clear_filters_button = ctk.CTkButton(search_frame,
                                          text="🧹 Effacer les filtres",
                                          command=self.clear_filters,
                                          width=120,
                                          height=30,
                                          corner_radius=10)
        clear_filters_button.pack(side='left', padx=5)
        
        # Refresh button
        refresh_button = ctk.CTkButton(search_frame,
                                     text="🔄",
                                     command=self.load_download_history,
                                     width=30,
                                     height=30,
                                     corner_radius=10)
        refresh_button.pack(side='left', padx=5)
        
        # Export button
        export_button = ctk.CTkButton(search_frame,
                                    text="📊 Exporter",
                                    command=self.export_history,
                                    width=100,
                                    height=30,
                                    corner_radius=10)
        export_button.pack(side='left', padx=5)
        
        # Create scrollable frame for history items
        self.history_content_frame = ctk.CTkScrollableFrame(history_frame, fg_color="transparent")
        self.history_content_frame.pack(pady=10, padx=10, fill='both', expand=True)
        
        # Load actual history from database
        self.load_download_history()
        
    def clear_filters(self):
        """Réinitialise tous les filtres à leurs valeurs par défaut"""
        if hasattr(self, 'search_entry'):
            self.search_entry.delete(0, 'end')
        
        if hasattr(self, 'filter_var'):
            self.filter_var.set("Tous")
            
        if hasattr(self, 'date_filter_var'):
            self.date_filter_var.set("Toutes les dates")
            
        # Recharger l'historique sans filtres
        self.load_download_history()
    
    def change_avatar(self):
        """Permet à l'utilisateur de changer son avatar"""
        file_path = filedialog.askopenfilename(
            title="Sélectionner une image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.gif")]
        )
        
        if not file_path:
            return
            
        try:
            # Ouvrir et redimensionner l'image
            with open(file_path, "rb") as f:
                img_data = f.read()
                
            # Mettre à jour l'avatar dans la base de données
            self.users.update_one(
                {"username": self.current_user},
                {"$set": {"avatar": img_data}}
            )
            
            # Rafraîchir l'interface
            messagebox.showinfo("Succès", "Avatar mis à jour avec succès!")
            self.setup_profile_tab()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de mettre à jour l'avatar: {str(e)}")
    
    def load_download_history(self):
        # Clear existing history items
        for widget in self.history_content_frame.winfo_children():
            widget.destroy()
        
        # Get filter and search criteria
        filter_type = self.filter_var.get()
        search_text = self.search_entry.get() if hasattr(self, 'search_entry') else ""
        date_filter = self.date_filter_var.get() if hasattr(self, 'date_filter_var') else "Toutes les dates"
        
        # Build query
        query = {"username": self.current_user}
        
        # Add type filter if not "All"
        if filter_type != "Tous":
            query["type"] = filter_type
        
        # Add date filter
        if date_filter != "Toutes les dates":
            now = datetime.now()
            if date_filter == "Aujourd'hui":
                start_date = datetime(now.year, now.month, now.day)
                query["timestamp"] = {"$gte": start_date}
            elif date_filter == "Cette semaine":
                start_date = now - timedelta(days=now.weekday())
                start_date = datetime(start_date.year, start_date.month, start_date.day)
                query["timestamp"] = {"$gte": start_date}
            elif date_filter == "Ce mois":
                start_date = datetime(now.year, now.month, 1)
                query["timestamp"] = {"$gte": start_date}
            elif date_filter == "Cette année":
                start_date = datetime(now.year, 1, 1)
                query["timestamp"] = {"$gte": start_date}
        
        # Add search text if provided
        if search_text:
            query["$or"] = [
                {"title": {"$regex": search_text, "$options": "i"}},
                {"channel": {"$regex": search_text, "$options": "i"}}
            ]
            
    def load_profile_history(self):
        # Clear existing history items
        for widget in self.profile_history_frame.winfo_children():
            widget.destroy()
        
        # Get filter and search criteria
        filter_type = self.profile_filter_var.get()
        search_text = self.profile_search_entry.get() if hasattr(self, 'profile_search_entry') else ""
        date_filter = self.profile_date_filter_var.get() if hasattr(self, 'profile_date_filter_var') else "Toutes les dates"
        
        # Build query
        query = {"username": self.current_user}
        
        # Add type filter if not "All"
        if filter_type != "Tous":
            query["type"] = filter_type
        
        # Add date filter
        if date_filter != "Toutes les dates":
            now = datetime.now()
            if date_filter == "Aujourd'hui":
                start_date = datetime(now.year, now.month, now.day)
                query["timestamp"] = {"$gte": start_date}
            elif date_filter == "Cette semaine":
                start_date = now - timedelta(days=now.weekday())
                start_date = datetime(start_date.year, start_date.month, start_date.day)
                query["timestamp"] = {"$gte": start_date}
            elif date_filter == "Ce mois":
                start_date = datetime(now.year, now.month, 1)
                query["timestamp"] = {"$gte": start_date}
            elif date_filter == "Cette année":
                start_date = datetime(now.year, 1, 1)
                query["timestamp"] = {"$gte": start_date}
        
        # Add search text if provided
        if search_text:
            query["$or"] = [
                {"title": {"$regex": search_text, "$options": "i"}},
                {"channel": {"$regex": search_text, "$options": "i"}}
            ]
        
        # Get downloads from database
        downloads = list(self.db['downloads'].find(query).sort("timestamp", -1))
        
        # Display message if no downloads found
        if not downloads:
            no_data_label = ctk.CTkLabel(self.profile_history_frame, 
                                       text="Aucun téléchargement trouvé",
                                       font=("Helvetica", 14))
            no_data_label.pack(pady=20)
            return
        
        # Display downloads
        for item in downloads:
            item_frame = ctk.CTkFrame(self.profile_history_frame, corner_radius=10)
            item_frame.pack(pady=10, padx=5, fill='x')
            
            # Créer le cadre gauche pour la miniature
            left_frame = ctk.CTkFrame(item_frame, corner_radius=10)
            left_frame.pack(side='left', padx=5, pady=5)
            
            # Charger et afficher la miniature
            try:
                # Vérifier si la miniature est stockée dans la base de données
                if 'thumbnail' in item and item['thumbnail']:
                    img = Image.open(BytesIO(item['thumbnail']))
                    img = img.resize((120, 90), Image.Resampling.LANCZOS)
                    photo = ctk.CTkImage(light_image=img, dark_image=img, size=(120, 90))
                    thumbnail_label = ctk.CTkLabel(left_frame, image=photo, text="")
                    thumbnail_label.image = photo
                    thumbnail_label.pack()
                # Sinon, essayer de la récupérer depuis l'URL
                elif 'thumbnail_url' in item and item['thumbnail_url']:
                    response = requests.get(item['thumbnail_url'])
                    img = Image.open(BytesIO(response.content))
                    img = img.resize((120, 90), Image.Resampling.LANCZOS)
                    photo = ctk.CTkImage(light_image=img, dark_image=img, size=(120, 90))
                    thumbnail_label = ctk.CTkLabel(left_frame, image=photo, text="")
                    thumbnail_label.image = photo
                    thumbnail_label.pack()
                else:
                    raise Exception("No thumbnail available")
            except Exception as e:
                # Si le chargement de la miniature échoue, afficher un espace réservé
                ctk.CTkLabel(left_frame, text="🎥 Pas de miniature", width=120, height=90).pack()
            
            # Créer le cadre droit pour les informations et les boutons
            right_frame = ctk.CTkFrame(item_frame, corner_radius=10)
            right_frame.pack(side='left', fill='both', expand=True, padx=5, pady=5)
            
            # Étiquettes d'information avec icônes
            info_frame = ctk.CTkFrame(right_frame)
            info_frame.pack(fill='x', padx=5, pady=5)
            
            ctk.CTkLabel(info_frame, text=f"📝 Titre: {item['title']}", 
                        font=("Helvetica", 12, "bold")).pack(anchor='w', pady=2)
            
            # Afficher le canal si disponible
            if 'channel' in item and item['channel']:
                ctk.CTkLabel(info_frame, text=f"👤 Canal: {item['channel']}").pack(anchor='w', pady=2)
            
            type_icon = "🎬" if item['type'] == 'video' else "🎵" if item['type'] == 'audio' else "📄"
            ctk.CTkLabel(info_frame, text=f"{type_icon} Type: {item['type'].capitalize()}").pack(anchor='w', pady=2)
            
            format_icon = "📁" if item.get('format') else "❌"
            ctk.CTkLabel(info_frame, text=f"{format_icon} Format: {item.get('format', 'N/A')}").pack(anchor='w', pady=2)
            
            if item['type'] == 'video':
                quality_icon = "📊" if item.get('quality') else "❌"
                ctk.CTkLabel(info_frame, text=f"{quality_icon} Qualité: {item.get('quality', 'N/A')}").pack(anchor='w', pady=2)
            
            # Afficher la taille du fichier
            size_icon = "💾"
            file_size = item.get('file_size', 0)
            if file_size > 0:
                size_mb = file_size / 1024 / 1024
                ctk.CTkLabel(info_frame, text=f"{size_icon} Taille: {size_mb:.2f} MB").pack(anchor='w', pady=2)
            else:
                ctk.CTkLabel(info_frame, text=f"{size_icon} Taille: N/A").pack(anchor='w', pady=2)
            
            time_icon = "⏰"
            ctk.CTkLabel(info_frame, text=f"{time_icon} Téléchargé le: {item['timestamp'].strftime('%d/%m/%Y %H:%M:%S')}").pack(anchor='w', pady=2)
            
            # Créer le cadre des boutons
            button_frame = ctk.CTkFrame(right_frame)
            button_frame.pack(anchor='w', pady=(5,0))
            
            # Bouton pour ouvrir dans YouTube
            if 'url' in item and item['url']:
                ctk.CTkButton(
                    button_frame,
                    text="▶️ Ouvrir dans YouTube",
                    command=lambda url=item['url']: self.open_youtube(url),
                    width=150,
                    corner_radius=8
                ).pack(side='left', padx=5)
            
            # Bouton pour ouvrir le fichier local (uniquement si le fichier existe)
            file_path = os.path.join(
                self.video_path if item['type'] == 'video' else self.audio_path,
                item.get('file_path', '')
            )
            if os.path.exists(file_path):
                ctk.CTkButton(
                    button_frame,
                    text="📂 Ouvrir le fichier",
                    command=lambda path=file_path: self.open_local_file(path),
                    width=150,
                    corner_radius=8
                ).pack(side='left', padx=5)
        
        # Mettre à jour les statistiques du profil
        self.update_profile_stats()
    
    def clear_profile_filters(self):
        """Réinitialise tous les filtres du profil à leurs valeurs par défaut"""
        if hasattr(self, 'profile_search_entry'):
            self.profile_search_entry.delete(0, 'end')
        
        if hasattr(self, 'profile_filter_var'):
            self.profile_filter_var.set("Tous")
            
        if hasattr(self, 'profile_date_filter_var'):
            self.profile_date_filter_var.set("Toutes les dates")
            
        # Recharger l'historique sans filtres
        self.load_profile_history()
    
    def update_profile_stats(self):
        """Met à jour les statistiques affichées dans le profil"""
        # Récupérer les statistiques de téléchargement
        total_downloads = self.db['downloads'].count_documents({"username": self.current_user})
        video_downloads = self.db['downloads'].count_documents({"username": self.current_user, "type": "Vidéo"})
        audio_downloads = self.db['downloads'].count_documents({"username": self.current_user, "type": "Audio"})
        
        # Calculer l'espace disque utilisé
        storage_used = 0
        downloads = list(self.db['downloads'].find({"username": self.current_user}))
        for download in downloads:
            storage_used += download.get('file_size', 0)
        
        # Convertir en MB
        storage_used_mb = round(storage_used / (1024 * 1024), 2) if storage_used > 0 else 0
        
        # Mettre à jour les labels
        if hasattr(self, 'profile_total_downloads_label'):
            self.profile_total_downloads_label.configure(text=str(total_downloads))
        
        if hasattr(self, 'profile_video_downloads_label'):
            self.profile_video_downloads_label.configure(text=str(video_downloads))
        
        if hasattr(self, 'profile_audio_downloads_label'):
            self.profile_audio_downloads_label.configure(text=str(audio_downloads))
        
        if hasattr(self, 'profile_storage_usage_label'):
            self.profile_storage_usage_label.configure(text=f"{storage_used_mb} MB")
    
    def edit_profile_info(self):
        """Ouvre une fenêtre pour modifier le nom d'utilisateur et/ou l'email"""
        edit_window = ctk.CTkToplevel(self)
        edit_window.title("Modifier le profil")
        edit_window.geometry("500x300")
        edit_window.grab_set()  # Rendre la fenêtre modale
        
        # Récupérer les informations actuelles de l'utilisateur
        user = self.users.find_one({"username": self.current_user})
        current_username = self.current_user
        current_email = user.get('email', '')
        
        # Conteneur principal
        main_frame = ctk.CTkFrame(edit_window, fg_color="transparent")
        main_frame.pack(pady=20, padx=20, fill='both', expand=True)
        
        # Titre
        ctk.CTkLabel(main_frame, text="Modifier vos informations", font=("Helvetica", 16, "bold")).pack(pady=10)
        
        # Champ pour le nom d'utilisateur
        username_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        username_frame.pack(pady=10, fill='x')
        ctk.CTkLabel(username_frame, text="Nom d'utilisateur:", width=120).pack(side='left')
        self.edit_username_entry = ctk.CTkEntry(username_frame, width=250)
        self.edit_username_entry.pack(side='left', padx=10)
        self.edit_username_entry.insert(0, current_username)
        
        # Champ pour l'email
        email_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        email_frame.pack(pady=10, fill='x')
        ctk.CTkLabel(email_frame, text="Email:", width=120).pack(side='left')
        self.edit_email_entry = ctk.CTkEntry(email_frame, width=250)
        self.edit_email_entry.pack(side='left', padx=10)
        self.edit_email_entry.insert(0, current_email)
        
        # Boutons d'action
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.pack(pady=20)
        
        # Bouton d'annulation
        cancel_button = ctk.CTkButton(buttons_frame,
                                    text="Annuler",
                                    command=edit_window.destroy,
                                    width=100,
                                    height=35,
                                    corner_radius=10)
        cancel_button.pack(side='left', padx=10)
        
        # Bouton de sauvegarde
        save_button = ctk.CTkButton(buttons_frame,
                                  text="Enregistrer",
                                  command=lambda: self.save_profile_changes(edit_window),
                                  width=100,
                                  height=35,
                                  corner_radius=10)
        save_button.pack(side='left', padx=10)
    
    def save_profile_changes(self, window):
        """Enregistre les modifications du profil"""
        new_username = self.edit_username_entry.get()
        new_email = self.edit_email_entry.get()
        
        # Validation des entrées
        if not new_username or not new_email:
            messagebox.showerror("Erreur", "Tous les champs sont obligatoires")
            return
        
        # Validation de l'email avec une expression régulière simple
        import re
        email_pattern = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
        if not email_pattern.match(new_email):
            messagebox.showerror("Erreur", "Format d'email invalide")
            return
        
        # Vérifier si le nom d'utilisateur a changé et s'il est unique
        if new_username != self.current_user:
            if self.users.find_one({"username": new_username}):
                messagebox.showerror("Erreur", "Ce nom d'utilisateur existe déjà")
                return
        
        # Vérifier si l'email a changé et s'il est unique
        user = self.users.find_one({"username": self.current_user})
        if new_email != user.get('email') and self.users.find_one({"email": new_email}):
            messagebox.showerror("Erreur", "Cet email est déjà utilisé")
            return
        
        # Mettre à jour les informations dans la base de données
        update_data = {}
        if new_username != self.current_user:
            update_data["username"] = new_username
        if new_email != user.get('email'):
            update_data["email"] = new_email
        
        if update_data:
            self.users.update_one({"_id": user["_id"]}, {"$set": update_data})
            
            # Mettre à jour le nom d'utilisateur actuel si nécessaire
            if "username" in update_data:
                old_username = self.current_user
                self.current_user = new_username
                
                # Mettre à jour les téléchargements associés à cet utilisateur
                self.db['downloads'].update_many(
                    {"username": old_username},
                    {"$set": {"username": new_username}}
                )
                
                # Mettre à jour l'affichage du nom d'utilisateur
                if hasattr(self, 'username_label'):
                    self.username_label.configure(text=new_username)
            
            # Mettre à jour l'affichage de l'email si nécessaire
            if "email" in update_data and hasattr(self, 'email_label'):
                self.email_label.configure(text=new_email)
            
            messagebox.showinfo("Succès", "Profil mis à jour avec succès")
            window.destroy()
        else:
            messagebox.showinfo("Information", "Aucune modification détectée")
            window.destroy()
    
    def change_password(self):
        """Change le mot de passe de l'utilisateur"""
        old_password = self.old_password_entry.get()
        new_password = self.new_password_entry.get()
        confirm_password = self.confirm_password_entry.get()
        
        # Validation des entrées
        if not old_password or not new_password or not confirm_password:
            messagebox.showerror("Erreur", "Tous les champs sont obligatoires")
            return
        
        if new_password != confirm_password:
            messagebox.showerror("Erreur", "Les nouveaux mots de passe ne correspondent pas")
            return
        
        if len(new_password) < 8:
            messagebox.showerror("Erreur", "Le nouveau mot de passe doit contenir au moins 8 caractères")
            return
        
        # Vérifier l'ancien mot de passe
        user = self.users.find_one({"username": self.current_user})
        if not user or not bcrypt.checkpw(old_password.encode('utf-8'), user['password']):
            messagebox.showerror("Erreur", "Ancien mot de passe incorrect")
            return
        
        # Hacher et enregistrer le nouveau mot de passe
        hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        self.users.update_one({"_id": user["_id"]}, {"$set": {"password": hashed}})
        
        # Effacer les champs
        self.old_password_entry.delete(0, 'end')
        self.new_password_entry.delete(0, 'end')
        self.confirm_password_entry.delete(0, 'end')
        
        messagebox.showinfo("Succès", "Mot de passe modifié avec succès")
    
    def logout(self):
        """Déconnecte l'utilisateur et retourne à l'écran de connexion"""
        confirm = messagebox.askyesno("Confirmation", "Voulez-vous vraiment vous déconnecter?")
        if confirm:
            # Supprimer la session si elle existe
            session_file = os.path.join(os.getcwd(), ".session")
            if os.path.exists(session_file):
                os.remove(session_file)
            
            # Réinitialiser l'utilisateur actuel
            self.current_user = None
            
            # Fermer tous les onglets et revenir à l'écran de connexion
            if hasattr(self, 'tabview'):
                self.tabview.pack_forget()
            
            # Afficher l'écran de connexion
            self.setup_login_ui()
    
    def delete_account(self):
        """Supprime le compte de l'utilisateur"""
        confirm = messagebox.askyesno("Confirmation", "Voulez-vous vraiment supprimer votre compte? Cette action est irréversible.")
        if confirm:
            # Demander une confirmation supplémentaire avec le mot de passe
            password_dialog = ctk.CTkInputDialog(title="Confirmation", text="Entrez votre mot de passe pour confirmer la suppression:")
            password = password_dialog.get_input()
            
            if not password:
                return
            
            # Vérifier le mot de passe
            user = self.users.find_one({"username": self.current_user})
            if not user or not bcrypt.checkpw(password.encode('utf-8'), user['password']):
                messagebox.showerror("Erreur", "Mot de passe incorrect")
                return
            
            # Supprimer les téléchargements associés à cet utilisateur
            downloads = list(self.db['downloads'].find({"username": self.current_user}))
            for download in downloads:
                file_path = download.get('file_path')
                if file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        print(f"Erreur lors de la suppression du fichier {file_path}: {e}")
            
            self.db['downloads'].delete_many({"username": self.current_user})
            
            # Supprimer l'utilisateur
            self.users.delete_one({"_id": user["_id"]})
            
            # Supprimer la session si elle existe
            session_file = os.path.join(os.getcwd(), ".session")
            if os.path.exists(session_file):
                os.remove(session_file)
            
            messagebox.showinfo("Succès", "Votre compte a été supprimé avec succès")
            
            # Réinitialiser l'utilisateur actuel
            self.current_user = None
            
            # Fermer tous les onglets et revenir à l'écran de connexion
            if hasattr(self, 'tabview'):
                self.tabview.pack_forget()
            
            # Afficher l'écran de connexion
            self.setup_login_ui()
            
    def load_download_history(self):
        # Clear existing history items
        for widget in self.history_content_frame.winfo_children():
            widget.destroy()
        
        # Get filter and search criteria
        filter_type = self.filter_var.get()
        search_text = self.search_entry.get() if hasattr(self, 'search_entry') else ""
        date_filter = self.date_filter_var.get() if hasattr(self, 'date_filter_var') else "Toutes les dates"
        
        # Build query
        query = {"username": self.current_user}
        
        # Add type filter if not "All"
        if filter_type != "Tous":
            query["type"] = filter_type
        
        # Add date filter
        if date_filter != "Toutes les dates":
            now = datetime.now()
            if date_filter == "Aujourd'hui":
                start_date = datetime(now.year, now.month, now.day)
                query["timestamp"] = {"$gte": start_date}
            elif date_filter == "Cette semaine":
                start_date = now - timedelta(days=now.weekday())
                start_date = datetime(start_date.year, start_date.month, start_date.day)
                query["timestamp"] = {"$gte": start_date}
            elif date_filter == "Ce mois":
                start_date = datetime(now.year, now.month, 1)
                query["timestamp"] = {"$gte": start_date}
            elif date_filter == "Cette année":
                start_date = datetime(now.year, 1, 1)
                query["timestamp"] = {"$gte": start_date}
        
        # Add search text if provided
        if search_text:
            query["$or"] = [
                {"title": {"$regex": search_text, "$options": "i"}},
                {"channel": {"$regex": search_text, "$options": "i"}}
            ]
        
        # Get downloads from database
        downloads = list(self.db['downloads'].find(query).sort("timestamp", -1))
        
        # Update stats
        self.update_dashboard_stats()
        
        # Display message if no downloads found
        if not downloads:
            no_data_label = ctk.CTkLabel(self.history_content_frame, 
                                       text="Aucun téléchargement trouvé",
                                       font=("Helvetica", 14))
            no_data_label.pack(pady=20)
            return
        
        # Display each download
        for download in downloads:
            # Create history item frame
            history_item = ctk.CTkFrame(self.history_content_frame, corner_radius=10)
            history_item.pack(pady=5, fill='x', padx=5)
            
            # Create layout with thumbnail and info
            item_layout = ctk.CTkFrame(history_item, fg_color="transparent")
            item_layout.pack(pady=10, padx=10, fill='x')
            
            # Thumbnail section
            thumbnail_frame = ctk.CTkFrame(item_layout, width=120, height=68, corner_radius=5)
            thumbnail_frame.pack(side='left', padx=10)
            thumbnail_frame.pack_propagate(False)  # Fix the size
            
            # Charger et afficher la miniature
            if download.get('thumbnail'):
                try:
                    # Convert binary data to image
                    img = Image.open(BytesIO(download['thumbnail']))
                    img = img.resize((120, 68), Image.LANCZOS)
                    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(120, 68))
                    thumbnail_label = ctk.CTkLabel(thumbnail_frame, image=ctk_img, text="")
                    thumbnail_label.image = ctk_img  # Keep a reference
                    thumbnail_label.pack(fill='both', expand=True)
                    
                    # Ajouter un effet de survol pour agrandir l'image
                    def on_enter(e, img=img):
                        popup = ctk.CTkToplevel(self)
                        popup.title("Aperçu")
                        popup.geometry("400x300")
                        popup.attributes('-topmost', True)
                        img_large = img.resize((350, 200), Image.LANCZOS)
                        ctk_img_large = ctk.CTkImage(light_image=img_large, dark_image=img_large, size=(350, 200))
                        label = ctk.CTkLabel(popup, image=ctk_img_large, text="")
                        label.image = ctk_img_large
                        label.pack(pady=20)
                        
                    thumbnail_label.bind("<Enter>", on_enter)
                except Exception as e:
                    ctk.CTkLabel(thumbnail_frame, text="🎬", font=("Helvetica", 24)).pack(pady=15)
            else:
                ctk.CTkLabel(thumbnail_frame, text="🎬", font=("Helvetica", 24)).pack(pady=15)
            
            # Video info section
            info_frame = ctk.CTkFrame(item_layout, fg_color="transparent")
            info_frame.pack(side='left', padx=10, fill='both', expand=True)
            
            # Title with truncation if too long
            title = download.get('title', 'Sans titre')
            if len(title) > 50:
                title = title[:47] + "..."
            
            title_label = ctk.CTkLabel(info_frame, 
                                      text=title,
                                      font=("Helvetica", 14, "bold"),
                                      anchor="w")
            title_label.pack(anchor='w')
            
            # Format details
            format_text = f"Type: {download.get('type', 'Inconnu')} | "
            format_text += f"Format: {download.get('format', 'Inconnu')} | "
            format_text += f"Qualité: {download.get('quality', 'Inconnu')}"
            
            format_label = ctk.CTkLabel(info_frame, text=format_text, anchor="w")
            format_label.pack(anchor='w')
            
            # Size and date
            size_text = f"Taille: {self.format_size(download.get('file_size', 0))} | "
            timestamp = download.get('timestamp', datetime.now())
            date_str = timestamp.strftime("%d/%m/%Y %H:%M")
            size_text += f"Date: {date_str}"
            
            size_label = ctk.CTkLabel(info_frame, text=size_text, anchor="w")
            size_label.pack(anchor='w')
            
            # Action buttons
            buttons_frame = ctk.CTkFrame(item_layout, fg_color="transparent")
            buttons_frame.pack(side='right', padx=10)
            
            # YouTube button
            if download.get('url'):
                youtube_button = ctk.CTkButton(buttons_frame,
                                             text="YouTube",
                                             command=lambda url=download.get('url'): webbrowser.open(url),
                                             width=100,
                                             height=30,
                                             corner_radius=10)
                youtube_button.pack(side='top', padx=5, pady=2)
            
            # Open file button
            file_path = download.get('file_path')
            if file_path and os.path.exists(file_path):
                open_button = ctk.CTkButton(buttons_frame,
                                          text="Ouvrir fichier",
                                          command=lambda path=file_path: self.open_file(path),
                                          width=100,
                                          height=30,
                                          corner_radius=10)
                open_button.pack(side='top', padx=5, pady=2)
            
            # Delete button
            delete_button = ctk.CTkButton(buttons_frame,
                                        text="Supprimer",
                                        command=lambda id=download.get('_id'): self.delete_download(id),
                                        width=100,
                                        height=30,
                                        fg_color="#FF5555",
                                        hover_color="#FF0000",
                                        corner_radius=10)
            delete_button.pack(side='top', padx=5, pady=2)
            
            # Detail button
            detail_button = ctk.CTkButton(buttons_frame,
                                       text="Détail",
                                       command=lambda dl=download: self.show_video_details(dl),
                                       width=100,
                                       height=30,
                                       corner_radius=10)
            detail_button.pack(side='top', padx=5, pady=2)
            delete_button.pack(side='top', padx=5, pady=2)
    
    def show_video_details(self, download):
        # Créer une nouvelle fenêtre pour afficher les détails
        details_window = ctk.CTkToplevel(self)
        details_window.title("Détails de la vidéo")
        details_window.geometry("800x600")
        details_window.grab_set()  # Rendre la fenêtre modale
        
        # Conteneur principal
        main_frame = ctk.CTkScrollableFrame(details_window)
        main_frame.pack(pady=20, padx=20, fill='both', expand=True)
        
        # En-tête avec miniature et titre
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(pady=10, fill='x')
        
        # Miniature
        thumbnail_frame = ctk.CTkFrame(header_frame, width=200, height=120, corner_radius=5)
        thumbnail_frame.pack(side='left', padx=10)
        thumbnail_frame.pack_propagate(False)  # Fixer la taille
        
        if download.get('thumbnail'):
            try:
                img = Image.open(BytesIO(download['thumbnail']))
                img = img.resize((200, 120), Image.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(200, 120))
                thumbnail_label = ctk.CTkLabel(thumbnail_frame, image=ctk_img, text="")
                thumbnail_label.image = ctk_img
                thumbnail_label.pack(fill='both', expand=True)
            except Exception as e:
                ctk.CTkLabel(thumbnail_frame, text="🎬", font=("Helvetica", 36)).pack(pady=30)
        else:
            ctk.CTkLabel(thumbnail_frame, text="🎬", font=("Helvetica", 36)).pack(pady=30)
        
        # Titre et informations de base
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(side='left', padx=10, fill='both', expand=True)
        
        title = download.get('title', 'Sans titre')
        ctk.CTkLabel(title_frame, text=title, font=("Helvetica", 18, "bold"), anchor="w").pack(anchor='w')
        
        # Boutons d'action
        buttons_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        buttons_frame.pack(side='right', padx=10)
        
        # YouTube button
        if download.get('url'):
            youtube_button = ctk.CTkButton(buttons_frame,
                                         text="YouTube",
                                         command=lambda url=download.get('url'): webbrowser.open(url),
                                         width=100,
                                         height=30,
                                         corner_radius=10)
            youtube_button.pack(side='top', padx=5, pady=2)
        
        # Open file button
        file_path = download.get('file_path')
        if file_path and os.path.exists(file_path):
            open_button = ctk.CTkButton(buttons_frame,
                                      text="Ouvrir fichier",
                                      command=lambda path=file_path: self.open_file(path),
                                      width=100,
                                      height=30,
                                      corner_radius=10)
            open_button.pack(side='top', padx=5, pady=2)
        
        # Delete button
        delete_button = ctk.CTkButton(buttons_frame,
                                    text="Supprimer",
                                    command=lambda id=download.get('_id'): [self.delete_download(id), details_window.destroy()],
                                    width=100,
                                    height=30,
                                    fg_color="#FF5555",
                                    hover_color="#FF0000",
                                    corner_radius=10)
        delete_button.pack(side='top', padx=5, pady=2)
        
        # Informations détaillées
        details_frame = ctk.CTkFrame(main_frame)
        details_frame.pack(pady=10, fill='x')
        
        # Titre de la section
        ctk.CTkLabel(details_frame, text="Informations détaillées", font=("Helvetica", 16, "bold")).pack(pady=10, padx=10, anchor='w')
        
        # Grille d'informations
        info_grid = ctk.CTkFrame(details_frame, fg_color="transparent")
        info_grid.pack(pady=10, padx=20, fill='x')
        
        # Fonction pour ajouter une ligne d'information
        def add_info_row(label_text, value_text, row):
            ctk.CTkLabel(info_grid, text=label_text, font=("Helvetica", 14, "bold"), anchor="w").grid(row=row, column=0, sticky="w", padx=5, pady=5)
            ctk.CTkLabel(info_grid, text=value_text, font=("Helvetica", 14), anchor="w").grid(row=row, column=1, sticky="w", padx=5, pady=5)
        
        # Ajouter les informations disponibles
        row = 0
        
        # Type et format
        add_info_row("Type:", download.get('type', 'Inconnu'), row)
        row += 1
        
        add_info_row("Format:", download.get('format', 'Inconnu'), row)
        row += 1
        
        add_info_row("Qualité:", download.get('quality', 'Inconnu'), row)
        row += 1
        
        # Taille du fichier
        add_info_row("Taille:", self.format_size(download.get('file_size', 0)), row)
        row += 1
        
        # Date de téléchargement
        timestamp = download.get('timestamp', datetime.now())
        date_str = timestamp.strftime("%d/%m/%Y %H:%M")
        add_info_row("Date de téléchargement:", date_str, row)
        row += 1
        
        # Chemin du fichier
        if file_path:
            add_info_row("Emplacement:", file_path, row)
            row += 1
        
        # URL
        if download.get('url'):
            add_info_row("URL:", download.get('url'), row)
            row += 1
        
        # Informations supplémentaires de la vidéo si disponibles
        if download.get('video_info'):
            video_info = download.get('video_info', {})
            
            # Durée
            if video_info.get('duration'):
                duration = video_info.get('duration')
                # Convertir en format lisible si c'est un nombre de secondes
                if isinstance(duration, (int, float)):
                    minutes, seconds = divmod(int(duration), 60)
                    hours, minutes = divmod(minutes, 60)
                    duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes:02d}:{seconds:02d}"
                else:
                    duration_str = str(duration)
                add_info_row("Durée:", duration_str, row)
                row += 1
            
            # Vues
            if video_info.get('view_count'):
                add_info_row("Vues:", f"{video_info.get('view_count'):,}", row)
                row += 1
            
            # Likes
            if video_info.get('like_count'):
                add_info_row("Likes:", f"{video_info.get('like_count'):,}", row)
                row += 1
            
            # Dislikes si disponible
            if video_info.get('dislike_count'):
                add_info_row("Dislikes:", f"{video_info.get('dislike_count'):,}", row)
                row += 1
            
            # Chaîne
            if video_info.get('channel'):
                add_info_row("Chaîne:", video_info.get('channel'), row)
                row += 1
            
            # Abonnés
            if video_info.get('channel_follower_count'):
                add_info_row("Abonnés:", f"{video_info.get('channel_follower_count'):,}", row)
                row += 1
            
            # Nombre de commentaires
            if video_info.get('comment_count'):
                add_info_row("Commentaires:", f"{video_info.get('comment_count'):,}", row)
                row += 1
        
        # Description si disponible
        if download.get('description') or (download.get('video_info') and download.get('video_info').get('description')):
            description = download.get('description') or download.get('video_info', {}).get('description', '')
            
            description_frame = ctk.CTkFrame(main_frame)
            description_frame.pack(pady=10, fill='x')
            
            ctk.CTkLabel(description_frame, text="Description", font=("Helvetica", 16, "bold")).pack(pady=10, padx=10, anchor='w')
            
            description_text = ctk.CTkTextbox(description_frame, height=150, wrap="word")
            description_text.pack(pady=10, padx=20, fill='x')
            description_text.insert("1.0", description)
            description_text.configure(state="disabled")  # Rendre en lecture seule
    
    def update_dashboard_stats(self):
        # Get stats from database
        total_count = self.db['downloads'].count_documents({"username": self.current_user})
        video_count = self.db['downloads'].count_documents({"username": self.current_user, "type": "Vidéo"})
        audio_count = self.db['downloads'].count_documents({"username": self.current_user, "type": "Audio"})
        
        # Calculate total storage used
        pipeline = [
            {"$match": {"username": self.current_user}},
            {"$group": {"_id": None, "total_size": {"$sum": "$file_size"}}}
        ]
        result = list(self.db['downloads'].aggregate(pipeline))
        total_size = result[0]["total_size"] if result else 0
        
        # Update labels
        self.total_downloads_label.configure(text=str(total_count))
        self.video_downloads_label.configure(text=str(video_count))
        self.audio_downloads_label.configure(text=str(audio_count))
        self.storage_usage_label.configure(text=self.format_size(total_size))
        
        # Update graphs if we have matplotlib
        try:
            self.update_type_graph(video_count, audio_count)
            self.update_time_graph()
        except Exception as e:
            print(f"Erreur lors de la mise à jour des graphiques: {e}")
    
    def update_type_graph(self, video_count, audio_count):
        # Clear previous graph
        for widget in self.type_graph_frame.winfo_children():
            if widget.winfo_class() != "CTkLabel":
                widget.destroy()
        
        if video_count == 0 and audio_count == 0:
            return
        
        # Create pie chart
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        
        fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
        labels = ['Vidéo', 'Audio']
        sizes = [video_count, audio_count]
        colors = ['#3498db', '#2ecc71']
        
        ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
        
        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.type_graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
    
    def update_time_graph(self):
        # Clear previous graph
        for widget in self.time_graph_frame.winfo_children():
            if widget.winfo_class() != "CTkLabel":
                widget.destroy()
        
        # Get download history for the last 7 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        pipeline = [
            {"$match": {
                "username": self.current_user,
                "timestamp": {"$gte": start_date, "$lte": end_date}
            }},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]
        
        result = list(self.db['downloads'].aggregate(pipeline))
        
        if not result:
            return
        
        # Create date range for all 7 days
        date_range = [(end_date - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7, -1, -1)]
        counts = [0] * len(date_range)
        
        # Fill in actual counts
        for item in result:
            if item["_id"] in date_range:
                idx = date_range.index(item["_id"])
                counts[idx] = item["count"]
        
        # Format dates for display
        display_dates = [(end_date - timedelta(days=i)).strftime("%d/%m") for i in range(7, -1, -1)]
        
        # Create bar chart
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        
        fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
        ax.bar(display_dates, counts, color='#3498db')
        ax.set_ylabel('Téléchargements')
        ax.set_title('Activité des 7 derniers jours')
        
        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.time_graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
    
    def export_history(self):
        # Ask for export format
        export_format = ctk.CTkInputDialog(title="Exporter l'historique", 
                                         text="Choisissez le format d'export (pdf/csv):").get_input()
        
        if not export_format:
            return
        
        export_format = export_format.lower()
        
        if export_format not in ["pdf", "csv"]:
            messagebox.showerror("Erreur", "Format non supporté. Utilisez 'pdf' ou 'csv'.")
            return
        
        # Ask for save location
        file_path = filedialog.asksaveasfilename(
            defaultextension=f".{export_format}",
            filetypes=[("PDF files", "*.pdf"), ("CSV files", "*.csv")]
        )
        
        if not file_path:
            return
        
        # Get download history
        downloads = list(self.db['downloads'].find({"username": self.current_user}).sort("timestamp", -1))
        
        if not downloads:
            messagebox.showinfo("Information", "Aucun téléchargement à exporter.")
            return
        
        try:
            if export_format == "pdf":
                self.export_to_pdf(file_path, downloads)
            else:  # csv
                self.export_to_csv(file_path, downloads)
                
            messagebox.showinfo("Succès", f"Historique exporté avec succès vers {file_path}")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'export: {str(e)}")
    
    def export_to_pdf(self, file_path, downloads):
        doc = SimpleDocTemplate(file_path, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []
        
        # Title
        title_style = styles["Title"]
        elements.append(Paragraph("Historique des téléchargements YouTube", title_style))
        elements.append(Spacer(1, 0.5*inch))
        
        # User info
        user_style = styles["Heading2"]
        elements.append(Paragraph(f"Utilisateur: {self.current_user}", user_style))
        elements.append(Paragraph(f"Date d'export: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles["Normal"]))
        elements.append(Spacer(1, 0.5*inch))
        
        # Table data
        data = [["Titre", "Type", "Format", "Qualité", "Taille", "Date"]]
        
        for download in downloads:
            title = download.get('title', 'Sans titre')
            if len(title) > 30:  # Truncate long titles
                title = title[:27] + "..."
                
            row = [
                title,
                download.get('type', 'Inconnu'),
                download.get('format', 'Inconnu'),
                download.get('quality', 'Inconnu'),
                self.format_size(download.get('file_size', 0)),
                download.get('timestamp', datetime.now()).strftime("%d/%m/%Y")
            ]
            data.append(row)
        
        # Create table
        table = Table(data, colWidths=[2.5*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch])
        
        # Style the table
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ])
        
        # Add zebra striping
        for i in range(1, len(data)):
            if i % 2 == 0:
                table_style.add('BACKGROUND', (0, i), (-1, i), colors.lightgrey)
        
        table.setStyle(table_style)
        elements.append(table)
        
        # Build the PDF
        doc.build(elements)
    
    def export_to_csv(self, file_path, downloads):
        # Prepare data for CSV
        data = []
        for download in downloads:
            data.append({
                "Titre": download.get('title', 'Sans titre'),
                "Type": download.get('type', 'Inconnu'),
                "Format": download.get('format', 'Inconnu'),
                "Qualité": download.get('quality', 'Inconnu'),
                "Taille": self.format_size(download.get('file_size', 0)),
                "URL": download.get('url', ''),
                "Date": download.get('timestamp', datetime.now()).strftime("%d/%m/%Y %H:%M")
            })
        
        # Create DataFrame and export
        df = pd.DataFrame(data)
        df.to_csv(file_path, index=False, encoding='utf-8-sig')  # utf-8-sig for Excel compatibility
    
    def open_file(self, file_path):
        """Ouvre le fichier avec l'application par défaut"""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(file_path)
            elif os.name == 'posix':  # macOS, Linux
                subprocess.call(('xdg-open', file_path))
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le fichier: {str(e)}")
    
    def delete_download(self, download_id):
        """Supprime un téléchargement de l'historique"""
        confirm = messagebox.askyesno("Confirmation", "Voulez-vous vraiment supprimer ce téléchargement de l'historique?")
        if not confirm:
            return
    
    def paste_url(self):
        """Colle le contenu du presse-papiers dans le champ d'entrée URL"""
        try:
            # Récupérer le contenu du presse-papiers
            clipboard_content = self.clipboard_get()
            # Effacer le contenu actuel du champ d'entrée
            self.url_entry.delete(0, 'end')
            # Insérer le contenu du presse-papiers
            self.url_entry.insert(0, clipboard_content)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de coller depuis le presse-papiers: {str(e)}")
    
    def setup_profile_tab(self):
        # Create main container
        container = ctk.CTkFrame(self.profile_tab, fg_color="transparent")
        container.pack(pady=20, padx=20, fill='both', expand=True)
        
        # Profile info section with avatar
        profile_frame = ctk.CTkFrame(container, corner_radius=15)
        profile_frame.pack(pady=10, fill='x')
        
        profile_header = ctk.CTkFrame(profile_frame, fg_color="transparent")
        profile_header.pack(pady=10, fill='x')
        
        # Avatar section
        avatar_frame = ctk.CTkFrame(profile_header, width=100, height=100, corner_radius=50)
        avatar_frame.pack(side='left', padx=20)
        avatar_frame.pack_propagate(False)  # Fix the size
        
        # Default avatar or user avatar
        try:
            user = self.users.find_one({"username": self.current_user})
            if user and user.get('avatar'):
                img = Image.open(BytesIO(user['avatar']))
            else:
                img = Image.open("images/default_avatar.png")
                
            img = img.resize((100, 100), Image.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(100, 100))
            avatar_label = ctk.CTkLabel(avatar_frame, image=ctk_img, text="")
            avatar_label.image = ctk_img
            avatar_label.pack(fill='both', expand=True)
        except Exception as e:
            # Fallback to text avatar
            initials = self.current_user[0].upper() if self.current_user else "U"
            avatar_label = ctk.CTkLabel(avatar_frame, text=initials, font=("Helvetica", 36, "bold"))
            avatar_label.pack(fill='both', expand=True)
        
        # Change avatar button
        change_avatar_btn = ctk.CTkButton(profile_header, text="Changer l'avatar", 
                                       command=self.change_avatar,
                                       width=150, height=30)
        change_avatar_btn.pack(side='right', padx=5)
        
        # Edit profile button
        edit_profile_btn = ctk.CTkButton(profile_header, text="Modifier profil", 
                                      command=self.edit_profile_info,
                                      width=150, height=30)
        edit_profile_btn.pack(side='right', padx=5)
        
        # Profile info
        info_frame = ctk.CTkFrame(profile_header, fg_color="transparent")
        info_frame.pack(side='left', padx=10, fill='both', expand=True)
        
        ctk.CTkLabel(info_frame, text="Informations du profil", font=("Helvetica", 16, "bold")).pack(anchor='w')
        
        # Username
        username_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        username_frame.pack(pady=5, fill='x')
        
        ctk.CTkLabel(username_frame, text="👤 Nom d'utilisateur:", font=("Helvetica", 14)).pack(side='left', padx=5)
        self.username_label = ctk.CTkLabel(username_frame, text=self.current_user, font=("Helvetica", 14, "bold"))
        self.username_label.pack(side='left', padx=5)
        
        # Email
        email_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        email_frame.pack(pady=5, fill='x')
        
        # Get actual email from database
        user_email = "user@example.com"
        if user and user.get('email'):
            user_email = user['email']
            
        ctk.CTkLabel(email_frame, text="📧 Email:", font=("Helvetica", 14)).pack(side='left', padx=5)
        self.email_label = ctk.CTkLabel(email_frame, text=user_email, font=("Helvetica", 14))
        self.email_label.pack(side='left', padx=5)
        
        # Member since
        joined_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        joined_frame.pack(pady=5, fill='x')
        
        join_date = datetime.now().strftime("%d/%m/%Y")
        if user and user.get('created_at'):
            join_date = user['created_at'].strftime("%d/%m/%Y")
            
        ctk.CTkLabel(joined_frame, text="📅 Membre depuis:", font=("Helvetica", 14)).pack(side='left', padx=5)
        self.joined_label = ctk.CTkLabel(joined_frame, text=join_date, font=("Helvetica", 14))
        self.joined_label.pack(side='left', padx=5)
        
        # Résumé des téléchargements
        download_summary_frame = ctk.CTkFrame(container, corner_radius=15)
        download_summary_frame.pack(pady=10, fill='x')
        
        ctk.CTkLabel(download_summary_frame, text="Résumé des téléchargements", font=("Helvetica", 16, "bold")).pack(pady=10)
        
        # Récupérer les statistiques de téléchargement
        total_downloads = self.db['downloads'].count_documents({"username": self.current_user})
        video_downloads = self.db['downloads'].count_documents({"username": self.current_user, "type": "Vidéo"})
        audio_downloads = self.db['downloads'].count_documents({"username": self.current_user, "type": "Audio"})
        
        # Calculer l'espace disque utilisé
        storage_used = 0
        downloads = list(self.db['downloads'].find({"username": self.current_user}))
        for download in downloads:
            storage_used += download.get('file_size', 0)
        
        # Convertir en MB
        storage_used_mb = round(storage_used / (1024 * 1024), 2) if storage_used > 0 else 0
        
        # Create stats cards row
        stats_row = ctk.CTkFrame(download_summary_frame, fg_color="transparent")
        stats_row.pack(pady=10, fill='x')
        
        # Total downloads card
        total_card = ctk.CTkFrame(stats_row, corner_radius=10)
        total_card.pack(side='left', padx=10, fill='both', expand=True)
        ctk.CTkLabel(total_card, text="Total", font=("Helvetica", 14, "bold")).pack(pady=5)
        self.profile_total_downloads_label = ctk.CTkLabel(total_card, text=str(total_downloads), font=("Helvetica", 24))
        self.profile_total_downloads_label.pack(pady=5)
        
        # Video downloads card
        video_card = ctk.CTkFrame(stats_row, corner_radius=10)
        video_card.pack(side='left', padx=10, fill='both', expand=True)
        ctk.CTkLabel(video_card, text="Vidéos", font=("Helvetica", 14, "bold")).pack(pady=5)
        self.profile_video_downloads_label = ctk.CTkLabel(video_card, text=str(video_downloads), font=("Helvetica", 24))
        self.profile_video_downloads_label.pack(pady=5)
        
        # Audio downloads card
        audio_card = ctk.CTkFrame(stats_row, corner_radius=10)
        audio_card.pack(side='left', padx=10, fill='both', expand=True)
        ctk.CTkLabel(audio_card, text="Audio", font=("Helvetica", 14, "bold")).pack(pady=5)
        self.profile_audio_downloads_label = ctk.CTkLabel(audio_card, text=str(audio_downloads), font=("Helvetica", 24))
        self.profile_audio_downloads_label.pack(pady=5)
        
        # Storage usage card
        storage_card = ctk.CTkFrame(stats_row, corner_radius=10)
        storage_card.pack(side='left', padx=10, fill='both', expand=True)
        ctk.CTkLabel(storage_card, text="Espace utilisé", font=("Helvetica", 14, "bold")).pack(pady=5)
        self.profile_storage_usage_label = ctk.CTkLabel(storage_card, text=f"{storage_used_mb} MB", font=("Helvetica", 24))
        self.profile_storage_usage_label.pack(pady=5)
        


        
        # Conteneur pour les options de compte
        options_frame = ctk.CTkFrame(account_frame, fg_color="transparent")
        options_frame.pack(pady=20, padx=20, fill='both', expand=True)
        
        # Section de modification du mot de passe
        password_frame = ctk.CTkFrame(options_frame, corner_radius=10)
        password_frame.pack(pady=10, fill='x')
        
        ctk.CTkLabel(password_frame, text="Modifier le mot de passe", font=("Helvetica", 14, "bold")).pack(pady=10)
        
        # Champs pour le mot de passe
        password_fields = ctk.CTkFrame(password_frame, fg_color="transparent")
        password_fields.pack(pady=10, padx=20, fill='x')
        
        # Ancien mot de passe
        old_password_frame = ctk.CTkFrame(password_fields, fg_color="transparent")
        old_password_frame.pack(pady=5, fill='x')
        ctk.CTkLabel(old_password_frame, text="Ancien mot de passe:", width=150).pack(side='left')
        self.old_password_entry = ctk.CTkEntry(old_password_frame, show="*", width=250)
        self.old_password_entry.pack(side='left', padx=10)
        
        # Nouveau mot de passe
        new_password_frame = ctk.CTkFrame(password_fields, fg_color="transparent")
        new_password_frame.pack(pady=5, fill='x')
        ctk.CTkLabel(new_password_frame, text="Nouveau mot de passe:", width=150).pack(side='left')
        self.new_password_entry = ctk.CTkEntry(new_password_frame, show="*", width=250)
        self.new_password_entry.pack(side='left', padx=10)
        
        # Confirmation du nouveau mot de passe
        confirm_password_frame = ctk.CTkFrame(password_fields, fg_color="transparent")
        confirm_password_frame.pack(pady=5, fill='x')
        ctk.CTkLabel(confirm_password_frame, text="Confirmer mot de passe:", width=150).pack(side='left')
        self.confirm_password_entry = ctk.CTkEntry(confirm_password_frame, show="*", width=250)
        self.confirm_password_entry.pack(side='left', padx=10)
        
        # Bouton de modification du mot de passe
        change_password_button = ctk.CTkButton(password_frame, 
                                            text="Modifier le mot de passe",
                                            command=self.change_password,
                                            width=200,
                                            height=35,
                                            corner_radius=10)
        change_password_button.pack(pady=15)
        
        # Section de déconnexion et suppression de compte
        actions_frame = ctk.CTkFrame(options_frame, corner_radius=10)
        actions_frame.pack(pady=10, fill='x')
        
        ctk.CTkLabel(actions_frame, text="Actions du compte", font=("Helvetica", 14, "bold")).pack(pady=10)
        
        # Boutons d'action
        buttons_frame = ctk.CTkFrame(actions_frame, fg_color="transparent")
        buttons_frame.pack(pady=15, padx=20)
        
        # Bouton de déconnexion
        logout_button = ctk.CTkButton(buttons_frame,
                                    text="Déconnexion",
                                    command=self.logout,
                                    width=200,
                                    height=35,
                                    corner_radius=10)
        logout_button.pack(side='left', padx=10)
        
        # Bouton de suppression de compte
        delete_account_button = ctk.CTkButton(buttons_frame,
                                           text="Supprimer le compte",
                                           command=self.delete_account,
                                           width=200,
                                           height=35,
                                           fg_color="#FF5555",
                                           hover_color="#FF0000",
                                           corner_radius=10)
        delete_account_button.pack(side='left', padx=10)
        
        # Account stats
        stats_frame = ctk.CTkFrame(container, corner_radius=15)
        stats_frame.pack(pady=10, fill='x')
        
        ctk.CTkLabel(stats_frame, text="Statistiques du compte", font=("Helvetica", 16, "bold")).pack(pady=10)
        
        # Create grid for stats
        stats_grid = ctk.CTkFrame(stats_frame, fg_color="transparent")
        stats_grid.pack(pady=10, fill='x')
        
        # Récupérer des statistiques supplémentaires
        last_download = self.db['downloads'].find_one({"username": self.current_user}, sort=[("timestamp", -1)])
        last_download_date = "Jamais" if not last_download else last_download["timestamp"].strftime("%d/%m/%Y")
        
        # Téléchargement le plus récent
        recent_frame = ctk.CTkFrame(stats_grid, corner_radius=10)
        recent_frame.pack(side='left', padx=10, fill='both', expand=True)
        ctk.CTkLabel(recent_frame, text="Dernier téléchargement", font=("Helvetica", 14)).pack(pady=5)
        ctk.CTkLabel(recent_frame, text=last_download_date, font=("Helvetica", 18, "bold")).pack(pady=5)
        
        # Formats les plus utilisés
        formats_count = {}
        for download in downloads:
            format_name = download.get('format', 'Inconnu')
            formats_count[format_name] = formats_count.get(format_name, 0) + 1
        
        top_format = "Aucun" if not formats_count else max(formats_count.items(), key=lambda x: x[1])[0]
        
        format_frame = ctk.CTkFrame(stats_grid, corner_radius=10)
        format_frame.pack(side='left', padx=10, fill='both', expand=True)
        ctk.CTkLabel(format_frame, text="Format préféré", font=("Helvetica", 14)).pack(pady=5)
        ctk.CTkLabel(format_frame, text=top_format, font=("Helvetica", 18, "bold")).pack(pady=5)
        
        # Qualité la plus utilisée
        quality_count = {}
        for download in downloads:
            quality_name = download.get('quality', 'Inconnue')
            quality_count[quality_name] = quality_count.get(quality_name, 0) + 1
        
        top_quality = "Aucune" if not quality_count else max(quality_count.items(), key=lambda x: x[1])[0]
        
        quality_frame = ctk.CTkFrame(stats_grid, corner_radius=10)
        quality_frame.pack(side='left', padx=10, fill='both', expand=True)
        ctk.CTkLabel(quality_frame, text="Qualité préférée", font=("Helvetica", 14)).pack(pady=5)
        ctk.CTkLabel(quality_frame, text=top_quality, font=("Helvetica", 18, "bold")).pack(pady=5)
        
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

if __name__ == "__main__":
    app = App()
    app.mainloop()
