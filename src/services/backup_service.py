"""
Accura Finance - Yedekleme Servisi
Veritabanı yedekleme ve geri yükleme işlemleri
"""

import os
import shutil
import json
import glob
import threading
import time
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
from pathlib import Path

from src.utils.logger import setup_logger
from src.database.connection import get_database_manager


class BackupService:
    """Veritabanı yedekleme ve geri yükleme servisi"""

    def __init__(self, db_manager=None):
        self.db = db_manager or get_database_manager()
        self.logger = setup_logger('BackupService')
        self._backup_dir = self._get_backup_dir()
        self._scheduler_thread = None
        self._scheduler_running = False
        os.makedirs(self._backup_dir, exist_ok=True)

    def _get_backup_dir(self) -> str:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        backup_dir = os.path.join(base_dir, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        return backup_dir

    def _get_db_path(self) -> Optional[str]:
        try:
            conn = self.db.get_connection()
            if hasattr(conn, 'execute'):
                cursor = conn.execute("PRAGMA database_list")
                row = cursor.fetchone()
                conn.close()
                if row:
                    return row[2]
            conn.close()
        except Exception:
            pass

        possible_paths = [
            os.path.join(os.path.dirname(self._backup_dir), 'data', 'accura_finance.db'),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'accura_finance.db'),
        ]
        for p in possible_paths:
            if os.path.exists(p):
                return p
        return None

    def create_backup(self) -> Optional[str]:
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            db_path = self._get_db_path()

            if db_path and os.path.exists(db_path):
                backup_filename = f"accura_finance_backup_{timestamp}.db"
                backup_path = os.path.join(self._backup_dir, backup_filename)
                shutil.copy2(db_path, backup_path)

                info = {
                    'backup_file': backup_filename,
                    'created_at': datetime.now().isoformat(),
                    'db_size_mb': round(os.path.getsize(db_path) / (1024 * 1024), 2),
                    'backup_size_mb': round(os.path.getsize(backup_path) / (1024 * 1024), 2),
                    'type': 'sqlite_full'
                }
                info_path = backup_path + '.info'
                with open(info_path, 'w', encoding='utf-8') as f:
                    json.dump(info, f, indent=2, ensure_ascii=False)

                self.logger.info(f"Yedekleme basarili: {backup_filename} ({info['backup_size_mb']} MB)")
                return backup_path
            else:
                # SQL Server yedekleme
                backup_filename = f"accura_finance_backup_{timestamp}.bak"
                backup_path = os.path.join(self._backup_dir, backup_filename)

                try:
                    self.db.execute_query(
                        f"BACKUP DATABASE AccuraFinance TO DISK = ?",
                        (backup_path,), fetch=False
                    )
                    self.logger.info(f"SQL Server yedekleme basarili: {backup_filename}")
                    return backup_path
                except Exception as e:
                    self.logger.error(f"SQL Server yedekleme hatasi: {e}")
                    return None

        except Exception as e:
            self.logger.error(f"Yedekleme hatasi: {e}")
            return None

    def restore_backup(self, backup_file: str) -> bool:
        try:
            if not os.path.exists(backup_file):
                self.logger.error(f"Yedek dosyasi bulunamadi: {backup_file}")
                return False

            ext = os.path.splitext(backup_file)[1].lower()

            if ext == '.db':
                db_path = self._get_db_path()
                if not db_path:
                    self.logger.error("Veritabani yolu bulunamadi")
                    return False

                backup_path = os.path.join(self._backup_dir, os.path.basename(backup_file))
                if not os.path.exists(backup_path):
                    backup_path = backup_file

                backup_name = os.path.basename(backup_path)
                restore_name = f"accura_finance_before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                restore_path = os.path.join(self._backup_dir, restore_name)

                if os.path.exists(db_path):
                    shutil.copy2(db_path, restore_path)
                    self.logger.info(f"Mevcut veritabani yedeklendi: {restore_name}")

                shutil.copy2(backup_path, db_path)
                self.logger.info(f"Geri yukleme basarili: {backup_name} -> {db_path}")
                return True

            elif ext == '.bak':
                try:
                    self.db.execute_query(
                        f"RESTORE DATABASE AccuraFinance FROM DISK = ? WITH REPLACE",
                        (backup_file,), fetch=False
                    )
                    self.logger.info(f"SQL Server geri yukleme basarili")
                    return True
                except Exception as e:
                    self.logger.error(f"SQL Server geri yukleme hatasi: {e}")
                    return False

            else:
                self.logger.error(f"Desteklenmeyen yedek format: {ext}")
                return False

        except Exception as e:
            self.logger.error(f"Geri yukleme hatasi: {e}")
            return False

    def list_backups(self) -> List[Dict]:
        try:
            backups = []
            db_files = glob.glob(os.path.join(self._backup_dir, 'accura_finance_backup_*.db'))
            bak_files = glob.glob(os.path.join(self._backup_dir, 'accura_finance_backup_*.bak'))

            for fp in db_files + bak_files:
                stat = os.stat(fp)
                info_path = fp + '.info'
                info = {}
                if os.path.exists(info_path):
                    try:
                        with open(info_path, 'r', encoding='utf-8') as f:
                            info = json.load(f)
                    except Exception:
                        pass

                backups.append({
                    'filename': os.path.basename(fp),
                    'filepath': fp,
                    'size_mb': round(stat.st_size / (1024 * 1024), 2),
                    'created_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'info': info
                })

            backups.sort(key=lambda x: x['created_at'], reverse=True)
            return backups

        except Exception as e:
            self.logger.error(f"Yedek listesi hatasi: {e}")
            return []

    def schedule_backup(self, interval_hours: int, retention_days: int) -> bool:
        if self._scheduler_running:
            self.logger.warning("Zamanlayici zaten calisiyor")
            return False

        self._scheduler_running = True

        def _run_scheduler():
            self.logger.info(f"Yedekleme zamanlayicisi baslatildi: {interval_hours} saat aralik, {retention_days} gun saklama")
            while self._scheduler_running:
                try:
                    backup_path = self.create_backup()
                    if backup_path:
                        self.cleanup_old_backups(retention_days)
                    time.sleep(interval_hours * 3600)
                except Exception as e:
                    self.logger.error(f"Zamanlanmis yedekleme hatasi: {e}")
                    time.sleep(300)

        self._scheduler_thread = threading.Thread(target=_run_scheduler, daemon=True)
        self._scheduler_thread.start()
        return True

    def stop_scheduler(self):
        self._scheduler_running = False
        self.logger.info("Yedekleme zamanlayicisi durduruldu")

    def cleanup_old_backups(self, retention_days: int) -> int:
        try:
            cutoff = datetime.now() - timedelta(days=retention_days)
            deleted_count = 0

            backups = self.list_backups()
            for backup in backups:
                created = datetime.fromisoformat(backup['created_at'])
                if created < cutoff:
                    try:
                        os.remove(backup['filepath'])
                        info_path = backup['filepath'] + '.info'
                        if os.path.exists(info_path):
                            os.remove(info_path)
                        deleted_count += 1
                    except Exception as e:
                        self.logger.error(f"Yedek silme hatasi: {backup['filename']} - {e}")

            if deleted_count > 0:
                self.logger.info(f"Eski yedekler temizlendi: {deleted_count} dosya silindi")
            return deleted_count

        except Exception as e:
            self.logger.error(f"Yedek temizleme hatasi: {e}")
            return 0
