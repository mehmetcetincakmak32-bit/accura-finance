"""
Accura Finance - Veritabanı Modelleri
SQLAlchemy ORM modelleri
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Numeric, Date, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func
from datetime import datetime, date
import hashlib
import secrets

Base = declarative_base()

class Company(Base):
    __tablename__ = 'Companies'
    
    CompanyID = Column(Integer, primary_key=True, autoincrement=True)
    CompanyName = Column(String(200), nullable=False)
    TaxNumber = Column(String(50), unique=True, nullable=False)
    TaxOffice = Column(String(100))
    Address = Column(String(500))
    Phone = Column(String(50))
    Email = Column(String(100))
    Website = Column(String(100))
    LogoPath = Column(String(500))
    CreatedDate = Column(DateTime, default=func.now())
    UpdatedDate = Column(DateTime, default=func.now(), onupdate=func.now())
    IsActive = Column(Boolean, default=True)

class User(Base):
    __tablename__ = 'Users'
    
    UserID = Column(Integer, primary_key=True, autoincrement=True)
    Username = Column(String(50), unique=True, nullable=False)
    PasswordHash = Column(String(255), nullable=False)
    FullName = Column(String(100), nullable=False)
    Email = Column(String(100))
    Phone = Column(String(50))
    Role = Column(String(50), nullable=False)  # Admin, Muhasebeci, Kullanici
    IsActive = Column(Boolean, default=True)
    LastLogin = Column(DateTime)
    CreatedDate = Column(DateTime, default=func.now())
    CreatedBy = Column(Integer, ForeignKey('Users.UserID'))
    
    # Relationships
    creator = relationship("User", remote_side=[UserID])
    
    def set_password(self, password):
        """Şifreyi hash'le ve kaydet (PBKDF2-SHA256)"""
        salt = secrets.token_hex(16)
        pw_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
        self.PasswordHash = f"{salt}${pw_hash}"
    
    def check_password(self, password):
        """Şifreyi kontrol et"""
        stored = self.PasswordHash
        if "$" in stored:
            salt, expected = stored.split("$", 1)
            computed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
            return computed == expected
        else:
            # Eski SHA256 formatı için geriye uyumluluk
            return self.PasswordHash == hashlib.sha256(password.encode()).hexdigest()

class ChartOfAccount(Base):
    __tablename__ = 'ChartOfAccounts'
    
    AccountID = Column(Integer, primary_key=True, autoincrement=True)
    AccountCode = Column(String(20), unique=True, nullable=False)
    AccountName = Column(String(200), nullable=False)
    ParentAccountID = Column(Integer, ForeignKey('ChartOfAccounts.AccountID'))
    AccountType = Column(String(50), nullable=False)  # Aktif, Pasif, Gelir, Gider, Özkaynaklar
    AccountGroup = Column(String(100))
    IsDetailAccount = Column(Boolean, default=False)
    CurrencyCode = Column(String(3), default='TRY')
    IsActive = Column(Boolean, default=True)
    CreatedDate = Column(DateTime, default=func.now())
    UpdatedDate = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    parent = relationship("ChartOfAccount", remote_side=[AccountID])
    children = relationship("ChartOfAccount")
    journal_details = relationship("JournalEntryDetail", back_populates="account")

class CurrentAccount(Base):
    __tablename__ = 'CurrentAccounts'
    
    CurrentAccountID = Column(Integer, primary_key=True, autoincrement=True)
    CurrentAccountCode = Column(String(20), unique=True, nullable=False)
    CurrentAccountName = Column(String(200), nullable=False)
    CurrentAccountType = Column(String(50), nullable=False)  # Musteri, Tedarikci, Personel, Diger
    TaxNumber = Column(String(50))
    TaxOffice = Column(String(100))
    Address = Column(String(500))
    City = Column(String(50))
    District = Column(String(50))
    PostalCode = Column(String(10))
    Phone = Column(String(50))
    Mobile = Column(String(50))
    Email = Column(String(100))
    Website = Column(String(100))
    ContactPerson = Column(String(100))
    PaymentTerm = Column(Integer, default=0)
    CreditLimit = Column(Numeric(18, 2), default=0)
    RiskLimit = Column(Numeric(18, 2), default=0)
    IsActive = Column(Boolean, default=True)
    CreatedDate = Column(DateTime, default=func.now())
    UpdatedDate = Column(DateTime, default=func.now(), onupdate=func.now())
    CreatedBy = Column(Integer, ForeignKey('Users.UserID'))
    
    # Relationships
    creator = relationship("User")
    invoices = relationship("Invoice", back_populates="current_account")
    journal_details = relationship("JournalEntryDetail", back_populates="current_account")

class StockCategory(Base):
    __tablename__ = 'StockCategories'
    
    CategoryID = Column(Integer, primary_key=True, autoincrement=True)
    CategoryCode = Column(String(20), unique=True, nullable=False)
    CategoryName = Column(String(100), nullable=False)
    ParentCategoryID = Column(Integer, ForeignKey('StockCategories.CategoryID'))
    Description = Column(String(500))
    IsActive = Column(Boolean, default=True)
    CreatedDate = Column(DateTime, default=func.now())
    
    # Relationships
    parent = relationship("StockCategory", remote_side=[CategoryID])
    children = relationship("StockCategory")
    stock_items = relationship("StockItem", back_populates="category")

