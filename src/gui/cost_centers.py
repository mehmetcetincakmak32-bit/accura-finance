import customtkinter as ctk
from tkinter import messagebox, ttk
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PRIMARY = "#1565c0"; SUCCESS = "#2e7d32"; DANGER = "#c62828"; WARNING = "#f57f17"
TEXT_DARK = "#1a1a2e"; TEXT_MUTED = "#6c757d"; BORDER = "#e8eaed"

class CostCentersFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="#f4f6f8")
        self.app = app
        self.build_ui()

    def build_ui(self):
        header = ctk.CTkFrame(self, fg_color="white", corner_radius=10, height=50)
        header.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(header, text="Masraf Merkezleri Yonetimi", font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_DARK).pack(side="left", padx=16, pady=12)
        ctk.CTkButton(header, text="+ Yeni Merkez", width=110, height=32, fg_color=PRIMARY, corner_radius=6, command=self.new_center).pack(side="right", padx=4)
        ctk.CTkButton(header, text="Masraf Girisi", width=110, height=32, fg_color=WARNING, corner_radius=6, command=self.add_expense).pack(side="right", padx=4)

        main = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        main.pack(fill="both", expand=True)

        notebook = ttk.Notebook(main)
        notebook.pack(fill="both", expand=True, padx=12, pady=12)

        tabs = [
            ("Masraf Merkezleri", self.build_centers),
            ("Masraf Kayitlari", self.build_expenses),
            ("Butce Takibi", self.build_budget),
            ("Sube Bazinda", self.build_branch),
            ("Raporlar", self.build_reports),
        ]
        for name, builder in tabs:
            tab = ctk.CTkFrame(notebook, fg_color="transparent")
            notebook.add(tab, text=name)
            builder(tab)

        stats = ctk.CTkFrame(main, fg_color="transparent")
        stats.pack(fill="x", padx=12, pady=(0, 12))
        for label, val, color in [
            ("Toplam Merkez", "8", PRIMARY), ("Toplam Butce", "2,450,000 TL", SUCCESS),
            ("Harcanan", "1,280,000 TL", WARNING), ("Kalan", "1,170,000 TL", "#6a1b9a")
        ]:
            card = ctk.CTkFrame(stats, fg_color="#f8f9fa", corner_radius=8, border_width=1, border_color=BORDER)
            card.pack(side="left", fill="x", expand=True, padx=3)
            ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=12), text_color=TEXT_MUTED).pack(pady=(6, 0))
            ctk.CTkLabel(card, text=val, font=ctk.CTkFont(size=16, weight="bold"), text_color=color).pack(pady=(0, 6))

    def build_centers(self, parent):
        cols = ["Merkez Kodu", "Merkez Adi", "Ust Merkez", "Sube", "Butce", "Harcanan", "Kalan", "Durum"]
        for c, txt in enumerate(cols):
            ctk.CTkLabel(parent, text=txt, font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).grid(row=0, column=c, padx=5, pady=6, sticky="w")
        data = [
            ("M-001", "Genel Yonetim", "-", "Merkez", "500,000 TL", "320,000 TL", "180,000 TL", "Aktif"),
            ("M-002", "Pazarlama", "M-001", "Merkez", "350,000 TL", "210,000 TL", "140,000 TL", "Aktif"),
            ("M-003", "Lojistik", "M-001", "Merkez", "400,000 TL", "180,000 TL", "220,000 TL", "Aktif"),
            ("M-004", "Personel", "M-001", "Merkez", "600,000 TL", "450,000 TL", "150,000 TL", "Aktif"),
            ("SM-01", "Kadikoy Sube Gider", "-", "Kadikoy", "300,000 TL", "120,000 TL", "180,000 TL", "Aktif"),
        ]
        for r, row in enumerate(data, 1):
            for c, val in enumerate(row):
                clr = TEXT_DARK
                if c == 7:
                    clr = SUCCESS if val == "Aktif" else DANGER
                ctk.CTkLabel(parent, text=val, font=ctk.CTkFont(size=11), text_color=clr).grid(row=r, column=c, padx=5, pady=4, sticky="w")

    def build_expenses(self, parent):
        cols = ["Tarih", "Merkez", "Aciklama", "Tutar", "Belge No", "Kategori", "Ekleyen"]
        for c, txt in enumerate(cols):
            ctk.CTkLabel(parent, text=txt, font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).grid(row=0, column=c, padx=5, pady=6, sticky="w")
        data = [
            ("20.06.2026", "Genel Yonetim", "Kirtasiye gideri", "2,450 TL", "FAT-001", "Ofis", "Admin"),
            ("21.06.2026", "Pazarlama", "Reklam harcamasi", "15,000 TL", "FAT-002", "Reklam", "Admin"),
            ("22.06.2026", "Lojistik", "Nakliye bedeli", "4,800 TL", "FAT-003", "Nakliye", "Admin"),
        ]
        for r, row in enumerate(data, 1):
            for c, val in enumerate(row):
                ctk.CTkLabel(parent, text=val, font=ctk.CTkFont(size=11), text_color=TEXT_DARK).grid(row=r, column=c, padx=5, pady=4, sticky="w")

    def build_budget(self, parent):
        cols = ["Merkez", "Yillik Butce", "Ocak", "Subat", "Mart", "Nisan", "Mayis", "Haziran", "Kullanilan %"]
        for c, txt in enumerate(cols):
            ctk.CTkLabel(parent, text=txt, font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).grid(row=0, column=c, padx=4, pady=6, sticky="w")
        data = [
            ("Genel Yonetim", "1,000,000 TL", "85,000", "82,000", "90,000", "78,000", "95,000", "88,000", "%52"),
            ("Pazarlama", "700,000 TL", "55,000", "48,000", "62,000", "58,000", "70,000", "65,000", "%60"),
        ]
        for r, row in enumerate(data, 1):
            for c, val in enumerate(row):
                clr = DANGER if c == 8 and int(val.replace("%", "")) > 75 else SUCCESS if c == 8 and int(val.replace("%", "")) < 40 else TEXT_DARK
                ctk.CTkLabel(parent, text=val, font=ctk.CTkFont(size=11), text_color=clr).grid(row=r, column=c, padx=4, pady=4, sticky="w")

    def build_branch(self, parent):
        cols = ["Sube", "Merkez Sayisi", "Toplam Butce", "Harcanan", "Kalan", "Verim %"]
        for c, txt in enumerate(cols):
            ctk.CTkLabel(parent, text=txt, font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).grid(row=0, column=c, padx=5, pady=6, sticky="w")
        data = [
            ("Merkez Sube", "4", "1,850,000 TL", "1,160,000 TL", "690,000 TL", "%63"),
            ("Kadikoy Sube", "2", "300,000 TL", "120,000 TL", "180,000 TL", "%40"),
            ("Ankara Sube", "2", "300,000 TL", "0 TL", "300,000 TL", "%0"),
        ]
        for r, row in enumerate(data, 1):
            for c, val in enumerate(row):
                clr = DANGER if c == 5 and int(val.replace("%", "")) > 80 else SUCCESS if c == 5 and int(val.replace("%", "")) < 30 else TEXT_DARK
                ctk.CTkLabel(parent, text=val, font=ctk.CTkFont(size=11), text_color=clr).grid(row=r, column=c, padx=5, pady=4, sticky="w")

    def build_reports(self, parent):
        ctk.CTkLabel(parent, text="Masraf Merkezi Raporlari", font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_DARK).pack(anchor="w", padx=12, pady=8)
        reports = [
            "Masraf Merkezi Detay Raporu", "Butce Karsilastirma Raporu",
            "Sube Bazinda Masraf Raporu", "Aylik Masraf Raporu",
            "Yillik Butce Gerceklestirme Raporu",
            "En Yuksek Masraf Merkezleri Analizi",
        ]
        for rep in reports:
            btn = ctk.CTkButton(parent, text=rep, width=350, height=30, anchor="w", fg_color="transparent",
                                text_color=TEXT_DARK, hover_color="#e8eaf6", corner_radius=6,
                                font=ctk.CTkFont(size=11))
            btn.pack(pady=1)

    def new_center(self):
        win = ctk.CTkToplevel(self)
        win.title("Yeni Masraf Merkezi")
        win.geometry("400x300")
        win.transient(self.master)
        win.grab_set()
        ctk.CTkLabel(win, text="Yeni Masraf Merkezi", font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_DARK).pack(pady=12)
        for lbl in ["Merkez Kodu:", "Merkez Adi:", "Ust Merkez:", "Sube:", "Butce:", "Yonetici:"]:
            f = ctk.CTkFrame(win, fg_color="transparent")
            f.pack(fill="x", padx=20, pady=3)
            ctk.CTkLabel(f, text=lbl, width=100, anchor="w", font=ctk.CTkFont(size=11), text_color=TEXT_DARK).pack(side="left")
            if lbl == "Ust Merkez:":
                ctk.CTkOptionMenu(f, values=["- (Kok)", "Genel Yonetim", "Pazarlama", "Lojistik"], height=28).pack(side="left", fill="x", expand=True)
            elif lbl == "Sube:":
                ctk.CTkOptionMenu(f, values=["Merkez", "Kadikoy", "Ankara"], height=28).pack(side="left", fill="x", expand=True)
            else:
                ctk.CTkEntry(f, height=28).pack(side="left", fill="x", expand=True)
        ctk.CTkButton(win, text="Kaydet", width=120, height=36, fg_color=SUCCESS, corner_radius=6).pack(pady=16)

    def add_expense(self):
        win = ctk.CTkToplevel(self)
        win.title("Masraf Girisi")
        win.geometry("400x300")
        win.transient(self.master)
        win.grab_set()
        ctk.CTkLabel(win, text="Yeni Masraf Kaydi", font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_DARK).pack(pady=12)
        for lbl in ["Tarih:", "Masraf Merkezi:", "Tutar:", "Aciklama:", "Belge No:", "Kategori:"]:
            f = ctk.CTkFrame(win, fg_color="transparent")
            f.pack(fill="x", padx=20, pady=3)
            ctk.CTkLabel(f, text=lbl, width=110, anchor="w", font=ctk.CTkFont(size=11), text_color=TEXT_DARK).pack(side="left")
            if lbl in ["Masraf Merkezi:", "Kategori:"]:
                vals = ["Genel Yonetim", "Pazarlama", "Lojistik"] if lbl == "Masraf Merkezi:" else ["Ofis", "Reklam", "Nakliye", "Personel", "Diger"]
                ctk.CTkOptionMenu(f, values=vals, height=28).pack(side="left", fill="x", expand=True)
            else:
                ctk.CTkEntry(f, height=28).pack(side="left", fill="x", expand=True)
        ctk.CTkButton(win, text="Kaydet", width=120, height=36, fg_color=WARNING, corner_radius=6).pack(pady=16)
