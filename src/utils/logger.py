"""
Accura Finance - Logging Sistem
Gelişmiş loglama ve hata takibi
"""

import logging
import logging.handlers
import os
import sys
import colorlog
from datetime import datetime

def setup_logger(name='AccuraFinance', level=logging.INFO):
    """
    Gelişmiş logger kurulumu
    """
    
    # Log dizinini oluştur
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Logger oluştur
    logger = logging.getLogger(name)
    
    # Eğer logger zaten yapılandırılmışsa, tekrar yapılandırma
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(module)s.%(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    
    # File Handler - Rotating File Handler
    log_file = os.path.join(log_dir, f'{name.lower()}.log')
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    # Error File Handler - Sadece hata ve kritik loglar
    error_log_file = os.path.join(log_dir, f'{name.lower()}_errors.log')
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    
    # Handlers'ları logger'a ekle
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.addHandler(error_handler)
    
    # İlk log mesajı
    logger.info(f"{name} logger başlatıldı")
    
    return logger

class DatabaseLogger:
    """
    Veritabanı işlemleri için özel logger
    """
    
    def __init__(self, db_manager=None):
        self.logger = setup_logger('Database')
        self.db_manager = db_manager
    
    def log_query(self, query, params=None, execution_time=None):
        """SQL sorgu logla"""
        log_msg = f"SQL Query: {query[:200]}..."
        if params:
            log_msg += f" | Params: {params}"
        if execution_time:
            log_msg += f" | Time: {execution_time:.3f}s"
        
        self.logger.debug(log_msg)
    
    def log_error(self, error, query=None):
        """Veritabanı hatası logla"""
        log_msg = f"Database Error: {error}"
        if query:
            log_msg += f" | Query: {query[:200]}..."
        
        self.logger.error(log_msg)
    
    def log_connection(self, status, details=None):
        """Bağlantı durumu logla"""
        log_msg = f"Database Connection: {status}"
        if details:
            log_msg += f" | Details: {details}"
        
        if status == "SUCCESS":
            self.logger.info(log_msg)
        else:
            self.logger.error(log_msg)

class AuditLogger:
    """
    Kullanıcı işlemleri için audit logger
    """
    
    def __init__(self, db_manager=None):
        self.logger = setup_logger('Audit')
        self.db_manager = db_manager
    
    def log_user_action(self, user_id, action, table_name, record_id, details=None):
        """Kullanıcı işlemi logla"""
        log_msg = f"User: {user_id} | Action: {action} | Table: {table_name} | Record: {record_id}"
        if details:
            log_msg += f" | Details: {details}"
        
        self.logger.info(log_msg)
        
        # Veritabanına da kaydet (eğer mümkünse)
        if self.db_manager:
            try:
                self.db_manager.execute_query(
                    """INSERT INTO AuditLog (TableName, RecordID, Action, UserID, ActionDate, NewValues)
                       VALUES (?, ?, ?, ?, datetime('now','localtime'), ?)""",
                    (table_name, record_id, action, user_id, details),
                    fetch=False
                )
            except Exception as e:
                self.logger.error(f"Audit log veritabanına kaydedilemedi: {e}")
    
    def log_login(self, username, success, ip_address=None):
        """Login işlemi logla"""
        status = "SUCCESS" if success else "FAILED"
        log_msg = f"Login {status}: {username}"
        if ip_address:
            log_msg += f" | IP: {ip_address}"
        
        if success:
            self.logger.info(log_msg)
        else:
            self.logger.warning(log_msg)
    
    def log_logout(self, username, session_duration=None):
        """Logout işlemi logla"""
        log_msg = f"Logout: {username}"
        if session_duration:
            log_msg += f" | Session Duration: {session_duration}"
        
        self.logger.info(log_msg)

class PerformanceLogger:
    """
    Performans takibi için logger
    """
    
    def __init__(self):
        self.logger = setup_logger('Performance')
    
    def log_operation_time(self, operation, duration, details=None):
        """İşlem süresi logla"""
        log_msg = f"Operation: {operation} | Duration: {duration:.3f}s"
        if details:
            log_msg += f" | Details: {details}"
        
        # Uzun süren işlemleri uyarı olarak logla
        if duration > 5.0:
            self.logger.warning(f"SLOW {log_msg}")
        elif duration > 2.0:
            self.logger.info(f"MEDIUM {log_msg}")
        else:
            self.logger.debug(log_msg)
    
    def log_memory_usage(self, process_name, memory_mb):
        """Bellek kullanımı logla"""
        log_msg = f"Memory Usage: {process_name} | {memory_mb:.2f} MB"
        
        # Yüksek bellek kullanımını uyarı olarak logla
        if memory_mb > 500:
            self.logger.warning(f"HIGH {log_msg}")
        elif memory_mb > 200:
            self.logger.info(f"MEDIUM {log_msg}")
        else:
            self.logger.debug(log_msg)

class BusinessLogger:
    """
    İş mantığı için özel logger
    """
    
    def __init__(self):
        self.logger = setup_logger('Business')
    
    def log_transaction(self, transaction_type, amount, details=None):
        """Mali işlem logla"""
        log_msg = f"Transaction: {transaction_type} | Amount: {amount}"
        if details:
            log_msg += f" | Details: {details}"
        
        self.logger.info(log_msg)
    
    def log_invoice(self, invoice_type, invoice_number, total_amount, customer=None):
        """Fatura işlemi logla"""
        log_msg = f"Invoice {invoice_type}: {invoice_number} | Total: {total_amount}"
        if customer:
            log_msg += f" | Customer: {customer}"
        
        self.logger.info(log_msg)
    
    def log_payment(self, payment_type, amount, account, description=None):
        """Ödeme işlemi logla"""
        log_msg = f"Payment {payment_type}: {amount} | Account: {account}"
        if description:
            log_msg += f" | Description: {description}"
        
        self.logger.info(log_msg)
    
    def log_stock_movement(self, movement_type, stock_code, quantity, location=None):
        """Stok hareketi logla"""
        log_msg = f"Stock {movement_type}: {stock_code} | Quantity: {quantity}"
        if location:
            log_msg += f" | Location: {location}"
        
        self.logger.info(log_msg)

def get_log_summary():
    """
    Log dosyalarının özetini getir
    """
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    
    if not os.path.exists(log_dir):
        return "Log dizini bulunamadı"
    
    summary = []
    for filename in os.listdir(log_dir):
        if filename.endswith('.log'):
            file_path = os.path.join(log_dir, filename)
            try:
                stat = os.stat(file_path)
                size_mb = stat.st_size / (1024 * 1024)
                modified = datetime.fromtimestamp(stat.st_mtime)
                
                summary.append({
                    'file': filename,
                    'size_mb': round(size_mb, 2),
                    'modified': modified.strftime('%d.%m.%Y %H:%M:%S')
                })
            except:
                continue
    
    return summary

def clear_old_logs(days=30):
    """
    Eski log dosyalarını temizle
    """
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    
    if not os.path.exists(log_dir):
        return
    
    from datetime import datetime, timedelta
    cutoff_date = datetime.now() - timedelta(days=days)
    
    deleted_count = 0
    for filename in os.listdir(log_dir):
        if filename.endswith('.log'):
            file_path = os.path.join(log_dir, filename)
            try:
                stat = os.stat(file_path)
                modified = datetime.fromtimestamp(stat.st_mtime)
                
                if modified < cutoff_date:
                    os.remove(file_path)
                    deleted_count += 1
            except:
                continue
    
    logger = setup_logger()
    logger.info(f"Eski log dosyaları temizlendi: {deleted_count} dosya silindi")

# Exception handler
def handle_exception(exc_type, exc_value, exc_traceback):
    """
    Yakalanmamış exception'ları logla
    """
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logger = setup_logger()
    logger.critical(
        "Yakalanmamış exception:",
        exc_info=(exc_type, exc_value, exc_traceback)
    )

# Sistemde exception handler'ı ayarla
sys.excepthook = handle_exception
