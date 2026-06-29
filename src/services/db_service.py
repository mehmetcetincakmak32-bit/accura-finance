"""
Accura Finance - Veritabanı Servis Katmanı
Tüm iş modülleri için CRUD ve iş mantığı servisleri
"""

import logging
from datetime import datetime, date, timedelta
from typing import Any, Optional, List, Dict
from abc import ABC, abstractmethod

from src.utils.logger import setup_logger
from src.database.connection import get_database_manager


class BaseDBService(ABC):
    """Tüm servisler için temel CRUD işlemleri sağlayan abstract sınıf"""

    def __init__(self, db_manager=None):
        self.db = db_manager or get_database_manager()
        self.logger = setup_logger(self.__class__.__name__)

    def _execute(self, query: str, params: tuple = None, fetch: bool = True) -> Any:
        try:
            self.logger.debug(f"SQL: {query[:150]}... | Params: {params}")
            result = self.db.execute_query(query, params, fetch)
            return result
        except Exception as e:
            self.logger.error(f"Sorgu hatası: {e} | Query: {query[:200]}")
            raise

    def _execute_many(self, query: str, params_list: List[tuple]) -> int:
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()
            conn.close()
            self.logger.info(f"Toplu ekleme: {len(params_list)} kayıt eklendi")
            return cursor.rowcount
        except Exception as e:
            self.logger.error(f"Toplu ekleme hatası: {e}")
            raise

    def get_by_id(self, table: str, id_column: str, id_value: Any) -> Optional[Dict]:
        result = self._execute(f"SELECT * FROM [{table}] WHERE [{id_column}] = ?", (id_value,))
        return result[0] if result else None

    def get_all(self, table: str, order_by: str = None, limit: int = None, offset: int = None) -> List[Dict]:
        query = f"SELECT * FROM [{table}]"
        if order_by:
            query += f" ORDER BY {order_by}"
        if limit:
            query += f" LIMIT {limit}"
        if offset:
            query += f" OFFSET {offset}"
        return self._execute(query)

    def search(self, table: str, search_cols: List[str], term: str, exact: bool = False) -> List[Dict]:
        if exact:
            conditions = " OR ".join(f"[{col}] = ?" for col in search_cols)
            params = tuple(term for _ in search_cols)
        else:
            conditions = " OR ".join(f"[{col}] LIKE ?" for col in search_cols)
            params = tuple(f"%{term}%" for _ in search_cols)
        query = f"SELECT * FROM [{table}] WHERE {conditions}"
        return self._execute(query, params)

    def count(self, table: str, where_clause: str = None, params: tuple = None) -> int:
        query = f"SELECT COUNT(*) as cnt FROM [{table}]"
        if where_clause:
            query += f" WHERE {where_clause}"
        result = self._execute(query, params)
        return result[0]['cnt'] if result else 0

    def insert(self, table: str, data: Dict) -> int:
        columns = ", ".join(f"[{k}]" for k in data.keys())
        placeholders = ", ".join("?" for _ in data)
        values = tuple(data.values())
        query = f"INSERT INTO [{table}] ({columns}) VALUES ({placeholders})"
        self._execute(query, values, fetch=False)
        result = self._execute("SELECT last_insert_rowid() as id")
        new_id = result[0]['id'] if result else None
        self.logger.info(f"Ekleme: {table} ID={new_id}")
        return new_id

    def update(self, table: str, data: Dict, id_column: str, id_value: Any) -> int:
        set_clause = ", ".join(f"[{k}] = ?" for k in data.keys())
        values = tuple(data.values()) + (id_value,)
        query = f"UPDATE [{table}] SET {set_clause} WHERE [{id_column}] = ?"
        result = self._execute(query, values, fetch=False)
        self.logger.info(f"Güncelleme: {table} {id_column}={id_value} | Etkilenen: {result}")
        return result

    def delete(self, table: str, id_column: str, id_value: Any, soft_delete: bool = False) -> int:
        if soft_delete:
            query = f"UPDATE [{table}] SET IsActive = 0, UpdatedDate = datetime('now','localtime') WHERE [{id_column}] = ?"
        else:
            query = f"DELETE FROM [{table}] WHERE [{id_column}] = ?"
        result = self._execute(query, (id_value,), fetch=False)
        self.logger.info(f"Silme: {table} {id_column}={id_value} | Soft={soft_delete} | Etkilenen: {result}")
        return result

    def get_paginated(self, table: str, page: int = 1, per_page: int = 50,
                      order_by: str = None, search_cols: List[str] = None,
                      search_term: str = None, where_clause: str = None,
                      where_params: tuple = None) -> Dict:
        base_query = f"FROM [{table}]"
        conditions = []
        params = []

        if where_clause:
            conditions.append(f"({where_clause})")
            if where_params:
                params.extend(where_params)

        if search_term and search_cols:
            search_conditions = " OR ".join(f"[{col}] LIKE ?" for col in search_cols)
            conditions.append(f"({search_conditions})")
            params.extend([f"%{search_term}%" for _ in search_cols])

        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)

        count_query = f"SELECT COUNT(*) as total {base_query}"
        count_result = self._execute(count_query, tuple(params) if params else None)
        total = count_result[0]['total'] if count_result else 0

        data_query = f"SELECT * {base_query}"
        if order_by:
            data_query += f" ORDER BY {order_by}"
        data_query += f" LIMIT {per_page} OFFSET {(page - 1) * per_page}"

        data = self._execute(data_query, tuple(params) if params else None)
        total_pages = max(1, (total + per_page - 1) // per_page)

        return {
            'data': data,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_previous': page > 1
        }


class AccountingService(BaseDBService):
    """Muhasebe işlemleri servisi"""

    def get_accounts(self, parent_id: int = None) -> List[Dict]:
        if parent_id is not None:
            return self._execute(
                "SELECT * FROM ChartOfAccounts WHERE ParentAccountID = ? ORDER BY AccountCode",
                (parent_id,)
            )
        return self._execute(
            "SELECT * FROM ChartOfAccounts WHERE ParentAccountID IS NULL ORDER BY AccountCode"
        )

    def get_account_balance(self, account_id: int, start_date: str = None, end_date: str = None) -> Dict:
        params = [account_id]
        date_filter = ""
        if start_date and end_date:
            date_filter = " AND je.VoucherDate BETWEEN ? AND ?"
            params.extend([start_date, end_date])

        query = f"""
            SELECT coa.AccountID, coa.AccountCode, coa.AccountName, coa.AccountType,
                   COALESCE(SUM(jed.DebitAmount), 0) as TotalDebit,
                   COALESCE(SUM(jed.CreditAmount), 0) as TotalCredit,
                   CASE
                       WHEN coa.AccountType IN ('Aktif', 'Gider') THEN
                           COALESCE(SUM(jed.DebitAmount), 0) - COALESCE(SUM(jed.CreditAmount), 0)
                       ELSE
                           COALESCE(SUM(jed.CreditAmount), 0) - COALESCE(SUM(jed.DebitAmount), 0)
                   END as Balance
            FROM ChartOfAccounts coa
            LEFT JOIN JournalEntryDetails jed ON coa.AccountID = jed.AccountID
            LEFT JOIN JournalEntries je ON jed.JournalEntryID = je.JournalEntryID
            WHERE coa.AccountID = ?{date_filter}
            GROUP BY coa.AccountID
        """
        result = self._execute(query, tuple(params))
        return result[0] if result else {
            'AccountID': account_id, 'TotalDebit': 0, 'TotalCredit': 0, 'Balance': 0
        }

    def get_trial_balance(self, start_date: str, end_date: str) -> List[Dict]:
        return self._execute("""
            SELECT coa.AccountCode, coa.AccountName, coa.AccountType,
                   COALESCE(SUM(jed.DebitAmount), 0) as DebitAmount,
                   COALESCE(SUM(jed.CreditAmount), 0) as CreditAmount,
                   CASE
                       WHEN coa.AccountType IN ('Aktif', 'Gider') THEN
                           COALESCE(SUM(jed.DebitAmount), 0) - COALESCE(SUM(jed.CreditAmount), 0)
                       ELSE
                           COALESCE(SUM(jed.CreditAmount), 0) - COALESCE(SUM(jed.DebitAmount), 0)
                   END as Balance
            FROM ChartOfAccounts coa
            LEFT JOIN JournalEntryDetails jed ON coa.AccountID = jed.AccountID
            LEFT JOIN JournalEntries je ON jed.JournalEntryID = je.JournalEntryID
                AND je.VoucherDate BETWEEN ? AND ?
            GROUP BY coa.AccountID
            HAVING DebitAmount != 0 OR CreditAmount != 0
            ORDER BY coa.AccountCode
        """, (start_date, end_date))

    def get_income_statement(self, start_date: str, end_date: str) -> List[Dict]:
        return self._execute("""
            SELECT coa.AccountCode, coa.AccountName,
                   COALESCE(SUM(jed.DebitAmount), 0) as DebitAmount,
                   COALESCE(SUM(jed.CreditAmount), 0) as CreditAmount,
                   CASE
                       WHEN coa.AccountType = 'Gelir' THEN
                           COALESCE(SUM(jed.CreditAmount), 0) - COALESCE(SUM(jed.DebitAmount), 0)
                       ELSE
                           COALESCE(SUM(jed.DebitAmount), 0) - COALESCE(SUM(jed.CreditAmount), 0)
                   END as Amount
            FROM ChartOfAccounts coa
            JOIN JournalEntryDetails jed ON coa.AccountID = jed.AccountID
            JOIN JournalEntries je ON jed.JournalEntryID = je.JournalEntryID
            WHERE coa.AccountType IN ('Gelir', 'Gider')
                AND je.VoucherDate BETWEEN ? AND ?
            GROUP BY coa.AccountID
            ORDER BY coa.AccountCode
        """, (start_date, end_date))

    def get_balance_sheet(self, as_of_date: str) -> List[Dict]:
        return self._execute("""
            SELECT coa.AccountCode, coa.AccountName, coa.AccountType, coa.AccountGroup,
                   CASE
                       WHEN coa.AccountType IN ('Aktif', 'Gider') THEN
                           COALESCE(SUM(jed.DebitAmount), 0) - COALESCE(SUM(jed.CreditAmount), 0)
                       ELSE
                           COALESCE(SUM(jed.CreditAmount), 0) - COALESCE(SUM(jed.DebitAmount), 0)
                   END as Balance
            FROM ChartOfAccounts coa
            LEFT JOIN JournalEntryDetails jed ON coa.AccountID = jed.AccountID
            LEFT JOIN JournalEntries je ON jed.JournalEntryID = je.JournalEntryID
                AND je.VoucherDate <= ?
            WHERE coa.AccountType IN ('Aktif', 'Pasif', 'Ozkaynaklar')
            GROUP BY coa.AccountID
            HAVING Balance != 0
            ORDER BY coa.AccountCode
        """, (as_of_date,))

    def get_cash_flow(self, start_date: str, end_date: str) -> List[Dict]:
        return self._execute("""
            SELECT cm.MovementDate, cm.MovementNumber, cm.MovementType,
                   cm.Amount, cm.Description, cr.CashRegisterName
            FROM CashMovements cm
            JOIN CashRegisters cr ON cm.CashRegisterID = cr.CashRegisterID
            WHERE cm.MovementDate BETWEEN ? AND ?
            ORDER BY cm.MovementDate
        """, (start_date, end_date))

    def get_debt_aging(self, as_of_date: str) -> List[Dict]:
        return self._execute("""
            SELECT ca.CurrentAccountCode, ca.CurrentAccountName, ca.CurrentAccountType,
                   inv.InvoiceDate, inv.DueDate, inv.TotalAmount, inv.PaidAmount, inv.RemainingAmount,
                   CASE
                       WHEN julianday(?) - julianday(inv.DueDate) <= 0 THEN 'Vadesi Gelmemis'
                       WHEN julianday(?) - julianday(inv.DueDate) <= 30 THEN '1-30 Gun'
                       WHEN julianday(?) - julianday(inv.DueDate) <= 60 THEN '31-60 Gun'
                       WHEN julianday(?) - julianday(inv.DueDate) <= 90 THEN '61-90 Gun'
                       ELSE '90+ Gun'
                   END as AgingRange,
                   inv.RemainingAmount as AgingAmount
            FROM Invoices inv
            JOIN CurrentAccounts ca ON inv.CurrentAccountID = ca.CurrentAccountID
            WHERE inv.RemainingAmount > 0 AND inv.DueDate <= ?
            ORDER BY AgingRange, ca.CurrentAccountName
        """, (as_of_date, as_of_date, as_of_date, as_of_date, as_of_date))

    def get_vat_report(self, start_date: str, end_date: str) -> List[Dict]:
        return self._execute("""
            SELECT inv.InvoiceType, inv.InvoiceDate, inv.InvoiceNumber,
                   ca.CurrentAccountName, ca.TaxNumber,
                   inv.SubTotal, inv.VATAmount, inv.TotalAmount,
                   jed.VATRate
            FROM Invoices inv
            JOIN CurrentAccounts ca ON inv.CurrentAccountID = ca.CurrentAccountID
            JOIN InvoiceDetails jed ON inv.InvoiceID = jed.InvoiceID
            WHERE inv.InvoiceDate BETWEEN ? AND ?
            ORDER BY inv.InvoiceDate
        """, (start_date, end_date))

    def post_journal_entry(self, entry_data: Dict, details: List[Dict]) -> int:
        voucher_no = entry_data.get('VoucherNumber', f"YV-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        voucher_date = entry_data.get('VoucherDate', date.today().isoformat())
        description = entry_data.get('Description', '')
        created_by = entry_data.get('CreatedBy', 1)

        total_debit = sum(d.get('DebitAmount', 0) for d in details)
        total_credit = sum(d.get('CreditAmount', 0) for d in details)

        je_query = """INSERT INTO JournalEntries
            (VoucherNumber, VoucherDate, Description, TotalDebit, TotalCredit, IsBalanced, CreatedBy)
            VALUES (?, ?, ?, ?, ?, ?, ?)"""
        self._execute(je_query, (
            voucher_no, voucher_date, description,
            total_debit, total_credit, 1 if abs(total_debit - total_credit) < 0.01 else 0,
            created_by
        ), fetch=False)

        result = self._execute("SELECT last_insert_rowid() as id")
        journal_id = result[0]['id']

        for i, det in enumerate(details):
            det_query = """INSERT INTO JournalEntryDetails
                (JournalEntryID, LineNumber, AccountID, CurrentAccountID,
                 Description, DebitAmount, CreditAmount, CurrencyCode, ExchangeRate,
                 DebitAmountLocal, CreditAmountLocal)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
            self._execute(det_query, (
                journal_id, i + 1,
                det.get('AccountID'),
                det.get('CurrentAccountID'),
                det.get('Description', ''),
                det.get('DebitAmount', 0),
                det.get('CreditAmount', 0),
                det.get('CurrencyCode', 'TRY'),
                det.get('ExchangeRate', 1),
                det.get('DebitAmount', 0),
                det.get('CreditAmount', 0)
            ), fetch=False)

        self.logger.info(f"Yevmiye kaydı oluşturuldu: {voucher_no} (ID={journal_id})")
        return journal_id

    def get_general_ledger(self, account_id: int, start_date: str, end_date: str) -> List[Dict]:
        return self._execute("""
            SELECT je.VoucherDate, je.VoucherNumber, je.Description as EntryDescription,
                   jed.Description, jed.DebitAmount, jed.CreditAmount,
                   coa.AccountCode, coa.AccountName
            FROM JournalEntryDetails jed
            JOIN JournalEntries je ON jed.JournalEntryID = je.JournalEntryID
            JOIN ChartOfAccounts coa ON jed.AccountID = coa.AccountID
            WHERE jed.AccountID = ? AND je.VoucherDate BETWEEN ? AND ?
            ORDER BY je.VoucherDate, je.JournalEntryID
        """, (account_id, start_date, end_date))


class InventoryService(BaseDBService):
    """Stok işlemleri servisi"""

    def get_stock_items(self, category_id: int = None, low_stock: bool = False) -> List[Dict]:
        query = """SELECT si.*, sc.CategoryName
                   FROM StockItems si
                   LEFT JOIN StockCategories sc ON si.CategoryID = sc.CategoryID
                   WHERE si.IsActive = 1"""
        params = []
        if category_id is not None:
            query += " AND si.CategoryID = ?"
            params.append(category_id)
        if low_stock:
            query += " AND si.CurrentStock <= si.MinStockLevel"
        query += " ORDER BY si.StockCode"
        return self._execute(query, tuple(params) if params else None)

    def get_stock_card(self, item_id: int) -> Dict:
        result = self._execute("""
            SELECT si.*, sc.CategoryName, sc.CategoryCode
            FROM StockItems si
            LEFT JOIN StockCategories sc ON si.CategoryID = sc.CategoryID
            WHERE si.StockID = ?
        """, (item_id,))
        return result[0] if result else {}

    def get_stock_movements(self, item_id: int, start_date: str = None, end_date: str = None) -> List[Dict]:
        query = """SELECT sm.*, si.StockCode, si.StockName
                   FROM StockMovements sm
                   JOIN StockItems si ON sm.StockID = si.StockID
                   WHERE sm.StockID = ?"""
        params = [item_id]
        if start_date and end_date:
            query += " AND sm.MovementDate BETWEEN ? AND ?"
            params.extend([start_date, end_date])
        query += " ORDER BY sm.MovementDate DESC"
        return self._execute(query, tuple(params))

    def add_stock_movement(self, item_id: int, movement_type: str, quantity: float,
                           unit_price: float, reference_no: str = None, notes: str = None) -> int:
        movement_no = f"HAR-{datetime.now().strftime('%Y%m%d%H%M%S')}-{item_id}"
        movement_date = date.today().isoformat()
        total_value = quantity * unit_price

        query = """INSERT INTO StockMovements
            (MovementNumber, MovementDate, MovementType, StockID, Quantity,
             UnitPrice, TotalValue, Description, CreatedDate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))"""
        self._execute(query, (
            movement_no, movement_date, movement_type, item_id,
            quantity, unit_price, total_value, notes or ''
        ), fetch=False)

        result = self._execute("SELECT last_insert_rowid() as id")
        mov_id = result[0]['id'] if result else None

        sign = 1 if movement_type in ('Giris', 'SayimFazlasi', 'Iade') else -1
        self._execute(
            "UPDATE StockItems SET CurrentStock = CurrentStock + (? * ?), UpdatedDate = datetime('now','localtime') WHERE StockID = ?",
            (sign, quantity, item_id), fetch=False
        )

        self.logger.info(f"Stok hareketi: {movement_no} | Tur: {movement_type} | Miktar: {quantity}")
        return mov_id

    def check_stock_level(self, item_id: int) -> Dict:
        result = self._execute("""
            SELECT StockID, StockCode, StockName, CurrentStock, MinStockLevel, MaxStockLevel,
                   CASE
                       WHEN CurrentStock <= MinStockLevel THEN 'Kritik'
                       WHEN CurrentStock <= MinStockLevel * 1.5 THEN 'Dusuk'
                       WHEN CurrentStock >= MaxStockLevel THEN 'Fazla'
                       ELSE 'Normal'
                   END as StockStatus
            FROM StockItems WHERE StockID = ?
        """, (item_id,))
        return result[0] if result else {}

    def get_low_stock_items(self, threshold: int = 10) -> List[Dict]:
        return self._execute("""
            SELECT si.*, sc.CategoryName,
                   (si.MinStockLevel - si.CurrentStock) as Deficiency
            FROM StockItems si
            LEFT JOIN StockCategories sc ON si.CategoryID = sc.CategoryID
            WHERE si.CurrentStock <= si.MinStockLevel
                AND si.CurrentStock <= ?
                AND si.IsActive = 1
            ORDER BY si.CurrentStock ASC
        """, (threshold,))

    def get_stock_value(self) -> Dict:
        result = self._execute("""
            SELECT COUNT(*) as TotalItems,
                   COALESCE(SUM(CurrentStock), 0) as TotalQuantity,
                   COALESCE(SUM(CurrentStock * PurchasePrice), 0) as TotalValueLIFO,
                   COALESCE(SUM(CurrentStock * SalePrice), 0) as TotalSaleValue
            FROM StockItems WHERE IsActive = 1
        """)
        return result[0] if result else {}

    def get_category_summary(self) -> List[Dict]:
        return self._execute("""
            SELECT sc.CategoryID, sc.CategoryCode, sc.CategoryName,
                   COUNT(si.StockID) as ItemCount,
                   COALESCE(SUM(si.CurrentStock), 0) as TotalStock,
                   COALESCE(SUM(si.CurrentStock * si.PurchasePrice), 0) as TotalValue,
                   COALESCE(SUM(si.CurrentStock * si.SalePrice), 0) as TotalSaleValue
            FROM StockCategories sc
            LEFT JOIN StockItems si ON sc.CategoryID = si.CategoryID AND si.IsActive = 1
            WHERE sc.IsActive = 1
            GROUP BY sc.CategoryID
            ORDER BY sc.CategoryCode
        """)

    def get_valuation_report(self, method: str = 'weighted_average') -> List[Dict]:
        if method == 'weighted_average':
            return self._execute("""
                SELECT si.StockID, si.StockCode, si.StockName, si.Unit,
                       si.CurrentStock, si.PurchasePrice, si.SalePrice,
                       (si.CurrentStock * si.PurchasePrice) as TotalCost,
                       (si.CurrentStock * si.SalePrice) as TotalSaleValue,
                       ((si.SalePrice - si.PurchasePrice) * si.CurrentStock) as ProfitPotential
                FROM StockItems si
                WHERE si.IsActive = 1 AND si.CurrentStock > 0
                ORDER BY si.StockCode
            """)
        return []


class CustomerService(BaseDBService):
    """Cari islemleri servisi"""

    def get_customers(self, type_filter: str = None, is_active: bool = True) -> List[Dict]:
        query = "SELECT * FROM CurrentAccounts WHERE IsActive = ?"
        params = [1 if is_active else 0]
        if type_filter:
            query += " AND CurrentAccountType = ?"
            params.append(type_filter)
        query += " ORDER BY CurrentAccountCode"
        return self._execute(query, tuple(params))

    def get_customer_detail(self, customer_id: int) -> Dict:
        result = self._execute("""
            SELECT ca.*,
                   (SELECT COUNT(*) FROM Invoices WHERE CurrentAccountID = ca.CurrentAccountID) as InvoiceCount,
                   (SELECT COALESCE(SUM(TotalAmount), 0) FROM Invoices WHERE CurrentAccountID = ca.CurrentAccountID) as TotalTransactionAmount,
                   (SELECT COALESCE(SUM(PaidAmount), 0) FROM Invoices WHERE CurrentAccountID = ca.CurrentAccountID) as TotalPaidAmount
            FROM CurrentAccounts ca
            WHERE ca.CurrentAccountID = ?
        """, (customer_id,))
        return result[0] if result else {}

    def get_customer_balance(self, customer_id: int) -> Dict:
        result = self._execute("""
            SELECT ca.CurrentAccountID, ca.CurrentAccountCode, ca.CurrentAccountName,
                   ca.CurrentAccountType, ca.Balance,
                   (SELECT COALESCE(SUM(RemainingAmount), 0) FROM Invoices
                    WHERE CurrentAccountID = ca.CurrentAccountID AND RemainingAmount > 0) as OutstandingBalance,
                   (SELECT COUNT(*) FROM Invoices
                    WHERE CurrentAccountID = ca.CurrentAccountID AND RemainingAmount > 0 AND DueDate < date('now')) as OverdueInvoiceCount
            FROM CurrentAccounts ca
            WHERE ca.CurrentAccountID = ?
        """, (customer_id,))
        return result[0] if result else {}

    def get_customer_transactions(self, customer_id: int, start_date: str = None, end_date: str = None) -> List[Dict]:
        query = """
            SELECT inv.InvoiceID, inv.InvoiceNumber, inv.InvoiceType,
                   inv.InvoiceDate, inv.DueDate, inv.SubTotal,
                   inv.VATAmount, inv.TotalAmount, inv.PaidAmount,
                   inv.RemainingAmount, inv.Notes
            FROM Invoices inv
            WHERE inv.CurrentAccountID = ?"""
        params = [customer_id]
        if start_date and end_date:
            query += " AND inv.InvoiceDate BETWEEN ? AND ?"
            params.extend([start_date, end_date])
        query += " ORDER BY inv.InvoiceDate DESC"
        return self._execute(query, tuple(params))

    def get_aging_report(self, as_of_date: str) -> List[Dict]:
        return self._execute("""
            SELECT ca.CurrentAccountID, ca.CurrentAccountCode, ca.CurrentAccountName,
                   ca.CurrentAccountType,
                   COALESCE(SUM(CASE WHEN julianday(?) - julianday(inv.DueDate) <= 0 THEN inv.RemainingAmount ELSE 0 END), 0) as VadesiGelmemis,
                   COALESCE(SUM(CASE WHEN julianday(?) - julianday(inv.DueDate) BETWEEN 1 AND 30 THEN inv.RemainingAmount ELSE 0 END), 0) as Gun1_30,
                   COALESCE(SUM(CASE WHEN julianday(?) - julianday(inv.DueDate) BETWEEN 31 AND 60 THEN inv.RemainingAmount ELSE 0 END), 0) as Gun31_60,
                   COALESCE(SUM(CASE WHEN julianday(?) - julianday(inv.DueDate) BETWEEN 61 AND 90 THEN inv.RemainingAmount ELSE 0 END), 0) as Gun61_90,
                   COALESCE(SUM(CASE WHEN julianday(?) - julianday(inv.DueDate) > 90 THEN inv.RemainingAmount ELSE 0 END), 0) as Gun90Plus,
                   COALESCE(SUM(inv.RemainingAmount), 0) as TotalBalance
            FROM CurrentAccounts ca
            LEFT JOIN Invoices inv ON ca.CurrentAccountID = inv.CurrentAccountID
                AND inv.RemainingAmount > 0
            WHERE ca.IsActive = 1
            GROUP BY ca.CurrentAccountID
            HAVING TotalBalance > 0
            ORDER BY TotalBalance DESC
        """, (as_of_date, as_of_date, as_of_date, as_of_date, as_of_date))

    def get_overdue_accounts(self, days: int = 30) -> List[Dict]:
        return self._execute("""
            SELECT ca.*, inv.InvoiceNumber, inv.InvoiceDate, inv.DueDate,
                   inv.TotalAmount, inv.RemainingAmount,
                   julianday('now') - julianday(inv.DueDate) as OverdueDays
            FROM CurrentAccounts ca
            JOIN Invoices inv ON ca.CurrentAccountID = inv.CurrentAccountID
            WHERE inv.RemainingAmount > 0
                AND inv.DueDate < date('now', ?)
            ORDER BY OverdueDays DESC
        """, (f"-{days} days",))

    def get_top_customers(self, limit: int = 10, by: str = 'balance') -> List[Dict]:
        order_col = "ca.Balance" if by == 'balance' else "TotalAmount"
        return self._execute(f"""
            SELECT ca.CurrentAccountID, ca.CurrentAccountCode, ca.CurrentAccountName,
                   ca.CurrentAccountType, ca.Balance,
                   COALESCE(SUM(inv.TotalAmount), 0) as TotalAmount,
                   COUNT(inv.InvoiceID) as InvoiceCount
            FROM CurrentAccounts ca
            LEFT JOIN Invoices inv ON ca.CurrentAccountID = inv.CurrentAccountID
            WHERE ca.IsActive = 1
            GROUP BY ca.CurrentAccountID
            ORDER BY {order_col} DESC
            LIMIT ?
        """, (limit,))

    def update_balance(self, customer_id: int) -> float:
        result = self._execute("""
            SELECT COALESCE(SUM(
                CASE WHEN InvoiceType = 'Satis' THEN RemainingAmount
                     ELSE -RemainingAmount END
            ), 0) as Balance
            FROM Invoices WHERE CurrentAccountID = ?
        """, (customer_id,))
        balance = result[0]['Balance'] if result else 0.0
        self._execute(
            "UPDATE CurrentAccounts SET Balance = ? WHERE CurrentAccountID = ?",
            (balance, customer_id), fetch=False
        )
        self.logger.info(f"Cari bakiye guncellendi: ID={customer_id} | Bakiye={balance}")
        return balance


class InvoiceService(BaseDBService):
    """Fatura islemleri servisi"""

    def create_invoice(self, invoice_data: Dict, details: List[Dict]) -> int:
        inv_no = invoice_data.get('InvoiceNumber', f"FAT-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        inv_type = invoice_data.get('InvoiceType', 'Satis')
        inv_date = invoice_data.get('InvoiceDate', date.today().isoformat())
        customer_id = invoice_data.get('CurrentAccountID')
        due_date = invoice_data.get('DueDate', inv_date)
        notes = invoice_data.get('Notes', '')
        created_by = invoice_data.get('CreatedBy', 1)

        sub_total = sum(d.get('NetAmount', d.get('TotalAmount', 0)) for d in details)
        vat_amount = sum(d.get('VATAmount', 0) for d in details)
        discount_amount = sum(d.get('DiscountAmount', 0) for d in details)
        total_amount = sub_total + vat_amount - discount_amount

        inv_query = """INSERT INTO Invoices
            (InvoiceNumber, InvoiceType, InvoiceDate, CurrentAccountID,
             SubTotal, VATAmount, DiscountAmount, TotalAmount, PaidAmount,
             RemainingAmount, DueDate, Notes, CreatedBy, CreatedDate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, datetime('now','localtime'))"""
        self._execute(inv_query, (
            inv_no, inv_type, inv_date, customer_id,
            sub_total, vat_amount, discount_amount, total_amount,
            total_amount, due_date, notes, created_by
        ), fetch=False)

        result = self._execute("SELECT last_insert_rowid() as id")
        invoice_id = result[0]['id']

        for i, det in enumerate(details):
            det_query = """INSERT INTO InvoiceDetails
                (InvoiceID, LineNumber, StockID, Description, Quantity, Unit,
                 UnitPrice, DiscountRate, DiscountAmount, NetAmount, VATRate,
                 VATAmount, TotalAmount)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
            self._execute(det_query, (
                invoice_id, i + 1,
                det.get('StockID'),
                det.get('Description', ''),
                det.get('Quantity', 1),
                det.get('Unit', 'Adet'),
                det.get('UnitPrice', 0),
                det.get('DiscountRate', 0),
                det.get('DiscountAmount', 0),
                det.get('NetAmount', det.get('Quantity', 1) * det.get('UnitPrice', 0)),
                det.get('VATRate', 18),
                det.get('VATAmount', 0),
                det.get('TotalAmount', det.get('NetAmount', 0))
            ), fetch=False)

            if det.get('StockID'):
                mov_type = 'Cikis' if inv_type == 'Satis' else 'Giris'
                qty = det.get('Quantity', 0)
                price = det.get('UnitPrice', 0)
                self._execute("""INSERT INTO StockMovements
                    (MovementNumber, MovementDate, MovementType, StockID, Quantity,
                     UnitPrice, TotalValue, InvoiceID, Description, CreatedDate)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))""", (
                    f"FAT-{invoice_id}-{i+1}", inv_date, mov_type,
                    det.get('StockID'), qty, price, qty * price,
                    invoice_id, f"Fatura #{inv_no} - {det.get('Description', '')}"
                ), fetch=False)

                sign = -1 if inv_type == 'Satis' else 1
                self._execute(
                    "UPDATE StockItems SET CurrentStock = CurrentStock + (? * ?) WHERE StockID = ?",
                    (sign, qty, det.get('StockID')), fetch=False
                )

        self._execute(
            "UPDATE CurrentAccounts SET Balance = Balance + ? WHERE CurrentAccountID = ?",
            (total_amount if inv_type == 'Satis' else -total_amount, customer_id), fetch=False
        )

        self.logger.info(f"Fatura olusturuldu: {inv_no} (ID={invoice_id}) | Toplam: {total_amount}")
        return invoice_id

    def get_invoices(self, type_filter: str = None, status_filter: str = None,
                     date_range: tuple = None) -> List[Dict]:
        query = """SELECT inv.*, ca.CurrentAccountCode, ca.CurrentAccountName
                   FROM Invoices inv
                   JOIN CurrentAccounts ca ON inv.CurrentAccountID = ca.CurrentAccountID
                   WHERE 1=1"""
        params = []
        if type_filter:
            query += " AND inv.InvoiceType = ?"
            params.append(type_filter)
        if status_filter == 'odendi':
            query += " AND inv.RemainingAmount <= 0"
        elif status_filter == 'odenmedi':
            query += " AND inv.RemainingAmount > 0"
        elif status_filter == 'gecikmis':
            query += " AND inv.RemainingAmount > 0 AND inv.DueDate < date('now')"
        if date_range:
            query += " AND inv.InvoiceDate BETWEEN ? AND ?"
            params.extend(date_range)
        query += " ORDER BY inv.InvoiceDate DESC"
        return self._execute(query, tuple(params) if params else None)

    def get_invoice_detail(self, invoice_id: int) -> Dict:
        inv = self._execute("""
            SELECT inv.*, ca.CurrentAccountCode, ca.CurrentAccountName,
                   ca.TaxNumber, ca.TaxOffice, ca.Address, ca.Phone, ca.Email,
                   u.FullName as CreatedByName
            FROM Invoices inv
            JOIN CurrentAccounts ca ON inv.CurrentAccountID = ca.CurrentAccountID
            LEFT JOIN Users u ON inv.CreatedBy = u.UserID
            WHERE inv.InvoiceID = ?
        """, (invoice_id,))
        if not inv:
            return {}
        invoice = inv[0]
        invoice['details'] = self._execute("""
            SELECT ind.*, si.StockCode, si.StockName
            FROM InvoiceDetails ind
            LEFT JOIN StockItems si ON ind.StockID = si.StockID
            WHERE ind.InvoiceID = ?
            ORDER BY ind.LineNumber
        """, (invoice_id,))
        return invoice

    def get_invoice_status(self, invoice_id: int) -> Dict:
        result = self._execute("""
            SELECT InvoiceID, InvoiceNumber, InvoiceType, InvoiceDate,
                   TotalAmount, PaidAmount, RemainingAmount, DueDate, IsPosted,
                   CASE
                       WHEN RemainingAmount <= 0 THEN 'Odendi'
                       WHEN DueDate < date('now') THEN 'Gecikmis'
                       ELSE 'Bekliyor'
                   END as PaymentStatus
            FROM Invoices WHERE InvoiceID = ?
        """, (invoice_id,))
        return result[0] if result else {}

    def cancel_invoice(self, invoice_id: int) -> bool:
        inv = self.get_by_id('Invoices', 'InvoiceID', invoice_id)
        if not inv:
            return False

        self._execute(
            "UPDATE Invoices SET RemainingAmount = 0, Notes = COALESCE(Notes || ' | ', '') || 'IPTAL EDILDI' WHERE InvoiceID = ?",
            (invoice_id,), fetch=False
        )
        self._execute(
            "UPDATE CurrentAccounts SET Balance = Balance - ? WHERE CurrentAccountID = ?",
            (inv['TotalAmount'] if inv['InvoiceType'] == 'Satis' else -inv['TotalAmount'],
             inv['CurrentAccountID']), fetch=False
        )

        movements = self._execute(
            "SELECT * FROM StockMovements WHERE InvoiceID = ?", (invoice_id,)
        )
        for mov in movements:
            sign = 1 if mov['MovementType'] == 'Cikis' else -1
            self._execute(
                "UPDATE StockItems SET CurrentStock = CurrentStock + (? * ?) WHERE StockID = ?",
                (sign, mov['Quantity'], mov['StockID']), fetch=False
            )

        self.logger.info(f"Fatura iptal edildi: ID={invoice_id}")
        return True

    def get_payment_schedule(self, invoice_id: int) -> List[Dict]:
        inv = self.get_by_id('Invoices', 'InvoiceID', invoice_id)
        if not inv:
            return []

        schedule = []
        remaining = inv['RemainingAmount']
        due = inv['DueDate']
        due_date = datetime.strptime(due, '%Y-%m-%d') if isinstance(due, str) else due

        for i in range(3):
            if remaining <= 0:
                break
            installment_amount = remaining / (3 - i)
            installment_date = (due_date + timedelta(days=30 * (i + 1))).strftime('%Y-%m-%d')
            schedule.append({
                'installment_no': i + 1,
                'due_date': installment_date,
                'amount': round(installment_amount, 2),
                'status': 'Bekliyor'
            })
            remaining -= installment_amount

        return schedule

    def get_monthly_invoice_summary(self, year: int) -> List[Dict]:
        return self._execute("""
            SELECT strftime('%m', InvoiceDate) as Month,
                   COUNT(*) as InvoiceCount,
                   SUM(CASE WHEN InvoiceType = 'Satis' THEN TotalAmount ELSE 0 END) as SalesTotal,
                   SUM(CASE WHEN InvoiceType = 'Alis' THEN TotalAmount ELSE 0 END) as PurchaseTotal,
                   SUM(VATAmount) as TotalVAT,
                   SUM(PaidAmount) as TotalPaid,
                   SUM(RemainingAmount) as TotalRemaining
            FROM Invoices
            WHERE strftime('%Y', InvoiceDate) = ?
            GROUP BY strftime('%m', InvoiceDate)
            ORDER BY Month
        """, (str(year),))

    def get_daily_sales(self, date_str: str) -> List[Dict]:
        return self._execute("""
            SELECT inv.InvoiceID, inv.InvoiceNumber, inv.InvoiceDate,
                   ca.CurrentAccountName, inv.TotalAmount, inv.VATAmount,
                   inv.PaidAmount, inv.RemainingAmount, inv.IsPosted
            FROM Invoices inv
            JOIN CurrentAccounts ca ON inv.CurrentAccountID = ca.CurrentAccountID
            WHERE inv.InvoiceDate = ? AND inv.InvoiceType = 'Satis'
            ORDER BY inv.InvoiceNumber
        """, (date_str,))


class POSService(BaseDBService):
    """POS islemleri servisi"""

    def create_session(self, user_id: int, cash_register_id: int, branch_id: int = None) -> int:
        query = """INSERT INTO POS_Sessions
            (POSRegisterID, UserID, OpeningDate, OpeningAmount, Status, IsActive)
            VALUES (?, ?, datetime('now','localtime'), 0, 'Acik', 1)"""
        self._execute(query, (cash_register_id, user_id), fetch=False)
        result = self._execute("SELECT last_insert_rowid() as id")
        session_id = result[0]['id'] if result else None
        self.logger.info(f"POS oturumu acildi: SessionID={session_id}, Kullanici={user_id}")
        return session_id

    def close_session(self, session_id: int, closing_amount: float) -> bool:
        self._execute("""
            UPDATE POS_Sessions SET
                ClosingDate = datetime('now','localtime'),
                ClosingAmount = ?,
                Status = 'Kapali',
                IsActive = 0
            WHERE SessionID = ?
        """, (closing_amount, session_id), fetch=False)
        self.logger.info(f"POS oturumu kapatildi: SessionID={session_id}, Kapanis={closing_amount}")
        return True

    def create_sale(self, sale_data: Dict, items: List[Dict], payments: List[Dict]) -> int:
        receipt_no = sale_data.get('ReceiptNumber', f"POS-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        session_id = sale_data.get('SessionID')
        register_id = sale_data.get('POSRegisterID')
        branch_id = sale_data.get('BranchID')
        user_id = sale_data.get('UserID', 1)
        customer_id = sale_data.get('CurrentAccountID')
        receipt_date = sale_data.get('ReceiptDate', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        sub_total = sum(it.get('TotalAmount', it.get('Quantity', 1) * it.get('UnitPrice', 0)) for it in items)
        discount = sum(it.get('DiscountAmount', 0) for it in items)
        vat = sum(it.get('VATAmount', 0) for it in items)
        total = sub_total - discount + vat

        query = """INSERT INTO POSReceipts
            (ReceiptNumber, SessionID, POSRegisterID, BranchID, UserID, CurrentAccountID,
             ReceiptDate, ReceiptType, SubTotal, DiscountAmount, VATAmount, TotalAmount,
             PaidAmount, IsCancelled, CreatedDate)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Satis', ?, ?, ?, ?, 0, 0, datetime('now','localtime'))"""
        self._execute(query, (
            receipt_no, session_id, register_id, branch_id, user_id, customer_id,
            receipt_date, sub_total, discount, vat, total
        ), fetch=False)

        result = self._execute("SELECT last_insert_rowid() as id")
        receipt_id = result[0]['id']

        for i, it in enumerate(items):
            det_query = """INSERT INTO POSReceiptDetails
                (ReceiptID, LineNumber, StockID, StockName, Barcode, Quantity,
                 UnitPrice, DiscountRate, DiscountAmount, NetPrice, VATRate,
                 VATAmount, TotalAmount, CostPrice)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
            qty = it.get('Quantity', 1)
            price = it.get('UnitPrice', 0)
            disc_rate = it.get('DiscountRate', 0)
            disc_amt = it.get('DiscountAmount', 0)
            net_price = price - disc_amt / qty if qty > 0 else price
            vat_rate = it.get('VATRate', 18)
            vat_amt = it.get('VATAmount', (net_price * qty) * vat_rate / 100)
            total_amt = it.get('TotalAmount', net_price * qty + vat_amt)
            cost_price = it.get('CostPrice', 0)

            self._execute(det_query, (
                receipt_id, i + 1, it.get('StockID'), it.get('StockName', ''),
                it.get('Barcode'), qty, price, disc_rate, disc_amt,
                net_price, vat_rate, vat_amt, total_amt, cost_price
            ), fetch=False)

            if it.get('StockID'):
                self._execute(
                    "UPDATE StockItems SET CurrentStock = CurrentStock - ? WHERE StockID = ?",
                    (qty, it.get('StockID')), fetch=False
                )

        payment_total = sum(p.get('Amount', 0) for p in payments)
        self._execute(
            "UPDATE POSReceipts SET PaidAmount = ? WHERE ReceiptID = ?",
            (payment_total, receipt_id), fetch=False
        )

        if session_id:
            self._execute("""
                UPDATE POS_Sessions SET
                    TotalSales = TotalSales + ?,
                    CashSales = CashSales + ?,
                    DiscountAmount = DiscountAmount + ?
                WHERE SessionID = ?
            """, (total, payment_total, discount, session_id), fetch=False)

        self.logger.info(f"POS satis: {receipt_no} (ID={receipt_id}) | Toplam: {total}")
        return receipt_id

    def cancel_sale(self, receipt_id: int) -> bool:
        receipt = self.get_by_id('POSReceipts', 'ReceiptID', receipt_id)
        if not receipt or receipt.get('IsCancelled'):
            return False

        self._execute(
            "UPDATE POSReceipts SET IsCancelled = 1, CancelReason = 'Kullanici iptali' WHERE ReceiptID = ?",
            (receipt_id,), fetch=False
        )

        details = self._execute(
            "SELECT * FROM POSReceiptDetails WHERE ReceiptID = ?", (receipt_id,)
        )
        for det in details:
            if det.get('StockID'):
                self._execute(
                    "UPDATE StockItems SET CurrentStock = CurrentStock + ? WHERE StockID = ?",
                    (det['Quantity'], det['StockID']), fetch=False
                )

        self.logger.info(f"POS satis iptal: ReceiptID={receipt_id}")
        return True

    def get_daily_sales(self, date_str: str, branch_id: int = None) -> List[Dict]:
        query = """SELECT r.*, b.BranchName, u.FullName as UserName
                   FROM POSReceipts r
                   LEFT JOIN Branches b ON r.BranchID = b.BranchID
                   LEFT JOIN Users u ON r.UserID = u.UserID
                   WHERE date(r.ReceiptDate) = ? AND r.IsCancelled = 0"""
        params = [date_str]
        if branch_id:
            query += " AND r.BranchID = ?"
            params.append(branch_id)
        query += " ORDER BY r.ReceiptDate"
        return self._execute(query, tuple(params))

    def get_hourly_sales(self, date_str: str) -> List[Dict]:
        return self._execute("""
            SELECT strftime('%H', ReceiptDate) as Hour,
                   COUNT(*) as ReceiptCount,
                   SUM(TotalAmount) as TotalSales,
                   SUM(CASE WHEN PaymentType = 'Nakit' THEN TotalAmount ELSE 0 END) as CashSales,
                   SUM(CASE WHEN PaymentType = 'KrediKarti' THEN TotalAmount ELSE 0 END) as CreditSales
            FROM POSReceipts
            WHERE date(ReceiptDate) = ? AND IsCancelled = 0
            GROUP BY strftime('%H', ReceiptDate)
            ORDER BY Hour
        """, (date_str,))

    def get_payment_summary(self, date_str: str, branch_id: int = None) -> List[Dict]:
        query = """SELECT PaymentType,
                          COUNT(*) as TransactionCount,
                          SUM(TotalAmount) as TotalAmount
                   FROM POSReceipts
                   WHERE date(ReceiptDate) = ? AND IsCancelled = 0"""
        params = [date_str]
        if branch_id:
            query += " AND BranchID = ?"
            params.append(branch_id)
        query += " GROUP BY PaymentType"
        return self._execute(query, tuple(params))

    def get_top_products(self, date_range: tuple, limit: int = 10) -> List[Dict]:
        return self._execute("""
            SELECT si.StockID, si.StockCode, si.StockName,
                   SUM(pd.Quantity) as TotalQuantity,
                   SUM(pd.TotalAmount) as TotalAmount,
                   COUNT(DISTINCT r.ReceiptID) as SaleCount
            FROM POSReceiptDetails pd
            JOIN POSReceipts r ON pd.ReceiptID = r.ReceiptID
            JOIN StockItems si ON pd.StockID = si.StockID
            WHERE date(r.ReceiptDate) BETWEEN ? AND ?
                AND r.IsCancelled = 0
            GROUP BY si.StockID
            ORDER BY TotalQuantity DESC
            LIMIT ?
        """, (date_range[0], date_range[1], limit))

    def get_cashier_performance(self, user_id: int, date_range: tuple) -> List[Dict]:
        return self._execute("""
            SELECT u.UserID, u.FullName,
                   COUNT(r.ReceiptID) as ReceiptCount,
                   SUM(r.TotalAmount) as TotalSales,
                   SUM(r.DiscountAmount) as TotalDiscount,
                   AVG(r.TotalAmount) as AvgReceipt,
                   SUM(r.PointsEarned) as TotalPoints
            FROM POSReceipts r
            JOIN Users u ON r.UserID = u.UserID
            WHERE r.UserID = ?
                AND date(r.ReceiptDate) BETWEEN ? AND ?
                AND r.IsCancelled = 0
            GROUP BY u.UserID
        """, (user_id, date_range[0], date_range[1]))


class CheckService(BaseDBService):
    """Cek islemleri servisi"""

    def register_check(self, check_data: Dict) -> int:
        check_no = check_data.get('CheckNo')
        bank = check_data.get('BankName', '')
        branch = check_data.get('BankBranch', '')
        account_no = check_data.get('AccountNo', '')
        amount = check_data.get('Amount', 0)
        check_date = check_data.get('CheckDate', date.today().isoformat())
        maturity = check_data.get('MaturityDate', check_date)
        customer_id = check_data.get('CurrentAccountID')
        check_type = check_data.get('CheckType', 'Musteri')
        status = check_data.get('CheckStatus', 'Portfoyde')
        received_date = check_data.get('ReceivedDate', date.today().isoformat())
        created_by = check_data.get('CreatedBy', 1)

        query = """INSERT INTO Checks
            (CheckNo, BankName, BankBranch, AccountNo, Amount,
             CheckDate, MaturityDate, CurrentAccountID, CheckType,
             CheckStatus, ReceivedDate, Description, CreatedBy, CreatedDate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))"""
        self._execute(query, (
            check_no, bank, branch, account_no, amount,
            check_date, maturity, customer_id, check_type,
            status, received_date, check_data.get('Description', ''),
            created_by
        ), fetch=False)

        result = self._execute("SELECT last_insert_rowid() as id")
        check_id = result[0]['id'] if result else None
        self.logger.info(f"Cek kaydedildi: {check_no} (ID={check_id}) | Tutar: {amount}")
        return check_id

    def endorse_check(self, check_id: int, endorse_data: Dict) -> bool:
        endorsed_to = endorse_data.get('EndorsedTo', '')
        endorse_date = endorse_data.get('EndorsementDate', date.today().isoformat())
        amount = endorse_data.get('Amount', 0)
        created_by = endorse_data.get('CreatedBy', 1)

        self._execute("""INSERT INTO CheckEndorsements
            (CheckID, EndorsementDate, EndorsedTo, EndorsementType, Amount, Description, CreatedBy, CreatedDate)
            VALUES (?, ?, ?, 'Ciro', ?, ?, ?, datetime('now','localtime'))""", (
            check_id, endorse_date, endorsed_to, amount,
            endorse_data.get('Description', ''), created_by
        ), fetch=False)

        self._execute(
            "UPDATE Checks SET CheckStatus = 'CiroEdildi', EndorsedTo = ? WHERE CheckID = ?",
            (endorsed_to, check_id), fetch=False
        )
        self.logger.info(f"Cek ciro edildi: CheckID={check_id} -> {endorsed_to}")
        return True

    def collect_check(self, check_id: int) -> bool:
        check = self.get_by_id('Checks', 'CheckID', check_id)
        if not check:
            return False

        self._execute(
            "UPDATE Checks SET CheckStatus = 'TahsilEdildi', DeliveredDate = date('now') WHERE CheckID = ?",
            (check_id,), fetch=False
        )
        self.logger.info(f"Cek tahsil edildi: CheckID={check_id}")
        return True

    def bounce_check(self, check_id: int, reason: str) -> bool:
        check = self.get_by_id('Checks', 'CheckID', check_id)
        if not check:
            return False

        self._execute(
            "UPDATE Checks SET CheckStatus = 'Karsiliksiz' WHERE CheckID = ?",
            (check_id,), fetch=False
        )
        self._execute("""INSERT INTO BouncedChecks
            (CheckID, ProtestDate, Reason, CreatedDate)
            VALUES (?, date('now'), ?, datetime('now','localtime'))""",
            (check_id, reason), fetch=False)
        self.logger.warning(f"Cek karsiliksiz: CheckID={check_id} | Sebep: {reason}")
        return True

    def protest_check(self, check_id: int) -> bool:
        self._execute(
            "UPDATE Checks SET CheckStatus = 'Protestolu' WHERE CheckID = ?",
            (check_id,), fetch=False
        )
        self._execute(
            "UPDATE BouncedChecks SET LegalProcessStarted = 1 WHERE CheckID = ?",
            (check_id,), fetch=False
        )
        self.logger.info(f"Cek protesto edildi: CheckID={check_id}")
        return True

    def get_portfolio(self, status_filter: str = None) -> List[Dict]:
        query = """SELECT c.*, ca.CurrentAccountCode, ca.CurrentAccountName
                   FROM Checks c
                   LEFT JOIN CurrentAccounts ca ON c.CurrentAccountID = ca.CurrentAccountID
                   WHERE 1=1"""
        params = []
        if status_filter:
            query += " AND c.CheckStatus = ?"
            params.append(status_filter)
        query += " ORDER BY c.MaturityDate"
        return self._execute(query, tuple(params) if params else None)

    def get_maturing_checks(self, days: int = 30) -> List[Dict]:
        return self._execute("""
            SELECT c.*, ca.CurrentAccountCode, ca.CurrentAccountName
            FROM Checks c
            LEFT JOIN CurrentAccounts ca ON c.CurrentAccountID = ca.CurrentAccountID
            WHERE c.CheckStatus = 'Portfoyde'
                AND c.MaturityDate BETWEEN date('now') AND date('now', ?)
            ORDER BY c.MaturityDate
        """, (f"+{days} days",))

    def get_bounced_checks(self) -> List[Dict]:
        return self._execute("""
            SELECT c.*, bc.ProtestDate, bc.Reason, bc.LegalProcessStarted,
                   bc.RecoveryAmount, bc.RecoveryDate,
                   ca.CurrentAccountCode, ca.CurrentAccountName
            FROM Checks c
            JOIN BouncedChecks bc ON c.CheckID = bc.CheckID
            LEFT JOIN CurrentAccounts ca ON c.CurrentAccountID = ca.CurrentAccountID
            ORDER BY bc.ProtestDate DESC
        """)

    def create_portfolio(self, portfolio_data: Dict, check_ids: List[int]) -> int:
        portfolio_code = portfolio_data.get('PortfolioCode', f"BRD-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        portfolio_date = portfolio_data.get('PortfolioDate', date.today().isoformat())
        port_type = portfolio_data.get('PortfolioType', 'Tahsilat')
        created_by = portfolio_data.get('CreatedBy', 1)

        checks = []
        total_amount = 0
        for cid in check_ids:
            ch = self.get_by_id('Checks', 'CheckID', cid)
            if ch:
                checks.append(ch)
                total_amount += ch['Amount']
                self._execute(
                    "UPDATE Checks SET CheckStatus = 'Portfoyde' WHERE CheckID = ?",
                    (cid,), fetch=False
                )

        query = """INSERT INTO CheckPortfolios
            (PortfolioCode, PortfolioDate, PortfolioType, TotalCount, TotalAmount, Description, CreatedBy, CreatedDate)
            VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))"""
        self._execute(query, (
            portfolio_code, portfolio_date, port_type,
            len(checks), total_amount, portfolio_data.get('Description', ''),
            created_by
        ), fetch=False)
        result = self._execute("SELECT last_insert_rowid() as id")
        portfolio_id = result[0]['id'] if result else None

        self.logger.info(f"Bordro olusturuldu: {portfolio_code} (ID={portfolio_id}) | {len(checks)} cek | Toplam: {total_amount}")
        return portfolio_id

    def get_check_report(self, start_date: str, end_date: str) -> List[Dict]:
        return self._execute("""
            SELECT c.CheckStatus, COUNT(*) as Count, SUM(c.Amount) as TotalAmount
            FROM Checks c
            WHERE c.CreatedDate BETWEEN ? AND ?
            GROUP BY c.CheckStatus
        """, (start_date, end_date))


class ProductionService(BaseDBService):
    """Uretim islemleri servisi"""

    def create_recipe(self, recipe_data: Dict, details: List[Dict]) -> int:
        recipe_code = recipe_data.get('RecipeCode', f"REC-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        recipe_name = recipe_data.get('RecipeName', '')
        product_id = recipe_data.get('ProductID')
        quantity = recipe_data.get('Quantity', 1)
        unit = recipe_data.get('Unit', 'Adet')
        created_by = recipe_data.get('CreatedBy', 1)

        total_cost = sum(d.get('TotalCost', d.get('Quantity', 0) * d.get('UnitCost', 0)) for d in details)

        query = """INSERT INTO ProductionRecipes
            (RecipeCode, RecipeName, ProductID, Quantity, Unit, TotalCost, Notes, CreatedBy, CreatedDate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))"""
        self._execute(query, (
            recipe_code, recipe_name, product_id, quantity, unit,
            total_cost, recipe_data.get('Notes', ''), created_by
        ), fetch=False)

        result = self._execute("SELECT last_insert_rowid() as id")
        recipe_id = result[0]['id']

        for i, det in enumerate(details):
            qty = det.get('Quantity', 0)
            unit_cost = det.get('UnitCost', 0)
            waste = det.get('WasteRate', 0)
            det_query = """INSERT INTO ProductionRecipeDetails
                (RecipeID, LineNumber, RawMaterialID, Quantity, Unit, UnitCost, TotalCost, WasteRate)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
            self._execute(det_query, (
                recipe_id, i + 1, det.get('RawMaterialID'),
                qty, det.get('Unit', 'Adet'), unit_cost, qty * unit_cost, waste
            ), fetch=False)

        self.logger.info(f"Recete olusturuldu: {recipe_code} (ID={recipe_id})")
        return recipe_id

    def get_recipes(self) -> List[Dict]:
        return self._execute("""
            SELECT pr.*, si.StockCode, si.StockName
            FROM ProductionRecipes pr
            LEFT JOIN StockItems si ON pr.ProductID = si.StockID
            WHERE pr.IsActive = 1
            ORDER BY pr.RecipeCode
        """)

    def create_production_order(self, order_data: Dict) -> int:
        order_code = order_data.get('OrderCode', f"URE-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        order_date = order_data.get('OrderDate', date.today().isoformat())
        recipe_id = order_data.get('RecipeID')
        product_id = order_data.get('ProductID')
        planned_qty = order_data.get('PlannedQuantity', 0)
        responsible = order_data.get('ResponsiblePerson', '')
        notes = order_data.get('Notes', '')
        created_by = order_data.get('CreatedBy', 1)

        recipe = self.get_by_id('ProductionRecipes', 'RecipeID', recipe_id) if recipe_id else None
        unit_cost = recipe['TotalCost'] if recipe else 0

        query = """INSERT INTO ProductionOrders
            (OrderCode, OrderDate, RecipeID, ProductID, PlannedQuantity,
             UnitCost, TotalCost, Status, ResponsiblePerson, Notes, CreatedBy, CreatedDate)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Planlandi', ?, ?, ?, datetime('now','localtime'))"""
        self._execute(query, (
            order_code, order_date, recipe_id, product_id, planned_qty,
            unit_cost, unit_cost * planned_qty, responsible, notes, created_by
        ), fetch=False)

        result = self._execute("SELECT last_insert_rowid() as id")
        order_id = result[0]['id'] if result else None
        self.logger.info(f"Uretim emri olusturuldu: {order_code} (ID={order_id})")
        return order_id

    def complete_production_order(self, order_id: int) -> bool:
        order = self.get_by_id('ProductionOrders', 'OrderID', order_id)
        if not order:
            return False

        product_id = order['ProductID']
        produced_qty = order.get('ProducedQuantity', order['PlannedQuantity'])
        defect_qty = order.get('DefectQuantity', 0)

        if product_id and produced_qty > 0:
            self._execute(
                "UPDATE StockItems SET CurrentStock = CurrentStock + ? WHERE StockID = ?",
                (produced_qty, product_id), fetch=False
            )

            recipe = self.get_by_id('ProductionRecipes', 'RecipeID', order['RecipeID']) if order.get('RecipeID') else None
            if recipe:
                details = self._execute(
                    "SELECT * FROM ProductionRecipeDetails WHERE RecipeID = ?", (recipe['RecipeID'],)
                )
                for det in details:
                    raw_qty = det['Quantity'] * produced_qty / recipe['Quantity']
                    self._execute(
                        "UPDATE StockItems SET CurrentStock = CurrentStock - ? WHERE StockID = ?",
                        (raw_qty, det['RawMaterialID']), fetch=False
                    )
                    self._execute("""INSERT INTO StockMovements
                        (MovementNumber, MovementDate, MovementType, StockID, Quantity, UnitPrice, TotalValue, Description, CreatedDate)
                        VALUES (?, date('now'), 'Cikis', ?, ?, ?, ?, ?, datetime('now','localtime'))""", (
                        f"URE-{order_id}-{det['RecipeDetailID']}", det['RawMaterialID'],
                        -raw_qty, det['UnitCost'], raw_qty * det['UnitCost'],
                        f"Uretim #{order['OrderCode']} - {det.get('RawMaterialID', '')}"
                    ), fetch=False)

            self._execute("""INSERT INTO StockMovements
                (MovementNumber, MovementDate, MovementType, StockID, Quantity, UnitPrice, TotalValue, Description, CreatedDate)
                VALUES (?, date('now'), 'Giris', ?, ?, ?, 0, ?, datetime('now','localtime'))""", (
                f"URE-GIRIS-{order_id}", product_id, produced_qty, 0,
                f"Uretim Tamamlandi #{order['OrderCode']}"
            ), fetch=False)

        self._execute("""
            UPDATE ProductionOrders SET
                Status = 'Tamamlandi',
                ProducedQuantity = ?,
                DefectQuantity = ?,
                EndDate = datetime('now','localtime')
            WHERE OrderID = ?
        """, (produced_qty, defect_qty, order_id), fetch=False)

        self.logger.info(f"Uretim emri tamamlandi: OrderID={order_id} | Uretilen: {produced_qty}")
        return True

    def get_production_costs(self, order_id: int) -> Dict:
        order = self.get_by_id('ProductionOrders', 'OrderID', order_id)
        if not order:
            return {}

        cost = {
            'order': order,
            'raw_material_cost': 0,
            'labor_cost': order.get('TotalCost', 0) * 0.3 if order.get('TotalCost') else 0,
            'overhead_cost': order.get('TotalCost', 0) * 0.1 if order.get('TotalCost') else 0,
            'unit_cost': order.get('UnitCost', 0),
            'total_cost': order.get('TotalCost', 0)
        }

        if order.get('RecipeID'):
            recipe = self.get_by_id('ProductionRecipes', 'RecipeID', order['RecipeID'])
            if recipe:
                details = self._execute(
                    "SELECT * FROM ProductionRecipeDetails WHERE RecipeID = ?", (recipe['RecipeID'],)
                )
                for det in details:
                    ratio = order['PlannedQuantity'] / recipe['Quantity'] if recipe['Quantity'] > 0 else 1
                    cost['raw_material_cost'] += det['TotalCost'] * ratio

        cost['total_cost'] = cost['raw_material_cost'] + cost['labor_cost'] + cost['overhead_cost']
        return cost

    def get_material_requirements(self, recipe_id: int, quantity: float) -> List[Dict]:
        recipe = self.get_by_id('ProductionRecipes', 'RecipeID', recipe_id)
        if not recipe:
            return []

        ratio = quantity / recipe['Quantity'] if recipe['Quantity'] > 0 else 1
        details = self._execute("""
            SELECT prd.*, si.StockCode, si.StockName, si.CurrentStock,
                      (prd.Quantity * ?) as RequiredQuantity,
                      CASE
                          WHEN si.CurrentStock >= (prd.Quantity * ?) THEN 'Yeterli'
                          ELSE 'Eksik'
                      END as StockStatus,
                      CASE
                          WHEN si.CurrentStock < (prd.Quantity * ?) THEN (prd.Quantity * ?) - si.CurrentStock
                          ELSE 0
                      END as MissingQuantity
               FROM ProductionRecipeDetails prd
               JOIN StockItems si ON prd.RawMaterialID = si.StockID
               WHERE prd.RecipeID = ?
        """, (ratio, ratio, ratio, ratio, recipe_id))
        return details


class BranchService(BaseDBService):
    """Sube islemleri servisi"""

    def get_branches(self) -> List[Dict]:
        return self._execute("SELECT * FROM Branches WHERE IsActive = 1 ORDER BY BranchCode")

    def create_transfer(self, transfer_data: Dict, items: List[Dict]) -> int:
        transfer_code = transfer_data.get('TransferCode', f"TRF-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        transfer_date = transfer_data.get('TransferDate', date.today().isoformat())
        source_branch = transfer_data.get('SourceBranchID')
        target_branch = transfer_data.get('TargetBranchID')
        notes = transfer_data.get('Notes', '')
        created_by = transfer_data.get('CreatedBy', 1)

        query = """INSERT INTO BranchTransfers
            (TransferCode, TransferDate, SourceBranchID, TargetBranchID, Status, Notes, CreatedBy, CreatedDate)
            VALUES (?, ?, ?, ?, 'Hazirlaniyor', ?, ?, datetime('now','localtime'))"""
        self._execute(query, (
            transfer_code, transfer_date, source_branch, target_branch, notes, created_by
        ), fetch=False)

        result = self._execute("SELECT last_insert_rowid() as id")
        transfer_id = result[0]['id'] if result else None
        self.logger.info(f"Transfer olusturuldu: {transfer_code} (ID={transfer_id})")
        return transfer_id

    def complete_transfer(self, transfer_id: int) -> bool:
        transfer = self.get_by_id('BranchTransfers', 'TransferID', transfer_id)
        if not transfer:
            return False

        self._execute(
            "UPDATE BranchTransfers SET Status = 'Tamamlandi' WHERE TransferID = ?",
            (transfer_id,), fetch=False
        )
        self.logger.info(f"Transfer tamamlandi: TransferID={transfer_id}")
        return True

    def get_branch_stock(self, branch_id: int) -> List[Dict]:
        return self._execute("""
            SELECT si.StockID, si.StockCode, si.StockName, si.Unit,
                   si.CurrentStock, si.MinStockLevel,
                   sc.CategoryName
            FROM StockItems si
            LEFT JOIN StockCategories sc ON si.CategoryID = sc.CategoryID
            WHERE si.IsActive = 1
            ORDER BY si.StockCode
        """)

    def get_transactions(self, branch_id: int, date_range: tuple = None) -> List[Dict]:
        query = """SELECT bt.*, sb.BranchName as SourceBranch, tb.BranchName as TargetBranch
                   FROM BranchTransfers bt
                   LEFT JOIN Branches sb ON bt.SourceBranchID = sb.BranchID
                   LEFT JOIN Branches tb ON bt.TargetBranchID = tb.BranchID
                   WHERE (bt.SourceBranchID = ? OR bt.TargetBranchID = ?)"""
        params = [branch_id, branch_id]
        if date_range:
            query += " AND bt.TransferDate BETWEEN ? AND ?"
            params.extend(date_range)
        query += " ORDER BY bt.TransferDate DESC"
        return self._execute(query, tuple(params))


class CRMService(BaseDBService):
    """CRM islemleri servisi"""

    def log_activity(self, activity_data: Dict) -> int:
        activity_date = activity_data.get('ActivityDate', date.today().isoformat())
        activity_type = activity_data.get('ActivityType', 'Gorusme')
        customer_id = activity_data.get('CurrentAccountID')
        contact = activity_data.get('ContactPerson', '')
        subject = activity_data.get('Subject', '')
        description = activity_data.get('Description', '')
        follow_up = activity_data.get('FollowUpDate')
        assigned_to = activity_data.get('AssignedTo')
        created_by = activity_data.get('CreatedBy', 1)

        query = """INSERT INTO CRM_Activities
            (ActivityDate, ActivityType, CurrentAccountID, ContactPerson, Subject,
             Description, Status, FollowUpDate, AssignedTo, CreatedBy, CreatedDate)
            VALUES (?, ?, ?, ?, ?, ?, 'Tamamlandi', ?, ?, ?, datetime('now','localtime'))"""
        self._execute(query, (
            activity_date, activity_type, customer_id, contact, subject,
            description, follow_up, assigned_to, created_by
        ), fetch=False)

        result = self._execute("SELECT last_insert_rowid() as id")
        activity_id = result[0]['id'] if result else None
        self.logger.info(f"CRM aktivite kaydedildi: ID={activity_id} | Tur: {activity_type}")
        return activity_id

    def get_activities(self, customer_id: int = None, activity_type: str = None,
                       date_range: tuple = None) -> List[Dict]:
        query = """SELECT a.*, ca.CurrentAccountName, u.FullName as AssignedUserName
                   FROM CRM_Activities a
                   LEFT JOIN CurrentAccounts ca ON a.CurrentAccountID = ca.CurrentAccountID
                   LEFT JOIN Users u ON a.AssignedTo = u.UserID
                   WHERE 1=1"""
        params = []
        if customer_id:
            query += " AND a.CurrentAccountID = ?"
            params.append(customer_id)
        if activity_type:
            query += " AND a.ActivityType = ?"
            params.append(activity_type)
        if date_range:
            query += " AND a.ActivityDate BETWEEN ? AND ?"
            params.extend(date_range)
        query += " ORDER BY a.ActivityDate DESC"
        return self._execute(query, tuple(params) if params else None)

    def get_customer_analytics(self, customer_id: int) -> Dict:
        analytics = {
            'customer': self.get_by_id('CurrentAccounts', 'CurrentAccountID', customer_id),
            'total_invoices': 0,
            'total_amount': 0,
            'total_paid': 0,
            'total_activities': 0,
            'last_activity': None,
            'avg_payment_time': 0
        }

        inv_stats = self._execute("""
            SELECT COUNT(*) as cnt, COALESCE(SUM(TotalAmount), 0) as tot,
                   COALESCE(SUM(PaidAmount), 0) as paid
            FROM Invoices WHERE CurrentAccountID = ?
        """, (customer_id,))
        if inv_stats:
            analytics['total_invoices'] = inv_stats[0]['cnt']
            analytics['total_amount'] = float(inv_stats[0]['tot'])
            analytics['total_paid'] = float(inv_stats[0]['paid'])

        act = self._execute("""
            SELECT COUNT(*) as cnt, MAX(ActivityDate) as last_act
            FROM CRM_Activities WHERE CurrentAccountID = ?
        """, (customer_id,))
        if act:
            analytics['total_activities'] = act[0]['cnt']
            analytics['last_activity'] = act[0]['last_act']

        return analytics

    def get_upcoming_activities(self, days: int = 7) -> List[Dict]:
        return self._execute("""
            SELECT a.*, ca.CurrentAccountName
            FROM CRM_Activities a
            LEFT JOIN CurrentAccounts ca ON a.CurrentAccountID = ca.CurrentAccountID
            WHERE a.IsCompleted = 0
                AND a.FollowUpDate BETWEEN date('now') AND date('now', ?)
            ORDER BY a.FollowUpDate
        """, (f"+{days} days",))

    def get_customer_segments(self) -> List[Dict]:
        return self._execute("""
            SELECT
                CASE
                    WHEN COUNT(inv.InvoiceID) = 0 THEN 'Yeni'
                    WHEN SUM(inv.TotalAmount) > 100000 THEN 'Premium'
                    WHEN SUM(inv.TotalAmount) > 50000 THEN 'Altin'
                    WHEN SUM(inv.TotalAmount) > 10000 THEN 'Standart'
                    ELSE 'Potansiyel'
                END as Segment,
                ca.CurrentAccountID, ca.CurrentAccountCode, ca.CurrentAccountName,
                COUNT(inv.InvoiceID) as InvoiceCount,
                COALESCE(SUM(inv.TotalAmount), 0) as TotalAmount,
                ca.Balance
            FROM CurrentAccounts ca
            LEFT JOIN Invoices inv ON ca.CurrentAccountID = inv.CurrentAccountID
            WHERE ca.IsActive = 1
            GROUP BY ca.CurrentAccountID
            ORDER BY TotalAmount DESC
        """)


class SettingService(BaseDBService):
    """Sistem ayarlari servisi"""

    def get_setting(self, key: str, default: Any = None) -> Any:
        result = self._execute(
            "SELECT SettingValue FROM SystemSettings WHERE SettingKey = ?", (key,)
        )
        if result:
            return result[0]['SettingValue']
        return default

    def set_setting(self, key: str, value: Any) -> bool:
        existing = self._execute(
            "SELECT COUNT(*) as cnt FROM SystemSettings WHERE SettingKey = ?", (key,)
        )
        if existing and existing[0]['cnt'] > 0:
            self._execute(
                "UPDATE SystemSettings SET SettingValue = ?, UpdatedDate = datetime('now','localtime') WHERE SettingKey = ?",
                (str(value), key), fetch=False
            )
        else:
            self._execute(
                "INSERT INTO SystemSettings (SettingKey, SettingValue, Description, UpdatedDate) VALUES (?, ?, ?, datetime('now','localtime'))",
                (key, str(value), f"Auto-generated: {key}"), fetch=False
            )
        self.logger.info(f"Ayar guncellendi: {key} = {value}")
        return True

    def get_all_settings(self) -> List[Dict]:
        return self._execute("SELECT * FROM SystemSettings ORDER BY SettingKey")

    def get_settings_by_group(self, group: str) -> List[Dict]:
        return self._execute(
            "SELECT * FROM SystemSettings WHERE SettingKey LIKE ? ORDER BY SettingKey",
            (f"{group}.%",)
        )


class BarcodeService(BaseDBService):
    """Barkod islemleri servisi"""

    def generate_barcode(self, product_code: str, barcode_format: str = 'code128') -> str:
        timestamp = datetime.now().strftime('%H%M%S')
        return f"{product_code}{timestamp}"

    def lookup_barcode(self, barcode: str) -> Optional[Dict]:
        return self._execute(
            "SELECT * FROM StockItems WHERE Barcode = ?", (barcode,)
        )

    def create_template(self, template_data: Dict) -> int:
        query = """INSERT INTO BarcodeTemplates
            (TemplateName, LabelWidth, LabelHeight, FieldsConfiguration, PrinterName, IsDefault, CreatedDate)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now','localtime'))"""
        self._execute(query, (
            template_data.get('TemplateName'),
            template_data.get('LabelWidth', 50),
            template_data.get('LabelHeight', 30),
            template_data.get('FieldsConfiguration', '{}'),
            template_data.get('PrinterName', ''),
            template_data.get('IsDefault', False),
        ), fetch=False)

        if template_data.get('IsDefault'):
            self._execute(
                "UPDATE BarcodeTemplates SET IsDefault = 0 WHERE TemplateID != last_insert_rowid()",
                fetch=False
            )

        result = self._execute("SELECT last_insert_rowid() as id")
        template_id = result[0]['id'] if result else None
        self.logger.info(f"Barkod sablonu olusturuldu: ID={template_id}")
        return template_id

    def get_templates(self) -> List[Dict]:
        return self._execute("SELECT * FROM BarcodeTemplates ORDER BY IsDefault DESC, TemplateName")