class StockItem(Base):
    __tablename__ = 'StockItems'
    
    StockID = Column(Integer, primary_key=True, autoincrement=True)
    StockCode = Column(String(50), unique=True, nullable=False)
    StockName = Column(String(200), nullable=False)
    CategoryID = Column(Integer, ForeignKey('StockCategories.CategoryID'))
    Unit = Column(String(20), nullable=False)
    Barcode = Column(String(50))
    Description = Column(String(500))
    PurchasePrice = Column(Numeric(18, 4), default=0)
    SalePrice = Column(Numeric(18, 4), default=0)
    MinStockLevel = Column(Numeric(18, 2), default=0)
    MaxStockLevel = Column(Numeric(18, 2), default=0)
    CurrentStock = Column(Numeric(18, 2), default=0)
    VATRate = Column(Numeric(5, 2), default=18.00)
    IsActive = Column(Boolean, default=True)
    CreatedDate = Column(DateTime, default=func.now())
    UpdatedDate = Column(DateTime, default=func.now(), onupdate=func.now())
    CreatedBy = Column(Integer, ForeignKey('Users.UserID'))
    
    # Relationships
    category = relationship("StockCategory", back_populates="stock_items")
    creator = relationship("User")
    movements = relationship("StockMovement", back_populates="stock_item")
    invoice_details = relationship("InvoiceDetail", back_populates="stock_item")

class CashRegister(Base):
    __tablename__ = 'CashRegisters'
    
    CashRegisterID = Column(Integer, primary_key=True, autoincrement=True)
    CashRegisterCode = Column(String(20), unique=True, nullable=False)
    CashRegisterName = Column(String(100), nullable=False)
    CurrencyCode = Column(String(3), default='TRY')
    OpeningBalance = Column(Numeric(18, 2), default=0)
    CurrentBalance = Column(Numeric(18, 2), default=0)
    ResponsiblePerson = Column(String(100))
    IsActive = Column(Boolean, default=True)
    CreatedDate = Column(DateTime, default=func.now())
    UpdatedDate = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    movements = relationship("CashMovement", back_populates="cash_register")

class Bank(Base):
    __tablename__ = 'Banks'
    
    BankID = Column(Integer, primary_key=True, autoincrement=True)
    BankCode = Column(String(20), unique=True, nullable=False)
    BankName = Column(String(100), nullable=False)
    AccountNumber = Column(String(50))
    IBAN = Column(String(50))
    BranchName = Column(String(100))
    BranchCode = Column(String(20))
    CurrencyCode = Column(String(3), default='TRY')
    OpeningBalance = Column(Numeric(18, 2), default=0)
    CurrentBalance = Column(Numeric(18, 2), default=0)
    ResponsiblePerson = Column(String(100))
    IsActive = Column(Boolean, default=True)
    CreatedDate = Column(DateTime, default=func.now())
    UpdatedDate = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    movements = relationship("BankMovement", back_populates="bank")

class JournalEntry(Base):
    __tablename__ = 'JournalEntries'
    
    JournalEntryID = Column(Integer, primary_key=True, autoincrement=True)
    VoucherNumber = Column(String(50), unique=True, nullable=False)
    VoucherDate = Column(Date, nullable=False)
    Description = Column(String(500))
    TotalDebit = Column(Numeric(18, 2), nullable=False)
    TotalCredit = Column(Numeric(18, 2), nullable=False)
    IsBalanced = Column(Boolean, default=False)
    IsPosted = Column(Boolean, default=False)
    PostedDate = Column(DateTime)
    DocumentType = Column(String(50))
    DocumentNumber = Column(String(50))
    CreatedDate = Column(DateTime, default=func.now())
    CreatedBy = Column(Integer, ForeignKey('Users.UserID'))
    ApprovedBy = Column(Integer, ForeignKey('Users.UserID'))
    ApprovedDate = Column(DateTime)
    
    # Relationships
    creator = relationship("User", foreign_keys=[CreatedBy])
    approver = relationship("User", foreign_keys=[ApprovedBy])
    details = relationship("JournalEntryDetail", back_populates="journal_entry", cascade="all, delete-orphan")

class JournalEntryDetail(Base):
    __tablename__ = 'JournalEntryDetails'
    
    JournalDetailID = Column(Integer, primary_key=True, autoincrement=True)
    JournalEntryID = Column(Integer, ForeignKey('JournalEntries.JournalEntryID'), nullable=False)
    LineNumber = Column(Integer, nullable=False)
    AccountID = Column(Integer, ForeignKey('ChartOfAccounts.AccountID'), nullable=False)
    CurrentAccountID = Column(Integer, ForeignKey('CurrentAccounts.CurrentAccountID'))
    Description = Column(String(500))
    DebitAmount = Column(Numeric(18, 2), default=0)
    CreditAmount = Column(Numeric(18, 2), default=0)
    CurrencyCode = Column(String(3), default='TRY')
    ExchangeRate = Column(Numeric(10, 4), default=1)
    DebitAmountLocal = Column(Numeric(18, 2), default=0)
    CreditAmountLocal = Column(Numeric(18, 2), default=0)
    
    # Relationships
    journal_entry = relationship("JournalEntry", back_populates="details")
    account = relationship("ChartOfAccount", back_populates="journal_details")
    current_account = relationship("CurrentAccount", back_populates="journal_details")

class Invoice(Base):
    __tablename__ = 'Invoices'
    
    InvoiceID = Column(Integer, primary_key=True, autoincrement=True)
    InvoiceNumber = Column(String(50), unique=True, nullable=False)
    InvoiceType = Column(String(20), nullable=False)  # Alis, Satis
    InvoiceDate = Column(Date, nullable=False)
    CurrentAccountID = Column(Integer, ForeignKey('CurrentAccounts.CurrentAccountID'), nullable=False)
    SubTotal = Column(Numeric(18, 2), default=0)
    VATAmount = Column(Numeric(18, 2), default=0)
    DiscountAmount = Column(Numeric(18, 2), default=0)
    TotalAmount = Column(Numeric(18, 2), default=0)
    PaidAmount = Column(Numeric(18, 2), default=0)
    RemainingAmount = Column(Numeric(18, 2), default=0)
    DueDate = Column(Date)
    PaymentTerm = Column(String(100))
    Notes = Column(String(500))
    IsPosted = Column(Boolean, default=False)
    PostedDate = Column(DateTime)
    JournalEntryID = Column(Integer, ForeignKey('JournalEntries.JournalEntryID'))
    CreatedDate = Column(DateTime, default=func.now())
    CreatedBy = Column(Integer, ForeignKey('Users.UserID'))
    
    # Relationships
    current_account = relationship("CurrentAccount", back_populates="invoices")
    journal_entry = relationship("JournalEntry")
    creator = relationship("User")
    details = relationship("InvoiceDetail", back_populates="invoice", cascade="all, delete-orphan")

