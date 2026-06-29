"""
Accura Finance - POS Entegrasyon Sunucusu
Banka POS cihazlariyla TCP/IP uzerinden iletisim kuran ana sunucu
"""

import os
import socket
import threading
import json
import ssl
import logging
from datetime import datetime

from .config import POSConfig
from .transaction_logger import TransactionLogger
from .bank_protocols import get_protocol


class POSServer:
    """Ana POS entegrasyon sunucusu. Banka POS cihazlariyla TCP/IP uzerinden iletisim kurar."""

    def __init__(self, config=None):
        self.config = config or POSConfig()
        self.logger = self._setup_logger()
        self.transaction_logger = TransactionLogger(
            self.config.get_log_db_path()
        )
        self._server_socket = None
        self._running = False
        self._clients = {}
        self._client_lock = threading.Lock()

    def _setup_logger(self):
        """Sunucu logger'ini yapilandir"""
        log_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'posentegre_logs'
        )
        os.makedirs(log_dir, exist_ok=True)

        logger = logging.getLogger('POSServer')
        logger.setLevel(logging.DEBUG)

        if not logger.handlers:
            fh = logging.FileHandler(
                os.path.join(log_dir, f"sunucu_{datetime.now().strftime('%Y%m%d')}.log"),
                encoding='utf-8'
            )
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            ))
            logger.addHandler(fh)

            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)
            ch.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
            logger.addHandler(ch)

        return logger

    def start(self, host=None, port=None):
        """TCP/IP sunucusunu baslat

        Args:
            host (str): Baglanti adresi (varsayilan: 127.0.0.1)
            port (int): Baglanti portu (varsayilan: 9090)
        """
        if self._running:
            self.logger.warning('Sunucu zaten calisiyor')
            return {'success': False, 'message': 'Sunucu zaten calisiyor'}

        host = host or self.config.host
        port = port or self.config.port

        try:
            self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server_socket.bind((host, port))
            self._server_socket.listen(self.config.max_clients)
            self._server_socket.settimeout(1.0)

            if self.config.ssl_enabled:
                context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                context.load_cert_chain(
                    self.config.cert_file,
                    self.config.key_file
                )
                self._server_socket = context.wrap_socket(
                    self._server_socket,
                    server_side=True
                )
                self.logger.info('SSL/TLS guvenli baglanti aktif')

            self._running = True
            self._accept_thread = threading.Thread(target=self._accept_connections, daemon=True)
            self._accept_thread.start()

            self.logger.info(f'POS sunucu baslatildi: {host}:{port}')
            return {'success': True, 'message': f'Sunucu baslatildi: {host}:{port}'}

        except Exception as e:
            self.logger.error(f'Sunucu baslatilamadi: {e}')
            return {'success': False, 'message': f'Sunucu baslatilamadi: {e}'}

    def stop(self):
        """Sunucuyu durdur ve tum baglantilari kapat"""
        self._running = False

        with self._client_lock:
            for client_id, client_sock in self._clients.items():
                try:
                    client_sock.close()
                except Exception:
                    pass
            self._clients.clear()

        if self._server_socket:
            try:
                self._server_socket.close()
            except Exception:
                pass

        self.logger.info('POS sunucu durduruldu')
        return {'success': True, 'message': 'Sunucu durduruldu'}

    def _accept_connections(self):
        """Gelen baglantilari kabul eden thread"""
        while self._running:
            try:
                client_sock, client_addr = self._server_socket.accept()
                client_id = f"{client_addr[0]}:{client_addr[1]}"
                self.logger.info(f'Yeni baglanti: {client_id}')

                with self._client_lock:
                    self._clients[client_id] = client_sock

                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_id, client_sock, client_addr),
                    daemon=True
                )
                client_thread.start()

            except socket.timeout:
                continue
            except OSError:
                break
            except Exception as e:
                if self._running:
                    self.logger.error(f'Baglanti kabul hatasi: {e}')

    def _handle_client(self, client_id, client_sock, client_addr):
        """Bagli istemciyi yoneten thread

        Args:
            client_id (str): Istemci ID
            client_sock (socket): Istemci soketi
            client_addr (tuple): Istemci adresi (ip, port)
        """
        self.logger.info(f'Istemci baglandi: {client_addr}')

        try:
            while self._running:
                data = client_sock.recv(self.config.buffer_size)
                if not data:
                    break

                message = data.decode('utf-8')
                self.logger.debug(f'Istemciden mesaj {client_id}: {message[:100]}')

                response = self._process_message(message)
                client_sock.send(json.dumps(response, ensure_ascii=False).encode('utf-8'))

        except (ConnectionResetError, BrokenPipeError):
            self.logger.info(f'Istemci baglantisi koptu: {client_id}')
        except Exception as e:
            self.logger.error(f'Istemci hatasi {client_id}: {e}')
        finally:
            with self._client_lock:
                self._clients.pop(client_id, None)
            try:
                client_sock.close()
            except Exception:
                pass
            self.logger.info(f'Istemci ayrildi: {client_id}')

    def _process_message(self, message):
        """Gelen mesaji isle ve yanit olustur

        Args:
            message (str): Ham mesaj (JSON formatinda beklenir)

        Returns:
            dict: Islem sonucu
        """
        try:
            data = json.loads(message)
            command = data.get('command', '').lower()
            params = data.get('params', {})

            if command == 'payment':
                return self.process_transaction(
                    params.get('card_info', ''),
                    params.get('amount', 0),
                    params.get('installment', 1),
                    params.get('currency', 'TRY'),
                    params.get('bank', ''),
                    params.get('device_id', '')
                )
            elif command == 'refund':
                return self._process_refund(
                    params.get('reference_no', ''),
                    params.get('amount', 0)
                )
            elif command == 'cancel':
                return self._process_cancel(
                    params.get('reference_no', '')
                )
            elif command == 'status':
                return self.get_device_status(params.get('device_id', ''))
            elif command == 'settlement':
                return self._process_settlement(params.get('bank', ''))
            elif command == 'ping':
                return {'success': True, 'message': 'pong'}
            else:
                return {'success': False, 'message': f'Bilinmeyen komut: {command}'}

        except json.JSONDecodeError:
            return {'success': False, 'message': 'Gecersiz JSON formati'}
        except Exception as e:
            return {'success': False, 'message': f'Islem hatasi: {e}'}

    def process_transaction(self, card_info, amount, installment=1, currency='TRY', bank='', device_id=''):
        """Odeme islemini gerceklestir

        Args:
            card_info (str): Kart bilgisi (kart_no|son_kul|cvv)
            amount (float): Odeme tutari
            installment (int): Taksit sayisi
            currency (str): Para birimi (varsayilan: TRY)
            bank (str): Banka adi
            device_id (str): POS cihaz ID

        Returns:
            dict: Islem sonucu
        """
        self.logger.info(
            f'Odeme istegi - Tutar: {amount} {currency}, Taksit: {installment}, Banka: {bank}'
        )

        try:
            parts = card_info.split('|')
            card_no = parts[0].replace(' ', '')
            card_bin = card_no[:6]
            card_last4 = card_no[-4:]

            protocol = get_protocol(bank)
            result = protocol.process_payment(card_no, amount, installment)
            result['currency'] = currency
            result['device_id'] = device_id

            self.transaction_logger.log_transaction(result)

            self.logger.info(
                f'Odeme basarili - Ref: {result["reference_no"]}, '
                f'Auth: {result["auth_code"]}, Komisyon: {result["commission"]}'
            )

            return {'success': True, 'data': result}

        except Exception as e:
            self.logger.error(f'Odeme hatasi: {e}')
            return {'success': False, 'message': f'Odeme hatasi: {e}'}

    def send_command(self, device_id, command, data):
        """POS cihazina komut gonder

        Args:
            device_id (str): Cihaz ID
            command (str): Gonderilecek komut
            data (dict): Komut verisi

        Returns:
            dict: Cihaz cevabi
        """
        self.logger.info(f'Cihaza komut gonderiliyor: {device_id} -> {command}')

        message = json.dumps({
            'command': command,
            'params': data,
            'timestamp': datetime.now().isoformat()
        })

        with self._client_lock:
            client_sock = self._clients.get(device_id)

        if not client_sock:
            return {'success': False, 'message': 'Cihaz bagli degil'}

        try:
            client_sock.send(message.encode('utf-8'))
            response = client_sock.recv(self.config.buffer_size)
            return json.loads(response.decode('utf-8'))
        except Exception as e:
            return {'success': False, 'message': f'Komut gonderilemedi: {e}'}

    def get_device_status(self, device_id):
        """Cihaz baglanti durumunu kontrol et

        Args:
            device_id (str): Kontrol edilecek cihaz ID

        Returns:
            dict: Cihaz durumu
        """
        with self._client_lock:
            is_connected = device_id in self._clients
        return {
            'success': True,
            'device_id': device_id,
            'connected': is_connected,
            'status': 'online' if is_connected else 'offline'
        }

    def _process_refund(self, reference_no, amount):
        """Iade islemi"""
        self.logger.info(f'Iade istegi - Referans: {reference_no}, Tutar: {amount}')
        protocol = get_protocol('')
        result = protocol.process_refund(reference_no, amount)
        result['type'] = 'refund'
        self.transaction_logger.log_transaction(result)
        return {'success': True, 'data': result}

    def _process_cancel(self, reference_no):
        """Iptal islemi"""
        self.logger.info(f'Iptal istegi - Referans: {reference_no}')
        protocol = get_protocol('')
        result = protocol.process_cancel(reference_no)
        result['type'] = 'cancel'
        self.transaction_logger.log_transaction(result)
        return {'success': True, 'data': result}

    def _process_settlement(self, bank=''):
        """Gun sonu islemi"""
        self.logger.info(f'Gun sonu istegi - Banka: {bank}')
        protocol = get_protocol(bank)
        result = protocol.process_settlement()
        result['type'] = 'settlement'
        self.transaction_logger.log_transaction(result)
        return {'success': True, 'data': result}

    @property
    def is_running(self):
        return self._running

    @property
    def connected_clients(self):
        with self._client_lock:
            return list(self._clients.keys())
