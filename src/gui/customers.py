"""
Accura Finance - Cari Hesaplar Modülü
Müşteri ve tedarikçi yönetimi
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class CustomersFrame(ctk.CTkFrame):
    def __init__(self, parent, main_app):
        super().__init__(parent)
        self.main_app = main_app
        self.db_manager = main_app.db_manager
        self.customers = []
        self.create_interface()
        self.load_customers()

    def create_interface(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        header = ctk.CTkFrame(self, height=60, corner_radius=10)
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        header.grid_propagate(False)
        ctk.CTkLabel(header, text="👥 CARİ HESAPLAR",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=("#1f538d", "#14375e")).pack(side="left", padx=20, pady=15)

        toolbar = ctk.CTkFrame(self, height=50, corner_radius=10)
        toolbar.grid(row=1, column=0, sticky="ew", padx=10, pady=5)

        for text, cmd, color in [
            ("➕ Müşteri Ekle", self.add_customer, "#2e7d32"),
            ("➕ Tedarikçi Ekle", self.add_supplier, "#1565c0"),
            ("📊 Bakiye Raporu", self.balance_report, "#7b1fa2"),
        ]:
            ctk.CTkButton(toolbar, text=text, command=cmd,
                fg_color=color, height=32,
                font=ctk.CTkFont(size=12, weight="bold"), corner_radius=8
            ).pack(side="left", padx=5, pady=8)

        content = ctk.CTkFrame(self, corner_radius=10)
        content.grid(row=2, column=0, sticky="nsew", padx=10, pady=(5, 10))
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)

        columns = ("ID", "Kod", "Unvan", "Tür", "Vergi No", "Telefon", "Email", "Bakiye", "Durum")
        self.tree = ttk.Treeview(content, columns=columns, show="headings", height=18)
        widths = [40, 80, 200, 100, 120, 120, 150, 120, 80]
        for col, w in zip(columns, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center")

        scroll = ttk.Scrollbar(content, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scroll.grid(row=0, column=1, sticky="ns", pady=5)

    def load_customers(self):
        try:
            if self.db_manager:
                result = self.db_manager.execute_query(
                    "SELECT * FROM CurrentAccounts WHERE IsActive=1 ORDER BY CurrentAccountName")
                if result:
                    self.customers = [dict(r) for r in result]
                else:
                    self._sample_data()
            else:
                self._sample_data()
            self.refresh_table()
        except:
            self._sample_data()
            self.refresh_table()

    def _sample_data(self):
        self.customers = [
            {"CurrentAccountID": 1, "CurrentAccountCode": "CAR1001", "CurrentAccountName": "ABC Ticaret Ltd. Şti.",
             "CurrentAccountType": "Musteri", "TaxNumber": "1234567890", "Phone": "0212 123 45 67",
             "Email": "info@abcticaret.com", "Balance": 150000},
            {"CurrentAccountID": 2, "CurrentAccountCode": "CAR2001", "CurrentAccountName": "XYZ Tekstil San. A.Ş.",
             "CurrentAccountType": "Tedarikci", "TaxNumber": "9876543210", "Phone": "0216 234 56 78",
             "Email": "info@xyztekstil.com", "Balance": -85000},
        ]

    def refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for c in self.customers:
            bal = c.get("Balance", 0)
            bal_str = f"{bal:,.0f} ₺" if bal >= 0 else f"({abs(bal):,.0f} ₺)"
            self.tree.insert("", "end", values=(
                c.get("CurrentAccountID"),
                c.get("CurrentAccountCode"),
                c.get("CurrentAccountName"),
                "👤 Müşteri" if c.get("CurrentAccountType") == "Musteri" else "🏭 Tedarikçi",
                c.get("TaxNumber"),
                c.get("Phone"),
                c.get("Email"),
                bal_str,
                "✅ Aktif" if c.get("IsActive", 1) else "❌ Pasif"
            ))

    def add_customer(self):
        self._add_dialog("Müşteri")

    def add_supplier(self):
        self._add_dialog("Tedarikçi")

    def _add_dialog(self, ctype):
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"➕ {ctype} Ekle")
        dialog.geometry("500x500")
        dialog.transient(self)
        dialog.grab_set()

        frame = ctk.CTkFrame(dialog, corner_radius=10)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text=f"➕ YENİ {ctype.upper()}",
            font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(0, 20))

        fields = {}
        for label in ["Unvan", "Vergi No", "Vergi Dairesi", "Telefon", "Email", "Adres"]:
            ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=12, weight="bold"),
                anchor="w").pack(fill="x", padx=20)
            e = ctk.CTkEntry(frame, height=35, font=ctk.CTkFont(size=14))
            e.pack(fill="x", padx=20, pady=(0, 10))
            fields[label] = e

        def save():
            try:
                code = f"CAR{len(self.customers)+1001}"
                ctype_en = "Musteri" if ctype == "Müşteri" else "Tedarikci"
                new_c = {
                    "CurrentAccountCode": code, "CurrentAccountName": fields["Unvan"].get(),
                    "CurrentAccountType": ctype_en, "TaxNumber": fields["Vergi No"].get(),
                    "Phone": fields["Telefon"].get(), "Email": fields["Email"].get(),
                    "Address": fields["Adres"].get(), "Balance": 0, "IsActive": 1
                }
                new_c["CurrentAccountID"] = len(self.customers) + 1
                self.customers.append(new_c)
                self.refresh_table()
                messagebox.showinfo("Başarılı", f"{ctype} eklendi!")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Hata", str(e))

        ctk.CTkButton(frame, text="💾 Kaydet", command=save,
            fg_color="#2e7d32" if ctype == "Müşteri" else "#1565c0",
            height=40, font=ctk.CTkFont(size=14, weight="bold")).pack(pady=15)

    def balance_report(self):
        messagebox.showinfo("Bilgi", "Bakiye raporu yakında eklenecek.")
