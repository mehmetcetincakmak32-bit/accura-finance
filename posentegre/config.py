"""
Accura Finance - POS Entegrasyon Yapilandirmasi
Sunucu ayarlari, banka komisyon oranlari ve kimlik bilgileri
"""

import os
import json
import configparser


class POSConfig:
    """POS entegrasyon sistemi merkezi yapilandirma"""

    def __init__(self, config_dir=None):
        if config_dir is None:
            config_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'posentegre_logs'
            )
        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, 'pos_config.ini')
        os.makedirs(config_dir, exist_ok=True)
        self._config = configparser.ConfigParser()
        self._load()

    def _load(self):
        """Yapilandirma dosyasini yukle veya varsayilanlari olustur"""
        if os.path.exists(self.config_file):
            self._config.read(self.config_file, encoding='utf-8')
        else:
            self._create_defaults()
            self._save()

    def _create_defaults(self):
        """Varsayilan yapilandirma degerlerini olustur"""
        # Sunucu ayarlari
        self._config['SERVER'] = {
            'host': '127.0.0.1',
            'port': '9090',
            'max_clients': '10',
            'buffer_size': '4096',
            'timeout': '30'
        }

        # SSL/TLS ayarlari
        self._config['SSL'] = {
            'enabled': 'False',
            'cert_file': '',
            'key_file': '',
            'ca_file': ''
        }

        # Veritabani yolu
        self._config['DATABASE'] = {
            'log_db_path': os.path.join(self.config_dir, 'transactions.json')
        }

        # Banka komisyon oranlari (yuzde)
        self._config['COMMISSIONS'] = {
            'akbank': '1.8',
            'garanti': '1.6',
            'ykb': '1.9',
            'isbank': '1.7',
            'ziraat': '1.4',
            'halkbank': '1.5'
        }

        # Banka kimlik bilgileri (ortam değişkenlerinden ayarlanmalı)
        self._config['MERCHANT_IDS'] = {
            'akbank': '',
            'garanti': '',
            'ykb': '',
            'isbank': '',
            'ziraat': '',
            'halkbank': ''
        }

        self._config['TERMINAL_IDS'] = {
            'akbank': '',
            'garanti': '',
            'ykb': '',
            'isbank': '',
            'ziraat': '',
            'halkbank': ''
        }

        # REST API ayarlari
        self._config['REST_API'] = {
            'enabled': 'True',
            'host': '127.0.0.1',
            'port': '9091'
        }

    def _save(self):
        """Yapilandirmayi dosyaya kaydet"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                self._config.write(f)
        except Exception as e:
            print(f"POS yapilandirma kaydetme hatasi: {e}")

    def get(self, section, key, fallback=None):
        """Yapilandirma degeri al"""
        try:
            return self._config.get(section, key, fallback=fallback)
        except Exception:
            return fallback

    def getint(self, section, key, fallback=0):
        """Integer yapilandirma degeri al"""
        try:
            return self._config.getint(section, key, fallback=fallback)
        except Exception:
            return fallback

    def getfloat(self, section, key, fallback=0.0):
        """Float yapilandirma degeri al"""
        try:
            return self._config.getfloat(section, key, fallback=fallback)
        except Exception:
            return fallback

    def getboolean(self, section, key, fallback=False):
        """Boolean yapilandirma degeri al"""
        try:
            return self._config.getboolean(section, key, fallback=fallback)
        except Exception:
            return fallback

    def set(self, section, key, value):
        """Yapilandirma degeri ayarla ve kaydet"""
        if not self._config.has_section(section):
            self._config.add_section(section)
        self._config.set(section, key, str(value))
        self._save()

    @property
    def host(self):
        return self.get('SERVER', 'host', '127.0.0.1')

    @property
    def port(self):
        return self.getint('SERVER', 'port', 9090)

    @property
    def max_clients(self):
        return self.getint('SERVER', 'max_clients', 10)

    @property
    def buffer_size(self):
        return self.getint('SERVER', 'buffer_size', 4096)

    @property
    def ssl_enabled(self):
        return self.getboolean('SSL', 'enabled', False)

    @property
    def cert_file(self):
        return self.get('SSL', 'cert_file', '')

    @property
    def key_file(self):
        return self.get('SSL', 'key_file', '')

    def get_commission(self, bank_name):
        bank_key = bank_name.lower().replace(' ', '')
        return self.getfloat('COMMISSIONS', bank_key, 1.5)

    def get_merchant_id(self, bank_name):
        bank_key = bank_name.lower().replace(' ', '')
        return self.get('MERCHANT_IDS', bank_key, '')

    def get_terminal_id(self, bank_name):
        bank_key = bank_name.lower().replace(' ', '')
        return self.get('TERMINAL_IDS', bank_key, '')

    def get_log_db_path(self):
        return self.get('DATABASE', 'log_db_path',
                        os.path.join(self.config_dir, 'transactions.json'))
