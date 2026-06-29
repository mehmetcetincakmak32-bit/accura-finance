"""
Accura Finance - Global Arama Servisi
Tüm modüllerde arama yapma işlemleri
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from src.utils.logger import setup_logger
from src.database.connection import get_database_manager


class SearchService:
    """Global arama servisi - tum modullerde arama"""

    def __init__(self, db_manager=None):
        self.db = db_manager or get_database_manager()
        self.logger = setup_logger('SearchService')

    def global_search(self, term: str, modules: List[str] = None) -> Dict:
        if not term or len(term.strip()) < 2:
            return {'total': 0, 'results': []}

        term = term.strip()
        results = {}
        total = 0

        if modules is None or 'customers' in modules:
            customers = self.search_customers(term)
            if customers:
                results['customers'] = customers
                total += len(customers)

        if modules is None or 'products' in modules:
            products = self.search_products(term)
            if products:
                results['products'] = products
                total += len(products)

        if modules is None or 'invoices' in modules:
            invoices = self.search_invoices(term)
            if invoices:
                results['invoices'] = invoices
                total += len(invoices)

        if modules is None or 'checks' in modules:
            checks = self.search_checks(term)
            if checks:
                results['checks'] = checks
                total += len(checks)

        if modules is None or 'accounts' in modules:
            accounts = self.search_accounts(term)
            if accounts:
                results['accounts'] = accounts
                total += len(accounts)

        return {'total': total, 'results': results}

    def search_customers(self, term: str) -> List[Dict]:
        try:
            return self.db.execute_query("""
                SELECT CurrentAccountID as id, CurrentAccountCode as code,
                       CurrentAccountName as name, CurrentAccountType as type,
                       TaxNumber, Phone, Balance,
                       'cari' as module
                FROM CurrentAccounts
                WHERE CurrentAccountCode LIKE ? OR CurrentAccountName LIKE ?
                   OR TaxNumber LIKE ? OR Phone LIKE ?
                ORDER BY CurrentAccountName
                LIMIT 20
            """, (f"%{term}%", f"%{term}%", f"%{term}%", f"%{term}%"))
        except Exception as e:
            self.logger.error(f"Cari arama hatasi: {e}")
            return []

    def search_products(self, term: str) -> List[Dict]:
        try:
            return self.db.execute_query("""
                SELECT si.StockID as id, si.StockCode as code,
                       si.StockName as name, si.Barcode, si.CurrentStock,
                       si.Unit, si.SalePrice, sc.CategoryName,
                       'urun' as module
                FROM StockItems si
                LEFT JOIN StockCategories sc ON si.CategoryID = sc.CategoryID
                WHERE si.StockCode LIKE ? OR si.StockName LIKE ?
                   OR si.Barcode LIKE ?
                ORDER BY si.StockName
                LIMIT 20
            """, (f"%{term}%", f"%{term}%", f"%{term}%"))
        except Exception as e:
            self.logger.error(f"Urun arama hatasi: {e}")
            return []

    def search_invoices(self, term: str) -> List[Dict]:
        try:
            return self.db.execute_query("""
                SELECT inv.InvoiceID as id, inv.InvoiceNumber as code,
                       inv.InvoiceDate, inv.InvoiceType,
                       inv.TotalAmount, inv.RemainingAmount,
                       ca.CurrentAccountName as customer_name,
                       CASE
                           WHEN inv.RemainingAmount <= 0 THEN 'Odendi'
                           WHEN inv.DueDate < date('now') THEN 'Gecikmis'
                           ELSE 'Bekliyor'
                       END as status,
                       'fatura' as module
                FROM Invoices inv
                JOIN CurrentAccounts ca ON inv.CurrentAccountID = ca.CurrentAccountID
                WHERE inv.InvoiceNumber LIKE ? OR ca.CurrentAccountName LIKE ?
                ORDER BY inv.InvoiceDate DESC
                LIMIT 20
            """, (f"%{term}%", f"%{term}%"))
        except Exception as e:
            self.logger.error(f"Fatura arama hatasi: {e}")
            return []

    def search_checks(self, term: str) -> List[Dict]:
        try:
            return self.db.execute_query("""
                SELECT c.CheckID as id, c.CheckNo as code, c.BankName,
                       c.Amount, c.CheckDate, c.MaturityDate, c.CheckStatus,
                       ca.CurrentAccountName as customer_name,
                       'cek' as module
                FROM Checks c
                LEFT JOIN CurrentAccounts ca ON c.CurrentAccountID = ca.CurrentAccountID
                WHERE c.CheckNo LIKE ? OR c.BankName LIKE ?
                   OR ca.CurrentAccountName LIKE ?
                ORDER BY c.MaturityDate DESC
                LIMIT 20
            """, (f"%{term}%", f"%{term}%", f"%{term}%"))
        except Exception as e:
            self.logger.error(f"Cek arama hatasi: {e}")
            return []

    def search_accounts(self, term: str) -> List[Dict]:
        try:
            return self.db.execute_query("""
                SELECT AccountID as id, AccountCode as code,
                       AccountName as name, AccountType as type,
                       AccountGroup as group_name,
                       'hesap' as module
                FROM ChartOfAccounts
                WHERE AccountCode LIKE ? OR AccountName LIKE ?
                ORDER BY AccountCode
                LIMIT 20
            """, (f"%{term}%", f"%{term}%"))
        except Exception as e:
            self.logger.error(f"Hesap arama hatasi: {e}")
            return []

    def get_search_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        try:
            return self.db.execute_query("""
                SELECT SearchID, SearchTerm, Module, SearchedAt
                FROM SearchHistory
                WHERE UserID = ?
                ORDER BY SearchedAt DESC
                LIMIT ?
            """, (user_id, limit))
        except Exception as e:
            self.logger.error(f"Arama gecmisi hatasi: {e}")
            return []

    def save_search(self, user_id: int, term: str, module: str) -> bool:
        try:
            self.db.execute_query("""
                INSERT INTO SearchHistory (UserID, SearchTerm, Module, SearchedAt)
                VALUES (?, ?, ?, datetime('now','localtime'))
            """, (user_id, term, module), fetch=False)
            return True
        except Exception as e:
            self.logger.error(f"Arama kaydetme hatasi: {e}")
            return False
