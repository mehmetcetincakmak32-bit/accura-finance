import customtkinter as ctk
from tkinter import messagebox, ttk
import sys, os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PRIMARY = "#1565c0"; SUCCESS = "#2e7d32"; DANGER = "#c62828"; WARNING = "#f57f17"
TEXT_DARK = "#1a1a2e"; TEXT_MUTED = "#6c757d"; BORDER = "#e8eaed"

class EInvoiceFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="#f4f6f8")
        self.app = app
        self.build_ui()

    def build_ui(self):
        header = ctk.CTkFrame(self, fg_color="white", corner_radius=10, height=50)
        header.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(header, text="e-Fatura / e-Defter / GIB Entegrasyonu", font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_DARK).pack(side="left", padx=16, pady=12)
        ctk.CTkButton(header, text="Gonder", width=80, height=32, fg_color=PRIMARY, corner_radius=6).pack(side="right", padx=4)
        ctk.CTkButton(header, text="GIB'den Sorgula", width=110, height=32, fg_color=SUCCESS, corner_radius=6).pack(side="right", padx=4)

        main = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        main.pack(fill="both", expand=True)

        notebook = ttk.Notebook(main)
        notebook.pack(fill="both", expand=True, padx=12, pady=12)

        tabs = [
            ("e-Faturalar", self.build_einvoice),
            ("e-Arsiv", self.build_earchive),
            ("e-Defter", self.build_eledger),
            ("e-Irsaliye", self.build_edespatch),
            ("GIB Durum", self.build_gib),
            ("Raporlar", self.build_reports),
        ]
        for name, builder in tabs:
            tab = ctk.CTkFrame(notebook, fg_color="transparent")
            notebook.add(tab, text=name)
            builder(tab)

    def build_table(self, parent, headers, data, status_col=None):
        for c, txt in enumerate(headers):
            ctk.CTkLabel(parent, text=txt, font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).grid(row=0, column=c, padx=5, pady=6, sticky="w")
        for r, row in enumerate(data, 1):
            for c, val in enumerate(row):
                clr = TEXT_DARK
                if status_col is not None and c == status_col:
                    clr = {"Basarili": SUCCESS, "Basarisiz": DANGER, "Beklemede": WARNING,
                           "Taslak": TEXT_MUTED, "Gonderildi": PRIMARY}.get(val, TEXT_DARK)
                ctk.CTkLabel(parent, text=val, font=ctk.CTkFont(size=11), text_color=clr).grid(row=r, column=c, padx=5, pady=4, sticky="w")

    def build_einvoice(self, parent):
        headers = ["Fatura No", "UUID", "Tarih", "Musteri", "Tutar", "Profil", "Durum", "GIB Kodu", "Gonderim"]
        data = [
            ("EFT-2024-001", "a1b2c3d4-...", "20.06.2026", "ABC Ltd.", "4,500.00 TL", "TICARI", "Basarili", "GIB-001", "Gonderildi"),
            ("EFT-2024-002", "e5f6g7h8-...", "21.06.2026", "XYZ A.S.", "12,800.00 TL", "TEMEL", "Basarili", "GIB-002", "Gonderildi"),
            ("EFT-2024-003", "", "22.06.2026", "DEF Tic.", "2,350.00 TL", "TICARI", "Taslak", "", "Hazirlaniyor"),
        ]
        self.build_table(parent, headers, data, status_col=6)

    def build_earchive(self, parent):
        headers = ["Fatura No", "Tarih", "Musteri", "Tutar", "Durum", "GIB Kodu"]
        data = [
            ("EARS-2024-001", "20.06.2026", "Musteri A", "850.00 TL", "Basarili", "GIB-003"),
            ("EARS-2024-002", "21.06.2026", "Musteri B", "1,200.00 TL", "Basarili", "GIB-004"),
            ("EARS-2024-003", "22.06.2026", "Musteri C", "450.00 TL", "Beklemede", ""),
        ]
        self.build_table(parent, headers, data, status_col=4)

    def build_eledger(self, parent):
        ctk.CTkLabel(parent, text="e-Defter Donemleri", font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_DARK).pack(anchor="w", padx=12, pady=8)
        headers = ["Donem", "Defter Turu", "Olusturma", "Durum", "GIB Kodu", "Indir"]
        data = [
            ("2026/06", "Yevmiye Defteri", "25.06.2026", "Hazirlaniyor", "", "Indir"),
            ("2026/05", "Yevmiye Defteri", "10.06.2026", "Basarili", "GIB-100", "Indir"),
            ("2026/05", "Kebir Defteri", "10.06.2026", "Basarili", "GIB-101", "Indir"),
            ("2026/04", "Yevmiye Defteri", "05.05.2026", "Basarili", "GIB-098", "Indir"),
        ]
        self.build_table(parent, headers, data, status_col=3)

    def build_edespatch(self, parent):
        headers = ["Irsaliye No", "Tarih", "Musteri", "Tutar", "Durum", "GIB Kodu"]
        data = [("EIR-2024-001", "20.06.2026", "ABC Ltd.", "4,500.00 TL", "Basarili", "GIB-005")]
        self.build_table(parent, headers, data, status_col=4)

    def build_gib(self, parent):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=12, pady=12)
        ctk.CTkLabel(f, text="GIB Entegrasyon Bilgileri", font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_DARK).pack(anchor="w")

        statuses = [
            ("GIB Baglantisi:", "Aktif", SUCCESS),
            ("e-Fatura:", "Aktif (TEMEL + TICARI)", SUCCESS),
            ("e-Arsiv:", "Aktif", SUCCESS),
            ("e-Defter:", "Aktif", SUCCESS),
            ("e-Irsaliye:", "Aktif", SUCCESS),
            ("Son Senkron:", datetime.now().strftime("%d.%m.%Y %H:%M"), PRIMARY),
        ]
        for lbl, val, color in statuses:
            r = ctk.CTkFrame(f, fg_color="#f8f9fa", corner_radius=6)
            r.pack(fill="x", pady=2)
            ctk.CTkLabel(r, text=lbl, width=150, anchor="w", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack(side="left", padx=12, pady=4)
            ctk.CTkLabel(r, text=val, font=ctk.CTkFont(size=11, weight="bold"), text_color=color).pack(side="left", padx=5, pady=4)

        ctk.CTkButton(f, text="GIB ile Senkronize Et", width=180, height=36, fg_color=SUCCESS,
                       corner_radius=6, command=lambda: messagebox.showinfo("GIB", "GIB ile senkronizasyon baslatildi.\nFaturalar ve defterler kontrol ediliyor...")).pack(pady=12)

    def build_reports(self, parent):
        ctk.CTkLabel(parent, text="e-Fatura / e-Defter Raporlari", font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_DARK).pack(anchor="w", padx=12, pady=8)
        reports = [
            "Aylik e-Fatura Gonderim Raporu", "e-Defter Berat Raporu",
            "GIB Hata Log Raporu", "e-Arsiv Raporu",
            "Donemsel e-Defter Durum Raporu",
        ]
        for rep in reports:
            btn = ctk.CTkButton(parent, text=rep, width=350, height=30, anchor="w", fg_color="transparent",
                                text_color=TEXT_DARK, hover_color="#e8eaf6", corner_radius=6,
                                font=ctk.CTkFont(size=11))
            btn.pack(pady=1)
