import customtkinter as ctk
from tkinter import messagebox, ttk
import sys, os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PRIMARY = "#1565c0"; SUCCESS = "#2e7d32"; DANGER = "#c62828"; WARNING = "#f57f17"
TEXT_DARK = "#1a1a2e"; TEXT_MUTED = "#6c757d"; BORDER = "#e8eaed"

class OrdersFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="#f4f6f8")
        self.app = app
        self.build_ui()

    def build_ui(self):
        header = ctk.CTkFrame(self, fg_color="white", corner_radius=10, height=50)
        header.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(header, text="Musteri Siparis Yonetimi", font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_DARK).pack(side="left", padx=16, pady=12)
        ctk.CTkButton(header, text="+ Yeni Siparis", width=110, height=32, fg_color=PRIMARY, corner_radius=6, command=self.new_order).pack(side="right", padx=16)

        main = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        main.pack(fill="both", expand=True)

        notebook = ttk.Notebook(main)
        notebook.pack(fill="both", expand=True, padx=12, pady=12)

        tabs = [
            ("Bekleyen Siparisler", self.build_pending),
            ("Hazirlanan Siparisler", self.build_preparing),
            ("Kargoya Verilenler", self.build_shipped),
            ("Teslim Edilenler", self.build_delivered),
            ("Iptal Edilenler", self.build_cancelled),
            ("Tum Siparisler", self.build_all),
        ]
        for tab_name, builder in tabs:
            tab = ctk.CTkFrame(notebook, fg_color="transparent")
            notebook.add(tab, text=tab_name)
            builder(tab)

        stats = ctk.CTkFrame(main, fg_color="transparent")
        stats.pack(fill="x", padx=12, pady=(0, 12))
        data = [("Bekleyen", "12", WARNING), ("Hazirlanan", "8", PRIMARY), ("Kargoda", "15", "#6a1b9a"),
                ("Teslim", "124", SUCCESS), ("Iptal", "3", DANGER), ("Bu Ay", "162", TEXT_DARK)]
        for label, val, color in data:
            card = ctk.CTkFrame(stats, fg_color="#f8f9fa", corner_radius=8, border_width=1, border_color=BORDER)
            card.pack(side="left", fill="x", expand=True, padx=3)
            ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=12), text_color=TEXT_MUTED).pack(pady=(6, 0))
            ctk.CTkLabel(card, text=val, font=ctk.CTkFont(size=16, weight="bold"), text_color=color).pack(pady=(0, 6))

    def build_table(self, parent, data):
        cols = ["Siparis No", "Tarih", "Musteri", "Urun Sayisi", "Toplam", "Teslimat", "Odeme", "Durum"]
        for c, txt in enumerate(cols):
            ctk.CTkLabel(parent, text=txt, font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).grid(row=0, column=c, padx=5, pady=6, sticky="w")
        for r, row in enumerate(data, 1):
            for c, val in enumerate(row):
                clr = TEXT_DARK
                if c == 7:
                    clr = {"Beklemede": WARNING, "Hazirlaniyor": PRIMARY, "Kargoya Verildi": "#6a1b9a",
                           "Teslim Edildi": SUCCESS, "Iptal": DANGER}.get(val, TEXT_DARK)
                if c == 6:
                    clr = {"Odendi": SUCCESS, "Bekliyor": WARNING}.get(val, TEXT_DARK)
                ctk.CTkLabel(parent, text=val, font=ctk.CTkFont(size=11), text_color=clr).grid(row=r, column=c, padx=5, pady=4, sticky="w")

    def build_pending(self, parent):
        data = [("SIP-001", "20.06.2026", "ABC Ltd.", "5", "2,450 TL", "25.06.2026", "Bekliyor", "Beklemede"),
                ("SIP-002", "21.06.2026", "XYZ A.S.", "3", "1,280 TL", "28.06.2026", "Odendi", "Beklemede")]
        self.build_table(parent, data)

    def build_preparing(self, parent):
        data = [("SIP-003", "19.06.2026", "DEF Tic.", "8", "4,560 TL", "23.06.2026", "Odendi", "Hazirlaniyor")]
        self.build_table(parent, data)

    def build_shipped(self, parent):
        data = [("SIP-004", "18.06.2026", "MNO Ltd.", "2", "890 TL", "22.06.2026", "Odendi", "Kargoya Verildi")]
        self.build_table(parent, data)

    def build_delivered(self, parent):
        data = [("SIP-005", "15.06.2026", "PQR A.S.", "4", "3,200 TL", "19.06.2026", "Odendi", "Teslim Edildi")]
        self.build_table(parent, data)

    def build_cancelled(self, parent):
        data = [("SIP-006", "10.06.2026", "RST Ltd.", "1", "450 TL", "-", "Iade", "Iptal")]
        self.build_table(parent, data)

    def build_all(self, parent):
        data = [
            ("SIP-001", "20.06.2026", "ABC Ltd.", "5", "2,450 TL", "25.06.2026", "Bekliyor", "Beklemede"),
            ("SIP-003", "19.06.2026", "DEF Tic.", "8", "4,560 TL", "23.06.2026", "Odendi", "Hazirlaniyor"),
            ("SIP-004", "18.06.2026", "MNO Ltd.", "2", "890 TL", "22.06.2026", "Odendi", "Kargoya Verildi"),
            ("SIP-005", "15.06.2026", "PQR A.S.", "4", "3,200 TL", "19.06.2026", "Odendi", "Teslim Edildi"),
        ]
        self.build_table(parent, data)

    def new_order(self):
        win = ctk.CTkToplevel(self)
        win.title("Yeni Musteri Siparisi")
        win.geometry("500x400")
        win.transient(self.master)
        win.grab_set()
        ctk.CTkLabel(win, text="Yeni Siparis Formu", font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_DARK).pack(pady=12)

        f = ctk.CTkFrame(win, fg_color="transparent")
        f.pack(fill="x", padx=20, pady=5)
        for lbl in ["Musteri:", "Siparis Tarihi:", "Teslimat Tarihi:", "Odeme Turu:", "Teslimat Adresi:"]:
            r = ctk.CTkFrame(f, fg_color="transparent")
            r.pack(fill="x", pady=2)
            ctk.CTkLabel(r, text=lbl, width=120, anchor="w", font=ctk.CTkFont(size=11), text_color=TEXT_DARK).pack(side="left")
            if lbl == "Odeme Turu:":
                ctk.CTkOptionMenu(r, values=["Nakit", "Kredi Karti", "Havale/EFT", "Cek"], height=28).pack(side="left", fill="x", expand=True)
            elif lbl == "Teslimat Adresi:":
                ctk.CTkEntry(r, height=28).pack(side="left", fill="x", expand=True)
            else:
                ctk.CTkEntry(r, height=28).pack(side="left", fill="x", expand=True)

        ctk.CTkButton(win, text="Siparisi Olustur", width=160, height=36, fg_color=SUCCESS,
                       corner_radius=6, command=lambda: self.save_order(win)).pack(pady=16)

    def save_order(self, win):
        messagebox.showinfo("Basarili", "Siparis basariyla olusturuldu.", parent=win)
        win.destroy()
