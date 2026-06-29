"""
TaxHacker entegrasyon modülü - AI fatura/makbuz analizi
Gemini API ile akilli belge tanima ve kategorize etme
"""

import csv
import io
import json
import os
import re
import tempfile
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

try:
    from PIL import Image, ImageFilter
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    try:
        import PyPDF2
        HAS_PYPDF2 = True
    except ImportError:
        HAS_PYPDF2 = False
    HAS_PDFPLUMBER = False


GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"


class TaxHackerAdapter:
    """TaxHacker entegrasyonu - AI fatura/makbuz analizi"""

    def __init__(self, main_app=None, db_manager=None):
        self.main_app = main_app
        self.db_manager = db_manager
        self.api_key = GEMINI_API_KEY
        self.api_url = GEMINI_API_URL
        self.logger = self._setup_logger()

    def _setup_logger(self):
        try:
            from src.utils.logger import setup_logger as sl
            return sl("TaxHacker")
        except Exception:
            import logging
            logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            return logging.getLogger("TaxHacker")

    def _call_gemini(self, prompt: str, image_data: Optional[str] = None) -> str:
        try:
            import urllib.request
            import urllib.parse

            parts: List[Dict[str, Any]] = [{"text": prompt}]
            if image_data:
                parts.append({"inline_data": {"mime_type": "image/jpeg", "data": image_data}})

            data = {
                "contents": [{"parts": parts}],
                "generationConfig": {
                    "temperature": 0.1,
                    "topK": 1,
                    "topP": 1,
                    "maxOutputTokens": 8192,
                },
            }

            url = f"{self.api_url}?key={self.api_key}"
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode(),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read())

            if "candidates" in result and result["candidates"]:
                return result["candidates"][0]["content"]["parts"][0]["text"]
            return ""
        except Exception as e:
            if self.logger:
                self.logger.error(f"AI cagri hatasi: {e}")
            return ""

    def _image_to_base64(self, image_path_or_bytes: Union[str, bytes, Path]) -> Optional[str]:
        try:
            import base64
            if isinstance(image_path_or_bytes, bytes):
                img_bytes = image_path_or_bytes
            else:
                with open(image_path_or_bytes, "rb") as f:
                    img_bytes = f.read()
            return base64.b64encode(img_bytes).decode("utf-8")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Resim okuma hatasi: {e}")
            return None

    def _extract_text_from_image(self, image_path_or_bytes: Union[str, bytes, Path]) -> str:
        if not HAS_PIL:
            return ""
        try:
            if isinstance(image_path_or_bytes, bytes):
                img = Image.open(io.BytesIO(image_path_or_bytes))
            else:
                img = Image.open(image_path_or_bytes)
            img = img.convert("L")
            img = img.filter(ImageFilter.SHARPEN)
            text = self._call_gemini(
                "Bu bir fatura veya makbuz goruntusudur. Fotograftaki tum metni oldugu gibi cikar.",
                self._image_to_base64(image_path_or_bytes),
            )
            return text.strip()
        except Exception as e:
            if self.logger:
                self.logger.error(f"Goruntu metin cikarma hatasi: {e}")
            return ""

    def _extract_text_from_pdf(self, pdf_path_or_bytes: Union[str, bytes, Path]) -> str:
        text = ""
        try:
            if HAS_PDFPLUMBER:
                if isinstance(pdf_path_or_bytes, bytes):
                    with pdfplumber.open(io.BytesIO(pdf_path_or_bytes)) as pdf:
                        for page in pdf.pages:
                            t = page.extract_text()
                            if t:
                                text += t + "\n"
                else:
                    with pdfplumber.open(pdf_path_or_bytes) as pdf:
                        for page in pdf.pages:
                            t = page.extract_text()
                            if t:
                                text += t + "\n"
            elif HAS_PYPDF2:
                if isinstance(pdf_path_or_bytes, bytes):
                    reader = PyPDF2.PdfReader(io.BytesIO(pdf_path_or_bytes))
                else:
                    reader = PyPDF2.PdfReader(pdf_path_or_bytes)
                for page in reader.pages:
                    t = page.extract_text()
                    if t:
                        text += t + "\n"
            else:
                if self.logger:
                    self.logger.warning("PDF kutuphanesi bulunamadi. pip install pdfplumber")
        except Exception as e:
            if self.logger:
                self.logger.error(f"PDF okuma hatasi: {e}")
        return text.strip()

    def _parse_ai_json(self, response: str) -> dict:
        try:
            json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {"raw": response}
        except (json.JSONDecodeError, AttributeError):
            return {"raw": response}

    def _get_db(self):
        if self.db_manager:
            return self.db_manager
        try:
            from src.database.sqlite_adapter import get_database_manager
            return get_database_manager()
        except Exception:
            return None

    def _save_invoice_to_db(self, invoice_data: dict) -> Optional[int]:
        db = self._get_db()
        if not db:
            return None
        try:
            inv_no = invoice_data.get("fatura_no") or invoice_data.get("invoice_number") or f"TH-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            inv_type = invoice_data.get("fatura_turu") or invoice_data.get("invoice_type", "Alis")
            inv_date = invoice_data.get("tarih") or invoice_data.get("date", datetime.now().strftime("%d.%m.%Y"))
            sub_total = float(invoice_data.get("ara_toplam") or invoice_data.get("sub_total", 0))
            vat_total = float(invoice_data.get("kdv_toplam") or invoice_data.get("vat_total", 0))
            grand_total = float(invoice_data.get("genel_toplam") or invoice_data.get("total", 0))

            sql = """INSERT INTO Invoices (InvoiceNumber, InvoiceType, InvoiceDate, SubTotal, VATAmount, TotalAmount, Notes, CreatedDate)
                     VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))"""
            params = (inv_no, inv_type, inv_date, sub_total, vat_total, grand_total,
                      json.dumps(invoice_data, ensure_ascii=False))
            db.execute_query(sql, params, fetch=False)
            conn = db.get_connection()
            inv_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.close()

            urunler = invoice_data.get("urunler") or invoice_data.get("line_items", [])
            for i, item in enumerate(urunler):
                desc = item.get("urun_adi") or item.get("description", "")
                qty = float(item.get("miktar") or item.get("quantity", 1))
                unit = item.get("birim") or item.get("unit", "Adet")
                price = float(item.get("birim_fiyat") or item.get("unit_price", 0))
                vat_rate = float(item.get("kdv_orani") or item.get("vat_rate", 18))
                vat_amt = float(item.get("toplam") or item.get("total", 0)) * vat_rate / (100 + vat_rate) if vat_rate else 0
                net_amt = float(item.get("toplam") or item.get("total", 0)) - vat_amt
                total_amt = float(item.get("toplam") or item.get("total", 0))

                detail_sql = """INSERT INTO InvoiceDetails (InvoiceID, LineNumber, Description, Quantity, Unit, UnitPrice, NetAmount, VATRate, VATAmount, TotalAmount)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
                db.execute_query(detail_sql, (inv_id, i + 1, desc, qty, unit, price, net_amt, vat_rate, vat_amt, total_amt), fetch=False)

            return inv_id
        except Exception as e:
            if self.logger:
                self.logger.error(f"Fatura kayit hatasi: {e}")
            return None

    def analyze_receipt(self, image_path_or_bytes: Union[str, bytes, Path]) -> dict:
        text = self._extract_text_from_image(image_path_or_bytes)
        if not text:
            return {"error": "Makbuzdan metin cikarilamadi"}

        prompt = f"""
