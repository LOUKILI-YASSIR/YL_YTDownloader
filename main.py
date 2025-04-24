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
        
        # Configure la fenêtre
        self.title("YL YTDownloader")
        self.geometry("800x600")
        self.minsize(800, 600)
        
        # Configure le thème
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        # Charge les images
        self.logo_image = ctk.CTkImage(
            light_image=Image.open("assets/logo.png"),
            dark_image=Image.open("assets/logo.png"),
            size=(50, 50)
        )
        
        # Configure la base de données
        self.db = self.setup_database()
        
        # Configure l'interface
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
        self.password_strength_label = ctk.CTkLabel(input_frame,
                                                  text="Force du mot de passe: Faible",
                                                  font=("Helvetica", 12))
        self.password_strength_label.pack(pady=5)
        
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
            
        self.password_strength_label.configure(text=f"Force du mot de passe: {feedback}")
    
    def toggle_theme(self):
        """Bascule entre le mode sombre et clair"""
        current_mode = ctk.get_appearance_mode()
        new_mode = "dark" if current_mode == "light" else "light"
        ctk.set_appearance_mode(new_mode)
        
        # Mettre à jour le texte du bouton de thème
        self.theme_button.configure(text="🌙" if new_mode == "light" else "☀️")
        
        # Mettre à jour le thème de tous les widgets
        self.update_theme_colors()

    def update_theme_colors(self):
        """Met à jour les couleurs de tous les widgets en fonction du thème"""
        current_mode = ctk.get_appearance_mode()
        
        # Couleurs pour le mode clair
        if current_mode == "light":
            fg_color = "gray75"
            selected_color = "gray65"
            selected_hover_color = "gray60"
            unselected_color = "gray85"
            unselected_hover_color = "gray80"
        # Couleurs pour le mode sombre
        else:
            fg_color = "gray25"
            selected_color = "gray35"
            selected_hover_color = "gray40"
            unselected_color = "gray15"
            unselected_hover_color = "gray20"
        
        # Mettre à jour les couleurs du tabview
        if hasattr(self, 'tabview'):
            self.tabview.configure(
                segmented_button_fg_color=(fg_color, fg_color),
                segmented_button_selected_color=(selected_color, selected_color),
                segmented_button_selected_hover_color=(selected_hover_color, selected_hover_color),
                segmented_button_unselected_color=(unselected_color, unselected_color),
                segmented_button_unselected_hover_color=(unselected_hover_color, unselected_hover_color)
            )
    
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
                photo = ImageTk.PhotoImage(img)
                thumbnail_label = ctk.CTkLabel(left_frame, image=photo, text="")
                thumbnail_label.image = photo
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
    
    def check_url(self):
        url = self.url_entry.get()
        if not url:
            messagebox.showerror("Erreur", "Veuillez entrer une URL YouTube valide")
            return
        
        # Show progress frame and reset
        self.progress_frame.pack(pady=5, padx=10, fill='x')
        self.progress_bar.pack(pady=5, fill='x')
        self.progress_label.configure(text="Initialisation...")
        self.progress_label.pack(pady=2)
        self.progress_bar.set(0)
        
        # Create an indeterminate progress bar
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()
        
        def update_progress(step, total_steps=6):
            progress = step / total_steps
            self.after(0, lambda: self.progress_bar.set(progress))

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
                self.after(0, lambda: messagebox.showerror("Erreur", 
                    f"Impossible de récupérer les informations de la vidéo : {str(e)}\n"
                    "Vérifiez que l'URL est correcte et que votre connexion internet fonctionne."))
            finally:
                self.after(0, lambda: self.progress_bar.stop())
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
                    photo = ImageTk.PhotoImage(img)
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
        
        # Check if URL has been verified
        if not hasattr(self, '_video_info'):
            messagebox.showerror("Erreur", "Veuillez d'abord vérifier l'URL")
            return

        # Check if ffmpeg is installed
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            messagebox.showerror(
                "Erreur",
                "FFmpeg n'est pas installé. Veuillez installer FFmpeg pour continuer.\n\n"
                "Instructions d'installation :\n"
                "1. Téléchargez FFmpeg depuis https://ffmpeg.org/download.html\n"
                "2. Ajoutez le chemin d'installation de FFmpeg à votre PATH système\n"
                "3. Redémarrez l'application"
            )
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
                if content_type == "Vidéo":
                    format_info = [f for f in self._video_formats if f['height'] == int(quality)]
                else:
                    format_info = [f for f in self._audio_formats if f['abr'] == int(quality)]
                
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

    def setup_downloader_ui(self):
        """Configure l'interface du téléchargeur"""
        # Créer le frame principal
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True)
        
        # Créer le header
        header_frame = ctk.CTkFrame(self.main_frame)
        header_frame.pack(fill="x", padx=20, pady=20)
        
        # Logo et titre
        logo_label = ctk.CTkLabel(
            header_frame,
            text="🎬",
            font=("Helvetica", 24)
        )
        logo_label.pack(side="left", padx=10)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="YL YTDownloader",
            font=("Helvetica", 24, "bold")
        )
        title_label.pack(side="left", padx=10)
        
        # Bouton de thème
        self.theme_button = ctk.CTkButton(
            header_frame,
            text="🌙" if ctk.get_appearance_mode() == "light" else "☀️",
            command=self.toggle_theme,
            width=40,
            height=40,
            corner_radius=20
        )
        self.theme_button.pack(side="right", padx=10)
        
        # Bouton de déconnexion
        logout_button = ctk.CTkButton(
            header_frame,
            text="Déconnexion",
            command=self.logout,
            width=100,
            height=40
        )
        logout_button.pack(side="right", padx=10)
        
        # Créer le tabview
        self.tabview = ctk.CTkTabview(self.main_frame)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Ajouter les onglets et les stocker comme attributs
        self.download_tab = self.tabview.add("Téléchargement")
        self.dashboard_tab = self.tabview.add("Tableau de bord")
        self.profile_tab = self.tabview.add("Profil")
        
        # Configurer les onglets
        self.setup_download_tab()
        self.setup_dashboard_tab()
        self.setup_profile_tab()
        
        # Configurer le style des onglets
        self.tabview.configure(
            segmented_button_fg_color=("gray75", "gray25"),
            segmented_button_selected_color=("gray65", "gray35"),
            segmented_button_selected_hover_color=("gray60", "gray40"),
            segmented_button_unselected_color=("gray85", "gray15"),
            segmented_button_unselected_hover_color=("gray80", "gray20")
        )

    def toggle_theme(self):
        """Bascule entre le mode sombre et clair"""
        current_mode = ctk.get_appearance_mode()
        new_mode = "dark" if current_mode == "light" else "light"
        ctk.set_appearance_mode(new_mode)
        
        # Mettre à jour le texte du bouton de thème
        self.theme_button.configure(text="🌙" if new_mode == "light" else "☀️")
        
        # Mettre à jour le thème de tous les widgets
        self.update_theme_colors()

    def update_theme_colors(self):
        """Met à jour les couleurs de tous les widgets en fonction du thème"""
        current_mode = ctk.get_appearance_mode()
        
        # Couleurs pour le mode clair
        if current_mode == "light":
            fg_color = "gray75"
            selected_color = "gray65"
            selected_hover_color = "gray60"
            unselected_color = "gray85"
            unselected_hover_color = "gray80"
        # Couleurs pour le mode sombre
        else:
            fg_color = "gray25"
            selected_color = "gray35"
            selected_hover_color = "gray40"
            unselected_color = "gray15"
            unselected_hover_color = "gray20"
        
        # Mettre à jour les couleurs du tabview
        if hasattr(self, 'tabview'):
            self.tabview.configure(
                segmented_button_fg_color=(fg_color, fg_color),
                segmented_button_selected_color=(selected_color, selected_color),
                segmented_button_selected_hover_color=(selected_hover_color, selected_hover_color),
                segmented_button_unselected_color=(unselected_color, unselected_color),
                segmented_button_unselected_hover_color=(unselected_hover_color, unselected_hover_color)
            )
    
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
                photo = ImageTk.PhotoImage(img)
                thumbnail_label = ctk.CTkLabel(left_frame, image=photo, text="")
                thumbnail_label.image = photo
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
    
    def check_url(self):
        url = self.url_entry.get()
        if not url:
            messagebox.showerror("Erreur", "Veuillez entrer une URL YouTube valide")
            return
        
        # Show progress frame and reset
        self.progress_frame.pack(pady=5, padx=10, fill='x')
        self.progress_bar.pack(pady=5, fill='x')
        self.progress_label.configure(text="Initialisation...")
        self.progress_label.pack(pady=2)
        self.progress_bar.set(0)
        
        # Create a determinate progress bar
        self.progress_bar.configure(mode="determinate")
        
        def update_progress(step, total_steps=6):
            progress = step / total_steps
            self.after(0, lambda: self.progress_bar.set(progress))

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
                self.after(0, lambda: messagebox.showerror("Erreur", 
                    f"Impossible de récupérer les informations de la vidéo : {str(e)}\n"
                    "Vérifiez que l'URL est correcte et que votre connexion internet fonctionne."))
            finally:
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
                    photo = ImageTk.PhotoImage(img)
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
        
        # Check if URL has been verified
        if not hasattr(self, '_video_info'):
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
                if content_type == "Vidéo":
                    format_info = [f for f in self._video_formats if f['height'] == int(quality)]
                else:
                    format_info = [f for f in self._audio_formats if f['abr'] == int(quality)]
                
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

    def setup_download_tab(self):
        # URL input frame
        url_frame = ctk.CTkFrame(self.download_tab, fg_color="transparent")
        url_frame.pack(pady=10, fill='x')
        
        ctk.CTkLabel(url_frame, text="URL YouTube:", font=("Helvetica", 14)).pack(side='left', padx=5)
        self.url_entry = ctk.CTkEntry(url_frame, 
                                    placeholder_text="Collez l'URL de la vidéo YouTube ici",
                                    width=400,
                                    height=40,
                                    corner_radius=10)
        self.url_entry.pack(side='left', padx=5, fill='x', expand=True)
        
        check_button = ctk.CTkButton(url_frame,
                                   text="Vérifier l'URL",
                                   command=self.check_url,
                                   width=100,
                                   height=40,
                                   corner_radius=10)
        check_button.pack(side='left', padx=5)
        
        # Content type selection
        type_frame = ctk.CTkFrame(self.download_tab, fg_color="transparent")
        type_frame.pack(pady=10, fill='x')
        
        ctk.CTkLabel(type_frame, text="Type de contenu:", font=("Helvetica", 14)).pack(side='left', padx=5)
        self.content_type = ctk.StringVar(value="Vidéo")
        type_menu = ctk.CTkOptionMenu(type_frame,
                                    variable=self.content_type,
                                    values=["Vidéo", "Audio"],
                                    command=self.on_content_type_change,
                                    width=150,
                                    height=40,
                                    corner_radius=10)
        type_menu.pack(side='left', padx=5)
        
        # Format selection frame
        self.format_frame = ctk.CTkFrame(self.download_tab, fg_color="transparent")
        self.format_frame.pack(pady=10, fill='x')
        
        ctk.CTkLabel(self.format_frame, text="Format:", font=("Helvetica", 14)).pack(side='left', padx=5)
        self.format_var = ctk.StringVar(value="----")
        self.format_menu = ctk.CTkOptionMenu(self.format_frame,
                                           variable=self.format_var,
                                           values=["----"],
                                           width=150,
                                           height=40,
                                           corner_radius=10)
        self.format_menu.pack(side='left', padx=5)
        
        # Quality selection frame
        self.quality_frame = ctk.CTkFrame(self.download_tab, fg_color="transparent")
        self.quality_frame.pack(pady=10, fill='x')
        
        ctk.CTkLabel(self.quality_frame, text="Qualité:", font=("Helvetica", 14)).pack(side='left', padx=5)
        self.quality_var = ctk.StringVar(value="----")
        self.quality_menu = ctk.CTkOptionMenu(self.quality_frame,
                                            variable=self.quality_var,
                                            values=["----"],
                                            width=150,
                                            height=40,
                                            corner_radius=10)
        self.quality_menu.pack(side='left', padx=5)
        
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
                                    text="Parcourir",
                                    command=self.browse_path,
                                    width=100,
                                    height=40,
                                    corner_radius=10)
        browse_button.pack(side='left', padx=5)
        
        # Video info frame
        self.info_frame = ctk.CTkFrame(self.download_tab, fg_color="transparent")
        self.info_frame.pack(pady=10, fill='x')
        
        # Download button
        download_button = ctk.CTkButton(self.download_tab,
                                      text="Télécharger",
                                      command=self.download,
                                      width=150,
                                      height=40,
                                      corner_radius=10)
        download_button.pack(pady=10)
        
        # Progress frame
        self.progress_frame = ctk.CTkFrame(self.download_tab, fg_color="transparent")
        self.progress_frame.pack(pady=10, fill='x')
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, width=400)
        self.progress_bar.set(0)
        
        self.progress_label = ctk.CTkLabel(self.progress_frame, text="")
    
    def setup_dashboard_tab(self):
        """Configure l'onglet du tableau de bord"""
        # Créer un frame pour le tableau de bord
        dashboard_frame = ctk.CTkFrame(self.tabview.tab("Tableau de bord"))
        dashboard_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Titre du tableau de bord
        title_label = ctk.CTkLabel(
            dashboard_frame,
            text="Tableau de bord",
            font=("Helvetica", 24, "bold")
        )
        title_label.pack(pady=20)
        
        # Statistiques
        stats_frame = ctk.CTkFrame(dashboard_frame)
        stats_frame.pack(fill="x", padx=20, pady=10)
        
        # Récupérer les statistiques
        stats = self.get_user_stats()
        if stats:
            # Total des téléchargements
            total_label = ctk.CTkLabel(
                stats_frame,
                text=f"Total des téléchargements: {stats.get('total_downloads', 0)}",
                font=("Helvetica", 16)
            )
            total_label.pack(pady=5)
            
            # Téléchargements vidéo
            video_label = ctk.CTkLabel(
                stats_frame,
                text=f"Vidéos téléchargées: {stats.get('video_downloads', 0)}",
                font=("Helvetica", 16)
            )
            video_label.pack(pady=5)
            
            # Téléchargements audio
            audio_label = ctk.CTkLabel(
                stats_frame,
                text=f"Audios téléchargés: {stats.get('audio_downloads', 0)}",
                font=("Helvetica", 16)
            )
            audio_label.pack(pady=5)
            
            # Dernière activité
            last_activity = stats.get('last_activity', datetime.now())
            last_activity_label = ctk.CTkLabel(
                stats_frame,
                text=f"Dernière activité: {last_activity.strftime('%d/%m/%Y %H:%M')}",
                font=("Helvetica", 16)
            )
            last_activity_label.pack(pady=5)
        
        # Historique récent
        history_frame = ctk.CTkFrame(dashboard_frame)
        history_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        history_label = ctk.CTkLabel(
            history_frame,
            text="Historique récent",
            font=("Helvetica", 18, "bold")
        )
        history_label.pack(pady=10)
        
        # Récupérer l'historique
        history = self.get_download_history()
        if history:
            for item in history[:5]:  # Afficher les 5 derniers téléchargements
                history_item = ctk.CTkFrame(history_frame)
                history_item.pack(fill="x", padx=10, pady=5)
                
                title = ctk.CTkLabel(
                    history_item,
                    text=item["title"],
                    font=("Helvetica", 14)
                )
                title.pack(side="left", padx=5)
                
                type_label = ctk.CTkLabel(
                    history_item,
                    text=f"{item['type']} - {item['format']}",
                    font=("Helvetica", 12)
                )
                type_label.pack(side="right", padx=5)
        
        else:
            no_history_label = ctk.CTkLabel(
                history_frame,
                text="Aucun historique de téléchargement",
                font=("Helvetica", 14)
            )
            no_history_label.pack(pady=20)

    def setup_profile_tab(self):
        """Configure l'onglet du profil"""
        # Créer un frame pour le profil
        profile_frame = ctk.CTkFrame(self.tabview.tab("Profil"))
        profile_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Titre du profil
        title_label = ctk.CTkLabel(
            profile_frame,
            text="Profil",
            font=("Helvetica", 24, "bold")
        )
        title_label.pack(pady=20)
        
        # Informations utilisateur
        user_info = self.db.users.find_one({"username": self.current_user})
        if user_info:
            # Nom d'utilisateur
            username_frame = ctk.CTkFrame(profile_frame)
            username_frame.pack(fill="x", padx=20, pady=10)
            
            username_label = ctk.CTkLabel(
                username_frame,
                text=f"Nom d'utilisateur: {user_info['username']}",
                font=("Helvetica", 16)
            )
            username_label.pack(side="left", padx=5)
            
            # Email
            email_frame = ctk.CTkFrame(profile_frame)
            email_frame.pack(fill="x", padx=20, pady=10)
            
            email_label = ctk.CTkLabel(
                email_frame,
                text=f"Email: {user_info['email']}",
                font=("Helvetica", 16)
            )
            email_label.pack(side="left", padx=5)
            
            # Date d'inscription
            register_date = user_info.get('register_date', datetime.now())
            date_frame = ctk.CTkFrame(profile_frame)
            date_frame.pack(fill="x", padx=20, pady=10)
            
            date_label = ctk.CTkLabel(
                date_frame,
                text=f"Date d'inscription: {register_date.strftime('%d/%m/%Y')}",
                font=("Helvetica", 16)
            )
            date_label.pack(side="left", padx=5)
        
        # Bouton de déconnexion
        logout_button = ctk.CTkButton(
            profile_frame,
            text="Déconnexion",
            command=self.logout,
            font=("Helvetica", 14),
            width=200,
            height=40
        )
        logout_button.pack(pady=20)
        
        # Bouton de suppression de compte
        delete_button = ctk.CTkButton(
            profile_frame,
            text="Supprimer le compte",
            command=self.delete_account,
            font=("Helvetica", 14),
            width=200,
            height=40,
            fg_color="red",
            hover_color="darkred"
        )
        delete_button.pack(pady=10)

    def delete_account(self):
        """Supprime le compte de l'utilisateur"""
        if messagebox.askyesno(
            "Confirmation",
            "Êtes-vous sûr de vouloir supprimer votre compte ? Cette action est irréversible."
        ):
            try:
                # Supprimer l'historique des téléchargements
                self.db.downloads.delete_many({"username": self.current_user})
                
                # Supprimer le compte utilisateur
                self.db.users.delete_one({"username": self.current_user})
                
                # Déconnecter l'utilisateur
                self.logout()
                
                messagebox.showinfo(
                    "Succès",
                    "Votre compte a été supprimé avec succès."
                )
            except Exception as e:
                messagebox.showerror(
                    "Erreur",
                    f"Une erreur est survenue lors de la suppression du compte: {str(e)}"
                )

    def save_download_history(self, download_info):
        """Sauvegarde les informations de téléchargement dans la base de données"""
        try:
            # Créer un document pour l'historique
            history_doc = {
                "username": self.current_user,
                "url": download_info["url"],
                "title": download_info["title"],
                "type": download_info["type"],
                "format": download_info["format"],
                "quality": download_info["quality"],
                "path": download_info["path"],
                "timestamp": datetime.now(),
                "file_size": download_info.get("file_size", 0)
            }
            
            # Insérer dans la collection downloads
            self.db.downloads.insert_one(history_doc)
            
            # Mettre à jour les statistiques de l'utilisateur
            self.update_user_stats()
            
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de l'historique: {str(e)}")
            return False

    def update_user_stats(self):
        """Met à jour les statistiques de l'utilisateur"""
        try:
            # Compter le nombre total de téléchargements
            total_downloads = self.db.downloads.count_documents({"username": self.current_user})
            
            # Compter les téléchargements par type
            video_downloads = self.db.downloads.count_documents({
                "username": self.current_user,
                "type": "Vidéo"
            })
            
            audio_downloads = self.db.downloads.count_documents({
                "username": self.current_user,
                "type": "Audio"
            })
            
            # Mettre à jour les statistiques dans la collection users
            self.db.users.update_one(
                {"username": self.current_user},
                {
                    "$set": {
                        "total_downloads": total_downloads,
                        "video_downloads": video_downloads,
                        "audio_downloads": audio_downloads,
                        "last_activity": datetime.now()
                    }
                }
            )
        except Exception as e:
            print(f"Erreur lors de la mise à jour des statistiques: {str(e)}")

    def get_download_history(self):
        """Récupère l'historique des téléchargements de l'utilisateur"""
        try:
            return list(self.db.downloads.find(
                {"username": self.current_user}
            ).sort("timestamp", -1))
        except Exception as e:
            print(f"Erreur lors de la récupération de l'historique: {str(e)}")
            return []

    def get_user_stats(self):
        """Récupère les statistiques de l'utilisateur"""
        try:
            return self.db.users.find_one(
                {"username": self.current_user},
                {
                    "total_downloads": 1,
                    "video_downloads": 1,
                    "audio_downloads": 1,
                    "last_activity": 1
                }
            )
        except Exception as e:
            print(f"Erreur lors de la récupération des statistiques: {str(e)}")
            return None

if __name__ == "__main__":
    app = App()
    app.mainloop()
