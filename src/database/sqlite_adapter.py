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
        """

        try:
            cursor.executescript(tables)
            conn.commit()

            # Admin kullanıcısını ekle
            import hashlib
            cursor.execute("SELECT COUNT(*) as cnt FROM Users WHERE Username='admin'")
            if cursor.fetchone()[0] == 0:
                pw_hash = hashlib.sha256("admin123".encode()).hexdigest()
                cursor.execute("INSERT INTO Users (Username, PasswordHash, FullName, Role) VALUES (?, ?, ?, ?)",
                             ("admin", pw_hash, "Admin Kullanıcı", "Admin"))

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
