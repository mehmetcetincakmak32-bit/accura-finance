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
TEXT_DARK = "#1a1a2e"
TEXT_MUTED = "#6c757d"
BORDER = "#e8eaed"


class InventoryFrame(ctk.CTkFrame):
    def __init__(self, parent, main_app):
        super().__init__(parent)
        self.main_app = main_app
        self.db_manager = main_app.db_manager
        self.use_db = False
        self.stock_items = []
        self.stock_categories = []
        self.stock_movements = []
        self.next_stock_id = 1
        self.next_category_id = 1
        self.next_movement_id = 1

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
            header, text="STOK YONETIMI",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=PRIMARY_DARK
        ).pack(side="left", padx=20, pady=15)
        ctk.CTkLabel(
            header, text="Stok Kartlari - Kategoriler - Stok Hareketleri",
            font=ctk.CTkFont(size=12), text_color=TEXT_MUTED
        ).pack(side="left", padx=5, pady=15)

    def create_tabs(self):
        self.tabview = ctk.CTkTabview(self, corner_radius=10, fg_color="#ffffff")
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 10))
        self.tabview._segmented_button.configure(font=ctk.CTkFont(size=13, weight="bold"))

        self.tabview.add("Stok Kartlari")
        self.tabview.add("Kategoriler")
        self.tabview.add("Stok Hareketleri")

        self.create_stock_cards_tab()
        self.create_categories_tab()
        self.create_movements_tab()

    def load_initial_data(self):
        if self.db_manager:
            self.check_and_create_tables()
        if not self.use_db:
            self.load_sample_data()

    def check_and_create_tables(self):
        try:
            self.db_manager.execute_query(
                "CREATE TABLE IF NOT EXISTS StockCategories ("
                "CategoryID INTEGER PRIMARY KEY AUTOINCREMENT, "
                "CategoryCode TEXT UNIQUE NOT NULL, "
                "CategoryName TEXT NOT NULL, "
                "ParentCategoryID INTEGER, "
                "Description TEXT, "
                "IsActive INTEGER DEFAULT 1)",
                fetch=False
            )
            self.db_manager.execute_query(
                "CREATE TABLE IF NOT EXISTS StockItems ("
                "StockID INTEGER PRIMARY KEY AUTOINCREMENT, "
                "StockCode TEXT UNIQUE NOT NULL, "
                "StockName TEXT NOT NULL, "
                "CategoryID INTEGER, "
                "Unit TEXT DEFAULT 'Adet', "
                "Barcode TEXT, "
                "PurchasePrice REAL DEFAULT 0, "
                "SalePrice REAL DEFAULT 0, "
                "VATRate REAL DEFAULT 18, "
                "MinStockLevel REAL DEFAULT 0, "
                "CurrentStock REAL DEFAULT 0, "
                "IsActive INTEGER DEFAULT 1, "
                "CreatedDate TEXT DEFAULT (datetime('now','localtime')), "
                "FOREIGN KEY (CategoryID) REFERENCES StockCategories(CategoryID))",
                fetch=False
            )
            self.db_manager.execute_query(
                "CREATE TABLE IF NOT EXISTS StockMovements ("
                "MovementID INTEGER PRIMARY KEY AUTOINCREMENT, "
                "StockID INTEGER NOT NULL, "
                "MovementDate TEXT NOT NULL, "
                "MovementType TEXT NOT NULL, "
                "Quantity REAL NOT NULL, "
                "UnitPrice REAL DEFAULT 0, "
                "TotalAmount REAL DEFAULT 0, "
                "Description TEXT, "
                "CreatedDate TEXT DEFAULT (datetime('now','localtime')), "
                "FOREIGN KEY (StockID) REFERENCES StockItems(StockID))",
                fetch=False
            )
            self.use_db = True
            self.load_stock_from_db()
            self.load_categories_from_db()
            self.load_movements_from_db()
        except Exception:
            self.use_db = False

    def load_stock_from_db(self):
        try:
            result = self.db_manager.execute_query(
                "SELECT s.*, c.CategoryName FROM StockItems s "
                "LEFT JOIN StockCategories c ON s.CategoryID = c.CategoryID "
                "ORDER BY s.StockCode"
            )
            if result:
                self.stock_items = result
            else:
                self.load_sample_stock()
            self.refresh_stock_tree()
        except Exception:
            self.load_sample_stock()

    def load_categories_from_db(self):
        try:
            result = self.db_manager.execute_query(
                "SELECT c1.*, c2.CategoryName as ParentName FROM StockCategories c1 "
                "LEFT JOIN StockCategories c2 ON c1.ParentCategoryID = c2.CategoryID "
                "ORDER BY c1.CategoryCode"
            )
            if result:
                self.stock_categories = result
            else:
                self.load_sample_categories()
            self.refresh_category_tree()
        except Exception:
            self.load_sample_categories()

    def load_movements_from_db(self):
        try:
            result = self.db_manager.execute_query(
                "SELECT m.*, s.StockName, s.StockCode FROM StockMovements m "
                "LEFT JOIN StockItems s ON m.StockID = s.StockID "
                "ORDER BY m.MovementDate DESC"
            )
            if result:
                self.stock_movements = result
            else:
                self.load_sample_movements()
            self.refresh_movement_tree()
        except Exception:
            self.load_sample_movements()

    def load_sample_data(self):
        self.load_sample_categories()
        self.load_sample_stock()
        self.load_sample_movements()

    def load_sample_categories(self):
        self.stock_categories = [
            {"CategoryID": 1, "CategoryCode": "KAT001", "CategoryName": "Elektronik", "ParentCategoryID": None, "ParentName": None, "IsActive": 1},
            {"CategoryID": 2, "CategoryCode": "KAT002", "CategoryName": "Ofis Malzemeleri", "ParentCategoryID": None, "ParentName": None, "IsActive": 1},
            {"CategoryID": 3, "CategoryCode": "KAT003", "CategoryName": "Temel Gida", "ParentCategoryID": None, "ParentName": None, "IsActive": 1},
            {"CategoryID": 4, "CategoryCode": "KAT004", "CategoryName": "Laptop", "ParentCategoryID": 1, "ParentName": "Elektronik", "IsActive": 1},
            {"CategoryID": 5, "CategoryCode": "KAT005", "CategoryName": "Kirtasiye", "ParentCategoryID": 2, "ParentName": "Ofis Malzemeleri", "IsActive": 1},
        ]
        self.next_category_id = 6
        self.refresh_category_tree()

    def load_sample_stock(self):
        self.stock_items = [
            {"StockID": 1, "StockCode": "STK001", "StockName": "Dizustu Bilgisayar", "CategoryID": 4, "CategoryName": "Laptop", "Unit": "Adet", "Barcode": "8691234567890", "PurchasePrice": 15000, "SalePrice": 22000, "VATRate": 18, "MinStockLevel": 5, "CurrentStock": 12, "IsActive": 1},
            {"StockID": 2, "StockCode": "STK002", "StockName": "Fotokopi Kagit A4", "CategoryID": 5, "CategoryName": "Kirtasiye", "Unit": "Adet", "Barcode": "8692345678901", "PurchasePrice": 80, "SalePrice": 120, "VATRate": 18, "MinStockLevel": 100, "CurrentStock": 350, "IsActive": 1},
            {"StockID": 3, "StockCode": "STK003", "StockName": "Zeytinyagi 1L", "CategoryID": 3, "CategoryName": "Temel Gida", "Unit": "Lt", "Barcode": "8693456789012", "PurchasePrice": 180, "SalePrice": 250, "VATRate": 8, "MinStockLevel": 30, "CurrentStock": 25, "IsActive": 1},
            {"StockID": 4, "StockCode": "STK004", "StockName": "Pirinç 5Kg", "CategoryID": 3, "CategoryName": "Temel Gida", "Unit": "Kg", "Barcode": "8694567890123", "PurchasePrice": 120, "SalePrice": 175, "VATRate": 8, "MinStockLevel": 20, "CurrentStock": 40, "IsActive": 1},
        ]
        self.next_stock_id = 5
        self.refresh_stock_tree()

    def load_sample_movements(self):
        self.stock_movements = [
            {"MovementID": 1, "StockID": 1, "StockCode": "STK001", "StockName": "Dizustu Bilgisayar", "MovementDate": "2025-01-10", "MovementType": "Giris", "Quantity": 10, "UnitPrice": 15000, "TotalAmount": 150000, "Description": "Tedarikciden alis"},
            {"MovementID": 2, "StockID": 1, "StockCode": "STK001", "StockName": "Dizustu Bilgisayar", "MovementDate": "2025-01-15", "MovementType": "Cikis", "Quantity": 3, "UnitPrice": 22000, "TotalAmount": 66000, "Description": "Musteri satisi"},
            {"MovementID": 3, "StockID": 3, "StockCode": "STK003", "StockName": "Zeytinyagi 1L", "MovementDate": "2025-01-12", "MovementType": "Giris", "Quantity": 50, "UnitPrice": 180, "TotalAmount": 9000, "Description": "Tedarikciden alis"},
            {"MovementID": 4, "StockID": 3, "StockCode": "STK003", "StockName": "Zeytinyagi 1L", "MovementDate": "2025-01-18", "MovementType": "Cikis", "Quantity": 25, "UnitPrice": 250, "TotalAmount": 6250, "Description": "Musteri satisi"},
        ]
        self.next_movement_id = 5
        self.refresh_movement_tree()

    # =====================================================================
    # TAB 1: STOK KARTLARI
    # =====================================================================
    def create_stock_cards_tab(self):
        tab = self.tabview.tab("Stok Kartlari")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        toolbar = ctk.CTkFrame(tab, fg_color="transparent", height=44)
        toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))

        ctk.CTkButton(toolbar, text="Stok Ekle", command=self.add_stock_dialog,
                       fg_color=SUCCESS, hover_color="#1b5e20", height=34,
                       corner_radius=8, font=ctk.CTkFont(size=12, weight="bold")
                       ).pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text="Duzenle", command=self.edit_stock_dialog,
                       fg_color=PRIMARY, hover_color=PRIMARY_DARK, height=34,
                       corner_radius=8, font=ctk.CTkFont(size=12, weight="bold")
                       ).pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text="Sil", command=self.delete_stock_item,
                       fg_color=DANGER, hover_color="#b71c1c", height=34,
                       corner_radius=8, font=ctk.CTkFont(size=12, weight="bold")
                       ).pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text="Yenile", command=self.refresh_stock_tree,
                       fg_color=TEXT_MUTED, hover_color="#5a6268", height=34,
                       corner_radius=8, font=ctk.CTkFont(size=12, weight="bold")
                       ).pack(side="right", padx=4)

        content = ctk.CTkFrame(tab, corner_radius=10, fg_color="#ffffff",
                                border_width=1, border_color=BORDER)
        content.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 10))
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)

        columns = ("Stok Kodu", "Stok Adi", "Kategori", "Birim", "Alis Fiyat", "Satis Fiyat", "Mevcut Stok")
        self.stock_tree = ttk.Treeview(content, columns=columns, show="headings", height=20, selectmode="browse")
        widths = [100, 200, 120, 70, 110, 110, 110]
        for col, w in zip(columns, widths):
            self.stock_tree.heading(col, text=col)
            self.stock_tree.column(col, width=w, anchor="center")

        scroll = ttk.Scrollbar(content, orient="vertical", command=self.stock_tree.yview)
        self.stock_tree.configure(yscrollcommand=scroll.set)
        self.stock_tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scroll.grid(row=0, column=1, sticky="ns", pady=5)

    def refresh_stock_tree(self):
        for item in self.stock_tree.get_children():
            self.stock_tree.delete(item)
        for s in self.stock_items:
            self.stock_tree.insert("", "end", iid=str(s.get("StockID")), values=(
                s.get("StockCode", ""),
                s.get("StockName", ""),
                s.get("CategoryName", s.get("CategoryName", "")),
                s.get("Unit", ""),
                f"{s.get('PurchasePrice', 0):,.2f}",
                f"{s.get('SalePrice', 0):,.2f}",
                f"{s.get('CurrentStock', 0):.2f}"
            ))

    def add_stock_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Stok Ekle")
        dialog.geometry("520x540")
        dialog.transient(self)
        dialog.grab_set()

        frame = ctk.CTkFrame(dialog, corner_radius=10, fg_color="#ffffff")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text="YENI STOK KARTI",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=PRIMARY_DARK).pack(pady=(0, 20))

        form = ctk.CTkFrame(frame, fg_color="transparent")
        form.pack(fill="x", padx=10)
        form.grid_columnconfigure(1, weight=1)

        fields = {}
        row_labels = ["Stok Kodu", "Stok Adi", "Barkod", "Alis Fiyat", "Satis Fiyat", "KDV Oran", "Min Stok"]
        self._build_form_fields(form, row_labels, fields, 0)

        ctk.CTkLabel(form, text="Kategori", font=ctk.CTkFont(size=12, weight="bold"),
                     anchor="w").grid(row=7, column=0, sticky="w", padx=10, pady=4)
        cat_values = [f"{c['CategoryCode']} - {c['CategoryName']}" for c in self.stock_categories]
        cat_combo = ctk.CTkComboBox(form, values=cat_values, height=35,
                                     font=ctk.CTkFont(size=14), state="readonly")
        cat_combo.grid(row=7, column=1, sticky="ew", padx=10, pady=4)

        ctk.CTkLabel(form, text="Birim", font=ctk.CTkFont(size=12, weight="bold"),
                     anchor="w").grid(row=8, column=0, sticky="w", padx=10, pady=4)
        unit_combo = ctk.CTkComboBox(form, values=["Adet", "Kg", "Lt", "M", "M2", "Kutu", "Paket"],
                                      height=35, font=ctk.CTkFont(size=14), state="readonly")
        unit_combo.set("Adet")
        unit_combo.grid(row=8, column=1, sticky="ew", padx=10, pady=4)

        def save():
            code = fields["Stok Kodu"].get().strip()
            name = fields["Stok Adi"].get().strip()
            if not code or not name:
                messagebox.showwarning("Uyari", "Stok kodu ve adi zorunludur!")
                return
            try:
                cat_id = None
                cat_text = cat_combo.get()
                if cat_text:
                    for c in self.stock_categories:
                        if f"{c['CategoryCode']} - {c['CategoryName']}" == cat_text:
                            cat_id = c["CategoryID"]
                            break
                purchase = float(fields["Alis Fiyat"].get().replace(",", ".") or 0)
                sale = float(fields["Satis Fiyat"].get().replace(",", ".") or 0)
                vat = float(fields["KDV Oran"].get().replace(",", ".") or 18)
                min_stock = float(fields["Min Stok"].get().replace(",", ".") or 0)
                if self.use_db:
                    self.db_manager.execute_query(
                        "INSERT INTO StockItems (StockCode, StockName, CategoryID, Unit, Barcode, "
                        "PurchasePrice, SalePrice, VATRate, MinStockLevel, CurrentStock) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)",
                        (code, name, cat_id, unit_combo.get(), fields["Barkod"].get(),
                         purchase, sale, vat, min_stock), fetch=False
                    )
                    self.load_stock_from_db()
                else:
                    new_id = max(s.get("StockID", 0) for s in self.stock_items) + 1
                    cat_name = ""
                    for c in self.stock_categories:
                        if c["CategoryID"] == cat_id:
                            cat_name = c["CategoryName"]
                            break
                    self.stock_items.append({
                        "StockID": new_id, "StockCode": code, "StockName": name,
                        "CategoryID": cat_id, "CategoryName": cat_name,
                        "Unit": unit_combo.get(), "Barcode": fields["Barkod"].get(),
                        "PurchasePrice": purchase, "SalePrice": sale,
                        "VATRate": vat, "MinStockLevel": min_stock, "CurrentStock": 0, "IsActive": 1
                    })
                    self.refresh_stock_tree()
                messagebox.showinfo("Basarili", "Stok kart eklendi!")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Hata", str(e))

        ctk.CTkButton(frame, text="Kaydet", command=save,
                       fg_color=SUCCESS, height=40,
                       font=ctk.CTkFont(size=14, weight="bold")).pack(pady=15)

    def edit_stock_dialog(self):
        sel = self.stock_tree.selection()
        if not sel:
            messagebox.showwarning("Uyari", "Lutfen bir stok secin!")
            return
        sid = int(sel[0])
        item = next((s for s in self.stock_items if s.get("StockID") == sid), None)
        if not item:
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Stok Duzenle")
        dialog.geometry("520x540")
        dialog.transient(self)
        dialog.grab_set()

        frame = ctk.CTkFrame(dialog, corner_radius=10, fg_color="#ffffff")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text="STOK KARTI DUZENLE",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=PRIMARY_DARK).pack(pady=(0, 20))

        form = ctk.CTkFrame(frame, fg_color="transparent")
        form.pack(fill="x", padx=10)
        form.grid_columnconfigure(1, weight=1)

        fields = {}
        row_labels = ["Stok Kodu", "Stok Adi", "Barkod", "Alis Fiyat", "Satis Fiyat", "KDV Oran", "Min Stok"]
        entries = self._build_form_fields(form, row_labels, fields, 0)

        entries[0].insert(0, item.get("StockCode", ""))
        entries[1].insert(0, item.get("StockName", ""))
        entries[2].insert(0, item.get("Barcode", ""))
        entries[3].insert(0, str(item.get("PurchasePrice", 0)))
        entries[4].insert(0, str(item.get("SalePrice", 0)))
        entries[5].insert(0, str(item.get("VATRate", 18)))
        entries[6].insert(0, str(item.get("MinStockLevel", 0)))

        ctk.CTkLabel(form, text="Kategori", font=ctk.CTkFont(size=12, weight="bold"),
                     anchor="w").grid(row=7, column=0, sticky="w", padx=10, pady=4)
        cat_values = [f"{c['CategoryCode']} - {c['CategoryName']}" for c in self.stock_categories]
        cat_combo = ctk.CTkComboBox(form, values=cat_values, height=35,
                                     font=ctk.CTkFont(size=14), state="readonly")
        for c in self.stock_categories:
            if c["CategoryID"] == item.get("CategoryID"):
                cat_combo.set(f"{c['CategoryCode']} - {c['CategoryName']}")
                break
        cat_combo.grid(row=7, column=1, sticky="ew", padx=10, pady=4)

        ctk.CTkLabel(form, text="Birim", font=ctk.CTkFont(size=12, weight="bold"),
                     anchor="w").grid(row=8, column=0, sticky="w", padx=10, pady=4)
        unit_combo = ctk.CTkComboBox(form, values=["Adet", "Kg", "Lt", "M", "M2", "Kutu", "Paket"],
                                      height=35, font=ctk.CTkFont(size=14), state="readonly")
        unit_combo.set(item.get("Unit", "Adet"))
        unit_combo.grid(row=8, column=1, sticky="ew", padx=10, pady=4)

        def save():
            code = fields["Stok Kodu"].get().strip()
            name = fields["Stok Adi"].get().strip()
            if not code or not name:
                messagebox.showwarning("Uyari", "Stok kodu ve adi zorunludur!")
                return
            try:
                cat_id = None
                cat_text = cat_combo.get()
                if cat_text:
                    for c in self.stock_categories:
                        if f"{c['CategoryCode']} - {c['CategoryName']}" == cat_text:
                            cat_id = c["CategoryID"]
                            break
                purchase = float(fields["Alis Fiyat"].get().replace(",", ".") or 0)
                sale = float(fields["Satis Fiyat"].get().replace(",", ".") or 0)
                vat = float(fields["KDV Oran"].get().replace(",", ".") or 18)
                min_stock = float(fields["Min Stok"].get().replace(",", ".") or 0)
                if self.use_db:
                    self.db_manager.execute_query(
                        "UPDATE StockItems SET StockCode=?, StockName=?, CategoryID=?, Unit=?, Barcode=?, "
                        "PurchasePrice=?, SalePrice=?, VATRate=?, MinStockLevel=? WHERE StockID=?",
                        (code, name, cat_id, unit_combo.get(), fields["Barkod"].get(),
                         purchase, sale, vat, min_stock, sid), fetch=False
                    )
                    self.load_stock_from_db()
                else:
                    for s in self.stock_items:
                        if s["StockID"] == sid:
                            cat_name = ""
                            for c in self.stock_categories:
                                if c["CategoryID"] == cat_id:
                                    cat_name = c["CategoryName"]
                                    break
                            s.update({
                                "StockCode": code, "StockName": name,
                                "CategoryID": cat_id, "CategoryName": cat_name,
                                "Unit": unit_combo.get(), "Barcode": fields["Barkod"].get(),
                                "PurchasePrice": purchase, "SalePrice": sale,
                                "VATRate": vat, "MinStockLevel": min_stock
                            })
                            break
                    self.refresh_stock_tree()
                messagebox.showinfo("Basarili", "Stok kart guncellendi!")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Hata", str(e))

        ctk.CTkButton(frame, text="Kaydet", command=save,
                       fg_color=PRIMARY, height=40,
                       font=ctk.CTkFont(size=14, weight="bold")).pack(pady=15)

    def _build_form_fields(self, parent, labels, fields_dict, start_row):
        entries = []
        for i, label in enumerate(labels):
            row = start_row + i
            ctk.CTkLabel(parent, text=label, font=ctk.CTkFont(size=12, weight="bold"),
                         anchor="w").grid(row=row, column=0, sticky="w", padx=10, pady=4)
            e = ctk.CTkEntry(parent, height=35, font=ctk.CTkFont(size=14))
            e.grid(row=row, column=1, sticky="ew", padx=10, pady=4)
            fields_dict[label] = e
            entries.append(e)
        return entries

    def delete_stock_item(self):
        sel = self.stock_tree.selection()
        if not sel:
            messagebox.showwarning("Uyari", "Lutfen bir stok secin!")
            return
        sid = int(sel[0])
        item = next((s for s in self.stock_items if s.get("StockID") == sid), None)
        if not item:
            return
        if not messagebox.askyesno("Onay", f"{item['StockCode']} - {item['StockName']}\nsilinecek. Emin misiniz?"):
            return
        try:
            if self.use_db:
                self.db_manager.execute_query("DELETE FROM StockItems WHERE StockID=?", (sid,), fetch=False)
                self.load_stock_from_db()
            else:
                self.stock_items = [s for s in self.stock_items if s.get("StockID") != sid]
                self.refresh_stock_tree()
            messagebox.showinfo("Basarili", "Stok silindi!")
        except Exception as e:
            messagebox.showerror("Hata", str(e))

    # =====================================================================
    # TAB 2: KATEGORILER
    # =====================================================================
    def create_categories_tab(self):
        tab = self.tabview.tab("Kategoriler")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        toolbar = ctk.CTkFrame(tab, fg_color="transparent", height=44)
        toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))

        ctk.CTkButton(toolbar, text="Kategori Ekle", command=self.add_category_dialog,
                       fg_color=SUCCESS, hover_color="#1b5e20", height=34,
                       corner_radius=8, font=ctk.CTkFont(size=12, weight="bold")
                       ).pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text="Duzenle", command=self.edit_category_dialog,
                       fg_color=PRIMARY, hover_color=PRIMARY_DARK, height=34,
                       corner_radius=8, font=ctk.CTkFont(size=12, weight="bold")
                       ).pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text="Sil", command=self.delete_category,
                       fg_color=DANGER, hover_color="#b71c1c", height=34,
                       corner_radius=8, font=ctk.CTkFont(size=12, weight="bold")
                       ).pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text="Yenile", command=self.refresh_category_tree,
                       fg_color=TEXT_MUTED, hover_color="#5a6268", height=34,
                       corner_radius=8, font=ctk.CTkFont(size=12, weight="bold")
                       ).pack(side="right", padx=4)

        content = ctk.CTkFrame(tab, corner_radius=10, fg_color="#ffffff",
                                border_width=1, border_color=BORDER)
        content.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 10))
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)

        columns = ("Kod", "Kategori Adi", "Ust Kategori")
        self.category_tree = ttk.Treeview(content, columns=columns, show="headings", height=20, selectmode="browse")
        widths_c = [100, 250, 200]
        for col, w in zip(columns, widths_c):
            self.category_tree.heading(col, text=col)
            self.category_tree.column(col, width=w, anchor="center")

        scroll = ttk.Scrollbar(content, orient="vertical", command=self.category_tree.yview)
        self.category_tree.configure(yscrollcommand=scroll.set)
        self.category_tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scroll.grid(row=0, column=1, sticky="ns", pady=5)

    def refresh_category_tree(self):
        for item in self.category_tree.get_children():
            self.category_tree.delete(item)
        for c in self.stock_categories:
            parent_name = c.get("ParentName", "")
            if not parent_name and c.get("ParentCategoryID"):
                for p in self.stock_categories:
                    if p["CategoryID"] == c["ParentCategoryID"]:
                        parent_name = p["CategoryName"]
                        break
            self.category_tree.insert("", "end", iid=str(c["CategoryID"]), values=(
                c.get("CategoryCode", ""),
                c.get("CategoryName", ""),
                parent_name if parent_name else "-"
            ))

    def add_category_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Kategori Ekle")
        dialog.geometry("400x280")
        dialog.transient(self)
        dialog.grab_set()

        frame = ctk.CTkFrame(dialog, corner_radius=10, fg_color="#ffffff")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text="YENI KATEGORI",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=PRIMARY_DARK).pack(pady=(0, 20))

        ctk.CTkLabel(frame, text="Kategori Kodu", font=ctk.CTkFont(size=12, weight="bold"),
                     anchor="w").pack(fill="x", padx=20)
        code_entry = ctk.CTkEntry(frame, height=35, font=ctk.CTkFont(size=14))
        code_entry.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(frame, text="Kategori Adi", font=ctk.CTkFont(size=12, weight="bold"),
                     anchor="w").pack(fill="x", padx=20)
        name_entry = ctk.CTkEntry(frame, height=35, font=ctk.CTkFont(size=14))
        name_entry.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(frame, text="Ust Kategori", font=ctk.CTkFont(size=12, weight="bold"),
                     anchor="w").pack(fill="x", padx=20)
        parent_values = [""] + [f"{c['CategoryCode']} - {c['CategoryName']}" for c in self.stock_categories]
        parent_combo = ctk.CTkComboBox(frame, values=parent_values, height=35,
                                        font=ctk.CTkFont(size=14), state="readonly")
        parent_combo.set("")
        parent_combo.pack(fill="x", padx=20, pady=(0, 15))

        def save():
            code = code_entry.get().strip()
            name = name_entry.get().strip()
            if not code or not name:
                messagebox.showwarning("Uyari", "Kod ve ad zorunludur!")
                return
            parent_id = None
            parent_text = parent_combo.get()
            if parent_text:
                for c in self.stock_categories:
                    if f"{c['CategoryCode']} - {c['CategoryName']}" == parent_text:
                        parent_id = c["CategoryID"]
                        break
            try:
                if self.use_db:
                    self.db_manager.execute_query(
                        "INSERT INTO StockCategories (CategoryCode, CategoryName, ParentCategoryID) VALUES (?, ?, ?)",
                        (code, name, parent_id), fetch=False
                    )
                    self.load_categories_from_db()
                else:
                    new_id = max(c.get("CategoryID", 0) for c in self.stock_categories) + 1
                    parent_name = ""
                    for c in self.stock_categories:
                        if c["CategoryID"] == parent_id:
                            parent_name = c["CategoryName"]
                            break
                    self.stock_categories.append({
                        "CategoryID": new_id, "CategoryCode": code, "CategoryName": name,
                        "ParentCategoryID": parent_id, "ParentName": parent_name, "IsActive": 1
                    })
                    self.refresh_category_tree()
                messagebox.showinfo("Basarili", "Kategori eklendi!")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Hata", str(e))

        ctk.CTkButton(frame, text="Kaydet", command=save,
                       fg_color=SUCCESS, height=40,
                       font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)

    def edit_category_dialog(self):
        sel = self.category_tree.selection()
        if not sel:
            messagebox.showwarning("Uyari", "Lutfen bir kategori secin!")
            return
        cid = int(sel[0])
        cat = next((c for c in self.stock_categories if c.get("CategoryID") == cid), None)
        if not cat:
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Kategori Duzenle")
        dialog.geometry("400x280")
        dialog.transient(self)
        dialog.grab_set()

        frame = ctk.CTkFrame(dialog, corner_radius=10, fg_color="#ffffff")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text="KATEGORI DUZENLE",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=PRIMARY_DARK).pack(pady=(0, 20))

        ctk.CTkLabel(frame, text="Kategori Kodu", font=ctk.CTkFont(size=12, weight="bold"),
                     anchor="w").pack(fill="x", padx=20)
        code_entry = ctk.CTkEntry(frame, height=35, font=ctk.CTkFont(size=14))
        code_entry.insert(0, cat.get("CategoryCode", ""))
        code_entry.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(frame, text="Kategori Adi", font=ctk.CTkFont(size=12, weight="bold"),
                     anchor="w").pack(fill="x", padx=20)
        name_entry = ctk.CTkEntry(frame, height=35, font=ctk.CTkFont(size=14))
        name_entry.insert(0, cat.get("CategoryName", ""))
        name_entry.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(frame, text="Ust Kategori", font=ctk.CTkFont(size=12, weight="bold"),
                     anchor="w").pack(fill="x", padx=20)
        parent_values = [""] + [f"{c['CategoryCode']} - {c['CategoryName']}" for c in self.stock_categories if c["CategoryID"] != cid]
        parent_combo = ctk.CTkComboBox(frame, values=parent_values, height=35,
                                        font=ctk.CTkFont(size=14), state="readonly")
        if cat.get("ParentCategoryID"):
            for c in self.stock_categories:
                if c["CategoryID"] == cat["ParentCategoryID"]:
                    parent_combo.set(f"{c['CategoryCode']} - {c['CategoryName']}")
                    break
        else:
            parent_combo.set("")
        parent_combo.pack(fill="x", padx=20, pady=(0, 15))

        def save():
            code = code_entry.get().strip()
            name = name_entry.get().strip()
            if not code or not name:
                messagebox.showwarning("Uyari", "Kod ve ad zorunludur!")
                return
            parent_id = None
            parent_text = parent_combo.get()
            if parent_text:
                for c in self.stock_categories:
                    if f"{c['CategoryCode']} - {c['CategoryName']}" == parent_text:
                        parent_id = c["CategoryID"]
                        break
            try:
                if self.use_db:
                    self.db_manager.execute_query(
                        "UPDATE StockCategories SET CategoryCode=?, CategoryName=?, ParentCategoryID=? WHERE CategoryID=?",
                        (code, name, parent_id, cid), fetch=False
                    )
                    self.load_categories_from_db()
                else:
                    for c in self.stock_categories:
                        if c["CategoryID"] == cid:
                            parent_name = ""
                            for pc in self.stock_categories:
                                if pc["CategoryID"] == parent_id:
                                    parent_name = pc["CategoryName"]
                                    break
                            c.update({"CategoryCode": code, "CategoryName": name,
                                      "ParentCategoryID": parent_id, "ParentName": parent_name})
                            break
                    self.refresh_category_tree()
                messagebox.showinfo("Basarili", "Kategori guncellendi!")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Hata", str(e))

        ctk.CTkButton(frame, text="Kaydet", command=save,
                       fg_color=PRIMARY, height=40,
                       font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)

    def delete_category(self):
        sel = self.category_tree.selection()
        if not sel:
            messagebox.showwarning("Uyari", "Lutfen bir kategori secin!")
            return
        cid = int(sel[0])
        cat = next((c for c in self.stock_categories if c.get("CategoryID") == cid), None)
        if not cat:
            return
        if not messagebox.askyesno("Onay", f"{cat['CategoryName']} kategorisi silinecek. Emin misiniz?"):
            return
        try:
            if self.use_db:
                self.db_manager.execute_query("DELETE FROM StockCategories WHERE CategoryID=?", (cid,), fetch=False)
                self.load_categories_from_db()
            else:
                self.stock_categories = [c for c in self.stock_categories if c.get("CategoryID") != cid]
                self.refresh_category_tree()
            messagebox.showinfo("Basarili", "Kategori silindi!")
        except Exception as e:
            messagebox.showerror("Hata", str(e))

    # =====================================================================
    # TAB 3: STOK HAREKETLERI
    # =====================================================================
    def create_movements_tab(self):
        tab = self.tabview.tab("Stok Hareketleri")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)

        top = ctk.CTkFrame(tab, corner_radius=10, fg_color="#ffffff",
                            border_width=1, border_color=BORDER)
        top.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        top.grid_columnconfigure((1, 3), weight=1)

        ctk.CTkLabel(top, text="STOK HAREKETLERI",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=PRIMARY_DARK).grid(row=0, column=0, columnspan=6,
                                                   sticky="w", padx=16, pady=(12, 4))

        ctk.CTkLabel(top, text="Stok:", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=TEXT_DARK).grid(row=1, column=0, sticky="w", padx=16, pady=8)
        self.movement_stock_var = ctk.StringVar()
        stock_values = [f"{s['StockCode']} - {s['StockName']}" for s in self.stock_items]
        self.movement_stock_combo = ctk.CTkComboBox(top, variable=self.movement_stock_var,
                                                     values=stock_values, height=34, width=250,
                                                     font=ctk.CTkFont(size=13), state="readonly")
        self.movement_stock_combo.grid(row=1, column=1, sticky="w", padx=5, pady=8)

        ctk.CTkLabel(top, text="Baslangic:", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=TEXT_DARK).grid(row=1, column=2, sticky="w", padx=(20, 0), pady=8)
        self.movement_start_entry = ctk.CTkEntry(top, height=32, width=120,
                                                  font=ctk.CTkFont(size=13))
        self.movement_start_entry.insert(0, f"01.01.{date.today().year}")
        self.movement_start_entry.grid(row=1, column=3, sticky="w", padx=5, pady=8)

        ctk.CTkLabel(top, text="Bitis:", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=TEXT_DARK).grid(row=1, column=4, sticky="w", padx=(10, 0), pady=8)
        self.movement_end_entry = ctk.CTkEntry(top, height=32, width=120,
                                                font=ctk.CTkFont(size=13))
        self.movement_end_entry.insert(0, date.today().strftime("%d.%m.%Y"))
        self.movement_end_entry.grid(row=1, column=5, sticky="w", padx=5, pady=8)

        btn_frame = ctk.CTkFrame(tab, fg_color="transparent", height=44)
        btn_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)

        ctk.CTkButton(btn_frame, text="Hareket Ekle", command=self.add_movement_dialog,
                       fg_color=SUCCESS, hover_color="#1b5e20", height=34,
                       corner_radius=8, font=ctk.CTkFont(size=12, weight="bold")
                       ).pack(side="left", padx=4)
        ctk.CTkButton(btn_frame, text="Filtrele", command=self.filter_movements,
                       fg_color=PRIMARY, hover_color=PRIMARY_DARK, height=34,
                       corner_radius=8, font=ctk.CTkFont(size=12, weight="bold")
                       ).pack(side="left", padx=4)
        ctk.CTkButton(btn_frame, text="Tumunu Goster", command=self.refresh_movement_tree,
                       fg_color=TEXT_MUTED, hover_color="#5a6268", height=34,
                       corner_radius=8, font=ctk.CTkFont(size=12, weight="bold")
                       ).pack(side="right", padx=4)

        content = ctk.CTkFrame(tab, corner_radius=10, fg_color="#ffffff",
                                border_width=1, border_color=BORDER)
        content.grid(row=2, column=0, sticky="nsew", padx=10, pady=(5, 10))
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)

        columns = ("Hareket No", "Tarih", "Tur", "Stok", "Miktar", "Birim Fiyat", "Toplam", "Aciklama")
        self.movement_tree = ttk.Treeview(content, columns=columns, show="headings", height=20, selectmode="browse")
        widths_m = [90, 110, 80, 180, 80, 110, 130, 200]
        for col, w in zip(columns, widths_m):
            self.movement_tree.heading(col, text=col)
            self.movement_tree.column(col, width=w, anchor="center")

        scroll = ttk.Scrollbar(content, orient="vertical", command=self.movement_tree.yview)
        self.movement_tree.configure(yscrollcommand=scroll.set)
        self.movement_tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scroll.grid(row=0, column=1, sticky="ns", pady=5)

    def refresh_movement_tree(self, movements=None):
        for item in self.movement_tree.get_children():
            self.movement_tree.delete(item)
        data = movements if movements is not None else self.stock_movements
        for m in data:
            stock_display = f"{m.get('StockCode', '')} - {m.get('StockName', '')}"
            self.movement_tree.insert("", "end", values=(
                m.get("MovementID", ""),
                str(m.get("MovementDate", ""))[:10],
                m.get("MovementType", ""),
                stock_display,
                f"{m.get('Quantity', 0):.2f}",
                f"{m.get('UnitPrice', 0):.2f}",
                f"{m.get('TotalAmount', 0):.2f}",
                m.get("Description", "")
            ))

    def filter_movements(self):
        start_str = self.movement_start_entry.get().strip()
        end_str = self.movement_end_entry.get().strip()
        stock_text = self.movement_stock_var.get()

        filtered = list(self.stock_movements)

        if stock_text:
            code = stock_text.split(" - ")[0]
            filtered = [m for m in filtered if m.get("StockCode") == code]

        def parse_date(s):
            for sep in [".", "-", "/"]:
                if sep in s:
                    parts = s.split(sep)
                    if len(parts) == 3:
                        return f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
            return s

        if start_str:
            sd = parse_date(start_str)
            filtered = [m for m in filtered if str(m.get("MovementDate", ""))[:10] >= sd]
        if end_str:
            ed = parse_date(end_str)
            filtered = [m for m in filtered if str(m.get("MovementDate", ""))[:10] <= ed]

        self.refresh_movement_tree(filtered)

    def add_movement_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Stok Hareketi Ekle")
        dialog.geometry("500x400")
        dialog.transient(self)
        dialog.grab_set()

        frame = ctk.CTkFrame(dialog, corner_radius=10, fg_color="#ffffff")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text="YENI STOK HAREKETI",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=PRIMARY_DARK).pack(pady=(0, 20))

        form = ctk.CTkFrame(frame, fg_color="transparent")
        form.pack(fill="x", padx=10)
        form.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(form, text="Stok", font=ctk.CTkFont(size=12, weight="bold"),
                     anchor="w").grid(row=0, column=0, sticky="w", padx=10, pady=4)
        stock_values = [f"{s['StockCode']} - {s['StockName']}" for s in self.stock_items]
        stock_combo = ctk.CTkComboBox(form, values=stock_values, height=35,
                                       font=ctk.CTkFont(size=14), state="readonly")
        stock_combo.grid(row=0, column=1, sticky="ew", padx=10, pady=4)

        ctk.CTkLabel(form, text="Tarih", font=ctk.CTkFont(size=12, weight="bold"),
                     anchor="w").grid(row=1, column=0, sticky="w", padx=10, pady=4)
        date_entry = ctk.CTkEntry(form, height=35, font=ctk.CTkFont(size=14))
        date_entry.insert(0, date.today().strftime("%d.%m.%Y"))
        date_entry.grid(row=1, column=1, sticky="ew", padx=10, pady=4)

        ctk.CTkLabel(form, text="Hareket Turu", font=ctk.CTkFont(size=12, weight="bold"),
                     anchor="w").grid(row=2, column=0, sticky="w", padx=10, pady=4)
        type_combo = ctk.CTkComboBox(form, values=["Giris", "Cikis"], height=35,
                                      font=ctk.CTkFont(size=14), state="readonly")
        type_combo.set("Giris")
        type_combo.grid(row=2, column=1, sticky="ew", padx=10, pady=4)

        ctk.CTkLabel(form, text="Miktar", font=ctk.CTkFont(size=12, weight="bold"),
                     anchor="w").grid(row=3, column=0, sticky="w", padx=10, pady=4)
        qty_entry = ctk.CTkEntry(form, height=35, font=ctk.CTkFont(size=14))
        qty_entry.grid(row=3, column=1, sticky="ew", padx=10, pady=4)

        ctk.CTkLabel(form, text="Birim Fiyat", font=ctk.CTkFont(size=12, weight="bold"),
                     anchor="w").grid(row=4, column=0, sticky="w", padx=10, pady=4)
        price_entry = ctk.CTkEntry(form, height=35, font=ctk.CTkFont(size=14))
        price_entry.grid(row=4, column=1, sticky="ew", padx=10, pady=4)

        ctk.CTkLabel(form, text="Aciklama", font=ctk.CTkFont(size=12, weight="bold"),
                     anchor="w").grid(row=5, column=0, sticky="w", padx=10, pady=4)
        desc_entry = ctk.CTkEntry(form, height=35, font=ctk.CTkFont(size=14))
        desc_entry.grid(row=5, column=1, sticky="ew", padx=10, pady=4)

        def save():
            stock_text = stock_combo.get()
            if not stock_text:
                messagebox.showwarning("Uyari", "Lutfen bir stok secin!")
                return
            try:
                qty = float(qty_entry.get().replace(",", ".") or 0)
                price = float(price_entry.get().replace(",", ".") or 0)
                if qty <= 0:
                    messagebox.showwarning("Uyari", "Miktar pozitif olmalidir!")
                    return
                total = qty * price
                mtype = type_combo.get()
                date_str = date_entry.get().strip()

                stock_id = None
                stock_code = stock_text.split(" - ")[0]
                for s in self.stock_items:
                    if s.get("StockCode") == stock_code:
                        stock_id = s["StockID"]
                        break

                if self.use_db:
                    self.db_manager.execute_query(
                        "INSERT INTO StockMovements (StockID, MovementDate, MovementType, Quantity, UnitPrice, TotalAmount, Description) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (stock_id, date_str, mtype, qty, price, total, desc_entry.get()), fetch=False
                    )
                    new_qty = qty if mtype == "Giris" else -qty
                    self.db_manager.execute_query(
                        "UPDATE StockItems SET CurrentStock = CurrentStock + ? WHERE StockID=?",
                        (new_qty, stock_id), fetch=False
                    )
                    self.load_stock_from_db()
                    self.load_movements_from_db()
                else:
                    new_id = max(m.get("MovementID", 0) for m in self.stock_movements) + 1
                    stock_name = stock_text.split(" - ")[1] if " - " in stock_text else ""
                    for s in self.stock_items:
                        if s.get("StockID") == stock_id:
                            if mtype == "Giris":
                                s["CurrentStock"] = s.get("CurrentStock", 0) + qty
                            else:
                                s["CurrentStock"] = s.get("CurrentStock", 0) - qty
                            break
                    self.stock_movements.insert(0, {
                        "MovementID": new_id, "StockID": stock_id,
                        "StockCode": stock_code, "StockName": stock_name,
                        "MovementDate": date_str, "MovementType": mtype,
                        "Quantity": qty, "UnitPrice": price, "TotalAmount": total,
                        "Description": desc_entry.get()
                    })
                    self.refresh_stock_tree()
                    self.refresh_movement_tree()
                messagebox.showinfo("Basarili", "Stok hareketi kaydedildi!")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Hata", str(e))

        ctk.CTkButton(frame, text="Kaydet", command=save,
                       fg_color=SUCCESS, height=40,
                       font=ctk.CTkFont(size=14, weight="bold")).pack(pady=15)
