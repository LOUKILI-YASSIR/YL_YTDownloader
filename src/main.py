import customtkinter as ctk
from controllers.app_controller import AppController
import os

def main():
    # Set the appearance mode and color theme
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    
    # Create and run the application
    app = AppController()
    app.run()

if __name__ == "__main__":
    main()