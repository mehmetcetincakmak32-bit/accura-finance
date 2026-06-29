import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, ttk
import sys
import os
from datetime import datetime, date
import threading
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.database.connection import get_database_manager
    from src.utils.config import ConfigManager
    from src.utils.logger import setup_logger
    from src.gui.login_window import LoginWindow
except ImportError as e:
    print(f"Modul import hatasi: {e}")
    try:
        import sys, os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
        from src.database.connection import get_database_manager
        from src.utils.config import ConfigManager
        from src.utils.logger import setup_logger
        from src.gui.login_window import LoginWindow
    except ImportError as e2:
        print(f"Alternatif import da basarisiz: {e2}")
        ConfigManager = None

DashboardFrame = None
AccountingFrame = None
InventoryFrame = None
CustomersFrame = None
ReportsFrame = None
SettingsFrame = None
POSFrame = None
PurchasingFrame = None
ProductionFrame = None
PriceGroupFrame = None
CampaignFrame = None
BranchFrame = None
CRMFrame = None
BarcodeFrame = None
OrderFrame = None
MarketplaceFrame = None
EInvoiceFrame = None
CostCenterFrame = None
CekFrame = None
BackupFrame = None
NotificationFrame = None

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

PRIMARY = "#1565c0"
PRIMARY_DARK = "#0d47a1"
PRIMARY_LIGHT = "#42a5f5"
SIDEBAR_BG = "#f8f9fa"
HEADER_BG = "#ffffff"
CARD_BG = "#ffffff"
SUCCESS = "#2e7d32"
DANGER = "#c62828"
WARNING = "#f57f17"
TEXT_DARK = "#1a1a2e"
TEXT_MUTED = "#6c757d"
BORDER = "#e8eaed"

class AccuraFinanceApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.current_user = None
        self.db_manager = None
        self.services = {}
        
        if ConfigManager is not None:
            self.config_manager = ConfigManager()
        else:
            self.config_manager = None
        
        self.logger = setup_logger('AccuraFinance') if 'setup_logger' in globals() else None
        
        self.setup_main_window()
        self.check_database_connection()
        self.init_services()
        self.show_login()
    
    def setup_main_window(self):
        self.root.title("Accura Finance - Profesyonel Muhasebe Çozumu v1.0")
        w = 1500; h = 950
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2; y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.minsize(1300, 850)
        self.root.state("normal")
        self.root.attributes("-topmost", True)
        self.root.after(200, lambda: (self.root.attributes("-topmost", False), self.root.lift(), self.root.focus_force()))
        
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        try:
            icon_path = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'icon.ico')
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except:
            pass
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.create_main_layout()
        self.hide_main_content()
    
    def create_main_layout(self):
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        
        self.create_toolbar()
        self.create_sidebar()
        self.create_main_content()
        self.create_status_bar()
    
    def create_toolbar(self):
        self.toolbar = ctk.CTkFrame(self.root, height=64, corner_radius=0, fg_color=HEADER_BG)
        self.toolbar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=0, pady=0)
        self.toolbar.grid_columnconfigure(1, weight=1)
        
        ctk.CTkFrame(self.toolbar, height=1, fg_color=BORDER).grid(row=1, column=0, columnspan=2, sticky="ew")
        
        title_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="w", padx=24, pady=12)
        
        logo_text = ctk.CTkLabel(
            title_frame, text="ACCURA", 
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=PRIMARY
        )
        logo_text.pack(side="left")
        
        logo_sub = ctk.CTkLabel(
            title_frame, text="FINANCE", 
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=PRIMARY_LIGHT
        )
        logo_sub.pack(side="left")
        
        badge = ctk.CTkLabel(
            title_frame, text="MUHASEBE", 
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color="white", fg_color=PRIMARY,
            corner_radius=4, width=60, height=18
        )
        badge.pack(side="left", padx=(10, 0))
        
        # Global arama cubugu
        search_frame = ctk.CTkFrame(self.toolbar, fg_color="#f0f2f5", corner_radius=8)
        search_frame.grid(row=0, column=1, padx=10, pady=12, sticky="ew")
        search_frame.grid_columnconfigure(0, weight=1)
        
        self.global_search_entry = ctk.CTkEntry(
            search_frame, placeholder_text="Tum modullerde ara (urun, cari, fatura, cek...)",
            height=32, fg_color="transparent", border_width=0,
            font=ctk.CTkFont(size=12)
        )
        self.global_search_entry.pack(side="left", fill="x", expand=True, padx=(8, 0))
        self.global_search_entry.bind("<Return>", lambda e: self.global_search())
        
        ctk.CTkButton(
            search_frame, text="Ara", width=50, height=28,
            font=ctk.CTkFont(size=11), fg_color=PRIMARY,
            corner_radius=6, command=self.global_search
        ).pack(side="right", padx=4, pady=2)
        
        self.user_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        self.user_frame.grid(row=0, column=2, sticky="e", padx=24, pady=12)
        
        self.user_label = ctk.CTkLabel(
            self.user_frame, text="", 
            font=ctk.CTkFont(size=12), text_color=TEXT_MUTED
        )
        self.user_label.pack(side="left", padx=(0, 12))
        
        self.logout_btn = ctk.CTkButton(
            self.user_frame, text="Cikis", width=80, height=32,
            command=self.logout, fg_color="transparent",
            text_color=TEXT_MUTED, hover_color="#fee2e2",
            border_width=1, border_color=BORDER,
            corner_radius=6, font=ctk.CTkFont(size=12)
        )
        self.logout_btn.pack(side="right")
    
    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self.root, width=240, corner_radius=0, fg_color=SIDEBAR_BG)
        self.sidebar.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(1, weight=1)
        
        # Sabit baslik
        header_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=60)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(20, 8))
        header_frame.grid_propagate(False)
        ctk.CTkLabel(
            header_frame, text="MENU", 
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=TEXT_MUTED
        ).pack()
        
        # Kaydirilabilir menu
        self.sidebar_scroll = ctk.CTkScrollableFrame(
            self.sidebar, fg_color="transparent",
            scrollbar_button_color=BORDER,
            scrollbar_button_hover_color=TEXT_MUTED
        )
        self.sidebar_scroll.grid(row=1, column=0, sticky="nsew")
        
        self.menu_buttons = {}
        
        self.ai_assistant_btn = ctk.CTkButton(
            self.sidebar_scroll, text="AI Asistan", width=210, height=42,
            anchor="w", font=ctk.CTkFont(size=13, weight="bold"),
            command=self.open_ai_assistant,
            fg_color="#7b1fa2", hover_color="#6a1b9a",
            corner_radius=8, image=None
        )
        self.ai_assistant_btn.pack(pady=(0, 8), padx=15)
        
        ctk.CTkFrame(self.sidebar_scroll, height=1, fg_color=BORDER).pack(fill="x", padx=15, pady=4)
        
        self.create_menu_buttons()
    
    def create_menu_buttons(self):
        s = self.sidebar_scroll
        # Ana modüller
        ctk.CTkLabel(
            s, text="ANA MODULLER",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=TEXT_MUTED
        ).pack(pady=(4, 2), padx=15, anchor="w")

        menu_font = ctk.CTkFont(size=14)
        menu_header_font = ctk.CTkFont(size=12, weight="bold")

        main_items = [
            ("Dashboard", "dashboard"),
            ("POS Satis", "pos"),
            ("Muhasebe", "accounting"),
            ("Cari Hesaplar", "customers"),
            ("Stok Yonetimi", "inventory"),
        ]

        for text, key in main_items:
            btn = ctk.CTkButton(
                s, text=text, width=210, height=40,
                anchor="w", font=menu_font,
                command=lambda k=key: self.show_module(k),
                fg_color="transparent",
                text_color=TEXT_DARK,
                hover_color="#e8eaf6",
                corner_radius=6
            )
            btn.pack(pady=2, padx=15)
            self.menu_buttons[key] = btn

        ctk.CTkFrame(s, height=1, fg_color=BORDER).pack(fill="x", padx=15, pady=4)

        # Ticari İşlemler
        ctk.CTkLabel(
            s, text="TICARI ISLEMLER",
            font=menu_header_font,
            text_color=TEXT_MUTED
        ).pack(pady=(4, 2), padx=15, anchor="w")

        trade_items = [
            ("Faturalar", "invoices"),
            ("Satinalma", "purchasing"),
            ("Siparisler", "orders"),
            ("Kasa & Banka", "cashbank"),
        ]

        for text, key in trade_items:
            btn = ctk.CTkButton(
                s, text=text, width=210, height=40,
                anchor="w", font=menu_font,
                command=lambda k=key: self.show_module(k),
                fg_color="transparent",
                text_color=TEXT_DARK,
                hover_color="#e8eaf6",
                corner_radius=6
            )
            btn.pack(pady=2, padx=15)
            self.menu_buttons[key] = btn

        ctk.CTkFrame(s, height=1, fg_color=BORDER).pack(fill="x", padx=15, pady=4)

        # Üretim ve Envanter
        ctk.CTkLabel(
            s, text="URETIM & ENVANTER",
            font=menu_header_font,
            text_color=TEXT_MUTED
        ).pack(pady=(4, 2), padx=15, anchor="w")

        inv_items = [
            ("Uretim", "production"),
            ("Fiyat Gruplari", "pricegroups"),
            ("Kampanyalar", "campaigns"),
            ("Barkod Islemleri", "barcode"),
        ]

        for text, key in inv_items:
            btn = ctk.CTkButton(
                s, text=text, width=210, height=40,
                anchor="w", font=menu_font,
                command=lambda k=key: self.show_module(k),
                fg_color="transparent",
                text_color=TEXT_DARK,
                hover_color="#e8eaf6",
                corner_radius=6
            )
            btn.pack(pady=2, padx=15)
            self.menu_buttons[key] = btn

        ctk.CTkFrame(s, height=1, fg_color=BORDER).pack(fill="x", padx=15, pady=4)

        # Yönetim
        ctk.CTkLabel(
            s, text="YONETIM",
            font=menu_header_font,
            text_color=TEXT_MUTED
        ).pack(pady=(4, 2), padx=15, anchor="w")

        mgmt_items = [
            ("Subeler", "branches"),
            ("CRM", "crm"),
            ("Personel", "personnel"),
            ("Masraf Merkezleri", "costcenters"),
        ]

        for text, key in mgmt_items:
            btn = ctk.CTkButton(
                s, text=text, width=210, height=40,
                anchor="w", font=menu_font,
                command=lambda k=key: self.show_module(k),
                fg_color="transparent",
                text_color=TEXT_DARK,
                hover_color="#e8eaf6",
                corner_radius=6
            )
            btn.pack(pady=2, padx=15)
            self.menu_buttons[key] = btn

        ctk.CTkFrame(s, height=1, fg_color=BORDER).pack(fill="x", padx=15, pady=4)

        # Entegrasyonlar
        ctk.CTkLabel(
            s, text="ENTEGRASYONLAR",
            font=menu_header_font,
            text_color=TEXT_MUTED
        ).pack(pady=(4, 2), padx=15, anchor="w")

        integ_items = [
            ("Cek Modulu", "cek"),
            ("e-Fatura/e-Defter", "einvoice"),
            ("Pazaryerleri", "marketplace"),
            ("Raporlar", "reports"),
            ("Ayarlar", "settings"),
        ]

        for text, key in integ_items:
            btn = ctk.CTkButton(
                s, text=text, width=210, height=40,
                anchor="w", font=menu_font,
                command=lambda k=key: self.show_module(k),
                fg_color="transparent",
                text_color=TEXT_DARK,
                hover_color="#e8eaf6",
                corner_radius=6
            )
            btn.pack(pady=2, padx=15)
            self.menu_buttons[key] = btn

        ctk.CTkFrame(s, height=1, fg_color=BORDER).pack(fill="x", padx=15, pady=4)

        # Sistem
        ctk.CTkLabel(
            s, text="SISTEM",
            font=menu_header_font,
            text_color=TEXT_MUTED
        ).pack(pady=(4, 2), padx=15, anchor="w")

        system_items = [
            ("Veri Yedekleme", "backup"),
            ("Bildirim Ayarlari", "notifications"),
        ]

        for text, key in system_items:
            btn = ctk.CTkButton(
                s, text=text, width=210, height=40,
                anchor="w", font=menu_font,
                command=lambda k=key: self.show_module(k),
                fg_color="transparent",
                text_color=TEXT_DARK,
                hover_color="#e8eaf6",
                corner_radius=6
            )
            btn.pack(pady=2, padx=15)
            self.menu_buttons[key] = btn
    
    def create_main_content(self):
        self.main_frame = ctk.CTkFrame(self.root, corner_radius=0, fg_color="#f4f6f8")
        self.main_frame.grid(row=1, column=1, sticky="nsew", padx=0, pady=0)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        
        self.content_frames = {}
        self.create_dashboard_frame()
    
    def create_dashboard_frame(self):
        if 'dashboard' not in self.content_frames:
            try:
                from src.gui.dashboard import DashboardFrame
                self.content_frames['dashboard'] = DashboardFrame(self.main_frame, self)
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Dashboard olusturma hatasi: {e}")
                frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
                label = ctk.CTkLabel(
                    frame, text="Dashboard yuklenemedi", font=ctk.CTkFont(size=14), text_color=TEXT_MUTED
                )
                label.pack(expand=True)
                self.content_frames['dashboard'] = frame
    
    def create_status_bar(self):
        self.status_bar = ctk.CTkFrame(self.root, height=28, corner_radius=0, fg_color=SIDEBAR_BG)
        self.status_bar.grid(row=2, column=0, columnspan=2, sticky="ew", padx=0, pady=0)
        self.status_bar.grid_columnconfigure(1, weight=1)
        
        ctk.CTkFrame(self.status_bar, height=1, fg_color=BORDER).grid(row=0, column=0, columnspan=2, sticky="ew")
        
        self.status_label = ctk.CTkLabel(
            self.status_bar, text="Hazir", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED
        )
        self.status_label.grid(row=1, column=0, sticky="w", padx=16, pady=3)
        
        self.datetime_label = ctk.CTkLabel(
            self.status_bar, text="", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED
        )
        self.datetime_label.grid(row=1, column=1, sticky="e", padx=16, pady=3)
        
        self.update_datetime()
    
    def update_datetime(self):
        current_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        try:
            self.datetime_label.configure(text=current_time)
        except:
            pass
        try:
            self.root.after(1000, self.update_datetime)
        except:
            pass
    
    def check_database_connection(self):
        try:
            if 'get_database_manager' in globals():
                self.db_manager = get_database_manager()
                
                if not self.db_manager.create_database_if_not_exists():
                    self.show_error("Veritabani olusturulamadi!")
                    return False
                
                if not self.db_manager.test_connection():
                    self.show_error("Veritabani baglantisi basarisiz!")
                    return False
                
                self.initialize_database()
                
                if self.logger:
                    self.logger.info("Veritabani baglantisi basarili")
                return True
            else:
                self.db_manager = None
                return False
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Veritabani baglanti hatasi: {e}")
            self.show_error(f"Veritabani hatasi: {e}")
            return False
    
    def init_services(self):
        try:
            from src.services.db_service import BaseDBService
            from src.services.report_service import ReportService
            from src.services.backup_service import BackupService
            from src.services.notification_service import NotificationService
            from src.services.search_service import SearchService
            self.services['db'] = BaseDBService(self.db_manager)
            self.services['report'] = ReportService()
            self.services['backup'] = BackupService(self.db_manager)
            self.services['notification'] = NotificationService(self.db_manager)
            self.services['search'] = SearchService(self.db_manager)
            if self.logger:
                self.logger.info("Servis katmani baslatildi")
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Servis katmani baslatilamadi: {e}")
    
    def initialize_database(self):
        try:
            script_dir = os.path.join(os.path.dirname(__file__), '..', 'database')
            
            tables_script = os.path.join(script_dir, 'create_tables.sql')
            if os.path.exists(tables_script):
                try:
                    self.db_manager.execute_script(tables_script)
                    if self.logger:
                        self.logger.info("Veritabani tablolari kontrol edildi")
                except Exception as e:
                    pass
            
            data_script = os.path.join(script_dir, 'initial_data.sql')
            if os.path.exists(data_script):
                try:
                    result = self.db_manager.execute_query(
                        "SELECT COUNT(*) as count FROM Users WHERE Username = 'admin'"
                    )
                    if result and result[0]['count'] == 0:
                        self.db_manager.execute_script(data_script)
                        if self.logger:
                            self.logger.info("Baslangic verileri eklendi")
                    else:
                        pass
                except Exception as e:
                    pass
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Veritabani baslatma hatasi: {e}")
    
    def show_login(self):
        self.login_window = LoginWindow(self.root, self.on_login_success)
    
    def on_login_success(self, user_data):
        self.current_user = user_data
        self.user_label.configure(text=f"Hos geldiniz, {user_data['FullName']}")
        self.show_main_content()
        self.show_module('dashboard')
        self.status_label.configure(text="Giris basarili")
        if self.logger:
            self.logger.info(f"Kullanici giris yapti: {user_data['Username']}")
    
    def show_main_content(self):
        self.sidebar.grid(row=1, column=0, sticky="nsew")
        self.main_frame.grid(row=1, column=1, sticky="nsew")
    
    def hide_main_content(self):
        self.sidebar.grid_remove()
        self.main_frame.grid_remove()
    
    def show_module(self, module_key):
        for frame in self.content_frames.values():
            frame.pack_forget()
        
        if module_key not in self.content_frames:
            self.create_content_frame(module_key)
        
        if module_key in self.content_frames:
            self.content_frames[module_key].pack(fill="both", expand=True, padx=10, pady=10)
            self.status_label.configure(text=f"{module_key.title()} modulu acildi")
        
        self.update_menu_selection(module_key)
    
    def open_ai_assistant(self):
        try:
            from src.gui.ai_assistant import AIAssistantFrame
            ai_window = ctk.CTkToplevel(self.root)
            ai_window.title("AI Muhasebe Asistani")
            ai_window.geometry("800x600")
            AIAssistantFrame(ai_window, self)
        except Exception as e:
            self.show_error(f"AI Asistan acilamadi: {e}")
    
    def create_content_frame(self, module_key):
        try:
            if module_key == 'dashboard':
                from src.gui.dashboard import DashboardFrame
                self.content_frames[module_key] = DashboardFrame(self.main_frame, self)
            elif module_key == 'accounting':
                from src.gui.accounting import AccountingFrame
                self.content_frames[module_key] = AccountingFrame(self.main_frame, self)
            elif module_key == 'customers':
                from src.gui.customers import CustomersFrame
                self.content_frames[module_key] = CustomersFrame(self.main_frame, self)
            elif module_key == 'inventory':
                from src.gui.inventory import InventoryFrame
                self.content_frames[module_key] = InventoryFrame(self.main_frame, self)
            elif module_key == 'cek':
                from src.gui.cek import CekFrame
                self.content_frames[module_key] = CekFrame(self.main_frame, self)
            elif module_key == 'barcode':
                from src.gui.barcode import BarcodeFrame
                self.content_frames[module_key] = BarcodeFrame(self.main_frame, self)
            elif module_key == 'orders':
                from src.gui.orders import OrdersFrame
                self.content_frames[module_key] = OrdersFrame(self.main_frame, self)
            elif module_key == 'marketplace':
                from src.gui.marketplace import MarketplaceFrame
                self.content_frames[module_key] = MarketplaceFrame(self.main_frame, self)
            elif module_key == 'einvoice':
                from src.gui.einvoice import EInvoiceFrame
                self.content_frames[module_key] = EInvoiceFrame(self.main_frame, self)
            elif module_key == 'costcenters':
                from src.gui.cost_centers import CostCentersFrame
                self.content_frames[module_key] = CostCentersFrame(self.main_frame, self)
            elif module_key == 'invoices':
                from src.gui.invoices import InvoicesFrame
                self.content_frames[module_key] = InvoicesFrame(self.main_frame, self)
            elif module_key == 'personnel':
                from src.gui.personnel import PersonnelFrame
                self.content_frames[module_key] = PersonnelFrame(self.main_frame, self)
            elif module_key == 'cashbank':
                from src.gui.cashbank import CashBankFrame
                self.content_frames[module_key] = CashBankFrame(self.main_frame, self)
            elif module_key == 'reports':
                from src.gui.reports import ReportsFrame
                self.content_frames[module_key] = ReportsFrame(self.main_frame, self)
            elif module_key == 'settings':
                from src.gui.settings import SettingsFrame
                self.content_frames[module_key] = SettingsFrame(self.main_frame, self)
            elif module_key == 'pos':
                from src.gui.pos import POSFrame
                self.content_frames[module_key] = POSFrame(self.main_frame, self)
            elif module_key == 'purchasing':
                from src.gui.purchasing import PurchasingFrame
                self.content_frames[module_key] = PurchasingFrame(self.main_frame, self)
            elif module_key == 'production':
                from src.gui.production import ProductionFrame
                self.content_frames[module_key] = ProductionFrame(self.main_frame, self)
            elif module_key == 'pricegroups':
                from src.gui.price_groups import PriceGroupsFrame
                self.content_frames[module_key] = PriceGroupsFrame(self.main_frame, self)
            elif module_key == 'campaigns':
                from src.gui.campaigns import CampaignsFrame
                self.content_frames[module_key] = CampaignsFrame(self.main_frame, self)
            elif module_key == 'branches':
                from src.gui.branches import BranchesFrame
                self.content_frames[module_key] = BranchesFrame(self.main_frame, self)
            elif module_key == 'crm':
                from src.gui.crm import CRMFrame
                self.content_frames[module_key] = CRMFrame(self.main_frame, self)
            elif module_key == 'backup':
                from src.gui.backup import BackupFrame
                self.content_frames[module_key] = BackupFrame(self.main_frame, self)
            elif module_key == 'notifications':
                from src.gui.notifications import NotificationSettingsFrame
                self.content_frames[module_key] = NotificationSettingsFrame(self.main_frame, self)
            else:
                frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
                label = ctk.CTkLabel(
                    frame, text=f"{module_key.upper()} MODULU - Gelistirme asamasinda",
                    font=ctk.CTkFont(size=14), text_color=TEXT_MUTED
                )
                label.pack(expand=True)
                self.content_frames[module_key] = frame

        except Exception as e:
            if self.logger:
                self.logger.error(f"Modul olusturma hatasi ({module_key}): {e}")
            frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
            label = ctk.CTkLabel(
                frame, text=f"HATA: {module_key} modulu yuklenemedi\n{str(e)}",
                font=ctk.CTkFont(size=12), text_color=DANGER
            )
            label.pack(expand=True)
            self.content_frames[module_key] = frame
    
    def update_menu_selection(self, selected_key):
        for key, button in self.menu_buttons.items():
            if key == selected_key:
                button.configure(
                    fg_color=PRIMARY, text_color="white",
                    hover_color=PRIMARY_DARK
                )
            else:
                button.configure(
                    fg_color="transparent", text_color=TEXT_DARK,
                    hover_color="#e8eaf6"
                )
    
    def logout(self):
        if messagebox.askyesno("Cikis", "Oturumu kapatmak istediginizden emin misiniz?"):
            self.current_user = None
            self.user_label.configure(text="")
            self.hide_main_content()
            self.show_login()
            self.status_label.configure(text="Cikis yapildi")
            if self.logger:
                self.logger.info("Kullanici cikis yapti")
    
    def on_closing(self):
        try:
            self.root.destroy()
        except:
            os._exit(0)
    
    def global_search(self):
        term = self.global_search_entry.get().strip()
        if not term:
            return
        try:
            search_svc = self.services.get('search')
            if search_svc:
                results = search_svc.global_search(term)
                count = results.get('total', 0) if isinstance(results, dict) and 'total' in results else sum(len(v) for v in results.values()) if isinstance(results, dict) else 0
                self.show_info(f"Arama sonucu: {count} kayit bulundu.\n\nEn hizli erisim icin ilgili modulu acin.")
            else:
                # Servis yoksa modul adi eslesmesi dene
                module_map = {
                    'urun': 'inventory', 'stok': 'inventory', 'mal': 'inventory',
                    'cari': 'customers', 'musteri': 'customers', 'tedarik': 'customers',
                    'fatura': 'invoices', 'satis': 'invoices',
                    'cek': 'cek', 'banka': 'cashbank', 'kasa': 'cashbank',
                    'personel': 'personnel', 'maas': 'personnel',
                    'rapor': 'reports', 'mizan': 'reports', 'bilanco': 'reports',
                    'pos': 'pos', 'satis noktasi': 'pos',
                    'uretim': 'production', 'recelte': 'production',
                    'sube': 'branches', 'masraf': 'costcenters',
                    'kampanya': 'campaigns', 'fiyat': 'pricegroups',
                    'barkod': 'barcode', 'siparis': 'orders',
                    'pazaryeri': 'marketplace', 'efatura': 'einvoice',
                    'yedek': 'backup', 'bildirim': 'notifications',
                }
                for keyword, mod in module_map.items():
                    if keyword in term.lower():
                        self.show_module(mod)
                        self.status_label.configure(text=f"Arama: '{term}' -> {mod} modulu acildi")
                        return
                self.show_info(f"'{term}' icin sonuc bulunamadi. Modul adiyla aramayi deneyin.")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Arama hatasi: {e}")
    
    def show_error(self, message):
        messagebox.showerror("Hata", message)
    
    def show_info(self, message):
        messagebox.showinfo("Bilgi", message)
    
    def show_warning(self, message):
        messagebox.showwarning("Uyari", message)
    
    def run(self):
        if self.logger:
            self.logger.info("Accura Finance uygulamasi baslatiliyor")
        try:
            self.root.mainloop()
        except Exception as e:
            if self.logger:
                self.logger.error(f"Ana dongu hatasi: {e}")

def main():
    try:
        app = AccuraFinanceApp()
        app.run()
    except Exception as e:
        try:
            messagebox.showerror("Kritik Hata", f"Uygulama baslatilamadi:\n{e}")
        except:
            print(f"Kritik hata: {e}")

if __name__ == "__main__":
    main()