Sen bir muhasebe uzmani AI asistanisin. Asagidaki makbuz/fis metnini analiz et ve JSON formatinda cikti ver.

Makbuz Metni:
{text}

Su formatta JSON cikti ver (sadece JSON, baska metin yok):
{{
    "fatura_turu": "Alis",
    "tarih": "GG.AA.YYYY",
    "cari_unvan": "isletme adi",
    "urunler": [
        {{"urun_adi": "...", "miktar": sayi, "birim": "...", "birim_fiyat": sayi, "kdv_orani": sayi, "toplam": sayi}}
    ],
    "ara_toplam": sayi,
    "kdv_toplam": sayi,
    "genel_toplam": sayi
}}
"""
        response = self._call_gemini(prompt)
        result = self._parse_ai_json(response)
        if "raw" not in result:
            self._save_invoice_to_db(result)
        return result

    def analyze_invoice_pdf(self, pdf_path_or_bytes: Union[str, bytes, Path]) -> dict:
        text = self._extract_text_from_pdf(pdf_path_or_bytes)
        if not text:
            return {"error": "PDF'den metin cikarilamadi"}

        prompt = f"""
Sen bir muhasebe uzmani AI asistanisin. Asagidaki fatura metnini analiz et ve JSON formatinda cikti ver.

