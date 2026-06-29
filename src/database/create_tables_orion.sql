-- Orion ERP - Ek Modül Tabloları
-- Şube, POS, Üretim, Fiyat Grupları, Kampanya, CRM, Sipariş, Pazaryeri, e-Fatura

-- 21. Şubeler (Branches)
CREATE TABLE Branches (
    BranchID INT IDENTITY(1,1) PRIMARY KEY,
    BranchCode NVARCHAR(20) UNIQUE NOT NULL,
    BranchName NVARCHAR(200) NOT NULL,
    Address NVARCHAR(500),
    City NVARCHAR(50),
    District NVARCHAR(50),
    Phone NVARCHAR(50),
    ManagerName NVARCHAR(100),
    IsHeadOffice BIT DEFAULT 0,
    IsActive BIT DEFAULT 1,
    CreatedDate DATETIME2 DEFAULT GETDATE()
);

-- 22. POS Kasaları
CREATE TABLE POSRegisters (
    POSRegisterID INT IDENTITY(1,1) PRIMARY KEY,
    POSRegisterCode NVARCHAR(20) UNIQUE NOT NULL,
    POSRegisterName NVARCHAR(100) NOT NULL,
    BranchID INT FOREIGN KEY REFERENCES Branches(BranchID),
    DeviceType NVARCHAR(50), -- Hugin, NCR, Toshiba, Npos, IBM, Escort
    DeviceSerial NVARCHAR(100),
    IPAddress NVARCHAR(50),
    PortNumber INT,
    IsActive BIT DEFAULT 1,
    LastConnection DATETIME2,
    CreatedDate DATETIME2 DEFAULT GETDATE()
);

-- 23. POS Oturumları
CREATE TABLE POS Sessions (
    SessionID INT IDENTITY(1,1) PRIMARY KEY,
    POSRegisterID INT FOREIGN KEY REFERENCES POSRegisters(POSRegisterID),
    UserID INT FOREIGN KEY REFERENCES Users(UserID),
    OpeningDate DATETIME2 NOT NULL,
    ClosingDate DATETIME2,
    OpeningAmount DECIMAL(18,2) DEFAULT 0,
    ClosingAmount DECIMAL(18,2) DEFAULT 0,
    CashSales DECIMAL(18,2) DEFAULT 0,
    CreditSales DECIMAL(18,2) DEFAULT 0,
    TotalSales DECIMAL(18,2) DEFAULT 0,
    ReturnCount INT DEFAULT 0,
    ReturnAmount DECIMAL(18,2) DEFAULT 0,
    DiscountAmount DECIMAL(18,2) DEFAULT 0,
    IsActive BIT DEFAULT 1,
    Status NVARCHAR(20) DEFAULT 'Acik' -- Acik, Kapali, ZorunluKapanis
);

-- 24. POS Satış Fişleri
CREATE TABLE POSReceipts (
    ReceiptID INT IDENTITY(1,1) PRIMARY KEY,
    ReceiptNumber NVARCHAR(50) UNIQUE NOT NULL,
    SessionID INT FOREIGN KEY REFERENCES POS_Sessions(SessionID),
    POSRegisterID INT FOREIGN KEY REFERENCES POSRegisters(POSRegisterID),
    BranchID INT FOREIGN KEY REFERENCES Branches(BranchID),
    UserID INT FOREIGN KEY REFERENCES Users(UserID),
    CurrentAccountID INT FOREIGN KEY REFERENCES CurrentAccounts(CurrentAccountID),
    ReceiptDate DATETIME2 NOT NULL,
    ReceiptType NVARCHAR(20) DEFAULT 'Satis', -- Satis, Iade, Vazgecme
    PaymentType NVARCHAR(20) DEFAULT 'Nakit', -- Nakit, KrediKarti, Ticket, HediyeCeki
    SubTotal DECIMAL(18,2) DEFAULT 0,
    DiscountAmount DECIMAL(18,2) DEFAULT 0,
    VATAmount DECIMAL(18,2) DEFAULT 0,
    TotalAmount DECIMAL(18,2) DEFAULT 0,
    PaidAmount DECIMAL(18,2) DEFAULT 0,
    ChangeAmount DECIMAL(18,2) DEFAULT 0,
    PointsEarned DECIMAL(10,2) DEFAULT 0,
    PointsUsed DECIMAL(10,2) DEFAULT 0,
    IsCancelled BIT DEFAULT 0,
    CancelReason NVARCHAR(200),
    IsPrinted BIT DEFAULT 0,
    PrintCount INT DEFAULT 0,
    CreatedDate DATETIME2 DEFAULT GETDATE()
);

