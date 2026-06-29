
"""
Musteri Ekrani Kontrol Modulu
================================
LCD/VFD musteri ekrani iletisimi. CD5220, Epson, Bixolon,
POS-X ve AIPHA protokollerini destekler.
"""

import logging
import time

logger = logging.getLogger(__name__)

try:
    import serial
    HAS_SERIAL = True
except ImportError:
    HAS_SERIAL = False
    logger.info("pyserial modulu bulunamadi, musteri ekrani simulasyonu kullanilacak")


class CustomerDisplay:
    """
    Musteri ekrani (LCD/VFD) kontrol sinifi.

    2x20, 2x16 LCD ve VFD ekranlari destekler.
    CD5220, Epson, Bixolon, POS-X protokolleri.
    """

    # Display kontrol komutlari
    CLEAR_DISPLAY = 0x01
    CURSOR_HOME = 0x02
    CURSOR_BACK = 0x08
    DISPLAY_ON = 0x0C
    DISPLAY_OFF = 0x0E

    def __init__(self, config=None):
        """
        CustomerDisplay baslatma.

        Args:
            config: Config nesnesi veya sozluk
        """
        self.config = config
        self.serial_port = None
        self.is_connected = False
        self.model = "CD5220"
        self.port = "COM2"
        self.baudrate = 9600
        self.columns = 20
        self.rows = 2
        self.brightness = 5

        if isinstance(config, dict):
            self.port = config.get("port", self.port)
            self.baudrate = config.get("baudrate", self.baudrate)
            self.model = config.get("model", self.model)
            self.columns = config.get("columns", self.columns)
            self.rows = config.get("rows", self.rows)
        elif config and hasattr(config, "data"):
            dconf = config.data.get("customer_display", {})
            self.port = dconf.get("port", self.port)
            self.baudrate = dconf.get("baudrate", self.baudrate)
            self.model = dconf.get("model", self.model)
            self.columns = dconf.get("columns", self.columns)
            self.rows = dconf.get("rows", self.rows)

    def connect(self, port=None, baudrate=None):
        """
        Musteri ekranina baglanir.

        Args:
            port: COM portu
            baudrate: Baud hizi

        Returns:
            bool: Basarili mi
        """
        if port:
            self.port = port
        if baudrate:
            self.baudrate = baudrate

        if self.is_connected:
            logger.warning("Musteri ekrani zaten bagli: %s", self.port)
            return True

        if HAS_SERIAL:
            try:
                self.serial_port = serial.Serial(
                    port=self.port,
                    baudrate=self.baudrate,
                    bytesize=8,
                    parity="N",
                    stopbits=1,
                    timeout=2.0,
                )
                self.is_connected = self.serial_port.is_open
                if self.is_connected:
                    logger.info("Musteri ekranina baglanildi: %s (%s, %dx%d)",
                                self.port, self.model, self.columns, self.rows)
                    self._initialize_display()
            except Exception as e:
                logger.error("Musteri ekrani baglanti hatasi (%s): %s", self.port, e)
                self.is_connected = False
        else:
            logger.info("[SIMULASYON] Musteri ekrani baglantisi: %s (%s)",
                        self.port, self.model)
            self.is_connected = True
            time.sleep(0.1)

        return self.is_connected

    def disconnect(self):
        """
        Musteri ekrani baglantisini kapatir.

        Returns:
            bool: Basarili mi
        """
        if not self.is_connected:
            return True

        self.clear()

        if HAS_SERIAL and self.serial_port:
            try:
                self.serial_port.close()
                logger.info("Musteri ekrani baglantisi kapatildi: %s", self.port)
            except Exception as e:
                logger.error("Musteri ekrani kapatma hatasi: %s", e)
                return False
        else:
            logger.info("[SIMULASYON] Musteri ekrani baglantisi kapatildi: %s", self.port)

        self.is_connected = False
        self.serial_port = None
        return True

    def _send_command(self, command):
        """Ekrana komut gonderir."""
        if HAS_SERIAL and self.serial_port and self.is_connected:
            try:
                self.serial_port.write(command)
                self.serial_port.flush()
                logger.debug("Ekran komutu: %s", command.hex())
            except Exception as e:
                logger.error("Ekran komut hatasi: %s", e)
        else:
            logger.info("[SIMULASYON] Ekran komutu: %s", command.hex())

    def _initialize_display(self):
        """Ekrani baslatir."""
        if self.model == "CD5220":
            # CD5220 baslatma
            self._send_command(bytes([0x0C]))  # Form feed
            time.sleep(0.05)
            self._send_command(bytes([0x0E]))  # Display on
        elif self.model == "Epson":
            self._send_command(bytes([self.DISPLAY_ON]))
        elif self.model == "Bixolon":
            self._send_command(bytes([0x1B, 0x40]))  # Reset
            time.sleep(0.05)
            self._send_command(bytes([0x1B, 0x53, 0x01]))  # DMD on
        else:
            self._send_command(bytes([self.CLEAR_DISPLAY]))

        time.sleep(0.05)
        logger.info("Musteri ekrani baslatildi: %s", self.model)

    def _set_cursor_position(self, row=0, col=0):
        """
        Imlec pozisyonunu ayarlar.

        Args:
            row: Satir (0-1)
            col: Sutun (0-19)
        """
        if self.model == "CD5220":
            # ESC = row col
            self._send_command(bytes([0x1B, 0x3D, row + 1, col + 1]))
        elif self.model == "Epson":
            # ESC [ row col H
            self._send_command(bytes([0x1B, 0x5B, row + 1, 0x3B, col + 1, 0x48]))
        elif self.model == "Bixolon":
            self._send_command(bytes([0x1B, 0x24, col, row]))
        else:
            # ESC = row col (generic CD5220)
            self._send_command(bytes([0x1B, 0x3D, row + 1, col + 1]))

    def show_text(self, line1="", line2="", align="center"):
        """
        Ekrana iki satir metin gosterir.

        Args:
            line1: 1. satir metni
            line2: 2. satir metni
            align: Hizalama ("left", "center", "right")

        Returns:
            bool: Basarili mi
        """
        if not self.is_connected:
            logger.error("Musteri ekrani bagli degil")
            return False

        logger.info("Ekran: '%s' / '%s' (hiza: %s)", line1, line2, align)

        # Metinleri sutun genisligine gore duzenle
        def align_text(text, width, align_mode):
            if len(text) >= width:
                return text[:width]
            if align_mode == "center":
                left = (width - len(text)) // 2
                return " " * left + text
            elif align_mode == "right":
                return " " * (width - len(text)) + text
            else:
                return text + " " * (width - len(text))

        line1 = align_text(self._sanitize(line1), self.columns, align)
        line2 = align_text(self._sanitize(line2), self.columns, align)

        self.clear()

        # 1. satir
        self._set_cursor_position(0, 0)
        self._send_command(line1.encode("cp857", errors="replace"))

        # 2. satir
        if self.rows >= 2:
            self._set_cursor_position(1, 0)
            self._send_command(line2.encode("cp857", errors="replace"))

        return True

    def _sanitize(self, text):
        """Ekran icin metni temizler (ozel karakterleri kaldirir)."""
        clean = ""
        for char in text:
            if ord(char) >= 32 and ord(char) <= 126 or ord(char) > 127:
                clean += char
            elif char in "\n\r\t":
                clean += " "
        return clean

    def show_price(self, amount):
        """
        Ekrana buyuk boyutta fiyat gosterir.

        Args:
            amount: Gosterilecek tutar

        Returns:
            bool: Basarili mi
        """
        if not self.is_connected:
            return False

        price_str = f"{float(amount):.2f} TL"
        logger.info("Fiyat gosteriliyor: %s", price_str)

        if self.columns >= 20:
            line1 = " " * 7 + "TOPLAM"
            line2 = " " * 4 + price_str
        else:
            line1 = "TOPLAM"
            line2 = price_str

        return self.show_text(line1, line2, align="center")

    def show_thank_you(self):
        """
        Tesekkur mesaji gosterir.

        Returns:
            bool: Basarili mi
        """
        if not self.is_connected:
            return False

        if self.columns >= 20:
            return self.show_text(
                "TESFEKKUR EDERIZ",
                "IYI GUNLER",
                align="center"
            )
        else:
            return self.show_text("TESFEKKURLER", "IYI GUNLER", align="center")

    def show_welcome(self):
        """
        Hos geldiniz mesaji gosterir.

        Returns:
            bool: Basarili mi
        """
        if not self.is_connected:
            return False

        return self.show_text("HOS GELDINIZ", "ALISVERISINIZ", align="center")

    def clear(self):
        """Ekrani temizler."""
        if not self.is_connected:
            return False

        self._send_command(bytes([self.CLEAR_DISPLAY]))
        time.sleep(0.05)
        logger.debug("Ekran temizlendi")
        return True

    def set_brightness(self, level):
        """
        Ekran parlakligini ayarlar (1-10).

        Args:
            level: Parlaklik seviyesi (1-10)

        Returns:
            bool: Basarili mi
        """
        if not self.is_connected:
            return False

        if level < 1:
            level = 1
        elif level > 10:
            level = 10

        self.brightness = level

        if self.model == "CD5220":
            brightness_byte = 0x80 + (level - 1)
            self._send_command(bytes([0x1B, 0x42, brightness_byte]))
            logger.info("Ekran parlakligi ayarlandi: %d", level)
            return True
        elif self.model == "Epson":
            self._send_command(bytes([0x1B, 0x64, level]))
            logger.info("Ekran parlakligi ayarlandi: %d", level)
            return True
        elif self.model == "Bixolon":
            # Bixolon: ESC * n (n=0-7)
            bixolon_level = min(level // 2, 7)
            self._send_command(bytes([0x1B, 0x2A, bixolon_level]))
            logger.info("Ekran parlakligi ayarlandi: %d", bixolon_level)
            return True
        else:
            logger.info("[SIMULASYON] Ekran parlakligi ayarlandi: %d", level)
            return True

    def scroll_text(self, text, speed=3):
        """
        Ekranda metin kaydirma.

        Args:
            text: Kaydirilacak metin
            speed: Hiz (1-5, 1 en yavas)

        Returns:
            bool: Basarili mi
        """
        if not self.is_connected:
            return False

        logger.info("Metin kaydirma: '%s' (hiz: %d)", text, speed)

        padded = text + " " * self.columns
        delay = max(0.1, 0.5 - (speed - 1) * 0.1)

        try:
            for i in range(len(padded) - self.columns + 1):
                segment = padded[i:i + self.columns]
                self._set_cursor_position(0, 0)
                self._send_command(segment.encode("cp857", errors="replace"))
                time.sleep(delay)
            return True
        except Exception as e:
            logger.error("Metin kaydirma hatasi: %s", e)
            return False

    def show_animation(self, animation_type="wave"):
        """
        Basit animasyon gosterir.

        Args:
            animation_type: "wave", "blink", "marquee"
        """
        if not self.is_connected:
            return

        if animation_type == "wave":
            chars = ["-", "\\", "|", "/"]
            for _ in range(4):
                for c in chars:
                    self._set_cursor_position(0, self.columns - 1)
                    self._send_command(c.encode())
                    time.sleep(0.1)
        elif animation_type == "blink":
            for _ in range(3):
                self.show_text("     ***     ", "  ODEME  ", align="center")
                time.sleep(0.3)
                self.clear()
                time.sleep(0.2)

    def test(self):
        """
        Musteri ekrani testini calistirir.

        Returns:
            dict: Test sonucu
        """
        logger.info("Musteri ekrani testi baslatiliyor...")

        result = {
            "test_name": "Musteri Ekrani Testi",
            "model": self.model,
            "port": self.port,
            "connect_test": False,
            "display_test": False,
            "clear_test": False,
            "brightness_test": False,
            "overall": False,
        }

        # Baglanti testi
        result["connect_test"] = self.connect()
        if not result["connect_test"]:
            result["overall"] = False
            return result

        # Gosterim testi
        try:
            result["display_test"] = self.show_welcome()
            time.sleep(0.5)
        except Exception as e:
            logger.error("Gosterim testi hatasi: %s", e)

        # Parlaklik testi
        try:
            result["brightness_test"] = self.set_brightness(8)
        except Exception as e:
            logger.error("Parlaklik testi hatasi: %s", e)

        # Temizleme testi
        try:
            time.sleep(0.3)
            result["clear_test"] = self.clear()
        except Exception as e:
            logger.error("Temizleme testi hatasi: %s", e)

        result["overall"] = (result["connect_test"] and result["display_test"]
                             and result["clear_test"])

        logger.info("Musteri ekrani testi: %s",
                    "BASARILI" if result["overall"] else "BASARISIZ")

        return result

    def __repr__(self):
        return (
            f"CustomerDisplay(model={self.model}, port={self.port}, "
            f"{self.columns}x{self.rows}, brightness={self.brightness})"
        )