class InvoiceDetail(Base):
    __tablename__ = 'InvoiceDetails'
    
    InvoiceDetailID = Column(Integer, primary_key=True, autoincrement=True)
    InvoiceID = Column(Integer, ForeignKey('Invoices.InvoiceID'), nullable=False)
    LineNumber = Column(Integer, nullable=False)
    StockID = Column(Integer, ForeignKey('StockItems.StockID'))
    Description = Column(String(200), nullable=False)
    Quantity = Column(Numeric(18, 2), nullable=False)
    Unit = Column(String(20))
    UnitPrice = Column(Numeric(18, 4), nullable=False)
    DiscountRate = Column(Numeric(5, 2), default=0)
    DiscountAmount = Column(Numeric(18, 2), default=0)
    NetAmount = Column(Numeric(18, 2), nullable=False)
    VATRate = Column(Numeric(5, 2), default=18.00)
    VATAmount = Column(Numeric(18, 2), default=0)
    TotalAmount = Column(Numeric(18, 2), nullable=False)
    
    # Relationships
    invoice = relationship("Invoice", back_populates="details")
    stock_item = relationship("StockItem", back_populates="invoice_details")

class StockMovement(Base):
    __tablename__ = 'StockMovements'
    
    MovementID = Column(Integer, primary_key=True, autoincrement=True)
    MovementNumber = Column(String(50), unique=True, nullable=False)
    MovementDate = Column(Date, nullable=False)
    MovementType = Column(String(20), nullable=False)  # Giris, Cikis, Transfer, Sayim
    StockID = Column(Integer, ForeignKey('StockItems.StockID'), nullable=False)
    WarehouseCode = Column(String(20))
    Quantity = Column(Numeric(18, 2), nullable=False)
    UnitPrice = Column(Numeric(18, 4), default=0)
    TotalValue = Column(Numeric(18, 2), default=0)
    CurrentAccountID = Column(Integer, ForeignKey('CurrentAccounts.CurrentAccountID'))
    InvoiceID = Column(Integer, ForeignKey('Invoices.InvoiceID'))
    Description = Column(String(500))
    CreatedDate = Column(DateTime, default=func.now())
    CreatedBy = Column(Integer, ForeignKey('Users.UserID'))
    
    # Relationships
    stock_item = relationship("StockItem", back_populates="movements")
    current_account = relationship("CurrentAccount")
    invoice = relationship("Invoice")
    creator = relationship("User")

class CashMovement(Base):
    __tablename__ = 'CashMovements'
    
    CashMovementID = Column(Integer, primary_key=True, autoincrement=True)
    MovementNumber = Column(String(50), unique=True, nullable=False)
    MovementDate = Column(Date, nullable=False)
    CashRegisterID = Column(Integer, ForeignKey('CashRegisters.CashRegisterID'), nullable=False)
    MovementType = Column(String(20), nullable=False)  # Giris, Cikis
    Amount = Column(Numeric(18, 2), nullable=False)
    CurrentAccountID = Column(Integer, ForeignKey('CurrentAccounts.CurrentAccountID'))
    Description = Column(String(500))
    DocumentNumber = Column(String(50))
    JournalEntryID = Column(Integer, ForeignKey('JournalEntries.JournalEntryID'))
    CreatedDate = Column(DateTime, default=func.now())
    CreatedBy = Column(Integer, ForeignKey('Users.UserID'))
    
    # Relationships
    cash_register = relationship("CashRegister", back_populates="movements")
    current_account = relationship("CurrentAccount")
    journal_entry = relationship("JournalEntry")
    creator = relationship("User")

class BankMovement(Base):
    __tablename__ = 'BankMovements'
    
    BankMovementID = Column(Integer, primary_key=True, autoincrement=True)
    MovementNumber = Column(String(50), unique=True, nullable=False)
    MovementDate = Column(Date, nullable=False)
    BankID = Column(Integer, ForeignKey('Banks.BankID'), nullable=False)
    MovementType = Column(String(20), nullable=False)  # Giris, Cikis
    Amount = Column(Numeric(18, 2), nullable=False)
    CurrentAccountID = Column(Integer, ForeignKey('CurrentAccounts.CurrentAccountID'))
    Description = Column(String(500))
    DocumentNumber = Column(String(50))
    JournalEntryID = Column(Integer, ForeignKey('JournalEntries.JournalEntryID'))
    CreatedDate = Column(DateTime, default=func.now())
    CreatedBy = Column(Integer, ForeignKey('Users.UserID'))
    
    # Relationships
    bank = relationship("Bank", back_populates="movements")
    current_account = relationship("CurrentAccount")
    journal_entry = relationship("JournalEntry")
    creator = relationship("User")

class Employee(Base):
    __tablename__ = 'Employees'
    
    EmployeeID = Column(Integer, primary_key=True, autoincrement=True)
    EmployeeCode = Column(String(20), unique=True, nullable=False)
    FullName = Column(String(100), nullable=False)
    IdentityNumber = Column(String(11), unique=True)
    Department = Column(String(50))
    Position = Column(String(50))
    HireDate = Column(Date)
    Salary = Column(Numeric(18, 2), default=0)
    Phone = Column(String(50))
    Email = Column(String(100))
    Address = Column(String(500))
    IsActive = Column(Boolean, default=True)
    CreatedDate = Column(DateTime, default=func.now())
    UpdatedDate = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    payrolls = relationship("Payroll", back_populates="employee")

