import customtkinter as ctk
from tkinter import messagebox, ttk
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PRIMARY = "#1565c0"; DANGER = "#c62828"; SUCCESS = "#2e7d32"
TEXT_DARK = "#1a1a2e"; TEXT_MUTED = "#6c757d"; BORDER = "#e8eaed"

class ProductionFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="#f4f6f8")
        self.app = app
        self.build_ui()

    def build_ui(self):
        header = ctk.CTkFrame(self, fg_color="white", corner_radius=10, height=50)
        header.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(header, text="Uretim Modulu", font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_DARK).pack(side="left", padx=16, pady=12)
        ctk.CTkButton(header, text="+ Yeni Recete", fg_color=PRIMARY, corner_radius=6, command=self.new_recipe).pack(side="right", padx=4)
        ctk.CTkButton(header, text="+ Uretim Emri", fg_color=SUCCESS, corner_radius=6, command=self.new_order).pack(side="right", padx=4)

        main = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        main.pack(fill="both", expand=True)

        notebook = ttk.Notebook(main)
        notebook.pack(fill="both", expand=True, padx=12, pady=12)

        self.tab_recete = ctk.CTkFrame(notebook, fg_color="transparent")
        self.tab_emir = ctk.CTkFrame(notebook, fg_color="transparent")
        notebook.add(self.tab_recete, text="Uretim Receteleri")
        notebook.add(self.tab_emir, text="Uretim Emirleri")

        for col, txt in [(0, "Recete Kodu"), (1, "Recete Adi"), (2, "Urun"), (3, "Miktar"), (4, "Birim"), (5, "Toplam Maliyet"), (6, "Durum")]:
            ctk.CTkLabel(self.tab_recete, text=txt, font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).grid(row=0, column=col, padx=6, pady=6, sticky="w")
        recetes = [("REC-001", "Cikolatali Pasta", "Pasta Urtunu", "1", "Adet", "45.20 TL"),
                   ("REC-002", "Tam Bugday Ekmek", "Ekmek", "50", "Adet", "28.50 TL"),
                   ("REC-003", "Meyve Suyu 1L", "Meyve Suyu", "100", "Lt", "120.00 TL")]
        for r, row in enumerate(recetes, 1):
            for c, val in enumerate(row):
                ctk.CTkLabel(self.tab_recete, text=val, font=ctk.CTkFont(size=11), text_color=TEXT_DARK).grid(row=r, column=c, padx=6, pady=4, sticky="w")

        for col, txt in [(0, "Emir No"), (1, "Tarih"), (2, "Urun"), (3, "Planlanan"), (4, "Uretilen"), (5, "Durum")]:
            ctk.CTkLabel(self.tab_emir, text=txt, font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).grid(row=0, column=col, padx=6, pady=6, sticky="w")
        orders = [("URE-001", "15.06.2026", "Pasta Urtunu", "50", "45", "Tamamlandi"),
                  ("URE-002", "20.06.2026", "Ekmek", "200", "0", "Uretimde")]
        for r, row in enumerate(orders, 1):
            for c, val in enumerate(row):
                ctk.CTkLabel(self.tab_emir, text=val, font=ctk.CTkFont(size=11), text_color=TEXT_DARK).grid(row=r, column=c, padx=6, pady=4, sticky="w")

    def new_recipe(self):
        messagebox.showinfo("Yeni Recete", "Uretim recetesi olusturma ekrani.")

    def new_order(self):
        messagebox.showinfo("Yeni Uretim Emri", "Uretim emri olusturma ekrani.")
