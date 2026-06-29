"""
Accura Finance - Banka POS Protokolleri
Her banka icin ozel dogrulama, komisyon hesaplama ve islem yonetimi
"""

import uuid
import random
import hashlib
from datetime import datetime


class BankProtocol:
    """Baz banka protokol sinifi - tum banka protokolleri bu sinifi miras alir"""

    def __init__(self, merchant_id='', terminal_id='', commission_rate=1.5):
        self.merchant_id = merchant_id
        self.terminal_id = terminal_id
        self.commission_rate = commission_rate
        self.bank_name = 'Genel'

    def process_payment(self, card_no, amount, installment=1):
        """Odeme islemi - kart no, tutar ve taksit bilgisi ile odeme yapar

        Args:
            card_no (str): Kart numarasi
            amount (float): Islem tutari
            installment (int): Taksit sayisi (1 = tek cekim)

        Returns:
            dict: auth_code, reference_no, commission, net_amount, status
        """
        if not card_no or len(card_no) < 6:
            return {'status': 'error', 'message': 'Gecersiz kart numarasi'}
        try:
            amount = float(amount)
        except (TypeError, ValueError):
            return {'status': 'error', 'message': 'Gecersiz tutar'}
        if amount <= 0:
            return {'status': 'error', 'message': 'Tutar pozitif olmalidir'}

        commission = round(amount * self.commission_rate / 100, 2)
        net_amount = round(amount - commission, 2)
        auth_code = self.generate_auth_code()
        reference_no = self.generate_reference_no()

        return {
            'auth_code': auth_code,
            'reference_no': reference_no,
            'commission': commission,
            'commission_rate': self.commission_rate,
            'net_amount': net_amount,
            'amount': amount,
            'installment': installment,
            'card_bin': card_no[:6],
            'card_last4': card_no[-4:] if len(card_no) >= 4 else card_no,
            'bank': self.bank_name,
            'status': 'success',
            'message': 'Islem basarili'
        }

    def process_refund(self, reference_no, amount):
        """Iade islemi - referans numarasina gore iade yapar"""
        refund_ref = self.generate_reference_no()
        return {
            'original_reference': reference_no,
            'refund_reference': refund_ref,
            'amount': amount,
            'bank': self.bank_name,
            'status': 'success',
            'message': 'Iade basarili'
        }

    def process_cancel(self, reference_no):
        """Iptal islemi - referans numarasina gore islem iptali"""
        cancel_ref = self.generate_reference_no()
        return {
            'original_reference': reference_no,
            'cancel_reference': cancel_ref,
            'bank': self.bank_name,
            'status': 'success',
            'message': 'Islem iptal edildi'
        }

    def process_settlement(self):
        """Gun sonu - gunluk kapanis islemi"""
        settlement_id = f"STL{datetime.now().strftime('%Y%m%d%H%M%S')}"
        return {
            'settlement_id': settlement_id,
            'bank': self.bank_name,
            'merchant_id': self.merchant_id,
            'terminal_id': self.terminal_id,
            'date': datetime.now().isoformat(),
            'status': 'completed'
        }

    def format_request(self, data):
        """Bankaya gonderilecek veriyi formatlar"""
        request = {
            'merchant_id': self.merchant_id,
            'terminal_id': self.terminal_id,
            'transaction_id': uuid.uuid4().hex[:16].upper(),
            'timestamp': datetime.now().isoformat(),
            'data': data,
            'checksum': self._calculate_checksum(data)
        }
        return request

    def parse_response(self, raw):
        """Bankadan gelen ham yaniti parse eder"""
        if isinstance(raw, str):
            import json
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return {'raw': raw, 'status': 'unknown'}
        return raw

    def generate_auth_code(self):
        """Banka onay kodu olustur"""
        return f"{random.randint(100000, 999999)}"

    def generate_reference_no(self):
        """Banka referans numarasi olustur"""
        date_part = datetime.now().strftime('%y%m%d')
        rand_part = uuid.uuid4().hex[:8].upper()
        return f"REF{date_part}{rand_part}"

    def _calculate_checksum(self, data):
        """Guvenlik kontrol toplami hesapla"""
        raw = str(data) + self.merchant_id + datetime.now().strftime('%Y%m%d')
        return hashlib.sha256(raw.encode()).hexdigest()[:16]


class AkbankProtocol(BankProtocol):
    """Akbank POS protokolu - Isyeri no, terminal no, komisyon (%1.8)"""

    def __init__(self, merchant_id='AKB12345', terminal_id='TML001'):
        super().__init__(merchant_id, terminal_id, commission_rate=1.8)
        self.bank_name = 'Akbank'


class GarantiProtocol(BankProtocol):
    """Garanti POS protokolu - Isyeri no, terminal no, komisyon (%1.6)"""

    def __init__(self, merchant_id='GAR12345', terminal_id='TML002'):
        super().__init__(merchant_id, terminal_id, commission_rate=1.6)
        self.bank_name = 'Garanti'


class YKBProtocol(BankProtocol):
    """YKB POS protokolu - Isyeri no, terminal no, komisyon (%1.9)"""

    def __init__(self, merchant_id='YKB12345', terminal_id='TML003'):
        super().__init__(merchant_id, terminal_id, commission_rate=1.9)
        self.bank_name = 'Yapi Kredi'


class IsbankProtocol(BankProtocol):
    """Isbank POS protokolu - Isyeri no, terminal no, komisyon (%1.7)"""

    def __init__(self, merchant_id='ISB12345', terminal_id='TML004'):
        super().__init__(merchant_id, terminal_id, commission_rate=1.7)
        self.bank_name = 'Isbankasi'


class ZiraatProtocol(BankProtocol):
    """Ziraat POS protokolu - Isyeri no, terminal no, komisyon (%1.4)"""

    def __init__(self, merchant_id='ZRT12345', terminal_id='TML005'):
        super().__init__(merchant_id, terminal_id, commission_rate=1.4)
        self.bank_name = 'Ziraat'


class HalkbankProtocol(BankProtocol):
    """Halkbank POS protokolu - Isyeri no, terminal no, komisyon (%1.5)"""

    def __init__(self, merchant_id='HLK12345', terminal_id='TML006'):
        super().__init__(merchant_id, terminal_id, commission_rate=1.5)
        self.bank_name = 'Halkbank'


def get_protocol(bank_name, merchant_id='', terminal_id=''):
    """Banka adina gore uygun protokol nesnesini dondur"""
    bank_map = {
        'akbank': AkbankProtocol,
        'garanti': GarantiProtocol,
        'ykb': YKBProtocol,
        'yapi kredi': YKBProtocol,
        'isbank': IsbankProtocol,
        'isbankasi': IsbankProtocol,
        'ziraat': ZiraatProtocol,
        'halkbank': HalkbankProtocol,
    }
    key = bank_name.lower().replace(' ', '')
    if key in bank_map:
        return bank_map[key](merchant_id, terminal_id)
    if key == 'yapikredi':
        return YKBProtocol(merchant_id, terminal_id)
    return BankProtocol(merchant_id, terminal_id)
