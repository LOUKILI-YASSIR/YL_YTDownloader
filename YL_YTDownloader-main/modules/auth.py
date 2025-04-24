import os
import json
import bcrypt
import jwt
import pyotp
import qrcode
from datetime import datetime, timedelta
from pymongo import MongoClient
from google.oauth2 import id_token
from google.auth.transport import requests
from customtkinter import CTk, CTkFrame, CTkLabel, CTkEntry, CTkButton, CTkOptionMenu
from tkinter import messagebox

class AuthManager:
    def __init__(self, app):
        self.app = app
        self.client = MongoClient(os.getenv('MONGODB_URI'))
        self.db = self.client['youtube_downloader']
        self.users = self.db['users']
        self.sessions = self.db['sessions']
        
        # Load JWT secret from environment
        self.jwt_secret = os.getenv('JWT_SECRET')
        
    def setup_auth_ui(self, parent):
        # Create login frame
        self.login_frame = CTkFrame(parent)
        self.login_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Email/Username entry
        CTkLabel(self.login_frame, text="Email/Username:").pack(pady=5)
        self.username_entry = CTkEntry(self.login_frame, width=300)
        self.username_entry.pack(pady=5)
        
        # Password entry
        CTkLabel(self.login_frame, text="Password:").pack(pady=5)
        self.password_entry = CTkEntry(self.login_frame, width=300, show="*")
        self.password_entry.pack(pady=5)
        
        # Login button
        CTkButton(self.login_frame, text="Login", command=self.login).pack(pady=10)
        
        # Google OAuth button
        CTkButton(self.login_frame, text="Login with Google", command=self.google_login).pack(pady=5)
        
        # Register link
        CTkButton(self.login_frame, text="Create Account", command=self.show_register).pack(pady=5)
        
        # Forgot password link
        CTkButton(self.login_frame, text="Forgot Password?", command=self.show_forgot_password).pack(pady=5)
        
    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        user = self.users.find_one({
            "$or": [
                {"email": username},
                {"username": username}
            ]
        })
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            # Check if 2FA is enabled
            if user.get('2fa_enabled'):
                self.show_2fa_verification(user)
            else:
                self.create_session(user)
        else:
            messagebox.showerror("Error", "Invalid credentials")
            
    def google_login(self):
        # Implement Google OAuth2 login
        # This requires setting up OAuth2 credentials in Google Cloud Console
        pass
        
    def show_register(self):
        # Create registration frame
        self.register_frame = CTkFrame(self.app)
        self.register_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Registration form
        CTkLabel(self.register_frame, text="Username:").pack(pady=5)
        self.register_username = CTkEntry(self.register_frame, width=300)
        self.register_username.pack(pady=5)
        
        CTkLabel(self.register_frame, text="Email:").pack(pady=5)
        self.register_email = CTkEntry(self.register_frame, width=300)
        self.register_email.pack(pady=5)
        
        CTkLabel(self.register_frame, text="Password:").pack(pady=5)
        self.register_password = CTkEntry(self.register_frame, width=300, show="*")
        self.register_password.pack(pady=5)
        
        CTkLabel(self.register_frame, text="Confirm Password:").pack(pady=5)
        self.register_confirm = CTkEntry(self.register_frame, width=300, show="*")
        self.register_confirm.pack(pady=5)
        
        # 2FA option
        self.enable_2fa = CTkOptionMenu(self.register_frame, values=["Enable 2FA", "Disable 2FA"])
        self.enable_2fa.pack(pady=5)
        
        # Register button
        CTkButton(self.register_frame, text="Register", command=self.register).pack(pady=10)
        
        # Back to login
        CTkButton(self.register_frame, text="Back to Login", command=self.show_login).pack(pady=5)
        
    def register(self):
        username = self.register_username.get()
        email = self.register_email.get()
        password = self.register_password.get()
        confirm = self.register_confirm.get()
        
        # Validate input
        if not all([username, email, password, confirm]):
            messagebox.showerror("Error", "All fields are required")
            return
            
        if password != confirm:
            messagebox.showerror("Error", "Passwords do not match")
            return
            
        # Check if username or email already exists
        if self.users.find_one({"$or": [{"username": username}, {"email": email}]}):
            messagebox.showerror("Error", "Username or email already exists")
            return
            
        # Hash password
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Setup 2FA if enabled
        if self.enable_2fa.get() == "Enable 2FA":
            secret = pyotp.random_base32()
            totp = pyotp.TOTP(secret)
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(totp.provisioning_uri(username, issuer_name="YouTube Downloader"))
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")
            qr_img.save(f"qr_{username}.png")
        else:
            secret = None
            
        # Create user
        user = {
            "username": username,
            "email": email,
            "password": hashed,
            "2fa_enabled": self.enable_2fa.get() == "Enable 2FA",
            "2fa_secret": secret,
            "created_at": datetime.now(),
            "last_login": None
        }
        
        self.users.insert_one(user)
        messagebox.showinfo("Success", "Registration successful")
        self.show_login()
        
    def show_2fa_verification(self, user):
        # Create 2FA verification frame
        self.twofa_frame = CTkFrame(self.app)
        self.twofa_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        CTkLabel(self.twofa_frame, text="Enter 2FA Code:").pack(pady=5)
        self.twofa_code = CTkEntry(self.twofa_frame, width=300)
        self.twofa_code.pack(pady=5)
        
        CTkButton(self.twofa_frame, text="Verify", 
                 command=lambda: self.verify_2fa(user)).pack(pady=10)
        
    def verify_2fa(self, user):
        code = self.twofa_code.get()
        totp = pyotp.TOTP(user['2fa_secret'])
        
        if totp.verify(code):
            self.create_session(user)
        else:
            messagebox.showerror("Error", "Invalid 2FA code")
            
    def create_session(self, user):
        # Create JWT token
        token = jwt.encode({
            'user_id': str(user['_id']),
            'exp': datetime.utcnow() + timedelta(days=1)
        }, self.jwt_secret, algorithm='HS256')
        
        # Store session
        self.sessions.insert_one({
            'user_id': user['_id'],
            'token': token,
            'created_at': datetime.now(),
            'expires_at': datetime.utcnow() + timedelta(days=1)
        })
        
        # Update last login
        self.users.update_one(
            {'_id': user['_id']},
            {'$set': {'last_login': datetime.now()}}
        )
        
        # Show main application
        self.app.show_main_ui()
        
    def show_forgot_password(self):
        # Create forgot password frame
        self.forgot_frame = CTkFrame(self.app)
        self.forgot_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        CTkLabel(self.forgot_frame, text="Email:").pack(pady=5)
        self.forgot_email = CTkEntry(self.forgot_frame, width=300)
        self.forgot_email.pack(pady=5)
        
        CTkButton(self.forgot_frame, text="Reset Password", 
                 command=self.send_reset_email).pack(pady=10)
        
    def send_reset_email(self):
        email = self.forgot_email.get()
        user = self.users.find_one({"email": email})
        
        if user:
            # Generate reset token
            reset_token = jwt.encode({
                'user_id': str(user['_id']),
                'exp': datetime.utcnow() + timedelta(hours=1)
            }, self.jwt_secret, algorithm='HS256')
            
            # Store reset token
            self.db['password_resets'].insert_one({
                'user_id': user['_id'],
                'token': reset_token,
                'created_at': datetime.now(),
                'expires_at': datetime.utcnow() + timedelta(hours=1)
            })
            
            # Send reset email (implement email sending)
            messagebox.showinfo("Success", "Password reset email sent")
        else:
            messagebox.showerror("Error", "Email not found")
            
    def show_login(self):
        # Remove current frame and show login
        if hasattr(self, 'register_frame'):
            self.register_frame.pack_forget()
        if hasattr(self, 'forgot_frame'):
            self.forgot_frame.pack_forget()
        if hasattr(self, 'twofa_frame'):
            self.twofa_frame.pack_forget()
            
        self.setup_auth_ui(self.app) 