-- 25. POS Satış Detayları
CREATE TABLE POSReceiptDetails (
    ReceiptDetailID INT IDENTITY(1,1) PRIMARY KEY,
    ReceiptID INT FOREIGN KEY REFERENCES POSReceipts(ReceiptID) ON DELETE CASCADE,
    LineNumber INT NOT NULL,
    StockID INT FOREIGN KEY REFERENCES StockItems(StockID),
    StockName NVARCHAR(200) NOT NULL,
    Barcode NVARCHAR(50),
    Quantity DECIMAL(18,2) NOT NULL,
    UnitPrice DECIMAL(18,4) NOT NULL,
    DiscountRate DECIMAL(5,2) DEFAULT 0,
    DiscountAmount DECIMAL(18,2) DEFAULT 0,
    NetPrice DECIMAL(18,4) NOT NULL,
    VATRate DECIMAL(5,2) DEFAULT 18.00,
    VATAmount DECIMAL(18,2) DEFAULT 0,
    TotalAmount DECIMAL(18,2) NOT NULL,
    CostPrice DECIMAL(18,4) DEFAULT 0,
    ProfitAmount DECIMAL(18,2) DEFAULT 0,
    PromotionID INT,
    IsReturned BIT DEFAULT 0
);

-- 26. Üretim Reçeteleri
CREATE TABLE ProductionRecipes (
    RecipeID INT IDENTITY(1,1) PRIMARY KEY,
    RecipeCode NVARCHAR(50) UNIQUE NOT NULL,
    RecipeName NVARCHAR(200) NOT NULL,
    ProductID INT FOREIGN KEY REFERENCES StockItems(StockID),
    Quantity DECIMAL(18,2) DEFAULT 1,
    Unit NVARCHAR(20),
    TotalCost DECIMAL(18,2) DEFAULT 0,
    LaborCost DECIMAL(18,2) DEFAULT 0,
    OverheadCost DECIMAL(18,2) DEFAULT 0,
    Notes NVARCHAR(500),
    IsActive BIT DEFAULT 1,
    VersionNo INT DEFAULT 1,
    CreatedDate DATETIME2 DEFAULT GETDATE(),
    CreatedBy INT FOREIGN KEY REFERENCES Users(UserID)
);

-- 27. Üretim Reçete Detayları (Hammaddeler)
CREATE TABLE ProductionRecipeDetails (
    RecipeDetailID INT IDENTITY(1,1) PRIMARY KEY,
    RecipeID INT FOREIGN KEY REFERENCES ProductionRecipes(RecipeID) ON DELETE CASCADE,
    LineNumber INT NOT NULL,
    RawMaterialID INT FOREIGN KEY REFERENCES StockItems(StockID),
    Quantity DECIMAL(18,4) NOT NULL,
    Unit NVARCHAR(20),
    UnitCost DECIMAL(18,4) DEFAULT 0,
    TotalCost DECIMAL(18,2) DEFAULT 0,
    WasteRate DECIMAL(5,2) DEFAULT 0,
    IsActive BIT DEFAULT 1
);

-- 28. Üretim Emirleri
CREATE TABLE ProductionOrders (
    OrderID INT IDENTITY(1,1) PRIMARY KEY,
    OrderCode NVARCHAR(50) UNIQUE NOT NULL,
    OrderDate DATE NOT NULL,
    RecipeID INT FOREIGN KEY REFERENCES ProductionRecipes(RecipeID),
    ProductID INT FOREIGN KEY REFERENCES StockItems(StockID),
    PlannedQuantity DECIMAL(18,2) NOT NULL,
    ProducedQuantity DECIMAL(18,2) DEFAULT 0,
    DefectQuantity DECIMAL(18,2) DEFAULT 0,
    UnitCost DECIMAL(18,4) DEFAULT 0,
    TotalCost DECIMAL(18,2) DEFAULT 0,
    Status NVARCHAR(20) DEFAULT 'Planlandi', -- Planlandi, Uretimde, Tamamlandi, Iptal
    StartDate DATETIME2,
    EndDate DATETIME2,
    ResponsiblePerson NVARCHAR(100),
    Notes NVARCHAR(500),
    CreatedDate DATETIME2 DEFAULT GETDATE(),
    CreatedBy INT FOREIGN KEY REFERENCES Users(UserID)
);

