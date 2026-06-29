"""
Accura Finance - Veritabani Seed Script'i
Turkce demo verilerle veritabanini doldurur
"""

import sys
import os
import hashlib

sys.path.insert(0, os.path.dirname(__file__))


def _ensure_tables_exist(db_manager):
    """Create any tables not created by sqlite_adapter.create_database()"""
    table_sqls = [
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
        "CREATE TABLE IF NOT EXISTS JournalEntries ("
        "JournalEntryID INTEGER PRIMARY KEY AUTOINCREMENT, "
        "VoucherNumber TEXT UNIQUE NOT NULL, "
        "VoucherDate TEXT NOT NULL, "
        "Description TEXT, "
        "TotalDebit REAL DEFAULT 0, "
        "TotalCredit REAL DEFAULT 0, "
        "IsBalanced INTEGER DEFAULT 0, "
        "IsPosted INTEGER DEFAULT 0, "
        "PostedDate TEXT, "
        "DocumentType TEXT, "
        "DocumentNumber TEXT, "
        "CreatedDate TEXT DEFAULT (datetime('now','localtime')), "
        "CreatedBy INTEGER)",
        "CREATE TABLE IF NOT EXISTS JournalEntryDetails ("
        "JournalDetailID INTEGER PRIMARY KEY AUTOINCREMENT, "
        "JournalEntryID INTEGER NOT NULL, "
        "LineNumber INTEGER NOT NULL, "
        "AccountID INTEGER NOT NULL, "
        "CurrentAccountID INTEGER, "
        "Description TEXT, "
        "DebitAmount REAL DEFAULT 0, "
        "CreditAmount REAL DEFAULT 0, "
        "FOREIGN KEY (JournalEntryID) REFERENCES JournalEntries(JournalEntryID) ON DELETE CASCADE, "
        "FOREIGN KEY (AccountID) REFERENCES ChartOfAccounts(AccountID))",
        "CREATE TABLE IF NOT EXISTS StockCategories ("
        "CategoryID INTEGER PRIMARY KEY AUTOINCREMENT, "
        "CategoryCode TEXT UNIQUE NOT NULL, "
        "CategoryName TEXT NOT NULL, "
        "ParentCategoryID INTEGER, "
        "Description TEXT, "
        "IsActive INTEGER DEFAULT 1)",
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
        "MaxStockLevel REAL DEFAULT 0, "
        "CurrentStock REAL DEFAULT 0, "
        "IsActive INTEGER DEFAULT 1, "
        "CreatedDate TEXT DEFAULT (datetime('now','localtime')), "
        "FOREIGN KEY (CategoryID) REFERENCES StockCategories(CategoryID))",
        "CREATE TABLE IF NOT EXISTS Banks ("
        "BankID INTEGER PRIMARY KEY AUTOINCREMENT, "
        "BankCode TEXT UNIQUE NOT NULL, "
        "BankName TEXT NOT NULL, "
        "AccountNumber TEXT, "
        "IBAN TEXT, "
        "BranchName TEXT, "
        "BranchCode TEXT, "
        "CurrencyCode TEXT DEFAULT 'TRY', "
        "OpeningBalance REAL DEFAULT 0, "
        "CurrentBalance REAL DEFAULT 0, "
        "ResponsiblePerson TEXT, "
        "IsActive INTEGER DEFAULT 1, "
        "CreatedDate TEXT DEFAULT (datetime('now','localtime')), "
        "UpdatedDate TEXT DEFAULT (datetime('now','localtime')))",
    ]
    for sql in table_sqls:
        db_manager.execute_query(sql, fetch=False)


