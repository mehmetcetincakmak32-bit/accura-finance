import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import hashlib
import sys
import os

PRIMARY = "#1565c0"
PRIMARY_DARK = "#0d47a1"
SUCCESS = "#2e7d32"
DANGER = "#c62828"
TEXT_DARK = "#1a1a2e"
TEXT_MUTED = "#6c757d"
BORDER = "#e8eaed"


class SettingsFrame(ctk.CTkFrame):
    def __init__(self, parent, main_app):
        super().__init__(parent)
        self.main_app = main_app
        self.db_manager = main_app.db_manager
        self.use_db = False
        self.users = []
        self.system_settings = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.create_header()
        self.create_tabs()
        self.load_initial_data()

    def create_header(self):
        header = ctk.CTkFrame(self, height=60, corner_radius=10, fg_color="#ffffff")
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        header.grid_propagate(False)
        ctk.CTkLabel(
            header, text="AYARLAR",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=PRIMARY_DARK
        ).pack(side="left", padx=20, pady=15)
        ctk.CTkLabel(
            header, text="Sirket Bilgileri - Kullanicilar - Sistem Ayarlari",
            font=ctk.CTkFont(size=12), text_color=TEXT_MUTED
        ).pack(side="left", padx=5, pady=15)

    def create_tabs(self):
        self.tabview = ctk.CTkTabview(self, corner_radius=10, fg_color="#ffffff")
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 10))
        self.tabview._segmented_button.configure(font=ctk.CTkFont(size=13, weight="bold"))

        self.tabview.add("Sirket Bilgileri")
        self.tabview.add("Kullanicilar")
        self.tabview.add("Sistem Ayarlari")

        self.create_company_tab()
        self.create_users_tab()
        self.create_system_settings_tab()

    def load_initial_data(self):
        if self.db_manager:
            self.check_and_create_tables()
        if not self.use_db:
            self.load_sample_data()

    def check_and_create_tables(self):
        try:
            # Tables already exist from sqlite_adapter, no need to CREATE
            self.use_db = True
            self.load_company_from_db()
            self.load_users_from_db()
            self.load_system_settings_from_db()
        except Exception:
            self.use_db = False

    def load_company_from_db(self):
        try:
            result = self.db_manager.execute_query(
                "SELECT * FROM Companies WHERE IsActive=1 ORDER BY CompanyID DESC LIMIT 1"
            )
            if result:
                self.company_data = result[0]
            else:
                self.company_data = {}
            self.populate_company_form()
        except Exception:
            self.company_data = {}

    def load_users_from_db(self):
        try:
            result = self.db_manager.execute_query(
                "SELECT UserID, Username, FullName, Email, Phone, Role, IsActive, LastLogin, CreatedDate "
                "FROM Users ORDER BY Username"
            )
            if result:
                self.users = result
            else:
                self.load_sample_users()
            self.refresh_users_tree()
        except Exception:
            self.load_sample_users()

    def load_system_settings_from_db(self):
        try:
            result = self.db_manager.execute_query(
                "SELECT SettingKey, SettingValue, Description FROM SystemSettings ORDER BY SettingKey"
            )
            if result:
                self.system_settings = {s["SettingKey"]: s for s in result}
            else:
                self.system_settings = {}
            self.populate_settings_form()
        except Exception:
            self.system_settings = {}

    def load_sample_data(self):
        self.company_data = {}
        self.load_sample_users()
        self.system_settings = {}

    def load_sample_users(self):
        self.users = [
            {"UserID": 1, "Username": "admin", "FullName": "Admin Kullanici",
             "Email": "admin@accurafinance.com", "Phone": "0555 111 22 33",
             "Role": "Admin", "IsActive": 1, "LastLogin": "2025-01-15 10:30:00"},
            {"UserID": 2, "Username": "muhasebe", "FullName": "Muhasebe Uzmani",
             "Email": "muhasebe@accurafinance.com", "Phone": "0555 222 33 44",
             "Role": "Muhasebeci", "IsActive": 1, "LastLogin": "2025-01-14 09:15:00"},
            {"UserID": 3, "Username": "depo", "FullName": "Depo Sorumlusu",
             "Email": "depo@accurafinance.com", "Phone": "0555 333 44 55",
             "Role": "Kullanici", "IsActive": 0, "LastLogin": "2024-12-20 14:00:00"},
        ]

    # =====================================================================
    # TAB 1: SIRKET BILGILERI
    # =====================================================================
    def create_company_tab(self):
        tab = self.tabview.tab("Sirket Bilgileri")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        scroll_frame = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        scroll_frame.grid_columnconfigure(0, weight=1)

        card = ctk.CTkFrame(scroll_frame, corner_radius=10, fg_color="#ffffff",
                             border_width=1, border_color=BORDER)
        card.pack(fill="x", padx=5, pady=5)
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(card, text="SIRKET BILGILERI",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=PRIMARY_DARK).grid(row=0, column=0, columnspan=2,
                                                   sticky="w", padx=20, pady=(16, 12))

        self.company_entries = {}
        fields = [
            ("Sirket Adi", "CompanyName"),
            ("Vergi No", "TaxNumber"),
            ("Vergi Dairesi", "TaxOffice"),
            ("Adres", "Address"),
            ("Telefon", "Phone"),
            ("Email", "Email"),
            ("Web sitesi", "Website"),
        ]

        for i, (label, key) in enumerate(fields):
            row = i + 1
            ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=12, weight="bold"),
                         anchor="w").grid(row=row, column=0, sticky="w", padx=20, pady=6)
            e = ctk.CTkEntry(card, height=35, font=ctk.CTkFont(size=14))
            e.grid(row=row, column=1, sticky="ew", padx=(5, 20), pady=6)
            self.company_entries[key] = e

        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.grid(row=len(fields) + 1, column=0, columnspan=2, pady=(16, 16))

        ctk.CTkButton(btn_frame, text="Kaydet", command=self.save_company,
                       fg_color=SUCCESS, height=38,
                       font=ctk.CTkFont(size=14, weight="bold")
                       ).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Temizle", command=self.clear_company_form,
                       fg_color=TEXT_MUTED, height=38,
                       font=ctk.CTkFont(size=14, weight="bold")
                       ).pack(side="left", padx=5)

    def populate_company_form(self):
        if not hasattr(self, "company_entries"):
            return
        data = getattr(self, "company_data", {})
        if not data:
            return
        for key, entry in self.company_entries.items():
            val = data.get(key, "")
            entry.delete(0, "end")
            if val:
                entry.insert(0, str(val))

    def clear_company_form(self):
        for entry in self.company_entries.values():
            entry.delete(0, "end")

    def save_company(self):
        data = {}
        for key, entry in self.company_entries.items():
            data[key] = entry.get().strip()

        if not data.get("CompanyName"):
            messagebox.showwarning("Uyari", "Sirket adi zorunludur!")
            return
        if not data.get("TaxNumber"):
            messagebox.showwarning("Uyari", "Vergi no zorunludur!")
            return

        try:
            if self.use_db:
                existing = self.db_manager.execute_query(
                    "SELECT CompanyID FROM Companies WHERE IsActive=1 LIMIT 1"
                )
                if existing:
                    self.db_manager.execute_query(
                        "UPDATE Companies SET CompanyName=?, TaxNumber=?, TaxOffice=?, Address=?, "
                        "Phone=?, Email=?, Website=?, UpdatedDate=datetime('now','localtime') "
                        "WHERE CompanyID=?",
                        (data["CompanyName"], data["TaxNumber"], data["TaxOffice"],
                         data["Address"], data["Phone"], data["Email"], data["Website"],
                         existing[0]["CompanyID"]), fetch=False
                    )
                else:
                    self.db_manager.execute_query(
                        "INSERT INTO Companies (CompanyName, TaxNumber, TaxOffice, Address, Phone, Email, Website) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (data["CompanyName"], data["TaxNumber"], data["TaxOffice"],
                         data["Address"], data["Phone"], data["Email"], data["Website"]),
                        fetch=False
                    )
            else:
                self.company_data = data
            messagebox.showinfo("Basarili", "Sirket bilgileri kaydedildi!")
        except Exception as e:
            messagebox.showerror("Hata", str(e))

    # =====================================================================
    # TAB 2: KULLANICILAR
    # =====================================================================
    def create_users_tab(self):
        tab = self.tabview.tab("Kullanicilar")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        toolbar = ctk.CTkFrame(tab, fg_color="transparent", height=44)
        toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))

        ctk.CTkButton(toolbar, text="Kullanici Ekle", command=self.add_user_dialog,
                       fg_color=SUCCESS, hover_color="#1b5e20", height=34,
                       corner_radius=8, font=ctk.CTkFont(size=12, weight="bold")
                       ).pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text="Duzenle", command=self.edit_user_dialog,
                       fg_color=PRIMARY, hover_color=PRIMARY_DARK, height=34,
                       corner_radius=8, font=ctk.CTkFont(size=12, weight="bold")
                       ).pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text="Sil", command=self.delete_user,
                       fg_color=DANGER, hover_color="#b71c1c", height=34,
                       corner_radius=8, font=ctk.CTkFont(size=12, weight="bold")
                       ).pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text="Yenile", command=self.refresh_users_tree,
                       fg_color=TEXT_MUTED, hover_color="#5a6268", height=34,
                       corner_radius=8, font=ctk.CTkFont(size=12, weight="bold")
                       ).pack(side="right", padx=4)

        content = ctk.CTkFrame(tab, corner_radius=10, fg_color="#ffffff",
                                border_width=1, border_color=BORDER)
        content.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 10))
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)

        columns = ("Kullanici Adi", "Ad Soyad", "Email", "Rol", "Durum", "Son Giris")
        self.users_tree = ttk.Treeview(content, columns=columns, show="headings", height=20, selectmode="browse")
        widths_u = [120, 180, 200, 110, 80, 150]
        for col, w in zip(columns, widths_u):
            self.users_tree.heading(col, text=col)
            self.users_tree.column(col, width=w, anchor="center")

        scroll = ttk.Scrollbar(content, orient="vertical", command=self.users_tree.yview)
        self.users_tree.configure(yscrollcommand=scroll.set)
        self.users_tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scroll.grid(row=0, column=1, sticky="ns", pady=5)

    def refresh_users_tree(self):
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
        for u in self.users:
            durum = "Aktif" if u.get("IsActive", 1) else "Pasif"
            last_login = str(u.get("LastLogin", ""))[:16] if u.get("LastLogin") else "-"
            self.users_tree.insert("", "end", iid=str(u["UserID"]), values=(
                u.get("Username", ""),
                u.get("FullName", ""),
                u.get("Email", ""),
                u.get("Role", ""),
                durum,
                last_login
            ))

    def _user_dialog(self, title, user_data=None):
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("480x420")
        dialog.transient(self)
        dialog.grab_set()

        frame = ctk.CTkFrame(dialog, corner_radius=10, fg_color="#ffffff")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        is_edit = user_data is not None
        heading = "KULLANICI DUZENLE" if is_edit else "YENI KULLANICI"
        ctk.CTkLabel(frame, text=heading,
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=PRIMARY_DARK).pack(pady=(0, 20))

        form = ctk.CTkFrame(frame, fg_color="transparent")
        form.pack(fill="x", padx=10)
        form.grid_columnconfigure(1, weight=1)

        fields = {}

        ctk.CTkLabel(form, text="Kullanici Adi", font=ctk.CTkFont(size=12, weight="bold"),
                     anchor="w").grid(row=0, column=0, sticky="w", padx=10, pady=4)
        username_entry = ctk.CTkEntry(form, height=35, font=ctk.CTkFont(size=14))
        username_entry.grid(row=0, column=1, sticky="ew", padx=10, pady=4)
        fields["username"] = username_entry

        ctk.CTkLabel(form, text="Ad Soyad", font=ctk.CTkFont(size=12, weight="bold"),
                     anchor="w").grid(row=1, column=0, sticky="w", padx=10, pady=4)
        name_entry = ctk.CTkEntry(form, height=35, font=ctk.CTkFont(size=14))
        name_entry.grid(row=1, column=1, sticky="ew", padx=10, pady=4)
        fields["name"] = name_entry

        ctk.CTkLabel(form, text="Email", font=ctk.CTkFont(size=12, weight="bold"),
                     anchor="w").grid(row=2, column=0, sticky="w", padx=10, pady=4)
        email_entry = ctk.CTkEntry(form, height=35, font=ctk.CTkFont(size=14))
        email_entry.grid(row=2, column=1, sticky="ew", padx=10, pady=4)
        fields["email"] = email_entry

        ctk.CTkLabel(form, text="Telefon", font=ctk.CTkFont(size=12, weight="bold"),
                     anchor="w").grid(row=3, column=0, sticky="w", padx=10, pady=4)
        phone_entry = ctk.CTkEntry(form, height=35, font=ctk.CTkFont(size=14))
        phone_entry.grid(row=3, column=1, sticky="ew", padx=10, pady=4)
        fields["phone"] = phone_entry

        ctk.CTkLabel(form, text="Sifre", font=ctk.CTkFont(size=12, weight="bold"),
                     anchor="w").grid(row=4, column=0, sticky="w", padx=10, pady=4)
        pass_entry = ctk.CTkEntry(form, height=35, font=ctk.CTkFont(size=14), show="*")
        pass_entry.grid(row=4, column=1, sticky="ew", padx=10, pady=4)
        fields["password"] = pass_entry

        ctk.CTkLabel(form, text="Rol", font=ctk.CTkFont(size=12, weight="bold"),
                     anchor="w").grid(row=5, column=0, sticky="w", padx=10, pady=4)
        role_combo = ctk.CTkComboBox(form, values=["Admin", "Muhasebeci", "Kullanici"],
                                      height=35, font=ctk.CTkFont(size=14), state="readonly")
        role_combo.set("Kullanici")
        role_combo.grid(row=5, column=1, sticky="ew", padx=10, pady=4)
        fields["role"] = role_combo

        ctk.CTkLabel(form, text="Durum", font=ctk.CTkFont(size=12, weight="bold"),
                     anchor="w").grid(row=6, column=0, sticky="w", padx=10, pady=4)
        status_combo = ctk.CTkComboBox(form, values=["Aktif", "Pasif"],
                                        height=35, font=ctk.CTkFont(size=14), state="readonly")
        status_combo.set("Aktif")
        status_combo.grid(row=6, column=1, sticky="ew", padx=10, pady=4)
        fields["status"] = status_combo

        if is_edit:
            username_entry.insert(0, user_data.get("Username", ""))
            name_entry.insert(0, user_data.get("FullName", ""))
            email_entry.insert(0, user_data.get("Email", ""))
            phone_entry.insert(0, user_data.get("Phone", ""))
            role_combo.set(user_data.get("Role", "Kullanici"))
            status_combo.set("Aktif" if user_data.get("IsActive", 1) else "Pasif")
            pass_entry.configure(placeholder_text="(bos birakilirsa degismez)")

        return dialog, frame, fields

    def add_user_dialog(self):
        dialog, frame, fields = self._user_dialog("Kullanici Ekle")

        def save():
            username = fields["username"].get().strip()
            name = fields["name"].get().strip()
            password = fields["password"].get()

            if not username or not name:
                messagebox.showwarning("Uyari", "Kullanici adi ve ad soyad zorunludur!")
                return
            if not password:
                messagebox.showwarning("Uyari", "Sifre zorunludur!")
                return
            if len(password) < 4:
                messagebox.showwarning("Uyari", "Sifre en az 4 karakter olmalidir!")
                return

            try:
                pw_hash = hashlib.sha256(password.encode()).hexdigest()
                role = fields["role"].get()
                is_active = 1 if fields["status"].get() == "Aktif" else 0
                if self.use_db:
                    self.db_manager.execute_query(
                        "INSERT INTO Users (Username, PasswordHash, FullName, Email, Phone, Role, IsActive) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (username, pw_hash, name, fields["email"].get(), fields["phone"].get(), role, is_active),
                        fetch=False
                    )
                    self.load_users_from_db()
                else:
                    new_id = max(u.get("UserID", 0) for u in self.users) + 1
                    self.users.append({
                        "UserID": new_id, "Username": username, "FullName": name,
                        "Email": fields["email"].get(), "Phone": fields["phone"].get(),
                        "Role": role, "IsActive": is_active, "LastLogin": None
                    })
                    self.refresh_users_tree()
                messagebox.showinfo("Basarili", "Kullanici eklendi!")
                dialog.destroy()
            except Exception as e:
                err = str(e)
                if "UNIQUE" in err.upper():
                    messagebox.showerror("Hata", "Bu kullanici adi zaten mevcut!")
                else:
                    messagebox.showerror("Hata", err)

        ctk.CTkButton(frame, text="Kaydet", command=save,
                       fg_color=SUCCESS, height=40,
                       font=ctk.CTkFont(size=14, weight="bold")).pack(pady=15)

    def edit_user_dialog(self):
        sel = self.users_tree.selection()
        if not sel:
            messagebox.showwarning("Uyari", "Lutfen bir kullanici secin!")
            return
        uid = int(sel[0])
        user = next((u for u in self.users if u.get("UserID") == uid), None)
        if not user:
            return

        dialog, frame, fields = self._user_dialog("Kullanici Duzenle", user)

        def save():
            username = fields["username"].get().strip()
            name = fields["name"].get().strip()
            if not username or not name:
                messagebox.showwarning("Uyari", "Kullanici adi ve ad soyad zorunludur!")
                return
            try:
                role = fields["role"].get()
                is_active = 1 if fields["status"].get() == "Aktif" else 0
                password = fields["password"].get()
                if self.use_db:
                    if password:
                        pw_hash = hashlib.sha256(password.encode()).hexdigest()
                        self.db_manager.execute_query(
                            "UPDATE Users SET Username=?, FullName=?, Email=?, Phone=?, "
                            "Role=?, IsActive=?, PasswordHash=? WHERE UserID=?",
                            (username, name, fields["email"].get(), fields["phone"].get(),
                             role, is_active, pw_hash, uid), fetch=False
                        )
                    else:
                        self.db_manager.execute_query(
                            "UPDATE Users SET Username=?, FullName=?, Email=?, Phone=?, "
                            "Role=?, IsActive=? WHERE UserID=?",
                            (username, name, fields["email"].get(), fields["phone"].get(),
                             role, is_active, uid), fetch=False
                        )
                    self.load_users_from_db()
                else:
                    for u in self.users:
                        if u["UserID"] == uid:
                            u.update({"Username": username, "FullName": name,
                                      "Email": fields["email"].get(), "Phone": fields["phone"].get(),
                                      "Role": role, "IsActive": is_active})
                            break
                    self.refresh_users_tree()
                messagebox.showinfo("Basarili", "Kullanici guncellendi!")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Hata", str(e))

        ctk.CTkButton(frame, text="Kaydet", command=save,
                       fg_color=PRIMARY, height=40,
                       font=ctk.CTkFont(size=14, weight="bold")).pack(pady=15)

    def delete_user(self):
        sel = self.users_tree.selection()
        if not sel:
            messagebox.showwarning("Uyari", "Lutfen bir kullanici secin!")
            return
        uid = int(sel[0])
        user = next((u for u in self.users if u.get("UserID") == uid), None)
        if not user:
            return
        if user.get("Username") == "admin":
            messagebox.showwarning("Uyari", "Admin kullanici silinemez!")
            return
        if not messagebox.askyesno("Onay", f"{user['Username']} kullanici silinecek. Emin misiniz?"):
            return
        try:
            if self.use_db:
                self.db_manager.execute_query("DELETE FROM Users WHERE UserID=?", (uid,), fetch=False)
                self.load_users_from_db()
            else:
                self.users = [u for u in self.users if u.get("UserID") != uid]
                self.refresh_users_tree()
            messagebox.showinfo("Basarili", "Kullanici silindi!")
        except Exception as e:
            messagebox.showerror("Hata", str(e))

    # =====================================================================
    # TAB 3: SISTEM AYARLARI
    # =====================================================================
    def create_system_settings_tab(self):
        tab = self.tabview.tab("Sistem Ayarlari")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        scroll_frame = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        scroll_frame.grid_columnconfigure(0, weight=1)

        card = ctk.CTkFrame(scroll_frame, corner_radius=10, fg_color="#ffffff",
                             border_width=1, border_color=BORDER)
        card.pack(fill="x", padx=5, pady=5)
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(card, text="SISTEM AYARLARI",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=PRIMARY_DARK).grid(row=0, column=0, columnspan=2,
                                                   sticky="w", padx=20, pady=(16, 12))

        self.settings_entries = {}
        settings_fields = [
            ("Varsayilan KDV Orani", "default_vat_rate", "18"),
            ("Para Birimi", "currency", "TRY"),
            ("Fatura Seri", "invoice_series", "F"),
            ("Fatura Baslangic No", "invoice_start_number", "0001"),
            ("Alis Fatura Seri", "purchase_invoice_series", "AF"),
            ("Alis Fatura Baslangic No", "purchase_invoice_start", "0001"),
            ("Stok Giris Seri", "stock_entry_series", "SG"),
            ("Stok Cikis Seri", "stock_exit_series", "SC"),
            ("Kasa Hesap Kodu", "cash_account_code", "100.01"),
            ("Banka Hesap Kodu", "bank_account_code", "102.01"),
        ]

        for i, (label, key, default) in enumerate(settings_fields):
            row = i + 1
            ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=12, weight="bold"),
                         anchor="w").grid(row=row, column=0, sticky="w", padx=20, pady=6)
            e = ctk.CTkEntry(card, height=35, font=ctk.CTkFont(size=14))
            e.grid(row=row, column=1, sticky="ew", padx=(5, 20), pady=6)
            e.insert(0, default)
            self.settings_entries[key] = (label, e)

        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.grid(row=len(settings_fields) + 1, column=0, columnspan=2, pady=(16, 16))

        ctk.CTkButton(btn_frame, text="Kaydet", command=self.save_system_settings,
                       fg_color=SUCCESS, height=38,
                       font=ctk.CTkFont(size=14, weight="bold")
                       ).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Varsayilana Don", command=self.reset_settings_form,
                       fg_color=TEXT_MUTED, height=38,
                       font=ctk.CTkFont(size=14, weight="bold")
                       ).pack(side="left", padx=5)

        # Description
        ctk.CTkLabel(card, text="Bu ayarlar fatura, stok ve muhasebe modullerinde kullanilir.",
                     font=ctk.CTkFont(size=11), text_color=TEXT_MUTED
                     ).grid(row=len(settings_fields) + 2, column=0, columnspan=2,
                            sticky="w", padx=20, pady=(0, 12))

    def populate_settings_form(self):
        if not hasattr(self, "settings_entries"):
            return
        defaults = {
            "default_vat_rate": "18", "currency": "TRY", "invoice_series": "F",
            "invoice_start_number": "0001", "purchase_invoice_series": "AF",
            "purchase_invoice_start": "0001", "stock_entry_series": "SG",
            "stock_exit_series": "SC", "cash_account_code": "100.01",
            "bank_account_code": "102.01",
        }
        for key, (label, entry) in self.settings_entries.items():
            entry.delete(0, "end")
            if key in self.system_settings:
                val = self.system_settings[key].get("SettingValue", "")
                entry.insert(0, str(val) if val else defaults.get(key, ""))
            else:
                entry.insert(0, defaults.get(key, ""))

    def reset_settings_form(self):
        defaults = {
            "default_vat_rate": "18", "currency": "TRY", "invoice_series": "F",
            "invoice_start_number": "0001", "purchase_invoice_series": "AF",
            "purchase_invoice_start": "0001", "stock_entry_series": "SG",
            "stock_exit_series": "SC", "cash_account_code": "100.01",
            "bank_account_code": "102.01",
        }
        for key, (label, entry) in self.settings_entries.items():
            entry.delete(0, "end")
            entry.insert(0, defaults.get(key, ""))

    def save_system_settings(self):
        try:
            for key, (label, entry) in self.settings_entries.items():
                val = entry.get().strip()
                if self.use_db:
                    existing = self.db_manager.execute_query(
                        "SELECT SettingID FROM SystemSettings WHERE SettingKey=?", (key,)
                    )
                    if existing:
                        self.db_manager.execute_query(
                            "UPDATE SystemSettings SET SettingValue=?, UpdatedDate=datetime('now','localtime') WHERE SettingKey=?",
                            (val, key), fetch=False
                        )
                    else:
                        self.db_manager.execute_query(
                            "INSERT INTO SystemSettings (SettingKey, SettingValue, Description) VALUES (?, ?, ?)",
                            (key, val, label), fetch=False
                        )
                self.system_settings[key] = {"SettingValue": val, "Description": label}
            messagebox.showinfo("Basarili", "Sistem ayarlari kaydedildi!")
        except Exception as e:
            messagebox.showerror("Hata", str(e))
