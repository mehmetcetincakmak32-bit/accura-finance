import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import hashlib
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.database.connection import get_database_manager
    from src.utils.logger import setup_logger
except ImportError as e:
    print(f"Modul import hatasi: {e}")

PRIMARY = "#1565c0"
PRIMARY_DARK = "#0d47a1"
PRIMARY_LIGHT = "#42a5f5"
TEXT_DARK = "#1a1a2e"
TEXT_MUTED = "#6c757d"

class LoginWindow:
    def __init__(self, parent, on_success_callback):
        self.parent = parent
        self.on_success_callback = on_success_callback
        self.db_manager = get_database_manager()
        self.logger = setup_logger('Login')
        self.create_login_window()
    
    def create_login_window(self):
        self.login_window = ctk.CTkToplevel(self.parent)
        self.login_window.title("Accura Finance - Giris")
        self.login_window.geometry("420x520")
        self.login_window.resizable(False, False)
        self.login_window.transient(self.parent)
        self.login_window.grab_set()
        self.login_window.protocol("WM_DELETE_WINDOW", self.on_close)
        self.center_window()
        
        self.login_window.configure(fg_color="#ffffff")
        
        main_frame = ctk.CTkFrame(self.login_window, fg_color="#ffffff", corner_radius=0)
        main_frame.pack(fill="both", expand=True)
        
        header = ctk.CTkFrame(main_frame, fg_color=PRIMARY, height=140, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        title_label = ctk.CTkLabel(
            header, text="ACCURA FINANCE",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color="white"
        )
        title_label.place(relx=0.5, rely=0.4, anchor="center")
        
        subtitle_label = ctk.CTkLabel(
            header, text="Profesyonel Muhasebe Cozumu",
            font=ctk.CTkFont(size=12),
            text_color="#bbdefb"
        )
        subtitle_label.place(relx=0.5, rely=0.65, anchor="center")
        
        form_frame = ctk.CTkFrame(main_frame, fg_color="#ffffff")
        form_frame.pack(fill="both", expand=True, padx=40, pady=(30, 20))
        
        username_label = ctk.CTkLabel(
            form_frame, text="Kullanici Adi",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=TEXT_DARK, anchor="w"
        )
        username_label.pack(fill="x", pady=(0, 6))
        
        self.username_entry = ctk.CTkEntry(
            form_frame, height=42, font=ctk.CTkFont(size=14),
            placeholder_text="admin", corner_radius=8,
            border_color="#ced4da", fg_color="#f8f9fa"
        )
        self.username_entry.pack(fill="x", pady=(0, 16))
        
        password_label = ctk.CTkLabel(
            form_frame, text="Sifre",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=TEXT_DARK, anchor="w"
        )
        password_label.pack(fill="x", pady=(0, 6))
        
        self.password_entry = ctk.CTkEntry(
            form_frame, height=42, font=ctk.CTkFont(size=14),
            placeholder_text="admin123", show="*", corner_radius=8,
            border_color="#ced4da", fg_color="#f8f9fa"
        )
        self.password_entry.pack(fill="x", pady=(0, 24))
        
        self.login_button = ctk.CTkButton(
            form_frame, text="Giris Yap", height=44,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self.login, corner_radius=8,
            fg_color=PRIMARY, hover_color=PRIMARY_DARK
        )
        self.login_button.pack(fill="x", pady=(0, 10))
        
        demo_button = ctk.CTkButton(
            form_frame, text="Demo ile Dene",
            height=36, font=ctk.CTkFont(size=12),
            command=self.demo_login,
            fg_color="transparent", border_width=1,
            text_color=PRIMARY, border_color="#ced4da",
            hover_color="#f0f4ff", corner_radius=8
        )
        demo_button.pack(fill="x")
        
        footer = ctk.CTkFrame(main_frame, fg_color="#ffffff", height=40)
        footer.pack(fill="x")
        
        ctk.CTkLabel(
            footer, text="(c) 2025 Accura Finance v1.0",
            font=ctk.CTkFont(size=10), text_color=TEXT_MUTED
        ).pack(pady=10)
        
        self.username_entry.bind("<Return>", lambda e: self.password_entry.focus())
        self.password_entry.bind("<Return>", lambda e: self.login())
    
    def on_close(self):
        try:
            self.parent.destroy()
        except:
            os._exit(0)
    
    def center_window(self):
        self.login_window.update_idletasks()
        w = self.login_window.winfo_width()
        h = self.login_window.winfo_height()
        x = (self.login_window.winfo_screenwidth() // 2) - (w // 2)
        y = (self.login_window.winfo_screenheight() // 2) - (h // 2)
        self.login_window.geometry(f"{w}x{h}+{x}+{y}")
    
    def demo_login(self):
        self.username_entry.delete(0, 'end')
        self.password_entry.delete(0, 'end')
        self.username_entry.insert(0, "admin")
        self.password_entry.insert(0, "admin123")
        self.login()
    
    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            messagebox.showerror("Hata", "Kullanici adi ve sifre giriniz!")
            return
        
        try:
            user = self.authenticate_user(username, password)
            
            if user:
                self.logger.info(f"Basarili giris: {username}")
                self.on_success_callback(user)
                self.login_window.destroy()
            else:
                self.logger.warning(f"Basarisiz giris: {username}")
                messagebox.showerror("Hata", "Kullanici adi veya sifre hatali!")
        
        except Exception as e:
            self.logger.error(f"Giris hatasi: {e}")
            messagebox.showerror("Hata", f"Giris yapilirken hata olustu: {e}")
    
    def authenticate_user(self, username, password):
        try:
            query = """
            SELECT UserID, Username, FullName, Email, Role, PasswordHash
            FROM Users 
            WHERE Username = ? AND IsActive = 1
            """
            
            result = self.db_manager.execute_query(query, (username,))
            
            if result and len(result) > 0:
                user = result[0]
                stored_hash = user.get("PasswordHash", "")
                if "$" in stored_hash:
                    salt, expected = stored_hash.split("$", 1)
                    computed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
                    if computed == expected:
                        return user
                else:
                    if hashlib.sha256(password.encode()).hexdigest() == stored_hash:
                        return user
            
            return None
        
        except Exception as e:
            self.logger.error(f"Kullanici dogrulama hatasi: {e}")
            return None