Fatura Metni:
{text}

Su formatta JSON cikti ver (sadece JSON, baska metin yok):
{{
    "fatura_turu": "Alis" veya "Satis",
    "fatura_no": "fatura numarasi",
    "tarih": "GG.AA.YYYY",
    "cari_unvan": "musteri/tedarikci adi",
    "vergi_no": "vergi numarasi",
    "vergi_dairesi": "vergi dairesi",
    "urunler": [
        {{"urun_adi": "...", "miktar": sayi, "birim": "...", "birim_fiyat": sayi, "kdv_orani": sayi, "toplam": sayi}}
    ],
    "ara_toplam": sayi,
    "kdv_toplam": sayi,
    "genel_toplam": sayi
}}
"""
        response = self._call_gemini(prompt)
        result = self._parse_ai_json(response)
        if "raw" not in result:
            self._save_invoice_to_db(result)
        return result

    def analyze_bank_statement(self, csv_path_or_text: Union[str, bytes, Path]) -> List[dict]:
        transactions = []
        try:
            if HAS_PANDAS:
                if isinstance(csv_path_or_text, bytes):
                    df = pd.read_csv(io.BytesIO(csv_path_or_text))
                elif isinstance(csv_path_or_text, (str, Path)) and Path(csv_path_or_text).exists():
                    df = pd.read_csv(csv_path_or_text)
                else:
                    df = pd.read_csv(io.StringIO(csv_path_or_text))
                transactions = df.to_dict(orient="records")
            else:
                if isinstance(csv_path_or_text, bytes):
                    content = csv_path_or_text.decode("utf-8-sig")
                elif isinstance(csv_path_or_text, (str, Path)) and Path(csv_path_or_text).exists():
                    with open(csv_path_or_text, "r", encoding="utf-8-sig") as f:
                        content = f.read()
                else:
                    content = csv_path_or_text
                reader = csv.DictReader(io.StringIO(content))
                transactions = [row for row in reader]
        except Exception as e:
            if self.logger:
                self.logger.error(f"Dekont okuma hatasi: {e}")
        return transactions

    def extract_transactions(self, raw_text: str) -> List[dict]:
        prompt = f"""
Asagidaki ham metinden finansal islemleri ayikla ve JSON array olarak cikar.

Metin:
{raw_text}

Her bir islem su formatta olmali:
{{
    "tarih": "GG.AA.YYYY",
    "aciklama": "...",
    "tutar": sayi,
    "tur": "Gelir" veya "Gider",
    "kategori": "ise en uygun kategori"
}}

Sadece JSON array cikisi ver:
"""
        response = self._call_gemini(prompt)
        try:
            array_match = re.search(r"\[.*\]", response, re.DOTALL)
            if array_match:
                return json.loads(array_match.group())
            return [{"raw": response}]
        except (json.JSONDecodeError, AttributeError):
            return [{"raw": response}]

    def categorize_transaction(self, description: str, amount: float) -> dict:
        prompt = f"""
Asagidaki islemi analiz ederek en uygun muhasebe kategorisini belirle.

Islem: {description}
Tutar: {amount} TL

