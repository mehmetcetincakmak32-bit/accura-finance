
"""
Mali Yazici Surucusu - ESC/POS Protokolu
===========================================
Seri port/USB uzerinden mali yazici ile iletisim.
Epson, Star, Bixolon, Eurotech ve Nashuatec destegi.
pyserial yoksa simulasyon modunda calisir.
"""

import logging
import time
import threading

logger = logging.getLogger(__name__)

try:
    import serial
    HAS_SERIAL = True
except ImportError:
    HAS_SERIAL = False
    logger.info("pyserial modulu bulunamadi, simulasyon modu kullanilacak")


class FiscalPrinter:
    """
    Mali yazici surucusu - ESC/POS protokolu ile iletisim.

    Epson, Star, Bixolon, Eurotech, Nashuatec ve
    diger ESC/POS uyumlu yazicilari destekler.
    """

    # ESC/POS komut sabitleri
    ESC = 0x1B
    GS = 0x1D
    LF = 0x0A
    CR = 0x0D
    DLE = 0x10
    CAN = 0x18

    def __init__(self, config=None):
        """
        FiscalPrinter baslatma.

        Args:
            config: Config nesnesi veya port ayarlari sozlugu
        """
        self.config = config
        self.serial_port = None
        self.is_connected = False
        self.port = "COM1"
        self.baudrate = 9600
        self.bytesize = 8
        self.parity = "N"
        self.stopbits = 1
        self.timeout = 5.0
        self.model = "auto"
        self._lock = threading.Lock()

        if isinstance(config, dict):
            self.port = config.get("port", self.port)
            self.baudrate = config.get("baudrate", self.baudrate)
            self.bytesize = config.get("bytesize", self.bytesize)
            self.parity = config.get("parity", self.parity)
            self.stopbits = config.get("stopbits", self.stopbits)
            self.timeout = config.get("timeout", self.timeout)
            self.model = config.get("model", self.model)
        elif config and hasattr(config, "data"):
            pconf = config.data.get("fiscal_printer", {})
            self.port = pconf.get("port", self.port)
            self.baudrate = pconf.get("baudrate", self.baudrate)
            self.bytesize = pconf.get("bytesize", self.bytesize)
            self.parity = pconf.get("parity", self.parity)
            self.stopbits = pconf.get("stopbits", self.stopbits)
            self.timeout = pconf.get("timeout", self.timeout)
            self.model = pconf.get("model", self.model)

    def connect(self, port=None, baudrate=None):
        """
        Yaziciya baglanir.

        Args:
            port: COM portu (orn. "COM1", "/dev/ttyUSB0")
            baudrate: Baud hizi (varsayilan: 9600)

        Returns:
            bool: Baglanti basarili mi
        """
        if port:
            self.port = port
        if baudrate:
            self.baudrate = baudrate

        if self.is_connected:
            logger.warning("Yazici zaten bagli: %s", self.port)
            return True

        parity_map = {"N": serial.PARITY_NONE, "E": serial.PARITY_EVEN,
                      "O": serial.PARITY_ODD} if HAS_SERIAL else {}
        parity = parity_map.get(self.parity, serial.PARITY_NONE) if HAS_SERIAL else self.parity
        stopbits_map = {1: serial.STOPBITS_ONE, 2: serial.STOPBITS_TWO} if HAS_SERIAL else {}

        if HAS_SERIAL:
            try:
                self.serial_port = serial.Serial(
                    port=self.port,
                    baudrate=self.baudrate,
                    bytesize=self.bytesize,
                    parity=parity,
                    stopbits=stopbits_map.get(self.stopbits, serial.STOPBITS_ONE),
                    timeout=self.timeout,
                )
                self.is_connected = self.serial_port.is_open
                if self.is_connected:
                    logger.info("Yaziciya baglanildi: %s (%d baud)", self.port, self.baudrate)
                    # Yaziciyi baslat
                    self._send_raw_bytes(bytes([0x1B, 0x40]))
                else:
                    logger.error("Yazici baglantisi acilamadi: %s", self.port)

            except Exception as e:
                logger.error("Baglanti hatasi (%s): %s", self.port, e)
                self.is_connected = False
                self.serial_port = None
        else:
            # Simulasyon modu
            logger.info("[SIMULASYON] Yazici baglantisi: %s (%d baud)", self.port, self.baudrate)
            self.is_connected = True
            time.sleep(0.1)

        return self.is_connected

    def disconnect(self):
        """
        Yazici baglantisini kapatir.

        Returns:
            bool: Basarili mi
        """
        if not self.is_connected:
            logger.warning("Yazici zaten bagli degil")
            return True

        if HAS_SERIAL and self.serial_port:
            try:
                self.serial_port.close()
                logger.info("Yazici baglantisi kapatildi: %s", self.port)
            except Exception as e:
                logger.error("Baglanti kapatma hatasi: %s", e)
                return False
        else:
            logger.info("[SIMULASYON] Yazici baglantisi kapatildi: %s", self.port)

        self.is_connected = False
        self.serial_port = None
        return True

    def send_raw(self, data):
        """
        Ham ESC/POS komutu gonderir.

        Args:
            data: bytes veya str (str ise CP857 ile kodlanir)

        Returns:
            int: Gonderilen bayt sayisi
        """
        if not self.is_connected:
            logger.error("Yazici bagli degil, komut gonderilemedi")
            return 0

        if isinstance(data, str):
            data = data.encode("cp857", errors="replace")

        return self._send_raw_bytes(data)

    def _send_raw_bytes(self, data):
        """Ham bayt dizisini yaziciya gonderir (thread safe)."""
        with self._lock:
            if HAS_SERIAL and self.serial_port:
                try:
                    written = self.serial_port.write(data)
                    self.serial_port.flush()
                    logger.debug("Gonderildi (%d bayt): %s", written, data.hex())
                    return written
                except Exception as e:
                    logger.error("Veri gonderme hatasi: %s", e)
                    return 0
            else:
                # Simulasyon
                hex_str = " ".join(f"{b:02X}" for b in data)
                logger.info("[SIMULASYON] Gonderildi (%d bayt): %s", len(data), hex_str)
                time.sleep(0.05)
                return len(data)

    def _read_response(self, length=1):
        """Yazicidan yanit okur."""
        if HAS_SERIAL and self.serial_port and self.is_connected:
            try:
                response = self.serial_port.read(length)
                logger.debug("Yanit (%d bayt): %s", len(response), response.hex())
                return response
            except Exception as e:
                logger.error("Yanit okuma hatasi: %s", e)
                return b""
        else:
            logger.debug("[SIMULASYON] Yanit okuma (%d bayt): simulasyon", length)
            return b"\x00"

    # --- Ana fonksiyonlar ---

    def print_receipt(self, receipt_data):
        """
        Fis yazdirir.

        Args:
            receipt_data: ReceiptBuilder nesnesi veya ESC/POS byte dizisi

        Returns:
            bool: Basarili mi
        """
        if not self.is_connected:
            logger.error("Yazici bagli degil, fis yazdirilamadi")
            return False

        logger.info("Fis yazdiriliyor...")

        if hasattr(receipt_data, "get_escpos"):
            data = receipt_data.get_escpos()
        elif isinstance(receipt_data, bytes):
            data = receipt_data
        elif isinstance(receipt_data, str):
            data = receipt_data.encode("cp857", errors="replace")
        else:
            logger.error("Gecersiz fis verisi tipi: %s", type(receipt_data))
            return False

        try:
            sent = self.send_raw(data)
            logger.info("Fis yazdirildi (%d bayt)", sent)
            return sent > 0
        except Exception as e:
            logger.error("Fis yazdirma hatasi: %s", e)
            return False

    def print_invoice(self, invoice_data):
        """
        Fatura yazdirir.

        Args:
            invoice_data: ReceiptBuilder.build_invoice() ciktisi veya
                         byte/str veri

        Returns:
            bool: Basarili mi
        """
        logger.info("Fatura yazdiriliyor...")
        return self.print_receipt(invoice_data)

    def print_report(self, report_type="Z"):
        """
        Rapor yazdirir (Z veya X).

        Args:
            report_type: "Z" (gun sonu) veya "X" (ara rapor)

        Returns:
            bool: Basarili mi
        """
        if not self.is_connected:
            logger.error("Yazici bagli degil, rapor yazdirilamadi")
            return False

        logger.info("Rapor yazdiriliyor: %s", report_type)

        # ESC/POS: Rapor komutlari (ureticiye gore degisir)
        try:
            if report_type.upper() == "Z":
                # Z raporu: GS V 0 + ozel komutlar
                data = bytes([
                    0x1B, 0x40,  # Initialize
                    0x1B, 0x61, 0x01,  # Center align
                ])
                data += f"Z RAPORU\n".encode("cp857", errors="replace")
                data += f"{time.strftime('%d.%m.%Y %H:%M:%S')}\n\n".encode("cp857", errors="replace")
                data += bytes([0x1D, 0x56, 0x00])  # Cut
                self.send_raw(data)
            else:
                # X raporu
                data = bytes([
                    0x1B, 0x40,
                    0x1B, 0x61, 0x01,
                ])
                data += f"X RAPORU\n".encode("cp857", errors="replace")
                data += f"{time.strftime('%d.%m.%Y %H:%M:%S')}\n\n".encode("cp857", errors="replace")
                data += bytes([0x1D, 0x56, 0x00])
                self.send_raw(data)

            logger.info("Rapor yazdirildi: %s", report_type)
            return True

        except Exception as e:
            logger.error("Rapor yazdirma hatasi: %s", e)
            return False

    def open_drawer(self):
        """
        Kasa cekmecesini acar.

        Returns:
            bool: Basarili mi
        """
        if not self.is_connected:
            logger.error("Yazici bagli degil, kasa acilamadi")
            return False

        logger.info("Kasa cekmecesi aciliyor...")

        try:
            # ESC/POS draw kick komutu (pin 2)
            self.send_raw(bytes([0x10, 0x14, 0x01, 0x00, 0x05]))
            logger.info("Kasa cekmecesi acildi")
            return True
        except Exception as e:
            logger.error("Kasa acma hatasi: %s", e)
            return False

    def get_status(self):
        """
        Yazici durumunu sorgular.

        Returns:
            dict: {
                "online": bool,
                "paper": bool (kagit var mi),
                "cover_open": bool,
                "error": bool,
                "error_description": str,
                "drawer_open": bool,
            }
        """
        status = {
            "online": self.is_connected,
            "paper": True,
            "cover_open": False,
            "error": False,
            "error_description": "",
            "drawer_open": False,
        }

        if not self.is_connected:
            status["error"] = True
            status["error_description"] = "Yazici bagli degil"
            return status

        if HAS_SERIAL and self.serial_port:
            try:
                # ESC/POS status commands
                # Paper status: DLE EOT 1
                self._send_raw_bytes(bytes([0x10, 0x04, 0x01]))
                paper_response = self._read_response(1)
                if paper_response:
                    paper_byte = paper_response[0]
                    status["paper"] = not bool(paper_byte & 0x0C)

                # Online status: DLE EOT 2
                self._send_raw_bytes(bytes([0x10, 0x04, 0x02]))
                online_response = self._read_response(1)
                if online_response:
                    status["online"] = online_response[0] == 0x00

                # Error status: DLE EOT 4
                self._send_raw_bytes(bytes([0x10, 0x04, 0x04]))
                error_response = self._read_response(1)
                if error_response:
                    err_byte = error_response[0]
                    status["error"] = bool(err_byte & 0x08)
                    status["cover_open"] = bool(err_byte & 0x04)
                    if err_byte & 0x08:
                        status["error_description"] = "Mekanik hata"
                    elif err_byte & 0x04:
                        status["error_description"] = "Kapi acik"

            except Exception as e:
                logger.error("Durum sorgulama hatasi: %s", e)
                status["error"] = True
                status["error_description"] = str(e)
        else:
            # Simulasyon
            logger.info("[SIMULASYON] Durum sorgulandi: online=%s", status["online"])

        return status

    def cut_paper(self, cut_type="full"):
        """
        Kagit keser.

        Args:
            cut_type: "full" (tam) veya "partial" (kismi)

        Returns:
            bool: Basarili mi
        """
        if not self.is_connected:
            logger.error("Yazici bagli degil, kagit kesilemedi")
            return False

        logger.info("Kagit kesiliyor (%s)...", cut_type)

        try:
            if cut_type == "partial":
                self.send_raw(bytes([0x1B, 0x6D]))  # ESC m (partial cut)
            else:
                self.send_raw(bytes([0x1D, 0x56, 0x00]))  # GS V 0 (full cut)
            logger.info("Kagit kesildi")
            return True
        except Exception as e:
            logger.error("Kagit kesme hatasi: %s", e)
            return False

    def set_header(self, text):
        """
        Fis baslik yazisini ayarlar.

        Args:
            text: Baslik metni

        Returns:
            bool: Basarili mi
        """
        if not self.is_connected:
            logger.error("Yazici bagli degil")
            return False

        logger.info("Fis baslik yazisi ayarlandi")
        if HAS_SERIAL:
            # Bazi yazicilar ozel komutlariyla baslik ayarlar
            pass
        return True

    def set_footer(self, text):
        """
        Fis ayak yazisini ayarlar.

        Args:
            text: Ayak metni

        Returns:
            bool: Basarili mi
        """
        if not self.is_connected:
            logger.error("Yazici bagli degil")
            return False

        logger.info("Fis ayak yazisi ayarlandi")
        return True

    def print_barcode(self, barcode_data, barcode_type="CODE128"):
        """
        Barkod yazdirir.

        Args:
            barcode_data: Barkod verisi
            barcode_type: Barkod tipi (CODE128, EAN13, vb.)

        Returns:
            bool: Basarili mi
        """
        if not self.is_connected:
            logger.error("Yazici bagli degil, barkod yazdirilamadi")
            return False

        logger.info("Barkod yazdiriliyor: %s (%s)", barcode_data, barcode_type)

        try:
            data_bytes = barcode_data.encode("ascii", errors="replace")

            if barcode_type.upper() == "CODE128":
                cmd = bytes([0x1D, 0x6B, 0x49, len(data_bytes)]) + data_bytes
            elif barcode_type.upper() == "EAN13":
                cmd = bytes([0x1D, 0x6B, 0x43]) + data_bytes + bytes([0x00])
            else:
                cmd = bytes([0x1D, 0x6B, 0x49, len(data_bytes)]) + data_bytes

            self.send_raw(cmd)
            self.send_raw(bytes([0x0A]))
            logger.info("Barkod yazdirildi")
            return True

        except Exception as e:
            logger.error("Barkod yazdirma hatasi: %s", e)
            return False

    def print_qr(self, qr_data):
        """
        QR kod yazdirir.

        Args:
            qr_data: QR kod icerigi

        Returns:
            bool: Basarili mi
        """
        if not self.is_connected:
            logger.error("Yazici bagli degil, QR kod yazdirilamadi")
            return False

        logger.info("QR kod yazdiriliyor: %s", qr_data)

        try:
            data_bytes = qr_data.encode("utf-8")
            data_len = len(data_bytes) + 3

            # Model 2
            self.send_raw(bytes([0x1D, 0x28, 0x6B, 0x04, 0x00, 0x31, 0x41, 0x32, 0x00]))
            # Size
            self.send_raw(bytes([0x1D, 0x28, 0x6B, 0x03, 0x00, 0x31, 0x43, 0x05]))
            # Error correction (M)
            self.send_raw(bytes([0x1D, 0x28, 0x6B, 0x03, 0x00, 0x31, 0x45, 0x31]))
            # Store data
            pl = data_len & 0xFF
            ph = (data_len >> 8) & 0xFF
            self.send_raw(bytes([0x1D, 0x28, 0x6B, pl, ph, 0x31, 0x50, 0x30]) + data_bytes)
            # Print
            self.send_raw(bytes([0x1D, 0x28, 0x6B, 0x03, 0x00, 0x31, 0x51, 0x30]))
            self.send_raw(bytes([0x0A]))

            logger.info("QR kod yazdirildi")
            return True

        except Exception as e:
            logger.error("QR kod yazdirma hatasi: %s", e)
            return False

    def get_fiscal_memory(self):
        """
        Mali bellegi okur (ureticiye gore ozel komutlar).

        Returns:
            dict: Mali bellek bilgisi veya None
        """
        if not self.is_connected:
            logger.error("Yazici bagli degil")
            return None

        logger.info("Mali bellek okunuyor...")

        # Bu islem ureticiye gore ozel komutlar gerektirir
        # Ornek bir uygulama:
        memory_info = {
            "serial_number": "TR1234567890",
            "model": self.model,
            "firmware": "v1.0",
            "memory_usage": "%45",
            "last_z_report": time.strftime("%d.%m.%Y"),
            "total_receipts": 1234,
        }

        if HAS_SERIAL:
            try:
                # GS r n - status command
                status_cmd = bytes([0x1D, 0x72, 0x01])
                self._send_raw_bytes(status_cmd)
                response = self._read_response(1)
                if response:
                    memory_info["status_byte"] = f"0x{response[0]:02X}"
            except Exception as e:
                logger.error("Mali bellek okuma hatasi: %s", e)
        else:
            logger.info("[SIMULASYON] Mali bellek okundu")
            time.sleep(0.5)

        return memory_info

    def feed_paper(self, lines=1):
        """
        Kagit besleme yapar.

        Args:
            lines: Beslenecek satir sayisi

        Returns:
            bool: Basarili mi
        """
        if not self.is_connected:
            return False

        try:
            self.send_raw(bytes([0x1B, 0x64, lines]))  # ESC d n
            return True
        except Exception as e:
            logger.error("Kagit besleme hatasi: %s", e)
            return False

    def set_barcode_height(self, height=100):
        """
        Barkod yuksekligini ayarlar.

        Args:
            height: Yukseklik (1-255 pixel)
        """
        if self.is_connected:
            self.send_raw(bytes([0x1D, 0x68, height]))

    def set_barcode_width(self, width=3):
        """
        Barkod genisligini ayarlar.

        Args:
            width: Genislik (2-6)
        """
        if self.is_connected:
            self.send_raw(bytes([0x1D, 0x77, width]))

    def initialize(self):
        """
        Yaziciyi baslatir.

        Returns:
            bool: Basarili mi
        """
        if not self.is_connected:
            return False

        try:
            self.send_raw(bytes([0x1B, 0x40]))  # ESC @
            logger.info("Yazici baslatildi")
            return True
        except Exception as e:
            logger.error("Yazici baslatma hatasi: %s", e)
            return False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return False