-- 29. Fiyat Grupları
CREATE TABLE PriceGroups (
    PriceGroupID INT IDENTITY(1,1) PRIMARY KEY,
    PriceGroupCode NVARCHAR(20) UNIQUE NOT NULL,
    PriceGroupName NVARCHAR(100) NOT NULL,
    DiscountRate DECIMAL(5,2) DEFAULT 0,
    MarkupRate DECIMAL(5,2) DEFAULT 0,
    IsActive BIT DEFAULT 1,
    CreatedDate DATETIME2 DEFAULT GETDATE()
);

-- 30. Fiyat Grup Ürünleri
CREATE TABLE PriceGroupItems (
    PriceGroupItemID INT IDENTITY(1,1) PRIMARY KEY,
    PriceGroupID INT FOREIGN KEY REFERENCES PriceGroups(PriceGroupID) ON DELETE CASCADE,
    StockID INT FOREIGN KEY REFERENCES StockItems(StockID) ON DELETE CASCADE,
    BasePrice DECIMAL(18,4) NOT NULL,
    PriceWithMarkup DECIMAL(18,4) NOT NULL,
    UNIQUE(PriceGroupID, StockID)
);

-- 31. Kampanyalar
CREATE TABLE Campaigns (
    CampaignID INT IDENTITY(1,1) PRIMARY KEY,
    CampaignCode NVARCHAR(50) UNIQUE NOT NULL,
    CampaignName NVARCHAR(200) NOT NULL,
    CampaignType NVARCHAR(50), -- Indirim, CokAlAzOd, HediyeUrun, Puan, Kupon
    DiscountRate DECIMAL(5,2),
    MinPurchaseAmount DECIMAL(18,2) DEFAULT 0,
    MinQuantity INT DEFAULT 0,
    FreeProductID INT FOREIGN KEY REFERENCES StockItems(StockID),
    FreeQuantity INT DEFAULT 0,
    PointsMultiplier DECIMAL(5,2) DEFAULT 1,
    StartDate DATE NOT NULL,
    EndDate DATE NOT NULL,
    BranchID INT FOREIGN KEY REFERENCES Branches(BranchID),
    IsActive BIT DEFAULT 1,
    Description NVARCHAR(500),
    CreatedBy INT FOREIGN KEY REFERENCES Users(UserID),
    CreatedDate DATETIME2 DEFAULT GETDATE()
);

-- 32. Masraf Merkezleri
CREATE TABLE CostCenters (
    CostCenterID INT IDENTITY(1,1) PRIMARY KEY,
    CostCenterCode NVARCHAR(20) UNIQUE NOT NULL,
    CostCenterName NVARCHAR(100) NOT NULL,
    BranchID INT FOREIGN KEY REFERENCES Branches(BranchID),
    ParentCostCenterID INT,
    BudgetAmount DECIMAL(18,2) DEFAULT 0,
    SpentAmount DECIMAL(18,2) DEFAULT 0,
    ManagerName NVARCHAR(100),
    IsActive BIT DEFAULT 1,
    CreatedDate DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (ParentCostCenterID) REFERENCES CostCenters(CostCenterID)
);

-- 33. CRM Aktiviteleri
CREATE TABLE CRM_Activities (
    ActivityID INT IDENTITY(1,1) PRIMARY KEY,
    ActivityDate DATE NOT NULL,
    ActivityType NVARCHAR(50), -- Telefon, Toplanti, Email, Ziyaret, Teklif
    CurrentAccountID INT FOREIGN KEY REFERENCES CurrentAccounts(CurrentAccountID),
    ContactPerson NVARCHAR(100),
    Subject NVARCHAR(200),
    Description NVARCHAR(MAX),
    Status NVARCHAR(20) DEFAULT 'Planlandi',
    FollowUpDate DATE,
    AssignedTo INT FOREIGN KEY REFERENCES Users(UserID),
    IsCompleted BIT DEFAULT 0,
    CompletedDate DATETIME2,
    CreatedDate DATETIME2 DEFAULT GETDATE(),
    CreatedBy INT FOREIGN KEY REFERENCES Users(UserID)
);