Su formatta JSON cikisi ver (sadece JSON):
{{
    "kategori": "kategori adi",
    "hesap_kodu": "XXX",
    "aciklama": "...",
    "guven_orani": 0-100 arasi sayi
}}
"""
        response = self._call_gemini(prompt)
        return self._parse_ai_json(response)

    def bulk_analyze(self, file_paths: List[Union[str, Path]], progress_callback: Optional[Callable[[int, int], None]] = None) -> List[dict]:
        results = []
        total = len(file_paths)
        for idx, fp in enumerate(file_paths):
            fp = Path(fp)
            try:
                ext = fp.suffix.lower()
                if ext in (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"):
                    result = self.analyze_receipt(fp)
                elif ext == ".pdf":
                    result = self.analyze_invoice_pdf(fp)
                elif ext == ".csv":
                    txns = self.analyze_bank_statement(fp)
                    result = {"file": fp.name, "transactions": txns, "count": len(txns)}
                else:
                    with open(fp, "r", encoding="utf-8") as f:
                        content = f.read()
                    result = self.extract_transactions(content)
                results.append({"file": fp.name, "success": True, "data": result})
            except Exception as e:
                results.append({"file": fp.name, "success": False, "error": str(e)})

            if progress_callback:
                progress_callback(idx + 1, total)

        return results

    def generate_invoice(self, invoice_data: dict) -> Optional[bytes]:
        try:
            from fpdf import FPDF

            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)

            pdf.set_font("Helvetica", "B", 18)
            pdf.cell(0, 12, "FATURA", new_x="LMARGIN", new_y="NEXT", align="C")
            pdf.ln(5)

            pdf.set_font("Helvetica", "", 10)
            inv_no = invoice_data.get("fatura_no") or invoice_data.get("invoice_number", "-------")
            inv_date = invoice_data.get("tarih") or invoice_data.get("date", datetime.now().strftime("%d.%m.%Y"))
            customer = invoice_data.get("cari_unvan") or invoice_data.get("customer", "-------")
            pdf.cell(0, 6, f"Fatura No: {inv_no}", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 6, f"Tarih: {inv_date}", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 6, f"Musteri: {customer}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(5)

            col_w = [60, 20, 20, 30, 30, 30]
            headers = ["Aciklama", "Miktar", "Birim", "Birim Fiyat", "KDV %", "Toplam"]
            pdf.set_font("Helvetica", "B", 9)
            for hw, hd in zip(col_w, headers):
                pdf.cell(hw, 8, hd, border=1, align="C")
            pdf.ln()

            pdf.set_font("Helvetica", "", 9)
            urunler = invoice_data.get("urunler") or invoice_data.get("line_items", [])
            for item in urunler:
                desc = item.get("urun_adi") or item.get("description", "")
                qty = str(item.get("miktar") or item.get("quantity", 1))
                unit = item.get("birim") or item.get("unit", "Adet")
                price = f"{float(item.get('birim_fiyat') or item.get('unit_price', 0)):.2f}"
                vat = f"%{item.get('kdv_orani') or item.get('vat_rate', 18)}"
                total = f"{float(item.get('toplam') or item.get('total', 0)):.2f}"
                for hw, val in zip(col_w, [desc, qty, unit, price, vat, total]):
                    pdf.cell(hw, 7, val, border=1, align="C")
                pdf.ln()

            pdf.ln(5)
            pdf.set_font("Helvetica", "B", 10)
            grand_total = invoice_data.get("genel_toplam") or invoice_data.get("total", 0)
            pdf.cell(0, 8, f"Genel Toplam: {float(grand_total):.2f} TL", new_x="LMARGIN", new_y="NEXT", align="R")

            return pdf.output()
        except Exception as e:
            if self.logger:
                self.logger.error(f"PDF olusturma hatasi: {e}")
            return None

    def extract_custom_field(self, text: str, field_prompt: str) -> dict:
        full_prompt = f"""
Asagidaki metinden istenen alani cikar.

Metin:
{text}

Istenen alan:
{field_prompt}

Sadece JSON formatinda cikis ver:
{{{{
    "field_name": "alan adi",
    "field_value": "cikarilan deger",
    "confidence": 0-100 arasi guven puani
}}}}
"""
        response = self._call_gemini(full_prompt)
        return self._parse_ai_json(response)


taxhacker = TaxHackerAdapter()

def get_taxhacker():
    return taxhacker
