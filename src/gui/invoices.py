"""
Accura Finance - Fatura Yönetimi Modülü
AI destekli otomatik fatura işleme
GitHub entegrasyonu ile senkronizasyon
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
import threading
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class InvoicesFrame(ctk.CTkFrame):
    def __init__(self, parent, main_app):
        super().__init__(parent)
        self.main_app = main_app
        self.db_manager = main_app.db_manager
        self.invoices = []
        self.filtered_invoices = []
        self.ai_agent = None
        self.github = None

        self._init_ai()
        self.create_interface()
        self.load_invoices()

    def _init_ai(self):
        try:
            from src.ai_agent import get_ai_agent
            from src.github_integration import get_github_integration
            self.ai_agent = get_ai_agent()
            self.github = get_github_integration(db_manager=self.db_manager)
        except Exception as e:
            print(f"AI yükleme hatası: {e}")

    def create_interface(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.create_header()
        self.create_toolbar()
        self.create_table()
        self.create_status_bar()

    def create_header(self):
        header = ctk.CTkFrame(self, height=60, corner_radius=10)
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        header.grid_propagate(False)

        title = ctk.CTkLabel(header, text="🧾 FATURA YÖNETİMİ",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=("#1f538d", "#14375e"))
        title.pack(side="left", padx=20, pady=15)

        ai_label = ctk.CTkLabel(header, text="🤖 AI Aktif",
            font=ctk.CTkFont(size=12), text_color=("#2e7d32", "#66bb6a"))
        ai_label.pack(side="right", padx=20)

    def create_toolbar(self):
        toolbar = ctk.CTkFrame(self, height=50, corner_radius=10)
        toolbar.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        toolbar.grid_columnconfigure(3, weight=1)

        buttons = [
            ("➕ Yeni Fatura", self.new_invoice, "#2e7d32"),
            ("📥 GitHub'dan İçe Aktar", self.import_from_github, "#1565c0"),
            ("🤖 AI Fatura İşle", self.ai_process_invoice, "#7b1fa2"),
            ("🔄 Senkronize Et", self.sync_github, "#f57f17"),
        ]

        for i, (text, cmd, color) in enumerate(buttons):
            btn = ctk.CTkButton(toolbar, text=text, command=cmd,
                fg_color=color, hover_color=color, height=32,
                font=ctk.CTkFont(size=12, weight="bold"), corner_radius=8)
            btn.grid(row=0, column=i, padx=5, pady=8)

        search_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        search_frame.grid(row=0, column=3, sticky="e", padx=10)

        self.search_entry = ctk.CTkEntry(search_frame, width=200, height=32,
            placeholder_text="🔍 Fatura ara...")
        self.search_entry.pack(side="left", padx=(0, 5))
        self.search_entry.bind("<KeyRelease>", self.filter_invoices)

        ctk.CTkButton(search_frame, text="Ara", width=60, height=32,
            command=self.filter_invoices, font=ctk.CTkFont(size=11)).pack(side="left")

    def create_table(self):
        table_frame = ctk.CTkFrame(self, corner_radius=10)
        table_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(5, 10))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        columns = ("ID", "Fatura No", "Tür", "Tarih", "Cari Hesap", "Toplam", "KDV", "Durum", "Kaynak")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)

        col_widths = [50, 150, 80, 100, 200, 120, 80, 100, 100]
        for col, width in zip(columns, col_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scrollbar.grid(row=0, column=1, sticky="ns", pady=5)

        self.tree.bind("<Double-1>", self.on_invoice_double_click)

    def create_status_bar(self):
        status = ctk.CTkFrame(self, height=30, corner_radius=5)
        status.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 5))

        self.status_label = ctk.CTkLabel(status, text="Hazır", font=ctk.CTkFont(size=11))
        self.status_label.pack(side="left", padx=10, pady=5)

        self.count_label = ctk.CTkLabel(status, text="0 fatura", font=ctk.CTkFont(size=11))
        self.count_label.pack(side="right", padx=10, pady=5)

    def load_invoices(self):
        try:
            if not self.db_manager:
                self._load_sample_data()
                return

            query = """
            SELECT i.InvoiceID, i.InvoiceNumber, i.InvoiceType, i.InvoiceDate,
                   IFNULL(c.CurrentAccountName, '') as CurrentAccountName,
                   i.TotalAmount, i.VATAmount, i.IsPosted,
                   CASE WHEN i.Notes LIKE '%github%' THEN 'GitHub' ELSE 'Manuel' END as Source
            FROM Invoices i
            LEFT JOIN CurrentAccounts c ON i.CurrentAccountID = c.CurrentAccountID
            ORDER BY i.InvoiceDate DESC
            """
            result = self.db_manager.execute_query(query)

            if result and len(result) > 0:
                self.invoices = [{
                    "id": r["InvoiceID"],
                    "no": r["InvoiceNumber"],
                    "type": "📤 Satış" if r["InvoiceType"] == "Satis" else "📥 Alış",
                    "date": r["InvoiceDate"].strftime("%d.%m.%Y") if hasattr(r["InvoiceDate"], "strftime") else str(r["InvoiceDate"]),
                    "customer": r["CurrentAccountName"],
                    "total": f"{r['TotalAmount']:,.2f} ₺",
                    "vat": f"{r['VATAmount']:,.2f} ₺",
                    "status": "✅ İşlendi" if r["IsPosted"] else "⏳ Bekliyor",
                    "source": r["Source"]
                } for r in result]
            else:
                self._load_sample_data()

            self.refresh_table()
            self.status_label.configure(text=f"{len(self.invoices)} fatura yüklendi")

        except Exception as e:
            print(f"Fatura yükleme hatası: {e}")
            self._load_sample_data()

    def _load_sample_data(self):
        self.invoices = []
        for i in range(10):
            self.invoices.append({
                "id": i + 1,
                "no": f"FT-{2026000 + i}",
                "type": "📤 Satış" if i % 2 == 0 else "📥 Alış",
                "date": f"{15 - i}.06.2026",
                "customer": f"Firma {['ABC', 'XYZ', 'DEF', 'GHI', 'JKL'][i % 5]} Ticaret",
                "total": f"{(i + 1) * 15000:,.2f} ₺",
                "vat": f"{(i + 1) * 2700:,.2f} ₺",
                "status": "✅ İşlendi" if i < 6 else "⏳ Bekliyor",
                "source": "Manuel" if i < 8 else "GitHub"
            })

    def refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        data = self.filtered_invoices if self.filtered_invoices else self.invoices
        for inv in data:
            values = (inv["id"], inv["no"], inv["type"], inv["date"],
                     inv["customer"], inv["total"], inv["vat"], inv["status"], inv["source"])
            self.tree.insert("", "end", values=values)

        self.count_label.configure(text=f"{len(data)} fatura")

    def filter_invoices(self, event=None):
        search = self.search_entry.get().lower().strip()
        if not search:
            self.filtered_invoices = []
            self.refresh_table()
            return

        self.filtered_invoices = [inv for inv in self.invoices
            if search in inv["no"].lower() or search in inv["customer"].lower()]
        self.refresh_table()

    def new_invoice(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Yeni Fatura")
        dialog.geometry("500x600")
        dialog.transient(self)
        dialog.grab_set()

        frame = ctk.CTkFrame(dialog, corner_radius=10)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text="➕ YENİ FATURA", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(0, 20))

        fields = {}
        for field in ["Fatura No", "Tür (Alış/Satış)", "Tarih (GG.AA.YYYY)", "Cari Hesap", "Toplam Tutar"]:
            ctk.CTkLabel(frame, text=field, font=ctk.CTkFont(size=12, weight="bold"),
                anchor="w").pack(fill="x", padx=20)
            entry = ctk.CTkEntry(frame, height=35, font=ctk.CTkFont(size=14))
            entry.pack(fill="x", padx=20, pady=(0, 15))
            fields[field] = entry

        fields["Fatura No"].insert(0, f"FT-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        fields["Tarih (GG.AA.YYYY)"].insert(0, datetime.now().strftime("%d.%m.%Y"))

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(pady=20)

        ctk.CTkButton(btn_frame, text="💾 Kaydet", command=lambda: self._save_invoice_dialog(dialog, fields),
            fg_color="#2e7d32", height=40, width=150,
            font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=10)

        ctk.CTkButton(btn_frame, text="❌ İptal", command=dialog.destroy,
            fg_color="#c62828", height=40, width=150,
            font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=10)

    def _save_invoice_dialog(self, dialog, fields):
        try:
            inv_no = fields["Fatura No"].get()
            inv_type = fields["Tür (Alış/Satış)"].get()
            inv_date = fields["Tarih (GG.AA.YYYY)"].get()
            customer = fields["Cari Hesap"].get()
            total = float(fields["Toplam Tutar"].get().replace(".", "").replace(",", "."))

            if self.db_manager:
                query = """
                INSERT INTO Invoices (InvoiceNumber, InvoiceType, InvoiceDate, SubTotal, VATAmount, TotalAmount, CreatedDate)
                VALUES (?, ?, ?, ?, ?, ?, GETDATE())
                """
                self.db_manager.execute_query(query, (inv_no, inv_type, inv_date, total * 0.82, total * 0.18, total), fetch=False)

            self.invoices.insert(0, {
                "id": len(self.invoices) + 1,
                "no": inv_no,
                "type": "📤 Satış" if "satış" in inv_type.lower() or "satis" in inv_type.lower() else "📥 Alış",
                "date": inv_date,
                "customer": customer,
                "total": f"{total:,.2f} ₺",
                "vat": f"{total * 0.18:,.2f} ₺",
                "status": "⏳ Bekliyor",
                "source": "Manuel"
            })
            self.refresh_table()
            messagebox.showinfo("Başarılı", "Fatura kaydedildi!")
            dialog.destroy()

        except Exception as e:
            messagebox.showerror("Hata", f"Kayıt hatası: {e}")

    def import_from_github(self):
        def task():
            self.status_label.configure(text="📥 GitHub'dan faturalar alınıyor...")

            if not self.github:
                self.after(0, lambda: messagebox.showerror("Hata", "GitHub entegrasyonu yüklenemedi!"))
                return

            invoices = self.github.sync_invoices_from_github()
            if "error" in invoices:
                self.after(0, lambda: messagebox.showerror("Hata", f"GitHub hatası: {invoices['error']}"))
                self.status_label.configure(text="GitHub bağlantı hatası")
                return

            imported = 0
            for inv_data in invoices:
                result = self.github.auto_process_invoice(inv_data)
                if result["status"] == "success":
                    inv = result["invoice"]
                    self.invoices.insert(0, {
                        "id": len(self.invoices) + 1,
                        "no": inv.get("fatura_no", "Bilinmiyor"),
                        "type": "📤 Satış" if inv.get("fatura_turu") == "Satis" else "📥 Alış",
                        "date": inv.get("tarih", ""),
                        "customer": inv.get("cari_unvan", ""),
                        "total": f"{inv.get('genel_toplam', 0):,.2f} ₺",
                        "vat": f"{inv.get('kdv_toplam', 0):,.2f} ₺",
                        "status": "✅ İşlendi",
                        "source": "GitHub"
                    })
                    imported += 1

            self.after(0, self.refresh_table)
            self.after(0, lambda: messagebox.showinfo("Başarılı", f"{imported} fatura içe aktarıldı!"))
            self.after(0, lambda: self.status_label.configure(text=f"{imported} fatura içe aktarıldı"))

        threading.Thread(target=task, daemon=True).start()

    def ai_process_invoice(self):
        if not self.ai_agent:
            messagebox.showerror("Hata", "AI Agent yüklenemedi!")
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("🤖 AI Fatura İşleme")
        dialog.geometry("600x500")
        dialog.transient(self)
        dialog.grab_set()

        frame = ctk.CTkFrame(dialog, corner_radius=10)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text="🤖 AI FATURA İŞLEME",
            font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(0, 15))

        ctk.CTkLabel(frame, text="Fatura metnini yapıştırın:", font=ctk.CTkFont(size=12)).pack(anchor="w")

        text_area = ctk.CTkTextbox(frame, height=200, font=ctk.CTkFont(size=12))
        text_area.pack(fill="both", expand=True, padx=10, pady=10)

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(pady=10)

        result_label = ctk.CTkLabel(frame, text="", font=ctk.CTkFont(size=12), wraplength=500)
        result_label.pack(fill="x", padx=10)

        def process():
            text = text_area.get("1.0", "end-1c").strip()
            if not text:
                messagebox.showwarning("Uyarı", "Lütfen fatura metnini girin!")
                return

            result_label.configure(text="🤖 AI işleniyor...")
            dialog.update()

            result = self.ai_agent.process_invoice_text(text)
            if "raw" in result:
                result_label.configure(text=f"⚠️ AI çıktısı:\n{result['raw']}")
            else:
                output = (
                    f"✅ Fatura Başarıyla İşlendi!\n\n"
                    f"📄 Fatura No: {result.get('fatura_no', '-')}\n"
                    f"🏢 Cari: {result.get('cari_unvan', '-')}\n"
                    f"📅 Tarih: {result.get('tarih', '-')}\n"
                    f"💰 Toplam: {result.get('genel_toplam', 0):,.2f} ₺\n"
                    f"📦 Ürün Sayısı: {len(result.get('urunler', []))}"
                )
                result_label.configure(text=output)

                if self.db_manager:
                    try:
                        inv_no = f"AI-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                        inv_type = "Satis" if result.get("fatura_turu") in ["Satis", "satış", "Sale"] else "Alis"
                        inv_date = result.get("tarih", datetime.now().strftime("%d.%m.%Y"))

                        query = """
                        INSERT INTO Invoices (InvoiceNumber, InvoiceType, InvoiceDate,
                            SubTotal, VATAmount, TotalAmount, Notes, CreatedDate)
                        VALUES (?, ?, ?, ?, ?, ?, ?, GETDATE())
                        """
                        self.db_manager.execute_query(query, (
                            inv_no, inv_type, inv_date,
                            result.get("ara_toplam", 0),
                            result.get("kdv_toplam", 0),
                            result.get("genel_toplam", 0),
                            "AI tarafından otomatik işlendi"
                        ), fetch=False)

                        result_label.configure(text=result_label.cget("text") + "\n\n✅ Veritabanına kaydedildi!")
                    except Exception as db_err:
                        result_label.configure(text=result_label.cget("text") + f"\n\n⚠️ DB kayıt hatası: {db_err}")

        ctk.CTkButton(btn_frame, text="🤖 AI ile İşle", command=process,
            fg_color="#7b1fa2", height=40, width=200,
            font=ctk.CTkFont(size=14, weight="bold")).pack()

    def sync_github(self):
        def task():
            self.status_label.configure(text="🔄 GitHub ile senkronize ediliyor...")

            if not self.github:
                self.after(0, lambda: messagebox.showerror("Hata", "GitHub entegrasyonu yüklenemedi!"))
                return

            issues = self.github.list_issues()
            for issue in issues:
                result = self.github.close_issue(issue["number"],
                    f"Accura Finance tarafından otomatik işlendi.\nTarih: {datetime.now().isoformat()}")

            self.after(0, lambda: messagebox.showinfo("Başarılı",
                f"GitHub senkronize edildi! {len(issues)} issue işlendi."))
            self.after(0, lambda: self.status_label.configure(text="GitHub senkronize edildi"))

        threading.Thread(target=task, daemon=True).start()

    def on_invoice_double_click(self, event):
        selection = self.tree.selection()
        if not selection:
            return

        item = self.tree.item(selection[0])
        values = item["values"]

        detail = ctk.CTkToplevel(self)
        detail.title(f"Fatura Detay - {values[1]}")
        detail.geometry("400x300")
        detail.transient(self)
        detail.grab_set()

        frame = ctk.CTkFrame(detail, corner_radius=10)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text=f"🧾 Fatura: {values[1]}",
            font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(0, 20))

        details = [
            f"📄 Fatura No: {values[1]}",
            f"📋 Tür: {values[2]}",
            f"📅 Tarih: {values[3]}",
            f"🏢 Cari Hesap: {values[4]}",
            f"💰 Toplam: {values[5]}",
            f"🧾 KDV: {values[6]}",
            f"📊 Durum: {values[7]}",
            f"🌐 Kaynak: {values[8]}"
        ]

        for detail_text in details:
            ctk.CTkLabel(frame, text=detail_text, font=ctk.CTkFont(size=13),
                anchor="w").pack(fill="x", padx=20, pady=3)
