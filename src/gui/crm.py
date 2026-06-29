import customtkinter as ctk
from tkinter import messagebox, ttk
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PRIMARY = "#1565c0"; SUCCESS = "#2e7d32"; WARNING = "#f57f17"
TEXT_DARK = "#1a1a2e"; TEXT_MUTED = "#6c757d"

class CRMFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="#f4f6f8")
        self.app = app
        self.build_ui()

    def build_ui(self):
        header = ctk.CTkFrame(self, fg_color="white", corner_radius=10, height=50)
        header.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(header, text="Musteri Iliskileri Yonetimi (CRM)", font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_DARK).pack(side="left", padx=16, pady=12)
        ctk.CTkButton(header, text="+ Yeni Aktivite", fg_color=PRIMARY, corner_radius=6, command=self.new_activity).pack(side="right", padx=4)
        ctk.CTkButton(header, text="Rapor", fg_color=SUCCESS, corner_radius=6, command=self.report).pack(side="right", padx=4)

        main = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        main.pack(fill="both", expand=True)

        notebook = ttk.Notebook(main)
        notebook.pack(fill="both", expand=True, padx=12, pady=12)

        self.tab_aktiviteler = ctk.CTkFrame(notebook, fg_color="transparent")
        self.tab_musteriler = ctk.CTkFrame(notebook, fg_color="transparent")
        notebook.add(self.tab_aktiviteler, text="Aktiviteler")
        notebook.add(self.tab_musteriler, text="Musteri Analizi")

        for col, txt in enumerate(["Tarih", "Aktivite Turu", "Musteri", "Konu", "Durum", "Takip Tarihi", "Sorumlu"]):
            ctk.CTkLabel(self.tab_aktiviteler, text=txt, font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).grid(row=0, column=col, padx=6, pady=6, sticky="w")

        acts = [("20.06.2026", "Telefon", "ABC Ltd.", "Fiyat teklifi gorusmesi", "Tamamlandi", "-", "Ahmet"),
                ("22.06.2026", "Toplanti", "XYZ A.S.", "Yeni sozlesme", "Planlandi", "25.06.2026", "Ayse"),
                ("23.06.2026", "Email", "DEF Tic.", "Urun talebi", "Beklemede", "28.06.2026", "Mehmet")]
        for r, row in enumerate(acts, 1):
            for c, val in enumerate(row):
                clr = {"Tamamlandi": SUCCESS, "Planlandi": PRIMARY, "Beklemede": WARNING}.get(val, TEXT_DARK)
                ctk.CTkLabel(self.tab_aktiviteler, text=val, font=ctk.CTkFont(size=11), text_color=clr).grid(row=r, column=c, padx=6, pady=4, sticky="w")

        stats_frame = ctk.CTkFrame(self.tab_musteriler, fg_color="transparent")
        stats_frame.pack(fill="x", pady=12)

        stats = [("Toplam Musteri", 145), ("Aktif Musteri", 128), ("Bugunku Gorusme", 6), ("Bekleyen Teklif", 12)]
        for i, (label, val) in enumerate(stats):
            card = ctk.CTkFrame(stats_frame, fg_color="#f8f9fa", corner_radius=8, border_width=1, border_color="#e8eaed")
            card.grid(row=0, column=i, padx=6, pady=6, sticky="nsew")
            stats_frame.grid_columnconfigure(i, weight=1)
            ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack(pady=(12, 2))
            ctk.CTkLabel(card, text=str(val), font=ctk.CTkFont(size=28, weight="bold"), text_color=PRIMARY).pack(pady=(0, 12))

    def new_activity(self):
        messagebox.showinfo("Yeni Aktivite", "CRM aktivitesi formu acilacak.\n\nTurler:\n- Telefon Gorusmesi\n- Toplanti\n- Email\n- Ziyaret\n- Teklif")

    def report(self):
        messagebox.showinfo("CRM Raporu", "Musteri aktivite raporu hazirlaniyor...")
