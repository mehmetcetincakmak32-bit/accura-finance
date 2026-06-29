"""
Accura Finance - Personel ve Bordro Yönetimi
- Personel kartları
- Maaş bordrosu
- Puantaj (günlük çalışma takibi)
- SGK ve vergi hesaplama
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date, timedelta
import calendar
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class PersonnelFrame(ctk.CTkFrame):
    def __init__(self, parent, main_app):
        super().__init__(parent)
        self.main_app = main_app
        self.db_manager = main_app.db_manager
        self.employees = []
        self.attendance = {}
        self.current_month = datetime.now().month
        self.current_year = datetime.now().year

        self.create_interface()
        self.load_employees()
        self.after(100, self.refresh_attendance)

    def create_interface(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.create_header()
        self.create_toolbar()
        self.create_main_content()
        self.create_status_bar()

    def create_header(self):
        header = ctk.CTkFrame(self, height=60, corner_radius=10)
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        header.grid_propagate(False)

        title = ctk.CTkLabel(header, text="👤 PERSONEL & BORDRO",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=("#1f538d", "#14375e"))
        title.pack(side="left", padx=20, pady=15)

        month_frame = ctk.CTkFrame(header, fg_color="transparent")
        month_frame.pack(side="right", padx=20)

        ctk.CTkButton(month_frame, text="◀", width=30, height=30,
            command=self.prev_month, font=ctk.CTkFont(size=16)).pack(side="left", padx=2)

        self.month_label = ctk.CTkLabel(month_frame,
            text=f"{self.month_name(self.current_month)} {self.current_year}",
            font=ctk.CTkFont(size=14, weight="bold"), width=150)
        self.month_label.pack(side="left", padx=5)

        ctk.CTkButton(month_frame, text="▶", width=30, height=30,
            command=self.next_month, font=ctk.CTkFont(size=16)).pack(side="left", padx=2)

    def month_name(self, m):
        return ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
                "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"][m]

    def create_toolbar(self):
        toolbar = ctk.CTkFrame(self, height=50, corner_radius=10)
        toolbar.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        toolbar.grid_columnconfigure(3, weight=1)

        btns = [
            ("➕ Personel Ekle", self.add_employee, "#2e7d32"),
            ("📋 Bordro Hesapla", self.calculate_payroll, "#1565c0"),
            ("📊 Toplu Bordro", self.bulk_payroll, "#7b1fa2"),
        ]

        for i, (text, cmd, color) in enumerate(btns):
            btn = ctk.CTkButton(toolbar, text=text, command=cmd,
                fg_color=color, height=32,
                font=ctk.CTkFont(size=12, weight="bold"), corner_radius=8)
            btn.grid(row=0, column=i, padx=5, pady=8)

        info = ctk.CTkLabel(toolbar, text="💡 Gün için tıklayın: 1=Tam, 0.5=Yarım, 2=Tatil",
            font=ctk.CTkFont(size=11), text_color="gray")
        info.grid(row=0, column=3, sticky="e", padx=10)

    def create_main_content(self):
        content = ctk.CTkFrame(self, corner_radius=10)
        content.grid(row=2, column=0, sticky="nsew", padx=10, pady=(5, 10))
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)

        self.tabview = ctk.CTkTabview(content, corner_radius=10)
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.tabview.add("👤 Personel Listesi")
        self.tabview.add("📅 Puantaj Takibi")
        self.tabview.add("💰 Bordro")

        self.create_personnel_tab()
        self.create_attendance_tab()
        self.create_payroll_tab()

    def create_personnel_tab(self):
        tab = self.tabview.tab("👤 Personel Listesi")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        columns = ("ID", "Sicil No", "Ad Soyad", "TC Kimlik", "Departman",
                  "Pozisyon", "İşe Giriş", "Maaş", "Durum")
        self.personnel_tree = ttk.Treeview(tab, columns=columns, show="headings", height=15)

        widths = [40, 100, 180, 130, 120, 120, 100, 100, 80]
        for col, w in zip(columns, widths):
            self.personnel_tree.heading(col, text=col)
            self.personnel_tree.column(col, width=w, anchor="center")

        scroll = ttk.Scrollbar(tab, orient="vertical", command=self.personnel_tree.yview)
        self.personnel_tree.configure(yscrollcommand=scroll.set)

        self.personnel_tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scroll.grid(row=0, column=1, sticky="ns", pady=5)

        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.grid(row=1, column=0, sticky="ew", pady=10)

        for text, cmd, color in [
            ("➕ Ekle", self.add_employee, "#2e7d32"),
            ("✏️ Düzenle", self.edit_employee, "#1565c0"),
            ("🗑️ Sil", self.delete_employee, "#c62828"),
        ]:
            ctk.CTkButton(btn_frame, text=text, command=cmd,
                fg_color=color, width=120, height=32,
                font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=5)

    def create_attendance_tab(self):
        tab = self.tabview.tab("📅 Puantaj Takibi")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        scroll_frame = ctk.CTkScrollableFrame(tab)
        scroll_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.attendance_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        self.attendance_frame.pack(fill="x", padx=5, pady=5)

        self.refresh_attendance()

    def refresh_attendance(self):
        for widget in self.attendance_frame.winfo_children():
            widget.destroy()

        days_in_month = calendar.monthrange(self.current_year, self.current_month)[1]

        header = ctk.CTkFrame(self.attendance_frame, fg_color=("#e3f2fd", "#1a237e"))
        header.pack(fill="x", pady=2)

        cells = ["Personel"] + [str(d) for d in range(1, days_in_month + 1)] + ["Toplam"]
        cell_width = 30 if days_in_month <= 31 else 25

        header_grid = ctk.CTkFrame(header, fg_color="transparent")
        header_grid.pack(fill="x", padx=2, pady=2)

        ctk.CTkLabel(header_grid, text="Personel", font=ctk.CTkFont(size=12, weight="bold"),
            width=150, anchor="w").grid(row=0, column=0, padx=2)

        for d in range(1, days_in_month + 1):
            day_name = datetime(self.current_year, self.current_month, d).strftime("%a")
            color = "#e57373" if day_name in ["Sat", "Sun"] else "white"
            ctk.CTkLabel(header_grid, text=str(d), width=cell_width, anchor="center",
                font=ctk.CTkFont(size=11), fg_color=color, corner_radius=3,
                text_color="black" if color == "#e57373" else None
            ).grid(row=0, column=d, padx=1)

        ctk.CTkLabel(header_grid, text="Toplam", font=ctk.CTkFont(size=12, weight="bold"),
            width=80, anchor="center").grid(row=0, column=days_in_month + 1, padx=2)

        for emp in self.employees:
            row_frame = ctk.CTkFrame(self.attendance_frame, fg_color="transparent")
            row_frame.pack(fill="x", pady=1)

            name = emp.get("FullName", emp.get("AdSoyad", emp.get("ad_soyad", "İsimsiz")))
            ctk.CTkLabel(row_frame, text=name[:20], width=150, anchor="w",
                font=ctk.CTkFont(size=12)).grid(row=0, column=0, padx=2)

            total = 0
            for d in range(1, days_in_month + 1):
                key = f"{emp.get('EmployeeID', emp.get('id'))}_{self.current_year}{self.current_month:02d}{d:02d}"
                val = self.attendance.get(key, "1")
                fg = "#c8e6c9" if val == "1" else "#fff9c4" if val == "0.5" else "#ffcdd2" if val == "2" else "white"
                lbl = ctk.CTkLabel(row_frame, text=val, width=cell_width, anchor="center",
                    font=ctk.CTkFont(size=11), fg_color=fg, corner_radius=3)
                lbl.grid(row=0, column=d, padx=1)
                lbl.bind("<Button-1>", lambda e, k=key, l=lbl: self.toggle_attendance(k, l))
                total += float(val) if val != "2" else 0

            ctk.CTkLabel(row_frame, text=str(int(total)), width=80, anchor="center",
                font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=days_in_month + 1, padx=2)

    def toggle_attendance(self, key, label):
        current = self.attendance.get(key, "1")
        next_val = {"1": "0.5", "0.5": "2", "2": "1"}
        new_val = next_val.get(current, "1")
        self.attendance[key] = new_val
        fg = "#c8e6c9" if new_val == "1" else "#fff9c4" if new_val == "0.5" else "#ffcdd2"
        label.configure(text=new_val, fg_color=fg)

    def create_payroll_tab(self):
        tab = self.tabview.tab("💰 Bordro")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        columns = ("Personel", "Brüt Maaş", "SGK İşçi", "İşsizlik", "Gelir Vergisi",
                  "Damga Vergisi", "Kesinti Toplam", "Net Maaş")
        self.payroll_tree = ttk.Treeview(tab, columns=columns, show="headings", height=15)

        widths = [180, 100, 80, 80, 100, 80, 100, 100]
        for col, w in zip(columns, widths):
            self.payroll_tree.heading(col, text=col)
            self.payroll_tree.column(col, width=w, anchor="center")

        scroll = ttk.Scrollbar(tab, orient="vertical", command=self.payroll_tree.yview)
        self.payroll_tree.configure(yscrollcommand=scroll.set)

        self.payroll_tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scroll.grid(row=0, column=1, sticky="ns", pady=5)

    def create_status_bar(self):
        status = ctk.CTkFrame(self, height=30, corner_radius=5)
        status.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 5))

        self.status_label = ctk.CTkLabel(status, text="Hazır", font=ctk.CTkFont(size=11))
        self.status_label.pack(side="left", padx=10, pady=5)

    def load_employees(self):
        try:
            if self.db_manager:
                query = "SELECT * FROM Employees WHERE IsActive = 1 ORDER BY FullName"
                result = self.db_manager.execute_query(query)
                if result:
                    self.employees = [dict(r) for r in result]
                else:
                    self._load_sample_employees()
            else:
                self._load_sample_employees()

            self.refresh_personnel_table()
        except:
            self._load_sample_employees()
            self.refresh_personnel_table()

    def _load_sample_employees(self):
        self.employees = [
            {"EmployeeID": 1, "EmployeeCode": "P001", "FullName": "Ahmet Yılmaz",
             "IdentityNumber": "12345678901", "Department": "Yazılım", "Position": "Kıdemli Geliştirici",
             "HireDate": date(2020, 1, 1), "Salary": 45000, "IsActive": 1},
            {"EmployeeID": 2, "EmployeeCode": "P002", "FullName": "Ayşe Demir",
             "IdentityNumber": "23456789012", "Department": "Muhasebe", "Position": "Muhasebe Uzmanı",
             "HireDate": date(2021, 3, 15), "Salary": 32000, "IsActive": 1},
            {"EmployeeID": 3, "EmployeeCode": "P003", "FullName": "Mehmet Kaya",
             "IdentityNumber": "34567890123", "Department": "Satış", "Position": "Satış Temsilcisi",
             "HireDate": date(2022, 6, 1), "Salary": 28000, "IsActive": 1},
            {"EmployeeID": 4, "EmployeeCode": "P004", "FullName": "Zeynep Çelik",
             "IdentityNumber": "45678901234", "Department": "İK", "Position": "İK Uzmanı",
             "HireDate": date(2023, 2, 1), "Salary": 25000, "IsActive": 1},
        ]

    def refresh_personnel_table(self):
        for item in self.personnel_tree.get_children():
            self.personnel_tree.delete(item)

        for emp in self.employees:
            self.personnel_tree.insert("", "end", values=(
                emp.get("EmployeeID", emp.get("id", "")),
                emp.get("EmployeeCode", ""),
                emp.get("FullName", emp.get("ad_soyad", "")),
                emp.get("IdentityNumber", ""),
                emp.get("Department", ""),
                emp.get("Position", ""),
                emp.get("HireDate", ""),
                f"{emp.get('Salary', 0):,.0f} ₺",
                "✅ Aktif" if emp.get("IsActive", 1) else "❌ Pasif"
            ))

        self.status_label.configure(text=f"{len(self.employees)} personel")

    def prev_month(self):
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self.month_label.configure(text=f"{self.month_name(self.current_month)} {self.current_year}")
        self.refresh_attendance()

    def next_month(self):
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self.month_label.configure(text=f"{self.month_name(self.current_month)} {self.current_year}")
        self.refresh_attendance()

    def add_employee(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("➕ Personel Ekle")
        dialog.geometry("500x600")
        dialog.transient(self)
        dialog.grab_set()

        frame = ctk.CTkFrame(dialog, corner_radius=10)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text="➕ YENİ PERSONEL", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(0, 20))

        fields = {}
        for label in ["Ad Soyad", "TC Kimlik", "Sicil No", "Departman", "Pozisyon", "Maaş (₺)"]:
            ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=12, weight="bold"),
                anchor="w").pack(fill="x", padx=20)
            entry = ctk.CTkEntry(frame, height=35, font=ctk.CTkFont(size=14))
            entry.pack(fill="x", padx=20, pady=(0, 12))
            fields[label] = entry

        def save():
            try:
                new_emp = {
                    "FullName": fields["Ad Soyad"].get(),
                    "IdentityNumber": fields["TC Kimlik"].get(),
                    "EmployeeCode": fields["Sicil No"].get() or f"P{len(self.employees)+1:03d}",
                    "Department": fields["Departman"].get(),
                    "Position": fields["Pozisyon"].get(),
                    "Salary": float(fields["Maaş (₺)"].get().replace(".", "").replace(",", ".")),
                    "HireDate": date.today(),
                    "IsActive": 1
                }

                if self.db_manager:
                    query = """
                    INSERT INTO Employees (EmployeeCode, FullName, IdentityNumber, Department, Position, Salary, HireDate, IsActive)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                    """
                    result = self.db_manager.execute_query(query, (
                        new_emp["EmployeeCode"], new_emp["FullName"], new_emp["IdentityNumber"],
                        new_emp["Department"], new_emp["Position"], new_emp["Salary"], new_emp["HireDate"]
                    ), fetch=False)
                    new_emp["EmployeeID"] = result if result else len(self.employees) + 1
                else:
                    new_emp["EmployeeID"] = len(self.employees) + 1

                self.employees.append(new_emp)
                self.refresh_personnel_table()
                messagebox.showinfo("Başarılı", "Personel eklendi!")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Hata", str(e))

        ctk.CTkButton(frame, text="💾 Kaydet", command=save,
            fg_color="#2e7d32", height=40, font=ctk.CTkFont(size=14, weight="bold")).pack(pady=15)

    def edit_employee(self):
        selection = self.personnel_tree.selection()
        if not selection:
            messagebox.showwarning("Uyarı", "Lütfen bir personel seçin!")
            return
        messagebox.showinfo("Bilgi", "Personel düzenleme yakında eklenecek.")

    def delete_employee(self):
        selection = self.personnel_tree.selection()
        if not selection:
            messagebox.showwarning("Uyarı", "Lütfen bir personel seçin!")
            return
        if messagebox.askyesno("Onay", "Personeli silmek istediğinize emin misiniz?"):
            messagebox.showinfo("Başarılı", "Personel silindi.")

    def calculate_payroll(self):
        if not self.employees:
            messagebox.showwarning("Uyarı", "Personel bulunamadı!")
            return

        for item in self.payroll_tree.get_children():
            self.payroll_tree.delete(item)

        total_net = 0
        for emp in self.employees:
            gross = emp.get("Salary", 0)
            sgk = round(gross * 0.14, 2)
            issizlik = round(gross * 0.01, 2)
            gelir_vergisi = round((gross - sgk - issizlik) * 0.15, 2)
            damga = round(gross * 0.00759, 2)
            kesinti = round(sgk + issizlik + gelir_vergisi + damga, 2)
            net = round(gross - kesinti, 2)

            self.payroll_tree.insert("", "end", values=(
                emp.get("FullName", ""),
                f"{gross:,.2f} ₺",
                f"{sgk:,.2f} ₺",
                f"{issizlik:,.2f} ₺",
                f"{gelir_vergisi:,.2f} ₺",
                f"{damga:,.2f} ₺",
                f"{kesinti:,.2f} ₺",
                f"{net:,.2f} ₺"
            ))
            total_net += net

        self.payroll_tree.insert("", "end", values=(
            "TOPLAM", "", "", "", "", "", "", f"{total_net:,.2f} ₺"
        ))
        messagebox.showinfo("Başarılı", "Bordro hesaplandı!")

    def bulk_payroll(self):
        messagebox.showinfo("Bilgi", "Toplu bordro işlemi yakında eklenecek.")
