"""
Accura Finance - POS Cihaz Yoneticisi
Fiziksel POS cihazlarinin kayit, baglanti, yapilandirma ve durum yonetimi
"""

import os
import json
import socket
import threading
import ssl
from datetime import datetime


class POSDeviceManager:
    """POS cihaz yoneticisi - baglanti, yapilandirma, durum takibi"""

    def __init__(self, storage_path=None):
        if storage_path is None:
            storage_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'posentegre_logs',
                'devices.json'
            )
        self.storage_path = storage_path
        self._devices = {}
        self._connections = {}
        self._lock = threading.Lock()
        self._ensure_storage()

    def _ensure_storage(self):
        """Depolama dosyasini kontrol et"""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        if not os.path.exists(self.storage_path):
            self._save_devices()

    def _load_devices(self):
        """Kayitli cihazlari yukle"""
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                with self._lock:
                    self._devices = data
        except (FileNotFoundError, json.JSONDecodeError):
            self._devices = {}

    def _save_devices(self):
        """Cihaz kayitlarini dosyaya kaydet"""
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(self._devices, f, ensure_ascii=False, indent=2)

    def register_device(self, device_id, device_type, bank, ip, port):
        """Yeni POS cihazi kaydet

        Args:
            device_id (str): Benzersiz cihaz ID
            device_type (str): Cihaz tipi (pinpad, terminal, yazici vb.)
            bank (str): Bagli oldugu banka
            ip (str): Cihaz IP adresi
            port (int): Cihaz portu

        Returns:
            dict: Kayit bilgisi
        """
        self._load_devices()

        with self._lock:
            if device_id in self._devices:
                return {'success': False, 'message': 'Bu cihaz zaten kayitli'}

            device = {
                'device_id': device_id,
                'device_type': device_type,
                'bank': bank,
                'ip': ip,
                'port': port,
                'ssl': False,
                'merchant_id': '',
                'terminal_id': '',
                'commission_rate': 1.5,
                'registered_at': datetime.now().isoformat(),
                'last_connected': None,
                'status': 'offline',
                'config': {}
            }

            self._devices[device_id] = device
            self._save_devices()

        return {'success': True, 'message': f'Cihaz {device_id} basariyla kaydedildi', 'device': device}

    def unregister_device(self, device_id):
        """POS cihazi kaydini sil

        Args:
            device_id (str): Silinecek cihaz ID

        Returns:
            dict: Islemin basarili olup olmadigi
        """
        self._load_devices()

        with self._lock:
            if device_id not in self._devices:
                return {'success': False, 'message': 'Cihaz bulunamadi'}

            self.disconnect_device(device_id)
            del self._devices[device_id]
            self._save_devices()

        return {'success': True, 'message': 'Cihaz kaydi silindi'}

    def get_device(self, device_id):
        """Cihaz bilgisini getir

        Args:
            device_id (str): Cihaz ID

        Returns:
            dict: Cihaz bilgisi veya None
        """
        self._load_devices()
        with self._lock:
            return self._devices.get(device_id)

    def list_devices(self):
        """Kayitli tum cihazlari listele

        Returns:
            list: Cihaz listesi
        """
        self._load_devices()
        with self._lock:
            return list(self._devices.values())

    def connect_device(self, device_id):
        """Cihazla TCP baglantisi kur

        Args:
            device_id (str): Baglanilacak cihaz ID

        Returns:
            dict: Baglanti sonucu
        """
        self._load_devices()

        with self._lock:
            device = self._devices.get(device_id)
            if not device:
                return {'success': False, 'message': 'Cihaz bulunamadi'}

            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                sock.connect((device['ip'], device['port']))

                if device.get('ssl'):
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    sock = context.wrap_socket(sock, server_hostname=device['ip'])

                self._connections[device_id] = sock
                device['status'] = 'online'
                device['last_connected'] = datetime.now().isoformat()
                self._save_devices()

                return {'success': True, 'message': f'Cihaz {device_id} baglandi'}
            except Exception as e:
                return {'success': False, 'message': f'Baglanti hatasi: {e}'}

    def disconnect_device(self, device_id):
        """Cihaz baglantisini kapat

        Args:
            device_id (str): Cihaz ID
        """
        with self._lock:
            conn = self._connections.pop(device_id, None)
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

            if device_id in self._devices:
                self._devices[device_id]['status'] = 'offline'
                self._save_devices()

    def get_device_status(self, device_id):
        """Cihazin online/offline durumunu kontrol et

        Args:
            device_id (str): Cihaz ID

        Returns:
            dict: Cihaz durumu
        """
        self._load_devices()

        with self._lock:
            device = self._devices.get(device_id)
            if not device:
                return {'success': False, 'message': 'Cihaz bulunamadi'}

            conn = self._connections.get(device_id)
            if conn:
                try:
                    conn.send(b'ping')
                    device['status'] = 'online'
                except Exception:
                    device['status'] = 'offline'
                    self._connections.pop(device_id, None)
                    try:
                        conn.close()
                    except Exception:
                        pass
            else:
                device['status'] = 'offline'

            self._save_devices()

            return {
                'success': True,
                'device_id': device_id,
                'status': device['status'],
                'bank': device['bank'],
                'last_connected': device.get('last_connected')
            }

    def configure_device(self, device_id, config):
        """Cihaz yapilandirmasi gonder

        Args:
            device_id (str): Cihaz ID
            config (dict): Yapilandirma parametreleri
                - merchant_id, terminal_id, commission_rate
                - ssl, ip, port

        Returns:
            dict: Islemin sonucu
        """
        self._load_devices()

        with self._lock:
            device = self._devices.get(device_id)
            if not device:
                return {'success': False, 'message': 'Cihaz bulunamadi'}

            for key, value in config.items():
                if key in ('merchant_id', 'terminal_id', 'commission_rate', 'ssl'):
                    device[key] = value
                elif key in ('ip', 'port'):
                    device[key] = value
                else:
                    device['config'][key] = value

            self._save_devices()

        return {'success': True, 'message': 'Cihaz yapilandirmasi guncellendi', 'device': device}

    def send_to_device(self, device_id, data):
        """Cihaza veri gonder

        Args:
            device_id (str): Cihaz ID
            data (bytes/str): Gonderilecek veri

        Returns:
            dict: Cevap
        """
        with self._lock:
            conn = self._connections.get(device_id)
            if not conn:
                return {'success': False, 'message': 'Cihaza bagli degil'}

            try:
                if isinstance(data, str):
                    data = data.encode('utf-8')
                conn.send(data)
                response = conn.recv(4096)
                return {'success': True, 'response': response.decode('utf-8')}
            except Exception as e:
                self._connections.pop(device_id, None)
                return {'success': False, 'message': f'Iletisim hatasi: {e}'}
