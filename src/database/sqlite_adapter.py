"""
Accura Finance - SQLite Veritabanı Adaptörü
SQL Server olmayan sistemler için SQLite kullanır
"""

import sqlite3
import os
import logging
from datetime import datetime
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "accura_finance.db")

class SQLiteManager:
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.logger = self._setup_logger()

    def _setup_logger(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        return logging.getLogger("SQLite")

    def get_connection(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def create_database(self):
        """Tabloları oluştur"""
        conn = self.get_connection()
        cursor = conn.cursor()

        tables = """
        CREATE TABLE IF NOT EXISTS Companies (
            CompanyID INTEGER PRIMARY KEY AUTOINCREMENT,
            CompanyName TEXT NOT NULL,
            TaxNumber TEXT UNIQUE NOT NULL,
            TaxOffice TEXT,
            Address TEXT,
            Phone TEXT,
            Email TEXT,
            Website TEXT,
            LogoPath TEXT,
            CreatedDate TEXT DEFAULT (datetime('now','localtime')),
            UpdatedDate TEXT DEFAULT (datetime('now','localtime')),
            IsActive INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS Users (
            UserID INTEGER PRIMARY KEY AUTOINCREMENT,
            Username TEXT UNIQUE NOT NULL,
            PasswordHash TEXT NOT NULL,
            FullName TEXT NOT NULL,
            Email TEXT,
            Phone TEXT,
            Role TEXT NOT NULL DEFAULT 'Kullanici',
            IsActive INTEGER DEFAULT 1,
            LastLogin TEXT,
            CreatedDate TEXT DEFAULT (datetime('now','localtime')),
            CreatedBy INTEGER
        );

        CREATE TABLE IF NOT EXISTS Employees (
            EmployeeID INTEGER PRIMARY KEY AUTOINCREMENT,
            EmployeeCode TEXT UNIQUE NOT NULL,
            FullName TEXT NOT NULL,
            IdentityNumber TEXT UNIQUE,
            Department TEXT,
            Position TEXT,
            HireDate TEXT,
            Salary REAL DEFAULT 0,
            Phone TEXT,
            Email TEXT,
            Address TEXT,
            IsActive INTEGER DEFAULT 1,
            CreatedDate TEXT DEFAULT (datetime('now','localtime')),
            UpdatedDate TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS Payroll (
            PayrollID INTEGER PRIMARY KEY AUTOINCREMENT,
            PayrollNumber TEXT UNIQUE NOT NULL,
            EmployeeID INTEGER NOT NULL,
            PayrollMonth INTEGER NOT NULL,
            PayrollYear INTEGER NOT NULL,
            BasicSalary REAL DEFAULT 0,
            Overtime REAL DEFAULT 0,
            Bonus REAL DEFAULT 0,
            GrossSalary REAL DEFAULT 0,
            SocialSecurityDeduction REAL DEFAULT 0,
            TaxDeduction REAL DEFAULT 0,
            OtherDeductions REAL DEFAULT 0,
            NetSalary REAL DEFAULT 0,
            AttendanceDays INTEGER DEFAULT 0,
            IsPaid INTEGER DEFAULT 0,
            PaidDate TEXT,
            CreatedDate TEXT DEFAULT (datetime('now','localtime')),
            CreatedBy INTEGER,
            FOREIGN KEY (EmployeeID) REFERENCES Employees(EmployeeID)
        );

        CREATE TABLE IF NOT EXISTS CurrentAccounts (
            CurrentAccountID INTEGER PRIMARY KEY AUTOINCREMENT,
            CurrentAccountCode TEXT UNIQUE NOT NULL,
            CurrentAccountName TEXT NOT NULL,
            CurrentAccountType TEXT NOT NULL,
            TaxNumber TEXT,
            TaxOffice TEXT,
            Address TEXT,
            City TEXT,
            District TEXT,
            Phone TEXT,
            Email TEXT,
            IsActive INTEGER DEFAULT 1,
            Balance REAL DEFAULT 0,
            CreatedDate TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS Invoices (
            InvoiceID INTEGER PRIMARY KEY AUTOINCREMENT,
            InvoiceNumber TEXT UNIQUE NOT NULL,
            InvoiceType TEXT NOT NULL,
            InvoiceDate TEXT NOT NULL,
            CurrentAccountID INTEGER,
            SubTotal REAL DEFAULT 0,
            VATAmount REAL DEFAULT 0,
            DiscountAmount REAL DEFAULT 0,
            TotalAmount REAL DEFAULT 0,
            PaidAmount REAL DEFAULT 0,
            RemainingAmount REAL DEFAULT 0,
            DueDate TEXT,
            Notes TEXT,
            IsPosted INTEGER DEFAULT 0,
            CreatedDate TEXT DEFAULT (datetime('now','localtime')),
            CreatedBy INTEGER,
            FOREIGN KEY (CurrentAccountID) REFERENCES CurrentAccounts(CurrentAccountID)
        );

        CREATE TABLE IF NOT EXISTS InvoiceDetails (
            InvoiceDetailID INTEGER PRIMARY KEY AUTOINCREMENT,
            InvoiceID INTEGER NOT NULL,
            LineNumber INTEGER NOT NULL,
            Description TEXT NOT NULL,
            Quantity REAL NOT NULL,
            Unit TEXT,
            UnitPrice REAL NOT NULL,
            DiscountRate REAL DEFAULT 0,
            DiscountAmount REAL DEFAULT 0,
            NetAmount REAL NOT NULL,
            VATRate REAL DEFAULT 18,
            VATAmount REAL DEFAULT 0,
            TotalAmount REAL NOT NULL,
            FOREIGN KEY (InvoiceID) REFERENCES Invoices(InvoiceID) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS CashRegisters (
            CashRegisterID INTEGER PRIMARY KEY AUTOINCREMENT,
            CashRegisterCode TEXT UNIQUE NOT NULL,
            CashRegisterName TEXT NOT NULL,
            CurrencyCode TEXT DEFAULT 'TRY',
            CurrentBalance REAL DEFAULT 0,
            IsActive INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS CashMovements (
            CashMovementID INTEGER PRIMARY KEY AUTOINCREMENT,
            MovementNumber TEXT UNIQUE NOT NULL,
            MovementDate TEXT NOT NULL,
            CashRegisterID INTEGER,
            MovementType TEXT NOT NULL,
            Amount REAL NOT NULL,
            Description TEXT,
            CurrentAccountID INTEGER,
            CreatedDate TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (CashRegisterID) REFERENCES CashRegisters(CashRegisterID)
        );

        CREATE TABLE IF NOT EXISTS Attendance (
            AttendanceID INTEGER PRIMARY KEY AUTOINCREMENT,
            EmployeeID INTEGER NOT NULL,
            Date TEXT NOT NULL,
            DayType TEXT DEFAULT '1',
            Notes TEXT,
            UNIQUE(EmployeeID, Date),
            FOREIGN KEY (EmployeeID) REFERENCES Employees(EmployeeID)
        );

        CREATE TABLE IF NOT EXISTS SystemSettings (
            SettingID INTEGER PRIMARY KEY AUTOINCREMENT,
            SettingKey TEXT UNIQUE NOT NULL,
            SettingValue TEXT,
            Description TEXT,
            UpdatedDate TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS ChartOfAccounts (
            AccountID INTEGER PRIMARY KEY AUTOINCREMENT,
            AccountCode TEXT UNIQUE NOT NULL,
            AccountName TEXT NOT NULL,
            ParentAccountID INTEGER,
            AccountType TEXT NOT NULL,
            AccountGroup TEXT,
            IsDetailAccount INTEGER DEFAULT 0,
            IsActive INTEGER DEFAULT 1,
            FOREIGN KEY (ParentAccountID) REFERENCES ChartOfAccounts(AccountID)
        );

        CREATE TABLE IF NOT EXISTS StockCategories (
            CategoryID INTEGER PRIMARY KEY AUTOINCREMENT,
            CategoryCode TEXT UNIQUE NOT NULL,
            CategoryName TEXT NOT NULL,
            ParentCategoryID INTEGER,
            Description TEXT,
            IsActive INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS StockItems (
            StockID INTEGER PRIMARY KEY AUTOINCREMENT,
            StockCode TEXT UNIQUE NOT NULL,
            StockName TEXT NOT NULL,
            CategoryID INTEGER,
            Unit TEXT DEFAULT 'Adet',
            Barcode TEXT,
            PurchasePrice REAL DEFAULT 0,
            SalePrice REAL DEFAULT 0,
            VATRate REAL DEFAULT 18,
            MinStockLevel REAL DEFAULT 0,
            MaxStockLevel REAL DEFAULT 0,
            CurrentStock REAL DEFAULT 0,
            IsActive INTEGER DEFAULT 1,
            CreatedDate TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (CategoryID) REFERENCES StockCategories(CategoryID)
        );

        CREATE TABLE IF NOT EXISTS StockMovements (
            MovementID INTEGER PRIMARY KEY AUTOINCREMENT,
            StockID INTEGER NOT NULL,
            MovementDate TEXT NOT NULL,
            MovementType TEXT NOT NULL,
            Quantity REAL NOT NULL,
            UnitPrice REAL DEFAULT 0,
            TotalAmount REAL DEFAULT 0,
            DocumentNumber TEXT,
            Description TEXT,
            CreatedDate TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (StockID) REFERENCES StockItems(StockID)
        );

        CREATE TABLE IF NOT EXISTS Banks (
            BankID INTEGER PRIMARY KEY AUTOINCREMENT,
            BankCode TEXT UNIQUE NOT NULL,
            BankName TEXT NOT NULL,
            AccountNumber TEXT,
            IBAN TEXT,
            BranchName TEXT,
            BranchCode TEXT,
            CurrencyCode TEXT DEFAULT 'TRY',
            OpeningBalance REAL DEFAULT 0,
            CurrentBalance REAL DEFAULT 0,
            ResponsiblePerson TEXT,
            IsActive INTEGER DEFAULT 1,
            CreatedDate TEXT DEFAULT (datetime('now','localtime')),
            UpdatedDate TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS JournalEntries (
            JournalEntryID INTEGER PRIMARY KEY AUTOINCREMENT,
            VoucherNumber TEXT UNIQUE NOT NULL,
            VoucherDate TEXT NOT NULL,
            Description TEXT,
            TotalDebit REAL DEFAULT 0,
            TotalCredit REAL DEFAULT 0,
            IsBalanced INTEGER DEFAULT 0,
            IsPosted INTEGER DEFAULT 0,
            PostedDate TEXT,
            DocumentType TEXT,
            DocumentNumber TEXT,
            CreatedDate TEXT DEFAULT (datetime('now','localtime')),
            CreatedBy INTEGER
        );

        CREATE TABLE IF NOT EXISTS JournalEntryDetails (
            JournalDetailID INTEGER PRIMARY KEY AUTOINCREMENT,
            JournalEntryID INTEGER NOT NULL,
            LineNumber INTEGER NOT NULL,
            AccountID INTEGER NOT NULL,
            CurrentAccountID INTEGER,
            Description TEXT,
            DebitAmount REAL DEFAULT 0,
            CreditAmount REAL DEFAULT 0,
            FOREIGN KEY (JournalEntryID) REFERENCES JournalEntries(JournalEntryID) ON DELETE CASCADE,
            FOREIGN KEY (AccountID) REFERENCES ChartOfAccounts(AccountID)
        );

        CREATE TABLE IF NOT EXISTS Branches (
            BranchID INTEGER PRIMARY KEY AUTOINCREMENT,
            BranchCode TEXT UNIQUE NOT NULL,
            BranchName TEXT NOT NULL,
            Address TEXT,
            City TEXT,
            District TEXT,
            Phone TEXT,
            ManagerName TEXT,
            IsHeadOffice INTEGER DEFAULT 0,
            IsActive INTEGER DEFAULT 1,
            CreatedDate TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS BranchTransfers (
            TransferID INTEGER PRIMARY KEY AUTOINCREMENT,
            TransferCode TEXT UNIQUE NOT NULL,
            TransferDate TEXT NOT NULL,
            SourceBranchID INTEGER,
            TargetBranchID INTEGER,
            Status TEXT DEFAULT 'Hazirlaniyor',
            Notes TEXT,
            FOREIGN KEY (SourceBranchID) REFERENCES Branches(BranchID),
            FOREIGN KEY (TargetBranchID) REFERENCES Branches(BranchID),
            CreatedDate TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS Checks (
            CheckID INTEGER PRIMARY KEY AUTOINCREMENT,
            CheckNo TEXT NOT NULL,
            BankName TEXT NOT NULL,
            BankBranch TEXT,
            AccountNo TEXT,
            Amount REAL NOT NULL,
            CheckDate TEXT NOT NULL,
            MaturityDate TEXT NOT NULL,
            CurrentAccountID INTEGER,
            CheckType TEXT NOT NULL,
            CheckStatus TEXT DEFAULT 'Portfoyde',
            ReceivedDate TEXT,
            DeliveredDate TEXT,
            EndorsedTo TEXT,
            Description TEXT,
            FOREIGN KEY (CurrentAccountID) REFERENCES CurrentAccounts(CurrentAccountID),
            CreatedDate TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS CheckEndorsements (
            EndorsementID INTEGER PRIMARY KEY AUTOINCREMENT,
            CheckID INTEGER,
            EndorsementDate TEXT NOT NULL,
            EndorsedTo TEXT NOT NULL,
            EndorsementType TEXT,
            Amount REAL,
            Description TEXT,
            FOREIGN KEY (CheckID) REFERENCES Checks(CheckID) ON DELETE CASCADE,
            CreatedDate TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS BouncedChecks (
            BouncedID INTEGER PRIMARY KEY AUTOINCREMENT,
            CheckID INTEGER,
            ProtestDate TEXT NOT NULL,
            Reason TEXT,
            ProtestCost REAL DEFAULT 0,
            LegalProcessStarted INTEGER DEFAULT 0,
            LegalProcessNote TEXT,
            RecoveryAmount REAL DEFAULT 0,
            RecoveryDate TEXT,
            FOREIGN KEY (CheckID) REFERENCES Checks(CheckID),
            CreatedDate TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS CheckPortfolios (
            PortfolioID INTEGER PRIMARY KEY AUTOINCREMENT,
            PortfolioCode TEXT UNIQUE NOT NULL,
            PortfolioDate TEXT NOT NULL,
            PortfolioType TEXT,
            TotalCount INTEGER DEFAULT 0,
            TotalAmount REAL DEFAULT 0,
            Description TEXT,
            CreatedDate TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS POS_Sessions (
            SessionID INTEGER PRIMARY KEY AUTOINCREMENT,
            POSRegisterID INTEGER,
            UserID INTEGER,
            OpeningDate TEXT NOT NULL,
            ClosingDate TEXT,
            OpeningAmount REAL DEFAULT 0,
            ClosingAmount REAL DEFAULT 0,
            CashSales REAL DEFAULT 0,
            CreditSales REAL DEFAULT 0,
            TotalSales REAL DEFAULT 0,
            ReturnCount INTEGER DEFAULT 0,
            ReturnAmount REAL DEFAULT 0,
            DiscountAmount REAL DEFAULT 0,
            IsActive INTEGER DEFAULT 1,
            Status TEXT DEFAULT 'Acik',
            FOREIGN KEY (POSRegisterID) REFERENCES POSRegisters(POSRegisterID),
            FOREIGN KEY (UserID) REFERENCES Users(UserID)
        );

        CREATE TABLE IF NOT EXISTS POSReceipts (
            ReceiptID INTEGER PRIMARY KEY AUTOINCREMENT,
            ReceiptNumber TEXT UNIQUE NOT NULL,
            SessionID INTEGER,
            POSRegisterID INTEGER,
            BranchID INTEGER,
            UserID INTEGER,
            CurrentAccountID INTEGER,
            ReceiptDate TEXT NOT NULL,
            ReceiptType TEXT DEFAULT 'Satis',
            PaymentType TEXT DEFAULT 'Nakit',
            SubTotal REAL DEFAULT 0,
            DiscountAmount REAL DEFAULT 0,
            VATAmount REAL DEFAULT 0,
            TotalAmount REAL DEFAULT 0,
            PaidAmount REAL DEFAULT 0,
            ChangeAmount REAL DEFAULT 0,
            IsCancelled INTEGER DEFAULT 0,
            FOREIGN KEY (SessionID) REFERENCES POS_Sessions(SessionID),
            FOREIGN KEY (BranchID) REFERENCES Branches(BranchID),
            FOREIGN KEY (CurrentAccountID) REFERENCES CurrentAccounts(CurrentAccountID),
            CreatedDate TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS POSReceiptDetails (
            ReceiptDetailID INTEGER PRIMARY KEY AUTOINCREMENT,
            ReceiptID INTEGER NOT NULL,
            LineNumber INTEGER NOT NULL,
            StockID INTEGER,
            StockName TEXT NOT NULL,
            Barcode TEXT,
            Quantity REAL NOT NULL,
            UnitPrice REAL NOT NULL,
            DiscountRate REAL DEFAULT 0,
            DiscountAmount REAL DEFAULT 0,
            NetPrice REAL NOT NULL,
            VATRate REAL DEFAULT 18,
            VATAmount REAL DEFAULT 0,
            TotalAmount REAL NOT NULL,
            FOREIGN KEY (ReceiptID) REFERENCES POSReceipts(ReceiptID) ON DELETE CASCADE,
            FOREIGN KEY (StockID) REFERENCES StockItems(StockID)
        );

        CREATE TABLE IF NOT EXISTS ProductionRecipes (
            RecipeID INTEGER PRIMARY KEY AUTOINCREMENT,
            RecipeCode TEXT UNIQUE NOT NULL,
            RecipeName TEXT NOT NULL,
            ProductID INTEGER,
            Quantity REAL DEFAULT 1,
            Unit TEXT,
            TotalCost REAL DEFAULT 0,
            LaborCost REAL DEFAULT 0,
            OverheadCost REAL DEFAULT 0,
            Notes TEXT,
            IsActive INTEGER DEFAULT 1,
            FOREIGN KEY (ProductID) REFERENCES StockItems(StockID),
            CreatedDate TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS ProductionRecipeDetails (
            RecipeDetailID INTEGER PRIMARY KEY AUTOINCREMENT,
            RecipeID INTEGER NOT NULL,
            LineNumber INTEGER NOT NULL,
            RawMaterialID INTEGER,
            Quantity REAL NOT NULL,
            Unit TEXT,
            UnitCost REAL DEFAULT 0,
            TotalCost REAL DEFAULT 0,
            WasteRate REAL DEFAULT 0,
            FOREIGN KEY (RecipeID) REFERENCES ProductionRecipes(RecipeID) ON DELETE CASCADE,
            FOREIGN KEY (RawMaterialID) REFERENCES StockItems(StockID)
        );

        CREATE TABLE IF NOT EXISTS ProductionOrders (
            OrderID INTEGER PRIMARY KEY AUTOINCREMENT,
            OrderCode TEXT UNIQUE NOT NULL,
            OrderDate TEXT NOT NULL,
            RecipeID INTEGER,
            ProductID INTEGER,
            PlannedQuantity REAL NOT NULL,
            ProducedQuantity REAL DEFAULT 0,
            DefectQuantity REAL DEFAULT 0,
            UnitCost REAL DEFAULT 0,
            TotalCost REAL DEFAULT 0,
            Status TEXT DEFAULT 'Planlandi',
            StartDate TEXT,
            EndDate TEXT,
            Notes TEXT,
            FOREIGN KEY (RecipeID) REFERENCES ProductionRecipes(RecipeID),
            FOREIGN KEY (ProductID) REFERENCES StockItems(StockID),
            CreatedDate TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS CRM_Activities (
            ActivityID INTEGER PRIMARY KEY AUTOINCREMENT,
            ActivityDate TEXT NOT NULL,
            ActivityType TEXT,
            CurrentAccountID INTEGER,
            ContactPerson TEXT,
            Subject TEXT,
            Description TEXT,
            Status TEXT DEFAULT 'Planlandi',
            FollowUpDate TEXT,
            IsCompleted INTEGER DEFAULT 0,
            CompletedDate TEXT,
            FOREIGN KEY (CurrentAccountID) REFERENCES CurrentAccounts(CurrentAccountID),
            CreatedDate TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS BarcodeTemplates (
            TemplateID INTEGER PRIMARY KEY AUTOINCREMENT,
            TemplateName TEXT NOT NULL,
            LabelWidth REAL NOT NULL,
            LabelHeight REAL NOT NULL,
            FieldsConfiguration TEXT,
            PrinterName TEXT,
            IsDefault INTEGER DEFAULT 0,
            CreatedDate TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS SearchHistory (
            SearchID INTEGER PRIMARY KEY AUTOINCREMENT,
            UserID INTEGER,
            SearchTerm TEXT NOT NULL,
            Module TEXT,
            SearchedAt TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (UserID) REFERENCES Users(UserID)
        );

        CREATE TABLE IF NOT EXISTS AuditLog (
            AuditID INTEGER PRIMARY KEY AUTOINCREMENT,
            TableName TEXT NOT NULL,
            RecordID INTEGER,
            Action TEXT NOT NULL,
            UserID INTEGER,
            ActionDate TEXT DEFAULT (datetime('now','localtime')),
            NewValues TEXT,
            FOREIGN KEY (UserID) REFERENCES Users(UserID)
        );
        """

        try:
            cursor.executescript(tables)
            conn.commit()

            # Admin kullanıcısını ekle
            import hashlib
            import secrets
            cursor.execute("SELECT COUNT(*) as cnt FROM Users WHERE Username='admin'")
            if cursor.fetchone()[0] == 0:
                salt = secrets.token_hex(16)
                pw_hash = hashlib.pbkdf2_hmac('sha256', "admin123".encode(), salt.encode(), 100000).hex()
                cursor.execute("INSERT INTO Users (Username, PasswordHash, FullName, Role) VALUES (?, ?, ?, ?)",
                             ("admin", f"{salt}${pw_hash}", "Admin Kullanıcı", "Admin"))

            # Varsayılan kasa
            cursor.execute("SELECT COUNT(*) as cnt FROM CashRegisters WHERE CashRegisterCode='KASA001'")
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO CashRegisters (CashRegisterCode, CashRegisterName, CurrentBalance) VALUES (?, ?, ?)",
                             ("KASA001", "Ana Kasa", 50000))
                cursor.execute("INSERT INTO CashRegisters (CashRegisterCode, CashRegisterName, CurrentBalance) VALUES (?, ?, ?)",
                             ("KASA002", "Yedek Kasa", 10000))

            conn.commit()
            self.logger.info("Veritabanı başarıyla oluşturuldu")
            return True
        except Exception as e:
            self.logger.error(f"Veritabanı oluşturma hatası: {e}")
            return False
        finally:
            conn.close()

    def execute_query(self, query, params=None, fetch=True):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            if fetch and query.strip().upper().startswith("SELECT"):
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            else:
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            self.logger.error(f"Sorgu hatası: {e}")
            raise
        finally:
            conn.close()

    def test_connection(self):
        try:
            conn = self.get_connection()
            conn.execute("SELECT 1")
            conn.close()
            return True
        except:
            return False

_db_manager = None

def get_database_manager():
    global _db_manager
    if _db_manager is None:
        _db_manager = SQLiteManager()
    return _db_manager
