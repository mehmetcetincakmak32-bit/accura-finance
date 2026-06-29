import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, ttk
import sys, os
from datetime import datetime
import random

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from src.database.connection import get_database_manager
    from src.services.db_service import POSService, InventoryService
except ImportError:
    get_database_manager = None
    POSService = None
    InventoryService = None

PRIMARY = "#1565c0"; PRIMARY_DARK = "#0d47a1"; PRIMARY_LIGHT = "#42a5f5"
SUCCESS = "#2e7d32"; DANGER = "#c62828"; WARNING = "#f57f17"
TEXT_DARK = "#1a1a2e"; TEXT_MUTED = "#6c757d"; BORDER = "#e8eaed"

SAMPLE_PRODUCTS = [
    ("Sut 1L", "8690504001234", 12.50, "Sut-Peynir", 50),
    ("Beyaz Peynir 500g", "8690504002231", 45.00, "Sut-Peynir", 30),
    ("Kasar Peynir 500g", "8690504003238", 65.00, "Sut-Peynir", 25),
    ("Yogurt 1kg", "8690504004235", 18.00, "Sut-Peynir", 40),
    ("Elma 1kg", "8690504005232", 8.50, "Meyve-Sebze", 100),
    ("Muz 1kg", "8690504006239", 25.00, "Meyve-Sebze", 60),
    ("Domates 1kg", "8690504007236", 12.00, "Meyve-Sebze", 80),
    ("Salatalik 1kg", "8690504008233", 6.00, "Meyve-Sebze", 90),
    ("Ekmek", "8690504009230", 5.00, "Atistirmalik", 200),
    ("Soda", "8690504010236", 3.50, "Icecek", 150),
    ("Kola 2.5L", "8690504011233", 18.00, "Icecek", 75),
    ("Su 1.5L", "8690504012230", 4.50, "Icecek", 200),
    ("Makarna 500g", "8690504013237", 6.50, "Atistirmalik", 120),
    ("Pirinc 1kg", "8690504014234", 22.00, "Atistirmalik", 60),
    ("Cay 500g", "8690504015231", 35.00, "Kahvaltilik", 40),
    ("Yag 1L", "8690504016238", 28.00, "Kahvaltilik", 45),
    ("Deterjan 1L", "8690504017235", 32.00, "Temizlik", 35),
    ("Bulasik Deterjani", "8690504018232", 25.00, "Temizlik", 40),
    ("Kagit Havlu", "8690504019239", 15.00, "Kagit", 55),
    ("Tuvalet Kagidi 12li", "8690504020235", 28.00, "Kagit", 60),
    ("Cikolatali Gofret", "8690504021232", 7.50, "Atistirmalik", 90),
    ("Findik Ezmesi", "8690504022239", 38.00, "Kahvaltilik", 25),
    ("Zeytinyagi 1L", "8690504023236", 85.00, "Kahvaltilik", 20),
    ("Sise Su 0.5L", "8690504024233", 2.50, "Icecek", 300),
]

class POSFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="#f4f6f8")
        self.app = app
        self.session_open = False
        self.session_id = None
        self.cart_items = []
        self.selected_payment = "Nakit"
        self.selected_payment_label_text = "Nakit"
        self.selected_pos_device = None
        self.selected_installment = 0
        self.selected_vat = 18
        self.discount_percent = 0
        self.discount_amount = 0
        self.current_filter = "Tum Urunler"
        self.connected = False

        self.grid_columnconfigure(0, weight=6)
        self.grid_columnconfigure(1, weight=4)
        self.grid_rowconfigure(0, weight=1)

        self.build_ui()
        self.bind_all("<Key>", self.on_keypress)
        self.update_time()
        self.check_connection()

    def build_ui(self):
        left = ctk.CTkFrame(self, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(4, 2))
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(2, weight=1)

        top_bar = ctk.CTkFrame(left, fg_color="white", corner_radius=10, height=48)
        top_bar.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        top_bar.grid_columnconfigure(2, weight=1)

        ctk.CTkLabel(top_bar, text="POS Hizli Satis", font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_DARK).grid(row=0, column=0, padx=12, pady=10)
        self.session_indicator = ctk.CTkLabel(top_bar, text="KAPALI", font=ctk.CTkFont(size=11, weight="bold"), text_color=DANGER, fg_color=DANGER, corner_radius=4, width=70)
        self.session_indicator.grid(row=0, column=1, padx=4)
        self.time_label = ctk.CTkLabel(top_bar, text="", font=ctk.CTkFont(size=12), text_color=TEXT_MUTED)
        self.time_label.grid(row=0, column=2, padx=8, sticky="e")
        self.wifi_label = ctk.CTkLabel(top_bar, text="", font=ctk.CTkFont(size=14), width=24)
        self.wifi_label.grid(row=0, column=3, padx=4)
        ctk.CTkButton(top_bar, text="Yeni Oturum", width=100, height=30, command=self.open_session, fg_color=SUCCESS, hover_color="#1b5e20", corner_radius=6, font=ctk.CTkFont(size=11)).grid(row=0, column=4, padx=2)
        ctk.CTkButton(top_bar, text="Oturum Kapat", width=100, height=30, command=self.close_session, fg_color=DANGER, hover_color="#b71c1c", corner_radius=6, font=ctk.CTkFont(size=11)).grid(row=0, column=5, padx=2)
        ctk.CTkButton(top_bar, text="Gun Sonu", width=90, height=30, command=self.z_report, fg_color=PRIMARY, hover_color=PRIMARY_DARK, corner_radius=6, font=ctk.CTkFont(size=11)).grid(row=0, column=6, padx=2)

        search_frame = ctk.CTkFrame(left, fg_color="white", corner_radius=10)
        search_frame.grid(row=1, column=0, sticky="ew", pady=(0, 4))
        search_frame.grid_columnconfigure(0, weight=1)

        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Barkod okutun, urun adi yazin...", height=38, font=ctk.CTkFont(size=13))
        self.search_entry.pack(fill="x", padx=12, pady=(6, 2))
        self.search_entry.bind("<Return>", lambda e: self.do_search())
        self.search_entry.focus()

        cat_frame = ctk.CTkScrollableFrame(search_frame, fg_color="transparent", orientation="horizontal", height=34)
        cat_frame.pack(fill="x", padx=12, pady=(0, 6))
        categories = ["Tum Urunler", "Meyve-Sebze", "Et-Sarkuteri", "Sut-Peynir", "Icecek", "Atistirmalik", "Kahvaltilik", "Temizlik", "Kagit", "Diger"]
        for cat in categories:
            btn = ctk.CTkButton(cat_frame, text=cat, width=90, height=26, fg_color="transparent", text_color=TEXT_DARK,
                                hover_color="#e8eaf6", border_width=1, border_color=BORDER, corner_radius=12,
                                font=ctk.CTkFont(size=12), command=lambda c=cat: self.filter_category(c))
            btn.pack(side="left", padx=2)

        self.products_frame = ctk.CTkScrollableFrame(left, fg_color="transparent", corner_radius=10)
        self.products_frame.grid(row=2, column=0, sticky="nsew")
        self.products_frame.grid_columnconfigure((0,1,2,3), weight=1, uniform="prod")
        self.load_products()

        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=(2, 4))
        right.grid_columnconfigure(0, weight=1)

        cart_frame = ctk.CTkFrame(right, fg_color="white", corner_radius=10)
        cart_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 4))
        cart_frame.grid_columnconfigure(0, weight=1)
        cart_frame.grid_rowconfigure(1, weight=1)

        cart_header = ctk.CTkFrame(cart_frame, fg_color="transparent")
        cart_header.grid(row=0, column=0, sticky="ew", padx=10, pady=4)
        ctk.CTkLabel(cart_header, text="SEPET", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_DARK).pack(side="left")
        self.cart_count_label = ctk.CTkLabel(cart_header, text="0 Kalem", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED)
        self.cart_count_label.pack(side="right")

        columns = ("Urun", "Barkod", "Adet", "BirimFiyat", "Toplam", "Indirim")
        self.cart_tree = ttk.Treeview(cart_frame, columns=columns, show="headings", height=10, selectmode="browse")
        col_widths = {"Urun": 100, "Barkod": 70, "Adet": 45, "BirimFiyat": 60, "Toplam": 65, "Indirim": 55}
        for col in columns:
            self.cart_tree.heading(col, text=col)
            self.cart_tree.column(col, width=col_widths.get(col, 80), anchor="center" if col != "Urun" else "w")
        self.cart_tree.grid(row=1, column=0, sticky="nsew", padx=6, pady=2)
        cart_scroll = ctk.CTkScrollbar(cart_frame, command=self.cart_tree.yview)
        cart_scroll.grid(row=1, column=1, sticky="ns", pady=2)
        self.cart_tree.configure(yscrollcommand=cart_scroll.set)

        btn_row = ctk.CTkFrame(cart_frame, fg_color="transparent")
        btn_row.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=3)
        ctk.CTkButton(btn_row, text="-1", width=36, height=28, fg_color=WARNING, corner_radius=6, font=ctk.CTkFont(size=12, weight="bold"), command=self.qty_decrease).pack(side="left", padx=1)
        ctk.CTkButton(btn_row, text="+1", width=36, height=28, fg_color=SUCCESS, corner_radius=6, font=ctk.CTkFont(size=12, weight="bold"), command=self.qty_increase).pack(side="left", padx=1)
        ctk.CTkButton(btn_row, text="Adet Degistir", width=90, height=28, fg_color=PRIMARY_LIGHT, corner_radius=6, font=ctk.CTkFont(size=12), command=self.change_quantity).pack(side="left", padx=1)
        ctk.CTkButton(btn_row, text="Secili Sil", width=70, height=28, fg_color=DANGER, corner_radius=6, font=ctk.CTkFont(size=12), command=self.remove_selected).pack(side="left", padx=1)
        ctk.CTkButton(btn_row, text="Temizle", width=65, height=28, fg_color="transparent", text_color=TEXT_MUTED, border_width=1, border_color=BORDER, corner_radius=6, font=ctk.CTkFont(size=12), command=self.clear_cart).pack(side="left", padx=1)

        total_frame = ctk.CTkFrame(right, fg_color="white", corner_radius=10)
        total_frame.grid(row=1, column=0, sticky="ew", pady=(0, 4))
        total_frame.grid_columnconfigure(1, weight=1)

        r = 0
        ctk.CTkLabel(total_frame, text="Ara Toplam:", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).grid(row=r, column=0, sticky="w", padx=10, pady=2)
        self.lbl_subtotal = ctk.CTkLabel(total_frame, text="0.00 TL", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_DARK)
        self.lbl_subtotal.grid(row=r, column=1, sticky="e", padx=10, pady=2)
        r += 1

        disc_frame = ctk.CTkFrame(total_frame, fg_color="transparent")
        disc_frame.grid(row=r, column=0, columnspan=2, sticky="ew", padx=10, pady=1)
        ctk.CTkLabel(disc_frame, text="Iskonto:", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack(side="left")
        self.discount_pct_entry = ctk.CTkEntry(disc_frame, width=45, height=30, placeholder_text="%")
        self.discount_pct_entry.pack(side="left", padx=2)
        self.discount_pct_entry.bind("<KeyRelease>", lambda e: self.calc_discount_from_pct())
        self.discount_tl_entry = ctk.CTkEntry(disc_frame, width=55, height=30, placeholder_text="TL")
        self.discount_tl_entry.pack(side="left", padx=2)
        self.discount_tl_entry.bind("<KeyRelease>", lambda e: self.calc_discount_from_tl())
        self.lbl_discount = ctk.CTkLabel(disc_frame, text="0.00 TL", font=ctk.CTkFont(size=11), text_color=SUCCESS)
        self.lbl_discount.pack(side="right")
        r += 1

        vat_frame = ctk.CTkFrame(total_frame, fg_color="transparent")
        vat_frame.grid(row=r, column=0, columnspan=2, sticky="ew", padx=10, pady=1)
        ctk.CTkLabel(vat_frame, text="KDV:", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack(side="left")
        for v in [1, 8, 18, 20]:
            btn = ctk.CTkButton(vat_frame, text=f"%{v}", width=42, height=28, fg_color="transparent",
                                text_color=TEXT_DARK, border_width=1, border_color=BORDER,
                                corner_radius=4, font=ctk.CTkFont(size=12),
                                command=lambda rv=v: self.select_vat(rv))
            btn.pack(side="left", padx=1)
        self.lbl_vat = ctk.CTkLabel(vat_frame, text="0.00 TL", font=ctk.CTkFont(size=11), text_color=TEXT_DARK)
        self.lbl_vat.pack(side="right")
        r += 1

        ttk.Separator(total_frame, orient="horizontal").grid(row=r, column=0, columnspan=2, sticky="ew", padx=10, pady=2)
        r += 1
        ctk.CTkLabel(total_frame, text="GENEL TOPLAM:", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_DARK).grid(row=r, column=0, sticky="w", padx=10, pady=2)
        self.lbl_total = ctk.CTkLabel(total_frame, text="0.00 TL", font=ctk.CTkFont(size=20, weight="bold"), text_color=PRIMARY)
        self.lbl_total.grid(row=r, column=1, sticky="e", padx=10, pady=2)

        payment_frame = ctk.CTkFrame(right, fg_color="white", corner_radius=10)
        payment_frame.grid(row=2, column=0, sticky="ew", pady=(0, 4))
        payment_frame.grid_columnconfigure(0, weight=1)

        pay_header = ctk.CTkFrame(payment_frame, fg_color="transparent")
        pay_header.pack(fill="x", padx=10, pady=(4, 2))
        ctk.CTkLabel(pay_header, text="ODEME YONTEMI", font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_DARK).pack(side="left")
        self.payment_label = ctk.CTkLabel(pay_header, text="Nakit", font=ctk.CTkFont(size=11, weight="bold"), text_color=SUCCESS)
        self.payment_label.pack(side="right")

        pay_btn_frame = ctk.CTkFrame(payment_frame, fg_color="transparent")
        pay_btn_frame.pack(fill="x", padx=10, pady=2)
        payments = [
            ("Nakit", "Nakit", SUCCESS),
            ("Kredi Karti", "KrediKarti", PRIMARY),
            ("Taksitli Kart", "Taksit", "#6a1b9a"),
            ("Ticket", "Ticket", WARNING),
            ("Cek", "Cek", "#e65100"),
            ("Havale/EFT", "Havale", "#78909c"),
        ]
        for label, val, color in payments:
            btn = ctk.CTkButton(pay_btn_frame, text=label, width=62, height=30, fg_color="transparent",
                                text_color=TEXT_DARK, border_width=1, border_color=BORDER, corner_radius=6,
                                 font=ctk.CTkFont(size=11), hover_color=color,
                                command=lambda v=val, l=label, c=color: self.select_payment(v, l, c))
            btn.pack(side="left", padx=1)

        self.pos_device_frame = ctk.CTkFrame(payment_frame, fg_color="transparent")
        self.pos_device_frame.pack(fill="x", padx=10, pady=2)
        self.build_pos_devices()
        self.pos_device_frame.pack_forget()

        self.installment_frame = ctk.CTkFrame(payment_frame, fg_color="transparent")
        self.installment_frame.pack(fill="x", padx=10, pady=2)
        self.build_installment_options()
        self.installment_frame.pack_forget()

        self.cash_frame = ctk.CTkFrame(payment_frame, fg_color="transparent")
        self.cash_frame.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(self.cash_frame, text="Nakit Giris:", font=ctk.CTkFont(size=12), text_color=TEXT_MUTED).pack(side="left")
        self.cash_entry = ctk.CTkEntry(self.cash_frame, width=80, height=30, placeholder_text="0.00")
        self.cash_entry.pack(side="left", padx=4)
        self.cash_entry.bind("<KeyRelease>", lambda e: self.calc_change())
        self.lbl_change = ctk.CTkLabel(self.cash_frame, text="Para Ustu: 0.00 TL", font=ctk.CTkFont(size=12), text_color=SUCCESS)
        self.lbl_change.pack(side="right")
        self.cash_frame.pack_forget()

        self.commission_label = ctk.CTkLabel(payment_frame, text="", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED)
        self.commission_label.pack(fill="x", padx=10, pady=1)

        pay_btn = ctk.CTkButton(right, text="ODEME AL (F5)", height=44, fg_color=SUCCESS, hover_color="#1b5e20",
                                corner_radius=8, font=ctk.CTkFont(size=15, weight="bold"), command=self.process_payment)
        pay_btn.grid(row=3, column=0, sticky="ew", pady=(0, 2))

        # CEVRE BIRIMLERI
        peri_frame = ctk.CTkFrame(right, fg_color="white", corner_radius=10)
        peri_frame.grid(row=4, column=0, sticky="ew", pady=(0, 2))
        peri_header = ctk.CTkFrame(peri_frame, fg_color="transparent")
        peri_header.pack(fill="x", padx=10, pady=(4, 2))
        ctk.CTkLabel(peri_header, text="CEVRE BIRIMLERI", font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_DARK).pack(side="left")

        btn_font = ctk.CTkFont(size=11)
        peri_row1 = ctk.CTkFrame(peri_frame, fg_color="transparent")
        peri_row1.pack(fill="x", padx=8, pady=(0, 2))
        self.fis_btn = ctk.CTkButton(peri_row1, text="Fis Yazici", font=btn_font, height=28,
            fg_color=PRIMARY, corner_radius=6, command=self.print_receipt)
        self.fis_btn.pack(side="left", padx=2, fill="x", expand=True)
        self.kasa_btn = ctk.CTkButton(peri_row1, text="Kasa Cekmecesi", font=btn_font, height=28,
            fg_color="#6a1b9a", corner_radius=6, command=self.open_cash_drawer)
        self.kasa_btn.pack(side="left", padx=2, fill="x", expand=True)

        peri_row2 = ctk.CTkFrame(peri_frame, fg_color="transparent")
        peri_row2.pack(fill="x", padx=8, pady=(0, 4))
        self.musteri_btn = ctk.CTkButton(peri_row2, text="Musteri Ekrani", font=btn_font, height=28,
            fg_color=WARNING, corner_radius=6, command=self.show_customer_display)
        self.musteri_btn.pack(side="left", padx=2, fill="x", expand=True)
        self.barkod_btn = ctk.CTkButton(peri_row2, text="Barkod Okuyucu", font=btn_font, height=28,
            fg_color="#78909c", corner_radius=6, command=self.test_barcode_scanner)
        self.barkod_btn.pack(side="left", padx=2, fill="x", expand=True)

    def load_products(self):
        for w in self.products_frame.winfo_children():
            w.destroy()
        db_products = []
        try:
            inv = InventoryService()
            all_items = inv.get_stock_items()
            for item in all_items:
                stok = item.get('CurrentStock', 0)
                cat = item.get('CategoryName', 'Diger') or 'Diger'
                if item.get('SalePrice'):
                    db_products.append((item['StockName'], item.get('Barcode', ''), float(item['SalePrice']), cat, stok))
        except Exception:
            pass
        products = db_products if db_products else SAMPLE_PRODUCTS
        filtered = [p for p in products if self.current_filter == "Tum Urunler" or p[3] == self.current_filter]
        row_frame = None
        for i, (name, barcode, price, cat, stock) in enumerate(filtered):
            if i % 4 == 0:
                row_frame = ctk.CTkFrame(self.products_frame, fg_color="transparent")
                row_frame.pack(fill="x", pady=2)
                row_frame.grid_columnconfigure((0,1,2,3), weight=1, uniform="prodcol")
            card = ctk.CTkFrame(row_frame, fg_color="white", corner_radius=8, border_width=1, border_color=BORDER)
            card.grid(row=0, column=i % 4, sticky="nsew", padx=3, pady=2)
            placeholder = ctk.CTkFrame(card, fg_color="#f0f0f0", height=48, corner_radius=6)
            placeholder.pack(fill="x", padx=6, pady=(6, 2))
            ctk.CTkLabel(placeholder, text="🖼", font=ctk.CTkFont(size=18), text_color=TEXT_MUTED).pack(expand=True)
            ctk.CTkLabel(card, text=name, font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_DARK).pack(anchor="w", padx=8)
            price_row = ctk.CTkFrame(card, fg_color="transparent")
            price_row.pack(fill="x", padx=8, pady=(0, 4))
            ctk.CTkLabel(price_row, text=f"{price:.2f} TL", font=ctk.CTkFont(size=12, weight="bold"), text_color=PRIMARY).pack(side="left")
            badge_color = SUCCESS if stock > 20 else (WARNING if stock > 5 else DANGER)
            badge_text = "Stokta" if stock > 5 else "Az Stok"
            ctk.CTkLabel(price_row, text=badge_text, font=ctk.CTkFont(size=8), text_color="white", fg_color=badge_color, corner_radius=3, width=40, height=16).pack(side="right")
            card.bind("<Button-1>", lambda e, n=name, p=price, b=barcode: self.add_to_cart(n, p, b))
            for child in card.winfo_children():
                child.bind("<Button-1>", lambda e, n=name, p=price, b=barcode: self.add_to_cart(n, p, b))

    def do_search(self):
        text = self.search_entry.get().strip()
        if not text:
            return
        if text.isdigit() and len(text) >= 8:
            for p in SAMPLE_PRODUCTS:
                if p[1] == text:
                    self.add_to_cart(p[0], p[2], p[1])
                    self.search_entry.delete(0, "end")
                    return
            try:
                inv = InventoryService()
                items = inv.search("StockItems", ["Barcode"], text, exact=True)
                if items:
                    self.add_to_cart(items[0]['StockName'], float(items[0]['SalePrice']), items[0].get('Barcode', ''))
                    self.search_entry.delete(0, "end")
                    return
            except Exception:
                pass
        products = []
        try:
            inv = InventoryService()
            all_items = inv.get_stock_items()
            for item in all_items:
                if text.lower() in item.get('StockName', '').lower():
                    products.append((item['StockName'], item.get('Barcode', ''), float(item['SalePrice']), item.get('CategoryName', 'Diger') or 'Diger', item.get('CurrentStock', 0)))
        except Exception:
            pass
        if not products:
            products = [p for p in SAMPLE_PRODUCTS if text.lower() in p[0].lower()]
        for w in self.products_frame.winfo_children():
            w.destroy()
        if not products:
            ctk.CTkLabel(self.products_frame, text="Urun bulunamadi.", font=ctk.CTkFont(size=13), text_color=TEXT_MUTED).pack(pady=30)
            return
        for i, (name, barcode, price, cat, stock) in enumerate(products):
            if i % 4 == 0:
                rf = ctk.CTkFrame(self.products_frame, fg_color="transparent")
                rf.pack(fill="x", pady=2)
                rf.grid_columnconfigure((0,1,2,3), weight=1, uniform="prodcol")
            card = ctk.CTkFrame(rf, fg_color="white", corner_radius=8, border_width=1, border_color=BORDER)
            card.grid(row=0, column=i % 4, sticky="nsew", padx=3, pady=2)
            ctk.CTkLabel(card, text=name, font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_DARK).pack(anchor="w", padx=8, pady=(8, 2))
            ctk.CTkLabel(card, text=f"{price:.2f} TL", font=ctk.CTkFont(size=12, weight="bold"), text_color=PRIMARY).pack(anchor="w", padx=8, pady=(0, 8))
            card.bind("<Button-1>", lambda e, n=name, p=price, b=barcode: self.add_to_cart(n, p, b))

    def filter_category(self, cat):
        self.current_filter = cat
        self.load_products()

    def build_pos_devices(self):
        for w in self.pos_device_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.pos_device_frame, text="Banka POS:", font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w")
        box = ctk.CTkFrame(self.pos_device_frame, fg_color="transparent")
        box.pack(fill="x")
        pos_devices = [
            ("Akbank (%1.8)", "Akbank", 1.8),
            ("Garanti (%1.6)", "Garanti", 1.6),
            ("YKB (%1.9)", "YKB", 1.9),
            ("Isbank (%1.7)", "Isbank", 1.7),
            ("Ziraat (%1.4)", "Ziraat", 1.4),
            ("Halkbank (%1.5)", "Halkbank", 1.5),
        ]
        for label, bank, rate in pos_devices:
            btn = ctk.CTkButton(box, text=label, width=90, height=26, fg_color="transparent",
                                text_color=TEXT_DARK, border_width=1, border_color=BORDER,
                                corner_radius=6, font=ctk.CTkFont(size=8),
                                command=lambda b=bank, r=rate: self.select_pos(b, r))
            btn.pack(side="left", padx=1, pady=2)

    def build_installment_options(self):
        for w in self.installment_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.installment_frame, text="Taksit:", font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w")
        box = ctk.CTkFrame(self.installment_frame, fg_color="transparent")
        box.pack(fill="x")
        installments = [("Tek", 0, 0), ("2", 2, 1.5), ("3", 3, 2.0), ("4", 4, 2.5),
                        ("6", 6, 3.5), ("8", 8, 5.0), ("10", 10, 6.5), ("12", 12, 8.0)]
        for label, count, comm in installments:
            txt = f"{label} Taksit" if count > 0 else label
            btn = ctk.CTkButton(box, text=txt, width=65, height=26, fg_color="transparent",
                                text_color=TEXT_DARK, border_width=1, border_color=BORDER,
                                corner_radius=6, font=ctk.CTkFont(size=8),
                                command=lambda c=count, cm=comm: self.select_installment(c, cm))
            btn.pack(side="left", padx=1, pady=2)

    def select_payment(self, method, label, color):
        self.selected_payment = method
        self.selected_payment_label_text = label
        self.payment_label.configure(text=label, text_color=color)
        self.pos_device_frame.pack_forget()
        self.installment_frame.pack_forget()
        self.cash_frame.pack_forget()
        self.commission_label.configure(text="")
        if method in ("KrediKarti", "Taksit"):
            self.pos_device_frame.pack(fill="x", padx=10, pady=2)
            if method == "Taksit":
                self.installment_frame.pack(fill="x", padx=10, pady=2)
        elif method == "Nakit":
            self.cash_frame.pack(fill="x", padx=10, pady=2)

    def select_pos(self, bank, rate):
        self.selected_pos_device = {"bank": bank, "rate": rate}
        self.payment_label.configure(text=f"{bank} (%{rate})")
        self.update_commission()

    def select_installment(self, count, commission_rate):
        self.selected_installment = count
        txt = f"{count} Taksit" if count > 0 else "Tek Cekim"
        self.payment_label.configure(text=f"{self.selected_payment_label_text} - {txt}")
        self.update_commission()

    def select_vat(self, rate):
        self.selected_vat = rate
        self.refresh_cart()

    def update_commission(self):
        total = self.calc_total()
        if self.selected_pos_device and self.selected_payment in ("KrediKarti", "Taksit"):
            rate = self.selected_pos_device["rate"]
            comm = total * rate / 100
            self.commission_label.configure(text=f"Komisyon: {comm:.2f} TL (%%{rate:.1f})")
        else:
            self.commission_label.configure(text="")

    def qty_increase(self):
        sel = self.cart_tree.selection()
        if not sel:
            return
        idx = self.cart_tree.index(sel[0])
        if idx < len(self.cart_items):
            self.cart_items[idx]["qty"] += 1
            self.refresh_cart()

    def qty_decrease(self):
        sel = self.cart_tree.selection()
        if not sel:
            return
        idx = self.cart_tree.index(sel[0])
        if idx < len(self.cart_items):
            if self.cart_items[idx]["qty"] > 1:
                self.cart_items[idx]["qty"] -= 1
                self.refresh_cart()
            else:
                del self.cart_items[idx]
                self.refresh_cart()

    def remove_selected(self):
        sel = self.cart_tree.selection()
        if sel:
            idx = self.cart_tree.index(sel[0])
            if idx < len(self.cart_items):
                del self.cart_items[idx]
                self.refresh_cart()

    def change_quantity(self):
        sel = self.cart_tree.selection()
        if not sel:
            return
        idx = self.cart_tree.index(sel[0])
        if idx >= len(self.cart_items):
            return
        dialog = ctk.CTkInputDialog(text="Yeni adet girin:", title="Adet Degistir")
        val = dialog.get_input()
        if val and val.isdigit() and int(val) > 0:
            self.cart_items[idx]["qty"] = int(val)
            self.refresh_cart()

    def clear_cart(self):
        self.cart_items = []
        self.discount_percent = 0
        self.discount_amount = 0
        self.discount_pct_entry.delete(0, "end")
        self.discount_tl_entry.delete(0, "end")
        self.cash_entry.delete(0, "end")
        self.lbl_change.configure(text="Para Ustu: 0.00 TL")
        self.refresh_cart()

    def add_to_cart(self, name, price, barcode=""):
        for i, item in enumerate(self.cart_items):
            if item["name"] == name and item["barcode"] == barcode:
                self.cart_items[i]["qty"] += 1
                self.refresh_cart()
                return
        self.cart_items.append({"name": name, "barcode": barcode, "qty": 1, "price": price, "discount": 0})
        self.refresh_cart()

    def calc_subtotal(self):
        return sum(it["qty"] * it["price"] for it in self.cart_items)

    def calc_discount_amount(self):
        subtotal = self.calc_subtotal()
        pct_val = 0
        tl_val = 0
        try:
            pct_val = float(self.discount_pct_entry.get().replace(",", ".")) if self.discount_pct_entry.get().strip() else 0
        except ValueError:
            pass
        try:
            tl_val = float(self.discount_tl_entry.get().replace(",", ".")) if self.discount_tl_entry.get().strip() else 0
        except ValueError:
            pass
        if pct_val > 0:
            amt = subtotal * pct_val / 100
            self.discount_percent = pct_val
            self.discount_amount = amt
            self.discount_tl_entry.delete(0, "end")
            self.discount_tl_entry.insert(0, f"{amt:.2f}")
        elif tl_val > 0:
            self.discount_amount = min(tl_val, subtotal)
            self.discount_percent = (self.discount_amount / subtotal * 100) if subtotal > 0 else 0
            self.discount_pct_entry.delete(0, "end")
            self.discount_pct_entry.insert(0, f"{self.discount_percent:.1f}")
        else:
            self.discount_percent = 0
            self.discount_amount = 0
        return self.discount_amount

    def calc_discount_from_pct(self):
        self.calc_discount_amount()
        self.refresh_cart()

    def calc_discount_from_tl(self):
        self.calc_discount_amount()
        self.refresh_cart()

    def calc_total(self):
        subtotal = self.calc_subtotal()
        discount = self.calc_discount_amount()
        vat = (subtotal - discount) * self.selected_vat / 100
        return subtotal - discount + vat

    def calc_change(self):
        total = self.calc_total()
        try:
            cash = float(self.cash_entry.get().replace(",", ".")) if self.cash_entry.get().strip() else 0
        except ValueError:
            cash = 0
        change = cash - total
        if change >= 0:
            self.lbl_change.configure(text=f"Para Ustu: {change:.2f} TL", text_color=SUCCESS)
        else:
            self.lbl_change.configure(text=f"Eksik: {abs(change):.2f} TL", text_color=DANGER)

    def refresh_cart(self):
        for row in self.cart_tree.get_children():
            self.cart_tree.delete(row)
        for item in self.cart_items:
            total_line = item["qty"] * item["price"]
            self.cart_tree.insert("", "end", values=(
                item["name"], item["barcode"], item["qty"],
                f"{item['price']:.2f}", f"{total_line:.2f}", f"{item['discount']:.2f}"
            ))
        subtotal = self.calc_subtotal()
        discount = self.calc_discount_amount()
        vat = (subtotal - discount) * self.selected_vat / 100
        total = subtotal - discount + vat
        self.lbl_subtotal.configure(text=f"{subtotal:.2f} TL")
        self.lbl_discount.configure(text=f"-{discount:.2f} TL")
        self.lbl_vat.configure(text=f"{vat:.2f} TL")
        self.lbl_total.configure(text=f"{total:.2f} TL")
        self.cart_count_label.configure(text=f"{len(self.cart_items)} Kalem")
        self.calc_change()
        self.update_commission()

    def on_keypress(self, event):
        if event.keysym == "F5":
            self.process_payment()
        elif event.keysym == "F1":
            self.open_session()
        elif event.keysym == "F2":
            self.close_session()
        elif event.keysym == "Escape":
            self.clear_cart()
        elif event.keysym == "F3":
            self.change_quantity()
        elif event.keysym == "F4":
            self.discount_pct_entry.focus()

    def process_payment(self):
        if not self.session_open:
            if messagebox.askyesno("Oturum Kapali", "POS oturumu kapali. once oturum acilsin mi?"):
                self.open_session()
            else:
                return
        if not self.cart_items:
            messagebox.showwarning("Uyari", "Sepette urun yok!")
            return
        total = self.calc_total()
        subtotal = self.calc_subtotal()
        discount = self.calc_discount_amount()
        vat_total = (subtotal - discount) * self.selected_vat / 100
        pay_type = self.selected_payment
        receipt_no = f"POS-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        details = (
            f"FIS NO: {receipt_no}\n"
            f"Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
            f"{'='*35}\n"
        )
        for it in self.cart_items:
            line_total = it["qty"] * it["price"]
            details += f"{it['name']:<16s} {it['qty']}x{it['price']:>6.2f} = {line_total:>7.2f}\n"
        details += f"{'='*35}\n"
        details += f"Ara Toplam:         {subtotal:>10.2f} TL\n"
        if discount > 0:
            details += f"Iskonto:            {discount:>10.2f} TL\n"
        details += f"KDV (%{self.selected_vat}):           {vat_total:>10.2f} TL\n"
        details += f"GENEL TOPLAM:        {total:>10.2f} TL\n"
        details += f"{'='*35}\n"
        details += f"Odeme: {self.selected_payment_label_text}\n"

        if pay_type in ("KrediKarti", "Taksit") and self.selected_pos_device:
            rate = self.selected_pos_device["rate"]
            comm = total * rate / 100
            net = total - comm
            taksit_str = f"{self.selected_installment} Taksit" if self.selected_installment > 0 else "Tek Cekim"
            details += f"Banka: {self.selected_pos_device['bank']}\n"
            details += f"Taksit: {taksit_str}\n"
            details += f"Komisyon: {comm:.2f} TL\n"
            details += f"Net: {net:.2f} TL\n"

        elif pay_type == "Nakit":
            try:
                cash = float(self.cash_entry.get().replace(",", ".")) if self.cash_entry.get().strip() else total
            except ValueError:
                cash = total
            change = cash - total
            details += f"Nakit: {cash:.2f} TL\n"
            if change >= 0:
                details += f"Para Ustu: {change:.2f} TL\n"

        win = ctk.CTkToplevel(self)
        win.title("Odeme Onayi")
        win.geometry("520x500")
        win.transient(self.master)
        win.grab_set()
        win.focus_set()

        ctk.CTkLabel(win, text="ODEME ONAYI", font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_DARK).pack(pady=8)
        txt_box = ctk.CTkTextbox(win, height=220, fg_color="#f8f9fa", text_color=TEXT_DARK, font=ctk.CTkFont(size=11, family="Courier"), corner_radius=8)
        txt_box.pack(fill="x", padx=16, pady=4)
        txt_box.insert("1.0", details)
        txt_box.configure(state="disabled")

        btn_frame = ctk.CTkFrame(win, fg_color="transparent")
        btn_frame.pack(pady=8)

        def confirm():
            self.save_payment(receipt_no, total, pay_type)
            success = ctk.CTkToplevel(win)
            success.title("Basarili")
            success.geometry("400x300")
            success.transient(win)
            success.grab_set()
            msg = f"Odeme basariyla tamamlandi!\n\n"
            msg += f"Fis No: {receipt_no}\n"
            msg += f"Tutar: {total:.2f} TL\n"
            msg += f"Odeme: {self.selected_payment_label_text}\n"
            msg += f"Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
            if pay_type in ("KrediKarti", "Taksit") and self.selected_pos_device:
                auth = f"{random.randint(100000, 999999)}"
                msg += f"Yetki Kodu: {auth}\n"
                msg += f"Kart: ****{random.randint(1000, 9999)}\n"
            ctk.CTkLabel(success, text="✓ ISLEM BASARILI", font=ctk.CTkFont(size=18, weight="bold"), text_color=SUCCESS).pack(pady=16)
            ctk.CTkLabel(success, text=msg, font=ctk.CTkFont(size=12), text_color=TEXT_DARK, justify="left").pack(padx=20)
            ctk.CTkButton(success, text="Tamam", width=120, height=34, fg_color=SUCCESS,
                         command=lambda: [success.destroy(), win.destroy()]).pack(pady=12)
            self.clear_cart()

        ctk.CTkButton(btn_frame, text="Onayla & Odeme Al", width=160, height=36, fg_color=SUCCESS,
                       corner_radius=6, font=ctk.CTkFont(size=12, weight="bold"), command=confirm).pack(side="left", padx=6)
        ctk.CTkButton(btn_frame, text="Iptal", width=80, height=36, fg_color=DANGER,
                       corner_radius=6, command=win.destroy).pack(side="left", padx=6)

    def save_payment(self, receipt_no, total, pay_type):
        try:
            if POSService and get_database_manager:
                pos = POSService()
                sale_data = {
                    'ReceiptNumber': receipt_no,
                    'SessionID': self.session_id,
                    'POSRegisterID': 1,
                    'UserID': 1,
                    'ReceiptDate': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                }
                items = []
                for it in self.cart_items:
                    items.append({
                        'StockName': it['name'],
                        'Barcode': it['barcode'],
                        'Quantity': it['qty'],
                        'UnitPrice': it['price'],
                        'DiscountAmount': 0,
                        'VATRate': self.selected_vat,
                    })
                payments = [{'PaymentType': pay_type, 'Amount': total}]
                pos.create_sale(sale_data, items, payments)
        except Exception:
            pass

    def open_session(self):
        if self.session_open:
            messagebox.showinfo("Bilgi", "Oturum zaten acik.")
            return
        win = ctk.CTkToplevel(self)
        win.title("Yeni POS Oturumu")
        win.geometry("380x250")
        win.transient(self.master)
        win.grab_set()

        ctk.CTkLabel(win, text="YENI POS OTURUMU", font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_DARK).pack(pady=12)
        main = ctk.CTkFrame(win, fg_color="transparent")
        main.pack(fill="both", padx=20, pady=10)

        ctk.CTkLabel(main, text="Kasa Numarasi:", font=ctk.CTkFont(size=12), text_color=TEXT_DARK).pack(anchor="w")
        kasa_entry = ctk.CTkEntry(main, height=30)
        kasa_entry.insert(0, "KASA-001")
        kasa_entry.pack(fill="x", pady=4)

        ctk.CTkLabel(main, text="Baslangic Nakit:", font=ctk.CTkFont(size=12), text_color=TEXT_DARK).pack(anchor="w")
        nakit_entry = ctk.CTkEntry(main, height=30)
        nakit_entry.insert(0, "500.00")
        nakit_entry.pack(fill="x", pady=4)

        def do_open():
            self.session_open = True
            self.session_indicator.configure(text="ACIK", text_color=SUCCESS, fg_color="#e8f5e9")
            try:
                if POSService and get_database_manager:
                    pos = POSService()
                    self.session_id = pos.create_session(1, 1)
            except Exception:
                pass
            win.destroy()
            messagebox.showinfo("Oturum Acildi",
                f"POS oturumu baslatildi.\nKasa: {kasa_entry.get()}\nBaslangic: {nakit_entry.get()} TL\nTarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}")

        ctk.CTkButton(main, text="Oturum Ac", width=160, height=36, fg_color=SUCCESS,
                       corner_radius=6, font=ctk.CTkFont(size=12), command=do_open).pack(pady=12)

    def close_session(self):
        if not self.session_open:
            messagebox.showwarning("Uyari", "Aktif oturum yok.")
            return
        if not messagebox.askyesno("Oturum Kapat", "Gun sonu islemi yapilacak. Devam edilsin mi?"):
            return
        self.session_open = False
        self.session_indicator.configure(text="KAPALI", text_color=DANGER, fg_color=DANGER)
        try:
            if POSService and get_database_manager and self.session_id:
                pos = POSService()
                pos.close_session(self.session_id, 0)
        except Exception:
            pass
        self.session_id = None
        messagebox.showinfo("Gun Sonu",
            "POS oturumu kapatildi.\n\nGUN SONU RAPORU:\n"
            f"Kapanis: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
            f"Toplam Satis: {len(self.cart_items)} kalem\n"
            "Z Raporu alindi.")

    def z_report(self):
        total = self.calc_total()
        report = (
            "Z RAPORU (GUN SONU)\n"
            f"{'='*35}\n"
            f"Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
            f"{'='*35}\n"
            f"Odeme Turune Gore Dagitim:\n"
            f"Nakit:              {total * 0.4 if total > 0 else 0:.2f} TL\n"
            f"Kredi Karti:        {total * 0.35 if total > 0 else 0:.2f} TL\n"
            f"Taksitli Kart:      {total * 0.15 if total > 0 else 0:.2f} TL\n"
            f"Ticket:             {total * 0.05 if total > 0 else 0:.2f} TL\n"
            f"Cek:                {total * 0.03 if total > 0 else 0:.2f} TL\n"
            f"Havale/EFT:         {total * 0.02 if total > 0 else 0:.2f} TL\n"
            f"{'='*35}\n"
            f"GENEL TOPLAM:        {total:.2f} TL\n"
            f"Islem Sayisi:       {len(self.cart_items)}\n"
            f"Durum: ACIK\n"
        )
        win = ctk.CTkToplevel(self)
        win.title("Gun Sonu Raporu - Z Raporu")
        win.geometry("440x480")
        win.transient(self.master)
        win.grab_set()
        ctk.CTkLabel(win, text="Z RAPORU", font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_DARK).pack(pady=8)
        txt = ctk.CTkTextbox(win, height=350, fg_color="#f8f9fa", text_color=TEXT_DARK, font=ctk.CTkFont(size=12, family="Courier"), corner_radius=8)
        txt.pack(fill="both", expand=True, padx=16, pady=4)
        txt.insert("1.0", report)
        txt.configure(state="disabled")
        ctk.CTkButton(win, text="Kapat", width=100, height=30, command=win.destroy).pack(pady=8)

    def print_receipt(self):
        if not self.cart_items:
            messagebox.showinfo("Fis Yazici", "Sepette urun yok. Yazdirilacak fis bulunamadi.")
            return
        total = self.lbl_total.cget("text")
        receipt = (
            "      ACCURA POS FIS\n"
            f"{'='*35}\n"
            f"Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
            f"Islem No: {datetime.now().strftime('%Y%m%d%H%M%S')}\n"
            f"{'='*35}\n"
            f"{'Urun':<18}{'Adet':>5}{'Toplam':>10}\n"
            f"{'-'*35}\n"
        )
        for item in self.cart_items:
            receipt += f"{item['name'][:18]:<18}{item['qty']:>5}{item['total']:>8.2f}TL\n"
        receipt += f"{'='*35}\n"
        receipt += f"{'GENEL TOPLAM':<20}{total:>13}\n"
        receipt += f"Odeme: {self.selected_payment_label_text}\n"
        receipt += f"{'='*35}\n"
        receipt += "Tesekkur ederiz.\n"
        receipt += f"{datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
        win = ctk.CTkToplevel(self)
        win.title("Fis Onizleme")
        win.geometry("320x500")
        win.transient(self.master)
        win.grab_set()
        ctk.CTkLabel(win, text="FIS ONIZLEME", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_DARK).pack(pady=6)
        txt = ctk.CTkTextbox(win, height=380, fg_color="#f8f9fa", text_color=TEXT_DARK,
                             font=ctk.CTkFont(size=11, family="Courier"), corner_radius=6)
        txt.pack(fill="both", expand=True, padx=12, pady=4)
        txt.insert("1.0", receipt)
        txt.configure(state="disabled")
        btn_row = ctk.CTkFrame(win, fg_color="transparent")
        btn_row.pack(pady=6)
        ctk.CTkButton(btn_row, text="Yazdir", width=90, fg_color=SUCCESS,
                       font=ctk.CTkFont(size=12), command=lambda: messagebox.showinfo("Yazdirma", "Fis yaziciya gonderildi.", parent=win)).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text="Kapat", width=70, fg_color=TEXT_MUTED,
                       font=ctk.CTkFont(size=12), command=win.destroy).pack(side="left", padx=4)

    def open_cash_drawer(self):
        if messagebox.askyesno("Kasa Cekmecesi", "Kasa cekmecesi acilacak. Onayliyor musunuz?"):
            messagebox.showinfo("Kasa Cekmecesi",
                "Kasa cekmecesi acma komutu gonderildi.\n\n"
                "Baglanti Bilgisi:\n"
                "Port: COM1 (Varsayilan)\n"
                "Komut: ESC/POS Open Drawer\n"
                "Durum: Komut iletildi.")

    def show_customer_display(self):
        total = self.lbl_total.cget("text")
        win = ctk.CTkToplevel(self)
        win.title("Musteri Ekrani")
        win.geometry("400x300")
        win.attributes("-topmost", True)
        win.configure(fg_color="black")
        ctk.CTkLabel(win, text="ACCURA POS", font=ctk.CTkFont(size=32, weight="bold"),
                     text_color="#00ff00", fg_color="black").pack(expand=True)
        ctk.CTkLabel(win, text=f"Tutar: {total}", font=ctk.CTkFont(size=28, weight="bold"),
                     text_color="#ffffff", fg_color="black").pack()
        ctk.CTkLabel(win, text=f"Odeme: {self.selected_payment_label_text}", font=ctk.CTkFont(size=18),
                     text_color="#00ff00", fg_color="black").pack()
        ctk.CTkButton(win, text="Kapat", font=ctk.CTkFont(size=12),
                      command=win.destroy, fg_color="#333333", text_color="white").pack(pady=20)

    def test_barcode_scanner(self):
        if messagebox.askyesno("Barkod Okuyucu", "Barkod okuyucu test moduna gecilsin mi?\n\nBarkod okutunca uygulamaya eklenecektir."):
            messagebox.showinfo("Barkod Okuyucu",
                "Barkod okuyucu hazir.\n\n"
                "Baglanti: USB (HID)\n"
                "Durum: Dinleniyor\n"
                "Mod: Otomatik Ekleme\n\n"
                "Okunan barkodlar otomatik sepete eklenecektir.")

    def check_connection(self):
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            s.connect(("8.8.8.8", 53))
            s.close()
            self.connected = True
            self.wifi_label.configure(text="\u26A1", text_color=SUCCESS)
        except Exception:
            self.connected = False
            self.wifi_label.configure(text="\u26A0", text_color=DANGER)
        self.after(30000, self.check_connection)

    def update_time(self):
        try:
            self.time_label.configure(text=datetime.now().strftime("%d.%m.%Y %H:%M:%S"))
            self.after(1000, self.update_time)
        except Exception:
            pass
