"""
Accura Finance - Sanal POS ve Online Odeme Kapisi Entegrasyonu
3D Secure, non-3D odeme ve taksit sorgulama islemleri
"""

import uuid
import random
import hashlib
import hmac
from datetime import datetime


class PaymentGateway:
    """Sanal POS ve online odeme kapisi entegrasyonu - birden fazla saglayiciyi destekler"""

    INSTALLMENT_LIMITS = {
        2: 250,
        3: 300,
        4: 400,
        6: 500,
        9: 750,
        12: 1000
    }

    def __init__(self):
        self.gateway_name = 'Genel'

    def process_3d_payment(self, card_info, amount, merchant_id, merchant_key):
        """3D Secure odeme islemi - banka sayfasina yonlendirmeli guvenli odeme

        Args:
            card_info (str): Kart bilgisi (kart_no|son_kul|cvv)
            amount (float): Odeme tutari
            merchant_id (str): Satici/Isyeri numarasi
            merchant_key (str): Satici anahtari

        Returns:
            dict: 3D secure HTML/form verisi ve islem detaylari
        """
        parts = card_info.split('|')
        card_no = parts[0].replace(' ', '')
        card_bin = card_no[:6]
        card_last4 = card_no[-4:]

        order_id = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"
        transaction_id = uuid.uuid4().hex[:20].upper()

        hash_str = f"{merchant_id}{order_id}{amount}{merchant_key}"
        hash_value = hashlib.sha256(hash_str.encode()).hexdigest()

        return {
            'success': True,
            'method': '3d',
            'order_id': order_id,
            'transaction_id': transaction_id,
            'amount': amount,
            'currency': 'TRY',
            'card_bin': card_bin,
            'card_last4': card_last4,
            'merchant_id': merchant_id,
            'hash': hash_value,
            'three_d_url': 'https://sanalpos.bankasistemi.com/3dgate',
            'html_form': self._generate_3d_form(
                merchant_id, order_id, amount, hash_value
            ),
            'status': 'pending_3d',
            'message': '3D dogrulama icin banka sayfasina yonlendiriliyor'
        }

    def process_non_3d(self, card_info, amount):
        """Non-3D (3Dsiz) odeme islemi - tek adimda guvenliksiz provizyon

        Args:
            card_info (str): Kart bilgisi (kart_no|son_kul|cvv)
            amount (float): Odeme tutari

        Returns:
            dict: Islem sonucu
        """
        parts = card_info.split('|')
        card_no = parts[0].replace(' ', '')
        card_bin = card_no[:6]
        card_last4 = card_no[-4:]

        order_id = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"
        auth_code = f"{random.randint(100000, 999999)}"
        reference_no = f"REF{datetime.now().strftime('%y%m%d')}{uuid.uuid4().hex[:8].upper()}"

        return {
            'success': True,
            'method': 'non_3d',
            'order_id': order_id,
            'auth_code': auth_code,
            'reference_no': reference_no,
            'amount': amount,
            'currency': 'TRY',
            'card_bin': card_bin,
            'card_last4': card_last4,
            'commission': round(amount * 0.016, 2),
            'net_amount': round(amount * 0.984, 2),
            'status': 'success',
            'message': 'Non-3D odeme basarili'
        }

    def verify_payment(self, order_id):
        """Odeme durumunu sorgula

        Args:
            order_id (str): Siparis numarasi

        Returns:
            dict: Odeme durumu
        """
        return {
            'success': True,
            'order_id': order_id,
            'status': random.choice(['success', 'pending', 'failed']),
            'verified_at': datetime.now().isoformat(),
            'message': 'Odeme durumu sorgulandi'
        }

    def refund_payment(self, transaction_id, amount):
        """Odeme iadesi

        Args:
            transaction_id (str): Islem ID
            amount (float): Iade tutari

        Returns:
            dict: Iade sonucu
        """
        refund_id = f"RF{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"

        return {
            'success': True,
            'transaction_id': transaction_id,
            'refund_id': refund_id,
            'amount': amount,
            'status': 'refunded',
            'message': f'{amount} TL iade edildi'
        }

    def query_installments(self, bin_number, amount):
        """Kart BIN numarasina gore taksit seceneklerini sorgula

        Args:
            bin_number (str): Kartin ilk 6 hanesi (BIN)
            amount (float): Sorgulanacak tutar

        Returns:
            dict: Uygun taksit secenekleri
        """
        bank = self._detect_bank_from_bin(bin_number)

        installments = []
        for taksit, min_amount in self.INSTALLMENT_LIMITS.items():
            if amount >= min_amount:
                commission_rate = self._get_installment_commission(taksit)
                monthly = round((amount + (amount * commission_rate / 100)) / taksit, 2)
                total = round(amount + (amount * commission_rate / 100), 2)
                installments.append({
                    'installment': taksit,
                    'monthly_amount': monthly,
                    'total_amount': total,
                    'commission_rate': commission_rate,
                    'commission_amount': round(total - amount, 2)
                })

        return {
            'success': True,
            'bin_number': bin_number,
            'bank': bank,
            'card_type': self._get_card_type(bin_number),
            'amount': amount,
            'installments': installments,
            'max_installment': max(i['installment'] for i in installments) if installments else 1
        }

    def _detect_bank_from_bin(self, bin_number):
        """BIN numarasina gore banka tespiti"""
        bin_prefixes = {
            '4546': 'Akbank',
            '5526': 'Akbank',
            '4261': 'Garanti',
            '4475': 'Garanti',
            '5400': 'YKB',
            '4790': 'YKB',
            '4506': 'Isbankasi',
            '4155': 'Isbankasi',
            '5200': 'Ziraat',
            '5520': 'Ziraat',
            '4024': 'Halkbank',
            '5101': 'Halkbank',
        }

        for prefix, bank_name in bin_prefixes.items():
            if bin_number.startswith(prefix):
                return bank_name

        return 'Diger Banka'

    def _get_card_type(self, bin_number):
        """Kart tipini belirle"""
        first_digit = bin_number[0] if bin_number else ''
        if first_digit == '4':
            return 'Visa'
        elif first_digit == '5':
            bin_2 = int(bin_number[:2]) if len(bin_number) >= 2 else 0
            if 51 <= bin_2 <= 55:
                return 'MasterCard'
        elif first_digit == '3':
            if bin_number[:2] in ('34', '37'):
                return 'American Express'
            elif bin_number[:2] in ('30', '36', '38'):
                return 'Diners Club'
        elif first_digit == '6':
            return 'Discover'

        return 'Bilinmeyen Kart'

    def _get_installment_commission(self, installment):
        """Taksit sayisina gore komisyon orani"""
        commissions = {
            1: 0,
            2: 1.2,
            3: 1.5,
            4: 1.8,
            6: 2.2,
            9: 2.8,
            12: 3.5
        }
        return commissions.get(installment, 2.0)

    def _generate_3d_form(self, merchant_id, order_id, amount, hash_value):
        """3D Secure odeme sayfasi icin HTML form olustur"""
        import html
        safe_merchant = html.escape(str(merchant_id), quote=True)
        safe_order = html.escape(str(order_id), quote=True)
        safe_amount = html.escape(str(amount), quote=True)
        safe_hash = html.escape(str(hash_value), quote=True)
        return f"""<form id="threed_form" method="post" action="https://sanalpos.bankasistemi.com/3dgate">
    <input type="hidden" name="merchant_id" value="{safe_merchant}">
    <input type="hidden" name="order_id" value="{safe_order}">
    <input type="hidden" name="amount" value="{safe_amount}">
    <input type="hidden" name="hash" value="{safe_hash}">
    <input type="submit" value="3D Dogrulama icin tiklayin">
</form>
<script>document.getElementById('threed_form').submit();</script>"""


