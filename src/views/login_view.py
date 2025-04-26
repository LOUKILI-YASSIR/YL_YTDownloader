import customtkinter as ctk
from tkinter import messagebox
from PIL import Image
import os

class LoginView:
    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller
        
        # Load eye icons
        self.visible_eye = ctk.CTkImage(Image.open("images/VisibleEyeIcon.jpg"), size=(20, 20))
        self.invisible_eye = ctk.CTkImage(Image.open("images/InvisibleEyeIcon.jpg"), size=(20, 20))
        
        self.setup_login_ui()
    
    def setup_login_ui(self):
        self.login_frame = ctk.CTkFrame(self.parent, corner_radius=15)
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
                                         text="🌙 Mode Sombre" if self.controller.appearance_mode == "light" else "☀️ Mode Clair",
                                         command=self.controller.toggle_theme, 
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
    
    def toggle_password_visibility(self):
        self.show_password_var.set(not self.show_password_var.get())
        if self.show_password_var.get():
            self.password_entry.configure(show="")
            self.show_password_button.configure(image=self.visible_eye)
        else:
            self.password_entry.configure(show="*")
            self.show_password_button.configure(image=self.invisible_eye)
    
    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Erreur", "Veuillez remplir tous les champs")
            return
        
        success, result = self.controller.login(username, password)
        if success:
            if self.remember_var.get():
                self.controller.save_session(result)
            self.controller.show_downloader()
        else:
            messagebox.showerror("Erreur", result)
    
    def show_register(self):
        self.controller.show_register()
    
    def show_forgot_password(self):
        self.controller.show_forgot_password()
    
    def hide(self):
        self.login_frame.pack_forget() 