-- 34. Satın Alma Siparişleri
CREATE TABLE PurchaseOrders (
    OrderID INT IDENTITY(1,1) PRIMARY KEY,
    OrderCode NVARCHAR(50) UNIQUE NOT NULL,
    OrderDate DATE NOT NULL,
    DeliveryDate DATE,
    SupplierID INT FOREIGN KEY REFERENCES CurrentAccounts(CurrentAccountID),
    BranchID INT FOREIGN KEY REFERENCES Branches(BranchID),
    Status NVARCHAR(20) DEFAULT 'Beklemede', -- Beklemede, Onaylandi, TeslimEdildi, Iptal
    SubTotal DECIMAL(18,2) DEFAULT 0,
    DiscountAmount DECIMAL(18,2) DEFAULT 0,
    VATAmount DECIMAL(18,2) DEFAULT 0,
    TotalAmount DECIMAL(18,2) DEFAULT 0,
    Notes NVARCHAR(500),
    ApprovedBy INT FOREIGN KEY REFERENCES Users(UserID),
    CreatedBy INT FOREIGN KEY REFERENCES Users(UserID),
    CreatedDate DATETIME2 DEFAULT GETDATE()
);

-- 35. Satın Alma Sipariş Detayları
CREATE TABLE PurchaseOrderDetails (
    OrderDetailID INT IDENTITY(1,1) PRIMARY KEY,
    OrderID INT FOREIGN KEY REFERENCES PurchaseOrders(OrderID) ON DELETE CASCADE,
    LineNumber INT NOT NULL,
    StockID INT FOREIGN KEY REFERENCES StockItems(StockID),
    Description NVARCHAR(200),
    Quantity DECIMAL(18,2) NOT NULL,
    Unit NVARCHAR(20),
    UnitPrice DECIMAL(18,4) NOT NULL,
    TotalAmount DECIMAL(18,2) NOT NULL,
    ReceivedQuantity DECIMAL(18,2) DEFAULT 0
);

-- 36. Müşteri Siparişleri
CREATE TABLE CustomerOrders (
    OrderID INT IDENTITY(1,1) PRIMARY KEY,
    OrderCode NVARCHAR(50) UNIQUE NOT NULL,
    OrderDate DATE NOT NULL,
    CustomerID INT FOREIGN KEY REFERENCES CurrentAccounts(CurrentAccountID),
    BranchID INT FOREIGN KEY REFERENCES Branches(BranchID),
    Status NVARCHAR(20) DEFAULT 'Beklemede',
    SubTotal DECIMAL(18,2) DEFAULT 0,
    DiscountAmount DECIMAL(18,2) DEFAULT 0,
    VATAmount DECIMAL(18,2) DEFAULT 0,
    TotalAmount DECIMAL(18,2) DEFAULT 0,
    PaymentType NVARCHAR(50),
    DeliveryAddress NVARCHAR(500),
    Notes NVARCHAR(500),
    CreatedBy INT FOREIGN KEY REFERENCES Users(UserID),
    CreatedDate DATETIME2 DEFAULT GETDATE()
);

-- 37. Müşteri Sipariş Detayları
CREATE TABLE CustomerOrderDetails (
    OrderDetailID INT IDENTITY(1,1) PRIMARY KEY,
    OrderID INT FOREIGN KEY REFERENCES CustomerOrders(OrderID) ON DELETE CASCADE,
    LineNumber INT NOT NULL,
    StockID INT FOREIGN KEY REFERENCES StockItems(StockID),
    Description NVARCHAR(200),
    Quantity DECIMAL(18,2) NOT NULL,
    Unit NVARCHAR(20),
    UnitPrice DECIMAL(18,4) NOT NULL,
    TotalAmount DECIMAL(18,2) NOT NULL,
    DeliveredQuantity DECIMAL(18,2) DEFAULT 0
);

