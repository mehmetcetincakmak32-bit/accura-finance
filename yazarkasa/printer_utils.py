
"""
Yazici Yardimci Fonksiyonlari
===============================
Port tarama, yazici tespiti, Turkce karakter donusumu
ve cesitli yardimci fonksiyonlar.
"""

import logging
import re

logger = logging.getLogger(__name__)

# pyserial kontrolu
try:
    import serial.tools.list_ports as list_ports
    HAS_PYSERIAL = True
except ImportError:
    HAS_PYSERIAL = False
    logger.info("pyserial modulu bulunamadi, port listesi simulasyonu kullanilacak")


class PrinterUtils:
    """
    Yazici yardimci fonksiyonlar sinifi.
    Port tarama, yazici tespiti ve kod donusum islemleri.
    """

    # Turkce karakter donusum tablosu (CP857 icin)
    TURKISH_TO_CP857 = {
        "c": "c", "C": "C",
        "g": "g", "G": "G",
        "i": "i", "I": "I",
        "o": "o", "O": "O",
        "s": "s", "S": "S",
        "u": "u", "U": "U",
    }

    CP857_MAP = {
        0x00E7: 0x87,  # c
        0x00C7: 0x80,  # C
        0x011F: 0x9D,  # g
        0x011E: 0x8D,  # G
        0x0131: 0x86,  # i (dotless i)
        0x0130: 0x8E,  # I (dotted I)
        0x00F6: 0x94,  # o
        0x00D6: 0x99,  # O
        0x015F: 0x9E,  # s
        0x015E: 0x8A,  # S
        0x00FC: 0x81,  # u
        0x00DC: 0x9A,  # U
    }

    @staticmethod
    def list_available_ports():
        """
        Mevcut COM portlarini listeler.

        Returns:
            list: (port_adi, aciklama, donanim_id) seklinde tuple listesi
        """
        ports = []

        if HAS_PYSERIAL:
            try:
                for port in list_ports.comports():
                    ports.append((port.device, port.description, port.hwid))
            except Exception as e:
                logger.error("Port listeleme hatasi: %s", e)

        if not ports:
            ports = [
                ("COM1", "Seri Port 1 (Varsayilan)", ""),
                ("COM2", "Seri Port 2", ""),
                ("COM3", "Seri Port 3", ""),
                ("COM4", "Seri Port 4", ""),
                ("LPT1", "Paralel Port", ""),
                ("USB001", "USB Yazici", ""),
            ]
            logger.info("Simule port listesi kullaniliyor")

        return ports

    @staticmethod
    def list_usb_printers():
        """
        USB uzerinden bagli yazicilari listeler.

        Returns:
            list: (port, model, vid_pid) seklinde tuple listesi
        """
        usb_printers = []

        if HAS_PYSERIAL:
            try:
                for port in list_ports.comports():
                    if "USB" in port.description or "VID_" in port.hwid:
                        vid_pid = ""
                        # VID/PID bilgisini cikar
                        match = re.search(r"VID_([0-9A-F]+).*PID_([0-9A-F]+)", port.hwid, re.I)
                        if match:
                            vid_pid = f"{match.group(1)}:{match.group(2)}"
                        usb_printers.append((port.device, port.description, vid_pid))
            except Exception as e:
                logger.error("USB yazici listeleme hatasi: %s", e)

        if not usb_printers:
            usb_printers = [
                ("USB001", "USB Printing Support", "04B8:0202"),
                ("COM5", "USB Seri Port (Yazici)", "067B:2303"),
            ]
            logger.info("Simule USB yazici listesi kullaniliyor")

        return usb_printers

    @staticmethod
    def detect_printer(port=None):
        """
        Bagli yazicinin markasini/modelini otomatik tespit eder.

        Args:
            port: Test edilecek port (None = tum portlar)

        Returns:
            str: Tespit edilen yazici modeli veya "unknown"
        """
        logger.info("Yazici tespiti baslatiliyor...")

        if port:
            test_ports = [port]
        else:
            raw_ports = PrinterUtils.list_available_ports()
            test_ports = [p[0] for p in raw_ports]

        for p in test_ports:
            result = PrinterUtils.test_printer(p)
            if result["connected"]:
                model = result.get("model", "unknown")
                logger.info("Yazici tespit edildi: %s - %s", p, model)
                return model

        logger.info("Yazici tespit edilemedi, varsayilan kullanilacak")
        return "unknown"

    @staticmethod
    def test_printer(port):
        """
        Belirtilen porttaki yazici baglantisini test eder.

        Args:
            port: Test edilecek port adi

        Returns:
            dict: {
                "connected": bool,
                "port": str,
                "model": str,
                "error": str veya None
            }
        """
        result = {
            "connected": False,
            "port": port,
            "model": "unknown",
            "error": None,
        }

        try:
            import serial

            ser = serial.Serial(
                port=port,
                baudrate=9600,
                bytesize=8,
                parity="N",
                stopbits=1,
                timeout=2.0,
            )

            if ser.is_open:
                # Status sorgulama komutu (ESC/POS)
                status_cmd = bytes([0x10, 0x04, 0x01])
                try:
                    ser.write(status_cmd)
                    response = ser.read(1)
                    if response:
                        result["connected"] = True
                        result["model"] = PrinterUtils._identify_printer(response)
                except Exception:
                    result["connected"] = True
                    result["model"] = "generic_serial"

                ser.close()

        except (ImportError, serial.SerialException) as e:
            result["error"] = str(e)
            logger.debug("Port test edilemedi %s: %s", port, e)

        # Simulasyon: COM1 her zaman basarili
        if not result["connected"] and port.upper() in ("COM1", "LPT1"):
            result["connected"] = True
            result["model"] = "Epson (Simulated)"

        logger.info("Port test: %s -> baglanti=%s, model=%s",
                     port, result["connected"], result["model"])

        return result

    @staticmethod
    def _identify_printer(response_data):
        """
        Yanit verisine gore yazici modelini belirler.

        Args:
            response_data: Yazicidan gelen ham yanit

        Returns:
            str: Model adi
        """
        if not response_data:
            return "unknown"

        byte_val = response_data[0] if isinstance(response_data, (bytes, bytearray)) else ord(response_data)

        if byte_val == 0x00:
            return "Epson (Normal)"
        elif byte_val == 0x01:
            return "Epson (Mekanik Hata)"
        elif byte_val == 0x02:
            return "Star Micronics"
        elif byte_val == 0x03:
            return "Bixolon"
        else:
            return f"Generic (0x{byte_val:02X})"

    @staticmethod
    def format_turkish(text, encoding="cp857"):
        """
        Turkce karakterleri yazici kodlamasina uygun sekilde donusturur.

        Args:
            text: Donusturulecek metin
            encoding: Hedef kodlama ("cp857", "cp1254", "iso88599", "utf8")

        Returns:
            bytes: Kodlanmis bayt dizisi
        """
        if not text:
            return b""

        encodings = {
            "cp857": "cp857",
            "cp1254": "cp1254",
            "iso88599": "iso-8859-9",
            "utf8": "utf-8",
        }

        target = encodings.get(encoding, "utf-8")

        try:
            return text.encode(target)
        except (UnicodeEncodeError, UnicodeDecodeError):
            logger.warning("Turkce karakter donusum hatasi, UTF-8 kullaniliyor")
            return text.encode("utf-8", errors="replace")

    @staticmethod
    def turkish_to_ascii(text):
        """
        Turkce karakterleri ASCII esdegerlerine donusturur.

        Args:
            text: Donusturulecek metin

        Returns:
            str: ASCII donusumlu metin
        """
        replacements = {
            "c": "c", "C": "C",
            "g": "g", "G": "G",
            "i": "i", "I": "I",
            "o": "o", "O": "O",
            "s": "s", "S": "S",
            "u": "u", "U": "U",
        }

        result = ""
        for char in text:
            result += replacements.get(char, char)

        return result

    @staticmethod
    def calculate_checksum(data):
        """
        Veri uzerinde basit XOR saglama toplami hesaplar.

        Args:
            data: bytes veya bytearray

        Returns:
            int: XOR checksum degeri
        """
        if isinstance(data, str):
            data = data.encode("utf-8")

        checksum = 0
        for byte in data:
            checksum ^= byte

        return checksum

    @staticmethod
    def byte_to_hex(data, separator=" "):
        """
        Bayt dizisini okunabilir hexadecimal metne cevirir.

        Args:
            data: bytes veya bytearray
            separator: Baytlar arasi ayrac

        Returns:
            str: Orn: "1B 40 1B 69"
        """
        if isinstance(data, str):
            data = data.encode("utf-8")

        return separator.join(f"{b:02X}" for b in data)

    @staticmethod
    def calculate_crc16(data):
        """
        CRC-16/IBM saglama toplami hesaplar.

        Args:
            data: bytes

        Returns:
            int: CRC-16 degeri
        """
        if isinstance(data, str):
            data = data.encode("utf-8")

        crc = 0x0000
        polynomial = 0xA001

        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = ((crc >> 1) ^ polynomial) & 0xFFFF
                else:
                    crc = (crc >> 1) & 0xFFFF

        return crc

    @staticmethod
    def pad_center(text, width=42, fill_char=" "):
        """Metni ortalar."""
        if len(text) >= width:
            return text[:width]
        left = (width - len(text)) // 2
        return fill_char * left + text + fill_char * (width - len(text) - left)

    @staticmethod
    def pad_right(text, width=42, fill_char=" "):
        """Metni saga yaslar."""
        if len(text) >= width:
            return text[:width]
        return fill_char * (width - len(text)) + text

    @staticmethod
    def pad_left(text, width=42, fill_char=" "):
        """Metni sola yaslar."""
        if len(text) >= width:
            return text[:width]
        return text + fill_char * (width - len(text))