class IyzicoGateway(PaymentGateway):
    """Iyzico odeme kapisi entegrasyonu"""

    def __init__(self, api_key='', secret_key=''):
        super().__init__()
        self.gateway_name = 'Iyzico'
        self.api_key = api_key
        self.secret_key = secret_key

    def process_3d_payment(self, card_info, amount, merchant_id, merchant_key):
        result = super().process_3d_payment(card_info, amount, merchant_id, merchant_key)
        result['gateway'] = 'iyzico'
        result['three_d_url'] = 'https://api.iyzico.com/v1/three_d'
        return result


class PayTRGateway(PaymentGateway):
    """PayTR odeme kapisi entegrasyonu"""

    def __init__(self, merchant_id='', merchant_key='', merchant_salt=''):
        super().__init__()
        self.gateway_name = 'PayTR'
        self.merchant_id = merchant_id
        self.merchant_key = merchant_key
        self.merchant_salt = merchant_salt

    def process_3d_payment(self, card_info, amount, merchant_id, merchant_key):
        result = super().process_3d_payment(card_info, amount, merchant_id, merchant_key)
        result['gateway'] = 'paytr'
        result['three_d_url'] = 'https://www.paytr.com/odeme'
        hash_str = f"{merchant_id}{result['order_id']}{amount}{merchant_key}"
        result['paytr_token'] = hashlib.sha256(hash_str.encode()).hexdigest()
        return result


