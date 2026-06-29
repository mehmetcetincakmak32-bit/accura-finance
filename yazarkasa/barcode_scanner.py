
"""
Barkod Okuyucu Yonetim Modulu
================================
USB HID, Seri ve Bluetooth barkod okuyuculardan veri okuma,
barkod tipi tespiti ve callback mekanizmasi.
"""

import logging
import threading
import time
import re

logger = logging.getLogger(__name__)

try:
    import serial
    HAS_SERIAL = True
except ImportError:
    HAS_SERIAL = False
    logger.info("pyserial modulu bulunamadi, barkod okuyucu simulasyonu kullanilacak")


class BarcodeScanner:
    """
    Barkod okuyucu yonetim sinifi.

    USB HID (klavye arayuzu), Seri (RS-232) ve Bluetooth
    barkod okuyuculari destekler. Otomatik barkod tipi tespiti
    ve callback mekanizmasi icerir.
    """

    # Barkod tipleri ve regex desenleri
    BARCODE_PATTERNS = {
        "EAN13": r"^\d{13}$",
        "EAN8": r"^\d{8}$",
        "UPCA": r"^\d{12}$",
        "UPCE": r"^\d{6}$",
        "CODE39": r"^[A-Z0-9\-\.\ \$\/\+\%]+$",
        "CODE128": r"^[\x00-\x7F]+$",
        "ITF": r"^\d+$",
        "QRCODE": r"^.{1,100}$",  # Catch-all, detected by length/content
    }

    def __init__(self, config=None):
        """
        BarcodeScanner baslatma.

        Args:
            config: Config nesnesi veya sozluk
        """
        self.config = config
        self.port = "COM3"
        self.baudrate = 9600
        self.timeout = 1.0
        self.prefix = ""
        self.suffix = "\r\n"

        self.serial_port = None
        self.is_listening = False
        self.is_enabled = True
        self._listener_thread = None
        self._callback = None
        self._stop_event = threading.Event()

        if isinstance(config, dict):
            self.port = config.get("port", self.port)
            self.baudrate = config.get("baudrate", self.baudrate)
            self.timeout = config.get("timeout", self.timeout)
            self.prefix = config.get("prefix", self.prefix)
            self.suffix = config.get("suffix", self.suffix)
        elif config and hasattr(config, "data"):
            sconf = config.data.get("barcode_scanner", {})
            self.port = sconf.get("port", self.port)
            self.baudrate = sconf.get("baudrate", self.baudrate)
            self.timeout = sconf.get("timeout", self.timeout)
            self.prefix = sconf.get("prefix", self.prefix)
            self.suffix = sconf.get("suffix", self.suffix)

    def start_listening(self, port=None, baudrate=None):
        """
        Barkod okuyucudan okumaya baslar.

        Args:
            port: COM portu
            baudrate: Baud hizi

        Returns:
            bool: Basarili mi
        """
        if self.is_listening:
            logger.warning("Barkod okuyucu zaten dinleniyor: %s", self.port)
            return True

        if port:
            self.port = port
        if baudrate:
            self.baudrate = baudrate

        logger.info("Barkod okuyucu baslatiliyor (port: %s, baud: %d)...",
                    self.port, self.baudrate)

        if HAS_SERIAL:
            try:
                self.serial_port = serial.Serial(
                    port=self.port,
                    baudrate=self.baudrate,
                    bytesize=8,
                    parity="N",
                    stopbits=1,
                    timeout=self.timeout,
                )
                if not self.serial_port.is_open:
                    logger.error("Barkod okuyucu port acilamadi: %s", self.port)
                    return False
            except Exception as e:
                logger.error("Barkod okuyucu baglanti hatasi: %s", e)
                return False

        self.is_listening = True
        self._stop_event.clear()
        self._listener_thread = threading.Thread(target=self._listener_loop, daemon=True)
        self._listener_thread.start()

        logger.info("Barkod okuyucu dinleniyor: %s", self.port)
        return True

    def stop_listening(self):
        """
        Barkod okuyucu dinlemeyi durdurur.

        Returns:
            bool: Basarili mi
        """
        if not self.is_listening:
            return True

        logger.info("Barkod okuyucu durduruluyor...")

        self._stop_event.set()
        self.is_listening = False

        if self._listener_thread and self._listener_thread.is_alive():
            self._listener_thread.join(timeout=3.0)

        if HAS_SERIAL and self.serial_port:
            try:
                self.serial_port.close()
            except Exception as e:
                logger.error("Seri port kapatma hatasi: %s", e)

        self.serial_port = None
        self._listener_thread = None

        logger.info("Barkod okuyucu durduruldu")
        return True

    def _listener_loop(self):
        """Dinleme dongusu (arka plan thread)."""
        buffer = bytearray()

        while not self._stop_event.is_set() and self.is_listening:
            try:
                if HAS_SERIAL and self.serial_port:
                    # Seri porttan veri oku
                    if self.serial_port.in_waiting > 0:
                        data = self.serial_port.read(self.serial_port.in_waiting)
                        buffer.extend(data)

                        # Satir sonu karakterine gore ayir
                        suffix_bytes = self.suffix.encode("ascii", errors="replace")
                        while suffix_bytes in buffer:
                            idx = buffer.find(suffix_bytes)
                            line_bytes = buffer[:idx]
                            buffer = buffer[idx + len(suffix_bytes):]

                            if line_bytes:
                                self._process_raw_data(line_bytes)
                    else:
                        time.sleep(0.05)
                else:
                    # Simulasyon modu - yeni veri yok
                    time.sleep(0.1)

            except Exception as e:
                if not self._stop_event.is_set():
                    logger.error("Barkod okuma hatasi: %s", e)
                    time.sleep(0.5)

    def _process_raw_data(self, data):
        """Ham veriyi isler ve callback'i tetikler."""
        try:
            raw = data.decode("ascii", errors="replace").strip()
        except UnicodeDecodeError:
            raw = data.decode("utf-8", errors="replace").strip()

        if not raw:
            return

        # Prefix/suffix temizle
        if self.prefix and raw.startswith(self.prefix):
            raw = raw[len(self.prefix):]
        if self.suffix and raw.endswith(self.suffix.strip()):
            raw = raw[:-len(self.suffix.strip())]

        raw = raw.strip()

        if not raw:
            return

        if not self.is_enabled:
            logger.debug("Barkod okuyucu devre disi, atlaniyor: %s", raw)
            return

        # Barkodu parse et
        parsed = self.parse_barcode(raw)

        if parsed:
            logger.info("Barkod okundu: %s (tip: %s)", parsed["data"], parsed["type"])
            if self._callback:
                try:
                    self._callback(parsed)
                except Exception as e:
                    logger.error("Callback hatasi: %s", e)
        else:
            logger.debug("Bilinmeyen veri: %s", raw)

    def on_barcode(self, callback):
        """
        Barkod okundugunda cagrilacak fonksiyonu ayarlar.

        Args:
            callback: Callable - fonksiyon(barcode_dict)
                     barcode_dict: {"data": str, "type": str, "raw": str}
        """
        self._callback = callback
        logger.debug("Barkod callback fonksiyonu ayarlandi")

    def simulate_barcode(self, barcode):
        """
        Test amaciyla barkod okutma simule eder.

        Args:
            barcode: Barkod verisi
        """
        if not barcode:
            return

        logger.info("[SIMULASYON] Barkod okutuldu: %s", barcode)

        parsed = self.parse_barcode(barcode)
        if parsed:
            logger.info("Simule barkod: %s (tip: %s)", parsed["data"], parsed["type"])
            if self._callback:
                try:
                    self._callback(parsed)
                except Exception as e:
                    logger.error("Callback hatasi (simulasyon): %s", e)
        else:
            logger.warning("Simule barkod parse edilemedi: %s", barcode)

    @staticmethod
    def parse_barcode(data):
        """
        Barkod verisini parse eder ve tipini belirler.

        Args:
            data: Ham barkod verisi

        Returns:
            dict: {
                "data": str,
                "type": str (EAN13, CODE128, QRCODE, vb.),
                "raw": str (ham veri)
            } veya parse edilemezse None
        """
        if not data:
            return None

        raw_str = str(data).strip()

        if not raw_str:
            return None

        barcode_type = "UNKNOWN"

        for btype, pattern in BarcodeScanner.BARCODE_PATTERNS.items():
            if re.match(pattern, raw_str):
                barcode_type = btype
                break

        # QR kod tespiti (uzun metinler)
        if barcode_type == "UNKNOWN" and len(raw_str) > 30:
            barcode_type = "QRCODE"

        # EAN/UPC checksum dogrulama
        if barcode_type == "EAN13" and len(raw_str) == 13:
            if not BarcodeScanner._validate_ean13(raw_str):
                logger.debug("EAN13 checksum dogrulamasi basarisiz: %s", raw_str)
                barcode_type = "UNKNOWN"

        return {
            "data": raw_str,
            "type": barcode_type,
            "raw": str(data),
        }

    @staticmethod
    def _validate_ean13(ean):
        """EAN13 checksum dogrulamasi."""
        if len(ean) != 13 or not ean.isdigit():
            return False

        total = 0
        for i, digit in enumerate(ean[:12]):
            n = int(digit)
            total += n * 3 if i % 2 == 0 else n

        check = (10 - (total % 10)) % 10
        return check == int(ean[12])

    def enable_scanner(self):
        """
        Barkod okuyucuyu etkinlestirir.

        Returns:
            bool: Basarili mi
        """
        self.is_enabled = True
        logger.info("Barkod okuyucu etkinlestirildi")
        return True

    def disable_scanner(self):
        """
        Barkod okuyucuyu devre disi birakir.

        Returns:
            bool: Basarili mi
        """
        self.is_enabled = False
        logger.info("Barkod okuyucu devre disi birakildi")
        return True

    def get_status(self):
        """
        Barkod okuyucu durumunu dondurur.

        Returns:
            dict: Durum bilgisi
        """
        return {
            "listening": self.is_listening,
            "enabled": self.is_enabled,
            "port": self.port,
            "baudrate": self.baudrate,
            "connected": self.serial_port is not None and (
                self.serial_port.is_open if HAS_SERIAL else True
            ),
        }

    def test(self, simulate=True):
        """
        Barkod okuyucu testini calistirir.

        Args:
            simulate: Test barkodu simule et (True/False)

        Returns:
            dict: Test sonucu
        """
        logger.info("Barkod okuyucu testi baslatiliyor...")

        result = {
            "test_name": "Barkod Okuyucu Testi",
            "port": self.port,
            "start_test": False,
            "stop_test": False,
            "parse_test": False,
            "simulate_test": False,
            "overall": False,
        }

        # Baslatma testi
        try:
            result["start_test"] = self.start_listening()
        except Exception as e:
            logger.error("Baslatma testi hatasi: %s", e)

        # Parse testi
        try:
            test_barcodes = [
                ("8691234567890", "EAN13"),
                ("CODE128TEST", "CODE128"),
                ("12345678", "EAN8"),
                ("HELLO WORLD", "CODE39"),
            ]
            for test_data, expected_type in test_barcodes:
                parsed = self.parse_barcode(test_data)
                if parsed and parsed["type"] == expected_type:
                    result["parse_test"] = True
                    logger.debug("Parse test basarili: %s -> %s", test_data, parsed["type"])
                    break
        except Exception as e:
            logger.error("Parse testi hatasi: %s", e)

        # Simulasyon testi
        if simulate:
            try:
                self.simulate_barcode("8691234567890")
                result["simulate_test"] = True
            except Exception as e:
                logger.error("Simulasyon testi hatasi: %s", e)

        # Durdurma testi
        try:
            result["stop_test"] = self.stop_listening()
        except Exception as e:
            logger.error("Durdurma testi hatasi: %s", e)

        result["overall"] = (result["start_test"] and result["stop_test"]
                             and result["parse_test"])

        logger.info("Barkod okuyucu testi: %s",
                    "BASARILI" if result["overall"] else "BASARISIZ")

        return result

    def __repr__(self):
        return (
            f"BarcodeScanner(port={self.port}, listening={self.is_listening}, "
            f"enabled={self.is_enabled})"
        )
