import customtkinter as ctk
from tkinter import messagebox, ttk
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PRIMARY = "#1565c0"; TEXT_DARK = "#1a1a2e"; TEXT_MUTED = "#6c757d"; BORDER = "#e8eaed"

class BarcodeFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="#f4f6f8")
        self.app = app
        self.build_ui()

    def build_ui(self):
        header = ctk.CTkFrame(self, fg_color="white", corner_radius=10, height=50)
        header.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(header, text="Barkod & Etiket Islemi", font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_DARK).pack(side="left", padx=16, pady=12)

        main = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        main.pack(fill="both", expand=True)

        notebook = ttk.Notebook(main)
        notebook.pack(fill="both", expand=True, padx=12, pady=12)

        tabs = [
            ("Barkod Basim", self.build_print),
            ("Etiket Tasarim", self.build_design),
            ("Barkod Sorgulama", self.build_query),
            ("Barkod Sablonlari", self.build_templates),
        ]
        for tab_name, builder in tabs:
            tab = ctk.CTkFrame(notebook, fg_color="transparent")
            notebook.add(tab, text=tab_name)
            builder(tab)

    def build_print(self, parent):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", pady=12, padx=12)
        ctk.CTkLabel(f, text="Barkod Numarasi / Urun Kodu:", font=ctk.CTkFont(size=12), text_color=TEXT_DARK).pack(anchor="w")
        ctk.CTkEntry(f, height=32, placeholder_text="Barkod okutun veya urun kodu girin...").pack(fill="x", pady=4)
        ctk.CTkButton(f, text="Barkodu Ara", width=120, height=32, fg_color=PRIMARY, corner_radius=6).pack(anchor="w", pady=4)

        info = ctk.CTkFrame(f, fg_color="#f8f9fa", corner_radius=8, border_width=1, border_color=BORDER)
        info.pack(fill="x", pady=8)
        fields = ["Urun Adi:", "Stok Kodu:", "Fiyat:", "Barkod:"]
        for i, lbl in enumerate(fields):
            ctk.CTkLabel(info, text=lbl, font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).grid(row=i, column=0, sticky="w", padx=12, pady=3)
            ctk.CTkLabel(info, text="---", font=ctk.CTkFont(size=11), text_color=TEXT_DARK).grid(row=i, column=1, sticky="w", padx=12, pady=3)

        ctk.CTkFrame(parent, fg_color="transparent").pack(fill="x", padx=12)
        ctk.CTkLabel(parent, text="Basim Ayarlari", font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_DARK).pack(anchor="w", padx=12, pady=(8, 4))

        f2 = ctk.CTkFrame(parent, fg_color="transparent")
        f2.pack(fill="x", padx=12)
        settings = [("Etiket Boyutu:", "5cm x 3cm"), ("Yazici:", "Zebra ZD420"), ("Adet:", "1"), ("Kopya:", "1")]
        for i, (lbl, val) in enumerate(settings):
            ctk.CTkLabel(f2, text=lbl, font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).grid(row=i, column=0, sticky="w", pady=2)
            ctk.CTkLabel(f2, text=val, font=ctk.CTkFont(size=11), text_color=TEXT_DARK).grid(row=i, column=1, sticky="w", padx=12, pady=2)

        ctk.CTkButton(parent, text="Barkod Etiketi Bas", width=160, height=36, fg_color=PRIMARY,
                       corner_radius=6, command=lambda: messagebox.showinfo("Basim", "Barkod etiketi yaziciya gonderildi.")).pack(pady=12)

    def build_design(self, parent):
        ctk.CTkLabel(parent, text="Etiket Tasarim Editoru", font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_DARK).pack(anchor="w", padx=12, pady=8)
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=12, pady=4)
        fields = [("Etiket Genislik (mm):", "50"), ("Etiket Yukseklik (mm):", "30"),
                  ("Yazici:", "Zebra ZD420"), ("Kenar Boslugu:", "2 mm")]
        for i, (lbl, val) in enumerate(fields):
            ctk.CTkLabel(f, text=lbl, font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).grid(row=i, column=0, sticky="w", pady=3)
            e = ctk.CTkEntry(f, height=28, width=120)
            e.insert(0, val)
            e.grid(row=i, column=1, sticky="w", padx=12, pady=3)

        ctk.CTkLabel(parent, text="Etiket Uzerinde Gosterilecek Alanlar:", font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_DARK).pack(anchor="w", padx=12, pady=(8, 4))

        design_frame = ctk.CTkFrame(parent, fg_color="transparent")
        design_frame.pack(fill="x", padx=12)
        design_fields = [
            ("Urun Adi", True), ("Barkod", True), ("Fiyat", True),
            ("Stok Kodu", True), ("Kategori", False), ("KDV Orani", False),
        ]
        for lbl, checked in design_fields:
            var = ctk.BooleanVar(value=checked)
            ctk.CTkCheckBox(design_frame, text=lbl, variable=var, font=ctk.CTkFont(size=11)).pack(anchor="w", pady=1)

        ctk.CTkButton(parent, text="Tasarimi Kaydet", width=140, height=36, fg_color=PRIMARY,
                       corner_radius=6, command=lambda: messagebox.showinfo("Kayit", "Etiket sablonu kaydedildi.")).pack(pady=12)

    def build_query(self, parent):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=12, pady=12)
        ctk.CTkLabel(f, text="Barkod / Urun Kodu:", font=ctk.CTkFont(size=12), text_color=TEXT_DARK).pack(anchor="w")
        h = ctk.CTkFrame(f, fg_color="transparent")
        h.pack(fill="x", pady=4)
        ctk.CTkEntry(h, height=32, placeholder_text="Barkod numarasini girin veya okutun...").pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(h, text="Sorgula", width=100, height=32, fg_color=PRIMARY, corner_radius=6).pack(side="right")

        info = ctk.CTkFrame(f, fg_color="#f8f9fa", corner_radius=8, border_width=1, border_color=BORDER)
        info.pack(fill="x", pady=12)
        data = [("Urun Kodu", "STK-001"), ("Urun Adi", "Sut 1L"), ("Barkod", "8691234567890"),
                ("Fiyat", "12.50 TL"), ("Stok", "245"), ("KDV", "%18")]
        for i, (lbl, val) in enumerate(data):
            ctk.CTkLabel(info, text=lbl + ":", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).grid(row=i, column=0, sticky="w", padx=12, pady=2)
            ctk.CTkLabel(info, text=val, font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_DARK).grid(row=i, column=1, sticky="w", padx=12, pady=2)

    def build_templates(self, parent):
        cols = ["Sablon Adi", "Boyut", "Varsayilan", "Yazici", "Olusturma Tarihi"]
        for c, txt in enumerate(cols):
            ctk.CTkLabel(parent, text=txt, font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).grid(row=0, column=c, padx=8, pady=6, sticky="w")
        data = [("Standart Etiket", "5x3 cm", "Evet", "Zebra ZD420", "01.06.2026"),
                ("Kucuk Urun", "3x2 cm", "Hayir", "Zebra ZD420", "05.06.2026"),
                ("Fiyat Etiketi", "8x4 cm", "Hayir", "TSC TTP-244", "10.06.2026")]
        for r, row in enumerate(data, 1):
            for c, val in enumerate(row):
                ctk.CTkLabel(parent, text=val, font=ctk.CTkFont(size=11), text_color=TEXT_DARK).grid(row=r, column=c, padx=8, pady=4, sticky="w")