class Payroll(Base):
    __tablename__ = 'Payroll'
    
    PayrollID = Column(Integer, primary_key=True, autoincrement=True)
    PayrollNumber = Column(String(50), unique=True, nullable=False)
    EmployeeID = Column(Integer, ForeignKey('Employees.EmployeeID'), nullable=False)
    PayrollMonth = Column(Integer, nullable=False)
    PayrollYear = Column(Integer, nullable=False)
    BasicSalary = Column(Numeric(18, 2), default=0)
    Overtime = Column(Numeric(18, 2), default=0)
    Bonus = Column(Numeric(18, 2), default=0)
    GrossSalary = Column(Numeric(18, 2), default=0)
    SocialSecurityDeduction = Column(Numeric(18, 2), default=0)
    TaxDeduction = Column(Numeric(18, 2), default=0)
    OtherDeductions = Column(Numeric(18, 2), default=0)
    NetSalary = Column(Numeric(18, 2), default=0)
    IsPaid = Column(Boolean, default=False)
    PaidDate = Column(Date)
    JournalEntryID = Column(Integer, ForeignKey('JournalEntries.JournalEntryID'))
    CreatedDate = Column(DateTime, default=func.now())
    CreatedBy = Column(Integer, ForeignKey('Users.UserID'))
    
    # Relationships
    employee = relationship("Employee", back_populates="payrolls")
    journal_entry = relationship("JournalEntry")
    creator = relationship("User")

class SystemSetting(Base):
    __tablename__ = 'SystemSettings'
    
    SettingID = Column(Integer, primary_key=True, autoincrement=True)
    SettingKey = Column(String(100), unique=True, nullable=False)
    SettingValue = Column(String(500))
    Description = Column(String(200))
    Category = Column(String(50))
    DataType = Column(String(20))  # String, Number, Boolean, Date
    UpdatedDate = Column(DateTime, default=func.now(), onupdate=func.now())
    UpdatedBy = Column(Integer, ForeignKey('Users.UserID'))
    
    # Relationships
    updater = relationship("User")

class ExchangeRate(Base):
    __tablename__ = 'ExchangeRates'
    
    ExchangeRateID = Column(Integer, primary_key=True, autoincrement=True)
    CurrencyCode = Column(String(3), nullable=False)
    Date = Column(Date, nullable=False)
    BuyingRate = Column(Numeric(10, 4), nullable=False)
    SellingRate = Column(Numeric(10, 4), nullable=False)
    CreatedDate = Column(DateTime, default=func.now())

class Branch(Base):
    __tablename__ = 'Branches'

    BranchID = Column(Integer, primary_key=True, autoincrement=True)
    BranchCode = Column(String(20), unique=True, nullable=False)
    BranchName = Column(String(200), nullable=False)
    Address = Column(String(500))
    City = Column(String(50))
    District = Column(String(50))
    Phone = Column(String(50))
    ManagerName = Column(String(100))
    IsHeadOffice = Column(Boolean, default=False)
    IsActive = Column(Boolean, default=True)
    CreatedDate = Column(DateTime, default=func.now())

    pos_registers = relationship("POSRegister", back_populates="branch")
    cost_centers = relationship("CostCenter", back_populates="branch")
    campaigns = relationship("Campaign", back_populates="branch")
    purchase_orders = relationship("PurchaseOrder", back_populates="branch")
    customer_orders = relationship("CustomerOrder", back_populates="branch")

class POSRegister(Base):
    __tablename__ = 'POSRegisters'

    POSRegisterID = Column(Integer, primary_key=True, autoincrement=True)
    POSRegisterCode = Column(String(20), unique=True, nullable=False)
    POSRegisterName = Column(String(100), nullable=False)
    BranchID = Column(Integer, ForeignKey('Branches.BranchID'))
    DeviceType = Column(String(50))
    DeviceSerial = Column(String(100))
    IPAddress = Column(String(50))
    PortNumber = Column(Integer)
    IsActive = Column(Boolean, default=True)
    LastConnection = Column(DateTime)
    CreatedDate = Column(DateTime, default=func.now())

    branch = relationship("Branch", back_populates="pos_registers")
    sessions = relationship("POSSession", back_populates="pos_register")

class POSSession(Base):
    __tablename__ = 'POS_Sessions'

    SessionID = Column(Integer, primary_key=True, autoincrement=True)
    POSRegisterID = Column(Integer, ForeignKey('POSRegisters.POSRegisterID'))
    UserID = Column(Integer, ForeignKey('Users.UserID'))
    OpeningDate = Column(DateTime, nullable=False)
    ClosingDate = Column(DateTime)
    OpeningAmount = Column(Numeric(18,2), default=0)
    ClosingAmount = Column(Numeric(18,2), default=0)
    CashSales = Column(Numeric(18,2), default=0)
    CreditSales = Column(Numeric(18,2), default=0)
    TotalSales = Column(Numeric(18,2), default=0)
    ReturnCount = Column(Integer, default=0)
    ReturnAmount = Column(Numeric(18,2), default=0)
    DiscountAmount = Column(Numeric(18,2), default=0)
    IsActive = Column(Boolean, default=True)
    Status = Column(String(20), default='Acik')

    pos_register = relationship("POSRegister", back_populates="sessions")
    user = relationship("User")
    receipts = relationship("POSReceipt", back_populates="session")