-- 38. e-Fatura / e-Arşiv
CREATE TABLE EInvoices (
    EInvoiceID INT IDENTITY(1,1) PRIMARY KEY,
    InvoiceNumber NVARCHAR(50) UNIQUE NOT NULL,
    UUID NVARCHAR(100) UNIQUE,
    Profile NVARCHAR(20), -- TEMEL, TICARI
    InvoiceType NVARCHAR(20), -- SATIS, IADE
    Status NVARCHAR(20) DEFAULT 'Taslak',
    GibStatusCode NVARCHAR(50),
    GibResponse TEXT,
    InvoiceID INT FOREIGN KEY REFERENCES Invoices(InvoiceID),
    CreatedDate DATETIME2 DEFAULT GETDATE(),
    CreatedBy INT FOREIGN KEY REFERENCES Users(UserID)
);

-- 39. e-Defter Kayıtları
CREATE TABLE ELedger (
    ELedgerID INT IDENTITY(1,1) PRIMARY KEY,
    PeriodYear INT NOT NULL,
    PeriodMonth INT NOT NULL,
    LedgerType NVARCHAR(20), -- YevmiyeDefteri, KebirDefteri
    Status NVARCHAR(20) DEFAULT 'Hazirlaniyor',
    GibStatusCode NVARCHAR(50),
    CreatedDate DATETIME2 DEFAULT GETDATE(),
    CreatedBy INT FOREIGN KEY REFERENCES Users(UserID),
    UNIQUE(PeriodYear, PeriodMonth, LedgerType)
);

-- 40. Pazaryeri Entegrasyonu
CREATE TABLE MarketplaceListings (
    ListingID INT IDENTITY(1,1) PRIMARY KEY,
    MarketplaceName NVARCHAR(50), -- Ideasoft, Trendyol, Hepsiburada, N11, Amazon
    StockID INT FOREIGN KEY REFERENCES StockItems(StockID),
    MarketplaceProductID NVARCHAR(100),
    MarketplacePrice DECIMAL(18,2),
    ListedQuantity INT DEFAULT 0,
    ListingStatus NVARCHAR(20) DEFAULT 'Aktif',
    LastSyncDate DATETIME2,
    SyncLog TEXT,
    CreatedDate DATETIME2 DEFAULT GETDATE()
);

-- 41. Şubeler Arası Transfer
CREATE TABLE BranchTransfers (
    TransferID INT IDENTITY(1,1) PRIMARY KEY,
    TransferCode NVARCHAR(50) UNIQUE NOT NULL,
    TransferDate DATE NOT NULL,
    SourceBranchID INT FOREIGN KEY REFERENCES Branches(BranchID),
    TargetBranchID INT FOREIGN KEY REFERENCES Branches(BranchID),
    Status NVARCHAR(20) DEFAULT 'Hazirlaniyor',
    Notes NVARCHAR(500),
    CreatedBy INT FOREIGN KEY REFERENCES Users(UserID),
    CreatedDate DATETIME2 DEFAULT GETDATE()
);

-- 42. Transfer Detayları
CREATE TABLE BranchTransferDetails (
    TransferDetailID INT IDENTITY(1,1) PRIMARY KEY,
    TransferID INT FOREIGN KEY REFERENCES BranchTransfers(TransferID) ON DELETE CASCADE,
    StockID INT FOREIGN KEY REFERENCES StockItems(StockID),
    Quantity DECIMAL(18,2) NOT NULL,
    UnitPrice DECIMAL(18,4) DEFAULT 0
);

-- 43. Online Haberleşme Log
CREATE TABLE OnlineCommunication (
    CommID INT IDENTITY(1,1) PRIMARY KEY,
    CommDate DATETIME2 DEFAULT GETDATE(),
    BranchID INT FOREIGN KEY REFERENCES Branches(BranchID),
    CommType NVARCHAR(50), -- DosyaGonderimi, VeriSenkron, Mesaj
    FileName NVARCHAR(200),
    FileSize BIGINT,
    Direction NVARCHAR(10), -- Giden, Gelen
    Status NVARCHAR(20) DEFAULT 'Basarili',
    ErrorMessage NVARCHAR(500)
);

-- 44. Barkod Etiket Şablonları
CREATE TABLE BarcodeTemplates (
    TemplateID INT IDENTITY(1,1) PRIMARY KEY,
    TemplateName NVARCHAR(100) NOT NULL,
    LabelWidth DECIMAL(10,2) NOT NULL,
    LabelHeight DECIMAL(10,2) NOT NULL,
    FieldsConfiguration NVARCHAR(MAX), -- JSON alan yapılandırması
    PrinterName NVARCHAR(100),
    IsDefault BIT DEFAULT 0,
    CreatedDate DATETIME2 DEFAULT GETDATE()
);

