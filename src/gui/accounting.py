"""
Accura Finance - Muhasebe Modulu
Hesap Plani, Yevmiye, Defteri Kebir ve Mizan islemleri
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
import sys
import os

PRIMARY = "#1565c0"
PRIMARY_DARK = "#0d47a1"
SUCCESS = "#2e7d32"
DANGER = "#c62828"
WARNING = "#f57f17"
TEXT_DARK = "#1a1a2e"
TEXT_MUTED = "#6c757d"
BORDER = "#e8eaed"


class AccountingFrame(ctk.CTkFrame):
    def __init__(self, parent, main_app):
        super().__init__(parent)
        self.main_app = main_app
        self.db_manager = main_app.db_manager
        self.use_db = False

        self.accounts = []
        self.journal_entries = []
        self.journal_details = {}
        self.next_voucher = 1

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.create_header()
        self.create_tabs()
        self.load_initial_data()

    # ------------------------------------------------------------------ HEADER
    def create_header(self):
        header = ctk.CTkFrame(self, height=60, corner_radius=10, fg_color="#ffffff")
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        header.grid_propagate(False)
        ctk.CTkLabel(
            header, text="MUHASEBE MODULU",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=PRIMARY_DARK
        ).pack(side="left", padx=20, pady=15)
        ctk.CTkLabel(
            header, text="Hesap Plani - Yevmiye - Defteri Kebir - Mizan",
            font=ctk.CTkFont(size=12), text_color=TEXT_MUTED
        ).pack(side="left", padx=5, pady=15)

    # ---------------------------------------------------------------- TABS
    def create_tabs(self):
        self.tabview = ctk.CTkTabview(self, corner_radius=10, fg_color="#ffffff")
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 10))
        self.tabview._segmented_button.configure(font=ctk.CTkFont(size=13, weight="bold"))

        self.tabview.add("Hesap Plani")
        self.tabview.add("Yevmiye")
        self.tabview.add("Defteri Kebir")
        self.tabview.add("Mizan")

        self.create_chart_of_accounts_tab()
        self.create_journal_tab()
        self.create_ledger_tab()
        self.create_trial_balance_tab()

    # --------------------------------------------------------- DATA LOADING
    def load_initial_data(self):
        if self.db_manager:
            self.check_and_create_tables()
        if not self.use_db:
            self.load_sample_accounts()

    def check_and_create_tables(self):
        try:
            self.db_manager.execute_query(
                "CREATE TABLE IF NOT EXISTS ChartOfAccounts ("
                "AccountID INTEGER PRIMARY KEY AUTOINCREMENT, "
                "AccountCode TEXT UNIQUE NOT NULL, "
                "AccountName TEXT NOT NULL, "
                "ParentAccountID INTEGER, "
                "AccountType TEXT NOT NULL, "
                "AccountGroup TEXT, "
                "IsDetailAccount INTEGER DEFAULT 0, "
                "IsActive INTEGER DEFAULT 1, "
                "FOREIGN KEY (ParentAccountID) REFERENCES ChartOfAccounts(AccountID))",
                fetch=False
            )
            self.db_manager.execute_query(
                "CREATE TABLE IF NOT EXISTS JournalEntries ("
                "JournalEntryID INTEGER PRIMARY KEY AUTOINCREMENT, "
                "VoucherNumber TEXT UNIQUE NOT NULL, "
                "VoucherDate TEXT NOT NULL, "
                "Description TEXT, "
                "TotalDebit REAL DEFAULT 0, "
                "TotalCredit REAL DEFAULT 0, "
                "IsBalanced INTEGER DEFAULT 0, "
                "CreatedDate TEXT DEFAULT (datetime('now','localtime')))",
                fetch=False
            )
            self.db_manager.execute_query(
                "CREATE TABLE IF NOT EXISTS JournalEntryDetails ("
                "JournalDetailID INTEGER PRIMARY KEY AUTOINCREMENT, "
                "JournalEntryID INTEGER NOT NULL, "
                "LineNumber INTEGER NOT NULL, "
                "AccountID INTEGER NOT NULL, "
                "Description TEXT, "
                "DebitAmount REAL DEFAULT 0, "
                "CreditAmount REAL DEFAULT 0, "
                "FOREIGN KEY (JournalEntryID) REFERENCES JournalEntries(JournalEntryID) ON DELETE CASCADE, "
                "FOREIGN KEY (AccountID) REFERENCES ChartOfAccounts(AccountID))",
                fetch=False
            )
            self.use_db = True
            self.load_accounts_from_db()
            self.load_journal_from_db()
        except Exception:
            self.use_db = False

    def load_accounts_from_db(self):
        try:
            result = self.db_manager.execute_query(
                "SELECT AccountID, AccountCode, AccountName, ParentAccountID, "
                "AccountType, AccountGroup, IsDetailAccount, IsActive "
                "FROM ChartOfAccounts ORDER BY AccountCode"
            )
            if result:
                self.accounts = result
            else:
                self.use_db = False
                self.load_sample_accounts()
            self.refresh_accounts_tree()
        except Exception:
            self.use_db = False
            self.load_sample_accounts()

    def load_journal_from_db(self):
        try:
            result = self.db_manager.execute_query(
                "SELECT * FROM JournalEntries ORDER BY JournalEntryID DESC"
            )
            if result:
                self.journal_entries = result
                for je in self.journal_entries:
                    dets = self.db_manager.execute_query(
                        "SELECT jd.*, ca.AccountCode, ca.AccountName "
                        "FROM JournalEntryDetails jd "
                        "LEFT JOIN ChartOfAccounts ca ON jd.AccountID = ca.AccountID "
                        "WHERE jd.JournalEntryID = ? ORDER BY jd.LineNumber",
                        (je["JournalEntryID"],)
                    )
                    self.journal_details[je["JournalEntryID"]] = dets or []
                if self.journal_entries:
                    max_v = max(int(e["VoucherNumber"].replace("M", "")) for e in self.journal_entries)
                    self.next_voucher = max_v + 1
            self.refresh_journal_tree()
        except Exception:
            self.use_db = False
            self.load_sample_accounts()

    def load_sample_accounts(self):
        self.accounts = [
            {"AccountID": 1, "AccountCode": "1", "AccountName": "DONEN VARLIKLAR", "ParentAccountID": None, "AccountType": "Aktif", "AccountGroup": "Ana Grup", "IsDetailAccount": 0, "IsActive": 1},
            {"AccountID": 2, "AccountCode": "10", "AccountName": "HAZIR DEGERLER", "ParentAccountID": 1, "AccountType": "Aktif", "AccountGroup": "Grup", "IsDetailAccount": 0, "IsActive": 1},
            {"AccountID": 3, "AccountCode": "100", "AccountName": "KASA", "ParentAccountID": 2, "AccountType": "Aktif", "AccountGroup": "Grup", "IsDetailAccount": 0, "IsActive": 1},
            {"AccountID": 4, "AccountCode": "100.01", "AccountName": "TL Kasasi", "ParentAccountID": 3, "AccountType": "Aktif", "AccountGroup": "Detay", "IsDetailAccount": 1, "IsActive": 1},
            {"AccountID": 5, "AccountCode": "102", "AccountName": "BANKALAR", "ParentAccountID": 2, "AccountType": "Aktif", "AccountGroup": "Grup", "IsDetailAccount": 0, "IsActive": 1},
            {"AccountID": 6, "AccountCode": "102.01", "AccountName": "Ziraat Bankasi TL", "ParentAccountID": 5, "AccountType": "Aktif", "AccountGroup": "Detay", "IsDetailAccount": 1, "IsActive": 1},
            {"AccountID": 7, "AccountCode": "120", "AccountName": "ALICILAR", "ParentAccountID": 1, "AccountType": "Aktif", "AccountGroup": "Grup", "IsDetailAccount": 0, "IsActive": 1},
            {"AccountID": 8, "AccountCode": "153", "AccountName": "TICARI MALLAR", "ParentAccountID": 1, "AccountType": "Aktif", "AccountGroup": "Grup", "IsDetailAccount": 0, "IsActive": 1},
            {"AccountID": 9, "AccountCode": "2", "AccountName": "DURAN VARLIKLAR", "ParentAccountID": None, "AccountType": "Aktif", "AccountGroup": "Ana Grup", "IsDetailAccount": 0, "IsActive": 1},
            {"AccountID": 10, "AccountCode": "220", "AccountName": "ARAZI VE ARSALAR", "ParentAccountID": 9, "AccountType": "Aktif", "AccountGroup": "Grup", "IsDetailAccount": 0, "IsActive": 1},
            {"AccountID": 11, "AccountCode": "225", "AccountName": "DEMIRBASLAR", "ParentAccountID": 9, "AccountType": "Aktif", "AccountGroup": "Grup", "IsDetailAccount": 0, "IsActive": 1},
            {"AccountID": 12, "AccountCode": "3", "AccountName": "KISA VADELI YABANCI KAYNAKLAR", "ParentAccountID": None, "AccountType": "Pasif", "AccountGroup": "Ana Grup", "IsDetailAccount": 0, "IsActive": 1},
            {"AccountID": 13, "AccountCode": "320", "AccountName": "SATICILAR", "ParentAccountID": 12, "AccountType": "Pasif", "AccountGroup": "Grup", "IsDetailAccount": 0, "IsActive": 1},
            {"AccountID": 14, "AccountCode": "320.01", "AccountName": "Tedarikci Borclari", "ParentAccountID": 13, "AccountType": "Pasif", "AccountGroup": "Detay", "IsDetailAccount": 1, "IsActive": 1},
            {"AccountID": 15, "AccountCode": "6", "AccountName": "GELIRLER", "ParentAccountID": None, "AccountType": "Gelir", "AccountGroup": "Ana Grup", "IsDetailAccount": 0, "IsActive": 1},
            {"AccountID": 16, "AccountCode": "600", "AccountName": "YURTICI SATISLAR", "ParentAccountID": 15, "AccountType": "Gelir", "AccountGroup": "Grup", "IsDetailAccount": 0, "IsActive": 1},
            {"AccountID": 17, "AccountCode": "600.01", "AccountName": "Yurtici Satislar", "ParentAccountID": 16, "AccountType": "Gelir", "AccountGroup": "Detay", "IsDetailAccount": 1, "IsActive": 1},
            {"AccountID": 18, "AccountCode": "7", "AccountName": "GIDERLER", "ParentAccountID": None, "AccountType": "Gider", "AccountGroup": "Ana Grup", "IsDetailAccount": 0, "IsActive": 1},
            {"AccountID": 19, "AccountCode": "760", "AccountName": "PERSONEL UCRET VE GIDERLERI", "ParentAccountID": 18, "AccountType": "Gider", "AccountGroup": "Grup", "IsDetailAccount": 0, "IsActive": 1},
            {"AccountID": 20, "AccountCode": "760.01", "AccountName": "Personel Maaslari", "ParentAccountID": 19, "AccountType": "Gider", "AccountGroup": "Detay", "IsDetailAccount": 1, "IsActive": 1},
            {"AccountID": 21, "AccountCode": "770", "AccountName": "GENEL YONETIM GIDERLERI", "ParentAccountID": 18, "AccountType": "Gider", "AccountGroup": "Grup", "IsDetailAccount": 0, "IsActive": 1},
            {"AccountID": 22, "AccountCode": "770.01", "AccountName": "Kira Giderleri", "ParentAccountID": 21, "AccountType": "Gider", "AccountGroup": "Detay", "IsDetailAccount": 1, "IsActive": 1},
        ]
        if not self.journal_entries:
            self.load_sample_journals()
        self.refresh_accounts_tree()

    def load_sample_journals(self):
        self.journal_entries = []
        self.journal_details = {}
        self.next_voucher = 1

    # =====================================================================
    # TAB 1: HESAP PLANI
    # =====================================================================
    def create_chart_of_accounts_tab(self):
        tab = self.tabview.tab("Hesap Plani")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        toolbar = ctk.CTkFrame(tab, fg_color="transparent", height=44)
        toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))

        ctk.CTkButton(toolbar, text="Hesap Ekle", command=self.add_account_dialog,
                       fg_color=SUCCESS, hover_color="#1b5e20", height=34,
                       corner_radius=8, font=ctk.CTkFont(size=12, weight="bold")
                       ).pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text="Duzenle", command=self.edit_account_dialog,
                       fg_color=PRIMARY, hover_color=PRIMARY_DARK, height=34,
                       corner_radius=8, font=ctk.CTkFont(size=12, weight="bold")
                       ).pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text="Sil", command=self.delete_account,
                       fg_color=DANGER, hover_color="#b71c1c", height=34,
                       corner_radius=8, font=ctk.CTkFont(size=12, weight="bold")
                       ).pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text="Yenile", command=self.refresh_accounts_tree,
                       fg_color="#6c757d", hover_color="#5a6268", height=34,
                       corner_radius=8, font=ctk.CTkFont(size=12, weight="bold")
                       ).pack(side="right", padx=4)

        content = ctk.CTkFrame(tab, corner_radius=10, fg_color="#ffffff",
                                border_width=1, border_color=BORDER)
        content.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 10))
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)

        columns = ("Hesap Kodu", "Hesap Adi", "Tur", "Durum")
        self.accounts_tree = ttk.Treeview(content, columns=columns, show="headings", height=20, selectmode="browse")
        widths = [120, 350, 120, 80]
        for col, w in zip(columns, widths):
            self.accounts_tree.heading(col, text=col)
            self.accounts_tree.column(col, width=w, anchor="w" if col == "Hesap Adi" else "center")

        scroll = ttk.Scrollbar(content, orient="vertical", command=self.accounts_tree.yview)
        self.accounts_tree.configure(yscrollcommand=scroll.set)
        self.accounts_tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scroll.grid(row=0, column=1, sticky="ns", pady=5)

        self.accounts_tree.bind("<<TreeviewSelect>>", self.on_account_select)

    def on_account_select(self, event=None):
        pass

    def refresh_accounts_tree(self):
        for item in self.accounts_tree.get_children():
            self.accounts_tree.delete(item)
        for a in self.accounts:
            durum = "Aktif" if a.get("IsActive", 1) else "Pasif"
            self.accounts_tree.insert("", "end", iid=str(a["AccountID"]), values=(
                a.get("AccountCode", ""),
                a.get("AccountName", ""),
                a.get("AccountType", ""),
                durum
            ))

    def add_account_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Hesap Ekle")
        dialog.geometry("480x420")
        dialog.transient(self)
        dialog.grab_set()

        frame = ctk.CTkFrame(dialog, corner_radius=10, fg_color="#ffffff")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text="YENI HESAP",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=PRIMARY_DARK).pack(pady=(0, 20))

        fields = {}
        for label in ["Hesap Kodu", "Hesap Adi"]:
            ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=12, weight="bold"),
                         anchor="w").pack(fill="x", padx=20)
            e = ctk.CTkEntry(frame, height=35, font=ctk.CTkFont(size=14))
            e.pack(fill="x", padx=20, pady=(0, 10))
            fields[label] = e

        ctk.CTkLabel(frame, text="Tur", font=ctk.CTkFont(size=12, weight="bold"),
                     anchor="w").pack(fill="x", padx=20)
        type_combo = ctk.CTkComboBox(frame, values=["Aktif", "Pasif", "Gelir", "Gider"],
                                      height=35, font=ctk.CTkFont(size=14),
                                      state="readonly")
        type_combo.set("Aktif")
        type_combo.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(frame, text="Ust Hesap", font=ctk.CTkFont(size=12, weight="bold"),
                     anchor="w").pack(fill="x", padx=20)
        parent_combo = ctk.CTkComboBox(frame,
                                        values=[f"{a['AccountCode']} - {a['AccountName']}" for a in self.accounts],
                                        height=35, font=ctk.CTkFont(size=14),
                                        state="readonly")
        parent_combo.set("")
        parent_combo.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkLabel(frame, text="Detay Hesap", font=ctk.CTkFont(size=12, weight="bold"),
                     anchor="w").pack(fill="x", padx=20)
        detail_var = ctk.StringVar(value="Hayir")
        ctk.CTkSwitch(frame, text="", variable=detail_var, onvalue="Evet", offvalue="Hayir",
                       font=ctk.CTkFont(size=12)).pack(anchor="w", padx=20, pady=(0, 15))

        def save():
            code = fields["Hesap Kodu"].get().strip()
            name = fields["Hesap Adi"].get().strip()
            if not code or not name:
                messagebox.showwarning("Uyari", "Hesap kodu ve adi zorunludur!")
                return
            acc_type = type_combo.get()
            parent_id = None
            parent_text = parent_combo.get()
            if parent_text:
                for a in self.accounts:
                    if f"{a['AccountCode']} - {a['AccountName']}" == parent_text:
                        parent_id = a["AccountID"]
                        break
            is_detail = 1 if detail_var.get() == "Evet" else 0
            try:
                if self.use_db:
                    self.db_manager.execute_query(
                        "INSERT INTO ChartOfAccounts (AccountCode, AccountName, ParentAccountID, AccountType, IsDetailAccount) "
                        "VALUES (?, ?, ?, ?, ?)",
                        (code, name, parent_id, acc_type, is_detail), fetch=False
                    )
                    self.load_accounts_from_db()
                else:
                    new_id = max(a["AccountID"] for a in self.accounts) + 1
                    self.accounts.append({
                        "AccountID": new_id, "AccountCode": code, "AccountName": name,
                        "ParentAccountID": parent_id, "AccountType": acc_type,
                        "AccountGroup": "Detay" if is_detail else "Grup",
                        "IsDetailAccount": is_detail, "IsActive": 1
                    })
                    self.refresh_accounts_tree()
                messagebox.showinfo("Basarili", "Hesap eklendi!")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Hata", str(e))

        ctk.CTkButton(frame, text="Kaydet", command=save,
                       fg_color=SUCCESS, height=40,
                       font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)

    def edit_account_dialog(self):
        sel = self.accounts_tree.selection()
        if not sel:
            messagebox.showwarning("Uyari", "Lutfen bir hesap secin!")
            return
        aid = int(sel[0])
        acc = None
        for a in self.accounts:
            if a["AccountID"] == aid:
                acc = a
                break
        if not acc:
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Hesap Duzenle")
        dialog.geometry("480x420")
        dialog.transient(self)
        dialog.grab_set()

        frame = ctk.CTkFrame(dialog, corner_radius=10, fg_color="#ffffff")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text="HESAP DUZENLE",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=PRIMARY_DARK).pack(pady=(0, 20))

        ctk.CTkLabel(frame, text="Hesap Kodu", font=ctk.CTkFont(size=12, weight="bold"),
                     anchor="w").pack(fill="x", padx=20)
        code_entry = ctk.CTkEntry(frame, height=35, font=ctk.CTkFont(size=14))
        code_entry.insert(0, acc.get("AccountCode", ""))
        code_entry.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(frame, text="Hesap Adi", font=ctk.CTkFont(size=12, weight="bold"),
                     anchor="w").pack(fill="x", padx=20)
        name_entry = ctk.CTkEntry(frame, height=35, font=ctk.CTkFont(size=14))
        name_entry.insert(0, acc.get("AccountName", ""))
        name_entry.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(frame, text="Tur", font=ctk.CTkFont(size=12, weight="bold"),
                     anchor="w").pack(fill="x", padx=20)
        type_combo = ctk.CTkComboBox(frame, values=["Aktif", "Pasif", "Gelir", "Gider"],
                                      height=35, font=ctk.CTkFont(size=14))
        type_combo.set(acc.get("AccountType", "Aktif"))
        type_combo.pack(fill="x", padx=20, pady=(0, 10))

        def save():
            code = code_entry.get().strip()
            name = name_entry.get().strip()
            if not code or not name:
                messagebox.showwarning("Uyari", "Hesap kodu ve adi zorunludur!")
                return
            acc_type = type_combo.get()
            try:
                if self.use_db:
                    self.db_manager.execute_query(
                        "UPDATE ChartOfAccounts SET AccountCode=?, AccountName=?, AccountType=? WHERE AccountID=?",
                        (code, name, acc_type, aid), fetch=False
                    )
                    self.load_accounts_from_db()
                else:
                    for a in self.accounts:
                        if a["AccountID"] == aid:
                            a["AccountCode"] = code
                            a["AccountName"] = name
                            a["AccountType"] = acc_type
                            break
                    self.refresh_accounts_tree()
                messagebox.showinfo("Basarili", "Hesap guncellendi!")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Hata", str(e))

        ctk.CTkButton(frame, text="Kaydet", command=save,
                       fg_color=PRIMARY, height=40,
                       font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)

    def delete_account(self):
        sel = self.accounts_tree.selection()
        if not sel:
            messagebox.showwarning("Uyari", "Lutfen bir hesap secin!")
            return
        aid = int(sel[0])
        acc = next((a for a in self.accounts if a["AccountID"] == aid), None)
        if not acc:
            return
        if not messagebox.askyesno("Onay", f"{acc['AccountCode']} - {acc['AccountName']}\nhesabini silmek istediginize emin misiniz?"):
            return
        try:
            if self.use_db:
                self.db_manager.execute_query("DELETE FROM ChartOfAccounts WHERE AccountID=?", (aid,), fetch=False)
                self.load_accounts_from_db()
            else:
                self.accounts = [a for a in self.accounts if a["AccountID"] != aid]
                self.refresh_accounts_tree()
            messagebox.showinfo("Basarili", "Hesap silindi!")
        except Exception as e:
            messagebox.showerror("Hata", str(e))

    # =====================================================================
    # TAB 2: YEVMiYE
    # =====================================================================
    def create_journal_tab(self):
        tab = self.tabview.tab("Yevmiye")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)

        # Top form
        top_frame = ctk.CTkFrame(tab, corner_radius=10, fg_color="#ffffff",
                                  border_width=1, border_color=BORDER)
        top_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        top_frame.grid_columnconfigure((1, 3), weight=1)

        ctk.CTkLabel(top_frame, text="Yeni Yevmiye Kaydi",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=TEXT_DARK).grid(row=0, column=0, columnspan=4,
                                                sticky="w", padx=16, pady=(12, 8))

        ctk.CTkLabel(top_frame, text="Tarih:", font=ctk.CTkFont(size=12),
                     text_color=TEXT_DARK).grid(row=1, column=0, sticky="w", padx=16, pady=4)
        self.journal_date_entry = ctk.CTkEntry(top_frame, height=32, width=130,
                                                font=ctk.CTkFont(size=13))
        self.journal_date_entry.insert(0, date.today().strftime("%d.%m.%Y"))
        self.journal_date_entry.grid(row=1, column=1, sticky="w", padx=5, pady=4)

        self.journal_date_btn = ctk.CTkButton(top_frame, text="...", width=30, height=32,
                                               command=self.pick_journal_date,
                                               font=ctk.CTkFont(size=12))
        self.journal_date_btn.grid(row=1, column=2, sticky="w", padx=2, pady=4)

        ctk.CTkLabel(top_frame, text="Aciklama:", font=ctk.CTkFont(size=12),
                     text_color=TEXT_DARK).grid(row=1, column=3, sticky="w", padx=(30, 0), pady=4)
        self.journal_desc_entry = ctk.CTkEntry(top_frame, height=32,
                                                font=ctk.CTkFont(size=13))
        self.journal_desc_entry.grid(row=1, column=4, columnspan=2, sticky="ew", padx=5, pady=4, ipadx=10)

        ctk.CTkButton(top_frame, text="Yeni Kayit", command=self.add_journal_entry_dialog,
                       fg_color=SUCCESS, height=34, corner_radius=8,
                       font=ctk.CTkFont(size=12, weight="bold")
                       ).grid(row=1, column=6, padx=(10, 16), pady=4, sticky="e")

        # Middle: entries list
        mid_frame = ctk.CTkFrame(tab, corner_radius=10, fg_color="#ffffff",
                                  border_width=1, border_color=BORDER)
        mid_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        mid_frame.grid_columnconfigure(0, weight=1)
        mid_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(mid_frame, text="Yevmiye Kayitlari",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=TEXT_DARK).grid(row=0, column=0, sticky="w", padx=16, pady=(10, 4))

        columns = ("Fis No", "Tarih", "Aciklama", "Borc", "Alacak", " Durum")
        self.journal_tree = ttk.Treeview(mid_frame, columns=columns, show="headings", height=8, selectmode="browse")
        widths = [90, 100, 250, 130, 130, 80]
        for col, w in zip(columns, widths):
            self.journal_tree.heading(col, text=col)
            self.journal_tree.column(col, width=w, anchor="center")

        scroll_j = ttk.Scrollbar(mid_frame, orient="vertical", command=self.journal_tree.yview)
        self.journal_tree.configure(yscrollcommand=scroll_j.set)
        self.journal_tree.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        scroll_j.grid(row=1, column=1, sticky="ns", pady=5)
        self.journal_tree.bind("<<TreeviewSelect>>", self.on_journal_select)

        # Bottom: selected details
        bot_frame = ctk.CTkFrame(tab, corner_radius=10, fg_color="#ffffff",
                                  border_width=1, border_color=BORDER)
        bot_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(5, 10))
        bot_frame.grid_columnconfigure(0, weight=1)
        bot_frame.grid_rowconfigure(1, weight=1)

        top_row = ctk.CTkFrame(bot_frame, fg_color="transparent")
        top_row.grid(row=0, column=0, sticky="ew", padx=16, pady=(10, 4))
        top_row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(top_row, text="Secili Kayit Detaylari",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=TEXT_DARK).pack(side="left")
        ctk.CTkButton(top_row, text="Sil", command=self.delete_journal_entry,
                       fg_color=DANGER, height=30, width=60, corner_radius=6,
                       font=ctk.CTkFont(size=11, weight="bold")).pack(side="right", padx=5)

        columns_detail = ("Hesap Kodu", "Hesap Adi", "Aciklama", "Borc", "Alacak")
        self.journal_detail_tree = ttk.Treeview(bot_frame, columns=columns_detail,
                                                  show="headings", height=6, selectmode="browse")
        widths_d = [100, 200, 250, 120, 120]
        for col, w in zip(columns_detail, widths_d):
            self.journal_detail_tree.heading(col, text=col)
            self.journal_detail_tree.column(col, width=w, anchor="center")

        scroll_jd = ttk.Scrollbar(bot_frame, orient="vertical", command=self.journal_detail_tree.yview)
        self.journal_detail_tree.configure(yscrollcommand=scroll_jd.set)
        self.journal_detail_tree.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        scroll_jd.grid(row=1, column=1, sticky="ns", pady=5)

    def pick_journal_date(self):
        dp = DatePickerDialog(self, self.journal_date_entry)
        self.wait_window(dp)

    def refresh_journal_tree(self):
        for item in self.journal_tree.get_children():
            self.journal_tree.delete(item)
        for je in self.journal_entries:
            fmt_date = je.get("VoucherDate", "")
            if fmt_date and len(fmt_date) >= 10:
                fmt_date = fmt_date[:10]
            total_d = je.get("TotalDebit", 0) or 0
            total_c = je.get("TotalCredit", 0) or 0
            balanced = "Evet" if je.get("IsBalanced", 0) else "Hayir"
            self.journal_tree.insert("", "end", iid=str(je.get("JournalEntryID", 0)), values=(
                je.get("VoucherNumber", ""),
                fmt_date,
                je.get("Description", ""),
                f"{total_d:,.2f}",
                f"{total_c:,.2f}",
                balanced
            ))

    def on_journal_select(self, event=None):
        for item in self.journal_detail_tree.get_children():
            self.journal_detail_tree.delete(item)
        sel = self.journal_tree.selection()
        if not sel:
            return
        jid = int(sel[0])
        je = next((j for j in self.journal_entries if j.get("JournalEntryID") == jid), None)
        if not je:
            return
        details = self.journal_details.get(jid, [])
        for d in details:
            code = d.get("AccountCode", "")
            name = d.get("AccountName", "")
            desc = d.get("Description", "")
            debit = d.get("DebitAmount", 0) or 0
            credit = d.get("CreditAmount", 0) or 0
            self.journal_detail_tree.insert("", "end", values=(
                code, name, desc, f"{debit:,.2f}", f"{credit:,.2f}"
            ))

    def add_journal_entry_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Yeni Yevmiye Kaydi")
        dialog.geometry("700x550")
        dialog.transient(self)
        dialog.grab_set()

        frame = ctk.CTkFrame(dialog, corner_radius=10, fg_color="#ffffff")
        frame.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(frame, text="YENI YEVMiYE KAYDI",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=PRIMARY_DARK).pack(pady=(0, 12))

        form = ctk.CTkFrame(frame, fg_color="transparent")
        form.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(form, text="Tarih:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, sticky="w", padx=5, pady=4)
        date_entry = ctk.CTkEntry(form, height=32, width=120, font=ctk.CTkFont(size=13))
        date_entry.insert(0, self.journal_date_entry.get() or date.today().strftime("%d.%m.%Y"))
        date_entry.grid(row=0, column=1, sticky="w", padx=5, pady=4)

        ctk.CTkLabel(form, text="Aciklama:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=2, sticky="w", padx=(20, 5), pady=4)
        desc_entry = ctk.CTkEntry(form, height=32, font=ctk.CTkFont(size=13))
        desc_entry.insert(0, self.journal_desc_entry.get())
        desc_entry.grid(row=0, column=3, sticky="ew", padx=5, pady=4)
        form.grid_columnconfigure(3, weight=1)

        # Details table
        ctk.CTkLabel(frame, text="Hesap Hareketleri",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=TEXT_DARK).pack(anchor="w", padx=15, pady=(10, 4))

        columns = ("Hesap Kodu", "Aciklama", "Borc", "Alacak")
        line_tree = ttk.Treeview(frame, columns=columns, show="headings", height=10, selectmode="browse")
        for col, w in zip(columns, [130, 280, 120, 120]):
            line_tree.heading(col, text=col)
            line_tree.column(col, width=w, anchor="center")
        line_tree.pack(fill="both", expand=True, padx=10, pady=5)

        line_data = []

        add_line_frame = ctk.CTkFrame(frame, fg_color="transparent")
        add_line_frame.pack(fill="x", padx=10, pady=5)
        add_line_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        account_options = [f"{a['AccountCode']} - {a['AccountName']}" for a in self.accounts]
        account_combo = ctk.CTkComboBox(add_line_frame, values=account_options,
                                         height=32, font=ctk.CTkFont(size=12))
        account_combo.grid(row=0, column=0, padx=2, pady=4, sticky="ew")

        line_desc = ctk.CTkEntry(add_line_frame, height=32, font=ctk.CTkFont(size=12),
                                  placeholder_text="Aciklama")
        line_desc.grid(row=0, column=1, padx=2, pady=4, sticky="ew")

        line_debit = ctk.CTkEntry(add_line_frame, height=32, width=90, font=ctk.CTkFont(size=12),
                                   placeholder_text="Borc")
        line_debit.grid(row=0, column=2, padx=2, pady=4)

        line_credit = ctk.CTkEntry(add_line_frame, height=32, width=90, font=ctk.CTkFont(size=12),
                                    placeholder_text="Alacak")
        line_credit.grid(row=0, column=3, padx=2, pady=4)

        def add_line():
            acc_text = account_combo.get()
            desc_text = line_desc.get().strip()
            debit_text = line_debit.get().strip()
            credit_text = line_credit.get().strip()
            if not acc_text:
                messagebox.showwarning("Uyari", "Hesap kodu secin!")
                return
            if not debit_text and not credit_text:
                messagebox.showwarning("Uyari", "Borc veya alacak girin!")
                return
            try:
                debit_val = float(debit_text.replace(",", ".")) if debit_text else 0
            except ValueError:
                debit_val = 0
            try:
                credit_val = float(credit_text.replace(",", ".")) if credit_text else 0
            except ValueError:
                credit_val = 0
            if debit_val == 0 and credit_val == 0:
                messagebox.showwarning("Uyari", "Gecerli bir tutar girin!")
                return
            acc_id = None
            for a in self.accounts:
                if f"{a['AccountCode']} - {a['AccountName']}" == acc_text:
                    acc_id = a["AccountID"]
                    break
            line_data.append({
                "AccountID": acc_id,
                "AccountCode": acc_text.split(" - ")[0],
                "AccountName": acc_text.split(" - ")[1] if " - " in acc_text else "",
                "Description": desc_text,
                "DebitAmount": debit_val,
                "CreditAmount": credit_val
            })
            line_tree.insert("", "end", values=(acc_text.split(" - ")[0], desc_text,
                                                  f"{debit_val:,.2f}" if debit_val else "",
                                                  f"{credit_val:,.2f}" if credit_val else ""))
            line_desc.delete(0, "end")
            line_debit.delete(0, "end")
            line_credit.delete(0, "end")

        ctk.CTkButton(add_line_frame, text="Ekle", command=add_line,
                       fg_color=PRIMARY, height=32, width=70, corner_radius=6,
                       font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=4, padx=2, pady=4)

        def remove_line():
            sel = line_tree.selection()
            if not sel:
                return
            idx = line_tree.index(sel[0])
            line_tree.delete(sel[0])
            if idx < len(line_data):
                del line_data[idx]

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(btn_frame, text="Secili Satiri Sil", command=remove_line,
                       fg_color=DANGER, height=30, corner_radius=6,
                       font=ctk.CTkFont(size=11)).pack(side="left", padx=5)

        def save_journal():
            if not line_data:
                messagebox.showwarning("Uyari", "En az bir hesap hareketi ekleyin!")
                return
            total_debit = sum(d["DebitAmount"] for d in line_data)
            total_credit = sum(d["CreditAmount"] for d in line_data)
            if abs(total_debit - total_credit) > 0.01:
                if not messagebox.askyesno("Uyari", f"Toplam borc ({total_debit:,.2f}) ile toplam alacak ({total_credit:,.2f}) esit degil. Devam etmek istiyor musunuz?"):
                    return
            is_balanced = 1 if abs(total_debit - total_credit) < 0.01 else 0
            date_str = date_entry.get().strip()
            desc_text = desc_entry.get().strip()
            try:
                voucher_num = f"M{self.next_voucher:04d}"
                if self.use_db:
                    self.db_manager.execute_query(
                        "INSERT INTO JournalEntries (VoucherNumber, VoucherDate, Description, TotalDebit, TotalCredit, IsBalanced) "
                        "VALUES (?, ?, ?, ?, ?, ?)",
                        (voucher_num, date_str, desc_text, total_debit, total_credit, is_balanced),
                        fetch=False
                    )
                    result = self.db_manager.execute_query(
                        "SELECT JournalEntryID FROM JournalEntries WHERE VoucherNumber = ?", (voucher_num,)
                    )
                    jid = result[0]["JournalEntryID"] if result else 0
                    for i, d in enumerate(line_data):
                        self.db_manager.execute_query(
                            "INSERT INTO JournalEntryDetails (JournalEntryID, LineNumber, AccountID, Description, DebitAmount, CreditAmount) "
                            "VALUES (?, ?, ?, ?, ?, ?)",
                            (jid, i + 1, d["AccountID"], d["Description"], d["DebitAmount"], d["CreditAmount"]),
                            fetch=False
                        )
                    self.load_journal_from_db()
                else:
                    jid = max([j.get("JournalEntryID", 0) for j in self.journal_entries], default=0) + 1
                    new_entry = {
                        "JournalEntryID": jid,
                        "VoucherNumber": voucher_num,
                        "VoucherDate": date_str,
                        "Description": desc_text,
                        "TotalDebit": total_debit,
                        "TotalCredit": total_credit,
                        "IsBalanced": is_balanced
                    }
                    self.journal_entries.insert(0, new_entry)
                    details_with_names = []
                    for i, d in enumerate(line_data):
                        details_with_names.append({
                            "JournalDetailID": i + 1,
                            "JournalEntryID": jid,
                            "LineNumber": i + 1,
                            "AccountID": d["AccountID"],
                            "AccountCode": d["AccountCode"],
                            "AccountName": d["AccountName"],
                            "Description": d["Description"],
                            "DebitAmount": d["DebitAmount"],
                            "CreditAmount": d["CreditAmount"]
                        })
                    self.journal_details[jid] = details_with_names
                    self.next_voucher += 1
                    self.refresh_journal_tree()
                messagebox.showinfo("Basarili", f"Yevmiye kaydi olusturuldu! Fis No: {voucher_num}")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Hata", str(e))

        ctk.CTkButton(frame, text="Kaydet ve Kapat", command=save_journal,
                       fg_color=SUCCESS, height=40, corner_radius=8,
                       font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)

    def delete_journal_entry(self):
        sel = self.journal_tree.selection()
        if not sel:
            messagebox.showwarning("Uyari", "Lutfen bir kayit secin!")
            return
        jid = int(sel[0])
        je = next((j for j in self.journal_entries if j.get("JournalEntryID") == jid), None)
        if not je:
            return
        if not messagebox.askyesno("Onay", f"Fis {je['VoucherNumber']} silinsin mi?"):
            return
        try:
            if self.use_db:
                self.db_manager.execute_query("DELETE FROM JournalEntries WHERE JournalEntryID=?", (jid,), fetch=False)
                self.load_journal_from_db()
            else:
                self.journal_entries = [j for j in self.journal_entries if j.get("JournalEntryID") != jid]
                self.journal_details.pop(jid, None)
                self.refresh_journal_tree()
            self.journal_detail_tree.delete(*self.journal_detail_tree.get_children())
            messagebox.showinfo("Basarili", "Kayit silindi!")
        except Exception as e:
            messagebox.showerror("Hata", str(e))

    # =====================================================================
    # TAB 3: DEFTERi KEBiR
    # =====================================================================
    def create_ledger_tab(self):
        tab = self.tabview.tab("Defteri Kebir")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)

        top = ctk.CTkFrame(tab, corner_radius=10, fg_color="#ffffff",
                            border_width=1, border_color=BORDER)
        top.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        top.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(top, text="DEFTERI KEBIR",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=PRIMARY_DARK).grid(row=0, column=0, columnspan=4,
                                                   sticky="w", padx=16, pady=(12, 4))
        ctk.CTkLabel(top, text="Hesap:", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=TEXT_DARK).grid(row=1, column=0, sticky="w", padx=16, pady=10)
        self.ledger_account_var = ctk.StringVar()
        self.ledger_combo = ctk.CTkComboBox(top, variable=self.ledger_account_var,
                                             values=[], height=34, width=350,
                                             font=ctk.CTkFont(size=13), state="readonly")
        self.ledger_combo.grid(row=1, column=1, sticky="w", padx=5, pady=10)

        ctk.CTkButton(top, text="Sorgula", command=self.query_ledger,
                       fg_color=PRIMARY, height=34, corner_radius=8,
                       font=ctk.CTkFont(size=12, weight="bold")
                       ).grid(row=1, column=2, padx=10, pady=10)

        content = ctk.CTkFrame(tab, corner_radius=10, fg_color="#ffffff",
                                border_width=1, border_color=BORDER)
        content.grid(row=2, column=0, sticky="nsew", padx=10, pady=(5, 10))
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)

        columns = ("Tarih", "Fis No", "Aciklama", "Borc", "Alacak", "Bakiye")
        self.ledger_tree = ttk.Treeview(content, columns=columns, show="headings", height=20, selectmode="browse")
        widths_l = [110, 100, 300, 130, 130, 130]
        for col, w in zip(columns, widths_l):
            self.ledger_tree.heading(col, text=col)
            self.ledger_tree.column(col, width=w, anchor="center")

        scroll_l = ttk.Scrollbar(content, orient="vertical", command=self.ledger_tree.yview)
        self.ledger_tree.configure(yscrollcommand=scroll_l.set)
        self.ledger_tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scroll_l.grid(row=0, column=1, sticky="ns", pady=5)

        self.update_ledger_combo()

    def update_ledger_combo(self):
        options = [f"{a['AccountCode']} - {a['AccountName']}" for a in self.accounts]
        self.ledger_combo.configure(values=options)
        if options:
            self.ledger_combo.set(options[0])

    def query_ledger(self):
        for item in self.ledger_tree.get_children():
            self.ledger_tree.delete(item)
        acc_text = self.ledger_account_var.get()
        if not acc_text:
            messagebox.showwarning("Uyari", "Lutfen bir hesap secin!")
            return
        acc_code = acc_text.split(" - ")[0]
        acc = next((a for a in self.accounts if a["AccountCode"] == acc_code), None)
        if not acc:
            return
        account_id = acc["AccountID"]

        all_details = []
        if self.use_db:
            try:
                result = self.db_manager.execute_query(
                    "SELECT jd.*, je.VoucherNumber, je.VoucherDate, je.Description as JeDesc, "
                    "ca.AccountCode, ca.AccountName "
                    "FROM JournalEntryDetails jd "
                    "JOIN JournalEntries je ON jd.JournalEntryID = je.JournalEntryID "
                    "LEFT JOIN ChartOfAccounts ca ON jd.AccountID = ca.AccountID "
                    "WHERE jd.AccountID = ? "
                    "ORDER BY je.VoucherDate, je.JournalEntryID, jd.LineNumber",
                    (account_id,)
                )
                if result:
                    all_details = result
            except Exception:
                pass
        else:
            for jid, details in self.journal_details.items():
                je = next((j for j in self.journal_entries if j.get("JournalEntryID") == jid), None)
                if not je:
                    continue
                for d in details:
                    aid = d.get("AccountID")
                    if aid and aid == account_id:
                        all_details.append({
                            **d,
                            "VoucherNumber": je["VoucherNumber"],
                            "VoucherDate": je["VoucherDate"],
                            "JeDesc": je["Description"]
                        })

        if not all_details:
            messagebox.showinfo("Bilgi", "Bu hesaba ait hareket bulunamadi.")
            return

        balance = 0.0
        is_pasif_gelir = acc["AccountType"] in ("Pasif", "Gelir")
        for d in all_details:
            debit = d.get("DebitAmount", 0) or 0
            credit = d.get("CreditAmount", 0) or 0
            if is_pasif_gelir:
                balance += credit - debit
            else:
                balance += debit - credit
            fmt_date = str(d.get("VoucherDate", ""))[:10]
            desc = d.get("Description") or d.get("JeDesc") or ""
            self.ledger_tree.insert("", "end", values=(
                fmt_date,
                d.get("VoucherNumber", ""),
                desc,
                f"{debit:,.2f}" if debit else "-",
                f"{credit:,.2f}" if credit else "-",
                f"{balance:,.2f}"
            ))

    # =====================================================================
    # TAB 4: MiZAN
    # =====================================================================
    def create_trial_balance_tab(self):
        tab = self.tabview.tab("Mizan")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)

        top = ctk.CTkFrame(tab, corner_radius=10, fg_color="#ffffff",
                            border_width=1, border_color=BORDER)
        top.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        top.grid_columnconfigure((1, 3), weight=1)

        ctk.CTkLabel(top, text="MIZAN",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=PRIMARY_DARK).grid(row=0, column=0, columnspan=6,
                                                   sticky="w", padx=16, pady=(12, 4))

        ctk.CTkLabel(top, text="Baslangic:", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=TEXT_DARK).grid(row=1, column=0, sticky="w", padx=16, pady=8)
        self.mizan_start_entry = ctk.CTkEntry(top, height=32, width=120,
                                               font=ctk.CTkFont(size=13))
        self.mizan_start_entry.insert(0, f"01.01.{date.today().year}")
        self.mizan_start_entry.grid(row=1, column=1, sticky="w", padx=5, pady=8)

        ctk.CTkLabel(top, text="Bitis:", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=TEXT_DARK).grid(row=1, column=2, sticky="w", padx=(20, 0), pady=8)
        self.mizan_end_entry = ctk.CTkEntry(top, height=32, width=120,
                                             font=ctk.CTkFont(size=13))
        self.mizan_end_entry.insert(0, date.today().strftime("%d.%m.%Y"))
        self.mizan_end_entry.grid(row=1, column=3, sticky="w", padx=5, pady=8)

        ctk.CTkButton(top, text="Mizan Hazirla", command=self.prepare_trial_balance,
                       fg_color=SUCCESS, height=34, corner_radius=8,
                       font=ctk.CTkFont(size=12, weight="bold")
                       ).grid(row=1, column=4, padx=(20, 10), pady=8)

        content = ctk.CTkFrame(tab, corner_radius=10, fg_color="#ffffff",
                                border_width=1, border_color=BORDER)
        content.grid(row=2, column=0, sticky="nsew", padx=10, pady=(5, 10))
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)

        columns = ("Hesap Kodu", "Hesap Adi", "Borc", "Alacak", "Borc Bakiyesi", "Alacak Bakiyesi")
        self.mizan_tree = ttk.Treeview(content, columns=columns, show="headings", height=20, selectmode="browse")
        widths_m = [110, 250, 120, 120, 130, 130]
        for col, w in zip(columns, widths_m):
            self.mizan_tree.heading(col, text=col)
            self.mizan_tree.column(col, width=w, anchor="center")

        scroll_m = ttk.Scrollbar(content, orient="vertical", command=self.mizan_tree.yview)
        self.mizan_tree.configure(yscrollcommand=scroll_m.set)
        self.mizan_tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scroll_m.grid(row=0, column=1, sticky="ns", pady=5)

        self.mizan_summary_label = ctk.CTkLabel(
            content, text="", font=ctk.CTkFont(size=12, weight="bold"),
            text_color=TEXT_DARK
        )
        self.mizan_summary_label.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 8))

    def prepare_trial_balance(self):
        for item in self.mizan_tree.get_children():
            self.mizan_tree.delete(item)

        start_str = self.mizan_start_entry.get().strip()
        end_str = self.mizan_end_entry.get().strip()

        account_totals = {}
        for a in self.accounts:
            aid = a["AccountID"]
            account_totals[aid] = {"code": a["AccountCode"], "name": a["AccountName"],
                                    "total_debit": 0.0, "total_credit": 0.0,
                                    "balance_debit": 0.0, "balance_credit": 0.0}

        all_details = []
        if self.use_db:
            try:
                date_filter = ""
                params = []
                if start_str and end_str:
                    date_filter = " AND je.VoucherDate BETWEEN ? AND ?"
                    params = [start_str, end_str]
                result = self.db_manager.execute_query(
                    "SELECT jd.*, je.VoucherDate, ca.AccountID, ca.AccountCode, ca.AccountName, ca.AccountType "
                    "FROM JournalEntryDetails jd "
                    "JOIN JournalEntries je ON jd.JournalEntryID = je.JournalEntryID "
                    "JOIN ChartOfAccounts ca ON jd.AccountID = ca.AccountID "
                    "WHERE 1=1" + date_filter + " ORDER BY ca.AccountCode",
                    params if params else None
                )
                if result:
                    all_details = result
            except Exception:
                pass

        if not self.use_db or not all_details:
            for jid, details in self.journal_details.items():
                je = next((j for j in self.journal_entries if j.get("JournalEntryID") == jid), None)
                if not je:
                    continue
                jdate = str(je.get("VoucherDate", ""))
                if start_str and jdate < start_str:
                    continue
                if end_str and jdate > end_str:
                    continue
                for d in details:
                    aid = d.get("AccountID")
                    if aid and aid in account_totals:
                        a = next((x for x in self.accounts if x["AccountID"] == aid), None)
                        all_details.append({
                            **d, "AccountID": aid,
                            "AccountCode": d.get("AccountCode", ""),
                            "AccountName": d.get("AccountName", ""),
                            "AccountType": a["AccountType"] if a else "Aktif",
                            "VoucherDate": jdate
                        })

        for d in all_details:
            aid = d.get("AccountID")
            if aid not in account_totals:
                continue
            debit = d.get("DebitAmount", 0) or 0
            credit = d.get("CreditAmount", 0) or 0
            account_totals[aid]["total_debit"] += debit
            account_totals[aid]["total_credit"] += credit

        grand_debit = 0.0
        grand_credit = 0.0
        grand_bal_debit = 0.0
        grand_bal_credit = 0.0

        sorted_aids = sorted(account_totals.keys(), key=lambda x: account_totals[x]["code"])
        for aid in sorted_aids:
            at = account_totals[aid]
            td = at["total_debit"]
            tc = at["total_credit"]
            if td == 0 and tc == 0:
                continue
            a = next((x for x in self.accounts if x["AccountID"] == aid), None)
            acc_type = a["AccountType"] if a else "Aktif"
            if acc_type in ("Pasif", "Gelir"):
                bal = tc - td
                if bal >= 0:
                    at["balance_credit"] = bal
                else:
                    at["balance_debit"] = abs(bal)
            else:
                bal = td - tc
                if bal >= 0:
                    at["balance_debit"] = bal
                else:
                    at["balance_credit"] = abs(bal)

            grand_debit += td
            grand_credit += tc
            grand_bal_debit += at["balance_debit"]
            grand_bal_credit += at["balance_credit"]

            self.mizan_tree.insert("", "end", values=(
                at["code"], at["name"],
                f"{td:,.2f}" if td else "-",
                f"{tc:,.2f}" if tc else "-",
                f"{at['balance_debit']:,.2f}" if at['balance_debit'] else "-",
                f"{at['balance_credit']:,.2f}" if at['balance_credit'] else "-"
            ))

        if self.mizan_tree.get_children():
            self.mizan_tree.insert("", "end", values=(
                "TOPLAM", "",
                f"{grand_debit:,.2f}",
                f"{grand_credit:,.2f}",
                f"{grand_bal_debit:,.2f}",
                f"{grand_bal_credit:,.2f}"
            ), tags=("total",))
            self.mizan_tree.tag_configure("total", font=("Segoe UI", 10, "bold"))
            self.mizan_summary_label.configure(
                text=f"Toplam Borc: {grand_debit:,.2f}  |  Toplam Alacak: {grand_credit:,.2f}  |  "
                     f"Borc Bakiyesi: {grand_bal_debit:,.2f}  |  Alacak Bakiyesi: {grand_bal_credit:,.2f}"
            )


# ---------------------------------------------------------------------- Date Picker
class DatePickerDialog(ctk.CTkToplevel):
    def __init__(self, parent, entry_widget):
        super().__init__(parent)
        self.entry = entry_widget
        self.title("Tarih Sec")
        self.geometry("300x280")
        self.transient(parent)
        self.grab_set()

        now = datetime.now()
        self.year = now.year
        self.month = now.month

        frame = ctk.CTkFrame(self, corner_radius=10, fg_color="#ffffff")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        nav = ctk.CTkFrame(frame, fg_color="transparent")
        nav.pack(fill="x", padx=5, pady=5)
        nav.grid_columnconfigure(2, weight=1)

        self.month_label = ctk.CTkLabel(nav, text="", font=ctk.CTkFont(size=14, weight="bold"))
        self.month_label.grid(row=0, column=2)

        ctk.CTkButton(nav, text="<", width=30, height=28,
                       command=self.prev_month, font=ctk.CTkFont(size=14)).grid(row=0, column=1, padx=2)
        ctk.CTkButton(nav, text=">", width=30, height=28,
                       command=self.next_month, font=ctk.CTkFont(size=14)).grid(row=0, column=3, padx=2)

        self.days_frame = ctk.CTkFrame(frame, fg_color="transparent")
        self.days_frame.pack(fill="both", expand=True, padx=5, pady=5)
        for i in range(7):
            self.days_frame.grid_columnconfigure(i, weight=1)

        self.render_calendar()

    def render_calendar(self):
        for w in self.days_frame.winfo_children():
            w.destroy()

        import calendar
        month_names = ["", "Ocak", "Subat", "Mart", "Nisan", "Mayis", "Haziran",
                       "Temmuz", "Agustos", "Eylul", "Ekim", "Kasim", "Aralik"]
        self.month_label.configure(text=f"{month_names[self.month]} {self.year}")

        day_names = ["Pzt", "Sali", "Car", "Per", "Cum", "Cmt", "Paz"]
        for i, dn in enumerate(day_names):
            ctk.CTkLabel(self.days_frame, text=dn, font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=TEXT_MUTED).grid(row=0, column=i, padx=1, pady=2)

        cal = calendar.monthcalendar(self.year, self.month)
        for r, week in enumerate(cal):
            for c, day in enumerate(week):
                if day == 0:
                    ctk.CTkLabel(self.days_frame, text="", width=32).grid(row=r + 1, column=c, padx=1, pady=1)
                else:
                    btn = ctk.CTkButton(self.days_frame, text=str(day), width=32, height=28,
                                         command=lambda d=day: self.select_date(d),
                                         fg_color="transparent", text_color=TEXT_DARK,
                                         hover_color="#e3f2fd", font=ctk.CTkFont(size=11))
                    btn.grid(row=r + 1, column=c, padx=1, pady=1)

    def prev_month(self):
        self.month -= 1
        if self.month < 1:
            self.month = 12
            self.year -= 1
        self.render_calendar()

    def next_month(self):
        self.month += 1
        if self.month > 12:
            self.month = 1
            self.year += 1
        self.render_calendar()

    def select_date(self, day):
        selected = date(self.year, self.month, day)
        self.entry.delete(0, "end")
        self.entry.insert(0, selected.strftime("%d.%m.%Y"))
        self.destroy()