class POSReceipt(Base):
    __tablename__ = 'POSReceipts'

    ReceiptID = Column(Integer, primary_key=True, autoincrement=True)
    ReceiptNumber = Column(String(50), unique=True, nullable=False)
    SessionID = Column(Integer, ForeignKey('POS_Sessions.SessionID'))
    POSRegisterID = Column(Integer, ForeignKey('POSRegisters.POSRegisterID'))
    BranchID = Column(Integer, ForeignKey('Branches.BranchID'))
    UserID = Column(Integer, ForeignKey('Users.UserID'))
    CurrentAccountID = Column(Integer, ForeignKey('CurrentAccounts.CurrentAccountID'))
    ReceiptDate = Column(DateTime, nullable=False)
    ReceiptType = Column(String(20), default='Satis')
    PaymentType = Column(String(20), default='Nakit')
    SubTotal = Column(Numeric(18,2), default=0)
    DiscountAmount = Column(Numeric(18,2), default=0)
    VATAmount = Column(Numeric(18,2), default=0)
    TotalAmount = Column(Numeric(18,2), default=0)
    PaidAmount = Column(Numeric(18,2), default=0)
    ChangeAmount = Column(Numeric(18,2), default=0)
    PointsEarned = Column(Numeric(10,2), default=0)
    PointsUsed = Column(Numeric(10,2), default=0)
    IsCancelled = Column(Boolean, default=False)
    CancelReason = Column(String(200))
    IsPrinted = Column(Boolean, default=False)
    PrintCount = Column(Integer, default=0)
    CreatedDate = Column(DateTime, default=func.now())

    session = relationship("POSSession", back_populates="receipts")
    details = relationship("POSReceiptDetail", back_populates="receipt", cascade="all, delete-orphan")

class POSReceiptDetail(Base):
    __tablename__ = 'POSReceiptDetails'

    ReceiptDetailID = Column(Integer, primary_key=True, autoincrement=True)
    ReceiptID = Column(Integer, ForeignKey('POSReceipts.ReceiptID'), nullable=False)
    LineNumber = Column(Integer, nullable=False)
    StockID = Column(Integer, ForeignKey('StockItems.StockID'))
    StockName = Column(String(200), nullable=False)
    Barcode = Column(String(50))
    Quantity = Column(Numeric(18,2), nullable=False)
    UnitPrice = Column(Numeric(18,4), nullable=False)
    DiscountRate = Column(Numeric(5,2), default=0)
    DiscountAmount = Column(Numeric(18,2), default=0)
    NetPrice = Column(Numeric(18,4), nullable=False)
    VATRate = Column(Numeric(5,2), default=18.00)
    VATAmount = Column(Numeric(18,2), default=0)
    TotalAmount = Column(Numeric(18,2), nullable=False)
    CostPrice = Column(Numeric(18,4), default=0)
    ProfitAmount = Column(Numeric(18,2), default=0)
    PromotionID = Column(Integer)
    IsReturned = Column(Boolean, default=False)

    receipt = relationship("POSReceipt", back_populates="details")
    stock_item = relationship("StockItem")

class ProductionRecipe(Base):
    __tablename__ = 'ProductionRecipes'

    RecipeID = Column(Integer, primary_key=True, autoincrement=True)
    RecipeCode = Column(String(50), unique=True, nullable=False)
    RecipeName = Column(String(200), nullable=False)
    ProductID = Column(Integer, ForeignKey('StockItems.StockID'))
    Quantity = Column(Numeric(18,2), default=1)
    Unit = Column(String(20))
    TotalCost = Column(Numeric(18,2), default=0)
    LaborCost = Column(Numeric(18,2), default=0)
    OverheadCost = Column(Numeric(18,2), default=0)
    Notes = Column(String(500))
    IsActive = Column(Boolean, default=True)
    VersionNo = Column(Integer, default=1)
    CreatedDate = Column(DateTime, default=func.now())
    CreatedBy = Column(Integer, ForeignKey('Users.UserID'))

    details = relationship("ProductionRecipeDetail", back_populates="recipe", cascade="all, delete-orphan")
    product = relationship("StockItem", foreign_keys=[ProductID])

class ProductionRecipeDetail(Base):
    __tablename__ = 'ProductionRecipeDetails'

    RecipeDetailID = Column(Integer, primary_key=True, autoincrement=True)
    RecipeID = Column(Integer, ForeignKey('ProductionRecipes.RecipeID'), nullable=False)
    LineNumber = Column(Integer, nullable=False)
    RawMaterialID = Column(Integer, ForeignKey('StockItems.StockID'))
    Quantity = Column(Numeric(18,4), nullable=False)
    Unit = Column(String(20))
    UnitCost = Column(Numeric(18,4), default=0)
    TotalCost = Column(Numeric(18,2), default=0)
    WasteRate = Column(Numeric(5,2), default=0)
    IsActive = Column(Boolean, default=True)

    recipe = relationship("ProductionRecipe", back_populates="details")
    raw_material = relationship("StockItem", foreign_keys=[RawMaterialID])

class ProductionOrder(Base):
    __tablename__ = 'ProductionOrders'

    OrderID = Column(Integer, primary_key=True, autoincrement=True)
    OrderCode = Column(String(50), unique=True, nullable=False)
    OrderDate = Column(Date, nullable=False)
    RecipeID = Column(Integer, ForeignKey('ProductionRecipes.RecipeID'))
    ProductID = Column(Integer, ForeignKey('StockItems.StockID'))
    PlannedQuantity = Column(Numeric(18,2), nullable=False)
    ProducedQuantity = Column(Numeric(18,2), default=0)
    DefectQuantity = Column(Numeric(18,2), default=0)
    UnitCost = Column(Numeric(18,4), default=0)
    TotalCost = Column(Numeric(18,2), default=0)
    Status = Column(String(20), default='Planlandi')
    StartDate = Column(DateTime)
    EndDate = Column(DateTime)
    ResponsiblePerson = Column(String(100))
    Notes = Column(String(500))
    CreatedDate = Column(DateTime, default=func.now())
    CreatedBy = Column(Integer, ForeignKey('Users.UserID'))

    recipe = relationship("ProductionRecipe")
    product = relationship("StockItem", foreign_keys=[ProductID])
    creator = relationship("User", foreign_keys=[CreatedBy])

