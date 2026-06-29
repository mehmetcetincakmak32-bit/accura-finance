import customtkinter as ctk
from tkinter import messagebox, ttk
from datetime import datetime
import random

PRIMARY = "#1565c0"; SUCCESS = "#2e7d32"; WARNING = "#f57f17"
TEXT_DARK = "#1a1a2e"; TEXT_MUTED = "#6c757d"

class CRMFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="#f4f6f8")
        self.app = app
        self.db_manager = getattr(app, 'db_manager', None)
        self.activities = self._load_sample_activities()
        self.build_ui()

    def _load_sample_activities(self):
        return [
            {"Tarih": "20.06.2026", "Tur": "Telefon", "Musteri": "ABC Ltd.", "Konu": "Fiyat teklifi gorusmesi", "Durum": "Tamamlandi", "Takip": "-", "Sorumlu": "Ahmet"},
            {"Tarih": "22.06.2026", "Tur": "Toplanti", "Musteri": "XYZ A.S.", "Konu": "Yeni sozlesme", "Durum": "Planlandi", "Takip": "25.06.2026", "Sorumlu": "Ayse"},
            {"Tarih": "23.06.2026", "Tur": "Email", "Musteri": "DEF Tic.", "Konu": "Urun talebi", "Durum": "Beklemede", "Takip": "28.06.2026", "Sorumlu": "Mehmet"},
        ]

    def refresh_activities(self):
        for w in self.tab_aktiviteler.winfo_children():
            w.destroy()
        headers = ["Tarih", "Aktivite Turu", "Musteri", "Konu", "Durum", "Takip Tarihi", "Sorumlu"]
        for col, txt in enumerate(headers):
            ctk.CTkLabel(self.tab_aktiviteler, text=txt, font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).grid(row=0, column=col, padx=6, pady=6, sticky="w")
        for r, act in enumerate(self.activities, 1):
            vals = [act.get("Tarih", ""), act.get("Tur", ""), act.get("Musteri", ""), act.get("Konu", ""), act.get("Durum", ""), act.get("Takip", ""), act.get("Sorumlu", "")]
            for c, val in enumerate(vals):
                clr = {"Tamamlandi": SUCCESS, "Planlandi": PRIMARY, "Beklemede": WARNING}.get(val, TEXT_DARK)
                ctk.CTkLabel(self.tab_aktiviteler, text=val, font=ctk.CTkFont(size=11), text_color=clr).grid(row=r, column=c, padx=6, pady=4, sticky="w")

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

        self.refresh_activities()

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
        dialog = ctk.CTkToplevel(self)
        dialog.title("Yeni Aktivite")
        dialog.geometry("450x400")
        dialog.transient(self)
        dialog.grab_set()
        frame = ctk.CTkFrame(dialog, corner_radius=10)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        ctk.CTkLabel(frame, text="YENI AKTIVITE", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(0, 15))
        fields = {}
        for label in ["Musteri", "Konu", "Aktivite Turu", "Sorumlu"]:
            ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(fill="x", padx=10)
            e = ctk.CTkEntry(frame, height=32, font=ctk.CTkFont(size=13))
            e.pack(fill="x", padx=10, pady=(0, 10))
            fields[label] = e
        def save():
            self.activities.insert(0, {
                "Tarih": datetime.now().strftime("%d.%m.%Y"),
                "Tur": fields["Aktivite Turu"].get() or "Gorusme",
                "Musteri": fields["Musteri"].get() or "Bilinmiyor",
                "Konu": fields["Konu"].get() or "-",
                "Durum": "Beklemede",
                "Takip": "-",
                "Sorumlu": fields["Sorumlu"].get() or "Belirtilmemis"
            })
            self.refresh_activities()
            messagebox.showinfo("Basarili", "Aktivite eklendi!")
            dialog.destroy()
        ctk.CTkButton(frame, text="Kaydet", command=save, fg_color=SUCCESS, height=36).pack(pady=10)

    def report(self):
        messagebox.showinfo("CRM Raporu", "Musteri aktivite raporu hazirlaniyor...")
