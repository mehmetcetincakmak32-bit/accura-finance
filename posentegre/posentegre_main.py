"""
Accura Finance - POS Entegrasyon Ana Giris
POS sunucu yonetimi, banka POS emulator ve CLI menu
"""

import os
import sys
import json
import time
from datetime import datetime

from .config import POSConfig
from .pos_server import POSServer
from .rest_api import POSRestAPI
from .transaction_logger import TransactionLogger
from .bank_protocols import get_protocol
from .pos_device_manager import POSDeviceManager


class POSEntegreMain:
    """POS entegrasyon ana yonetici - CLI menu ve sistem yonetimi"""

    def __init__(self):
        self.config = POSConfig()
        self.txn_logger = TransactionLogger(self.config.get_log_db_path())
        self.device_manager = POSDeviceManager()
        self.pos_server = POSServer(self.config)
        self.rest_api = POSRestAPI(self.pos_server, self.config)
        self._running = True

    def run(self):
        """Ana menuyu calistir"""
        self._print_banner()
        while self._running:
            self._show_main_menu()
            try:
                choice = input("\nSeciminiz: ").strip()
                self._handle_menu_choice(choice)
            except KeyboardInterrupt:
                print("\n\nProgram sonlandiriliyor...")
                self._cleanup()
                break
            except Exception as e:
                print(f"\nHATA: {e}")
                input("Devam etmek icin Enter tusuna basin...")

    def _print_banner(self):
        """Baslik bannerini goster"""
        print("=" * 60)
        print("   ACCURA FINANCE - POS ENTEGRASYON SISTEMI")
        print("   Banka POS Cihazlari ve Online Odeme Kapilari")
        print("=" * 60)

    def _show_main_menu(self):
        """Ana menu seceneklerini goster"""
        server_status = "CALISIYOR" if self.pos_server.is_running else "DURDURULDU"
        api_status = "CALISIYOR" if self.rest_api.is_running else "DURDURULDU"

        print(f"\n[ Sunucu Durumu: POS={server_status} | REST API={api_status} ]")
        print("-" * 60)
        print("1. POS Sunucuyu Baslat")
        print("2. Banka POS Emulator (Test Modu)")
        print("3. Islem Gecmisi")
        print("4. Gun Sonu (Settlement)")
        print("5. POS Cihaz Yonetimi")
        print("6. REST API Baslat/Durdur")
        print("7. Cikis")
        print("-" * 60)

    def _handle_menu_choice(self, choice):
        """Menu secimine gore islem yap"""
        if choice == '1':
            self._pos_server_menu()
        elif choice == '2':
            self._pos_emulator()
        elif choice == '3':
            self._transaction_history()
        elif choice == '4':
            self._settlement_menu()
        elif choice == '5':
            self._device_management()
        elif choice == '6':
            self._rest_api_menu()
        elif choice == '7':
            self._cleanup()
            self._running = False
            print("Program sonlandirildi.")
        else:
            print("Gecersiz secim! Lutfen 1-7 arasi bir deger girin.")

    def _pos_server_menu(self):
        """POS sunucu baslatma/durdurma menusu"""
        if self.pos_server.is_running:
            print(f"\nPOS sunucu {self.config.host}:{self.config.port} adresinde calisiyor.")
            stop = input("Sunucuyu durdurmak ister misiniz? (e/h): ").strip().lower()
            if stop == 'e':
                result = self.pos_server.stop()
                print(f"-> {result['message']}")
        else:
            print(f"\nPOS sunucu baslatiliyor: {self.config.host}:{self.config.port}...")
            result = self.pos_server.start()
            print(f"-> {result['message']}")
            if result['success']:
                print("Bagli istemciler bekleniyor...")
                print("(Ana menuye donmek icin bir tusa basin)")

    def _pos_emulator(self):
        """Banka POS emulatoru - kartli odeme simulasyonu"""
        print("\n" + "=" * 60)
        print("   BANKA POS EMULATOR - Test Odeme Sistemi")
        print("=" * 60)

        kart_no = input("\nKart Numarasi (16 hane): ").strip().replace(' ', '')
        if not kart_no or len(kart_no) < 16 or not kart_no.isdigit():
            print("HATA: Gecerli bir kart numarasi girin (16 hane)")
            input("Devam etmek icin Enter tusuna basin...")
            return

        try:
            tutar = float(input("Tutar (TL): ").strip())
            if tutar <= 0:
                print("HATA: Tutar 0'dan buyuk olmali")
                return
        except ValueError:
            print("HATA: Gecerli bir tutar girin")
            return

        try:
            taksit = int(input("Taksit Sayisi (1=tek cekim): ").strip() or "1")
            if taksit < 1:
                taksit = 1
        except ValueError:
            taksit = 1

        print("\nBanka Secin:")
        print("1. Akbank (Komisyon: %1.8)")
        print("2. Garanti (Komisyon: %1.6)")
        print("3. Yapi Kredi (Komisyon: %1.9)")
        print("4. Isbankasi (Komisyon: %1.7)")
        print("5. Ziraat (Komisyon: %1.4)")
        print("6. Halkbank (Komisyon: %1.5)")
        banka_sec = input("Seciminiz (1-6): ").strip()

        banka_harita = {
            '1': ('Akbank', 'AKB12345', 'TML001'),
            '2': ('Garanti', 'GAR12345', 'TML002'),
            '3': ('Yapi Kredi', 'YKB12345', 'TML003'),
            '4': ('Isbankasi', 'ISB12345', 'TML004'),
            '5': ('Ziraat', 'ZRT12345', 'TML005'),
            '6': ('Halkbank', 'HLK12345', 'TML006'),
        }

        banka_adi, musteri_no, terminal_no = banka_harita.get(banka_sec, ('Akbank', 'AKB12345', 'TML001'))

        print(f"\nIslem Baslatiliyor...")
        print(f"Kart: {kart_no[:6]}******{kart_no[-4:]}")
        print(f"Tutar: {tutar:.2f} TL")
        print(f"Taksit: {taksit}")
        print(f"Banka: {banka_adi}")
        print("-" * 40)

        protocol = get_protocol(banka_adi, musteri_no, terminal_no)
        result = protocol.process_payment(kart_no, tutar, taksit)

        if result['status'] == 'success':
            print("\nISLEM BASARILI!")
            print(f"Yetki Kodu (Auth Code): {result['auth_code']}")
            print(f"Referans Numarasi: {result['reference_no']}")
            print(f"Komisyon Orani: %{result['commission_rate']}")
            print(f"Komisyon Tutari: {result['commission']:.2f} TL")
            print(f"Net Tutar: {result['net_amount']:.2f} TL")
            print(f"Banka: {result['bank']}")
        else:
            print(f"\nISLEM BASARISIZ: {result.get('message', 'Bilinmeyen hata')}")

        self.txn_logger.log_transaction(result)
        print("\nIslem kaydedildi.")
        input("Devam etmek icin Enter tusuna basin...")

    def _transaction_history(self):
        """Islem gecmisi goruntuleme"""
        print("\n" + "=" * 60)
        print("   ISLEM GECMISI")
        print("=" * 60)

        print("\nFiltreleme Secenekleri:")
        print("1. Son 24 saat")
        print("2. Son 7 gun")
        print("3. Son 30 gun")
        print("4. Tum islemler")
        print("5. Bankaya gore filtrele")
        print("6. Gunluk Ozet")
        print("7. Aylik Ozet")
        secim = input("Seciminiz (1-7): ").strip()

        transactions = []
        now = datetime.now()

        if secim == '1':
            start = now.strftime('%Y-%m-%d')
            end = now.strftime('%Y-%m-%d')
            transactions = self.txn_logger.get_transactions(date_range=(start, end))
        elif secim == '2':
            start = now.strftime('%Y-%m-%d')
            end = now.strftime('%Y-%m-%d')
            transactions = self.txn_logger.get_transactions()
            transactions = [t for t in transactions if
                          (now - datetime.fromisoformat(t['date'])).days <= 7]
        elif secim == '3':
            transactions = self.txn_logger.get_transactions()
            transactions = [t for t in transactions if
                          (now - datetime.fromisoformat(t['date'])).days <= 30]
        elif secim == '4':
            transactions = self.txn_logger.get_transactions()
        elif secim == '5':
            banka = input("Banka adi: ").strip()
            transactions = self.txn_logger.get_transactions(bank=banka)
        elif secim == '6':
            date = input("Tarih (YYYY-MM-DD, bos=bugun): ").strip() or now.strftime('%Y-%m-%d')
            summary = self.txn_logger.get_daily_summary(date)
            self._print_daily_summary(summary)
            input("\nDevam etmek icin Enter tusuna basin...")
            return
        elif secim == '7':
            year = input("Yil (bos=bu yil): ").strip()
            month = input("Ay (1-12, bos=bu ay): ").strip()
            year = int(year) if year else now.year
            month = int(month) if month else now.month
            summary = self.txn_logger.get_monthly_summary(year, month)
            self._print_monthly_summary(summary)
            input("\nDevam etmek icin Enter tusuna basin...")
            return
        else:
            print("Gecersiz secim!")
            return

        if not transactions:
            print("\nKayitli islem bulunamadi.")
        else:
            print(f"\nToplam {len(transactions)} islem bulundu:")
            print("-" * 80)
            print(f"{'ID':<20} {'Tarih':<22} {'Tutar':<10} {'Banka':<12} {'Durum':<10} {'Tip':<10}")
            print("-" * 80)
            for t in transactions[:50]:
                date_str = datetime.fromisoformat(t['date']).strftime('%d.%m.%Y %H:%M')
                print(f"{t['id']:<20} {date_str:<22} {t['amount']:<10.2f} "
                      f"{t['bank']:<12} {t['status']:<10} {t['type']:<10}")
            print("-" * 80)
            if len(transactions) > 50:
                print(f"... ve {len(transactions) - 50} islem daha")

        input("\nDevam etmek icin Enter tusuna basin...")

    def _print_daily_summary(self, summary):
        """Gunluk ozet yazdir"""
        print(f"\nGUNLUK OZET - {summary['date']}")
        print("=" * 50)
        print(f"Toplam Islem: {summary['total_transactions']}")
        print(f"Toplam Tutar: {summary['total_amount']:.2f} TL")
        print(f"Toplam Komisyon: {summary['total_commission']:.2f} TL")
        print(f"Toplam Net: {summary['total_net']:.2f} TL")
        print(f"Basarili: {summary['success_count']}")
        print(f"Basarisiz: {summary['failed_count']}")
        print(f"Iade: {summary['refunded_count']}")
        print(f"Iptal: {summary['cancelled_count']}")

        if summary['by_bank']:
            print("\nBankalara Gore:")
            for bank, data in summary['by_bank'].items():
                print(f"  {bank}: {data['count']} islem, {data['amount']:.2f} TL")

    def _print_monthly_summary(self, summary):
        """Aylik ozet yazdir"""
        print(f"\nAYLIK OZET - {summary['year']}/{summary['month']:02d}")
        print("=" * 50)
        print(f"Toplam Islem: {summary['total_transactions']}")
        print(f"Toplam Tutar: {summary['total_amount']:.2f} TL")
        print(f"Toplam Komisyon: {summary['total_commission']:.2f} TL")
        print(f"Toplam Net: {summary['total_net']:.2f} TL")
        print(f"Basarili: {summary['success_count']}")
        print(f"Basarisiz: {summary['failed_count']}")

        if summary['daily']:
            print("\nGunluk Dagilim:")
            for day, data in sorted(summary['daily'].items()):
                print(f"  {day}: {data['count']} islem, {data['amount']:.2f} TL")

    def _settlement_menu(self):
        """Gun sonu islemi"""
        print("\n" + "=" * 60)
        print("   GUN SONU (SETTLEMENT)")
        print("=" * 60)

        date = input("Tarih (YYYY-MM-DD, bos=bugun): ").strip()
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')

        print(f"\nGun sonu raporu hazirlaniyor: {date}")
        report = self.txn_logger.get_settlement_report(date)

        print(f"\nSETTLEMENT RAPORU - {report['date']}")
        print(f"Settlement ID: {report['settlement_id']}")
        print("=" * 50)
        print(f"Toplam Satis: {report['total_sales']:.2f} TL")
        print(f"Toplam Komisyon: {report['total_commission']:.2f} TL")
        print(f"Toplam Net: {report['total_net']:.2f} TL")
        print(f"Islem Sayisi: {report['transaction_count']}")
        print(f"Durum: {report['status']}")

        if report['bank_details']:
            print("\nBanka Detaylari:")
            for bank, data in report['bank_details'].items():
                print(f"  {bank}:")
                print(f"    Islem: {data['count']}")
                print(f"    Tutar: {data['amount']:.2f} TL")
                print(f"    Komisyon: {data['commission']:.2f} TL")

        print("\nGun sonu islemi tamamlandi.")
        input("Devam etmek icin Enter tusuna basin...")

    def _device_management(self):
        """POS cihaz yonetim menusu"""
        while True:
            print("\n" + "=" * 60)
            print("   POS CIHAZ YONETIMI")
            print("=" * 60)
            print("1. Cihazlari Listele")
            print("2. Cihaz Kaydet")
            print("3. Cihaz Sil")
            print("4. Cihaz Detayi Gor")
            print("5. Cihaz Baglan/Baglantiyi Kes")
            print("6. Cihaz Yapilandir")
            print("7. Ana Menuye Don")
            secim = input("\nSeciminiz (1-7): ").strip()

            if secim == '1':
                devices = self.device_manager.list_devices()
                if not devices:
                    print("\nKayitli cihaz bulunamadi.")
                else:
                    print(f"\nKayitli Cihazlar ({len(devices)}):")
                    print("-" * 80)
                    for d in devices:
                        print(f"  {d['device_id']} | {d['device_type']} | "
                              f"{d['bank']} | {d['ip']}:{d['port']} | {d['status']}")
                input("\nDevam icin Enter...")

            elif secim == '2':
                device_id = input("Cihaz ID: ").strip()
                device_type = input("Cihaz Tipi (pinpad/terminal/yazici): ").strip()
                bank = input("Banka: ").strip()
                ip = input("IP Adresi: ").strip()
                try:
                    port = int(input("Port: ").strip())
                except ValueError:
                    port = 9090
                result = self.device_manager.register_device(
                    device_id, device_type, bank, ip, port
                )
                print(f"-> {result['message']}")
                input("\nDevam icin Enter...")

            elif secim == '3':
                device_id = input("Silinecek cihaz ID: ").strip()
                result = self.device_manager.unregister_device(device_id)
                print(f"-> {result['message']}")
                input("\nDevam icin Enter...")

            elif secim == '4':
                device_id = input("Cihaz ID: ").strip()
                device = self.device_manager.get_device(device_id)
                if device:
                    print(f"\nCIHAZ DETAYI:")
                    for key, val in device.items():
                        print(f"  {key}: {val}")
                else:
                    print("Cihaz bulunamadi.")
                input("\nDevam icin Enter...")

            elif secim == '5':
                device_id = input("Cihaz ID: ").strip()
                device = self.device_manager.get_device(device_id)
                if not device:
                    print("Cihaz bulunamadi.")
                    input("\nDevam icin Enter...")
                    continue
                if device['status'] == 'online':
                    self.device_manager.disconnect_device(device_id)
                    print(f"Cihaz {device_id} baglantisi kesildi.")
                else:
                    result = self.device_manager.connect_device(device_id)
                    print(f"-> {result['message']}")
                input("\nDevam icin Enter...")

            elif secim == '6':
                device_id = input("Cihaz ID: ").strip()
                print("Yapilandirma degerleri (bos birakilirsa degismez):")
                config = {}
                merchant = input("  Merchant ID: ").strip()
                if merchant:
                    config['merchant_id'] = merchant
                terminal = input("  Terminal ID: ").strip()
                if terminal:
                    config['terminal_id'] = terminal
                comm = input("  Komisyon Orani (%): ").strip()
                if comm:
                    try:
                        config['commission_rate'] = float(comm)
                    except ValueError:
                        pass
                ssl_val = input("  SSL (e/h): ").strip().lower()
                if ssl_val:
                    config['ssl'] = ssl_val == 'e'
                ip = input("  IP Adresi: ").strip()
                if ip:
                    config['ip'] = ip
                port = input("  Port: ").strip()
                if port:
                    try:
                        config['port'] = int(port)
                    except ValueError:
                        pass

                result = self.device_manager.configure_device(device_id, config)
                print(f"-> {result['message']}")
                input("\nDevam icin Enter...")

            elif secim == '7':
                break
            else:
                print("Gecersiz secim!")

    def _rest_api_menu(self):
        """REST API baslat/durdur menusu"""
        if self.rest_api.is_running:
            print(f"\nREST API calisiyor. Durduruluyor...")
            result = self.rest_api.stop()
            print(f"-> {result['message']}")
        else:
            print(f"\nREST API baslatiliyor...")
            api_host = self.config.get('REST_API', 'host', '127.0.0.1')
            api_port = self.config.getint('REST_API', 'port', 9091)
            result = self.rest_api.start(api_host, api_port)
            print(f"-> {result['message']}")

    def _cleanup(self):
        """Kapanis oncesi temizlik"""
        if self.pos_server.is_running:
            self.pos_server.stop()
        if self.rest_api.is_running:
            self.rest_api.stop()
        print("Kaynaklar temizlendi.")


def main():
    """Ana giris fonksiyonu"""
    app = POSEntegreMain()
    app.run()


if __name__ == '__main__':
    main()