class PriceGroup(Base):
    __tablename__ = 'PriceGroups'

    PriceGroupID = Column(Integer, primary_key=True, autoincrement=True)
    PriceGroupCode = Column(String(20), unique=True, nullable=False)
    PriceGroupName = Column(String(100), nullable=False)
    DiscountRate = Column(Numeric(5,2), default=0)
    MarkupRate = Column(Numeric(5,2), default=0)
    IsActive = Column(Boolean, default=True)
    CreatedDate = Column(DateTime, default=func.now())

    items = relationship("PriceGroupItem", back_populates="price_group", cascade="all, delete-orphan")

class PriceGroupItem(Base):
    __tablename__ = 'PriceGroupItems'

    PriceGroupItemID = Column(Integer, primary_key=True, autoincrement=True)
    PriceGroupID = Column(Integer, ForeignKey('PriceGroups.PriceGroupID'), nullable=False)
    StockID = Column(Integer, ForeignKey('StockItems.StockID'), nullable=False)
    BasePrice = Column(Numeric(18,4), nullable=False)
    PriceWithMarkup = Column(Numeric(18,4), nullable=False)

    price_group = relationship("PriceGroup", back_populates="items")
    stock_item = relationship("StockItem")

class Campaign(Base):
    __tablename__ = 'Campaigns'

    CampaignID = Column(Integer, primary_key=True, autoincrement=True)
    CampaignCode = Column(String(50), unique=True, nullable=False)
    CampaignName = Column(String(200), nullable=False)
    CampaignType = Column(String(50))
    DiscountRate = Column(Numeric(5,2))
    MinPurchaseAmount = Column(Numeric(18,2), default=0)
    MinQuantity = Column(Integer, default=0)
    FreeProductID = Column(Integer, ForeignKey('StockItems.StockID'))
    FreeQuantity = Column(Integer, default=0)
    PointsMultiplier = Column(Numeric(5,2), default=1)
    StartDate = Column(Date, nullable=False)
    EndDate = Column(Date, nullable=False)
    BranchID = Column(Integer, ForeignKey('Branches.BranchID'))
    IsActive = Column(Boolean, default=True)
    Description = Column(String(500))
    CreatedBy = Column(Integer, ForeignKey('Users.UserID'))
    CreatedDate = Column(DateTime, default=func.now())

    branch = relationship("Branch", back_populates="campaigns")

class CostCenter(Base):
    __tablename__ = 'CostCenters'

    CostCenterID = Column(Integer, primary_key=True, autoincrement=True)
    CostCenterCode = Column(String(20), unique=True, nullable=False)
    CostCenterName = Column(String(100), nullable=False)
    BranchID = Column(Integer, ForeignKey('Branches.BranchID'))
    ParentCostCenterID = Column(Integer, ForeignKey('CostCenters.CostCenterID'))
    BudgetAmount = Column(Numeric(18,2), default=0)
    SpentAmount = Column(Numeric(18,2), default=0)
    ManagerName = Column(String(100))
    IsActive = Column(Boolean, default=True)
    CreatedDate = Column(DateTime, default=func.now())

    branch = relationship("Branch", back_populates="cost_centers")
    parent = relationship("CostCenter", remote_side=[CostCenterID])

class CRMActivity(Base):
    __tablename__ = 'CRM_Activities'

    ActivityID = Column(Integer, primary_key=True, autoincrement=True)
    ActivityDate = Column(Date, nullable=False)
    ActivityType = Column(String(50))
    CurrentAccountID = Column(Integer, ForeignKey('CurrentAccounts.CurrentAccountID'))
    ContactPerson = Column(String(100))
    Subject = Column(String(200))
    Description = Column(String)
    Status = Column(String(20), default='Planlandi')
    FollowUpDate = Column(Date)
    AssignedTo = Column(Integer, ForeignKey('Users.UserID'))
    IsCompleted = Column(Boolean, default=False)
    CompletedDate = Column(DateTime)
    CreatedDate = Column(DateTime, default=func.now())
    CreatedBy = Column(Integer, ForeignKey('Users.UserID'))

class PurchaseOrder(Base):
    __tablename__ = 'PurchaseOrders'

    OrderID = Column(Integer, primary_key=True, autoincrement=True)
    OrderCode = Column(String(50), unique=True, nullable=False)
    OrderDate = Column(Date, nullable=False)
    DeliveryDate = Column(Date)
    SupplierID = Column(Integer, ForeignKey('CurrentAccounts.CurrentAccountID'))
    BranchID = Column(Integer, ForeignKey('Branches.BranchID'))
    Status = Column(String(20), default='Beklemede')
    SubTotal = Column(Numeric(18,2), default=0)
    DiscountAmount = Column(Numeric(18,2), default=0)
    VATAmount = Column(Numeric(18,2), default=0)
    TotalAmount = Column(Numeric(18,2), default=0)
    Notes = Column(String(500))
    ApprovedBy = Column(Integer, ForeignKey('Users.UserID'))
    CreatedBy = Column(Integer, ForeignKey('Users.UserID'))
    CreatedDate = Column(DateTime, default=func.now())

    branch = relationship("Branch", back_populates="purchase_orders")
    supplier = relationship("CurrentAccount")
    details = relationship("PurchaseOrderDetail", back_populates="purchase_order", cascade="all, delete-orphan")

class PurchaseOrderDetail(Base):
    __tablename__ = 'PurchaseOrderDetails'

    OrderDetailID = Column(Integer, primary_key=True, autoincrement=True)
    OrderID = Column(Integer, ForeignKey('PurchaseOrders.OrderID'), nullable=False)
    LineNumber = Column(Integer, nullable=False)
    StockID = Column(Integer, ForeignKey('StockItems.StockID'))
    Description = Column(String(200))
    Quantity = Column(Numeric(18,2), nullable=False)
    Unit = Column(String(20))
    UnitPrice = Column(Numeric(18,4), nullable=False)
    TotalAmount = Column(Numeric(18,2), nullable=False)
    ReceivedQuantity = Column(Numeric(18,2), default=0)

    purchase_order = relationship("PurchaseOrder", back_populates="details")
    stock_item = relationship("StockItem")

