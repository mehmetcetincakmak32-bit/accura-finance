"""
Accura Finance - Veritabanı Bağlantı Yöneticisi
Önce SQL Server dener, yoksa SQLite kullanır
"""

import logging
import os
import sys

class DatabaseManagerProxy:
    def __init__(self):
        self._db = None
        self._use_sqlite = False
        self.logger = self._setup_logger()

    def _setup_logger(self):
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, 'database.log')),
                logging.StreamHandler(sys.stdout)
            ]
        )
        return logging.getLogger("Database")

    def _init_db(self):
        if self._db is not None:
            return True

        # Önce SQL Server dene (doğrudan pyodbc ile)
        try:
            import pyodbc
            conn_str = 'DRIVER={SQL Server};SERVER=localhost;DATABASE=AccuraFinance;Trusted_Connection=yes;'
            conn = pyodbc.connect(conn_str, timeout=3)
            conn.close()
            from src.database.sqlite_adapter import get_database_manager as get_sqlite
            self._db = get_sqlite()
            self._db.create_database()
            self.logger.info("SQL Server bağlantısı başarılı")
            return True
        except Exception as e:
            self.logger.warning(f"SQL Server bağlantı hatası: {e}")

        # SQL Server yoksa SQLite kullan
        try:
            from src.database.sqlite_adapter import get_database_manager as get_sqlite
            self._db = get_sqlite()
            self._db.create_database()
            self._use_sqlite = True
            self.logger.info("SQLite bağlantısı başarılı")
            return True
        except Exception as e:
            self.logger.error(f"SQLite bağlantı hatası: {e}")
            return False

    def create_database_if_not_exists(self):
        if not self._init_db():
            return False
        if hasattr(self._db, 'create_database'):
            return self._db.create_database()
        if hasattr(self._db, 'create_database_if_not_exists'):
            return self._db.create_database_if_not_exists()
        return bool(self._db)

    def test_connection(self):
        if not self._init_db():
            return False
        return self._db.test_connection() if self._db else False

    def execute_query(self, query, params=None, fetch=True):
        if not self._init_db():
            raise RuntimeError("Veritabani baslatilamadi")
        return self._db.execute_query(query, params, fetch)

    def execute_script(self, script_path):
        self._init_db()
        if hasattr(self._db, 'execute_script'):
            return self._db.execute_script(script_path)
        return False

    def get_connection(self):
        self._init_db()
        if hasattr(self._db, 'get_connection'):
            return self._db.get_connection()
        return None

_db_manager = None

def get_database_manager():
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManagerProxy()
    return _db_manager
