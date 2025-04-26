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
                response = requests.get(item.get('thumbnail_url', ''))
                img = Image.open(BytesIO(response.content))
                img = img.resize((120, 90), Image.Resampling.LANCZOS)
                photo = ctk.CTkImage(light_image=img, dark_image=img, size=(120, 90))
                thumbnail_label = ctk.CTkLabel(left_frame, image=photo, text="")
                thumbnail_label.pack()
            except:
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
            
            type_icon = "🎬" if item['type'] == 'Vidéo' else "🎵" if item['type'] == 'Audio' else "📄"
            ctk.CTkLabel(info_frame, text=f"{type_icon} Type: {item['type']}").pack(anchor='w', pady=2)
            
            format_icon = "📁" if item.get('format') else "❌"
            ctk.CTkLabel(info_frame, text=f"{format_icon} Format: {item.get('format', 'N/A')}").pack(anchor='w', pady=2)
            
            if item['type'] == 'Vidéo':
                quality_icon = "📊" if item.get('quality') else "❌"
                ctk.CTkLabel(info_frame, text=f"{quality_icon} Qualité: {item.get('quality', 'N/A')}").pack(anchor='w', pady=2)
            elif item['type'] == 'Transcription':
                language_icon = "🌐" if item.get('language') else "❌"
                ctk.CTkLabel(info_frame, text=f"{language_icon} Langue: {item.get('language', 'N/A')}").pack(anchor='w', pady=2)
            
            size_icon = "💾" if item.get('filesize') else "❌"
            ctk.CTkLabel(info_frame, text=f"{size_icon} Taille: {item.get('filesize', 'N/A')} Mo").pack(anchor='w', pady=2)
            
            time_icon = "⏰"
            ctk.CTkLabel(info_frame, text=f"{time_icon} Téléchargé le: {item['timestamp'].strftime('%d/%m/%Y %H:%M:%S')}").pack(anchor='w', pady=2)
            
            # Créer le cadre des boutons
            button_frame = ctk.CTkFrame(right_frame)
            button_frame.pack(anchor='w', pady=(5,0))
            
            # Bouton pour ouvrir dans YouTube
            ctk.CTkButton(
                button_frame,
                text="▶️ Ouvrir dans YouTube",
                command=lambda url=item['url']: self.open_youtube(url),
                width=150,
                corner_radius=8
            ).pack(side='left', padx=5)
            
            # Bouton pour ouvrir le fichier local (uniquement si le fichier existe)
            file_path = os.path.join(
                self.video_path if item['type'] == 'Vidéo' else self.audio_path,
                f"{item['title']}.{item.get('format', 'mp4')}"
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
            self.quality_menu.configure(values=["---"])
    
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
    
    def display_video_info(self, info):
        # Créer un cadre pour les informations de la vidéo
        self.video_info_frame = ctk.CTkFrame(self.info_frame, corner_radius=15)
        self.video_info_frame.pack(pady=15, padx=15, fill='both', expand=True)
        
        # Titre de la section
        title_frame = ctk.CTkFrame(self.video_info_frame, fg_color="transparent")
        title_frame.pack(pady=(10, 5), padx=10, fill='x')
        ctk.CTkLabel(title_frame, text="📋 Informations de la vidéo", font=("Helvetica", 20, "bold")).pack(anchor='w')
        
        # Conteneur principal avec deux colonnes
        content_frame = ctk.CTkFrame(self.video_info_frame, fg_color="transparent")
        content_frame.pack(pady=10, padx=10, fill='both', expand=True)
        
        # Colonne gauche pour la miniature
        left_column = ctk.CTkFrame(content_frame, fg_color="transparent")
        left_column.pack(side='left', padx=10, pady=10, fill='y')
        
        # Télécharger et afficher la miniature
        thumbnail_url = info.get('thumbnail')
        if thumbnail_url:
            try:
                response = requests.get(thumbnail_url)
                img_data = BytesIO(response.content)
                img = Image.open(img_data)
                
                # Redimensionner l'image tout en conservant les proportions
                width, height = img.size
                max_width = 320
                if width > max_width:
                    ratio = max_width / width
                    new_height = int(height * ratio)
                    img = img.resize((max_width, new_height), Image.LANCZOS)
                
                # Convertir en CTkImage
                thumbnail = ctk.CTkImage(img, size=img.size)
                thumbnail_label = ctk.CTkLabel(left_column, image=thumbnail, text="")
                thumbnail_label.pack(padx=10, pady=10)
            except Exception as e:
                ctk.CTkLabel(left_column, text="Impossible de charger la miniature", font=("Helvetica", 12)).pack(padx=10, pady=10)
        
        # Colonne droite pour les informations textuelles
        right_column = ctk.CTkFrame(content_frame, fg_color="transparent")
        right_column.pack(side='left', padx=10, pady=10, fill='both', expand=True)
        
        # Créer un cadre défilable pour les informations avec une hauteur plus grande
        scrollable_frame = ctk.CTkScrollableFrame(right_column, height=400)
        scrollable_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Titre de la vidéo
        title = info.get('title', 'Titre inconnu')
        title_label = ctk.CTkLabel(scrollable_frame, text=title, font=("Helvetica", 18, "bold"), wraplength=500)
        title_label.pack(anchor='w', pady=(0, 10), fill='x')
        
        # Informations principales
        info_grid = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        info_grid.pack(fill='x', pady=5)
        
        # Chaîne
        channel_frame = ctk.CTkFrame(info_grid, fg_color="transparent")
        channel_frame.pack(fill='x', pady=2)
        ctk.CTkLabel(channel_frame, text="📺 Chaîne:", font=("Helvetica", 14, "bold")).pack(side='left', padx=(0, 5))
        ctk.CTkLabel(channel_frame, text=info.get('uploader', 'Inconnu'), font=("Helvetica", 14)).pack(side='left')
        
        # Abonnés (cette information n'est pas directement disponible via yt-dlp)
        # Nous pouvons afficher un placeholder ou omettre cette information
        
        # Vues
        views_frame = ctk.CTkFrame(info_grid, fg_color="transparent")
        views_frame.pack(fill='x', pady=2)
        ctk.CTkLabel(views_frame, text="👁️ Vues:", font=("Helvetica", 14, "bold")).pack(side='left', padx=(0, 5))
        view_count = info.get('view_count', 0)
        formatted_views = f"{view_count:,}".replace(',', ' ')
        ctk.CTkLabel(views_frame, text=formatted_views, font=("Helvetica", 14)).pack(side='left')
        
        # Durée
        duration_frame = ctk.CTkFrame(info_grid, fg_color="transparent")
        duration_frame.pack(fill='x', pady=2)
        ctk.CTkLabel(duration_frame, text="⏱️ Durée:", font=("Helvetica", 14, "bold")).pack(side='left', padx=(0, 5))
        
        duration = info.get('duration', 0)
        if duration:
            minutes, seconds = divmod(int(duration), 60)
            hours, minutes = divmod(minutes, 60)
            if hours > 0:
                duration_text = f"{hours}h {minutes}m {seconds}s"
            else:
                duration_text = f"{minutes}m {seconds}s"
        else:
            duration_text = "Inconnue"
        
        ctk.CTkLabel(duration_frame, text=duration_text, font=("Helvetica", 14)).pack(side='left')
        
        # Date de publication
        upload_date_frame = ctk.CTkFrame(info_grid, fg_color="transparent")
        upload_date_frame.pack(fill='x', pady=2)
        ctk.CTkLabel(upload_date_frame, text="📅 Date:", font=("Helvetica", 14, "bold")).pack(side='left', padx=(0, 5))
        
        upload_date = info.get('upload_date', '')
        if upload_date and len(upload_date) == 8:
            year = upload_date[:4]
            month = upload_date[4:6]
            day = upload_date[6:8]
            formatted_date = f"{day}/{month}/{year}"
        else:
            formatted_date = "Inconnue"
        
        ctk.CTkLabel(upload_date_frame, text=formatted_date, font=("Helvetica", 14)).pack(side='left')
        
        # Catégorie
        category_frame = ctk.CTkFrame(info_grid, fg_color="transparent")
        category_frame.pack(fill='x', pady=2)
        ctk.CTkLabel(category_frame, text="🏷️ Catégorie:", font=("Helvetica", 14, "bold")).pack(side='left', padx=(0, 5))
        ctk.CTkLabel(category_frame, text=info.get('categories', ['Inconnue'])[0] if info.get('categories') else "Inconnue", font=("Helvetica", 14)).pack(side='left')
        
        # Likes
        likes_frame = ctk.CTkFrame(info_grid, fg_color="transparent")
        likes_frame.pack(fill='x', pady=2)
        ctk.CTkLabel(likes_frame, text="👍 Likes:", font=("Helvetica", 14, "bold")).pack(side='left', padx=(0, 5))
        like_count = info.get('like_count', 0)
        formatted_likes = f"{like_count:,}".replace(',', ' ') if like_count else "Inconnu"
        ctk.CTkLabel(likes_frame, text=formatted_likes, font=("Helvetica", 14)).pack(side='left')
        
        # Description (tronquée)
        description_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        description_frame.pack(fill='x', pady=10)
        ctk.CTkLabel(description_frame, text="📝 Description:", font=("Helvetica", 14, "bold")).pack(anchor='w')
        
        description = info.get('description', 'Aucune description disponible')
        if description:
            # Limiter la description à 200 caractères
            if len(description) > 200:
                description = description[:200] + "..."
            
            desc_label = ctk.CTkLabel(description_frame, text=description, font=("Helvetica", 12), wraplength=500, justify="left")
            desc_label.pack(anchor='w', pady=5, fill='x')
        
        # Bouton de téléchargement centré en bas
        button_frame = ctk.CTkFrame(self.video_info_frame, fg_color="transparent")
        button_frame.pack(pady=15, fill='x')
        
        download_button = ctk.CTkButton(button_frame,
                                      text="Télécharger",
                                      command=self.download,
                                      width=200,
                                      height=50,
                                      corner_radius=10,
                                      font=("Helvetica", 16, "bold"))
        download_button.pack(pady=10, padx=10)
        
        # Stocker l'ID de la vidéo pour le téléchargement
        self.current_video_id = info.get('id')
        
        # Mettre à jour les menus de format et qualité
        self.update_format_and_quality_options()
    
    def check_url(self):
        url = self.url_entry.get()
        if not url:
            messagebox.showerror("Erreur", "Veuillez entrer une URL YouTube valide")
            return

        # Show progress frame and reset
        self.progress_frame.pack(pady=5, padx=10, fill='x')
        self.progress_bar.pack(pady=5, fill='x')
        self.progress_status.configure(text="⏳ Vérification en cours...")
        self.progress_percentage.configure(text="0%")
        self.progress_label.configure(text="Initialisation...")
        self.progress_details_frame.pack(fill='x')
        self.progress_label.pack(side='left', padx=5)
        self.progress_time.pack(side='right', padx=5)
        self.progress_bar.set(0)

        # Create a determinate progress bar
        self.progress_bar.configure(mode="determinate")
        
        # Start time for elapsed time calculation
        start_time = time.time()
        
        # Masquer le bloc d'information vidéo s'il existe déjà
        if hasattr(self, 'video_info_frame') and self.video_info_frame.winfo_exists():
            self.video_info_frame.pack_forget()
        
        def update_progress(step, total_steps=6):
            progress = step / total_steps
            percentage = int(progress * 100)
            elapsed = time.time() - start_time
            
            self.after(0, lambda: [
                self.progress_bar.set(progress),
                self.progress_percentage.configure(text=f"{percentage}%"),
                self.progress_time.configure(text=f"⏱️ {elapsed:.1f}s")
            ])

        def fetch_info():
            try:
                # Step 1: Initialize
                update_progress(1)
                self.after(0, lambda: self.progress_label.configure(
                    text="🔄 Initialisation de la connexion..."
                ))
                time.sleep(0.5)  # Small delay for visual feedback

                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': False
                }

                # Step 2: Connecting
                update_progress(2)
                self.after(0, lambda: self.progress_label.configure(
                    text="🌐 Connexion à YouTube..."
                ))
                time.sleep(0.5)

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # Step 3: Extracting info
                    update_progress(3)
                    self.after(0, lambda: self.progress_label.configure(
                        text="📥 Extraction des informations de la vidéo..."
                    ))
                    info = ydl.extract_info(url, download=False)
                    
                    # Store format information
                    self._video_formats = []
                    self._audio_formats = []
                    
                    # Step 4: Processing video formats
                    update_progress(4)
                    self.after(0, lambda: self.progress_label.configure(
                        text="🎬 Analyse des formats vidéo..."
                    ))
                    
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
                        text="📊 Organisation des formats disponibles..."
                    ))
                    
                    # Sort formats
                    self._video_formats.sort(key=lambda x: (x['height'], x.get('tbr', 0)), reverse=True)
                    
                    # Step 6: Display video information
                    update_progress(6)
                    self.after(0, lambda: self.progress_label.configure(
                        text="✅ Affichage des informations de la vidéo..."
                    ))
                    
                    # Create video info frame
                    self.display_video_info(info)
                    self._audio_formats.sort(key=lambda x: x['abr'], reverse=True)
                    
                    # Store video info
                    self._video_info = info
                    
                    # Step 6: Finalizing
                    update_progress(6)
                    self.after(0, lambda: self.progress_label.configure(
                        text="✅ Finalisation..."
                    ))
                    time.sleep(0.5)
                    
                    # Process and display video info
                    self.after(0, lambda: self.process_video_info(info))
                    
            except Exception as e:
                error_message = f"Impossible de récupérer les informations de la vidéo : {str(e)}\nVérifiez que l'URL est correcte et que votre connexion internet fonctionne."
                self.after(0, lambda: messagebox.showerror("Erreur", error_message))
            finally:
                self.after(0, lambda: self.progress_frame.pack_forget())
        
        Thread(target=fetch_info).start()

    def process_video_info(self, info):
        try:
            # Clear previous info
            for widget in self.info_frame.winfo_children():
                widget.destroy()
            
            # Create a frame for video information with a border and background
            info_container = ctk.CTkFrame(self.info_frame, corner_radius=10)
            info_container.pack(pady=10, padx=10, fill='x')
            
            # Title bar for the info container
            title_bar = ctk.CTkFrame(info_container, fg_color="transparent")
            title_bar.pack(pady=(10, 5), padx=10, fill='x')
            ctk.CTkLabel(title_bar, text="✅ Vidéo vérifiée", font=("Helvetica", 16, "bold")).pack(side='left')
            
            # Content container
            content_container = ctk.CTkFrame(info_container, fg_color="transparent")
            content_container.pack(pady=5, padx=10, fill='x')
            
            # Left side - Thumbnail
            left_frame = ctk.CTkFrame(content_container, fg_color="transparent")
            left_frame.pack(side='left', padx=10)
            
            # Display thumbnail
            if 'thumbnail' in info:
                try:
                    response = requests.get(info['thumbnail'])
                    img = Image.open(BytesIO(response.content))
                    img = img.resize((240, 180), Image.Resampling.LANCZOS)
                    photo = ctk.CTkImage(light_image=img, dark_image=img, size=(240, 180))
                    thumbnail_label = ctk.CTkLabel(left_frame, image=photo, text="")
                    thumbnail_label.pack()
                except Exception as e:
                    ctk.CTkLabel(left_frame, text="🎬 Pas de miniature",
                               width=240, height=180).pack()
            
            # Right side - Information
            right_frame = ctk.CTkFrame(content_container, fg_color="transparent")
            right_frame.pack(side='left', padx=10, fill='x', expand=True)
            
            # Title with ellipsis if too long
            title = info.get('title', 'Unknown Title')
            if len(title) > 50:
                title = title[:47] + "..."
            ctk.CTkLabel(right_frame, 
                        text=title,
                        font=("Helvetica", 16, "bold")).pack(anchor='w')
            
            # Duration
            duration = info.get('duration')
            if duration:
                minutes = duration // 60
                seconds = duration % 60
                ctk.CTkLabel(right_frame, 
                           text=f"⏱️ Durée: {minutes}:{seconds:02d}",
                           font=("Helvetica", 14)).pack(anchor='w')
            
            # Channel info
            if info.get('channel'):
                ctk.CTkLabel(right_frame,
                           text=f"📺 Chaîne: {info['channel']}",
                           font=("Helvetica", 14)).pack(anchor='w')
            
            # View count if available
            if info.get('view_count'):
                view_count = "{:,}".format(info['view_count']).replace(',', ' ')
                ctk.CTkLabel(right_frame,
                           text=f"👁️ Vues: {view_count}",
                           font=("Helvetica", 14)).pack(anchor='w')
            
            # Upload date if available
            if info.get('upload_date'):
                upload_date = datetime.strptime(info['upload_date'], '%Y%m%d').strftime('%d/%m/%Y')
                ctk.CTkLabel(right_frame,
                           text=f"📅 Date: {upload_date}",
                           font=("Helvetica", 14)).pack(anchor='w')
            
            # Add download button directly in the info frame
            download_frame = ctk.CTkFrame(info_container, fg_color="transparent")
            download_frame.pack(pady=(10, 15), padx=10, fill='x')
            
            download_button = ctk.CTkButton(download_frame,
                                          text="📥 Télécharger",
                                          command=self.download,
                                          width=200,
                                          height=45,
                                          corner_radius=10,
                                          font=("Helvetica", 16, "bold"))
            download_button.pack(side='right', padx=10)
            
            # Update options based on content type
            self.update_format_and_quality_options()
            
            # Make the info frame visible
            self.info_frame.pack(pady=10, padx=10, fill='x')
            
        except Exception as e:
            messagebox.showerror("Error", f"Error processing video info: {str(e)}")

    def update_format_and_quality_options(self):
        content_type = self.content_type.get()
        
        # Define available formats for each type
        video_formats = {
            "mp4": "MP4 (Recommended)",
            "webm": "WebM",
            "mkv": "MKV",
            "avi": "AVI"
        }
        audio_formats = {
            "mp3": "MP3 (Recommended)",
            "wav": "WAV (High Quality)",
            "aac": "AAC",
            "m4a": "M4A",
            "opus": "Opus"
        }
        
        if content_type == "Vidéo":
            # Update format menu with video formats
            format_values = list(video_formats.values())
            self.format_menu.configure(values=format_values)
            self.format_var.set(format_values[0])
            
            # Update quality menu with video qualities
            qualities = [f"{f['height']}p ({f['tbr']:.1f}Mbps)" for f in self._video_formats]
            self.quality_menu.configure(values=qualities)
            self.quality_var.set(qualities[0] if qualities else "---")
            
        else:  # Audio
            # Update format menu with audio formats
            format_values = list(audio_formats.values())
            self.format_menu.configure(values=format_values)
            self.format_var.set(format_values[0])
            
            # Update quality menu with audio qualities
            qualities = [f"{int(f['abr'])}kbps" for f in self._audio_formats]
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
                
                # Get the actual format from the display name
                format_display = self.format_var.get()
                target_format = next(k for k, v in self._format_mappings.items() if v == format_display)
                
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
            
    def get_user_download_count(self):
        # Compte le nombre de téléchargements pour l'utilisateur actuel
        if not self.current_user:
            return 0
        return self.db['downloads'].count_documents({"username": self.current_user})

    def setup_downloader_ui(self):
        # Create main frame with modern styling
        self.downloader_frame = ctk.CTkFrame(self, corner_radius=15)
        self.downloader_frame.pack(pady=20, padx=20, fill='both', expand=True)
        
        # Header with logo and title - Enhanced with gradient effect
        header_frame = ctk.CTkFrame(self.downloader_frame, fg_color="transparent")
        header_frame.pack(pady=(20, 10), padx=10, fill='x')
        
        # Logo and title with improved styling
        logo_label = ctk.CTkLabel(header_frame, text="🎬", font=("Helvetica", 45))
        logo_label.pack(side='left', padx=10)
        
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(side='left', padx=10)
        ctk.CTkLabel(title_frame, text="YouTube Downloader Pro", font=("Helvetica", 26, "bold")).pack()
        ctk.CTkLabel(title_frame, text=f"Bienvenue, {self.current_user}", font=("Helvetica", 14, "italic")).pack()
        
        # User stats in header
        stats_label = ctk.CTkLabel(header_frame, 
                                 text=f"📊 Téléchargements: {self.get_user_download_count()}", 
                                 font=("Helvetica", 12))
        stats_label.pack(side='left', padx=20)
        
        # Theme button with improved styling
        self.theme_button = ctk.CTkButton(header_frame, 
                                         text="🌙" if self.appearance_mode == "light" else "☀️",
                                         command=self.toggle_theme, 
                                         width=40,
                                         height=40,
                                         corner_radius=20)
        self.theme_button.pack(side='right', padx=10)
        
        # Logout button with improved styling
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
        # Main container with vertical layout - Enhanced modern design
        main_container = ctk.CTkFrame(self.download_tab)
        main_container.pack(pady=10, padx=10, fill='both', expand=True)
        
        # Store the main container reference for later use
        self.download_main_container = main_container
        
        # Top section - Input and options
        top_section = ctk.CTkFrame(main_container, corner_radius=15)
        top_section.pack(padx=10, pady=10, fill='x')
        
        # Section title with enhanced styling
        title_frame = ctk.CTkFrame(top_section, fg_color="transparent")
        title_frame.pack(pady=(10, 15), fill='x')
        ctk.CTkLabel(title_frame, text="📥 Téléchargement", font=("Helvetica", 22, "bold")).pack(anchor='w', padx=10)
        
        # URL input with improved styling and paste functionality
        url_frame = ctk.CTkFrame(top_section, fg_color="transparent")
        url_frame.pack(pady=(5, 10), fill='x', padx=10)
        
        url_label_frame = ctk.CTkFrame(url_frame, fg_color="transparent")
        url_label_frame.pack(anchor='w', pady=5)
        ctk.CTkLabel(url_label_frame, text="🔗", font=("Helvetica", 18)).pack(side='left', padx=(0, 5))
        ctk.CTkLabel(url_label_frame, text="URL YouTube", font=("Helvetica", 16, "bold")).pack(side='left')
        
        url_input_frame = ctk.CTkFrame(url_frame, fg_color="transparent")
        url_input_frame.pack(fill='x')
        self.url_entry = ctk.CTkEntry(url_input_frame, 
                                    placeholder_text="Collez l'URL de la vidéo YouTube ici",
                                    height=45,
                                    corner_radius=10)
        self.url_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        # Paste button for easy URL pasting
        paste_button = ctk.CTkButton(url_input_frame,
                                   text="📋",
                                   command=lambda: self.url_entry.insert(0, self.clipboard_get()),
                                   width=45,
                                   height=45,
                                   corner_radius=10)
        paste_button.pack(side='left', padx=5)
        
        check_button = ctk.CTkButton(url_input_frame,
                                   text="Vérifier",
                                   command=self.check_url,
                                   width=100,
                                   height=45,
                                   corner_radius=10,
                                   font=("Helvetica", 12, "bold"))
        check_button.pack(side='right')
        
        # Progress frame with enhanced styling (hidden initially)
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
        
        # Créer un espace pour le bloc d'information vidéo (sera rempli lors de la vérification de l'URL)
        
        # Detailed progress information
        self.progress_details_frame = ctk.CTkFrame(self.progress_frame, fg_color="transparent")
        self.progress_details_frame.pack(fill='x')
        
        self.progress_label = ctk.CTkLabel(self.progress_details_frame, text="", font=("Helvetica", 12))
        self.progress_label.pack(side='left', padx=5)
        
        self.progress_time = ctk.CTkLabel(self.progress_details_frame, text="", font=("Helvetica", 12))
        self.progress_time.pack(side='right', padx=5)
        
        # Options section with enhanced card-like appearance
        options_card = ctk.CTkFrame(top_section, corner_radius=10)
        options_card.pack(pady=10, padx=10, fill='x')
        
        options_title = ctk.CTkFrame(options_card, fg_color="transparent")
        options_title.pack(pady=10, padx=10, fill='x')
        ctk.CTkLabel(options_title, text="⚙️ Options de téléchargement", font=("Helvetica", 16, "bold")).pack(anchor='w')
        
        # Content type selection with enhanced styling
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
        
        # Format selection with enhanced styling
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
        
        # Quality selection with icon
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
        
        # Path selection with icon
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
        
        # Video info frame - Now below options
        self.info_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        self.info_frame.pack(pady=10, padx=10, fill='both', expand=True)
        
        # Progress frame
        self.progress_frame = ctk.CTkFrame(self.download_tab, fg_color="transparent")
        self.progress_frame.pack(pady=10, fill='x')
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, width=400)
        self.progress_bar.set(0)
        
        self.progress_label = ctk.CTkLabel(self.progress_frame, text="")
    
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
        # TODO: Add actual graph here
        
        # Downloads over time graph
        time_graph_frame = ctk.CTkFrame(graphs_columns, corner_radius=10)
        time_graph_frame.pack(side='left', padx=10, fill='both', expand=True)
        ctk.CTkLabel(time_graph_frame, text="Téléchargements dans le temps", font=("Helvetica", 14)).pack(pady=10)
        # TODO: Add actual graph here
        
        # History section
        history_frame = ctk.CTkFrame(container, corner_radius=15)
        history_frame.pack(pady=10, fill='both', expand=True)
        
        ctk.CTkLabel(history_frame, text="Historique des téléchargements", font=("Helvetica", 16, "bold")).pack(pady=10)
        
        # Create scrollable frame for history items
        self.history_scroll = ctk.CTkScrollableFrame(history_frame, fg_color="transparent")
        self.history_scroll.pack(pady=10, padx=10, fill='both', expand=True)
        
        # Add sample history items
        for i in range(5):  # TODO: Replace with actual history items
            history_item = ctk.CTkFrame(self.history_scroll, corner_radius=10)
            history_item.pack(pady=5, fill='x')
            
            # Video info
            info_frame = ctk.CTkFrame(history_item, fg_color="transparent")
            info_frame.pack(side='left', padx=10, fill='both', expand=True)
            
            ctk.CTkLabel(info_frame, text=f"Vidéo {i+1}", font=("Helvetica", 14, "bold")).pack(anchor='w')
            ctk.CTkLabel(info_frame, text="Type: Vidéo | Qualité: 720p | Date: 2024-03-20").pack(anchor='w')
            
            # Action buttons
            buttons_frame = ctk.CTkFrame(history_item, fg_color="transparent")
            buttons_frame.pack(side='right', padx=10)
            
            open_youtube = ctk.CTkButton(buttons_frame,
                                       text="YouTube",
                                       width=100,
                                       height=30,
                                       corner_radius=10)
            open_youtube.pack(side='left', padx=5)
            
            open_file = ctk.CTkButton(buttons_frame,
                                    text="Ouvrir",
                                    width=100,
                                    height=30,
                                    corner_radius=10)
            open_file.pack(side='left', padx=5)
    
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
        self.username_label = ctk.CTkLabel(username_frame, text=self.current_user, font=("Helvetica", 14))
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

if __name__ == "__main__":
    app = App()
    app.mainloop()
