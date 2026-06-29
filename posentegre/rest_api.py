"""
Accura Finance - REST API ile POS Entegrasyonu
HTTP uzerinden POS islemleri icin RESTful servis
"""

import os
import json
import socket
import threading
import logging
import hmac
from datetime import datetime
from urllib.parse import urlparse, parse_qs


class POSRestAPI:
    """REST API endpoint'leri ile POS entegrasyonu - HTTP uzerinden islem yonetimi"""

    def __init__(self, pos_server=None, config=None):
        self.pos_server = pos_server
        self.config = config
        self._server_socket = None
        self._running = False
        self._api_token = os.environ.get("POS_API_TOKEN", "")
        self.logger = self._setup_logger()

    def _setup_logger(self):
        logger = logging.getLogger('POSRestAPI')
        logger.setLevel(logging.DEBUG)
        if not logger.handlers:
            log_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'posentegre_logs'
            )
            os.makedirs(log_dir, exist_ok=True)
            fh = logging.FileHandler(
                os.path.join(log_dir, f"rest_api_{datetime.now().strftime('%Y%m%d')}.log"),
                encoding='utf-8'
            )
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            logger.addHandler(fh)
        return logger

    def start(self, host='127.0.0.1', port=9091):
        """REST API sunucusunu baslat

        Args:
            host (str): Dinlenecek adres
            port (int): Dinlenecek port
        """
        if self._running:
            return {'success': False, 'message': 'API zaten calisiyor'}

        try:
            self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server_socket.bind((host, port))
            self._server_socket.listen(5)
            self._server_socket.settimeout(1.0)
            self._running = True

            thread = threading.Thread(target=self._accept, daemon=True)
            thread.start()

            self.logger.info(f'REST API baslatildi: http://{host}:{port}')
            return {'success': True, 'message': f'API baslatildi: http://{host}:{port}'}

        except Exception as e:
            self.logger.error(f'API baslatilamadi: {e}')
            return {'success': False, 'message': f'API baslatilamadi: {e}'}

    def stop(self):
        """API sunucusunu durdur"""
        self._running = False
        if self._server_socket:
            try:
                self._server_socket.close()
            except Exception:
                pass
        self.logger.info('REST API durduruldu')
        return {'success': True, 'message': 'API durduruldu'}

    def _accept(self):
        """Gelen HTTP baglantilarini kabul et"""
        while self._running:
            try:
                client, addr = self._server_socket.accept()
                threading.Thread(
                    target=self._handle_request,
                    args=(client, addr),
                    daemon=True
                ).start()
            except socket.timeout:
                continue
            except Exception:
                break

    def _handle_request(self, client, addr):
        """HTTP istegini isle"""
        try:
            data = client.recv(8192).decode('utf-8')
            if not data:
                return

            request_line = data.split('\r\n')[0]
            method, path, _ = request_line.split(' ')

            parsed = urlparse(path)
            route = parsed.path.rstrip('/')
            query = parse_qs(parsed.query)

            body = ''
            if '\r\n\r\n' in data:
                body = data.split('\r\n\r\n', 1)[1]

            self.logger.debug(f'{method} {route} - {addr}')

            if not self._check_auth(data):
                err_resp = self._json_response({'success': False, 'message': 'Yetkisiz erisim'}, 401)
                client.sendall(err_resp.encode('utf-8'))
                return

            response = self._route(method, route, query, body)
            client.sendall(response.encode('utf-8'))

        except Exception as e:
            self.logger.error(f'HTTP istegi hatasi: {e}')
            error_resp = self._json_response({'success': False, 'message': 'Ic hata'}, 500)
            try:
                client.sendall(error_resp.encode('utf-8'))
            except Exception:
                pass
        finally:
            try:
                client.close()
            except Exception:
                pass

    def _route(self, method, route, query, body):
        """HTTP metod ve route'a gore islemi yonlendir"""
        routes = {
            ('POST', '/api/payment'): self.handle_payment,
            ('POST', '/api/refund'): self.handle_refund,
            ('POST', '/api/cancel'): self.handle_cancel,
            ('GET', '/api/status'): self.handle_status,
            ('GET', '/api/settlement'): self.handle_settlement,
            ('GET', '/api/transactions'): self.handle_transactions,
            ('POST', '/api/installment-query'): self.handle_installment_query,
        }

        handler = routes.get((method, route))
        if handler:
            params = {}
            if method == 'POST' and body:
                try:
                    params = json.loads(body)
                except json.JSONDecodeError:
                    pass
            params.update(query)

            result = handler(params)
            return self._json_response(result)
        else:
            return self._json_response(
                {'success': False, 'message': f'{method} {route} bulunamadi'},
                404
            )

    def _check_auth(self, request_data):
        if not self._api_token:
            return True
        auth_header = None
        for line in request_data.split('\r\n'):
            if line.lower().startswith('authorization:'):
                auth_header = line.split(':', 1)[1].strip()
                break
        if auth_header and auth_header.lower().startswith('bearer '):
            token = auth_header[7:]
            return hmac.compare_digest(token, self._api_token)
        return False

    def _json_response(self, data, status=200):
        """HTTP JSON yaniti olustur"""
        body = json.dumps(data, ensure_ascii=False, indent=2)
        status_text = {200: 'OK', 400: 'Bad Request', 401: 'Unauthorized', 404: 'Not Found', 500: 'Internal Server Error'}
        return (
            f"HTTP/1.1 {status} {status_text.get(status, 'Unknown')}\r\n"
            f"Content-Type: application/json; charset=utf-8\r\n"
            f"Content-Length: {len(body.encode('utf-8'))}\r\n"
            f"Access-Control-Allow-Origin: {self._get_allowed_origin()}\r\n"
            f"Connection: close\r\n"
            f"\r\n"
            f"{body}"
        )

    def _get_allowed_origin(self):
        return os.environ.get("POS_API_ALLOWED_ORIGIN", "http://localhost:3000")

    def handle_payment(self, params):
        """POST /api/payment - Odeme islemi

        Parameters:
            card_number (str): Kart numarasi
            card_expiry (str): Son kullanma tarihi (AA/YY)
            card_cvv (str): CVV kodu
            amount (float): Tutar
            installment (int): Taksit (varsayilan: 1)
            currency (str): Para birimi (varsayilan: TRY)
            bank (str): Banka adi
        """
        card_number = params.get('card_number', '')
        if not card_number:
            return {'success': False, 'message': 'Kart numarasi gerekli'}

        amount = params.get('amount', 0)
        try:
            amount = float(amount)
        except (TypeError, ValueError):
            return {'success': False, 'message': 'Gecersiz tutar'}

        installment = int(params.get('installment', 1))
        currency = params.get('currency', 'TRY')
        bank = params.get('bank', '')

        card_info = f"{card_number}|{params.get('card_expiry', '12/28')}|{params.get('card_cvv', '000')}"

        if self.pos_server:
            result = self.pos_server.process_transaction(
                card_info, amount, installment, currency, bank
            )
        else:
            from .bank_protocols import get_protocol
            protocol = get_protocol(bank)
            result = get_protocol(bank).process_payment(card_number, amount, installment)
            from .transaction_logger import TransactionLogger
            logger = TransactionLogger()
            logger.log_transaction(result)
            result = {'success': True, 'data': result}

        return result

    def handle_refund(self, params):
        """POST /api/refund - Iade islemi

        Parameters:
            reference_no (str): Orijinal islem referans no
            amount (float): Iade tutari
        """
        reference_no = params.get('reference_no', '')
        amount = params.get('amount', 0)

        if not reference_no:
            return {'success': False, 'message': 'Referans numarasi gerekli'}

        try:
            amount = float(amount)
        except (TypeError, ValueError):
            return {'success': False, 'message': 'Gecersiz tutar'}

        if self.pos_server:
            from .bank_protocols import get_protocol
            protocol = get_protocol('')
            result = protocol.process_refund(reference_no, amount)
            result['type'] = 'refund'
            txn_logger = self.pos_server.transaction_logger
            txn_logger.log_transaction(result)
            return {'success': True, 'data': result}
        else:
            from .bank_protocols import get_protocol
            protocol = get_protocol('')
            result = protocol.process_refund(reference_no, amount)
            result['type'] = 'refund'
            from .transaction_logger import TransactionLogger
            TransactionLogger().log_transaction(result)
            return {'success': True, 'data': result}

    def handle_cancel(self, params):
        """POST /api/cancel - Iptal islemi

        Parameters:
            reference_no (str): Iptal edilecek referans no
        """
        reference_no = params.get('reference_no', '')
        if not reference_no:
            return {'success': False, 'message': 'Referans numarasi gerekli'}

        if self.pos_server:
            from .bank_protocols import get_protocol
            protocol = get_protocol('')
            result = protocol.process_cancel(reference_no)
            result['type'] = 'cancel'
            self.pos_server.transaction_logger.log_transaction(result)
            return {'success': True, 'data': result}
        else:
            from .bank_protocols import get_protocol
            protocol = get_protocol('')
            result = protocol.process_cancel(reference_no)
            result['type'] = 'cancel'
            from .transaction_logger import TransactionLogger
            TransactionLogger().log_transaction(result)
            return {'success': True, 'data': result}

    def handle_status(self, params):
        """GET /api/status - POS cihaz veya sunucu durumu

        Parameters:
            device_id (str, optional): Cihaz ID
        """
        device_id = params.get('device_id', '')

        if device_id and self.pos_server:
            return self.pos_server.get_device_status(device_id)

        return {
            'success': True,
            'data': {
                'server': 'running' if (self.pos_server and self.pos_server.is_running) else 'unknown',
                'api': 'running' if self._running else 'stopped',
                'timestamp': datetime.now().isoformat()
            }
        }

    def handle_settlement(self, params):
        """GET /api/settlement - Gun sonu raporu

        Parameters:
            date (str, optional): Tarih (YYYY-MM-DD)
            bank (str, optional): Banka adi
        """
        date = params.get('date', datetime.now().strftime('%Y-%m-%d'))
        bank = params.get('bank', '')

        from .transaction_logger import TransactionLogger
        txn_logger = TransactionLogger()

        report = txn_logger.get_settlement_report(date)

        if bank and bank in report.get('bank_details', {}):
            report['bank_details'] = {bank: report['bank_details'][bank]}

        return {'success': True, 'data': report}

    def handle_transactions(self, params):
        """GET /api/transactions - Islem listesi

        Parameters:
            start_date (str, optional): Baslangic tarihi
            end_date (str, optional): Bitis tarihi
            bank (str, optional): Banka filtre
            status (str, optional): Durum filtre
        """
        start = params.get('start_date', params.get('start', ''))
        end = params.get('end_date', params.get('end', ''))

        date_range = None
        if start and end:
            date_range = (start, end)

        bank = params.get('bank', '')
        status = params.get('status', '')

        from .transaction_logger import TransactionLogger
        txn_logger = TransactionLogger()
        transactions = txn_logger.get_transactions(
            date_range=date_range,
            bank=bank,
            status=status
        )

        return {'success': True, 'data': {'count': len(transactions), 'transactions': transactions}}

    def handle_installment_query(self, params):
        """POST /api/installment-query - Taksit seceneklerini sorgula

        Parameters:
            bin_number (str): Kart BIN numarasi (ilk 6 hane)
            amount (float): Tutar
        """
        bin_number = params.get('bin_number', params.get('bin', ''))
        amount = params.get('amount', 0)

        try:
            amount = float(amount)
        except (TypeError, ValueError):
            amount = 0

        if not bin_number:
            return {'success': False, 'message': 'BIN numarasi gerekli'}

        from .payment_gateway import PaymentGateway
        gateway = PaymentGateway()
        result = gateway.query_installments(bin_number, amount)

        return {'success': True, 'data': result}

    @property
    def is_running(self):
        return self._running
