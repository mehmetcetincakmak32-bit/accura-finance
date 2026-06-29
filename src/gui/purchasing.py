import customtkinter as ctk
from tkinter import messagebox, ttk
import sys, os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from src.database.connection import get_database_manager
except ImportError:
    get_database_manager = None

PRIMARY = "#1565c0"; DANGER = "#c62828"; SUCCESS = "#2e7d32"
TEXT_DARK = "#1a1a2e"; TEXT_MUTED = "#6c757d"; BORDER = "#e8eaed"

class PurchasingFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="#f4f6f8")
        self.app = app
        self.build_ui()

    def build_ui(self):
        header = ctk.CTkFrame(self, fg_color="white", corner_radius=10, height=50)
        header.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(header, text="Satinalma Siparis Yonetimi", font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_DARK).pack(side="left", padx=16, pady=12)
        ctk.CTkButton(header, text="+ Yeni Siparis", fg_color=PRIMARY, hover_color=PRIMARY, corner_radius=6, command=self.new_order).pack(side="right", padx=16)

        main = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        main.pack(fill="both", expand=True)

        notebook = ttk.Notebook(main)
        notebook.pack(fill="both", expand=True, padx=12, pady=12)
        style = ttk.Style()
        style.theme_use("default")

        self.tab_siparisler = ctk.CTkFrame(notebook, fg_color="transparent")
        self.tab_tedarikciler = ctk.CTkFrame(notebook, fg_color="transparent")
        notebook.add(self.tab_siparisler, text="Siparisler")
        notebook.add(self.tab_tedarikciler, text="Tedarikciler")

        for col, txt, width in [(0, "Siparis No", 120), (1, "Tarih", 100), (2, "Tedarikci", 180),
                                  (3, "Toplam", 100), (4, "Durum", 100), (5, "Islem", 80)]:
            ctk.CTkLabel(self.tab_siparisler, text=txt, font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=TEXT_MUTED).grid(row=0, column=col, padx=8, pady=8, sticky="w")

        data = [("SN-2024/001", "15.06.2026", "ABC Tedarik A.S.", "45,200.00 TL", "Beklemede"),
                ("SN-2024/002", "20.06.2026", "XYZ Gida Ltd.", "12,800.00 TL", "Onaylandi"),
                ("SN-2024/003", "25.06.2026", "MNP Tekstil A.S.", "28,500.00 TL", "TeslimEdildi")]
        for r, row in enumerate(data, 1):
            for c, val in enumerate(row):
                lbl = ctk.CTkLabel(self.tab_siparisler, text=val, font=ctk.CTkFont(size=11), text_color=TEXT_DARK)
                lbl.grid(row=r, column=c, padx=8, pady=6, sticky="w")
                if c == 4:
                    colors = {"Beklemede": "#f57f17", "Onaylandi": "#1565c0", "TeslimEdildi": "#2e7d32"}
                    lbl.configure(text_color=colors.get(val, TEXT_DARK))

        self.build_tedarikciler()

    def build_tedarikciler(self):
        for col, txt, width in [(0, "Kod", 80), (1, "Unvan", 200), (2, "Yetkili", 120),
                                  (3, "Telefon", 120), (4, "Bakiye", 100), (5, "Durum", 80)]:
            ctk.CTkLabel(self.tab_tedarikciler, text=txt, font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=TEXT_MUTED).grid(row=0, column=col, padx=8, pady=8, sticky="w")
        data = [("T-001", "ABC Tedarik A.S.", "Ahmet Yilmaz", "0212-555-0101", "45,200 TL"),
                ("T-002", "XYZ Gida Ltd.", "Mehmet Kaya", "0216-555-0202", "12,800 TL")]
        for r, row in enumerate(data, 1):
            for c, val in enumerate(row):
                ctk.CTkLabel(self.tab_tedarikciler, text=val, font=ctk.CTkFont(size=11), text_color=TEXT_DARK).grid(row=r, column=c, padx=8, pady=6, sticky="w")

    def new_order(self):
        messagebox.showinfo("Yeni Siparis", "Satinalma siparisi olusturma ekrani acilacak.")