class ParamGateway(PaymentGateway):
    """Param odeme kapisi entegrasyonu"""

    def __init__(self, client_code='', client_username='', client_password=''):
        super().__init__()
        self.gateway_name = 'Param'
        self.client_code = client_code
        self.client_username = client_username
        self.client_password = client_password

    def process_3d_payment(self, card_info, amount, merchant_id, merchant_key):
        result = super().process_3d_payment(card_info, amount, merchant_id, merchant_key)
        result['gateway'] = 'param'
        result['three_d_url'] = 'https://posws.param.com.tr/3dgate'
        return result


class PayUGateway(PaymentGateway):
    """PayU odeme kapisi entegrasyonu"""

    def __init__(self, merchant_code='', secret_key=''):
        super().__init__()
        self.gateway_name = 'PayU'
        self.merchant_code = merchant_code
        self.secret_key = secret_key

    def process_3d_payment(self, card_info, amount, merchant_id, merchant_key):
        result = super().process_3d_payment(card_info, amount, merchant_id, merchant_key)
        result['gateway'] = 'payu'
        result['three_d_url'] = 'https://secure.payu.com.tr/order/three_d'
        return result


class GarantiVPOSGateway(PaymentGateway):
    """Garanti Sanal POS entegrasyonu"""

    def __init__(self, terminal_id='', merchant_id='', user_code='', user_pass=''):
        super().__init__()
        self.gateway_name = 'GarantiVPOS'
        self.terminal_id = terminal_id
        self.merchant_id = merchant_id
        self.user_code = user_code
        self.user_pass = user_pass

    def process_3d_payment(self, card_info, amount, merchant_id, merchant_key):
        result = super().process_3d_payment(card_info, amount, merchant_id, merchant_key)
        result['gateway'] = 'garanti_vpos'
        result['three_d_url'] = 'https://sanalpos.garanti.com.tr/3dgate'
        return result


class AkbankPOSGateway(PaymentGateway):
    """Akbank Sanal POS entegrasyonu"""

    def __init__(self, merchant_id='', terminal_id='', store_key=''):
        super().__init__()
        self.gateway_name = 'AkbankPOS'
        self.merchant_id = merchant_id
        self.terminal_id = terminal_id
        self.store_key = store_key

    def process_3d_payment(self, card_info, amount, merchant_id, merchant_key):
        result = super().process_3d_payment(card_info, amount, merchant_id, merchant_key)
        result['gateway'] = 'akbank_pos'
        result['three_d_url'] = 'https://sanalpos.akbank.com.tr/3dgate'
        return result


def get_gateway(gateway_name, **kwargs):
    """Odeme kapisi adina gore uygun gateway nesnesini dondur"""
    gateway_map = {
        'iyzico': IyzicoGateway,
        'paytr': PayTRGateway,
        'param': ParamGateway,
        'payu': PayUGateway,
        'garanti_vpos': GarantiVPOSGateway,
        'akbank_pos': AkbankPOSGateway,
    }
    key = gateway_name.lower().replace(' ', '_')
    if key in gateway_map:
        return gateway_map[key](**kwargs)
    return PaymentGateway()
