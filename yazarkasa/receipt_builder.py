
"""
Fis Olusturma ve Bicimlendirme Modulu
========================================
ESC/POS komutlari ile fis olusturma, satir bicimlendirme,
barkod/QR kod ekleme ve farkli fis tiplerini destekler.
"""

import logging
from datetime import datetime

from yazarkasa.printer_utils import PrinterUtils

logger = logging.getLogger(__name__)


class ReceiptBuilder:
    """
    Fis olusturma ve bicimlendirme sinifi.
    ESC/POS byte komutlari ve duz metin ciktisi uretir.
    """

    # ESC/POS kontrol karakterleri
    ESC = 0x1B
    GS = 0x1D
    LF = 0x0A
    CR = 0x0D
    NUL = 0x00

    # Hizalama
    ALIGN_LEFT = 0x00
    ALIGN_CENTER = 0x01
    ALIGN_RIGHT = 0x02

    # Karakter boyutlari
    SIZE_NORMAL = 0x00
    SIZE_WIDE = 0x10
    SIZE_TALL = 0x20
    SIZE_BIG = 0x30

    def __init__(self, config=None):
        """
        ReceiptBuilder baslatma.

        Args:
            config: Config nesnesi (opsiyonel)
        """
        self.config = config
        self.lines = []
        self.encoding = "cp857"

        if config:
            self.encoding = config.encoding
            self.merchant = config.merchant_info
            self.char_width = config.char_per_line
            self.header_text = config.receipt_header
            self.footer_text = config.receipt_footer
        else:
            self.merchant = {
                "name": "ISYERI ADI",
                "tax_office": "",
                "tax_number": "",
                "address": "",
                "phone": "",
                "website": "",
                "email": "",
            }
            self.char_width = 42
            self.header_text = ""
            self.footer_text = ""

    def _make_escpos(self, *args):
        """ESC/POS komut bayt dizisi olusturur."""
        return bytes(args)

    def clear(self):
        """Fis tamponunu temizler."""
        self.lines = []

    def add_line(self, text, align="left", size="normal", bold=False, double=False):
        """
        Bicimlendirilmis satir ekler.

        Args:
            text: Satir metni
            align: Hizalama ("left", "center", "right")
            size: Boyut ("normal", "wide", "tall", "big")
            bold: Kalin yazi (True/False)
            double: Cift vurus (True/False)
        """
        self.lines.append({
            "type": "text",
            "text": text,
            "align": align,
            "size": size,
            "bold": bold,
            "double": double,
        })

    def add_separator(self, char="-"):
        """
        Ayrac satiri ekler.

        Args:
            char: Ayrac karakteri
        """
        self.lines.append({
            "type": "separator",
            "char": char,
        })

    def add_blank_line(self, count=1):
        """Bos satir ekler."""
        for _ in range(count):
            self.lines.append({
                "type": "blank",
            })

    def add_item(self, name, qty, price, total):
        """
        Urun satiri ekler (sutunlu format).

        Args:
            name: Urun adi
            qty: Miktar
            price: Birim fiyat
            total: Toplam tutar
        """
        self.lines.append({
            "type": "item",
            "name": name,
            "qty": qty,
            "price": price,
            "total": total,
        })

    def add_total(self, label, amount):
        """
        Toplam satiri ekler.

        Args:
            label: Aciklama (Orn: "ARA TOPLAM")
            amount: Tutar
        """
        self.lines.append({
            "type": "total",
            "label": label,
            "amount": amount,
        })

    def add_barcode(self, data, barcode_type="CODE128"):
        """
        Barkod ekleme komutu ekler.

        Args:
            data: Barkod verisi
            barcode_type: Barkod tipi
        """
        self.lines.append({
            "type": "barcode",
            "data": data,
            "barcode_type": barcode_type,
        })

    def add_qr(self, data):
        """
        QR kod ekleme komutu ekler.

        Args:
            data: QR kod verisi
        """
        self.lines.append({
            "type": "qr",
            "data": data,
        })

    def add_coupon(self, code, discount, description=""):
        """
        Kupon/indirim satiri ekler.

        Args:
            code: Kupon kodu
            discount: Indirim tutari
            description: Aciklama
        """
        self.lines.append({
            "type": "coupon",
            "code": code,
            "discount": discount,
            "description": description,
        })

    def add_payment_line(self, method, amount, change=0):
        """
        Odeme satiri ekler.

        Args:
            method: Odeme yontemi ("NAKIT", "KREDI KARTI", vb.)
            amount: Odenen tutar
            change: Para ustu
        """
        self.lines.append({
            "type": "payment",
            "method": method,
            "amount": amount,
            "change": change,
        })

    def add_header_footer(self):
        """Fis baslik ve ayak yazilarini ekler."""
        if self.header_text:
            for line in self.header_text.split("\n"):
                self.add_line(line.strip(), align="center")

        if self.header_text and any(l.get("type") != "blank" for l in self.lines):
            self.add_separator()

    def add_merchant_info(self):
        """Satici bilgilerini fise ekler."""
        info = self.merchant
        self.add_line(info["name"], align="center", bold=True, size="wide")
        if info["address"]:
            for addr_line in info["address"].split("\n"):
                if addr_line.strip():
                    self.add_line(addr_line.strip(), align="center")
        phone_line = info.get("phone", "")
        if phone_line:
            self.add_line(f"Tel: {phone_line}", align="center")
        tax_line = ""
        if info.get("tax_office"):
            tax_line += f"VD: {info['tax_office']}"
        if info.get("tax_number"):
            tax_line += f"  VN: {info['tax_number']}"
        if tax_line:
            self.add_line(tax_line, align="center")
        self.add_separator()

    # --- Fis olusturma metodlari ---

    def build_sale_receipt(self, items, total, payment, change, merchant_info=None):
        """
        Satis fisi olusturur.

        Args:
            items: Urun listesi [(isim, miktar, fiyat, toplam), ...]
            total: Genel toplam
            payment: Odenen tutar
            change: Para ustu
            merchant_info: Satici bilgileri (opsiyonel)

        Returns:
            ReceiptBuilder: Kendisi (zincirleme cagri icin)
        """
        self.clear()

        if merchant_info:
            self.merchant.update(merchant_info)

        # Satici bilgisi
        self.add_merchant_info()

        # Tarih/saat
        now = datetime.now()
        date_str = now.strftime("%d.%m.%Y %H:%M:%S")
        self.add_line(f"Fis Tarihi: {date_str}", align="left")
        self.add_line(f"Fis No: {now.strftime('%y%m%d%H%M%S')}", align="left")
        self.add_separator()

        # Baslik
        self.add_line("SATIS FISI", align="center", bold=True, size="big")
        self.add_line("*** SATIS ***", align="center", bold=True)
        self.add_separator()

        # Urunler
        self.add_line(f"{'URUN':<22} {'MIK':>5} {'TUTAR':>10}", align="left", bold=True)
        self.add_separator()

        for item in items:
            if len(item) == 4:
                name, qty, price, total_price = item
            else:
                name, price = item
                qty = 1
                total_price = price

            name = name[:22]
            try:
                qty_str = f"{qty:.2f}" if isinstance(qty, float) else str(qty)
            except (ValueError, TypeError):
                qty_str = "1"

            total_str = f"{float(total_price):.2f} TL"
            line = f"{name:<22} {qty_str:>5} {total_str:>10}"
            self.add_line(line, align="left")

        self.add_separator()

        # Toplam
        self.add_total("ARA TOPLAM", total)

        # Odeme
        self.add_line("", align="left")  # bos satir
        self.add_line("ODEME BILGILERI", align="center", bold=True)
        self.add_separator()

        payment_method = payment.get("method", "NAKIT") if isinstance(payment, dict) else "NAKIT"
        payment_amount = payment.get("amount", payment) if isinstance(payment, dict) else payment

        self.add_payment_line(payment_method, payment_amount, change)
        self.add_separator()

        # Para ustu
        if change > 0:
            self.add_total("PARA USTU", change)

        self.add_line("", align="left")
        self.add_line("TESFEKKUR EDERIZ", align="center", bold=True, size="wide")
        self.add_line("IYI GUNLER", align="center")

        # Footer
        if self.footer_text:
            self.add_separator()
            for line in self.footer_text.split("\n"):
                if line.strip():
                    self.add_line(line.strip(), align="center")

        return self

    def build_return_receipt(self, items, total, original_receipt_no):
        """
        Iade fisi olusturur.

        Args:
            items: Iade urun listesi
            total: Iade tutari
            original_receipt_no: Orijinal fis numarasi

        Returns:
            ReceiptBuilder: Kendisi
        """
        self.clear()
        self.add_merchant_info()

        now = datetime.now()
        self.add_line(f"Tarih: {now.strftime('%d.%m.%Y %H:%M:%S')}", align="left")
        self.add_separator()

        self.add_line("IADE FISI", align="center", bold=True, size="big")
        self.add_line("*** IADE ***", align="center", bold=True)
        self.add_line(f"Orijinal Fis: {original_receipt_no}", align="center")
        self.add_separator()

        for item in items:
            if len(item) >= 4:
                name, qty, price, total_price = item[:4]
            else:
                name, price = item
                qty = 1
                total_price = price

            name = name[:22]
            total_str = f"{float(total_price):.2f} TL"
            self.add_line(f"{name:<22} {str(qty):>5} {total_str:>10}", align="left")

        self.add_separator()
        self.add_total("IADE TOPLAMI", total)
        self.add_line("", align="left")
        self.add_line("IADE ISLEMI GERCEKLESTI", align="center", bold=True)

        return self

    def build_invoice(self, invoice_data, lines=None):
        """
        Fatura formati olusturur.

        Args:
            invoice_data: Fatura bilgileri (soyut)
                {
                    "number": "FTR2024000001",
                    "date": "01.01.2024",
                    "customer": "Musteri Adi",
                    "tax_office": "VD",
                    "tax_number": "VN",
                    "address": "Adres"
                }
            lines: Ek satirlar (opsiyonel)

        Returns:
            ReceiptBuilder: Kendisi
        """
        self.clear()
        self.add_merchant_info()

        now = datetime.now()
        self.add_line(f"Tarih: {now.strftime('%d.%m.%Y %H:%M:%S')}", align="left")
        self.add_separator()

        self.add_line("FATURA", align="center", bold=True, size="big")
        self.add_separator()

        inv_no = invoice_data.get("number", f"FTR{now.strftime('%Y%m%d%H%M%S')}")
        inv_date = invoice_data.get("date", now.strftime("%d.%m.%Y"))

        self.add_line(f"Fatura No: {inv_no}", align="left")
        self.add_line(f"Fatura Tarihi: {inv_date}", align="left")

        customer = invoice_data.get("customer", "")
        if customer:
            self.add_line(f"Musteri: {customer}", align="left")

        tax_office = invoice_data.get("tax_office", "")
        tax_number = invoice_data.get("tax_number", "")
        if tax_office or tax_number:
            self.add_line(f"VD: {tax_office}   VN: {tax_number}", align="left")

        address = invoice_data.get("address", "")
        if address:
            self.add_line(f"Adres: {address}", align="left")

        self.add_separator()

        # Fatura satirlari
        if lines:
            for line in lines:
                if len(line) >= 4:
                    name, qty, price, total_price = line[:4]
                    name = name[:22]
                    total_str = f"{float(total_price):.2f} TL"
                    self.add_line(f"{name:<22} {str(qty):>5} {total_str:>10}", align="left")

        total = invoice_data.get("total", 0)
        if total:
            self.add_separator()
            self.add_total("TOPLAM", total)

        return self

    def build_daily_report(self, sales_data):
        """
        Gun sonu Z raporu olusturur.

        Args:
            sales_data: Satis verileri sozlugu
                {
                    "date": "01.01.2024",
                    "total_sales": 10000,
                    "total_count": 50,
                    "total_returns": 500,
                    "return_count": 3,
                    "payment_breakdown": {"NAKIT": 7000, "KREDI KARTI": 3000},
                    "tax_totals": {"KDV %18": 1525.42, "KDV %8": 400.00},
                }

        Returns:
            ReceiptBuilder: Kendisi
        """
        self.clear()
        self.add_merchant_info()

        now = datetime.now()
        date_str = sales_data.get("date", now.strftime("%d.%m.%Y"))
        report_no = sales_data.get("report_no", now.strftime("%y%m%d%H%M%S"))

        self.add_line(f"Tarih: {date_str}", align="left")
        self.add_line(f"Rapor No: {report_no}", align="left")
        self.add_separator()

        self.add_line("Z RAPORU", align="center", bold=True, size="big")
        self.add_line("*** GUN SONU RAPORU ***", align="center", bold=True)
        self.add_separator()

        # Satis ozeti
        total_sales = sales_data.get("total_sales", 0)
        total_count = sales_data.get("total_count", 0)
        total_returns = sales_data.get("total_returns", 0)
        return_count = sales_data.get("return_count", 0)

        self.add_total("TOPLAM SATIS", total_sales)
        self.add_line(f"Fis Adedi       : {total_count}", align="left")
        self.add_total("TOPLAM IADE", total_returns)
        self.add_line(f"Iade Adedi      : {return_count}", align="left")
        self.add_total("NET SATIS", total_sales - total_returns)
        self.add_separator()

        # Odeme kirilimi
        self.add_line("ODEME TURLERI", align="center", bold=True)
        payment_breakdown = sales_data.get("payment_breakdown", {})
        for method, amount in payment_breakdown.items():
            self.add_line(f"{method:<15} {amount:>10.2f} TL", align="left")
        self.add_separator()

        # KDV kirilimi
        tax_totals = sales_data.get("tax_totals", {})
        if tax_totals:
            self.add_line("KDV KIRILIMI", align="center", bold=True)
            for tax_name, tax_amount in tax_totals.items():
                self.add_line(f"{tax_name:<15} {tax_amount:>10.2f} TL", align="left")
            self.add_separator()

        self.add_line("", align="left")
        self.add_line("RAPOR KAPANDI", align="center", bold=True, size="wide")

        return self

    def build_customer_receipt(self, items, total):
        """
        Musteri kopyasi (sade) fis olusturur.

        Args:
            items: Urun listesi
            total: Toplam

        Returns:
            ReceiptBuilder: Kendisi
        """
        self.clear()
        self.add_line("MUSTERI KOPYASI", align="center", bold=True, double=True)
        self.add_line("*** COKLU ODEME ***", align="center", bold=True)
        self.add_separator()

        for item in items:
            if len(item) >= 4:
                name, qty, price, total_price = item[:4]
            else:
                name, price = item
                qty = 1
                total_price = price

            name = name[:24]
            total_str = f"{float(total_price):.2f}"
            self.add_line(f"{name:<24} T {total_str:>8}", align="left")

        self.add_separator()
        self.add_total("TOPLAM", total)

        self.add_line("", align="left")
        self.add_line("ALISVERISINIZ ICIN TESFEKKUR EDERIZ", align="center")

        return self

    # --- ESC/POS byte komutlari ---

    def get_escpos(self):
        """
        Tum fisi ESC/POS byte komutlari olarak dondurur.

        Returns:
            bytes: ESC/POS komut dizisi
        """
        commands = bytearray()

        # Initialize printer
        commands.extend([0x1B, 0x40])  # ESC @

        for line in self.lines:
            commands.extend(self._line_to_escpos(line))

        # Cut paper
        commands.extend([0x1D, 0x56, 0x00])  # GS V 0 (full cut)

        # Print and feed
        commands.extend([0x1B, 0x64, 0x03])  # Feed 3 lines

        return bytes(commands)

    def _line_to_escpos(self, line):
        """Bir satiri ESC/POS komutlarina cevirir."""
        cmd = bytearray()
        line_type = line.get("type", "text")

        if line_type == "blank":
            cmd.extend([0x0A])
            return bytes(cmd)

        if line_type == "separator":
            char = line.get("char", "-")
            text = char * self.char_width
            cmd.extend(self._format_text(text, "center", "normal", False))
            return bytes(cmd)

        if line_type == "text":
            text = line.get("text", "")
            align = line.get("align", "left")
            size = line.get("size", "normal")
            bold = line.get("bold", False)
            cmd.extend(self._format_text(text, align, size, bold))
            return bytes(cmd)

        if line_type in ("total", "payment"):
            label = line.get("label", "")
            amount = line.get("amount", 0)
            text = f"{label:<25} {float(amount):>8.2f} TL"
            cmd.extend(self._format_text(text, "left", "normal", True))
            if line_type == "payment" and line.get("change", 0) > 0:
                change = line.get("change", 0)
                change_text = f"PARA USTU: {float(change):.2f} TL"
                cmd.extend(self._format_text(change_text, "right", "normal", False))
            return bytes(cmd)

        if line_type == "item":
            name = line.get("name", "")
            qty = str(line.get("qty", ""))
            total_price = f"{float(line.get('total', 0)):.2f} TL"
            text = f"{name[:22]:<22} {qty:>5} {total_price:>10}"
            cmd.extend(self._format_text(text, "left", "normal", False))
            return bytes(cmd)

        if line_type == "barcode":
            data = line.get("data", "")
            barcode_type = line.get("barcode_type", "CODE128")
            cmd.extend(self._barcode_escpos(data, barcode_type))
            return bytes(cmd)

        if line_type == "qr":
            data = line.get("data", "")
            cmd.extend(self._qr_escpos(data))
            return bytes(cmd)

        return bytes(cmd)

    def _format_text(self, text, align, size, bold):
        """Metni ESC/POS bicimlendirme komutlariyla birlikte dondurur."""
        cmd = bytearray()

        # Hizalama
        align_map = {"left": 0x00, "center": 0x01, "right": 0x02}
        align_val = align_map.get(align, 0x00)
        cmd.extend([0x1B, 0x61, align_val])  # ESC a n

        # Boyut
        size_map = {"normal": 0x00, "wide": 0x10, "tall": 0x20, "big": 0x30}
        size_val = size_map.get(size, 0x00)
        cmd.extend([0x1B, 0x21, size_val])  # ESC ! n

        # Kalin yazi
        if bold:
            cmd.extend([0x1B, 0x45, 0x01])  # ESC E 1
        else:
            cmd.extend([0x1B, 0x45, 0x00])  # ESC E 0

        # Metin
        encoded = PrinterUtils.format_turkish(text, self.encoding)
        cmd.extend(encoded)

        # Satir sonu
        cmd.extend([0x0A])

        return bytes(cmd)

    def _barcode_escpos(self, data, barcode_type):
        """Barkod icin ESC/POS komutlari."""
        cmd = bytearray()

        # Barkod tipini belirle
        type_map = {
            "CODE128": 0x49,  # GS k m n d1...dn
            "EAN13": 0x43,
            "EAN8": 0x45,
            "CODE39": 0x45,
            "ITF": 0x47,
            "UPCA": 0x41,
            "UPCE": 0x42,
        }

        btype = type_map.get(barcode_type.upper(), 0x49)

        # Hata: bazi turler icin parametre sayisi farkli
        data_bytes = data.encode("ascii", errors="replace")

        if barcode_type.upper() == "CODE128":
            # GS k 73 n d1...dn
            cmd.extend([0x1D, 0x6B, 0x49, len(data_bytes)])
            cmd.extend(data_bytes)
        else:
            # GS k m d1...dn NUL
            cmd.extend([0x1D, 0x6B, btype])
            cmd.extend(data_bytes)
            cmd.extend([0x00])

        # Barkod HRI (insan tarafindan okunabilir) karakterleri
        cmd.extend([0x1D, 0x48, 0x02])  # HRI altina yaz

        # Barkod yuksekligi
        cmd.extend([0x1D, 0x68, 0x64])  # 100 pixel

        # Barkod genisligi
        cmd.extend([0x1D, 0x77, 0x03])  # 3 (normal)

        cmd.extend([0x0A])

        return bytes(cmd)

    def _qr_escpos(self, data):
        """QR kod icin ESC/POS komutlari."""
        cmd = bytearray()

        if isinstance(data, str):
            data_bytes = data.encode("utf-8")
        else:
            data_bytes = data

        data_len = len(data_bytes) + 3

        # QR kod modeli (model 2)
        cmd.extend([0x1D, 0x28, 0x6B, 0x04, 0x00, 0x31, 0x41, 0x32, 0x00])

        # QR kod boyutu
        cmd.extend([0x1D, 0x28, 0x6B, 0x03, 0x00, 0x31, 0x43, 0x05])

        # Hata duzeltme seviyesi (M - %15)
        cmd.extend([0x1D, 0x28, 0x6B, 0x03, 0x00, 0x31, 0x45, 0x31])

        # Veriyi QR koda yaz
        pl = data_len & 0xFF
        ph = (data_len >> 8) & 0xFF
        cmd.extend([0x1D, 0x28, 0x6B, pl, ph, 0x31, 0x50, 0x30])
        cmd.extend(data_bytes)

        # QR kodu yazdir
        cmd.extend([0x1D, 0x28, 0x6B, 0x03, 0x00, 0x31, 0x51, 0x30])

        cmd.extend([0x0A])

        return bytes(cmd)

    # --- Duz metin ciktisi ---

    def get_text(self):
        """
        Fisi duz metin olarak dondurur.

        Returns:
            str: Okunabilir metin ciktisi
        """
        lines = []

        for line in self.lines:
            line_type = line.get("type", "text")

            if line_type == "blank":
                lines.append("")
            elif line_type == "separator":
                char = line.get("char", "-")
                lines.append(char * self.char_width)
            elif line_type == "text":
                text = line.get("text", "")
                align = line.get("align", "left")
                bold = line.get("bold", False)

                prefix = "** " if bold else "  "
                if align == "center":
                    text = PrinterUtils.pad_center(text, self.char_width)
                elif align == "right":
                    text = PrinterUtils.pad_right(text, self.char_width)
                else:
                    text = PrinterUtils.pad_left(text, self.char_width)

                lines.append(f"{prefix}{text}")
            elif line_type == "item":
                name = line.get("name", "")
                qty = str(line.get("qty", ""))
                total_price = f"{float(line.get('total', 0)):.2f} TL"
                lines.append(f"  {name[:22]:<22} {qty:>5} {total_price:>10}")
            elif line_type == "total":
                label = line.get("label", "")
                amount = line.get("amount", 0)
                lines.append(f"  {label:<25} {float(amount):>.2f} TL")
            elif line_type == "payment":
                method = line.get("method", "")
                amount = line.get("amount", 0)
                lines.append(f"  {method:<25} {float(amount):>.2f} TL")
                change = line.get("change", 0)
                if change > 0:
                    lines.append(f"  {'PARA USTU':<25} {float(change):>.2f} TL")

        return "\n".join(lines)

    def save_to_file(self, filepath):
        """
        Fisi metin dosyasina kaydeder.

        Args:
            filepath: Kayit yolu

        Returns:
            bool: Basarili mi
        """
        try:
            text = self.get_text()
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(text)
            logger.info("Fis dosyaya kaydedildi: %s", filepath)
            return True
        except OSError as e:
            logger.error("Fis kayit hatasi: %s", e)
            return False

    def __str__(self):
        return self.get_text()
