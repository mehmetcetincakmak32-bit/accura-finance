import customtkinter as ctk
from tkinter import messagebox, ttk
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PRIMARY = "#1565c0"; SUCCESS = "#2e7d32"
TEXT_DARK = "#1a1a2e"; TEXT_MUTED = "#6c757d"

class BranchesFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="#f4f6f8")
        self.app = app
        self.build_ui()

    def build_ui(self):
        header = ctk.CTkFrame(self, fg_color="white", corner_radius=10, height=50)
        header.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(header, text="Sube Yonetimi", font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_DARK).pack(side="left", padx=16, pady=12)
        ctk.CTkButton(header, text="+ Yeni Sube", fg_color=PRIMARY, corner_radius=6, command=self.new_branch).pack(side="right", padx=4)
        ctk.CTkButton(header, text="Subeler Arasi Transfer", fg_color=SUCCESS, corner_radius=6, command=self.transfer).pack(side="right", padx=4)

        main = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        main.pack(fill="both", expand=True)

        notebook = ttk.Notebook(main)
        notebook.pack(fill="both", expand=True, padx=12, pady=12)

        self.tab_subeler = ctk.CTkFrame(notebook, fg_color="transparent")
        self.tab_transfer = ctk.CTkFrame(notebook, fg_color="transparent")
        notebook.add(self.tab_subeler, text="Subeler")
        notebook.add(self.tab_transfer, text="Subeler Arasi Transferler")

        for col, txt in enumerate(["Sube Kodu", "Sube Adi", "Sehir", "Telefon", "Yonetici", "Merkez", "POS Sayisi", "Durum"]):
            ctk.CTkLabel(self.tab_subeler, text=txt, font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).grid(row=0, column=col, padx=6, pady=6, sticky="w")

        branches = [("M", "Merkez Sube", "Istanbul", "0212-555-0100", "Ali Yonetmen", "Evet", "5", "Aktif"),
                    ("S-01", "Kadikoy Sube", "Istanbul", "0216-555-0200", "Ayse Mudur", "Hayir", "3", "Aktif"),
                    ("S-02", "Ankara Sube", "Ankara", "0312-555-0300", "Mehmet Mudur", "Hayir", "2", "Aktif")]
        for r, row in enumerate(branches, 1):
            for c, val in enumerate(row):
                clr = SUCCESS if c == 7 else TEXT_DARK
                ctk.CTkLabel(self.tab_subeler, text=val, font=ctk.CTkFont(size=11), text_color=clr).grid(row=r, column=c, padx=6, pady=4, sticky="w")

        for col, txt in enumerate(["Transfer No", "Tarih", "Kaynak Sube", "Hedef Sube", "Urun Sayisi", "Durum"]):
            ctk.CTkLabel(self.tab_transfer, text=txt, font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).grid(row=0, column=col, padx=6, pady=6, sticky="w")
        transfers = [("TR-001", "20.06.2026", "Merkez Sube", "Kadikoy Sube", "15", "Tamamlandi"),
                     ("TR-002", "22.06.2026", "Merkez Sube", "Ankara Sube", "8", "Hazirlaniyor")]
        for r, row in enumerate(transfers, 1):
            for c, val in enumerate(row):
                ctk.CTkLabel(self.tab_transfer, text=val, font=ctk.CTkFont(size=11), text_color=TEXT_DARK).grid(row=r, column=c, padx=6, pady=4, sticky="w")

    def new_branch(self):
        messagebox.showinfo("Yeni Sube", "Sube tanimlama formu acilacak.")

    def transfer(self):
        messagebox.showinfo("Subeler Arasi Transfer", "Stok transfer formu acilacak.")
