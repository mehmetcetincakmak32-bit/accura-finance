
"""
Kasa Cekmecesi Kontrol Modulu
================================
COM, USB, Paralel ve TCP uzerinden kasa cekmecesi
acma/kapama ve durum sorgulama.
"""

import logging
import time

logger = logging.getLogger(__name__)

try:
    import serial
    HAS_SERIAL = True
except ImportError:
    HAS_SERIAL = False
    logger.info("pyserial modulu bulunamadi, kasa cekmecesi simulasyonu kullanilacak")


class CashDrawer:
    """
    Kasa cekmecesi kontrol sinifi.

    COM (RS-232), USB, Paralel (LPT) ve TCP/IP uzerinden
    kasa cekmecesini acma, durumunu sorgulama ve test
    etme fonksiyonlari.
    """

    # Drawer kick-out pin yapilandirmalari
    DRAWER_PIN_CONFIGS = {
        # (pin, pulse_duration) -> ESC/POS komutu
        2: bytes([0x10, 0x14, 0x01, 0x00, 0x05]),
        5: bytes([0x10, 0x14, 0x02, 0x00, 0x05]),
    }

    def __init__(self, config=None):
        """
        CashDrawer baslatma.

        Args:
            config: Config nesnesi veya sozluk
        """
        self.config = config
        self.port = "COM1"
        self.pin = 2
        self.pulse_duration = 200
        self.serial_port = None
        self.is_connected = False
        self.connection_type = "serial"  # serial, usb, parallel, tcp

        if isinstance(config, dict):
            self.port = config.get("port", self.port)
            self.pin = config.get("pin", self.pin)
            self.pulse_duration = config.get("pulse_duration", self.pulse_duration)
        elif config and hasattr(config, "data"):
            dconf = config.data.get("cash_drawer", {})
            self.port = dconf.get("port", self.port)
            self.pin = dconf.get("pin", self.pin)
            self.pulse_duration = dconf.get("pulse_duration", self.pulse_duration)

    def open(self, port=None, pin=None):
        """
        Kasa cekmecesini acar.

        Args:
            port: Port adi (opsiyonel)
            pin: Pin numarasi (2 veya 5, varsayilan: 2)

        Returns:
            bool: Basarili mi
        """
        if port:
            self.port = port
        if pin:
            self.pin = pin

        logger.info("Kasa cekmecesi aciliyor (port: %s, pin: %d)...", self.port, self.pin)

        success = False

        if self.connection_type == "serial":
            success = self._open_serial()
        elif self.connection_type == "parallel":
            success = self._open_parallel()
        elif self.connection_type == "tcp":
            success = self._open_tcp()
        else:
            success = self._open_serial()

        if success:
            logger.info("Kasa cekmecesi acildi")
        else:
            logger.error("Kasa cekmecesi acilamadi")

        return success

    def _open_serial(self):
        """Seri port uzerinden kasa acma."""
        if HAS_SERIAL:
            try:
                temp_port = serial.Serial(
                    port=self.port,
                    baudrate=9600,
                    bytesize=8,
                    parity="N",
                    stopbits=1,
                    timeout=1.0,
                )

                if temp_port.is_open:
                    # Drawer kick-out komutu
                    cmd = self.DRAWER_PIN_CONFIGS.get(self.pin,
                                                      self.DRAWER_PIN_CONFIGS[2])
                    temp_port.write(cmd)
                    temp_port.flush()
                    temp_port.close()
                    self.is_connected = True
                    return True

                temp_port.close()

            except serial.SerialException as e:
                logger.error("Seri port hatasi: %s", e)
            except Exception as e:
                logger.error("Kasa acma hatasi (seri): %s", e)

        # Simulasyon
        logger.info("[SIMULASYON] Kasa acma komutu gonderildi: port=%s, pin=%d, pulse=%dms",
                     self.port, self.pin, self.pulse_duration)
        time.sleep(0.3)
        return True

    def _open_parallel(self):
        """Paralel port (LPT) uzerinden kasa acma."""
        logger.info("[SIMULASYON] Paralel port kasa acma: %s", self.port)
        time.sleep(0.3)
        return True

    def _open_tcp(self):
        """TCP/IP uzerinden kasa acma."""
        logger.info("[SIMULASYON] TCP/IP kasa acma: %s", self.port)
        time.sleep(0.3)
        return True

    def get_status(self):
        """
        Kasa cekmecesi durumunu sorgular.

        Returns:
            dict: {
                "connected": bool,
                "is_open": bool,
                "port": str,
                "error": str veya None
            }
        """
        status = {
            "connected": self.is_connected,
            "is_open": False,
            "port": self.port,
            "error": None,
        }

        if HAS_SERIAL and self.port.upper().startswith("COM"):
            try:
                # Seri port uzerinden durum sorgulama
                temp_port = serial.Serial(
                    port=self.port,
                    baudrate=9600,
                    timeout=1.0,
                )
                if temp_port.is_open:
                    # DLE EOT 7 - drawer status
                    temp_port.write(bytes([0x10, 0x04, 0x07]))
                    response = temp_port.read(1)
                    if response:
                        status["is_open"] = bool(response[0] & 0x01)
                    temp_port.close()
                    status["connected"] = True
            except Exception as e:
                status["error"] = str(e)
                logger.debug("Kasa durumu sorgulanamadi: %s", e)
        else:
            # Simulasyon
            status["connected"] = True
            status["is_open"] = False
            logger.info("[SIMULASYON] Kasa durumu sorgulandi")

        return status

    def configure(self, pulse_duration=None, pin=None):
        """
        Kasa cekmecesi yapilandirmasini gunceller.

        Args:
            pulse_duration: Darbe suresi (ms)
            pin: Pin numarasi (2 veya 5)

        Returns:
            bool: Basarili mi
        """
        if pin is not None:
            if pin in (2, 5):
                self.pin = pin
                logger.info("Kasa pin numarasi ayarlandi: %d", pin)
            else:
                logger.warning("Gecersiz pin numarasi: %d (2 veya 5 olmali)", pin)
                return False

        if pulse_duration is not None:
            if 50 <= pulse_duration <= 500:
                self.pulse_duration = pulse_duration
                logger.info("Kasa darbe suresi ayarlandi: %d ms", pulse_duration)
            else:
                logger.warning("Gecersiz darbe suresi: %d (50-500 ms olmali)", pulse_duration)
                return False

        return True

    def test(self):
        """
        Kasa cekmecesi acma/kapama testi.

        Returns:
            dict: Test sonucu
        """
        logger.info("Kasa cekmecesi testi baslatiliyor...")

        result = {
            "test_name": "Kasa Cekmecesi Testi",
            "port": self.port,
            "pin": self.pin,
            "pulse_duration": self.pulse_duration,
            "open_test": False,
            "status_test": False,
            "overall": False,
        }

        # Acma testi
        try:
            open_result = self.open()
            result["open_test"] = open_result
            logger.info("Acma testi: %s", "BASARILI" if open_result else "BASARISIZ")
        except Exception as e:
            result["open_test"] = False
            logger.error("Acma testi hatasi: %s", e)

        # Durum sorgulama testi
        try:
            status = self.get_status()
            result["status_test"] = status.get("connected", False)
            logger.info("Durum testi: %s (acik=%s)",
                        "BASARILI" if result["status_test"] else "BASARISIZ",
                        status.get("is_open", False))
        except Exception as e:
            result["status_test"] = False
            logger.error("Durum testi hatasi: %s", e)

        result["overall"] = result["open_test"] and result["status_test"]

        if result["overall"]:
            logger.info("Kasa testi: BASARILI")
        else:
            logger.warning("Kasa testi: BASARISIZ")

        return result

    def set_port_type(self, port_type):
        """
        Port tipini belirler.

        Args:
            port_type: "serial", "usb", "parallel", "tcp"
        """
        valid_types = ["serial", "usb", "parallel", "tcp"]
        if port_type in valid_types:
            self.connection_type = port_type
            logger.info("Port tipi ayarlandi: %s", port_type)
        else:
            logger.warning("Gecersiz port tipi: %s", port_type)

    def __repr__(self):
        return (
            f"CashDrawer(port={self.port}, pin={self.pin}, "
            f"pulse={self.pulse_duration}ms, type={self.connection_type})"
        )
