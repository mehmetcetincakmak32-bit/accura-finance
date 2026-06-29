import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from src.database.connection import get_database_manager
except ImportError:
    get_database_manager = None

PRIMARY = "#1565c0"; PRIMARY_DARK = "#0d47a1"
SUCCESS = "#2e7d32"; DANGER = "#c62828"; WARNING = "#f57f17"
TEXT_DARK = "#1a1a2e"; TEXT_MUTED = "#6c757d"; BORDER = "#e8eaed"

class CekFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="#f4f6f8")
        self.app = app
        self.build_ui()

    def build_ui(self):
        header = ctk.CTkFrame(self, fg_color="white", corner_radius=10, height=50)
        header.pack(fill="x", pady=(0, 8))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(header, text="Cek Yonetimi", font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_DARK).grid(row=0, column=0, padx=16, pady=12, sticky="w")

        actions_frame = ctk.CTkFrame(header, fg_color="transparent")
        actions_frame.grid(row=0, column=1, padx=16, sticky="e")
        ctk.CTkButton(actions_frame, text="+ Cek Girisi", width=100, height=32, fg_color=PRIMARY, corner_radius=6, command=self.check_entry).pack(side="left", padx=2)
        ctk.CTkButton(actions_frame, text="Ciro Islemi", width=100, height=32, fg_color="#6a1b9a", corner_radius=6, command=self.endorse_check).pack(side="left", padx=2)
        ctk.CTkButton(actions_frame, text="Tahsilat", width=90, height=32, fg_color=SUCCESS, corner_radius=6, command=self.collect_check).pack(side="left", padx=2)
        ctk.CTkButton(actions_frame, text="Karsiliksiz", width=100, height=32, fg_color=DANGER, corner_radius=6, command=self.bounce_check).pack(side="left", padx=2)
        ctk.CTkButton(actions_frame, text="Bordro", width=80, height=32, fg_color=WARNING, corner_radius=6, command=self.check_portfolio).pack(side="left", padx=2)

        main = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        main.pack(fill="both", expand=True)

        notebook = ttk.Notebook(main)
        notebook.pack(fill="both", expand=True, padx=12, pady=12)
        style = ttk.Style()
        style.theme_use("default")

        tabs = [
            ("Cek Portfoyu", self.build_check_portfolio),
            ("Ciro Edilenler", self.build_endorsed),
            ("Tahsil Edilenler", self.build_collected),
            ("Karsiliksiz Cekler", self.build_bounced),
            ("Vadesi Gelenler", self.build_matured),
            ("Cek Bordrolari", self.build_portfolios),
            ("Raporlar", self.build_reports),
        ]

        for tab_name, builder in tabs:
            tab = ctk.CTkFrame(notebook, fg_color="transparent")
            notebook.add(tab, text=tab_name)
            builder(tab)

        # Durum özet kartları
        stats_frame = ctk.CTkFrame(main, fg_color="transparent")
        stats_frame.pack(fill="x", padx=12, pady=(0, 12))

        stats = [
            ("Portfoydeki Cekler", "24", PRIMARY),
            ("Vadesi Gelen", "5", WARNING),
            ("Tahsil Edilen (Bu Ay)", "18", SUCCESS),
            ("Karsiliksiz (Bu Yil)", "3", DANGER),
            ("Toplam Cek Tutari", "1,245,800 TL", "#6a1b9a"),
        ]
        for label, val, color in stats:
            card = ctk.CTkFrame(stats_frame, fg_color="#f8f9fa", corner_radius=8, border_width=1, border_color=BORDER)
            card.pack(side="left", fill="x", expand=True, padx=4, pady=6)
            ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=12), text_color=TEXT_MUTED).pack(pady=(8, 0))
            ctk.CTkLabel(card, text=val, font=ctk.CTkFont(size=18, weight="bold"), text_color=color).pack(pady=(0, 8))

    def build_check_portfolio(self, parent):
        cols = ["Cek No", "Banka", "Sube", "Tutar", "Keside Tarihi", "Vade Tarihi", "Cek Sahibi", "Alis Tarihi", "Durum"]
        for c, txt in enumerate(cols):
            ctk.CTkLabel(parent, text=txt, font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).grid(row=0, column=c, padx=5, pady=6, sticky="w")

        checks = [
            ("CK-001", "Akbank", "Kadikoy Sb.", "45,000.00 TL", "01.06.2026", "30.07.2026", "ABC Ltd. Sti.", "01.06.2026", "Portfoyde"),
            ("CK-002", "Garanti", "Merkez Sb.", "28,500.00 TL", "05.06.2026", "15.08.2026", "XYZ Tic. A.S.", "05.06.2026", "Portfoyde"),
            ("CK-003", "Isbank", "Levent Sb.", "12,800.00 TL", "10.06.2026", "10.07.2026", "DEF Tekstil", "10.06.2026", "Portfoyde"),
            ("CK-004", "YKB", "Ankara Sb.", "67,200.00 TL", "15.06.2026", "15.09.2026", "MNO Insaat", "15.06.2026", "Portfoyde"),
            ("CK-005", "Ziraat", "Bursa Sb.", "8,900.00 TL", "20.06.2026", "20.07.2026", "PQR Gida", "20.06.2026", "CiroEdildi"),
        ]
        for r, row in enumerate(checks, 1):
            for c, val in enumerate(row):
                clr = TEXT_DARK
                if c == 8:
                    clr = {"Portfoyde": SUCCESS, "CiroEdildi": PRIMARY, "TahsilEdildi": "#6a1b9a", "Karsiliksiz": DANGER}.get(val, TEXT_DARK)
                lbl = ctk.CTkLabel(parent, text=val, font=ctk.CTkFont(size=11), text_color=clr)
                lbl.grid(row=r, column=c, padx=5, pady=4, sticky="w")

    def build_endorsed(self, parent):
        cols = ["Cek No", "Banka", "Tutar", "Vade", "Ciro Edilen", "Ciro Tarihi", "Ciro Turu"]
        for c, txt in enumerate(cols):
            ctk.CTkLabel(parent, text=txt, font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).grid(row=0, column=c, padx=5, pady=6, sticky="w")
        data = [("CK-005", "Ziraat", "8,900 TL", "20.07.2026", "Supplier A.S.", "22.06.2026", "TahsilIcin")]
        for r, row in enumerate(data, 1):
            for c, val in enumerate(row):
                ctk.CTkLabel(parent, text=val, font=ctk.CTkFont(size=11), text_color=TEXT_DARK).grid(row=r, column=c, padx=5, pady=4, sticky="w")

    def build_collected(self, parent):
        cols = ["Cek No", "Banka", "Tutar", "Vade", "Tahsil Tarihi", "Cek Sahibi"]
        for c, txt in enumerate(cols):
            ctk.CTkLabel(parent, text=txt, font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).grid(row=0, column=c, padx=5, pady=6, sticky="w")
        data = [("CK-001", "Akbank", "45,000 TL", "30.07.2026", "15.06.2026", "ABC Ltd.")]
        for r, row in enumerate(data, 1):
            for c, val in enumerate(row):
                ctk.CTkLabel(parent, text=val, font=ctk.CTkFont(size=11), text_color=TEXT_DARK).grid(row=r, column=c, padx=5, pady=4, sticky="w")

    def build_bounced(self, parent):
        cols = ["Cek No", "Banka", "Tutar", "Protesto Tarihi", "Nedeni", "Hukuki Surec", "Tahsilat"]
        for c, txt in enumerate(cols):
            ctk.CTkLabel(parent, text=txt, font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).grid(row=0, column=c, padx=5, pady=6, sticky="w")
        data = [("CK-099", "YKB", "15,000 TL", "10.06.2026", "Karsiliksiz", "Basladi", "0 TL")]
        for r, row in enumerate(data, 1):
            for c, val in enumerate(row):
                clr = DANGER if c in [3, 4] else TEXT_DARK
                ctk.CTkLabel(parent, text=val, font=ctk.CTkFont(size=11), text_color=clr).grid(row=r, column=c, padx=5, pady=4, sticky="w")

    def build_matured(self, parent):
        cols = ["Cek No", "Banka", "Tutar", "Vade Tarihi", "Kalan Gun", "Cek Sahibi", "Islem"]
        for c, txt in enumerate(cols):
            ctk.CTkLabel(parent, text=txt, font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).grid(row=0, column=c, padx=5, pady=6, sticky="w")
        data = [("CK-003", "Isbank", "12,800 TL", "10.07.2026", "12 gun", "DEF Tekstil", "Tahsil Et")]
        for r, row in enumerate(data, 1):
            for c, val in enumerate(row):
                ctk.CTkLabel(parent, text=val, font=ctk.CTkFont(size=11), text_color=TEXT_DARK).grid(row=r, column=c, padx=5, pady=4, sticky="w")

    def build_portfolios(self, parent):
        cols = ["Bordro No", "Tarih", "Tur", "Cek Sayisi", "Toplam Tutar", "Olusturan"]
        for c, txt in enumerate(cols):
            ctk.CTkLabel(parent, text=txt, font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).grid(row=0, column=c, padx=5, pady=6, sticky="w")
        data = [("BRD-001", "01.06.2026", "Musteriden Alinan", "12", "245,000 TL", "Admin"),
                ("BRD-002", "05.06.2026", "Sirket Tarafindan Verilen", "3", "67,200 TL", "Admin")]
        for r, row in enumerate(data, 1):
            for c, val in enumerate(row):
                ctk.CTkLabel(parent, text=val, font=ctk.CTkFont(size=11), text_color=TEXT_DARK).grid(row=r, column=c, padx=5, pady=4, sticky="w")

    def build_reports(self, parent):
        ctk.CTkLabel(parent, text="Cek Raporlari", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_DARK).pack(anchor="w", pady=(12, 8))
        reports = [
            "Cek Portfoy Raporu",
            "Vade Analiz Raporu",
            "Ciro Edilen Cekler Raporu",
            "Karsiliksiz Cek Raporu",
            "Banka Bazinda Cek Dagilimi",
            "Aylik Cek Hacim Raporu",
            "Musteri Bazinda Cek Raporu",
            "Yillik Cek Hareket Raporu",
        ]
        for rep in reports:
            btn = ctk.CTkButton(parent, text=rep, width=300, height=30, anchor="w", fg_color="transparent",
                                text_color=TEXT_DARK, hover_color="#e8eaf6", corner_radius=6,
                                font=ctk.CTkFont(size=11), command=lambda r=rep: self.show_report(r))
            btn.pack(pady=1)

    def show_report(self, report_name):
        messagebox.showinfo("Rapor", f"{report_name} hazirlaniyor...\n\nRapor formati: PDF / Excel")

    def check_entry(self):
        win = ctk.CTkToplevel(self)
        win.title("Yeni Cek Girisi")
        win.geometry("550x550")
        win.transient(self.master)
        win.grab_set()

        ctk.CTkLabel(win, text="Yeni Cek Kaydi", font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_DARK).pack(pady=12)

        main = ctk.CTkScrollableFrame(win, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=20, pady=10)

        fields = [
            ("Cek Numarasi *", "entry"), ("Banka Adi *", "entry"), ("Sube Adi", "entry"),
            ("Hesap No", "entry"), ("Cek Tutari *", "entry"), ("Keside Tarihi", "entry"),
            ("Vade Tarihi *", "entry"), ("Cek Sahibi / Musteri", "entry"),
            ("Cek Turu", "combo"), ("Cizgili Cek mi?", "check"), ("Teyitli Cek mi?", "check"),
            ("Aciklama", "text"),
        ]
        self.entry_widgets = {}
        for label, typ in fields:
            f = ctk.CTkFrame(main, fg_color="transparent")
            f.pack(fill="x", pady=3)
            ctk.CTkLabel(f, text=label, width=140, anchor="w", font=ctk.CTkFont(size=11), text_color=TEXT_DARK).pack(side="left")
            if typ == "entry":
                w = ctk.CTkEntry(f, height=28)
                w.pack(side="left", fill="x", expand=True, padx=(5, 0))
                self.entry_widgets[label] = w
            elif typ == "combo":
                var = ctk.StringVar(value="Musteri Ceki")
                w = ctk.CTkOptionMenu(f, values=["Musteri Ceki", "Sirket Ceki"], variable=var, height=28)
                w.pack(side="left", fill="x", expand=True, padx=(5, 0))
                self.entry_widgets[label] = var
            elif typ == "check":
                var = ctk.BooleanVar(value=False)
                w = ctk.CTkCheckBox(f, text="", variable=var, height=28)
                w.pack(side="left", padx=(5, 0))
                self.entry_widgets[label] = var
            elif typ == "text":
                w = ctk.CTkTextbox(f, height=50)
                w.pack(side="left", fill="x", expand=True, padx=(5, 0))
                self.entry_widgets[label] = w

        btn_frame = ctk.CTkFrame(win, fg_color="transparent")
        btn_frame.pack(pady=12)
        ctk.CTkButton(btn_frame, text="Cek Kaydet", width=120, height=36, fg_color=SUCCESS,
                       corner_radius=6, command=lambda: self.save_check(win)).pack(side="left", padx=4)
        ctk.CTkButton(btn_frame, text="Iptal", width=80, height=36, fg_color=DANGER,
                       corner_radius=6, command=win.destroy).pack(side="left", padx=4)

    def save_check(self, win):
        data = {}
        for k, v in self.entry_widgets.items():
            if hasattr(v, 'get'):
                data[k] = v.get()
            elif hasattr(v, 'winfo_exists'):
                data[k] = v.get("1.0", "end-1c")
        if not data.get("Cek Numarasi *") or not data.get("Banka Adi *") or not data.get("Cek Tutari *"):
            messagebox.showwarning("Uyari", "Cek No, Banka ve Tutar zorunludur!", parent=win)
            return
        messagebox.showinfo("Basarili", "Cek basariyla kaydedildi.\n\nPortfoye eklendi.", parent=win)
        win.destroy()

    def endorse_check(self):
        win = ctk.CTkToplevel(self)
        win.title("Cek Ciro Islemi")
        win.geometry("400x300")
        win.transient(self.master)
        win.grab_set()

        ctk.CTkLabel(win, text="Cek Ciro Islemi", font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_DARK).pack(pady=12)

        f = ctk.CTkFrame(win, fg_color="transparent")
        f.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(f, text="Cek Numarasi:", width=110, anchor="w", font=ctk.CTkFont(size=11), text_color=TEXT_DARK).pack(side="left")
        ctk.CTkEntry(f, height=28).pack(side="left", fill="x", expand=True)

        f = ctk.CTkFrame(win, fg_color="transparent")
        f.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(f, text="Ciro Edilen:", width=110, anchor="w", font=ctk.CTkFont(size=11), text_color=TEXT_DARK).pack(side="left")
        ctk.CTkEntry(f, height=28).pack(side="left", fill="x", expand=True)

        f = ctk.CTkFrame(win, fg_color="transparent")
        f.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(f, text="Ciro Turu:", width=110, anchor="w", font=ctk.CTkFont(size=11), text_color=TEXT_DARK).pack(side="left")
        ctk.CTkOptionMenu(f, values=["Tahsil Icin", "Ciro", "Temlik"], height=28).pack(side="left", fill="x", expand=True, padx=(5, 0))

        f = ctk.CTkFrame(win, fg_color="transparent")
        f.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(f, text="Tarih:", width=110, anchor="w", font=ctk.CTkFont(size=11), text_color=TEXT_DARK).pack(side="left")
        ctk.CTkEntry(f, height=28, placeholder_text="GG.AA.YYYY").pack(side="left", fill="x", expand=True)

        ctk.CTkButton(win, text="Ciro Islemini Tamamla", width=180, height=36, fg_color="#6a1b9a",
                       corner_radius=6, command=lambda: self.do_endorse(win)).pack(pady=16)

    def do_endorse(self, win):
        messagebox.showinfo("Basarili", "Cek basariyla ciro edildi.", parent=win)
        win.destroy()

    def collect_check(self):
        win = ctk.CTkToplevel(self)
        win.title("Cek Tahsilati")
        win.geometry("400x250")
        win.transient(self.master)
        win.grab_set()

        ctk.CTkLabel(win, text="Cek Tahsilati", font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_DARK).pack(pady=12)
        for label in ["Cek Numarasi:", "Tahsil Tutari:", "Tahsil Tarihi:", "Banka Hesabi:"]:
            f = ctk.CTkFrame(win, fg_color="transparent")
            f.pack(fill="x", padx=20, pady=3)
            ctk.CTkLabel(f, text=label, width=110, anchor="w", font=ctk.CTkFont(size=11), text_color=TEXT_DARK).pack(side="left")
            ctk.CTkEntry(f, height=28).pack(side="left", fill="x", expand=True)

        ctk.CTkButton(win, text="Tahsilati Tamamla", width=160, height=36, fg_color=SUCCESS,
                       corner_radius=6, command=lambda: self.do_collect(win)).pack(pady=16)

    def do_collect(self, win):
        messagebox.showinfo("Basarili", "Cek tahsilati basariyla kaydedildi.", parent=win)
        win.destroy()

    def bounce_check(self):
        win = ctk.CTkToplevel(self)
        win.title("Karsiliksiz Cek Kaydi")
        win.geometry("450x350")
        win.transient(self.master)
        win.grab_set()

        ctk.CTkLabel(win, text="Karsiliksiz Cek Islemi", font=ctk.CTkFont(size=16, weight="bold"), text_color=DANGER).pack(pady=12)
        for label in ["Cek Numarasi:", "Protesto Tarihi:", "Karsiliksiz Nedeni:", "Protesto Masrafi:", "Hukuki Surec:"]:
            f = ctk.CTkFrame(win, fg_color="transparent")
            f.pack(fill="x", padx=20, pady=3)
            ctk.CTkLabel(f, text=label, width=120, anchor="w", font=ctk.CTkFont(size=11), text_color=TEXT_DARK).pack(side="left")
            if label == "Karsiliksiz Nedeni:":
                ctk.CTkOptionMenu(f, values=["Karsiliksiz", "Hesap Kapali", "Imza Uyusmazligi", "Tahrifat", "Diger"], height=28).pack(side="left", fill="x", expand=True, padx=(5, 0))
            elif label == "Hukuki Surec:":
                var = ctk.BooleanVar(value=True)
                ctk.CTkCheckBox(f, text="Hukuki surec baslatilsin", variable=var).pack(side="left", padx=(5, 0))
            else:
                ctk.CTkEntry(f, height=28).pack(side="left", fill="x", expand=True)

        ctk.CTkButton(win, text="Kaydet", width=120, height=36, fg_color=DANGER,
                       corner_radius=6, command=lambda: self.do_bounce(win)).pack(pady=16)

    def do_bounce(self, win):
        messagebox.showinfo("Kaydedildi", "Karsiliksiz cek kaydi olusturuldu.\nHukuki surec baslatildi.", parent=win)
        win.destroy()

    def check_portfolio(self):
        win = ctk.CTkToplevel(self)
        win.title("Cek Bordrosu")
        win.geometry("500x400")
        win.transient(self.master)
        win.grab_set()

        ctk.CTkLabel(win, text="Cek Bordrosu Olustur", font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_DARK).pack(pady=12)

        f = ctk.CTkFrame(win, fg_color="transparent")
        f.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(f, text="Bordro Tarihi:", width=110, anchor="w", font=ctk.CTkFont(size=11), text_color=TEXT_DARK).pack(side="left")
        ctk.CTkEntry(f, height=28, placeholder_text="GG.AA.YYYY").pack(side="left", fill="x", expand=True)

        f = ctk.CTkFrame(win, fg_color="transparent")
        f.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(f, text="Bordro Turu:", width=110, anchor="w", font=ctk.CTkFont(size=11), text_color=TEXT_DARK).pack(side="left")
        ctk.CTkOptionMenu(f, values=["Musteriden Alinan Cekler", "Sirket Tarafindan Verilen Cekler"], height=28).pack(side="left", fill="x", expand=True, padx=(5, 0))

        ctk.CTkLabel(win, text="Bordroya Eklenecek Cekler:", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_DARK).pack(anchor="w", padx=20, pady=(12, 4))

        checks_listbox = tk.Listbox(win, height=8, font=("Arial", 10), bg="white", fg=TEXT_DARK,
                                    selectbackground="#e8eaf6", selectforeground=TEXT_DARK, borderwidth=0)
        checks_listbox.pack(fill="both", expand=True, padx=20, pady=4)
        for c in ["CK-001 - Akbank - 45,000 TL", "CK-002 - Garanti - 28,500 TL", "CK-003 - Isbank - 12,800 TL"]:
            checks_listbox.insert("end", c)

        btn_frame = ctk.CTkFrame(win, fg_color="transparent")
        btn_frame.pack(pady=12)
        ctk.CTkButton(btn_frame, text="Bordro Olustur", width=140, height=36, fg_color=WARNING,
                       corner_radius=6, command=lambda: self.save_portfolio(win)).pack(side="left", padx=4)
        ctk.CTkButton(btn_frame, text="Iptal", width=80, height=36, fg_color=DANGER,
                       corner_radius=6, command=win.destroy).pack(side="left", padx=4)

    def save_portfolio(self, win):
        messagebox.showinfo("Basarili", "Cek bordrosu olusturuldu.\nYazdirma ekrani acilacak.", parent=win)
        win.destroy()