-- 45. Banka POS Cihazları (Kredi Kartı Ödeme)
CREATE TABLE BankPOSDevices (
    POSDeviceID INT IDENTITY(1,1) PRIMARY KEY,
    BankName NVARCHAR(100) NOT NULL, -- Akbank, Garanti, YKB, Isbank, Ziraat, Halkbank, Vakifbank
    POSModel NVARCHAR(100),
    TerminalID NVARCHAR(50),
    MerchantID NVARCHAR(50),
    CommissionRate DECIMAL(5,2) DEFAULT 0, -- % komisyon
    InstallmentCommissionRate DECIMAL(5,2) DEFAULT 0, -- Taksitli komisyon farki
    BranchID INT FOREIGN KEY REFERENCES Branches(BranchID),
    ConnectionType NVARCHAR(50), -- TCP/IP, Dial-Up, GPRS
    IPAddress NVARCHAR(50),
    PortNumber INT,
    IsActive BIT DEFAULT 1,
    CreatedDate DATETIME2 DEFAULT GETDATE()
);

-- 46. Taksit Seçenekleri
CREATE TABLE POSInstallmentOptions (
    InstallmentID INT IDENTITY(1,1) PRIMARY KEY,
    POSDeviceID INT FOREIGN KEY REFERENCES BankPOSDevices(POSDeviceID),
    InstallmentCount INT NOT NULL, -- 2,3,4,5,6,7,8,9,10,12
    CommissionRate DECIMAL(5,2) DEFAULT 0,
    MinAmount DECIMAL(18,2) DEFAULT 0,
    IsActive BIT DEFAULT 1
);

-- 47. POS İşlem Logları (Kartlı Ödeme Kayıtları)
CREATE TABLE POSTransactions (
    TransactionID INT IDENTITY(1,1) PRIMARY KEY,
    ReceiptID INT FOREIGN KEY REFERENCES POSReceipts(ReceiptID),
    POSDeviceID INT FOREIGN KEY REFERENCES BankPOSDevices(POSDeviceID),
    TransactionDate DATETIME2 NOT NULL,
    TransactionType NVARCHAR(20), -- Satis, Iade, Vazgecme
    CardNumberMasked NVARCHAR(20), -- ****1234
    CardHolderName NVARCHAR(100),
    CardType NVARCHAR(30), -- Visa, Mastercard, Amex, Troy
    InstallmentCount INT DEFAULT 0, -- 0 = tek cekim
    Amount DECIMAL(18,2) NOT NULL,
    CommissionRate DECIMAL(5,2) DEFAULT 0,
    CommissionAmount DECIMAL(18,2) DEFAULT 0,
    NetAmount DECIMAL(18,2) DEFAULT 0,
    AuthCode NVARCHAR(20), -- Banka yetki kodu
    ReferenceNo NVARCHAR(50), -- Banka referans no
    BatchNo NVARCHAR(20),
    Status NVARCHAR(20) DEFAULT 'Basarili', -- Basarili, Basarisiz, Iptal
    ErrorMessage NVARCHAR(500),
    ResponseData NVARCHAR(MAX),
    CreatedDate DATETIME2 DEFAULT GETDATE()
);

-- 48. Çek Kayıtları
CREATE TABLE Checks (
    CheckID INT IDENTITY(1,1) PRIMARY KEY,
    CheckNo NVARCHAR(50) NOT NULL,
    BankName NVARCHAR(100) NOT NULL,
    BankBranch NVARCHAR(100),
    AccountNo NVARCHAR(50),
    Amount DECIMAL(18,2) NOT NULL,
    CheckDate DATE NOT NULL, -- Keşide tarihi
    MaturityDate DATE NOT NULL, -- Vade tarihi
    CurrentAccountID INT FOREIGN KEY REFERENCES CurrentAccounts(CurrentAccountID),
    CheckType NVARCHAR(20) NOT NULL, -- MusteriCeki, SirketCeki
    CheckStatus NVARCHAR(30) DEFAULT 'Portfoyde', -- Portfoyde, CiroEdildi, TahsilEdildi, Karsiliksiz, IadeEdildi
    ReceivedDate DATE, -- Alış tarihi
    DeliveredDate DATE, -- Teslim/ciro tarihi
    EndorsedTo NVARCHAR(200), -- Ciro edilen kişi/firma
    Description NVARCHAR(500),
    IsCrossed BIT DEFAULT 0, -- Çek (çizgili) mi?
    IsGuaranteed BIT DEFAULT 0, -- Garanti banka çeki mi (teyitli)?
    CreatedDate DATETIME2 DEFAULT GETDATE(),
    CreatedBy INT FOREIGN KEY REFERENCES Users(UserID)
);

