"""
Accura Finance - Islem Kayit ve Raporlama Modulu
Tum POS islemlerini kaydeder, raporlar ve analiz eder
"""

import os
import json
import uuid
from datetime import datetime, timedelta


class TransactionLogger:
    """Islem kayit ve raporlama - tum islemleri JSON formatinda saklar"""

    def __init__(self, db_path=None):
        if db_path is None:
            log_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'posentegre_logs'
            )
            os.makedirs(log_dir, exist_ok=True)
            db_path = os.path.join(log_dir, 'transactions.json')
        self.db_path = db_path
        self._ensure_db()

    def _ensure_db(self):
        """Veritabani dosyasinin var oldugundan emin ol"""
        if not os.path.exists(self.db_path):
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False)

    def _load_transactions(self):
        """Tum islemleri yukle"""
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _save_transactions(self, transactions):
        """Islemleri kaydet"""
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(transactions, f, ensure_ascii=False, indent=2)

    def generate_id(self):
        """Benzersiz islem ID'si olustur"""
        return f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"

    def log_transaction(self, transaction_data):
        """Islem kaydet

        Args:
            transaction_data (dict): Islem bilgileri
                - amount, card_bin, card_last4, bank, installment
                - commission, net_amount, auth_code, reference_no
                - status, type (payment/refund/cancel/settlement)
        """
        transactions = self._load_transactions()

        record = {
            'id': self.generate_id(),
            'date': datetime.now().isoformat(),
            'amount': transaction_data.get('amount', 0),
            'card_bin': transaction_data.get('card_bin', ''),
            'card_last4': transaction_data.get('card_last4', ''),
            'bank': transaction_data.get('bank', ''),
            'installment': transaction_data.get('installment', 1),
            'commission': transaction_data.get('commission', 0),
            'commission_rate': transaction_data.get('commission_rate', 0),
            'net_amount': transaction_data.get('net_amount', 0),
            'auth_code': transaction_data.get('auth_code', ''),
            'reference_no': transaction_data.get('reference_no', ''),
            'status': transaction_data.get('status', 'pending'),
            'type': transaction_data.get('type', 'payment'),
            'description': transaction_data.get('description', ''),
            'device_id': transaction_data.get('device_id', ''),
            'currency': transaction_data.get('currency', 'TRY')
        }

        transactions.append(record)
        self._save_transactions(transactions)

        log_file = os.path.join(
            os.path.dirname(self.db_path),
            f"islem_{datetime.now().strftime('%Y%m%d')}.log"
        )
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(
                f"[{record['date']}] {record['type'].upper()} | "
                f"Tutar: {record['amount']} | Banka: {record['bank']} | "
                f"Durum: {record['status']} | Referans: {record['reference_no']}\n"
            )

        return record['id']

    def get_transactions(self, date_range=None, bank=None, status=None):
        """Islemleri sorgula

        Args:
            date_range (tuple): (baslangic_tarihi, bitis_tarihi) ISO formatinda
            bank (str): Banka adi filtre
            status (str): Durum filtre (success/failed/pending/refunded/cancelled)

        Returns:
            list: Filtrelenmis islem listesi
        """
        transactions = self._load_transactions()

        if date_range:
            start_date, end_date = date_range
            transactions = [
                t for t in transactions
                if start_date <= t['date'][:10] <= end_date
            ]

        if bank:
            transactions = [
                t for t in transactions
                if t['bank'].lower() == bank.lower()
            ]

        if status:
            transactions = [
                t for t in transactions
                if t['status'].lower() == status.lower()
            ]

        return sorted(transactions, key=lambda x: x['date'], reverse=True)

    def get_daily_summary(self, date=None):
        """Gunluk islem ozeti

        Args:
            date (str): Tarih (YYYY-MM-DD), varsayilan bugun

        Returns:
            dict: Ozet bilgileri
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        transactions = self.get_transactions(date_range=(date, date))

        summary = {
            'date': date,
            'total_transactions': len(transactions),
            'total_amount': sum(t['amount'] for t in transactions),
            'total_commission': sum(t['commission'] for t in transactions),
            'total_net': sum(t['net_amount'] for t in transactions),
            'success_count': sum(1 for t in transactions if t['status'] == 'success'),
            'failed_count': sum(1 for t in transactions if t['status'] == 'failed'),
            'refunded_count': sum(1 for t in transactions if t['status'] == 'refunded'),
            'cancelled_count': sum(1 for t in transactions if t['status'] == 'cancelled'),
            'payments': [t for t in transactions if t['type'] == 'payment'],
            'refunds': [t for t in transactions if t['type'] == 'refund'],
            'cancels': [t for t in transactions if t['type'] == 'cancel'],
            'by_bank': {}
        }

        for t in transactions:
            bank = t['bank']
            if bank not in summary['by_bank']:
                summary['by_bank'][bank] = {
                    'count': 0, 'amount': 0, 'commission': 0
                }
            summary['by_bank'][bank]['count'] += 1
            summary['by_bank'][bank]['amount'] += t['amount']
            summary['by_bank'][bank]['commission'] += t['commission']

        return summary

    def get_monthly_summary(self, year=None, month=None):
        """Aylik islem ozeti

        Args:
            year (int): Yil, varsayilan su anki yil
            month (int): Ay (1-12), varsayilan su anki ay

        Returns:
            dict: Aylik ozet
        """
        if year is None:
            year = datetime.now().year
        if month is None:
            month = datetime.now().month

        start_date = f"{year:04d}-{month:02d}-01"
        if month == 12:
            end_date = f"{year + 1:04d}-01-01"
        else:
            end_date = f"{year:04d}-{month + 1:02d}-01"

        transactions = self.get_transactions(date_range=(start_date, end_date))

        summary = {
            'year': year,
            'month': month,
            'total_transactions': len(transactions),
            'total_amount': sum(t['amount'] for t in transactions),
            'total_commission': sum(t['commission'] for t in transactions),
            'total_net': sum(t['net_amount'] for t in transactions),
            'success_count': sum(1 for t in transactions if t['status'] == 'success'),
            'failed_count': sum(1 for t in transactions if t['status'] == 'failed'),
            'daily': {}
        }

        for t in transactions:
            day = t['date'][:10]
            if day not in summary['daily']:
                summary['daily'][day] = {
                    'count': 0, 'amount': 0, 'commission': 0
                }
            summary['daily'][day]['count'] += 1
            summary['daily'][day]['amount'] += t['amount']
            summary['daily'][day]['commission'] += t['commission']

        return summary

    def get_settlement_report(self, date=None):
        """Gun sonu raporu - pos net ve komisyon detaylari

        Args:
            date (str): Tarih (YYYY-MM-DD)

        Returns:
            dict: Gunsonu raporu
        """
        daily = self.get_daily_summary(date)

        report = {
            'date': daily['date'],
            'created_at': datetime.now().isoformat(),
            'settlement_id': f"STL{daily['date'].replace('-', '')}{uuid.uuid4().hex[:4].upper()}",
            'total_sales': daily['total_amount'],
            'total_commission': daily['total_commission'],
            'total_net': daily['total_net'],
            'transaction_count': daily['total_transactions'],
            'bank_details': daily['by_bank'],
            'status': 'completed'
        }

        return report

    def get_bank_breakdown(self, date=None):
        """Bankalara gore islem dagilimi"""
        daily = self.get_daily_summary(date)
        return daily['by_bank']