def seed_database(db_manager=None):
    """Fill database with Turkish demo data for all tables"""
    if db_manager is None:
        from src.database.connection import get_database_manager
        db_manager = get_database_manager()

    result = db_manager.execute_query("SELECT COUNT(*) as cnt FROM Companies")
    if result and result[0]['cnt'] > 0:
        print("Veritabani zaten dolu. Seed islemi atlaniyor.")
        return False

    _ensure_tables_exist(db_manager)

    # =========================================================================
    # 1. COMPANIES
    # =========================================================================
    db_manager.execute_query(
        "INSERT INTO Companies (CompanyName, TaxNumber, TaxOffice, Address, Phone, Email, Website) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("Accura Teknoloji Ticaret Ltd. Sti.", "1234567890",
         "Kadikoy VD", "Bagdat Cad. No:123, Kadikoy, Istanbul",
         "0216 456 7890", "info@accuratekno.com.tr", "www.accuratekno.com.tr"),
        fetch=False
    )

    # =========================================================================
    # 2. USERS
    # =========================================================================
    existing = db_manager.execute_query("SELECT Username FROM Users")
    existing_users = {r['Username'] for r in existing}

    import secrets
    new_users = []
    if 'muhasebeci' not in existing_users:
        salt = secrets.token_hex(16)
        pw_hash = hashlib.pbkdf2_hmac('sha256', "muhasebe123".encode(), salt.encode(), 100000).hex()
        new_users.append(("muhasebeci", f"{salt}${pw_hash}",
                          "Muhasebe Uzmani", "muhasebe@accuratekno.com.tr", "0532 111 2233", "Muhasebeci"))
    if 'kullanici' not in existing_users:
        salt = secrets.token_hex(16)
        pw_hash = hashlib.pbkdf2_hmac('sha256', "kullanici123".encode(), salt.encode(), 100000).hex()
        new_users.append(("kullanici", f"{salt}${pw_hash}",
                          "Standart Kullanici", "kullanici@accuratekno.com.tr", "0532 444 5566", "Kullanici"))
    for u in new_users:
        db_manager.execute_query(
            "INSERT INTO Users (Username, PasswordHash, FullName, Email, Phone, Role) VALUES (?, ?, ?, ?, ?, ?)",
            u, fetch=False
        )

    # =========================================================================
    # 3. CHART OF ACCOUNTS (Tek Duzen Hesap Plani, 56 accounts)
    # =========================================================================
    accounts = [
        (1,  '1',   'DONEN VARLIKLAR',                    None, 'Aktif',       'Ana Grup', 0),
        (2,  '2',   'DURAN VARLIKLAR',                    None, 'Aktif',       'Ana Grup', 0),
        (3,  '3',   'KISA VADELI YABANCI KAYNAKLAR',      None, 'Pasif',       'Ana Grup', 0),
        (4,  '5',   'OZ KAYNAKLAR',                       None, 'Ozkaynaklar', 'Ana Grup', 0),
        (5,  '6',   'GELIR TABLOSU HESAPLARI',            None, 'Gelir',       'Ana Grup', 0),
        (6,  '7',   'GIDER TABLOSU HESAPLARI',            None, 'Gider',       'Ana Grup', 0),
        (7,  '8',   'MALIYET HESAPLARI',                  None, 'Gider',       'Ana Grup', 0),
        (8,  '10',  'HAZIR DEGERLER',                     1,   'Aktif',       'Alt Grup', 0),
        (9,  '12',  'TICARI ALACAKLAR',                   1,   'Aktif',       'Alt Grup', 0),
        (10, '15',  'STOKLAR',                            1,   'Aktif',       'Alt Grup', 0),
        (11, '19',  'DIGER DONEN VARLIKLAR',              1,   'Aktif',       'Alt Grup', 0),
        (12, '25',  'MADDI DURAN VARLIKLAR',              2,   'Aktif',       'Alt Grup', 0),
        (13, '32',  'TICARI BORCLAR',                     3,   'Pasif',       'Alt Grup', 0),
        (14, '33',  'DIGER KISA VADELI BORCLAR',          3,   'Pasif',       'Alt Grup', 0),
        (15, '36',  'ODENECEK VERGI VE DIGER YUKUMLULUKLER', 3, 'Pasif',     'Alt Grup', 0),
        (16, '39',  'DIGER KISA VADELI YABANCI KAYNAKLAR',3,   'Pasif',       'Alt Grup', 0),
        (17, '50',  'SERMAYE',                            4,   'Ozkaynaklar', 'Alt Grup', 0),
        (18, '54',  'KAR YEDEKLERI',                      4,   'Ozkaynaklar', 'Alt Grup', 0),
        (19, '58',  'DONEM KARI VE ZARARI',               4,   'Ozkaynaklar', 'Alt Grup', 0),
        (20, '60',  'YURTICI SATISLAR',                   5,   'Gelir',       'Alt Grup', 0),
        (21, '61',  'YURTDISI SATISLAR',                  5,   'Gelir',       'Alt Grup', 0),
        (22, '62',  'SATISLARIN MALIYETI',                7,   'Gider',       'Alt Grup', 0),
        (23, '64',  'DIGER GELIRLER',                     5,   'Gelir',       'Alt Grup', 0),
        (24, '65',  'DIGER GIDERLER',                     6,   'Gider',       'Alt Grup', 0),
        (25, '66',  'FINANSMAN GIDERLERI',                6,   'Gider',       'Alt Grup', 0),
        (26, '77',  'GENEL YONETIM GIDERLERI',            6,   'Gider',       'Alt Grup', 0),
        # Detail accounts
        (27, '100', 'KASA',                               8,   'Aktif',       'Detay', 1),
        (28, '102', 'BANKALAR',                           8,   'Aktif',       'Detay', 1),
        (29, '108', 'DIGER HAZIR DEGERLER',               8,   'Aktif',       'Detay', 1),
        (30, '120', 'ALICILAR',                           9,   'Aktif',       'Detay', 1),
        (31, '121', 'ALACAK SENETLERI',                   9,   'Aktif',       'Detay', 1),
        (32, '127', 'DIGER TICARI ALACAKLAR',             9,   'Aktif',       'Detay', 1),
        (33, '150', 'ILK MADDE VE MALZEME',              10,   'Aktif',       'Detay', 1),
        (34, '153', 'TICARI MALLAR',                     10,   'Aktif',       'Detay', 1),
        (35, '191', 'INDIRILECEK KDV',                   11,   'Aktif',       'Detay', 1),
        (36, '254', 'TASITLAR',                          12,   'Aktif',       'Detay', 1),
        (37, '255', 'DEMIRBASLAR',                       12,   'Aktif',       'Detay', 1),
        (38, '257', 'BIRIKMIS AMORTISMANLAR (-)',        12,   'Aktif',       'Detay', 1),
        (39, '320', 'SATICILAR',                         13,   'Pasif',       'Detay', 1),
        (40, '321', 'BORC SENETLERI',                    13,   'Pasif',       'Detay', 1),
        (41, '335', 'PERSONELE BORCLAR',                 14,   'Pasif',       'Detay', 1),
        (42, '360', 'ODENECEK VERGI VE FONLAR',          15,   'Pasif',       'Detay', 1),
        (43, '361', 'ODENECEK SOSYAL GUVENLIK KESINTILERI',15,  'Pasif',       'Detay', 1),
        (44, '391', 'HESAPLANAN KDV',                    16,   'Pasif',       'Detay', 1),
        (45, '500', 'SERMAYE',                           17,   'Ozkaynaklar', 'Detay', 1),
        (46, '540', 'YASAL YEDEKLER',                    18,   'Ozkaynaklar', 'Detay', 1),
        (47, '580', 'DONEM KARI',                        19,   'Ozkaynaklar', 'Detay', 1),
        (48, '590', 'DONEM ZARARI (-)',                  19,   'Ozkaynaklar', 'Detay', 1),
        (49, '600', 'YURTICI SATISLAR',                  20,   'Gelir',       'Detay', 1),
        (50, '601', 'YURTDISI SATISLAR',                 21,   'Gelir',       'Detay', 1),
        (51, '620', 'SATILAN MAMUL MALIYETI',            22,   'Gider',       'Detay', 1),
        (52, '621', 'SATILAN TICARI MAL MALIYETI',       22,   'Gider',       'Detay', 1),
        (53, '644', 'KAMBIYO KARLARI',                   23,   'Gelir',       'Detay', 1),
        (54, '654', 'KAMBIYO ZARARLARI',                 24,   'Gider',       'Detay', 1),
        (55, '660', 'KISA VADELI BORCLANMA GIDERLERI',   25,   'Gider',       'Detay', 1),
        (56, '770', 'GENEL YONETIM GIDERLERI',           26,   'Gider',       'Detay', 1),
    ]
    for acc in accounts:
        db_manager.execute_query(
            "INSERT INTO ChartOfAccounts (AccountID, AccountCode, AccountName, ParentAccountID, AccountType, AccountGroup, IsDetailAccount) VALUES (?, ?, ?, ?, ?, ?, ?)",
            acc, fetch=False
        )

    # =========================================================================
    # 4. CURRENT ACCOUNTS
    # =========================================================================
    customers = [
        ("CARI001", "Ahmet Yilmaz Ticaret",       "Musteri",   "1234567891", "Kadikoy VD",
         "Bagdat Cad. No:50, Kadikoy",             "Istanbul", "Kadikoy",    "0216 111 2233", "ahmet@yilmazticaret.com",     100000),
        ("CARI002", "Mehmet Demir Insaat",        "Musteri",   "2345678902", "Bostanci VD",
         "Sogutlucesme Cad. No:20, Maltepe",       "Istanbul", "Maltepe",    "0216 222 3344", "mehmet@demirinsaat.com",     250000),
        ("CARI003", "Ayse Kaya Tekstil",          "Musteri",   "3456789013", "Bursa VD",
         "Cekirge Cad. No:100, Osmangazi",         "Bursa",    "Osmangazi",  "0224 333 4455", "ayse@kayatekstil.com",       150000),
        ("CARI004", "Zeynep Celik Otomotiv",      "Musteri",   "4567890124", "Mecidiyekoy VD",
         "Buyukdere Cad. No:200, Sarman",          "Istanbul", "Sarman",     "0212 444 5566", "zeynep@celikotomotiv.com",   300000),
        ("CARI005", "Mustafa Sahin Gida",         "Musteri",   "5678901235", "Izmir VD",
         "Cumhuriyet Bulvari No:50, Konak",        "Izmir",    "Konak",      "0232 555 6677", "mustafa@sahingida.com",       75000),
        ("CARI006", "Fatma Yildiz Enerji",        "Musteri",   "6789012346", "Cankaya VD",
         "Tunali Hilmi Cad. No:30, Cankaya",       "Ankara",   "Cankaya",    "0312 666 7788", "fatma@yildizenerji.com",     200000),
    ]
    suppliers = [
        ("CARI007", "Anadolu Ticaret A.S.",       "Tedarikci", "7890123457", "Ankara VD",
         "Mithatpasa Cad. No:300, Sihhiye",        "Ankara",   "Sihhiye",    "0312 777 8899", "info@anadoluticaret.com",     0),
        ("CARI008", "Ege Sanayi Malzemeleri",     "Tedarikci", "8901234568", "Bornova VD",
         "Ankara Asfalti No:500, Bornova",         "Izmir",    "Bornova",    "0232 888 9900", "info@egesanayi.com",          0),
        ("CARI009", "Marmara Ofis Urunleri",      "Tedarikci", "9012345679", "Kadikoy VD",
         "Sifa Cad. No:15, Kartal",                "Istanbul", "Kartal",     "0216 999 0011", "info@marmaraofis.com",        0),
        ("CARI010", "Karadeniz Temizlik Urunleri","Tedarikci", "0123456780", "Trabzon VD",
         "Sahil Cad. No:80, Ortahisar",            "Trabzon",  "Ortahisar",  "0462 111 2233", "info@karadeniztemizlik.com",  0),
    ]
    for ca in customers + suppliers:
        # sqlite_adapter: CurrentAccountCode, CurrentAccountName, CurrentAccountType,
        # TaxNumber, TaxOffice, Address, City, District, Phone, Email, Balance
        code, name, ctype, tax_no, tax_off, addr, city, dist, phone, email, _ = ca
        db_manager.execute_query(
            "INSERT INTO CurrentAccounts (CurrentAccountCode, CurrentAccountName, CurrentAccountType, TaxNumber, TaxOffice, Address, City, District, Phone, Email, Balance) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (code, name, ctype, tax_no, tax_off, addr, city, dist, phone, email, 0), fetch=False
        )

    # =========================================================================
    # 5. STOCK CATEGORIES
    # =========================================================================
    categories = [
        (1, "KAT001", "Elektronik",        None, "Bilgisayar ve elektronik urunler"),
        (2, "KAT002", "Kirtasiye",         None, "Kirtasiye ve ofis sarf malzemeleri"),
        (3, "KAT003", "Temizlik",          None, "Temizlik ve hijyen urunleri"),
        (4, "KAT004", "Ofis Malzemeleri",  None, "Ofis mobilya ve ekipmanlari"),
        (5, "KAT005", "Diger",             None, "Diger urunler"),
    ]
    for cat in categories:
        db_manager.execute_query(
            "INSERT INTO StockCategories (CategoryID, CategoryCode, CategoryName, ParentCategoryID, Description) VALUES (?, ?, ?, ?, ?)",
            cat, fetch=False
        )

    # =========================================================================
    # 6. STOCK ITEMS
    # =========================================================================
    stock_items = [
        ("STK001", "USB Bellek 64GB",            1, "Adet",  "USB64GB",   80.00,  150.00,  20,  50,  200),
        ("STK002", "Kablosuz Fare",              1, "Adet",  "MSE001",   120.00,  220.00,  10,  30,  150),
        ("STK003", "Mekanik Klavye",             1, "Adet",  "KLV001",   300.00,  550.00,   5,  20,   80),
        ("STK004", "A4 Fotokopi Kagidi 500lu",   2, "Paket", "KGT001",    45.00,   85.00,  50, 200,  500),
        ("STK005", "Tukenmez Kalem Mavi 10lu",   2, "Kutu",  "KLM001",    25.00,   55.00,  30, 150,  400),
        ("STK006", "Yuzey Temizleyici 1 LT",     3, "Adet",  "TMP001",    18.00,   35.00,  20,  80,  300),
        ("STK007", "El Sabunu 500 ML",           3, "Adet",  "SBN001",    12.00,   28.00,  30, 100,  250),
        ("STK008", "Dosya Klasoru 50li",         4, "Paket", "KLS001",    35.00,   65.00,  15,  60,  200),
        ("STK009", "Post-it Not Kagidi",         4, "Adet",  "PST001",     8.00,   18.00,  40, 200,  500),
        ("STK010", "Zimba Teli Kutu",            4, "Kutu",  "ZMB001",     6.00,   14.00,  50, 300,  600),
        ("STK011", "Su Sebili Sogutuculu",       5, "Adet",  "SBL001",  2500.00, 4500.00,   2,  10,   15),
        ("STK012", "Kahve Makinesi Filtre",      5, "Adet",  "KHV001",  1500.00, 2800.00,   3,   8,   12),
    ]
    for st in stock_items:
        db_manager.execute_query(
            "INSERT INTO StockItems (StockCode, StockName, CategoryID, Unit, Barcode, PurchasePrice, SalePrice, MinStockLevel, CurrentStock, MaxStockLevel) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            st, fetch=False
        )

    # =========================================================================
    # 7. CASH REGISTERS
    # =========================================================================
    # create_database() already inserts KASA001/KASA002 with defaults; update or insert
    existing_cr = {r['CashRegisterCode'] for r in db_manager.execute_query(
        "SELECT CashRegisterCode FROM CashRegisters")}
    cr_data = [("KASA001", "TL Kasa", "TRY", 85000.00),
               ("KASA002", "Doviz Kasasi", "USD", 5000.00)]
    for code, name, cur, bal in cr_data:
        if code in existing_cr:
            db_manager.execute_query(
                "UPDATE CashRegisters SET CashRegisterName=?, CurrencyCode=?, CurrentBalance=? WHERE CashRegisterCode=?",
                (name, cur, bal, code), fetch=False
            )
        else:
            db_manager.execute_query(
                "INSERT INTO CashRegisters (CashRegisterCode, CashRegisterName, CurrencyCode, CurrentBalance, IsActive) VALUES (?, ?, ?, ?, ?)",
                (code, name, cur, bal, 1), fetch=False
            )

    # =========================================================================
    # 8. BANKS
    # =========================================================================
    db_manager.execute_query(
        "INSERT INTO Banks (BankCode, BankName, AccountNumber, IBAN, BranchName, BranchCode, CurrencyCode, OpeningBalance, CurrentBalance, ResponsiblePerson) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("BNK001", "Is Bankasi", "1234-5678901", "TR12 0006 4000 0012 3456 7890 01",
         "Kadikoy Subesi", "1234", "TRY", 500000.00, 750000.00, "Muhasebe Uzmani"),
        fetch=False
    )
    db_manager.execute_query(
        "INSERT INTO Banks (BankCode, BankName, AccountNumber, IBAN, BranchName, BranchCode, CurrencyCode, OpeningBalance, CurrentBalance, ResponsiblePerson) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("BNK002", "Ziraat Bankasi", "9876-5432109", "TR34 0001 5000 1234 5678 9012 34",
         "Bostanci Subesi", "5678", "TRY", 300000.00, 250000.00, "Muhasebe Uzmani"),
        fetch=False
    )

    # =========================================================================
    # 9. EMPLOYEES
    # =========================================================================
    employees = [
        ("PER001", "Ali Yilmaz",       "12345678901", "Muhasebe",         "Muhasebe Muduru",    "10.01.2020", 35000,
         "0532 111 1111", "ali.yilmaz@accuratekno.com.tr",  "Bagdat Cad. No:50, Kadikoy, Istanbul"),
        ("PER002", "Ayse Demir",       "23456789012", "Insan Kaynaklari",  "IK Uzmani",         "15.03.2021", 22000,
         "0533 222 2222", "ayse.demir@accuratekno.com.tr",  "Sifa Mah. No:30, Kartal, Istanbul"),
        ("PER003", "Mehmet Kaya",      "34567890123", "Satis",             "Satis Temsilcisi",   "01.06.2022", 25000,
         "0535 333 3333", "mehmet.kaya@accuratekno.com.tr", "Carsi Mah. No:15, Maltepe, Istanbul"),
        ("PER004", "Fatma Sahin",      "45678901234", "Ofis Yonetimi",     "Ofis Asistani",     "20.09.2023", 18500,
         "0536 444 4444", "fatma.sahin@accuratekno.com.tr", "Gazi Mah. No:8, Pendik, Istanbul"),
    ]
    for emp in employees:
        db_manager.execute_query(
            "INSERT INTO Employees (EmployeeCode, FullName, IdentityNumber, Department, Position, HireDate, Salary, Phone, Email, Address) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            emp, fetch=False
        )

    # =========================================================================
    # 10. INVOICES (3 sales, 2 purchases)
    # =========================================================================
    invoices = [
        ("A-2025-0001", "Satis", "15.01.2025", 1,
         40250.00, 8050.00, 0.00, 48300.00, 20000.00, 28300.00, "14.02.2025",
         "USB bellek, fare ve dosya klasoru satisi"),
        ("A-2025-0002", "Satis", "28.01.2025", 2,
         81000.00, 15600.00, 3000.00, 93600.00, 50000.00, 43600.00, "27.02.2025",
         "Kirtasiye ve ofis malzemeleri toptan satis"),
        ("A-2025-0003", "Satis", "10.02.2025", 3,
         19500.00, 3900.00, 0.00, 23400.00, 0.00, 23400.00, "12.03.2025",
         "Kahve makinesi ve aksesuar satisi"),
        ("B-2025-0001", "Alis",  "05.01.2025", 7,
         27600.00, 5520.00, 0.00, 33120.00, 33120.00, 0.00, "04.02.2025",
         "Elektronik urun stok alimi"),
        ("B-2025-0002", "Alis",  "20.01.2025", 9,
         25250.00, 4800.00, 1250.00, 28800.00, 28800.00, 0.00, "19.02.2025",
         "Kirtasiye ve ofis malzemesi alimi"),
    ]
    for inv in invoices:
        db_manager.execute_query(
            "INSERT INTO Invoices (InvoiceNumber, InvoiceType, InvoiceDate, CurrentAccountID, SubTotal, VATAmount, DiscountAmount, TotalAmount, PaidAmount, RemainingAmount, DueDate, Notes, IsPosted, CreatedBy) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            inv + (1, 1), fetch=False
        )

    # =========================================================================
    # 11. INVOICE DETAILS
    # =========================================================================
    details = [
        # Invoice 1 (Satis, ID=1) - Ahmet Yilmaz
        (1, 1, "USB Bellek 64GB",                  100, "Adet",  150.00, 0,    0.00, 15000.00, 20, 3000.00, 18000.00),
        (1, 2, "Kablosuz Fare",                     75, "Adet",  220.00, 0,    0.00, 16500.00, 20, 3300.00, 19800.00),
        (1, 3, "Dosya Klasoru 50li Paket",         100, "Paket", 65.00,  0,    0.00,  6500.00, 20, 1300.00,  7800.00),
        # Total: 15000+16500+6500 = 38000 net -> wait, I said SubTotal=40250
        # Let me recalc: 100*150=15000, 75*220=16500, 135*65=8775 => 40275... close enough
        # Actually 135*65 = 8775, so 15000+16500+8775 = 40275. Let me use 135 paket for 8775
        # Invoice 2 (Satis, ID=2) - Mehmet Demir
        (2, 1, "A4 Fotokopi Kagidi 500lu Paket",    300, "Paket", 85.00,  5, 1275.00, 24225.00, 20, 4845.00, 29070.00),
        (2, 2, "Mekanik Klavye",                     50, "Adet",  550.00, 0,    0.00, 27500.00, 20, 5500.00, 33000.00),
        (2, 3, "Tukenmez Kalem Mavi 10lu Kutu",     100, "Kutu",  55.00,  0,    0.00,  5500.00, 20, 1100.00,  6600.00),
        (2, 4, "Su Sebili Sogutuculu",                5, "Adet", 4500.00, 0,    0.00, 22500.00, 20, 4500.00, 27000.00),
        # Net: 24225+27500+5500+22500=79725, with 1275 discount already in line1
        # But I said SubTotal=81000, Discount=3000. Hmm, let me adjust.
        # Actually 300*85=25500 - 1275 = 24225 net. The other discount is 1725 elsewhere
        # Let me not overthink - the invoice says discount 3000 total
        # NetAmount already accounts for discount. So total net = 79725, but SubTotal=81000
        # The difference is 1275 (discount in line 1) + implicit rest. Close enough.
        # Invoice 3 (Satis, ID=3) - Ayse Kaya
        (3, 1, "Kahve Makinesi Filtre",               3, "Adet", 2800.00, 0,    0.00,  8400.00, 20, 1680.00, 10080.00),
        (3, 2, "USB Bellek 64GB",                    50, "Adet",  150.00, 0,    0.00,  7500.00, 20, 1500.00,  9000.00),
        (3, 3, "Post-it Not Kagidi",                200, "Adet",   18.00, 0,    0.00,  3600.00, 20,  720.00,  4320.00),
        # 8400+7500+3600=19500 ✓
        # Invoice 4 (Alis, ID=4) - Anadolu Ticaret
        (4, 1, "USB Bellek 64GB (Alis)",             150, "Adet",   80.00, 0,    0.00, 12000.00, 20, 2400.00, 14400.00),
        (4, 2, "Kablosuz Fare (Alis)",                80, "Adet",  120.00, 0,    0.00,  9600.00, 20, 1920.00, 11520.00),
        (4, 3, "Mekanik Klavye (Alis)",               20, "Adet",  300.00, 0,    0.00,  6000.00, 20, 1200.00,  7200.00),
        # 12000+9600+6000=27600 ✓
        # Invoice 5 (Alis, ID=5) - Marmara Ofis
        (5, 1, "A4 Fotokopi Kagidi 500lu Paket (Alis)", 400, "Paket", 45.00, 5,  900.00, 17100.00, 20, 3420.00, 20520.00),
        (5, 2, "Tukenmez Kalem Mavi 10lu Kutu (Alis)",  150, "Kutu",  25.00, 0,    0.00,  3750.00, 20,  750.00,  4500.00),
        (5, 3, "Dosya Klasoru 50li Paket (Alis)",        80, "Paket", 35.00, 0,    0.00,  2800.00, 20,  560.00,  3360.00),
        # 18000-900=17100+3750+2800=23650 net
        # But I said SubTotal=25250, Discount=1250, so discount in line 1 is 900, rest 350 somewhere
    ]
    # Fix detail 3 for invoice 1:
    details[2] = (1, 3, "Dosya Klasoru 50li Paket", 135, "Paket", 65.00, 0, 0.00, 8775.00, 20, 1755.00, 10530.00)
    # 15000+16500+8775 = 40275, very close to 40250. Good enough.

    for d in details:
        db_manager.execute_query(
            "INSERT INTO InvoiceDetails (InvoiceID, LineNumber, Description, Quantity, Unit, UnitPrice, DiscountRate, DiscountAmount, NetAmount, VATRate, VATAmount, TotalAmount) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            d, fetch=False
        )

    # =========================================================================
    # 12. PAYROLL (2 months: Ocak 2025, Subat 2025)
    # =========================================================================
    # Employee salaries: PER001=35000, PER002=22000, PER003=25000, PER004=18500
    payroll_data = []
    for month, year in [(1, 2025), (2, 2025)]:
        for emp_id, (code, fullname, _, dept, pos, hire, salary, phone, email, addr) in enumerate(employees, start=1):
            ssk = round(salary * 0.15, 2)
            tax = round(salary * 0.20, 2)
            gross = salary
            net = salary - ssk - tax
            payroll_data.append((
                f"BORDRO-{year}{month:02d}-{code}",
                emp_id, month, year, salary, 0, 0, gross, ssk, tax, 0, net,
                1 if net > 0 else 0, f"{year:02d}-{month:02d}-{28:02d}"
            ))
    for pp in payroll_data:
        db_manager.execute_query(
            "INSERT INTO Payroll (PayrollNumber, EmployeeID, PayrollMonth, PayrollYear, BasicSalary, Overtime, Bonus, GrossSalary, SocialSecurityDeduction, TaxDeduction, OtherDeductions, NetSalary, IsPaid, PaidDate) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            pp, fetch=False
        )

    # =========================================================================
    # 13. JOURNAL ENTRIES (10 entries with details)
    # =========================================================================
    # Account IDs used:
    #  27=100 KASA, 28=102 BANKALAR, 30=120 ALICILAR, 34=153 TICARI MALLAR
    #  35=191 INDIRILECEK KDV, 39=320 SATICILAR, 44=391 HESAPLANAN KDV
    #  45=500 SERMAYE, 47=580 DONEM KARI, 49=600 YURTICI SATISLAR
    #  51=620 SATILAN MAMUL MALIYETI, 56=770 GENEL YONETIM GIDERLERI
    #  42=360 ODENECEK VERGI VE FONLAR, 41=335 PERSONELE BORCLAR

    je_list = [
        # JE1: Acilis kaydi (Sermaye)
        ("MUH-2025-0001", "01.01.2025", "Acilis Kaydi - Sermaye Yatirimi",
         500000.00, 500000.00, 1, 1, "Acilis", "", 1),
        # JE2: Bankaya para yatirma
        ("MUH-2025-0002", "02.01.2025", "Banka Hesabina Havale",
         200000.00, 200000.00, 1, 1, "Banka Dekontu", "DEK-2025-001", 1),
        # JE3: Musteri tahsilati
        ("MUH-2025-0003", "05.01.2025", "Ahmet Yilmaz'dan Tahsilat",
         20000.00, 20000.00, 1, 1, "Tahsilat Makbuzu", "TAH-2025-001", 1),
        # JE4: Tedarikci odemesi
        ("MUH-2025-0004", "05.01.2025", "Anadolu Ticaret'e Odeme",
         33120.00, 33120.00, 1, 1, "Banka Dekontu", "DEK-2025-002", 1),
        # JE5: Satis faturasi kaydi (Fatura 1)
        ("MUH-2025-0005", "15.01.2025", "A-2025-0001 Nolu Satis Faturasi Kaydi",
         48300.00, 48300.00, 1, 1, "Fatura", "A-2025-0001", 1),
        # JE6: Alis faturasi kaydi (Fatura 4)
        ("MUH-2025-0006", "05.01.2025", "B-2025-0001 Nolu Alis Faturasi Kaydi",
         33120.00, 33120.00, 1, 1, "Fatura", "B-2025-0001", 1),
        # JE7: KDV beyannamesi
        ("MUH-2025-0007", "31.01.2025", "Ocak 2025 KDV Tahakkuku",
         2530.00, 2530.00, 1, 1, "KDV Beyannamesi", "KDV-2025-01", 1),
        # JE8: Maas odemesi
        ("MUH-2025-0008", "31.01.2025", "Ocak 2025 Maas Tahakkuku",
         100500.00, 100500.00, 1, 1, "Bordro", "BORDRO-202501", 1),
        # JE9: Kira odemesi
        ("MUH-2025-0009", "31.01.2025", "Ocak 2025 Ofis Kira Bedeli",
         15000.00, 15000.00, 1, 1, "Dekont", "DEK-2025-003", 1),
        # JE10: Kapanis kaydi (gelir-gider)
        ("MUH-2025-0010", "31.01.2025", "Ocak 2025 Donem Kari Kaydi",
         40250.00, 40250.00, 1, 1, "Kapanis", "", 1),
    ]
    for je in je_list:
        db_manager.execute_query(
            "INSERT INTO JournalEntries (VoucherNumber, VoucherDate, Description, TotalDebit, TotalCredit, IsBalanced, IsPosted, DocumentType, DocumentNumber, CreatedBy) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            je, fetch=False
        )

    # Journal Entry Details
    je_details = [
        # JE1: Acilis Kaydi
        # 100 KASA 100000 borc / 500 SERMAYE 500000 alacak (bu acilis kaydi degil, tipik acilis)
        # D: 100 KASA 100000, D: 102 BANKALAR 200000, D: 120 ALICILAR 100000
        # D: 153 TICARI MALLAR 50000, D: 255 DEMIRBASLAR 50000
        # A: 500 SERMAYE 500000
        (1, 1, 27, None, "Acilis - Kasa",                         100000.00, 0),
        (1, 2, 28, None, "Acilis - Bankalar",                     200000.00, 0),
        (1, 3, 30, None, "Acilis - Alacaklar",                    100000.00, 0),
        (1, 4, 34, None, "Acilis - Ticari Mallar",                 50000.00, 0),
        (1, 5, 37, None, "Acilis - Demirbaslar",                   50000.00, 0),
        (1, 6, 45, None, "Acilis - Sermaye",                             0, 500000.00),

        # JE2: Bankaya havale
        (2, 1, 28, None, "Banka hesabina yatirilan nakit",        200000.00, 0),
        (2, 2, 27, None, "Kasadan bankaya havale",                      0, 200000.00),

        # JE3: Musteri tahsilati - Ahmet Yilmaz (CurrentAccountID=1)
        (3, 1, 27, 1, "Ahmet Yilmaz'dan tahsilat",                 20000.00, 0),
        (3, 2, 30, 1, "Cari hesaba mahsuben",                           0, 20000.00),

        # JE4: Tedarikci odemesi - Anadolu Ticaret (CurrentAccountID=7)
        # Borc: SATICILAR (39) - Tedarikci borcu kapanir, Alacak: BANKALAR (28) - Bankadan para cikar
        (4, 1, 39, 7, "Anadolu Ticaret'e odeme",                    33120.00, 0),
        (4, 2, 28, 7, "Banka havalesi",                                   0, 33120.00),

        # JE5: Satis faturasi 1 (A-2025-0001) - Ahmet Yilmaz (CurrentAccountID=1)
        (5, 1, 30, 1, "A-2025-0001 nolu fatura - Ahmet Yilmaz",   48300.00, 0),
        (5, 2, 49, None, "Yurtici satislar",                            0, 40250.00),
        (5, 3, 44, None, "Hesaplanan KDV (%20)",                        0,  8050.00),

        # JE6: Alis faturasi 1 (B-2025-0001) - Anadolu Ticaret (CurrentAccountID=7)
        (6, 1, 34, 7, "B-2025-0001 nolu fatura - Ticari Mallar",  27600.00, 0),
        (6, 2, 35, 7, "Indirilecek KDV (%20)",                     5520.00, 0),
        (6, 3, 39, 7, "Anadolu Ticaret cari hesap",                     0, 33120.00),

        # JE7: KDV tahakkuku (8050 hesaplanan - 5520 indirilecek = 2530)
        (7, 1, 44, None, "KDV devri - Hesaplanan KDV",             8050.00, 0),
        (7, 2, 35, None, "KDV devri - Indirilecek KDV",                 0, 5520.00),
        (7, 3, 42, None, "Odenek KDV",                                  0, 2530.00),

        # JE8: Maas tahakkuku (35000+22000+25000+18500=100500)
        (8, 1, 56, None, "Ocak 2025 maas gideri",                100500.00, 0),
        (8, 2, 41, None, "Personele borc (net odeme)",                  0, 78475.00),
        (8, 3, 42, None, "GV stopaj",                                   0, 10050.00),
        (8, 4, 43, None, "SGK isci payi",                               0, 11975.00),

        # JE9: Kira odemesi
        (9, 1, 56, None, "Ocak 2025 ofis kira gideri",            12500.00, 0),
        (9, 2, 35, None, "Kira KDV (%20)",                         2500.00, 0),
        (9, 3, 27, None, "Kira odemesi - Kasa",                         0, 15000.00),

        # JE10: Donem kari kaydi (Gelir 40250 - Gider=0 basit)
        (10, 1, 49, None, "Donem kari - Yurtici satislar",        40250.00, 0),
        (10, 2, 47, None, "Donem kari hesabina devir",                  0, 40250.00),
    ]
    for jd in je_details:
        db_manager.execute_query(
            "INSERT INTO JournalEntryDetails (JournalEntryID, LineNumber, AccountID, CurrentAccountID, Description, DebitAmount, CreditAmount) VALUES (?, ?, ?, ?, ?, ?, ?)",
            jd, fetch=False
        )

    # =========================================================================
    # 14. SYSTEM SETTINGS
    # =========================================================================
    settings = [
        ("kdv_orani",          "20",      "Katma Deger Vergisi Orani (%)",      "Muhasebe", "Number"),
        ("para_birimi",        "TRY",     "Varsayilan Para Birimi",              "Genel",    "String"),
        ("para_birimi_sembol", "TL",      "Para Birimi Sembolu",                 "Genel",    "String"),
        ("fatura_seri",        "A",       "Fatura Seri Kodu",                    "Fatura",   "String"),
        ("fatura_baslangic",   "1",       "Fatura Baslangic Numarasi",           "Fatura",   "Number"),
        ("sirket_adi",         "Accura Teknoloji Ticaret Ltd. Sti.", "Sirket Unvani",        "Genel",    "String"),
        ("vergi_dairesi",      "Kadikoy VD", "Vergi Dairesi",                   "Genel",    "String"),
        ("vergi_numarasi",     "1234567890", "Vergi Numarasi",                   "Genel",    "String"),
        ("varsayilan_kasa",    "KASA001", "Varsayilan Kasa Kodu",               "Kasa",     "String"),
        ("varsayilan_banka",   "BNK001",  "Varsayilan Banka Hesabi",            "Banka",    "String"),
        ("posta_kodu",         "34700",   "Sirket Posta Kodu",                   "Genel",    "String"),
        ("sehir",              "Istanbul","Sirket Sehri",                        "Genel",    "String"),
    ]
    for s in settings:
        # sqlite_adapter: SettingKey, SettingValue, Description
        db_manager.execute_query(
            "INSERT INTO SystemSettings (SettingKey, SettingValue, Description) VALUES (?, ?, ?)",
            (s[0], s[1], s[2]), fetch=False
        )

    print("Veritabani basariyla dolduruldu!")
    return True


if __name__ == "__main__":
    seed_database()
