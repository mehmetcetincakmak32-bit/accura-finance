import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import threading
import sys
import os
import re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PRIMARY = "#1565c0"
PRIMARY_DARK = "#0d47a1"
PRIMARY_LIGHT = "#42a5f5"
SUCCESS = "#2e7d32"
DANGER = "#c62828"
WARNING = "#f57f17"
TEXT_DARK = "#1a1a2e"
TEXT_MUTED = "#6c757d"
BORDER = "#e8eaed"
CARD_BG = "#ffffff"

DAYS_OPTIONS = ["1 g\u00fcn", "3 g\u00fcn", "7 g\u00fcn", "14 g\u00fcn", "30 g\u00fcn"]
DAYS_VALUES = ["1", "3", "7", "14", "30"]
WEEK_DAYS = ["Pazartesi", "Sal\u0131", "\u00c7ar\u015famba", "Per\u015fembe", "Cuma", "Cumartesi", "Pazar"]


class NotificationSettingsFrame(ctk.CTkFrame):
    def __init__(self, parent, main_app):
        super().__init__(parent)
        self.main_app = main_app
        self.db_manager = main_app.db_manager
        self.notification_service = None
        self._init_service()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._create_header()
        self._create_tabs()
        self._load_all_settings()

    def _init_service(self):
        try:
            from src.services.notification_service import NotificationService
            self.notification_service = NotificationService(self.db_manager)
        except Exception:
            self.notification_service = None

    def _create_header(self):
        header = ctk.CTkFrame(self, height=60, corner_radius=10, fg_color=CARD_BG)
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        header.grid_propagate(False)
        ctk.CTkLabel(
            header, text="B\u0130LD\u0130R\u0130M AYARLARI",
            font=ctk.CTkFont(size=24, weight="bold"), text_color=PRIMARY_DARK
        ).pack(side="left", padx=20, pady=15)
        ctk.CTkLabel(
            header, text="E-posta ve SMS bildirim y\u00f6netimi",
            font=ctk.CTkFont(size=12), text_color=TEXT_MUTED
        ).pack(side="left", padx=5, pady=15)

    def _create_tabs(self):
        self.tabview = ctk.CTkTabview(self, corner_radius=10, fg_color=CARD_BG)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 10))
        self.tabview._segmented_button.configure(font=ctk.CTkFont(size=13, weight="bold"))

        self.tabview.add("E-posta Ayarlar\u0131")
        self.tabview.add("SMS Ayarlar\u0131")
        self.tabview.add("Bildirim Tercihleri")

        self._create_email_tab()
        self._create_sms_tab()
        self._create_preferences_tab()

    # ── Helpers ──────────────────────────────

    def _make_form_row(self, parent, row, label, widget, label_col=0, widget_col=1):
        lbl = ctk.CTkLabel(
            parent, text=label, font=ctk.CTkFont(size=12, weight="bold"),
            text_color=TEXT_DARK, anchor="w", width=150
        )
        lbl.grid(row=row, column=label_col, sticky="w", padx=(10, 5), pady=4)
        widget.grid(row=row, column=widget_col, sticky="ew", padx=(0, 10), pady=4)
        return lbl

    def _make_section_title(self, parent, text, row):
        sep = ctk.CTkFrame(parent, height=1, fg_color=BORDER)
        sep.grid(row=row, column=0, columnspan=2, sticky="ew", padx=10, pady=(8, 2))
        lbl = ctk.CTkLabel(
            parent, text=text, font=ctk.CTkFont(size=14, weight="bold"),
            text_color=PRIMARY, anchor="w"
        )
        lbl.grid(row=row + 1, column=0, columnspan=2, sticky="w", padx=10, pady=(2, 4))
        return row + 2

    def _save_setting(self, key, value):
        if not self.db_manager:
            return
        try:
            existing = self.db_manager.execute_query(
                "SELECT COUNT(*) as cnt FROM SystemSettings WHERE SettingKey = ?", (key,)
            )
            if existing and existing[0]["cnt"] > 0:
                self.db_manager.execute_query(
                    "UPDATE SystemSettings SET SettingValue = ?, UpdatedDate = datetime('now','localtime') WHERE SettingKey = ?",
                    (str(value), key), fetch=False
                )
            else:
                self.db_manager.execute_query(
                    "INSERT INTO SystemSettings (SettingKey, SettingValue, Description) VALUES (?, ?, 'Bildirim ayari')",
                    (key, str(value)), fetch=False
                )
        except Exception:
            pass

    def _show_status(self, label, success, message):
        if success:
            label.configure(text=f"\u2713 {message}", text_color=SUCCESS)
        else:
            label.configure(text=f"\u2717 {message}", text_color=DANGER)

    def _run_async(self, target, callback):
        threading.Thread(target=lambda: self._async_wrapper(target, callback), daemon=True).start()

    def _async_wrapper(self, target, callback):
        result = target()
        self.after(0, lambda: callback(result))

    # ── Tab 1: E-posta Ayarlar─ ──────────────

    def _create_email_tab(self):
        tab = self.tabview.tab("E-posta Ayarlar\u0131")
        tab.grid_columnconfigure(1, weight=1)

        canvas = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        canvas.pack(fill="both", expand=True, padx=5, pady=5)
        canvas.grid_columnconfigure(1, weight=1)

        r = 0
        r = self._make_section_title(canvas, "SMTP Sunucu Bilgileri", r)
        r += 1

        self.email_smtp_server = ctk.CTkEntry(canvas, height=30, border_color=BORDER, fg_color="#ffffff", text_color=TEXT_DARK)
        self.email_smtp_server.insert(0, "smtp.gmail.com")
        self._make_form_row(canvas, r, "SMTP Sunucu:", self.email_smtp_server)
        r += 1

        self.email_port = ctk.CTkEntry(canvas, height=30, border_color=BORDER, fg_color="#ffffff", text_color=TEXT_DARK)
        self.email_port.insert(0, "587")
        self._make_form_row(canvas, r, "Port:", self.email_port)
        r += 1

        self.email_security = ctk.CTkComboBox(canvas, values=["TLS", "SSL", "Yok"], height=30,
                                              border_color=BORDER, fg_color="#ffffff", text_color=TEXT_DARK, state="readonly")
        self.email_security.set("TLS")
        self._make_form_row(canvas, r, "G\u00fcvenlik:", self.email_security)
        r += 1

        r = self._make_section_title(canvas, "Hesap Bilgileri", r)
        r += 1

        self.email_username = ctk.CTkEntry(canvas, height=30, border_color=BORDER, fg_color="#ffffff", text_color=TEXT_DARK)
        self._make_form_row(canvas, r, "Kullan\u0131c\u0131 Ad\u0131:", self.email_username)
        r += 1

        self.email_password = ctk.CTkEntry(canvas, height=30, border_color=BORDER, fg_color="#ffffff", text_color=TEXT_DARK, show="*")
        self._make_form_row(canvas, r, "\u015eifre:", self.email_password)
        r += 1

        self.email_sender_name = ctk.CTkEntry(canvas, height=30, border_color=BORDER, fg_color="#ffffff", text_color=TEXT_DARK)
        self._make_form_row(canvas, r, "G\u00f6nderici Ad\u0131:", self.email_sender_name)
        r += 1

        self.email_sender_addr = ctk.CTkEntry(canvas, height=30, border_color=BORDER, fg_color="#ffffff", text_color=TEXT_DARK)
        self._make_form_row(canvas, r, "G\u00f6nderici E-posta:", self.email_sender_addr)
        r += 1

        r += 1
        btn_row = ctk.CTkFrame(canvas, fg_color="transparent")
        btn_row.grid(row=r, column=0, columnspan=2, sticky="w", padx=10, pady=6)

        self.email_status = ctk.CTkLabel(btn_row, text="", font=ctk.CTkFont(size=12))
        self.email_status.pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_row, text="Ba\u011flant\u0131y\u0131 Test Et",
            command=self._test_email_connection,
            fg_color=PRIMARY, hover_color=PRIMARY_DARK,
            font=ctk.CTkFont(size=12, weight="bold"), height=32
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_row, text="Ayarlar\u0131 Kaydet",
            command=self._save_email_settings,
            fg_color=SUCCESS, hover_color="#1b5e20",
            font=ctk.CTkFont(size=12, weight="bold"), height=32
        ).pack(side="left", padx=5)

    def _test_email_connection(self):
        self.email_status.configure(text="Test ediliyor...", text_color=WARNING)
        self._save_email_settings_to_service()
        self._run_async(
            target=lambda: self.notification_service.test_email_connection() if self.notification_service else {"success": False, "message": "Servis y\u00fcklenemedi"},
            callback=lambda r: self._show_status(self.email_status, r["success"], r["message"])
        )

    def _save_email_settings_to_service(self):
        if not self.notification_service:
            return
        settings = {
            "smtp_server": self.email_smtp_server.get(),
            "smtp_port": self.email_port.get(),
            "use_tls": "true" if self.email_security.get() == "TLS" else "false",
            "use_ssl": "true" if self.email_security.get() == "SSL" else "false",
            "smtp_username": self.email_username.get(),
            "smtp_password": self.email_password.get(),
            "from_name": self.email_sender_name.get(),
            "from_address": self.email_sender_addr.get(),
        }
        self.notification_service._save_email_settings(settings)

    def _save_email_settings(self):
        self._save_email_settings_to_service()
        self._show_status(self.email_status, True, "E-posta ayarlar\u0131 kaydedildi")

    # ── Tab 2: SMS Ayarlar─ ────────────────

    def _create_sms_tab(self):
        tab = self.tabview.tab("SMS Ayarlar\u0131")
        tab.grid_columnconfigure(1, weight=1)

        canvas = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        canvas.pack(fill="both", expand=True, padx=5, pady=5)
        canvas.grid_columnconfigure(1, weight=1)

        r = 0
        r = self._make_section_title(canvas, "Sa\u011flay\u0131c\u0131 Bilgileri", r)
        r += 1

        self.sms_provider = ctk.CTkComboBox(canvas, values=["NetGSM", "Telsam", "IletiMerkezi", "SMS765", "custom"],
                                            height=30, border_color=BORDER, fg_color="#ffffff", text_color=TEXT_DARK, state="readonly")
        self._make_form_row(canvas, r, "SMS Sa\u011flay\u0131c\u0131:", self.sms_provider)
        r += 1

        self.sms_api_key = ctk.CTkEntry(canvas, height=30, border_color=BORDER, fg_color="#ffffff", text_color=TEXT_DARK)
        self._make_form_row(canvas, r, "API Anahtar\u0131:", self.sms_api_key)
        r += 1

        self.sms_api_secret = ctk.CTkEntry(canvas, height=30, border_color=BORDER, fg_color="#ffffff", text_color=TEXT_DARK, show="*")
        self._make_form_row(canvas, r, "API \u015eifresi:", self.sms_api_secret)
        r += 1

        self.sms_sender = ctk.CTkEntry(canvas, height=30, border_color=BORDER, fg_color="#ffffff", text_color=TEXT_DARK)
        self.sms_sender.insert(0, "ACCURA")
        self._make_form_row(canvas, r, "G\u00f6nderici Ad\u0131:", self.sms_sender)
        r += 1

        r = self._make_section_title(canvas, "Test", r)
        r += 1

        self.sms_test_phone = ctk.CTkEntry(canvas, height=30, border_color=BORDER, fg_color="#ffffff", text_color=TEXT_DARK)
        self.sms_test_phone.insert(0, "05")
        self._make_form_row(canvas, r, "Telefon Numaras\u0131 (test):", self.sms_test_phone)
        r += 1

        r += 1
        btn_row = ctk.CTkFrame(canvas, fg_color="transparent")
        btn_row.grid(row=r, column=0, columnspan=2, sticky="w", padx=10, pady=6)

        self.sms_status = ctk.CTkLabel(btn_row, text="", font=ctk.CTkFont(size=12))
        self.sms_status.pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_row, text="Test SMS G\u00f6nder",
            command=self._test_sms,
            fg_color=PRIMARY, hover_color=PRIMARY_DARK,
            font=ctk.CTkFont(size=12, weight="bold"), height=32
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_row, text="Ayarlar\u0131 Kaydet",
            command=self._save_sms_settings,
            fg_color=SUCCESS, hover_color="#1b5e20",
            font=ctk.CTkFont(size=12, weight="bold"), height=32
        ).pack(side="left", padx=5)

    def _save_sms_settings_to_db(self):
        provider_map = {
            "NetGSM": "https://api.netgsm.com.tr/sms/send",
            "Telsam": "https://api.telsam.com.tr/v1/message",
            "IletiMerkezi": "https://api.iletimerkezi.com/v1/send",
            "SMS765": "https://api.sms765.com/v1/send",
        }
        provider = self.sms_provider.get()
        api_url = provider_map.get(provider, "")
        self._save_setting("sms.provider", provider)
        self._save_setting("sms.api_url", api_url)
        self._save_setting("sms.api_key", self.sms_api_key.get())
        self._save_setting("sms.api_secret", self.sms_api_secret.get())
        self._save_setting("sms.sender", self.sms_sender.get())

    def _save_sms_settings(self):
        self._save_sms_settings_to_db()
        self._show_status(self.sms_status, True, "SMS ayarlar\u0131 kaydedildi")

    def _test_sms(self):
        phone = self.sms_test_phone.get().strip()
        if not phone or len(phone) < 10:
            self._show_status(self.sms_status, False, "Ge\u00e7erli bir telefon numaras\u0131 girin")
            return
        self.sms_status.configure(text="G\u00f6nderiliyor...", text_color=WARNING)
        self._save_sms_settings_to_db()

        def _do_test():
            if not self.notification_service:
                return False
            return self.notification_service.send_sms(phone, "Accura Finance - Test mesaj\u0131")

        self._run_async(
            target=_do_test,
            callback=lambda ok: self._show_status(self.sms_status, ok, "SMS g\u00f6nderildi" if ok else "SMS g\u00f6nderilemedi")
        )

    # ── Tab 3: Bildirim Tercihleri ──────────

    def _create_preferences_tab(self):
        tab = self.tabview.tab("Bildirim Tercihleri")
        tab.grid_columnconfigure(0, weight=1)

        canvas = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        canvas.pack(fill="both", expand=True, padx=5, pady=5)
        canvas.grid_columnconfigure(1, weight=1)

        self._pref_widgets = {}
        r = 0

        header_lbl = ctk.CTkLabel(
            canvas, text="Bildirimleri \u00f6zelle\u015ftirin",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=PRIMARY, anchor="w"
        )
        header_lbl.grid(row=r, column=0, columnspan=3, sticky="w", padx=10, pady=(5, 10))
        r += 1

        prefs = [
            ("overdue_invoices", "Vadesi Gelen Faturalar", "switch", "days"),
            ("critical_stock", "Kritik Stok Seviyesi", "switch", None),
            ("customer_movements", "Cari Hesap Hareketleri", "switch", None),
            ("daily_sales", "G\u00fcnl\u00fck Sat\u0131\u015f Raporu", "switch", "time"),
            ("weekly_summary", "Haftal\u0131k \u00d6zet", "switch", "day"),
            ("monthly_report", "Ayl\u0131k Muhasebe Raporu", "switch", None),
            ("system_errors", "Sistem Hatalar\u0131", "switch", None),
            ("new_user", "Yeni Kullan\u0131c\u0131 Kayd\u0131", "switch", None),
            ("pos_endofday", "POS G\u00fcn Sonu", "switch", None),
        ]

        sub_keys = {
            "overdue_invoices": "overdue_days",
            "daily_sales": "daily_sales_time",
            "weekly_summary": "weekly_summary_day",
        }

        sub_defaults = {
            "overdue_days": "7",
            "daily_sales_time": "18:00",
            "weekly_summary_day": "Pazartesi",
        }

        sub_widgets_map = {
            "overdue_days": ("combo", DAYS_OPTIONS, DAYS_VALUES),
            "daily_sales_time": ("entry", None, None),
            "weekly_summary_day": ("combo", WEEK_DAYS, WEEK_DAYS),
        }

        self._pref_switches = {}
        self._pref_extras = {}

        for key, label, ftype, extra in prefs:
            row_frame = ctk.CTkFrame(canvas, fg_color="transparent")
            row_frame.grid(row=r, column=0, sticky="ew", padx=10, pady=3)
            row_frame.grid_columnconfigure(0, weight=0)
            row_frame.grid_columnconfigure(1, weight=1)
            row_frame.grid_columnconfigure(2, weight=0)

            var = tk.BooleanVar()
            switch = ctk.CTkSwitch(row_frame, text="", variable=var, onvalue=True, offvalue=False,
                                   command=lambda k=key: self._on_pref_toggle(k))
            switch.grid(row=0, column=0, padx=(0, 8))
            self._pref_switches[key] = var

            lbl = ctk.CTkLabel(row_frame, text=label, font=ctk.CTkFont(size=12), text_color=TEXT_DARK, anchor="w")
            lbl.grid(row=0, column=1, sticky="w")

            extra_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            extra_frame.grid(row=0, column=2, padx=(5, 0))

            sub_key = sub_keys.get(key)
            if sub_key:
                stype, opts, vals = sub_widgets_map[sub_key]
                if stype == "combo":
                    w = ctk.CTkComboBox(extra_frame, values=opts, height=28,
                                        border_color=BORDER, fg_color="#ffffff", text_color=TEXT_DARK, state="readonly")
                    w.set(sub_defaults[sub_key])
                    w.pack(side="left")
                else:
                    w = ctk.CTkEntry(extra_frame, height=28, width=80, border_color=BORDER,
                                     fg_color="#ffffff", text_color=TEXT_DARK)
                    w.insert(0, sub_defaults[sub_key])
                    w.pack(side="left")

                if sub_key == "overdue_days":
                    lbl2 = ctk.CTkLabel(extra_frame, text="\u00f6nce", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED)
                    lbl2.pack(side="left", padx=(4, 0))
                elif sub_key == "daily_sales_time":
                    lbl2 = ctk.CTkLabel(extra_frame, text="saatinde", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED)
                    lbl2.pack(side="left", padx=(4, 0))
                elif sub_key == "weekly_summary_day":
                    lbl2 = ctk.CTkLabel(extra_frame, text="g\u00fcn\u00fc", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED)
                    lbl2.pack(side="left", padx=(4, 0))

                self._pref_extras[sub_key] = w
            else:
                ctk.CTkLabel(extra_frame, text="").pack()

            r += 1

        r += 1
        bottom = ctk.CTkFrame(canvas, fg_color="transparent")
        bottom.grid(row=r, column=0, sticky="w", padx=10, pady=10)

        self.pref_status = ctk.CTkLabel(bottom, text="", font=ctk.CTkFont(size=12))
        self.pref_status.pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            bottom, text="Tercihleri Kaydet",
            command=self._save_preferences,
            fg_color=SUCCESS, hover_color="#1b5e20",
            font=ctk.CTkFont(size=12, weight="bold"), height=32
        ).pack(side="left")

    def _on_pref_toggle(self, key):
        pass

    def _save_preferences(self):
        prefs = {}
        for key, var in self._pref_switches.items():
            prefs[f"notification.{key}"] = "1" if var.get() else "0"
        for sub_key, widget in self._pref_extras.items():
            prefs[f"notification.{sub_key}"] = widget.get()
        for key, val in prefs.items():
            self._save_setting(key, val)
        self._show_status(self.pref_status, True, "Bildirim tercihleri kaydedildi")

    # ── Load ────────────────────────────────

    def _load_all_settings(self):
        if not self.db_manager:
            return
        try:
            rows = self.db_manager.execute_query(
                "SELECT SettingKey, SettingValue FROM SystemSettings WHERE SettingKey LIKE 'email.%' OR SettingKey LIKE 'sms.%' OR SettingKey LIKE 'notification.%'"
            )
            settings = {row["SettingKey"]: row["SettingValue"] for row in (rows or [])}
            self._populate_email(settings)
            self._populate_sms(settings)
            self._populate_preferences(settings)
        except Exception:
            pass

    def _populate_email(self, settings):
        if settings.get("email.smtp_server"):
            self.email_smtp_server.delete(0, "end")
            self.email_smtp_server.insert(0, settings["email.smtp_server"])
        if settings.get("email.smtp_port"):
            self.email_port.delete(0, "end")
            self.email_port.insert(0, settings["email.smtp_port"])
        use_tls = settings.get("email.use_tls", "true")
        use_ssl = settings.get("email.use_ssl", "false")
        if use_ssl == "true":
            self.email_security.set("SSL")
        elif use_tls == "true":
            self.email_security.set("TLS")
        else:
            self.email_security.set("Yok")
        if settings.get("email.smtp_username"):
            self.email_username.delete(0, "end")
            self.email_username.insert(0, settings["email.smtp_username"])
        if settings.get("email.smtp_password"):
            self.email_password.delete(0, "end")
            self.email_password.insert(0, settings["email.smtp_password"])
        if settings.get("email.from_name"):
            self.email_sender_name.delete(0, "end")
            self.email_sender_name.insert(0, settings["email.from_name"])
        if settings.get("email.from_address"):
            self.email_sender_addr.delete(0, "end")
            self.email_sender_addr.insert(0, settings["email.from_address"])

    def _populate_sms(self, settings):
        if settings.get("sms.provider"):
            self.sms_provider.set(settings["sms.provider"])
        if settings.get("sms.api_key"):
            self.sms_api_key.delete(0, "end")
            self.sms_api_key.insert(0, settings["sms.api_key"])
        if settings.get("sms.api_secret"):
            self.sms_api_secret.delete(0, "end")
            self.sms_api_secret.insert(0, settings["sms.api_secret"])
        if settings.get("sms.sender"):
            self.sms_sender.delete(0, "end")
            self.sms_sender.insert(0, settings["sms.sender"])

    def _populate_preferences(self, settings):
        for key, var in self._pref_switches.items():
            val = settings.get(f"notification.{key}", "0")
            var.set(val == "1")
        for sub_key, widget in self._pref_extras.items():
            val = settings.get(f"notification.{sub_key}")
            if val:
                if isinstance(widget, ctk.CTkComboBox):
                    widget.set(val)
                else:
                    widget.delete(0, "end")
                    widget.insert(0, val)