class CustomerOrder(Base):
    __tablename__ = 'CustomerOrders'

    OrderID = Column(Integer, primary_key=True, autoincrement=True)
    OrderCode = Column(String(50), unique=True, nullable=False)
    OrderDate = Column(Date, nullable=False)
    CustomerID = Column(Integer, ForeignKey('CurrentAccounts.CurrentAccountID'))
    BranchID = Column(Integer, ForeignKey('Branches.BranchID'))
    Status = Column(String(20), default='Beklemede')
    SubTotal = Column(Numeric(18,2), default=0)
    DiscountAmount = Column(Numeric(18,2), default=0)
    VATAmount = Column(Numeric(18,2), default=0)
    TotalAmount = Column(Numeric(18,2), default=0)
    PaymentType = Column(String(50))
    DeliveryAddress = Column(String(500))
    Notes = Column(String(500))
    CreatedBy = Column(Integer, ForeignKey('Users.UserID'))
    CreatedDate = Column(DateTime, default=func.now())

    branch = relationship("Branch", back_populates="customer_orders")
    customer = relationship("CurrentAccount")
    details = relationship("CustomerOrderDetail", back_populates="customer_order", cascade="all, delete-orphan")

class CustomerOrderDetail(Base):
    __tablename__ = 'CustomerOrderDetails'

    OrderDetailID = Column(Integer, primary_key=True, autoincrement=True)
    OrderID = Column(Integer, ForeignKey('CustomerOrders.OrderID'), nullable=False)
    LineNumber = Column(Integer, nullable=False)
    StockID = Column(Integer, ForeignKey('StockItems.StockID'))
    Description = Column(String(200))
    Quantity = Column(Numeric(18,2), nullable=False)
    Unit = Column(String(20))
    UnitPrice = Column(Numeric(18,4), nullable=False)
    TotalAmount = Column(Numeric(18,2), nullable=False)
    DeliveredQuantity = Column(Numeric(18,2), default=0)

    customer_order = relationship("CustomerOrder", back_populates="details")
    stock_item = relationship("StockItem")

class EInvoice(Base):
    __tablename__ = 'EInvoices'

    EInvoiceID = Column(Integer, primary_key=True, autoincrement=True)
    InvoiceNumber = Column(String(50), unique=True, nullable=False)
    UUID = Column(String(100), unique=True)
    Profile = Column(String(20))
    InvoiceType = Column(String(20))
    Status = Column(String(20), default='Taslak')
    GibStatusCode = Column(String(50))
    GibResponse = Column(String)
    InvoiceID = Column(Integer, ForeignKey('Invoices.InvoiceID'))
    CreatedDate = Column(DateTime, default=func.now())
    CreatedBy = Column(Integer, ForeignKey('Users.UserID'))

class MarketplaceListing(Base):
    __tablename__ = 'MarketplaceListings'

    ListingID = Column(Integer, primary_key=True, autoincrement=True)
    MarketplaceName = Column(String(50))
    StockID = Column(Integer, ForeignKey('StockItems.StockID'))
    MarketplaceProductID = Column(String(100))
    MarketplacePrice = Column(Numeric(18,2))
    ListedQuantity = Column(Integer, default=0)
    ListingStatus = Column(String(20), default='Aktif')
    LastSyncDate = Column(DateTime)
    SyncLog = Column(String)
    CreatedDate = Column(DateTime, default=func.now())

class BranchTransfer(Base):
    __tablename__ = 'BranchTransfers'

    TransferID = Column(Integer, primary_key=True, autoincrement=True)
    TransferCode = Column(String(50), unique=True, nullable=False)
    TransferDate = Column(Date, nullable=False)
    SourceBranchID = Column(Integer, ForeignKey('Branches.BranchID'))
    TargetBranchID = Column(Integer, ForeignKey('Branches.BranchID'))
    Status = Column(String(20), default='Hazirlaniyor')
    Notes = Column(String(500))
    CreatedBy = Column(Integer, ForeignKey('Users.UserID'))
    CreatedDate = Column(DateTime, default=func.now())

class BarcodeTemplate(Base):
    __tablename__ = 'BarcodeTemplates'

    TemplateID = Column(Integer, primary_key=True, autoincrement=True)
    TemplateName = Column(String(100), nullable=False)
    LabelWidth = Column(Numeric(10,2), nullable=False)
    LabelHeight = Column(Numeric(10,2), nullable=False)
    FieldsConfiguration = Column(String)
    PrinterName = Column(String(100))
    IsDefault = Column(Boolean, default=False)
    CreatedDate = Column(DateTime, default=func.now())

class BankPOSDevice(Base):
    __tablename__ = 'BankPOSDevices'

    POSDeviceID = Column(Integer, primary_key=True, autoincrement=True)
    BankName = Column(String(100), nullable=False)
    POSModel = Column(String(100))
    TerminalID = Column(String(50))
    MerchantID = Column(String(50))
    CommissionRate = Column(Numeric(5,2), default=0)
    InstallmentCommissionRate = Column(Numeric(5,2), default=0)
    BranchID = Column(Integer, ForeignKey('Branches.BranchID'))
    ConnectionType = Column(String(50))
    IPAddress = Column(String(50))
    PortNumber = Column(Integer)
    IsActive = Column(Boolean, default=True)
    CreatedDate = Column(DateTime, default=func.now())

    branch = relationship("Branch")
    installment_options = relationship("POSInstallmentOption", back_populates="pos_device", cascade="all, delete-orphan")
    transactions = relationship("POSTransaction", back_populates="pos_device")

