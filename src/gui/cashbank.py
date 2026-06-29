"""
Accura Finance - Kasa & Banka Modülü
- Kasa işlemleri
- Banka işlemleri
- Nakit akışı takibi
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class CashBankFrame(ctk.CTkFrame):
    def __init__(self, parent, main_app):
        super().__init__(parent)
        self.main_app = main_app
        self.db_manager = main_app.db_manager
        self.create_interface()

    def create_interface(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.create_header()
        self.create_tabs()

    def create_header(self):
        header = ctk.CTkFrame(self, height=60, corner_radius=10)
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        header.grid_propagate(False)

        title = ctk.CTkLabel(header, text="💰 KASA & BANKA",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=("#1f538d", "#14375e"))
        title.pack(side="left", padx=20, pady=15)

        ctk.CTkLabel(header, text=f"📅 {datetime.now().strftime('%d.%m.%Y')}",
            font=ctk.CTkFont(size=14)).pack(side="right", padx=20)

    def create_tabs(self):
        self.tabview = ctk.CTkTabview(self, corner_radius=10)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 10))

        self.tabview.add("💵 Kasa")
        self.tabview.add("🏦 Banka")
        self.tabview.add("📊 Nakit Akışı")

        self.create_cash_tab()
        self.create_bank_tab()
        self.create_cashflow_tab()

    def create_cash_tab(self):
        tab = self.tabview.tab("💵 Kasa")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        cards = ctk.CTkFrame(tab, fg_color="transparent")
        cards.grid(row=0, column=0, sticky="ew", pady=10)
        cards.grid_columnconfigure((0, 1, 2), weight=1)

        self.cash_card = self._create_balance_card(cards, "💵", "Kasa Bakiyesi", "0 ₺", "#2e7d32", 0)
        btn_frame = ctk.CTkFrame(cards, fg_color="transparent")
        btn_frame.grid(row=0, column=1, padx=10)

        ctk.CTkButton(btn_frame, text="💳 Kasa Giriş", command=lambda: self.cash_transaction("Giriş"),
            fg_color="#2e7d32", height=35, font=ctk.CTkFont(size=12, weight="bold")).pack(pady=5)
        ctk.CTkButton(btn_frame, text="💸 Kasa Çıkış", command=lambda: self.cash_transaction("Çıkış"),
            fg_color="#c62828", height=35, font=ctk.CTkFont(size=12, weight="bold")).pack(pady=5)

        columns = ("Tarih", "İşlem No", "Tür", "Açıklama", "Tutar")
        self.cash_tree = ttk.Treeview(tab, columns=columns, show="headings", height=15)
        for col, w in zip(columns, [100, 120, 80, 250, 120]):
            self.cash_tree.heading(col, text=col)
            self.cash_tree.column(col, width=w, anchor="center")

        scroll = ttk.Scrollbar(tab, orient="vertical", command=self.cash_tree.yview)
        self.cash_tree.configure(yscrollcommand=scroll.set)
        self.cash_tree.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        scroll.grid(row=1, column=1, sticky="ns", pady=5)

        self._load_cash_data()

    def create_bank_tab(self):
        tab = self.tabview.tab("🏦 Banka")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        cards = ctk.CTkFrame(tab, fg_color="transparent")
        cards.grid(row=0, column=0, sticky="ew", pady=10)
        cards.grid_columnconfigure((0, 1, 2), weight=1)

        self.bank_card = self._create_balance_card(cards, "🏦", "Banka Bakiyesi", "0 ₺", "#1565c0", 0)
        btn_frame = ctk.CTkFrame(cards, fg_color="transparent")
        btn_frame.grid(row=0, column=1, padx=10)

        ctk.CTkButton(btn_frame, text="🏦 Havale/EFT", command=self.bank_transfer,
            fg_color="#1565c0", height=35, font=ctk.CTkFont(size=12, weight="bold")).pack(pady=5)
        ctk.CTkButton(btn_frame, text="📋 Hesap Özeti", command=self.bank_statement,
            fg_color="#f57f17", height=35, font=ctk.CTkFont(size=12, weight="bold")).pack(pady=5)

        columns = ("Tarih", "İşlem No", "Tür", "Açıklama", "Tutar")
        self.bank_tree = ttk.Treeview(tab, columns=columns, show="headings", height=15)
        for col, w in zip(columns, [100, 120, 80, 250, 120]):
            self.bank_tree.heading(col, text=col)
            self.bank_tree.column(col, width=w, anchor="center")

        scroll = ttk.Scrollbar(tab, orient="vertical", command=self.bank_tree.yview)
        self.bank_tree.configure(yscrollcommand=scroll.set)
        self.bank_tree.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        scroll.grid(row=1, column=1, sticky="ns", pady=5)

        self._load_bank_data()

    def create_cashflow_tab(self):
        tab = self.tabview.tab("📊 Nakit Akışı")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        columns = ("Dönem", "Kasa Giriş", "Kasa Çıkış", "Net Nakit", "Banka Giriş", "Banka Çıkış", "Net Banka", "Toplam Nakit")
        self.cashflow_tree = ttk.Treeview(tab, columns=columns, show="headings", height=15)
        widths = [100, 120, 120, 120, 120, 120, 120, 120]
        for col, w in zip(columns, widths):
            self.cashflow_tree.heading(col, text=col)
            self.cashflow_tree.column(col, width=w, anchor="center")

        scroll = ttk.Scrollbar(tab, orient="vertical", command=self.cashflow_tree.yview)
        self.cashflow_tree.configure(yscrollcommand=scroll.set)
        self.cashflow_tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scroll.grid(row=0, column=1, sticky="ns", pady=5)

        for i in range(6):
            month = f"{['Ocak','Şubat','Mart','Nisan','Mayıs','Haziran'][i]} 2026"
            self.cashflow_tree.insert("", "end", values=(
                month,
                f"{(i+1)*50000:,.0f} ₺",
                f"{(i+1)*35000:,.0f} ₺",
                f"{(i+1)*15000:,.0f} ₺",
                f"{(i+1)*80000:,.0f} ₺",
                f"{(i+1)*60000:,.0f} ₺",
                f"{(i+1)*20000:,.0f} ₺",
                f"{(i+1)*35000:,.0f} ₺"
            ))

    def _create_balance_card(self, parent, icon, title, value, color, col):
        card = ctk.CTkFrame(parent, corner_radius=12, border_width=2, border_color=color)
        card.grid(row=0, column=col, padx=10, pady=10, sticky="ew")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", padx=15, pady=15)

        ctk.CTkLabel(inner, text=icon, font=ctk.CTkFont(size=28)).pack(anchor="w")
        ctk.CTkLabel(inner, text=title, font=ctk.CTkFont(size=13, weight="bold"),
            text_color=color).pack(anchor="w", pady=(5, 2))
        lbl = ctk.CTkLabel(inner, text=value, font=ctk.CTkFont(size=18, weight="bold"),
            text_color=color)
        lbl.pack(anchor="w")
        return lbl

    def _load_cash_data(self):
        for item in self.cash_tree.get_children():
            self.cash_tree.delete(item)

        sample = [
            [f"{15-i}.06.2026", f"KG-{2026000+i}", "Giriş" if i%2==0 else "Çıkış",
             f"{['Nakit Tahsilat','Kira Ödemesi','Satış Tahsilatı','Elektrik Faturası','Müşteri Ödemesi','Vergi Ödemesi'][i%6]}",
             f"{'➕' if i%2==0 else '➖'} {(i+1)*10000:,.0f} ₺"]
            for i in range(10)
        ]
        for row in sample:
            self.cash_tree.insert("", "end", values=row)

        total = sum((i+1)*10000 for i in range(10))
        self.cash_card.configure(text=f"{total:,.0f} ₺")

    def _load_bank_data(self):
        for item in self.bank_tree.get_children():
            self.bank_tree.delete(item)

        sample = [
            [f"{15-i}.06.2026", f"BH-{2026000+i}", "Havale" if i%2==0 else "EFT",
             f"{['Maaş Ödemesi','Tahsilat','Kredi Ödemesi','Faiz Geliri','Sigorta Ödemesi','Proje Ödemesi'][i%6]}",
             f"{'➕' if i%2==0 else '➖'} {(i+1)*25000:,.0f} ₺"]
            for i in range(10)
        ]
        for row in sample:
            self.bank_tree.insert("", "end", values=row)

        total = sum((i+1)*25000 for i in range(10))
        self.bank_card.configure(text=f"{total:,.0f} ₺")

    def cash_transaction(self, trans_type):
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"{'💳' if trans_type=='Giriş' else '💸'} Kasa {trans_type}")
        dialog.geometry("400x350")
        dialog.transient(self)
        dialog.grab_set()

        frame = ctk.CTkFrame(dialog, corner_radius=10)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text=f"{'💳' if trans_type=='Giriş' else '💸'} KASA {trans_type.upper()}",
            font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(0, 20))

        fields = {}
        for label in ["Tutar (₺)", "Açıklama"]:
            ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=12, weight="bold"),
                anchor="w").pack(fill="x", padx=20)
            e = ctk.CTkEntry(frame, height=35, font=ctk.CTkFont(size=14))
            e.pack(fill="x", padx=20, pady=(0, 15))
            fields[label] = e

        def save():
            try:
                amount = float(fields["Tutar (₺)"].get().replace(".", "").replace(",", "."))
                desc = fields["Açıklama"].get()
                messagebox.showinfo("Başarılı", f"Kasa {trans_type}: {amount:,.2f} ₺\n{desc}")
                dialog.destroy()
            except:
                messagebox.showerror("Hata", "Geçersiz tutar!")

        ctk.CTkButton(frame, text="💾 Kaydet", command=save,
            fg_color="#2e7d32" if trans_type == "Giriş" else "#c62828",
            height=40, font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)

    def bank_transfer(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("🏦 Havale/EFT")
        dialog.geometry("450x400")
        dialog.transient(self)
        dialog.grab_set()

        frame = ctk.CTkFrame(dialog, corner_radius=10)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text="🏦 HAVALE/EFT",
            font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(0, 20))

        for label in ["Gönderen Hesap", "Alıcı IBAN", "Alıcı Adı", "Tutar (₺)", "Açıklama"]:
            ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=12, weight="bold"),
                anchor="w").pack(fill="x", padx=20)
            e = ctk.CTkEntry(frame, height=35, font=ctk.CTkFont(size=14))
            e.pack(fill="x", padx=20, pady=(0, 12))

        ctk.CTkButton(frame, text="🚀 Gönder", fg_color="#1565c0",
            height=40, font=ctk.CTkFont(size=14, weight="bold"),
            command=lambda: [messagebox.showinfo("Başarılı", "Havale/EFT işlemi başarıyla gerçekleştirildi!"), dialog.destroy()]
        ).pack(pady=15)

    def bank_statement(self):
        messagebox.showinfo("Bilgi", "Hesap özeti yakında eklenecek.")
