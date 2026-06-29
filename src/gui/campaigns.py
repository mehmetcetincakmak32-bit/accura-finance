import customtkinter as ctk
from tkinter import messagebox, ttk
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PRIMARY = "#1565c0"; SUCCESS = "#2e7d32"; DANGER = "#c62828"
TEXT_DARK = "#1a1a2e"; TEXT_MUTED = "#6c757d"

class CampaignsFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="#f4f6f8")
        self.app = app
        self.build_ui()

    def build_ui(self):
        header = ctk.CTkFrame(self, fg_color="white", corner_radius=10, height=50)
        header.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(header, text="Kampanya & Promosyon Yonetimi", font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_DARK).pack(side="left", padx=16, pady=12)
        ctk.CTkButton(header, text="+ Yeni Kampanya", fg_color=PRIMARY, corner_radius=6, command=self.new_campaign).pack(side="right", padx=16)

        main = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        main.pack(fill="both", expand=True)

        notebook = ttk.Notebook(main)
        notebook.pack(fill="both", expand=True, padx=12, pady=12)

        self.tab_aktif = ctk.CTkFrame(notebook, fg_color="transparent")
        self.tab_gecmis = ctk.CTkFrame(notebook, fg_color="transparent")
        notebook.add(self.tab_aktif, text="Aktif Kampanyalar")
        notebook.add(self.tab_gecmis, text="Gecmis Kampanyalar")

        headers = ["Kampanya Kodu", "Kampanya Adi", "Tur", "Baslangic", "Bitis", "Indirim", "Sube", "Durum"]
        for col, txt in enumerate(headers):
            ctk.CTkLabel(self.tab_aktif, text=txt, font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).grid(row=0, column=col, padx=6, pady=6, sticky="w")

        campaigns = [
            ("KMP-001", "Yaz Indirimi", "Indirim", "01.06.2026", "31.08.2026", "%20", "Merkez", "Aktif"),
            ("KMP-002", "3 Al 2 Ode", "CokAlAzOde", "01.07.2026", "31.07.2026", "-", "Merkez", "Aktif"),
            ("KMP-003", "Hediye Kahve", "HediyeUrun", "01.06.2026", "30.06.2026", "Hediye", "Sube-1", "Aktif"),
        ]
        for r, row in enumerate(campaigns, 1):
            for c, val in enumerate(row):
                clr = SUCCESS if c == 7 else TEXT_DARK
                ctk.CTkLabel(self.tab_aktif, text=val, font=ctk.CTkFont(size=11), text_color=clr).grid(row=r, column=c, padx=6, pady=4, sticky="w")

        ctk.CTkLabel(self.tab_gecmis, text="Gecmis kampanya kaydi bulunamadi.", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack(pady=20)

    def new_campaign(self):
        messagebox.showinfo("Yeni Kampanya", "Kampanya olusturma formu acilacak.\n\nTurler:\n- Indirim\n- Cok Al Az Ode\n- Hediye Urun\n- Puan Kazanma\n- Kupon")