class POSInstallmentOption(Base):
    __tablename__ = 'POSInstallmentOptions'

    InstallmentID = Column(Integer, primary_key=True, autoincrement=True)
    POSDeviceID = Column(Integer, ForeignKey('BankPOSDevices.POSDeviceID'))
    InstallmentCount = Column(Integer, nullable=False)
    CommissionRate = Column(Numeric(5,2), default=0)
    MinAmount = Column(Numeric(18,2), default=0)
    IsActive = Column(Boolean, default=True)

    pos_device = relationship("BankPOSDevice", back_populates="installment_options")

class POSTransaction(Base):
    __tablename__ = 'POSTransactions'

    TransactionID = Column(Integer, primary_key=True, autoincrement=True)
    ReceiptID = Column(Integer, ForeignKey('POSReceipts.ReceiptID'))
    POSDeviceID = Column(Integer, ForeignKey('BankPOSDevices.POSDeviceID'))
    TransactionDate = Column(DateTime, nullable=False)
    TransactionType = Column(String(20))
    CardNumberMasked = Column(String(20))
    CardHolderName = Column(String(100))
    CardType = Column(String(30))
    InstallmentCount = Column(Integer, default=0)
    Amount = Column(Numeric(18,2), nullable=False)
    CommissionRate = Column(Numeric(5,2), default=0)
    CommissionAmount = Column(Numeric(18,2), default=0)
    NetAmount = Column(Numeric(18,2), default=0)
    AuthCode = Column(String(20))
    ReferenceNo = Column(String(50))
    BatchNo = Column(String(20))
    Status = Column(String(20), default='Basarili')
    ErrorMessage = Column(String(500))
    ResponseData = Column(String)
    CreatedDate = Column(DateTime, default=func.now())

    pos_device = relationship("BankPOSDevice", back_populates="transactions")

class Check(Base):
    __tablename__ = 'Checks'

    CheckID = Column(Integer, primary_key=True, autoincrement=True)
    CheckNo = Column(String(50), nullable=False)
    BankName = Column(String(100), nullable=False)
    BankBranch = Column(String(100))
    AccountNo = Column(String(50))
    Amount = Column(Numeric(18,2), nullable=False)
    CheckDate = Column(Date, nullable=False)
    MaturityDate = Column(Date, nullable=False)
    CurrentAccountID = Column(Integer, ForeignKey('CurrentAccounts.CurrentAccountID'))
    CheckType = Column(String(20), nullable=False)
    CheckStatus = Column(String(30), default='Portfoyde')
    ReceivedDate = Column(Date)
    DeliveredDate = Column(Date)
    EndorsedTo = Column(String(200))
    Description = Column(String(500))
    IsCrossed = Column(Boolean, default=False)
    IsGuaranteed = Column(Boolean, default=False)
    CreatedDate = Column(DateTime, default=func.now())
    CreatedBy = Column(Integer, ForeignKey('Users.UserID'))

    current_account = relationship("CurrentAccount")
    creator = relationship("User")
    endorsements = relationship("CheckEndorsement", back_populates="check_ref", cascade="all, delete-orphan")

class CheckEndorsement(Base):
    __tablename__ = 'CheckEndorsements'

    EndorsementID = Column(Integer, primary_key=True, autoincrement=True)
    CheckID = Column(Integer, ForeignKey('Checks.CheckID'), nullable=False)
    EndorsementDate = Column(Date, nullable=False)
    EndorsedTo = Column(String(200), nullable=False)
    EndorsementType = Column(String(30))
    Amount = Column(Numeric(18,2))
    Description = Column(String(500))
    CreatedBy = Column(Integer, ForeignKey('Users.UserID'))
    CreatedDate = Column(DateTime, default=func.now())

    check_ref = relationship("Check", back_populates="endorsements")

class BouncedCheck(Base):
    __tablename__ = 'BouncedChecks'

    BouncedID = Column(Integer, primary_key=True, autoincrement=True)
    CheckID = Column(Integer, ForeignKey('Checks.CheckID'))
    ProtestDate = Column(Date, nullable=False)
    Reason = Column(String(200))
    ProtestCost = Column(Numeric(18,2), default=0)
    LegalProcessStarted = Column(Boolean, default=False)
    LegalProcessNote = Column(String(500))
    RecoveryAmount = Column(Numeric(18,2), default=0)
    RecoveryDate = Column(Date)
    CreatedDate = Column(DateTime, default=func.now())

class CheckPortfolio(Base):
    __tablename__ = 'CheckPortfolios'

    PortfolioID = Column(Integer, primary_key=True, autoincrement=True)
    PortfolioCode = Column(String(50), unique=True, nullable=False)
    PortfolioDate = Column(Date, nullable=False)
    PortfolioType = Column(String(20))
    TotalCount = Column(Integer, default=0)
    TotalAmount = Column(Numeric(18,2), default=0)
    Description = Column(String(500))
    CreatedDate = Column(DateTime, default=func.now())
    CreatedBy = Column(Integer, ForeignKey('Users.UserID'))

class AuditLog(Base):
    __tablename__ = 'AuditLog'
    
    AuditID = Column(Integer, primary_key=True, autoincrement=True)
    TableName = Column(String(100), nullable=False)
    RecordID = Column(Integer, nullable=False)
    Action = Column(String(20), nullable=False)  # INSERT, UPDATE, DELETE
    OldValues = Column(Text)
    NewValues = Column(Text)
    UserID = Column(Integer, ForeignKey('Users.UserID'))
    ActionDate = Column(DateTime, default=func.now())
    IPAddress = Column(String(50))
    
    # Relationships
    user = relationship("User")

# Database session factory
def create_session(engine):
    """Database session oluştur"""
    Session = sessionmaker(bind=engine)
    return Session()

def create_all_tables(engine):
    """Tüm tabloları oluştur"""
    Base.metadata.create_all(engine)
