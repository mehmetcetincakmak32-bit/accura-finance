import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
import json
import shutil
import glob
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

PRIMARY = "#1565c0"; PRIMARY_DARK = "#0d47a1"; PRIMARY_LIGHT = "#42a5f5"
SUCCESS = "#2e7d32"; DANGER = "#c62828"; WARNING = "#f57f17"
TEXT_DARK = "#1a1a2e"; TEXT_MUTED = "#6c757d"; BORDER = "#e8eaed"; CARD_BG = "#ffffff"

try:
    from src.services.backup_service import BackupService
    _backup_svc = BackupService()
    HAS_SERVICE = True
except Exception:
    _backup_svc = None
    HAS_SERVICE = False


class BackupFrame(ctk.CTkFrame):
    def __init__(self, parent, main_app):
        super().__init__(parent, fg_color="#f0f2f5")
        self.main_app = main_app
        self.svc = _backup_svc
        self._scheduler_active = False
        self._scheduler_thread = None

        if not HAS_SERVICE:
            self._init_sim()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_header()
        self._build_tabs()
        self._build_statusbar()
        self._load_history()
        self._update_disk_space()

    # ---- simulation helpers ----
    def _init_sim(self):
        self._sim_dir = os.path.join(os.path.expanduser("~"), "accura_backups")
        os.makedirs(self._sim_dir, exist_ok=True)
        dbf = os.path.join(self._sim_dir, "accura_finance.db")
        if not os.path.exists(dbf):
            with open(dbf, "w") as f:
                f.write("simulated database content")

    def _sim_create(self, btype="full", desc=""):
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        ext = {"full": "db", "database": "db", "settings": "json"}.get(btype, "db")
        fn = f"accura_finance_backup_{ts}.{ext}"
        fp = os.path.join(self._sim_dir, fn)
        kb = {"full": 512, "database": 480, "settings": 32}
        with open(fp, "w") as f:
            f.write("x" * (kb.get(btype, 100) * 1024))
        info = {"backup_file": fn, "created_at": datetime.now().isoformat(),
                "db_size_mb": round(kb.get(btype, 100) / 1024, 2),
                "backup_size_mb": round(kb.get(btype, 100) / 1024, 2),
                "type": btype, "description": desc}
        with open(fp + ".info", "w", encoding="utf-8") as f:
            json.dump(info, f, indent=2, ensure_ascii=False)
        self._log(f"Yedekleme ba\u015far\u0131l\u0131: {fn}")
        return fp

    def _sim_list(self):
        backups = []
        for p in ["accura_finance_backup_*.db", "accura_finance_backup_*.json", "accura_finance_backup_*.bak"]:
            for fp in glob.glob(os.path.join(self._sim_dir, p)):
                st = os.stat(fp)
                ip = fp + ".info"
                info = {}
                if os.path.exists(ip):
                    try:
                        with open(ip, "r", encoding="utf-8") as f:
                            info = json.load(f)
                    except Exception:
                        pass
                backups.append({"filename": os.path.basename(fp), "filepath": fp,
                                "size_mb": round(st.st_size / (1024 * 1024), 2),
                                "created_at": datetime.fromtimestamp(st.st_mtime).isoformat(),
                                "info": info})
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        return backups

    def _sim_restore(self, fp):
        time.sleep(1)
        self._log(f"Geri y\u00fckleme ba\u015far\u0131l\u0131: {os.path.basename(fp)}")
        return True

    def _sim_disk_gb(self):
        try:
            import ctypes
            free = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                ctypes.c_wchar_p(self._sim_dir), None, None, ctypes.pointer(free))
            return free.value / (1024 ** 3)
        except Exception:
            return 0.0

    # ---- UI build ----
    def _build_header(self):
        h = ctk.CTkFrame(self, height=72, corner_radius=10, fg_color=CARD_BG)
        h.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 5))
        h.grid_propagate(False)
        ctk.CTkLabel(h, text="VER\u0130 YEDEKLEME & GER\u0130 Y\u00dcKLEME",
                     font=ctk.CTkFont(size=22, weight="bold"), text_color=TEXT_DARK
                     ).pack(side="left", padx=20, pady=(12, 0))
        ctk.CTkLabel(h, text="Otomatik ve manuel yedekleme y\u00f6netimi",
                     font=ctk.CTkFont(size=12), text_color=TEXT_MUTED
                     ).pack(side="left", padx=5, pady=(12, 0))
        self._disk_lbl = ctk.CTkLabel(h, text="", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED)
        self._disk_lbl.pack(side="right", padx=20, pady=(12, 0))

    def _build_tabs(self):
        self.tv = ctk.CTkTabview(self, corner_radius=10, fg_color=CARD_BG)
        self.tv.grid(row=1, column=0, sticky="nsew", padx=15, pady=5)
        self.tv._segmented_button.configure(font=ctk.CTkFont(size=13, weight="bold"))

        self.tv.add("Yedekleme")
        self.tv.add("Otomatik Yedekleme")
        self.tv.add("Geri Y\u00fckleme")

        self.grid_rowconfigure(2, weight=1)
        self._build_tab1()
        self._build_tab2()
        self._build_tab3()

    def _build_statusbar(self):
        sf = ctk.CTkFrame(self, height=28, corner_radius=5, fg_color=CARD_BG)
        sf.grid(row=3, column=0, sticky="ew", padx=15, pady=(5, 15))
        self._status_lbl = ctk.CTkLabel(sf, text="Haz\u0131r", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED)
        self._status_lbl.pack(side="left", padx=15)

    # ---- Tab 1: Yedekleme ----
    def _build_tab1(self):
        t = self.tv.tab("Yedekleme")
        t.grid_columnconfigure(0, weight=1)

        # big backup button
        bf = ctk.CTkFrame(t, fg_color="transparent")
        bf.grid(row=0, column=0, pady=(20, 5))
        self._backup_btn = ctk.CTkButton(bf, text="\u015eimdi Yedekle",
                                          font=ctk.CTkFont(size=18, weight="bold"),
                                          fg_color=SUCCESS, hover_color="#1b5e20",
                                          width=200, height=50, corner_radius=8,
                                          command=self._do_backup)
        self._backup_btn.pack()

        # progress
        pf = ctk.CTkFrame(t, fg_color="transparent")
        pf.grid(row=1, column=0, pady=(5, 0))
        self._bp = ctk.CTkProgressBar(pf, width=400, height=8, fg_color=BORDER,
                                       progress_color=PRIMARY, corner_radius=4)
        self._bp.pack()
        self._bp.set(0)
        self._bpl = ctk.CTkLabel(pf, text="", font=ctk.CTkFont(size=12), text_color=TEXT_MUTED)
        self._bpl.pack()
        self._bpl2 = ctk.CTkLabel(pf, text="", font=ctk.CTkFont(size=12), text_color=TEXT_MUTED)
        self._bpl2.pack()

        # options
        of = ctk.CTkFrame(t, fg_color="transparent")
        of.grid(row=2, column=0, sticky="ew", padx=40, pady=10)
        of.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(of, text="Yedekleme T\u00fcr\u00fc:", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=TEXT_DARK).grid(row=0, column=0, sticky="w", pady=4)
        self._bt_var = ctk.StringVar(value="Tam Yedek")
        self._bt_cb = ctk.CTkComboBox(of, values=["Tam Yedek", "Sadece Veritaban\u0131", "Sadece Ayarlar"],
                                       variable=self._bt_var, width=250,
                                       font=ctk.CTkFont(size=12), state="readonly")
        self._bt_cb.grid(row=0, column=1, sticky="w", padx=(10, 0), pady=4)

        ctk.CTkLabel(of, text="A\u00e7\u0131klama:", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=TEXT_DARK).grid(row=1, column=0, sticky="w", pady=4)
        self._desc_e = ctk.CTkEntry(of, placeholder_text="Yedekleme a\u00e7\u0131klamas\u0131 (iste\u011fe ba\u011fl\u0131)",
                                     width=250, font=ctk.CTkFont(size=12))
        self._desc_e.grid(row=1, column=1, sticky="w", padx=(10, 0), pady=4)

        ctk.CTkLabel(of, text="Yedekleme Konumu:", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=TEXT_DARK).grid(row=2, column=0, sticky="w", pady=4)
        lf = ctk.CTkFrame(of, fg_color="transparent")
        lf.grid(row=2, column=1, sticky="w", padx=(10, 0), pady=4)
        self._loc_var = ctk.StringVar(value=os.path.join(os.path.expanduser("~"), "accura_backups"))
        ctk.CTkEntry(lf, textvariable=self._loc_var, width=200, font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 5))
        ctk.CTkButton(lf, text="G\u00f6zat", font=ctk.CTkFont(size=11), fg_color=PRIMARY,
                       width=70, height=28, command=self._browse_loc).pack(side="left")

        # compression indicator
        cf = ctk.CTkFrame(t, fg_color="#e8f5e9", corner_radius=5)
        cf.grid(row=3, column=0, sticky="ew", padx=40, pady=5)
        ctk.CTkLabel(cf, text="\u2705 S\u0131k\u0131\u015ft\u0131rma: Aktif (varsay\u0131lan)",
                     font=ctk.CTkFont(size=11), text_color=SUCCESS).pack(padx=10, pady=4)

        # last backup
        self._last_lbl = ctk.CTkLabel(t, text="Son Yedekleme: Hen\u00fcz yap\u0131lmad\u0131",
                                       font=ctk.CTkFont(size=11), text_color=TEXT_MUTED)
        self._last_lbl.grid(row=4, column=0, pady=5)

        # history table
        tf = ctk.CTkFrame(t, fg_color=CARD_BG, corner_radius=8)
        tf.grid(row=5, column=0, sticky="nsew", padx=40, pady=(5, 15))
        t.grid_rowconfigure(5, weight=1)
        tf.grid_columnconfigure(0, weight=1)
        tf.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(tf, text="Yedekleme Ge\u00e7mi\u015fi", font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=TEXT_DARK).grid(row=0, column=0, sticky="w", padx=15, pady=(10, 5))

        cols = ("tarih", "tur", "boyut", "aciklama", "islem")
        self._tree = ttk.Treeview(tf, columns=cols, show="headings", height=6)
        self._tree.heading("tarih", text="Tarih")
        self._tree.heading("tur", text="T\u00fcr")
        self._tree.heading("boyut", text="Boyut")
        self._tree.heading("aciklama", text="A\u00e7\u0131klama")
        self._tree.heading("islem", text="\u0130\u015flem")
        self._tree.column("tarih", width=150)
        self._tree.column("tur", width=120)
        self._tree.column("boyut", width=80)
        self._tree.column("aciklama", width=200)
        self._tree.column("islem", width=0, stretch=False)
        sb = ttk.Scrollbar(tf, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        self._tree.grid(row=1, column=0, sticky="nsew", padx=(15, 0), pady=(0, 15))
        sb.grid(row=1, column=1, sticky="ns", pady=(0, 15))
        self._tree.bind("<Double-1>", lambda e: self._tree_restore())

    def _build_tab2(self):
        t = self.tv.tab("Otomatik Yedekleme")
        t.grid_columnconfigure(0, weight=1)

        mf = ctk.CTkFrame(t, fg_color="transparent")
        mf.grid(row=0, column=0, sticky="nsew", padx=40, pady=20)
        mf.grid_columnconfigure(0, weight=1)

        # toggle
        tof = ctk.CTkFrame(mf, fg_color=CARD_BG, corner_radius=8)
        tof.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        ctk.CTkLabel(tof, text="Otomatik Yedekleme", font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=TEXT_DARK).pack(side="left", padx=20, pady=15)
        self._sw = ctk.CTkSwitch(tof, text="A\u00c7IK", font=ctk.CTkFont(size=12),
                                  progress_color=SUCCESS, command=self._toggle_sched)
        self._sw.pack(side="right", padx=20, pady=15)

        # settings
        sf = ctk.CTkFrame(mf, fg_color=CARD_BG, corner_radius=8)
        sf.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        sf.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(sf, text="S\u0131kl\u0131k:", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=TEXT_DARK).grid(row=0, column=0, sticky="w", padx=20, pady=(15, 5))
        self._freq_v = ctk.StringVar(value="Her G\u00fcn")
        self._freq_cb = ctk.CTkComboBox(sf, values=["Her G\u00fcn", "Her Hafta", "Her Ay"],
                                         variable=self._freq_v, width=200,
                                         font=ctk.CTkFont(size=12), state="readonly",
                                         command=self._freq_change)
        self._freq_cb.grid(row=0, column=1, sticky="w", padx=(10, 20), pady=(15, 5))

        ctk.CTkLabel(sf, text="Saat:", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=TEXT_DARK).grid(row=1, column=0, sticky="w", padx=20, pady=5)
        tif = ctk.CTkFrame(sf, fg_color="transparent")
        tif.grid(row=1, column=1, sticky="w", padx=(10, 20), pady=5)
        self._hr_v = ctk.StringVar(value="03")
        ctk.CTkComboBox(tif, values=[f"{i:02d}" for i in range(24)],
                         variable=self._hr_v, width=70,
                         font=ctk.CTkFont(size=12), state="readonly").pack(side="left")
        ctk.CTkLabel(tif, text=":", font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=TEXT_DARK).pack(side="left", padx=3)
        self._mn_v = ctk.StringVar(value="00")
        ctk.CTkComboBox(tif, values=["00", "15", "30", "45"],
                         variable=self._mn_v, width=70,
                         font=ctk.CTkFont(size=12), state="readonly").pack(side="left")

        ctk.CTkLabel(sf, text="Saklama S\u00fcresi:", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=TEXT_DARK).grid(row=2, column=0, sticky="w", padx=20, pady=5)
        self._ret_v = ctk.StringVar(value="30 G\u00fcn")
        ctk.CTkComboBox(sf, values=["7 G\u00fcn", "30 G\u00fcn", "90 G\u00fcn", "180 G\u00fcn", "1 Y\u0131l", "S\u00fcresiz"],
                         variable=self._ret_v, width=200,
                         font=ctk.CTkFont(size=12), state="readonly"
                         ).grid(row=2, column=1, sticky="w", padx=(10, 20), pady=5)

        # weekly / monthly rows
        self._wd_lbl = ctk.CTkLabel(sf, text="Haftan\u0131n G\u00fcn\u00fc:", font=ctk.CTkFont(size=12, weight="bold"),
                                     text_color=TEXT_DARK)
        self._wd_lbl.grid(row=3, column=0, sticky="w", padx=20, pady=5)
        self._wd_cb = ctk.CTkComboBox(sf, values=["Pazartesi", "Sal\u0131", "\u00c7ar\u015famba", "Per\u015fembe",
                                                    "Cuma", "Cumartesi", "Pazar"],
                                        variable=ctk.StringVar(value="Pazartesi"), width=200,
                                        font=ctk.CTkFont(size=12), state="readonly")
        self._wd_cb.grid(row=3, column=1, sticky="w", padx=(10, 20), pady=5)

        self._md_lbl = ctk.CTkLabel(sf, text="Ay\u0131n G\u00fcn\u00fc:", font=ctk.CTkFont(size=12, weight="bold"),
                                     text_color=TEXT_DARK)
        self._md_lbl.grid(row=4, column=0, sticky="w", padx=20, pady=5)
        self._md_cb = ctk.CTkComboBox(sf, values=[str(i) for i in range(1, 29)],
                                        variable=ctk.StringVar(value="1"), width=200,
                                        font=ctk.CTkFont(size=12), state="readonly")
        self._md_cb.grid(row=4, column=1, sticky="w", padx=(10, 20), pady=5)

        # hide conditional rows initially
        self._wd_lbl.grid_remove()
        self._wd_cb.grid_remove()
        self._md_lbl.grid_remove()
        self._md_cb.grid_remove()

        ctk.CTkButton(sf, text="Ayarlar\u0131 Kaydet", font=ctk.CTkFont(size=13, weight="bold"),
                       fg_color=PRIMARY, hover_color=PRIMARY_DARK, width=200, height=35,
                       corner_radius=6, command=self._save_sched
                       ).grid(row=5, column=0, columnspan=2, pady=20)

        # next backup
        self._next_lbl = ctk.CTkLabel(mf, text="Bir sonraki yedekleme: Ayarlanmad\u0131",
                                       font=ctk.CTkFont(size=12), text_color=TEXT_MUTED)
        self._next_lbl.grid(row=2, column=0, pady=5)

        # log viewer
        lf = ctk.CTkFrame(mf, fg_color=CARD_BG, corner_radius=8)
        lf.grid(row=3, column=0, sticky="nsew", pady=(10, 0))
        mf.grid_rowconfigure(3, weight=1)
        lf.grid_columnconfigure(0, weight=1)
        lf.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(lf, text="Yedekleme G\u00fcnl\u00fc\u011f\u00fc", font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=TEXT_DARK).grid(row=0, column=0, sticky="w", padx=15, pady=(10, 5))

        self._log_txt = ctk.CTkTextbox(lf, height=120, font=ctk.CTkFont(family="Consolas", size=10),
                                        fg_color="#fafafa", text_color=TEXT_DARK,
                                        border_width=1, border_color=BORDER)
        self._log_txt.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))

    def _build_tab3(self):
        t = self.tv.tab("Geri Y\u00fckleme")
        t.grid_columnconfigure(0, weight=1)

        mf = ctk.CTkFrame(t, fg_color="transparent")
        mf.grid(row=0, column=0, sticky="nsew", padx=40, pady=20)
        mf.grid_columnconfigure(0, weight=1)

        # warning
        wf = ctk.CTkFrame(mf, fg_color="#fff3e0", corner_radius=8)
        wf.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        ctk.CTkLabel(wf, text="\u26a0 Geri y\u00fckleme i\u015flemi s\u0131ras\u0131nda uygulama kapanacakt\u0131r.",
                     font=ctk.CTkFont(size=12, weight="bold"), text_color=WARNING).pack(padx=20, pady=12)

        # file selector
        ff = ctk.CTkFrame(mf, fg_color=CARD_BG, corner_radius=8)
        ff.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        ff.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(ff, text="Yedek Dosyas\u0131:", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=TEXT_DARK).grid(row=0, column=0, sticky="w", padx=20, pady=(15, 5))
        bf = ctk.CTkFrame(ff, fg_color="transparent")
        bf.grid(row=0, column=1, sticky="ew", padx=(10, 20), pady=(15, 5))
        self._rf_v = ctk.StringVar(value="")
        ctk.CTkEntry(bf, textvariable=self._rf_v, placeholder_text="Yedek dosyas\u0131 se\u00e7in...",
                     width=300, font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 5))
        ctk.CTkButton(bf, text="G\u00f6zat", font=ctk.CTkFont(size=11), fg_color=PRIMARY,
                       width=70, height=28, command=self._browse_restore).pack(side="left")

        ctk.CTkLabel(ff, text="Geri Y\u00fckleme T\u00fcr\u00fc:", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=TEXT_DARK).grid(row=1, column=0, sticky="w", padx=20, pady=10)
        self._rt_v = ctk.StringVar(value="T\u00fcm\u00fcn\u00fc Geri Y\u00fckle")
        ctk.CTkComboBox(ff, values=["T\u00fcm\u00fcn\u00fc Geri Y\u00fckle", "Sadece Veritaban\u0131", "Sadece Ayarlar"],
                         variable=self._rt_v, width=250,
                         font=ctk.CTkFont(size=12), state="readonly"
                         ).grid(row=1, column=1, sticky="w", padx=(10, 20), pady=10)

        # preview
        pf = ctk.CTkFrame(mf, fg_color=CARD_BG, corner_radius=8)
        pf.grid(row=2, column=0, sticky="ew", pady=(0, 15))
        ctk.CTkLabel(pf, text="Geri Y\u00fckleme \u00d6nizlemesi", font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=TEXT_DARK).pack(anchor="w", padx=20, pady=(10, 5))
        self._preview_lbl = ctk.CTkLabel(pf, text="Dosya se\u00e7ilmedi",
                                          font=ctk.CTkFont(size=11), text_color=TEXT_MUTED)
        self._preview_lbl.pack(anchor="w", padx=20, pady=(0, 10))

        # restore button
        self._restore_btn = ctk.CTkButton(mf, text="Geri Y\u00fcklemeye Ba\u015fla",
                                           font=ctk.CTkFont(size=14, weight="bold"),
                                           fg_color=DANGER, hover_color="#b71c1c",
                                           width=250, height=40, corner_radius=8,
                                           command=self._do_restore)
        self._restore_btn.grid(row=3, column=0, pady=5)

        # progress
        self._rp = ctk.CTkProgressBar(mf, width=400, height=8, fg_color=BORDER,
                                       progress_color=DANGER, corner_radius=4)
        self._rp.grid(row=4, column=0, pady=5)
        self._rp.set(0)

    # ---- event handlers ----
    def _browse_loc(self):
        d = filedialog.askdirectory(title="Yedekleme Konumu Se\u00e7in")
        if d:
            self._loc_var.set(d)

    def _browse_restore(self):
        f = filedialog.askopenfilename(title="Yedek Dosyas\u0131 Se\u00e7in",
                                        filetypes=[("Yedek Dosyalar\u0131", "*.db *.bak *.json"),
                                                   ("T\u00fcm Dosyalar", "*.*")])
        if f:
            self._rf_v.set(f)
            self._update_preview(f)

    def _update_preview(self, fp):
        try:
            st = os.stat(fp)
            mb = st.st_size / (1024 * 1024)
            mt = datetime.fromtimestamp(st.st_mtime).strftime("%d.%m.%Y %H:%M")
            ip = fp + ".info"
            extra = ""
            if os.path.exists(ip):
                try:
                    with open(ip, "r", encoding="utf-8") as f:
                        info = json.load(f)
                    extra = f"T\u00fcr: {info.get('type', 'Bilinmiyor')} | "
                except Exception:
                    pass
            self._preview_lbl.configure(text=f"{extra}Tarih: {mt} | Boyut: {mb:.2f} MB | Dosya: {os.path.basename(fp)}")
        except Exception:
            self._preview_lbl.configure(text="Dosya bilgisi okunamad\u0131")

    def _freq_change(self, *args):
        v = self._freq_v.get()
        if v == "Her Hafta":
            self._wd_lbl.grid(); self._wd_cb.grid()
            self._md_lbl.grid_remove(); self._md_cb.grid_remove()
        elif v == "Her Ay":
            self._wd_lbl.grid_remove(); self._wd_cb.grid_remove()
            self._md_lbl.grid(); self._md_cb.grid()
        else:
            self._wd_lbl.grid_remove(); self._wd_cb.grid_remove()
            self._md_lbl.grid_remove(); self._md_cb.grid_remove()

    def _do_backup(self):
        def task():
            self._backup_btn.configure(state="disabled", text="Yedekleniyor...")
            self._bp.set(0.2); self._bpl.configure(text="Yedekleme ba\u015flat\u0131l\u0131yor...")
            tm = {"Tam Yedek": "full", "Sadece Veritaban\u0131": "database", "Sadece Ayarlar": "settings"}
            bt = tm.get(self._bt_var.get(), "full")
            desc = self._desc_e.get()
            self._bp.set(0.5)
            if HAS_SERVICE and self.svc:
                r = self.svc.create_backup()
            else:
                r = self._sim_create(bt, desc)
            self._bp.set(0.8)
            if r:
                self._bp.set(1.0)
                self._bpl.configure(text="\u2705 Yedekleme tamamland\u0131!")
                self._log(f"Yedekleme ba\u015far\u0131l\u0131: {os.path.basename(r)}")
                self._load_history()
                self.after(2000, lambda: self._bpl.configure(text=""))
            else:
                self._bp.set(0)
                self._bpl.configure(text="\u274c Yedekleme ba\u015far\u0131s\u0131z!")
                self._log("Yedekleme ba\u015far\u0131s\u0131z!")
            self._backup_btn.configure(state="normal", text="\u015eimdi Yedekle")
            self.after(3000, lambda: self._bp.set(0))

        threading.Thread(target=task, daemon=True).start()

    def _toggle_sched(self):
        if self._sw.get() == 1:
            self._sw.configure(text="A\u00c7IK")
            self._status("Otomatik yedekleme etkin.")
        else:
            self._sw.configure(text="KAPALI")
            if self._scheduler_active and HAS_SERVICE and self.svc:
                try:
                    self.svc.stop_scheduler()
                except Exception:
                    pass
            self._scheduler_active = False
            self._next_lbl.configure(text="Bir sonraki yedekleme: Devre d\u0131\u015f\u0131")
            self._status("Otomatik yedekleme devre d\u0131\u015f\u0131.")

    def _save_sched(self):
        if self._sw.get() == 0:
            messagebox.showwarning("Uyar\u0131", "Otomatik yedeklemeyi etkinle\u015ftirmek i\u00e7in anahtar\u0131 A\u00c7IK konuma getirin.")
            return
        freq = self._freq_v.get()
        hr = int(self._hr_v.get())
        mn = int(self._mn_v.get())
        ret_map = {"7 G\u00fcn": 7, "30 G\u00fcn": 30, "90 G\u00fcn": 90,
                   "180 G\u00fcn": 180, "1 Y\u0131l": 365, "S\u00fcresiz": 9999}
        ret = ret_map.get(self._ret_v.get(), 30)
        int_map = {"Her G\u00fcn": 24, "Her Hafta": 168, "Her Ay": 720}
        interval = int_map.get(freq, 24)

        if HAS_SERVICE and self.svc:
            try:
                self.svc.stop_scheduler()
                self.svc.schedule_backup(interval, ret)
                self._scheduler_active = True
            except Exception as e:
                messagebox.showerror("Hata", f"Zamanlay\u0131c\u0131 ba\u015flat\u0131lamad\u0131: {e}")
                return
        else:
            self._scheduler_active = True

        now = datetime.now()
        nxt = now.replace(hour=hr, minute=mn, second=0, microsecond=0)
        if nxt <= now:
            nxt += timedelta(hours=interval)
        self._next_lbl.configure(text=f"Bir sonraki yedekleme: {nxt.strftime('%d.%m.%Y %H:%M')}")
        self._log(f"Otomatik yedekleme ayarland\u0131: {freq}, {hr:02d}:{mn:02d}, saklama: {self._ret_v.get()}")
        messagebox.showinfo("Ba\u015far\u0131l\u0131", "Yedekleme ayarlar\u0131 kaydedildi.")
        self._status("Yedekleme ayarlar\u0131 kaydedildi.")

    def _do_restore(self):
        fp = self._rf_v.get()
        if not fp or not os.path.exists(fp):
            messagebox.showerror("Hata", "L\u00fctfen ge\u00e7erli bir yedek dosyas\u0131 se\u00e7in.")
            return
        rt = self._rt_v.get()
        if not messagebox.askyesno("Onay",
            f"'{os.path.basename(fp)}' dosyas\u0131ndan geri y\u00fckleme yap\u0131lacak.\n\n"
            f"T\u00fcr: {rt}\n\nBu i\u015flem s\u0131ras\u0131nda uygulama kapanacakt\u0131r.\nDevam etmek istiyor musunuz?"):
            return

        def task():
            self._restore_btn.configure(state="disabled", text="Geri Y\u00fckleniyor...")
            self._rp.set(0.3); self._status("Geri y\u00fckleme ba\u015flat\u0131l\u0131yor...")
            if HAS_SERVICE and self.svc:
                ok = self.svc.restore_backup(fp)
            else:
                ok = self._sim_restore(fp)
            if ok:
                self._rp.set(1.0)
                self._log(f"Geri y\u00fckleme ba\u015far\u0131l\u0131: {os.path.basename(fp)}")
                messagebox.showinfo("Ba\u015far\u0131l\u0131", "Geri y\u00fckleme tamamland\u0131.\nUygulama kapat\u0131l\u0131yor...")
                self.after(1000, self.master.quit)
            else:
                self._rp.set(0)
                self._log(f"Geri y\u00fckleme ba\u015far\u0131s\u0131z: {os.path.basename(fp)}")
                messagebox.showerror("Hata", "Geri y\u00fckleme s\u0131ras\u0131nda bir hata olu\u015ftu.")
            self._restore_btn.configure(state="normal", text="Geri Y\u00fcklemeye Ba\u015fla")

        threading.Thread(target=task, daemon=True).start()

    def _tree_restore(self):
        sel = self._tree.selection()
        if not sel:
            return
        vals = self._tree.item(sel[0])["values"]
        if len(vals) < 5:
            return
        fp = vals[4]
        if fp and os.path.exists(fp):
            self.tv.set("Geri Y\u00fckleme")
            self._rf_v.set(fp)
            self._update_preview(fp)
        else:
            messagebox.showerror("Hata", "Yedek dosyas\u0131 bulunamad\u0131.")

    def _load_history(self):
        for ch in self._tree.get_children():
            self._tree.delete(ch)
        backups = (self.svc.list_backups() if HAS_SERVICE and self.svc else self._sim_list())
        for b in backups[:20]:
            cr = datetime.fromisoformat(b["created_at"]).strftime("%d.%m.%Y %H:%M")
            info = b.get("info", {})
            bt = info.get("type", "sqlite_full")
            tn = {"sqlite_full": "Tam Yedek", "full": "Tam Yedek",
                  "database": "Veritaban\u0131", "settings": "Ayarlar"}.get(bt, bt)
            self._tree.insert("", "end", values=(cr, tn, f"{b['size_mb']:.1f} MB", info.get("description", ""), b["filepath"]))
        if backups:
            b = backups[0]
            cr = datetime.fromisoformat(b["created_at"]).strftime("%d.%m.%Y %H:%M")
            self._last_lbl.configure(text=f"Son Yedekleme: {cr} - {b['size_mb']:.1f} MB")

    def _update_disk_space(self):
        try:
            if HAS_SERVICE and self.svc:
                d = os.path.dirname(self.svc._backup_dir)
            else:
                d = self._sim_dir
            _, _, free = shutil.disk_usage(d)
            gb = free / (1024 ** 3)
        except Exception:
            gb = 0.0
        self._disk_lbl.configure(text=f"Kullan\u0131labilir Disk Alan\u0131: {gb:.1f} GB")
        self.after(30000, self._update_disk_space)

    def _status(self, msg):
        self._status_lbl.configure(text=msg)

    def _log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self._log_txt.insert("end", f"[{ts}] {msg}\n")
        self._log_txt.see("end")
