import customtkinter as ctk
from tkinter import messagebox, ttk
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PRIMARY = "#1565c0"; TEXT_DARK = "#1a1a2e"; TEXT_MUTED = "#6c757d"; BORDER = "#e8eaed"

class PriceGroupsFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="#f4f6f8")
        self.app = app
        self.build_ui()

    def build_ui(self):
        header = ctk.CTkFrame(self, fg_color="white", corner_radius=10, height=50)
        header.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(header, text="Fiyat Gruplari Yonetimi", font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_DARK).pack(side="left", padx=16, pady=12)
        ctk.CTkButton(header, text="+ Yeni Grup", fg_color=PRIMARY, corner_radius=6, command=self.new_group).pack(side="right", padx=16)

        main = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        main.pack(fill="both", expand=True)

        notebook = ttk.Notebook(main)
        notebook.pack(fill="both", expand=True, padx=12, pady=12)

        self.tab_gruplar = ctk.CTkFrame(notebook, fg_color="transparent")
        self.tab_urunler = ctk.CTkFrame(notebook, fg_color="transparent")
        notebook.add(self.tab_gruplar, text="Fiyat Gruplari")
        notebook.add(self.tab_urunler, text="Grup Urunleri")

        for col, txt in [(0, "Grup Kodu"), (1, "Grup Adi"), (2, "Iskonto Orani"), (3, "Kar Marjı"), (4, "Urun Sayisi"), (5, "Durum")]:
            ctk.CTkLabel(self.tab_gruplar, text=txt, font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).grid(row=0, column=col, padx=6, pady=6, sticky="w")

        groups = [("GRP-001", "300 Ml Meyve Sulari", "%5", "%15", "12", "Aktif"),
                  ("GRP-002", "1 Lt Icecekler", "%8", "%20", "8", "Aktif"),
                  ("GRP-003", "Atistirmalik", "%3", "%25", "25", "Aktif"),
                  ("GRP-004", "Temizlik Urunleri", "%10", "%18", "15", "Pasif")]
        for r, row in enumerate(groups, 1):
            for c, val in enumerate(row):
                clr = TEXT_DARK
                if c == 5:
                    clr = "#2e7d32" if val == "Aktif" else "#c62828"
                ctk.CTkLabel(self.tab_gruplar, text=val, font=ctk.CTkFont(size=11), text_color=clr).grid(row=r, column=c, padx=6, pady=4, sticky="w")

        for col, txt in [(0, "Grup"), (1, "Stok Kodu"), (2, "Urun Adi"), (3, "Taban Fiyat"), (4, "Grup Fiyati"), (5, "Fark %")]:
            ctk.CTkLabel(self.tab_urunler, text=txt, font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).grid(row=0, column=col, padx=6, pady=6, sticky="w")
        items = [("300 Ml Meyve Sulari", "STK-001", "Portakal Suyu 300ml", "12.50 TL", "14.38 TL", "+%15"),
                 ("300 Ml Meyve Sulari", "STK-002", "Elma Suyu 300ml", "11.00 TL", "12.65 TL", "+%15")]
        for r, row in enumerate(items, 1):
            for c, val in enumerate(row):
                ctk.CTkLabel(self.tab_urunler, text=val, font=ctk.CTkFont(size=11), text_color=TEXT_DARK).grid(row=r, column=c, padx=6, pady=4, sticky="w")

        info = ctk.CTkFrame(main, fg_color="transparent")
        info.pack(fill="x", padx=12, pady=(0, 12))
        ctk.CTkLabel(info, text="Bilgi: Fiyat grubundaki bir urunun fiyati degistiginde, gruba dahil tum urun fiyatlari otomatik guncellenir.",
                     font=ctk.CTkFont(size=12), text_color=TEXT_MUTED).pack()

    def new_group(self):
        messagebox.showinfo("Yeni Fiyat Grubu", "Fiyat grubu olusturma ekrani.")
