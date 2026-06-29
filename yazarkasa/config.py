
"""
Yazarkasa Yapilandirma Modulu
==============================
Varsayilan port ayarlari, desteklenen cihaz listesi,
fis baslik/ayak bilgileri ve satici bilgileri.
"""

import json
import os
import logging

logger = logging.getLogger(__name__)


class Config:
    """
    Yazarkasa sistemi yapilandirma sinifi.
    Tum cevre birimleri icin port, hiz ve diger
    parametreleri icerir.
    """

    # Varsayilan port yapilandirmalari
    DEFAULT_CONFIG = {
        "fiscal_printer": {
            "port": "COM1",
            "baudrate": 9600,
            "bytesize": 8,
            "parity": "N",
            "stopbits": 1,
            "timeout": 5.0,
            "model": "auto",
        },
        "receipt_printer": {
            "port": "COM1",
            "baudrate": 9600,
            "bytesize": 8,
            "parity": "N",
            "stopbits": 1,
            "timeout": 5.0,
        },
        "cash_drawer": {
            "port": "COM1",
            "pin": 2,
            "pulse_duration": 200,
        },
        "customer_display": {
            "port": "COM2",
            "baudrate": 9600,
            "bytesize": 8,
            "parity": "N",
            "stopbits": 1,
            "timeout": 2.0,
            "model": "CD5220",
            "columns": 20,
            "rows": 2,
        },
        "barcode_scanner": {
            "port": "COM3",
            "baudrate": 9600,
            "bytesize": 8,
            "parity": "N",
            "stopbits": 1,
            "timeout": 1.0,
            "prefix": "",
            "suffix": "\r\n",
        },
    }

    # Desteklenen mali yazici markalari
    SUPPORTED_PRINTERS = [
        "Epson",
        "Star",
        "Bixolon",
        "Eurotech",
        "Nashuatec",
    ]

    # Desteklenen musteri ekrani modelleri
    SUPPORTED_DISPLAYS = [
        "CD5220",
        "Epson",
        "Bixolon",
        "POS-X",
        "AIPHA",
        "Generic",
    ]

    # Desteklenen barkod tipleri
    BARCODE_TYPES = [
        "CODE128",
        "EAN13",
        "EAN8",
        "CODE39",
        "ITF",
        "UPCA",
        "UPCE",
        "QRCODE",
    ]

    # Turkce karakter kodlamalari
    ENCODINGS = {
        "cp857": "CP857",
        "cp1254": "CP1254",
        "iso88599": "ISO-8859-9",
        "utf8": "UTF-8",
    }

    def __init__(self, config_path=None):
        """
        Yapilandirma yukleyici.

        Args:
            config_path: JSON yapilandirma dosyasi yolu (opsiyonel)
        """
        self.config_path = config_path
        self.data = dict(self.DEFAULT_CONFIG)

        self.receipt_header = ""
        self.receipt_footer = ""
        self.encoding = "cp857"
        self.encoding_name = "CP857"
        self.char_per_line = 42
        self.merchant_info = {
            "name": "ISYERI ADI",
            "tax_office": "VERGI DAIRESI",
            "tax_number": "1234567890",
            "address": "ADRES SATIRI 1\nADRES SATIRI 2",
            "phone": "0212 123 45 67",
            "website": "",
            "email": "",
        }

        if config_path and os.path.exists(config_path):
            self._load_config(config_path)

    def _load_config(self, path):
        """JSON dosyasindan yapilandirma yukler."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                loaded = json.load(f)

            if "fiscal_printer" in loaded:
                self.data["fiscal_printer"].update(loaded["fiscal_printer"])
            if "receipt_printer" in loaded:
                self.data["receipt_printer"].update(loaded["receipt_printer"])
            if "cash_drawer" in loaded:
                self.data["cash_drawer"].update(loaded["cash_drawer"])
            if "customer_display" in loaded:
                self.data["customer_display"].update(loaded["customer_display"])
            if "barcode_scanner" in loaded:
                self.data["barcode_scanner"].update(loaded["barcode_scanner"])
            if "receipt_header" in loaded:
                self.receipt_header = loaded["receipt_header"]
            if "receipt_footer" in loaded:
                self.receipt_footer = loaded["receipt_footer"]
            if "encoding" in loaded:
                self.set_encoding(loaded["encoding"])
            if "char_per_line" in loaded:
                self.char_per_line = loaded["char_per_line"]
            if "merchant_info" in loaded:
                self.merchant_info.update(loaded["merchant_info"])

            logger.info("Yapilandirma dosyadan yuklendi: %s", path)

        except (json.JSONDecodeError, KeyError) as e:
            logger.error("Yapilandirma yukleme hatasi: %s", e)

    def save_config(self, path=None):
        """Yapilandirmayi JSON dosyasina kaydeder."""
        save_path = path or self.config_path
        if not save_path:
            logger.warning("Kayit yolu belirtilmedi")
            return False

        try:
            output = {
                "fiscal_printer": self.data["fiscal_printer"],
                "receipt_printer": self.data["receipt_printer"],
                "cash_drawer": self.data["cash_drawer"],
                "customer_display": self.data["customer_display"],
                "barcode_scanner": self.data["barcode_scanner"],
                "receipt_header": self.receipt_header,
                "receipt_footer": self.receipt_footer,
                "encoding": self.encoding,
                "char_per_line": self.char_per_line,
                "merchant_info": self.merchant_info,
            }

            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(output, f, ensure_ascii=False, indent=2)

            logger.info("Yapilandirma kaydedildi: %s", save_path)
            return True

        except OSError as e:
            logger.error("Yapilandirma kayit hatasi: %s", e)
            return False

    def set_encoding(self, encoding_key):
        """Kodlama ayarini yapar."""
        if encoding_key in self.ENCODINGS:
            self.encoding = encoding_key
            self.encoding_name = self.ENCODINGS[encoding_key]
            logger.info("Kodlama ayarlandi: %s (%s)", encoding_key, self.encoding_name)
        else:
            logger.warning("Bilinmeyen kodlama: %s, varsayilan kullaniliyor", encoding_key)

    def set_merchant_info(self, **kwargs):
        """Satici bilgilerini gunceller."""
        self.merchant_info.update(kwargs)
        logger.info("Satici bilgileri guncellendi")

    def set_header_footer(self, header="", footer=""):
        """Fis baslik ve ayak yazisini ayarlar."""
        self.receipt_header = header
        self.receipt_footer = footer
        logger.info("Fis baslik/ayak yazisi guncellendi")

    def get_printer_config(self):
        """Mali yazici yapilandirmasini dondurur."""
        return dict(self.data["fiscal_printer"])

    def get_display_config(self):
        """Musteri ekrani yapilandirmasini dondurur."""
        return dict(self.data["customer_display"])

    def get_scanner_config(self):
        """Barkod okuyucu yapilandirmasini dondurur."""
        return dict(self.data["barcode_scanner"])

    def get_drawer_config(self):
        """Kasa cekmecesi yapilandirmasini dondurur."""
        return dict(self.data["cash_drawer"])

    @staticmethod
    def list_available_encodings():
        """Mevcut kodlamalari listeler."""
        return list(Config.ENCODINGS.keys())

    def __repr__(self):
        return (
            f"Config(printer={self.data['fiscal_printer']['port']}, "
            f"display={self.data['customer_display']['port']}, "
            f"scanner={self.data['barcode_scanner']['port']}, "
            f"drawer={self.data['cash_drawer']['port']})"
        )
