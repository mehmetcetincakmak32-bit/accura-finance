import customtkinter as ctk
from tkinter import messagebox, ttk
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PRIMARY = "#1565c0"; SUCCESS = "#2e7d32"; DANGER = "#c62828"
TEXT_DARK = "#1a1a2e"; TEXT_MUTED = "#6c757d"; BORDER = "#e8eaed"

class MarketplaceFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="#f4f6f8")
        self.app = app
        self.build_ui()

    def build_ui(self):
        header = ctk.CTkFrame(self, fg_color="white", corner_radius=10, height=50)
        header.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(header, text="Pazaryeri & E-Ticaret Entegrasyonu", font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_DARK).pack(side="left", padx=16, pady=12)
        ctk.CTkButton(header, text="+ Urun Ekle", width=100, height=32, fg_color=PRIMARY, corner_radius=6, command=self.add_listing).pack(side="right", padx=4)
        ctk.CTkButton(header, text="Senkronize Et", width=120, height=32, fg_color=SUCCESS, corner_radius=6, command=self.sync).pack(side="right", padx=4)

        main = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        main.pack(fill="both", expand=True)

        notebook = ttk.Notebook(main)
        notebook.pack(fill="both", expand=True, padx=12, pady=12)

        platforms = [
            ("Ideasoft Entegrasyonu", self.build_ideasoft),
            ("Trendyol", self.build_trendyol),
            ("Hepsiburada", self.build_hb),
            ("N11", self.build_n11),
            ("Amazon", self.build_amazon),
            ("Tum Urunler", self.build_all),
        ]
        for name, builder in platforms:
            tab = ctk.CTkFrame(notebook, fg_color="transparent")
            notebook.add(tab, text=name)
            builder(tab)

        stats_frame = ctk.CTkFrame(main, fg_color="transparent")
        stats_frame.pack(fill="x", padx=12, pady=(0, 12))
        for label, val, color in [
            ("Toplam Kayit", "156", PRIMARY), ("Aktif", "142", SUCCESS),
            ("Senkronize", "150", "#6a1b9a"), ("Hatali", "6", DANGER)
        ]:
            card = ctk.CTkFrame(stats_frame, fg_color="#f8f9fa", corner_radius=8, border_width=1, border_color=BORDER)
            card.pack(side="left", fill="x", expand=True, padx=3)
            ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=12), text_color=TEXT_MUTED).pack(pady=(6, 0))
            ctk.CTkLabel(card, text=val, font=ctk.CTkFont(size=16, weight="bold"), text_color=color).pack(pady=(0, 6))

    def build_table(self, parent, platform):
        cols = ["Urun Kodu", "Urun Adi", "Platform", "Platform Fiyati", "Stok", "Durum", "Son Senkron"]
        for c, txt in enumerate(cols):
            ctk.CTkLabel(parent, text=txt, font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).grid(row=0, column=c, padx=5, pady=6, sticky="w")
        samples = [
            ("STK-001", "Sut 1L", platform, "15.90 TL", "245", "Aktif", "20.06.2026 14:30"),
            ("STK-002", "Ekmek", platform, "6.50 TL", "500", "Aktif", "20.06.2026 14:30"),
            ("STK-003", "Yogurt 1kg", platform, "22.50 TL", "180", "Aktif", "20.06.2026 14:30"),
        ]
        for r, row in enumerate(samples, 1):
            for c, val in enumerate(row):
                clr = SUCCESS if c == 5 and val == "Aktif" else TEXT_DARK
                ctk.CTkLabel(parent, text=val, font=ctk.CTkFont(size=11), text_color=clr).grid(row=r, column=c, padx=5, pady=4, sticky="w")

    def build_ideasoft(self, p): self.build_table(p, "Ideasoft")
    def build_trendyol(self, p): self.build_table(p, "Trendyol")
    def build_hb(self, p): self.build_table(p, "Hepsiburada")
    def build_n11(self, p): self.build_table(p, "N11")
    def build_amazon(self, p): self.build_table(p, "Amazon")
    def build_all(self, p):
        cols = ["Urun Kodu", "Urun Adi", "Platform", "Platform Fiyati", "Stok", "Durum", "Son Senkron"]
        for c, txt in enumerate(cols):
            ctk.CTkLabel(p, text=txt, font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).grid(row=0, column=c, padx=5, pady=6, sticky="w")
        data = [
            ("STK-001", "Sut 1L", "Ideasoft", "15.90 TL", "245", "Aktif", "20.06.2026"),
            ("STK-001", "Sut 1L", "Trendyol", "16.90 TL", "245", "Aktif", "20.06.2026"),
            ("STK-001", "Sut 1L", "Hepsiburada", "17.50 TL", "245", "Aktif", "20.06.2026"),
            ("STK-002", "Ekmek", "Ideasoft", "6.50 TL", "500", "Aktif", "20.06.2026"),
            ("STK-003", "Yogurt 1kg", "N11", "23.90 TL", "180", "Hatali", "19.06.2026"),
        ]
        for r, row in enumerate(data, 1):
            for c, val in enumerate(row):
                clr = SUCCESS if c == 5 and val == "Aktif" else DANGER if c == 5 and val == "Hatali" else TEXT_DARK
                ctk.CTkLabel(p, text=val, font=ctk.CTkFont(size=11), text_color=clr).grid(row=r, column=c, padx=5, pady=4, sticky="w")

    def add_listing(self):
        win = ctk.CTkToplevel(self)
        win.title("Pazaryeri Urun Ekle")
        win.geometry("400x300")
        win.transient(self.master)
        win.grab_set()
        ctk.CTkLabel(win, text="Yeni Pazaryeri Kaydi", font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_DARK).pack(pady=12)
        for lbl in ["Urun Kodu:", "Platform:", "Platform Fiyati:", "Stok Adeti:"]:
            f = ctk.CTkFrame(win, fg_color="transparent")
            f.pack(fill="x", padx=20, pady=3)
            ctk.CTkLabel(f, text=lbl, width=110, anchor="w", font=ctk.CTkFont(size=11), text_color=TEXT_DARK).pack(side="left")
            if lbl == "Platform:":
                ctk.CTkOptionMenu(f, values=["Ideasoft", "Trendyol", "Hepsiburada", "N11", "Amazon"], height=28).pack(side="left", fill="x", expand=True)
            else:
                ctk.CTkEntry(f, height=28).pack(side="left", fill="x", expand=True)
        ctk.CTkButton(win, text="Kaydet", width=120, height=36, fg_color=SUCCESS, corner_radius=6).pack(pady=16)

    def sync(self):
        messagebox.showinfo("Senkronizasyon", "Tum platformlar ile senkronizasyon baslatildi.\n\nIdeasoft: Basarili (45 urun)\nTrendyol: Basarili (38 urun)\nHepsiburada: Basarili (42 urun)\nN11: Basarili (28 urun)\nAmazon: Basarili (15 urun)")
