
"""
Yazarkasa - Ana Uygulama
===========================
Basit CLI menu ile tum cevre birimlerini test etme,
fis yazdirma, kasa acma ve barkod okutma islemleri.
"""

import logging
import sys
import time

from yazarkasa.config import Config
from yazarkasa.fiscal_printer import FiscalPrinter
from yazarkasa.receipt_builder import ReceiptBuilder
from yazarkasa.cash_drawer import CashDrawer
from yazarkasa.customer_display import CustomerDisplay
from yazarkasa.barcode_scanner import BarcodeScanner
from yazarkasa.printer_utils import PrinterUtils

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("yazarkasa")


class YazarkasaApp:

    def __init__(self):
        self.config = Config()
        self.printer = FiscalPrinter(self.config)
        self.receipt_builder = ReceiptBuilder(self.config)
        self.drawer = CashDrawer(self.config)
        self.display = CustomerDisplay(self.config)
        self.scanner = BarcodeScanner(self.config)
        self.running = False

    def run(self):
        self.running = True
        self._show_banner()
        while self.running:
            try:
                self._show_menu()
                choice = input("\nSeciminiz: ").strip()
                if choice == "0":
                    self.running = False
                    print("\nYazarkasa kapatiliyor...")
                    self._cleanup()
                    print("Gule gule!")
                elif choice == "1":
                    self._test_receipt()
                elif choice == "2":
                    self._test_printer()
                elif choice == "3":
                    self._test_drawer()
                elif choice == "4":
                    self._test_display()
                elif choice == "5":
                    self._test_scanner()
                elif choice == "6":
                    self._show_config()
                elif choice == "7":
                    self._list_ports()
                elif choice == "8":
                    self._interactive_receipt()
                elif choice == "b":
                    self._test_barcode_print()
                elif choice == "x":
                    self._test_z_report()
                else:
                    print("Gecersiz secim!")
            except KeyboardInterrupt:
                print("\n\nKullanici tarafindan durduruldu.")
                self.running = False
                self._cleanup()
            except Exception as e:
                logger.error("Beklenmeyen hata: %s", e)
                print(f"\nHata: {e}")

    def _cleanup(self):
        if self.printer.is_connected:
            self.printer.disconnect()
        if self.display.is_connected:
            self.display.disconnect()
        if self.scanner.is_listening:
            self.scanner.stop_listening()

    def _show_banner(self):
        print("""
 ========================================
   ACCURA FINANCE - YAZARKASA SISTEMI
   Fis / Mali Yazici / Kasa / Ekran
   Surum 1.0.0
 ========================================
        """)

    def _show_menu(self):
        print("""
 --------------- ANA MENU ---------------
  1  - Test Fis Yazdir
  2  - Mali Yazici Testi
  3  - Kasa Cekmecesi Testi
  4  - Musteri Ekrani Testi
  5  - Barkod Okuyucu Testi
  6  - Yapilandirma Bilgisi
  7  - Portlari Listele
  8  - Interaktif Fis
  b  - Barkod/QR Yazdir
  x  - Z Raporu Yazdir
  0  - Cikis
 ----------------------------------------
        """)

    def _test_receipt(self):
        print("\n--- Test Fis Yazdirma ---\n")
        items = [
            ("Ekmek", 1, 5.00, 5.00),
            ("Sut 1L", 2, 32.50, 65.00),
            ("Yumurta 30'l", 1, 85.00, 85.00),
            ("Peynir 500g", 1, 120.00, 120.00),
            ("Zeytin 1kg", 1, 180.00, 180.00),
            ("Cay 500g", 1, 95.00, 95.00),
            ("Seker 5kg", 1, 75.00, 75.00),
        ]
        total = sum(item[3] for item in items)
        payment = 700.00
        change = payment - total
        merchant = {
            "name": "ACCURA MARKET",
            "tax_office": "KADIKOY VD",
            "tax_number": "1234567890",
            "address": "Bagdat Cad. No:123\nKadikoy / Istanbul",
            "phone": "0216 123 45 67",
        }
        print("Fis olusturuluyor...")
        receipt = self.receipt_builder.build_sale_receipt(
            items=items, total=total,
            payment={"method": "NAKIT", "amount": payment},
            change=change, merchant_info=merchant,
        )
        print("\n" + "=" * 42)
        print(receipt.get_text())
        print("=" * 42)
        print(f"\nYaziciya baglaniyor: {self.config.data['fiscal_printer']['port']}...")
        connected = self.printer.connect()
        if connected:
            print("Yaziciya baglanildi. Fis yazdiriliyor...")
            if self.printer.print_receipt(receipt):
                print("Fis basariyla yazdirildi!")
            else:
                print("Fis yazdirilamadi!")
            self.printer.disconnect()
        else:
            print("Yaziciya baglanilamadi. Fis sadece ekranda goruntulendi.")
        input("\nDevam etmek icin Enter'a basin...")

    def _test_printer(self):
        print("\n--- Mali Yazici Testi ---\n")
        pconf = self.config.data["fiscal_printer"]
        print(f"Port: {pconf['port']}")
        print(f"Hiz: {pconf['baudrate']} baud")
        print(f"Model: {self.printer.model}")
        print(f"\nBaglaniyor: {pconf['port']}...")
        connected = self.printer.connect()
        if connected:
            print("Baglanti BASARILI")
        else:
            print("Baglanti BASARISIZ (simulasyon modu)")
            self.printer.is_connected = True
        if self.printer.is_connected:
            print("\nYazici durumu sorgulaniyor...")
            status = self.printer.get_status()
            print(f"  Online: {status['online']}")
            print(f"  Kagit: {'VAR' if status['paper'] else 'YOK'}")
            print(f"  Kapi: {'ACIK' if status['cover_open'] else 'KAPALI'}")
            print(f"  Hata: {'VAR' if status['error'] else 'YOK'}")
            if status.get("error_description"):
                print(f"  Hata Aciklama: {status['error_description']}")
            print("\nKagit kesiliyor...")
            self.printer.cut_paper("partial")
            print("Kesme komutu gonderildi.")
            self.printer.disconnect()
            print("Baglanti kapatildi.")
        input("\nDevam etmek icin Enter'a basin...")

    def _test_drawer(self):
        print("\n--- Kasa Cekmecesi Testi ---\n")
        dconf = self.config.data["cash_drawer"]
        print(f"Port: {dconf['port']}")
        print(f"Pin: {dconf['pin']}")
        print(f"Darbe: {dconf['pulse_duration']}ms")
        print("\n1. Kasa Acma Testi")
        print("2. Kapsamli Test")
        secim = input("Seciminiz (1-2): ").strip()
        if secim == "2":
            result = self.drawer.test()
            print(f"\nTest Sonucu:")
            print(f"  Acma Testi: {'BASARILI' if result.get('open_test') else 'BASARISIZ'}")
            print(f"  Durum Testi: {'BASARILI' if result.get('status_test') else 'BASARISIZ'}")
            print(f"  Genel: {'BASARILI' if result.get('overall') else 'BASARISIZ'}")
        else:
            print("\nKasa aciliyor...")
            if self.drawer.open():
                print("Kasa acildi!")
            else:
                print("Kasa acilamadi!")
            status = self.drawer.get_status()
            print(f"\nKasa Durumu:")
            print(f"  Baglanti: {'VAR' if status.get('connected') else 'YOK'}")
            print(f"  Acik: {'EVET' if status.get('is_open') else 'HAYIR'}")
        input("\nDevam etmek icin Enter'a basin...")

    def _test_display(self):
        print("\n--- Musteri Ekrani Testi ---\n")
        dconf = self.config.data["customer_display"]
        print(f"Port: {dconf['port']}")
        print(f"Model: {self.display.model}")
        print(f"Ekran: {self.display.columns}x{self.display.rows}")
        print("\n1. Basit Test")
        print("2. Kapsamli Test")
        print("3. Fiyat Goster")
        print("4. Mesaj Goster (ozel)")
        secim = input("Seciminiz (1-4): ").strip()
        if secim == "2":
            result = self.display.test()
            print(f"\nTest Sonucu:")
            print(f"  Baglanti: {'BASARILI' if result.get('connect_test') else 'BASARISIZ'}")
            print(f"  Gosterim: {'BASARILI' if result.get('display_test') else 'BASARISIZ'}")
            print(f"  Genel: {'BASARILI' if result.get('overall') else 'BASARISIZ'}")
        elif secim == "3":
            amount = input("Gosterilecek tutar: ").strip()
            try:
                amount = float(amount)
                self.display.connect()
                self.display.show_price(amount)
                print(f"Ekranda '{amount:.2f} TL' gosteriliyor...")
                input("Devam etmek icin Enter'a basin...")
                self.display.show_thank_you()
                time.sleep(1)
                self.display.disconnect()
            except ValueError:
                print("Gecersiz tutar!")
        elif secim == "4":
            line1 = input("1. Satir: ").strip()
            line2 = input("2. Satir: ").strip()
            self.display.connect()
            self.display.show_text(line1, line2)
            print("Mesaj ekranda...")
            input("Devam etmek icin Enter'a basin...")
            self.display.disconnect()
        else:
            self.display.connect()
            self.display.show_welcome()
            print("Hos geldiniz mesaji gosteriliyor...")
            time.sleep(1.5)
            self.display.show_text("DENEME MESAJI", "TEST BASARILI", align="center")
            time.sleep(1.5)
            self.display.show_thank_you()
            time.sleep(1)
            self.display.disconnect()
            print("Test tamamlandi.")
        input("\nDevam etmek icin Enter'a basin...")

    def _test_scanner(self):
        print("\n--- Barkod Okuyucu Testi ---\n")
        sconf = self.config.data["barcode_scanner"]
        print(f"Port: {sconf['port']}")
        print(f"Hiz: {sconf['baudrate']} baud")
        print("\n1. Kapsamli Test")
        print("2. Simulasyon Testi")
        print("3. Barkod Parse Testi")
        secim = input("Seciminiz (1-3): ").strip()
        if secim == "3":
            print("\nBarkod parse testi:")
            test_data = input("Barkod verisi girin: ").strip()
            if test_data:
                parsed = self.scanner.parse_barcode(test_data)
                if parsed:
                    print(f"  Veri: {parsed['data']}")
                    print(f"  Tip: {parsed['type']}")
                else:
                    print("  Parse edilemedi!")
        elif secim == "2":
            print("\nSimulasyon modu (5 barkod okutulacak)...")
            test_barcodes = [
                "8691234567890", "CODE128TEST123",
                "9789751000000", "QR-TEST-MESAJI-12345", "12345678",
            ]
            self.scanner.start_listening()
            def on_barcode(data):
                print(f"  [OKUNDU] Tip: {data['type']}, Veri: {data['data']}")
            self.scanner.on_barcode(on_barcode)
            for bc in test_barcodes:
                print(f"  Simule ediliyor: {bc}")
                self.scanner.simulate_barcode(bc)
                time.sleep(0.3)
            self.scanner.stop_listening()
        else:
            print("\nKapsamli test calistiriliyor...")
            result = self.scanner.test(simulate=True)
            print(f"\nTest Sonucu:")
            print(f"  Baslatma: {'BASARILI' if result.get('start_test') else 'BASARISIZ'}")
            print(f"  Durdurma: {'BASARILI' if result.get('stop_test') else 'BASARISIZ'}")
            print(f"  Parse: {'BASARILI' if result.get('parse_test') else 'BASARISIZ'}")
            print(f"  Simulasyon: {'BASARILI' if result.get('simulate_test') else 'BASARISIZ'}")
            print(f"  Genel: {'BASARILI' if result.get('overall') else 'BASARISIZ'}")
        input("\nDevam etmek icin Enter'a basin...")

    def _show_config(self):
        print("\n--- Yapilandirma Bilgisi ---\n")
        sections = [
            ("Mali Yazici", self.config.data["fiscal_printer"]),
            ("Fis Yazici", self.config.data["receipt_printer"]),
            ("Kasa Cekmecesi", self.config.data["cash_drawer"]),
            ("Musteri Ekrani", self.config.data["customer_display"]),
            ("Barkod Okuyucu", self.config.data["barcode_scanner"]),
        ]
        for title, conf in sections:
            print(f"  [{title}]")
            for key, val in conf.items():
                print(f"    {key}: {val}")
            print()
        print(f"  Kodlama: {self.config.encoding_name}")
        print(f"  Satir Genisligi: {self.config.char_per_line}")
        print(f"\n  Satici Bilgisi:")
        for key, val in self.config.merchant_info.items():
            if val:
                val_str = str(val).replace("\n", " | ")
                print(f"    {key}: {val_str}")
        input("\nDevam etmek icin Enter'a basin...")

    def _list_ports(self):
        print("\n--- Kullanilabilir Portlar ---\n")
        print("Seri Portlar:")
        ports = PrinterUtils.list_available_ports()
        for port, desc, hwid in ports:
            print(f"  {port}: {desc}")
            if hwid:
                print(f"         {hwid}")
        print("\nUSB Yazicilar:")
        usb_printers = PrinterUtils.list_usb_printers()
        for port, model, vid_pid in usb_printers:
            print(f"  {port}: {model} ({vid_pid})")
        input("\nDevam etmek icin Enter'a basin...")

    def _interactive_receipt(self):
        print("\n--- Interaktif Fis Olusturma ---\n")
        print("Urunleri girin (bitirmek icin bos birakin):")
        items = []
        while True:
            name = input("  Urun adi: ").strip()
            if not name:
                break
            try:
                qty = float(input("  Miktar: ").strip() or "1")
                price = float(input("  Birim fiyat (TL): ").strip())
                total = qty * price
                items.append((name, qty, price, total))
                print(f"  -> {name} x {qty} = {total:.2f} TL")
            except ValueError:
                print("  Gecersiz deger!")
        if not items:
            print("Urun girilmedi.")
            return
        total = sum(item[3] for item in items)
        print(f"\nToplam: {total:.2f} TL")
        try:
            payment = float(input("Odenen tutar: ").strip() or str(total))
            change = payment - total
            if change < 0:
                print("Eksik odeme!")
                change = 0
        except ValueError:
            payment = total
            change = 0
        receipt = self.receipt_builder.build_sale_receipt(
            items=items, total=total,
            payment={"method": "NAKIT", "amount": payment},
            change=change,
        )
        print("\n" + "=" * 42)
        print(receipt.get_text())
        print("=" * 42)
        yazdir = input("\nYaziciya yazdirilsin mi? (e/h): ").strip().lower()
        if yazdir == "e":
            self.printer.connect()
            if self.printer.print_receipt(receipt):
                print("Fis yazdirildi!")
            else:
                print("Yazdirma hatasi!")
            self.printer.disconnect()
        input("\nDevam etmek icin Enter'a basin...")

    def _test_barcode_print(self):
        print("\n--- Barkod/QR Yazdirma Testi ---\n")
        print("1. Barkod Yazdir")
        print("2. QR Kod Yazdir")
        secim = input("Seciminiz (1-2): ").strip()
        self.printer.connect()
        if secim == "1":
            data = input("Barkod verisi: ").strip() or "8691234567890"
            btype = input("Barkod tipi (CODE128/EAN13): ").strip() or "CODE128"
            if self.printer.print_barcode(data, btype):
                print(f"Barkod yazdirildi: {data} ({btype})")
            else:
                print("Barkod yazdirilamadi!")
        elif secim == "2":
            data = input("QR kod verisi: ").strip() or "https://accura.com.tr"
            if self.printer.print_qr(data):
                print(f"QR kod yazdirildi: {data}")
            else:
                print("QR kod yazdirilamadi!")
        self.printer.disconnect()
        input("\nDevam etmek icin Enter'a basin...")

    def _test_z_report(self):
        print("\n--- Z Raporu Testi ---\n")
        sales_data = {
            "date": time.strftime("%d.%m.%Y"),
            "report_no": time.strftime("%y%m%d%H%M%S"),
            "total_sales": 15246.50,
            "total_count": 47,
            "total_returns": 325.00,
            "return_count": 2,
            "payment_breakdown": {
                "NAKIT": 10246.50,
                "KREDI KARTI": 4500.00,
                "CEK": 500.00,
            },
            "tax_totals": {
                "KDV %18": 2326.50,
                "KDV %8": 320.00,
            },
        }
        report = self.receipt_builder.build_daily_report(sales_data)
        print("\n" + "=" * 42)
        print(report.get_text())
        print("=" * 42)
        self.printer.connect()
        print("\nRapor yazdiriliyor...")
        if self.printer.print_report("Z"):
            print("Z raporu yazdirildi!")
        else:
            print("Rapor yazdirilamadi!")
        self.printer.disconnect()
        input("\nDevam etmek icin Enter'a basin...")


def main():
    app = YazarkasaApp()
    app.run()


if __name__ == "__main__":
    main()