-- 49. Çek Ciroları (Check Endorsements)
CREATE TABLE CheckEndorsements (
    EndorsementID INT IDENTITY(1,1) PRIMARY KEY,
    CheckID INT FOREIGN KEY REFERENCES Checks(CheckID) ON DELETE CASCADE,
    EndorsementDate DATE NOT NULL,
    EndorsedTo NVARCHAR(200) NOT NULL, -- Ciro edilen
    EndorsementType NVARCHAR(30), -- TahsilIcin, Ciro, Temlik
    Amount DECIMAL(18,2),
    Description NVARCHAR(500),
    CreatedBy INT FOREIGN KEY REFERENCES Users(UserID),
    CreatedDate DATETIME2 DEFAULT GETDATE()
);

-- 50. Karşılıksız Çek Kayıtları
CREATE TABLE BouncedChecks (
    BouncedID INT IDENTITY(1,1) PRIMARY KEY,
    CheckID INT FOREIGN KEY REFERENCES Checks(CheckID),
    ProtestDate DATE NOT NULL, -- Protesto / karşılıksız tarihi
    Reason NVARCHAR(200), -- Karşılıksız nedeni
    ProtestCost DECIMAL(18,2) DEFAULT 0, -- Protesto masrafı
    LegalProcessStarted BIT DEFAULT 0,
    LegalProcessNote NVARCHAR(500),
    RecoveryAmount DECIMAL(18,2) DEFAULT 0,
    RecoveryDate DATE,
    CreatedDate DATETIME2 DEFAULT GETDATE()
);

-- 51. Çek Bordrosu
CREATE TABLE CheckPortfolios (
    PortfolioID INT IDENTITY(1,1) PRIMARY KEY,
    PortfolioCode NVARCHAR(50) UNIQUE NOT NULL,
    PortfolioDate DATE NOT NULL,
    PortfolioType NVARCHAR(20), -- MusteridenAlinan, SirketTarafindanVerilen
    TotalCount INT DEFAULT 0,
    TotalAmount DECIMAL(18,2) DEFAULT 0,
    Description NVARCHAR(500),
    CreatedDate DATETIME2 DEFAULT GETDATE(),
    CreatedBy INT FOREIGN KEY REFERENCES Users(UserID)
);

-- 52. Çek Bordro Detayları
CREATE TABLE CheckPortfolioDetails (
    PortfolioDetailID INT IDENTITY(1,1) PRIMARY KEY,
    PortfolioID INT FOREIGN KEY REFERENCES CheckPortfolios(PortfolioID) ON DELETE CASCADE,
    CheckID INT FOREIGN KEY REFERENCES Checks(CheckID)
);

-- İndeksler
CREATE INDEX IX_POSReceipts_ReceiptDate ON POSReceipts(ReceiptDate);
CREATE INDEX IX_POSReceipts_SessionID ON POSReceipts(SessionID);
CREATE INDEX IX_ProductionOrders_Status ON ProductionOrders(Status);
CREATE INDEX IX_PurchaseOrders_SupplierID ON PurchaseOrders(SupplierID);
CREATE INDEX IX_CustomerOrders_CustomerID ON CustomerOrders(CustomerID);
CREATE INDEX IX_Campaigns_DateRange ON Campaigns(StartDate, EndDate);
CREATE INDEX IX_CRM_Activities_FollowUp ON CRM_Activities(FollowUpDate, IsCompleted);
CREATE INDEX IX_BranchTransfers_Date ON BranchTransfers(TransferDate);
CREATE INDEX IX_Checks_MaturityDate ON Checks(MaturityDate);
CREATE INDEX IX_Checks_Status ON Checks(CheckStatus);
CREATE INDEX IX_POSTransactions_Date ON POSTransactions(TransactionDate);
CREATE INDEX IX_POSTransactions_Status ON POSTransactions(Status);
