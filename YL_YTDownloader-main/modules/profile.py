import os
import json
import bcrypt
import pyotp
import qrcode
from datetime import datetime
from PIL import Image, ImageTk
from customtkinter import CTkFrame, CTkLabel, CTkEntry, CTkButton, CTkOptionMenu, CTkImage
from tkinter import messagebox, filedialog

class ProfileManager:
    def __init__(self, app):
        self.app = app
        self.client = app.client
        self.db = app.db
        self.users = app.db['users']
        
    def setup_profile_info(self, parent):
        # Get current user
        user = self.users.find_one({'_id': self.app.current_user['_id']})
        
        # Profile picture
        profile_pic_frame = CTkFrame(parent)
        profile_pic_frame.pack(fill="x", padx=10, pady=10)
        
        if user.get('profile_picture'):
            try:
                img = Image.open(user['profile_picture'])
                img = img.resize((100, 100))
                photo = CTkImage(img)
                CTkLabel(profile_pic_frame, image=photo).pack(side="left", padx=5)
            except:
                CTkLabel(profile_pic_frame, text="No Profile Picture").pack(side="left", padx=5)
        
        CTkButton(profile_pic_frame, text="Change Picture", 
                 command=self.change_profile_picture).pack(side="left", padx=5)
        
        # User info
        info_frame = CTkFrame(parent)
        info_frame.pack(fill="x", padx=10, pady=10)
        
        # Username
        username_frame = CTkFrame(info_frame)
        username_frame.pack(fill="x", pady=5)
        CTkLabel(username_frame, text="Username:", width=100).pack(side="left")
        self.username_entry = CTkEntry(username_frame)
        self.username_entry.insert(0, user.get('username', ''))
        self.username_entry.pack(side="left", fill="x", expand=True)
        
        # Email
        email_frame = CTkFrame(info_frame)
        email_frame.pack(fill="x", pady=5)
        CTkLabel(email_frame, text="Email:", width=100).pack(side="left")
        self.email_entry = CTkEntry(email_frame)
        self.email_entry.insert(0, user.get('email', ''))
        self.email_entry.pack(side="left", fill="x", expand=True)
        
        # Save button
        CTkButton(parent, text="Save Changes", 
                 command=self.save_profile_changes).pack(pady=10)
        
    def setup_settings(self, parent):
        # Security settings
        security_frame = CTkFrame(parent)
        security_frame.pack(fill="x", padx=10, pady=10)
        
        CTkLabel(security_frame, text="Security Settings", 
                font=("Helvetica", 14, "bold")).pack(pady=5)
        
        # Change password
        password_frame = CTkFrame(security_frame)
        password_frame.pack(fill="x", pady=5)
        CTkButton(password_frame, text="Change Password", 
                 command=self.change_password).pack(side="left", padx=5)
        
        # 2FA
        twofa_frame = CTkFrame(security_frame)
        twofa_frame.pack(fill="x", pady=5)
        CTkButton(twofa_frame, text="Setup 2FA", 
                 command=self.setup_2fa).pack(side="left", padx=5)
        
        # Download settings
        download_frame = CTkFrame(parent)
        download_frame.pack(fill="x", padx=10, pady=10)
        
        CTkLabel(download_frame, text="Download Settings", 
                font=("Helvetica", 14, "bold")).pack(pady=5)
        
        # Default download path
        path_frame = CTkFrame(download_frame)
        path_frame.pack(fill="x", pady=5)
        CTkLabel(path_frame, text="Download Path:", width=100).pack(side="left")
        self.download_path_entry = CTkEntry(path_frame)
        self.download_path_entry.insert(0, os.getenv('DOWNLOAD_PATH', 'downloads'))
        self.download_path_entry.pack(side="left", fill="x", expand=True)
        CTkButton(path_frame, text="Browse", 
                 command=self.browse_download_path).pack(side="left", padx=5)
        
        # Default format
        format_frame = CTkFrame(download_frame)
        format_frame.pack(fill="x", pady=5)
        CTkLabel(format_frame, text="Default Format:", width=100).pack(side="left")
        self.default_format = CTkOptionMenu(format_frame, 
                                          values=["mp4", "webm", "mkv", "mp3", "wav"])
        self.default_format.pack(side="left", fill="x", expand=True)
        
        # Save settings
        CTkButton(parent, text="Save Settings", 
                 command=self.save_settings).pack(pady=10)
        
    def change_profile_picture(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.png *.jpg *.jpeg")]
        )
        
        if file_path:
            try:
                # Resize image
                img = Image.open(file_path)
                img = img.resize((100, 100))
                
                # Save to user directory
                user_dir = os.path.join('profiles', str(self.app.current_user['_id']))
                os.makedirs(user_dir, exist_ok=True)
                save_path = os.path.join(user_dir, 'profile.jpg')
                img.save(save_path)
                
                # Update database
                self.users.update_one(
                    {'_id': self.app.current_user['_id']},
                    {'$set': {'profile_picture': save_path}}
                )
                
                messagebox.showinfo("Success", "Profile picture updated")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update profile picture: {str(e)}")
                
    def save_profile_changes(self):
        username = self.username_entry.get()
        email = self.email_entry.get()
        
        if not username or not email:
            messagebox.showerror("Error", "Username and email are required")
            return
            
        try:
            self.users.update_one(
                {'_id': self.app.current_user['_id']},
                {'$set': {
                    'username': username,
                    'email': email,
                    'updated_at': datetime.now()
                }}
            )
            messagebox.showinfo("Success", "Profile updated successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update profile: {str(e)}")
            
    def change_password(self):
        # Create password change dialog
        dialog = CTkFrame(self.app)
        dialog.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Current password
        CTkLabel(dialog, text="Current Password:").pack(pady=5)
        current_password = CTkEntry(dialog, show="*")
        current_password.pack(pady=5)
        
        # New password
        CTkLabel(dialog, text="New Password:").pack(pady=5)
        new_password = CTkEntry(dialog, show="*")
        new_password.pack(pady=5)
        
        # Confirm password
        CTkLabel(dialog, text="Confirm Password:").pack(pady=5)
        confirm_password = CTkEntry(dialog, show="*")
        confirm_password.pack(pady=5)
        
        def save_password():
            if not all([current_password.get(), new_password.get(), confirm_password.get()]):
                messagebox.showerror("Error", "All fields are required")
                return
                
            if new_password.get() != confirm_password.get():
                messagebox.showerror("Error", "Passwords do not match")
                return
                
            # Verify current password
            user = self.users.find_one({'_id': self.app.current_user['_id']})
            if not bcrypt.checkpw(current_password.get().encode('utf-8'), user['password']):
                messagebox.showerror("Error", "Current password is incorrect")
                return
                
            # Update password
            hashed = bcrypt.hashpw(new_password.get().encode('utf-8'), bcrypt.gensalt())
            self.users.update_one(
                {'_id': self.app.current_user['_id']},
                {'$set': {'password': hashed}}
            )
            
            messagebox.showinfo("Success", "Password changed successfully")
            dialog.pack_forget()
            
        CTkButton(dialog, text="Save", command=save_password).pack(pady=10)
        CTkButton(dialog, text="Cancel", 
                 command=lambda: dialog.pack_forget()).pack(pady=5)
        
    def setup_2fa(self):
        # Generate secret
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp.provisioning_uri(
            self.app.current_user['username'],
            issuer_name="YouTube Downloader"
        ))
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Save QR code
        user_dir = os.path.join('profiles', str(self.app.current_user['_id']))
        os.makedirs(user_dir, exist_ok=True)
        qr_path = os.path.join(user_dir, '2fa_qr.png')
        qr_img.save(qr_path)
        
        # Show QR code and verification
        dialog = CTkFrame(self.app)
        dialog.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Display QR code
        img = Image.open(qr_path)
        img = img.resize((200, 200))
        photo = CTkImage(img)
        CTkLabel(dialog, image=photo).pack(pady=10)
        
        # Verification code
        CTkLabel(dialog, text="Enter verification code:").pack(pady=5)
        verification_code = CTkEntry(dialog)
        verification_code.pack(pady=5)
        
        def verify_2fa():
            if totp.verify(verification_code.get()):
                # Save 2FA secret
                self.users.update_one(
                    {'_id': self.app.current_user['_id']},
                    {'$set': {
                        '2fa_enabled': True,
                        '2fa_secret': secret
                    }}
                )
                messagebox.showinfo("Success", "2FA setup completed")
                dialog.pack_forget()
            else:
                messagebox.showerror("Error", "Invalid verification code")
                
        CTkButton(dialog, text="Verify", command=verify_2fa).pack(pady=10)
        CTkButton(dialog, text="Cancel", 
                 command=lambda: dialog.pack_forget()).pack(pady=5)
        
    def browse_download_path(self):
        path = filedialog.askdirectory()
        if path:
            self.download_path_entry.delete(0, 'end')
            self.download_path_entry.insert(0, path)
            
    def save_settings(self):
        download_path = self.download_path_entry.get()
        default_format = self.default_format.get()
        
        if not download_path:
            messagebox.showerror("Error", "Download path is required")
            return
            
        try:
            # Update settings
            self.users.update_one(
                {'_id': self.app.current_user['_id']},
                {'$set': {
                    'settings': {
                        'download_path': download_path,
                        'default_format': default_format
                    }
                }}
            )
            
            # Update environment variable
            os.environ['DOWNLOAD_PATH'] = download_path
            
            messagebox.showinfo("Success", "Settings saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}") 