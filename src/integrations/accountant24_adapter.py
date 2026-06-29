"""
Accountant24 entegrasyon modulu - dogal dil ile muhasebe kaydi
Plain-text, AI destekli, cift tarafli kayit sistemi
"""

import csv
import io
import json
import os
import re
import tempfile
from datetime import datetime, date
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"


class Accountant24Adapter:
    """Accountant24 entegrasyonu - dogal dil ile muhasebe kaydi"""

    def __init__(self, main_app=None, db_manager=None):
        self.main_app = main_app
        self.db_manager = db_manager
        self.api_key = GEMINI_API_KEY
        self.api_url = GEMINI_API_URL
        self.logger = self._setup_logger()

    def _setup_logger(self):
        try:
            from src.utils.logger import setup_logger as sl
            return sl("Accountant24")
        except Exception:
            import logging
            logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            return logging.getLogger("Accountant24")

    def _call_gemini(self, prompt: str) -> str:
        try:
            import urllib.request
            import urllib.parse

            data = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.1,
                    "topK": 1,
                    "topP": 1,
                    "maxOutputTokens": 8192,
                },
            }

            req = urllib.request.Request(
                self.api_url,
                data=json.dumps(data).encode(),
                headers={
                    "Content-Type": "application/json",
                    "X-Goog-Api-Key": self.api_key
                },
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

    def _parse_ai_json_array(self, response: str) -> list:
        try:
            array_match = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", response, re.DOTALL)
            if array_match:
                return json.loads(array_match.group(1))
            array_match = re.search(r"\[.*\]", response, re.DOTALL)
            if array_match:
                return json.loads(array_match.group())
            return [{"raw": response}]
        except (json.JSONDecodeError, AttributeError):
            return [{"raw": response}]

    def _get_db(self):
        if self.db_manager:
            return self.db_manager
        try:
            from src.database.sqlite_adapter import get_database_manager
            return get_database_manager()
        except Exception:
            return None

    def _fmt_date(self, d=None):
        if d is None:
            d = date.today()
        if isinstance(d, str):
            return d
        return d.strftime("%Y-%m-%d")

    def _next_voucher_no(self):
        db = self._get_db()
        if not db:
            return f"ATH-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        try:
            rows = db.execute_query(
                "SELECT VoucherNumber FROM JournalEntries WHERE VoucherNumber LIKE 'ATH-%' ORDER BY JournalEntryID DESC LIMIT 1"
            )
            if rows:
                last = rows[0]["VoucherNumber"]
                seq = int(last.split("-")[-1]) + 1
            else:
                seq = 1
            return f"ATH-{datetime.now().strftime('%Y%m%d')}-{seq:04d}"
        except Exception:
            return f"ATH-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def log_transaction(self, natural_language_text: str) -> dict:
        """Log a transaction using natural language
        Example: "kirtasiyeye 150 tl kredi karti ile oldu" -> Journal Entry
        """
        rules = self._load_rules()
        rules_text = ""
        if rules:
            rules_text = "Kullanabilecegin kategorizasyon kurallari:\n" + "\n".join(
                f"- '{r['pattern']}' -> {r['category']} (Hesap: {r['account_code']})"
                for r in rules
            )

        accounts = self._get_accounts_context()
        prompt = f"""
Sen bir muhasebe asistanisin. Kullanicinin dogal dildeki istegini analiz ederek muhasebe kaydi olustur.

{rules_text}

Mevcut hesaplar:
{accounts}

Kullanici: {natural_language_text}

Su formatta JSON cikti ver (sadece JSON):
{{
    "tarih": "YYYY-MM-DD",
    "aciklama": "islem aciklamasi",
    "islem_turu": "Gelir" veya "Gider",
    "tutar": sayi,
    "kategori": "kategori adi",
    "odeme_yontemi": "nakit/kredi karti/banka/havale",
    "borc_hesap_kodu": "XXX",
    "alacak_hesap_kodu": "XXX",
    "cari_kodu": "(varsa cari hesap kodu, yoksa bos)",
    "etiketler": ["etiket1", "etiket2"]
}}
"""
        response = self._call_gemini(prompt)
        result = self._parse_ai_json(response)

        if "raw" not in result:
            self._create_journal_entry(result)

        return result

    def _get_accounts_context(self) -> str:
        db = self._get_db()
        if not db:
            return ""
        try:
            rows = db.execute_query(
                "SELECT AccountCode, AccountName, AccountType FROM ChartOfAccounts WHERE IsActive = 1 ORDER BY AccountCode"
            )
            return "\n".join(f"  {r['AccountCode']} - {r['AccountName']} ({r['AccountType']})" for r in rows[:50])
        except Exception:
            return ""

    def _create_journal_entry(self, data: dict) -> Optional[int]:
        db = self._get_db()
        if not db:
            return None
        try:
            voucher_no = self._next_voucher_no()
            t_date = data.get("tarih", self._fmt_date())
            desc = data.get("aciklama", "Accountant24 kaydi")
            amount = float(data.get("tutar", 0))
            debit_code = data.get("borc_hesap_kodu", "100")
            credit_code = data.get("alacak_hesap_kodu", "320")

            sql = """INSERT INTO JournalEntries (VoucherNumber, VoucherDate, Description, TotalDebit, TotalCredit, IsBalanced, IsPosted, DocumentType, CreatedDate)
                     VALUES (?, ?, ?, ?, ?, 1, 1, 'Accountant24', datetime('now','localtime'))"""
            db.execute_query(sql, (voucher_no, t_date, desc, amount, amount), fetch=False)
            conn = db.get_connection()
            je_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.close()

            debit_account = self._resolve_account(debit_code)
            credit_account = self._resolve_account(credit_code)

            detail_sql = """INSERT INTO JournalEntryDetails (JournalEntryID, LineNumber, AccountID, Description, DebitAmount, CreditAmount, DebitAmountLocal, CreditAmountLocal)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
            db.execute_query(detail_sql, (je_id, 1, debit_account, desc, amount, 0, amount, 0), fetch=False)
            db.execute_query(detail_sql, (je_id, 2, credit_account, desc, 0, amount, 0, amount), fetch=False)

            return je_id
        except Exception as e:
            if self.logger:
                self.logger.error(f"Yevmiye kaydi olusturma hatasi: {e}")
            return None

    def _resolve_account(self, code: str) -> int:
        db = self._get_db()
        if not db:
            return 1
        try:
            rows = db.execute_query("SELECT AccountID FROM ChartOfAccounts WHERE AccountCode = ?", (code,))
            if rows:
                return rows[0]["AccountID"]
            rows = db.execute_query("SELECT AccountID FROM ChartOfAccounts ORDER BY AccountID LIMIT 1")
            return rows[0]["AccountID"] if rows else 1
        except Exception:
            return 1

    def import_statement(self, csv_text_or_path: Union[str, bytes, Path], bank_name: str = "") -> list:
        """Import bank statement and auto-create journal entries"""
        try:
            if isinstance(csv_text_or_path, bytes):
                content = csv_text_or_path.decode("utf-8-sig")
            elif isinstance(csv_text_or_path, (str, Path)) and Path(csv_text_or_path).exists():
                with open(csv_text_or_path, "r", encoding="utf-8-sig") as f:
                    content = f.read()
            else:
                content = csv_text_or_path

            reader = csv.DictReader(io.StringIO(content))
            rows = list(reader)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Dekont okuma hatasi: {e}")
            return []

        if not rows:
            return []

        sample = json.dumps(rows[:3], ensure_ascii=False, indent=2)
        accounts = self._get_accounts_context()
        rules = self._load_rules()
        rules_text = ""
        if rules:
            rules_text = "Kurallar:\n" + "\n".join(
                f"- '{r['pattern']}' -> {r['category']} ({r['account_code']})"
                for r in rules
            )

        prompt = f"""
Asagidaki banka hesap hareketlerini analiz et ve her biri icin yevmiye kaydi bilgisi cikar.

Banka: {bank_name or "Belirtilmemis"}

{rules_text}

Mevcut hesaplar:
{accounts}

Hareketler (ornek):
{sample}

Her hareket icin su formatta JSON array cikti ver (sadece JSON):
[
    {{
        "tarih": "YYYY-MM-DD",
        "aciklama": "islem aciklamasi",
        "tutar": sayi,
        "islem_turu": "Gelir" veya "Gider",
        "kategori": "kategori",
        "borc_hesap_kodu": "XXX",
        "alacak_hesap_kodu": "XXX"
    }}
]
"""
        response = self._call_gemini(prompt)
        transactions = self._parse_ai_json_array(response)

        created = []
        for txn in transactions:
            if "raw" not in txn:
                je_id = self._create_journal_entry(txn)
                txn["journal_entry_id"] = je_id
                created.append(txn)
        return created

    def ask_question(self, question: str) -> str:
        """Answer financial questions in natural language
        Example: "bu ay ne kadar harcadim?" -> "Bu ay toplam 45.230 TL harcadiniz."
        """
        db = self._get_db()
        context = ""
        if db:
            try:
                today = date.today()
                first_day = today.replace(day=1)
                month_start = self._fmt_date(first_day)
                month_end = self._fmt_date(today)

                rows = db.execute_query(
                    """SELECT COALESCE(SUM(je.TotalDebit), 0) as toplam_gider
                       FROM JournalEntries je
                       WHERE je.VoucherDate >= ? AND je.VoucherDate <= ?
                       AND je.Description NOT LIKE '%Acilis%'""",
                    (month_start, month_end),
                )
                ay_harcama = rows[0]["toplam_gider"] if rows else 0

                rows = db.execute_query(
                    """SELECT COALESCE(SUM(c.Amount), 0) as toplam_masraf
                       FROM CashMovements c
                       WHERE c.MovementType = 'Cikis'
                       AND c.MovementDate >= ? AND c.MovementDate <= ?""",
                    (month_start, month_end),
                )
                ay_kasa_cikis = rows[0]["toplam_masraf"] if rows else 0

                rows = db.execute_query(
                    "SELECT COALESCE(SUM(CurrentBalance), 0) as toplam FROM CashRegisters WHERE IsActive = 1"
                )
                kasa_bakiye = rows[0]["toplam"] if rows else 0

                rows = db.execute_query(
                    "SELECT COALESCE(SUM(CurrentBalance), 0) as toplam FROM Banks WHERE IsActive = 1"
                )
                banka_bakiye = rows[0]["toplam"] if rows else 0

                rows = db.execute_query(
                    "SELECT COUNT(*) as adet FROM Invoices WHERE InvoiceType = 'Satis' AND IsPosted = 1"
                )
                fatura_adet = rows[0]["adet"] if rows else 0

                rows = db.execute_query(
                    "SELECT COUNT(*) as adet FROM CurrentAccounts WHERE IsActive = 1"
                )
                cari_adet = rows[0]["adet"] if rows else 0

                context = f"""
Mevcut finansal durum:
- Bu ayki yevmiye toplami: {ay_harcama:,.2f} TL
- Bu ayki kasa cikis: {ay_kasa_cikis:,.2f} TL
- Kasa bakiyesi: {kasa_bakiye:,.2f} TL
- Banka bakiyesi: {banka_bakiye:,.2f} TL
- Kesinlesmis satis fatura sayisi: {fatura_adet}
- Aktif cari hesap sayisi: {cari_adet}
"""
            except Exception as e:
                context = f"(Finansal veriler alinamadi: {e})"

        prompt = f"""
Sen bir muhasebe asistanisin. Kullanicinin sorusuna finansal verilere dayanarak Turkiye Turkcesi ile cevap ver.

{context}

Kullanici sorusu: {question}

Cevap kisa, oz ve bilgilendirici olsun. Sayilari Turkce formatinda (1.234,56) goster.
"""
        response = self._call_gemini(prompt)
        return response.strip() or "Uzgunum, sorunuzu anlayamadim."

    def get_spending_summary(self, period: str = "this-month") -> str:
        """Get spending summary for a period"""
        db = self._get_db()
        if not db:
            return "Veritabanina erisilemiyor."

        today = date.today()

        if period == "this-month":
            start = today.replace(day=1)
            end = today
            label = "bu ay"
        elif period == "last-month":
            first_this = today.replace(day=1)
            end = first_this - __import__("datetime").timedelta(days=1)
            start = end.replace(day=1)
            label = "gecen ay"
        elif period == "this-year":
            start = today.replace(month=1, day=1)
            end = today
            label = "bu yil"
        elif period == "last-year":
            start = today.replace(year=today.year - 1, month=1, day=1)
            end = today.replace(year=today.year - 1, month=12, day=31)
            label = "gecen yil"
        else:
            start = today.replace(day=1)
            end = today
            label = "bu ay"

        try:
            rows = db.execute_query(
                """SELECT COALESCE(SUM(TotalDebit), 0) as toplam
                   FROM JournalEntries
                   WHERE VoucherDate >= ? AND VoucherDate <= ?""",
                (self._fmt_date(start), self._fmt_date(end)),
            )
            toplam = rows[0]["toplam"] if rows else 0

            rows = db.execute_query(
                """SELECT a.AccountName, COALESCE(SUM(jd.DebitAmount), 0) as tutar
                   FROM JournalEntryDetails jd
                   JOIN ChartOfAccounts a ON jd.AccountID = a.AccountID
                   JOIN JournalEntries je ON jd.JournalEntryID = je.JournalEntryID
                   WHERE je.VoucherDate >= ? AND je.VoucherDate <= ?
                   AND a.AccountType = 'Gider'
                   GROUP BY a.AccountName ORDER BY tutar DESC LIMIT 10""",
                (self._fmt_date(start), self._fmt_date(end)),
            )
            detay = rows if rows else []

            lines = [f"{label.capitalize()} Harcama Ozeti:"]
            lines.append(f"Toplam harcama: {toplam:,.2f} TL")
            if detay:
                lines.append("Kategorilere gore dagilim:")
                for r in detay:
                    lines.append(f"  - {r['AccountName']}: {r['tutar']:,.2f} TL")
            return "\n".join(lines)
        except Exception as e:
            return f"Ozet alinamadi: {e}"

    def get_balance_report(self) -> str:
        """Get current balance report in natural language"""
        db = self._get_db()
        if not db:
            return "Veritabanina erisilemiyor."

        try:
            kasalar = db.execute_query(
                "SELECT CashRegisterName, CurrentBalance FROM CashRegisters WHERE IsActive = 1"
            )
            bankalar = db.execute_query(
                "SELECT BankName, IBAN, CurrentBalance FROM Banks WHERE IsActive = 1"
            )
            rows = db.execute_query(
                "SELECT COUNT(*) as adet, COALESCE(SUM(TotalAmount - PaidAmount), 0) as toplam FROM Invoices WHERE InvoiceType = 'Alis' AND IsPosted = 1"
            )
            alis_borc = rows[0]["toplam"] if rows else 0
            rows = db.execute_query(
                "SELECT COUNT(*) as adet, COALESCE(SUM(TotalAmount - PaidAmount), 0) as toplam FROM Invoices WHERE InvoiceType = 'Satis' AND IsPosted = 1"
            )
            satis_alacak = rows[0]["toplam"] if rows else 0

            lines = ["Bakiye Raporu", "=" * 30]
            if kasalar:
                lines.append("Kasalar:")
                for k in kasalar:
                    lines.append(f"  {k['CashRegisterName']}: {k['CurrentBalance']:,.2f} TL")
            if bankalar:
                lines.append("Bankalar:")
                for b in bankalar:
                    iban = b['IBAN'] or ""
                    lines.append(f"  {b['BankName']} ({iban[-6:]}): {b['CurrentBalance']:,.2f} TL")
            lines.append(f"Tedarikcilere borc: {alis_borc:,.2f} TL")
            lines.append(f"Musterilerden alacak: {satis_alacak:,.2f} TL")
            return "\n".join(lines)
        except Exception as e:
            return f"Rapor alinamadi: {e}"

    def teach_rule(self, pattern: str, category: str, account_code: str):
        """Teach the agent a new categorization rule"""
        db = self._get_db()
        if not db:
            return False
        try:
            rules = self._load_rules()
            rules.append({"pattern": pattern, "category": category, "account_code": account_code})
            self._save_rules(rules)
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Kural kayit hatasi: {e}")
            return False

    def _load_rules(self) -> list:
        db = self._get_db()
        if not db:
            return []
        try:
            rows = db.execute_query(
                "SELECT SettingValue FROM SystemSettings WHERE SettingKey = 'accountant24_rules'"
            )
            if rows and rows[0]["SettingValue"]:
                return json.loads(rows[0]["SettingValue"])
            return []
        except Exception:
            return []

    def _save_rules(self, rules: list):
        db = self._get_db()
        if not db:
            return
        try:
            val = json.dumps(rules, ensure_ascii=False)
            rows = db.execute_query(
                "SELECT SettingID FROM SystemSettings WHERE SettingKey = 'accountant24_rules'"
            )
            if rows:
                db.execute_query(
                    "UPDATE SystemSettings SET SettingValue = ?, UpdatedDate = datetime('now','localtime') WHERE SettingKey = 'accountant24_rules'",
                    (val,),
                    fetch=False,
                )
            else:
                db.execute_query(
                    "INSERT INTO SystemSettings (SettingKey, SettingValue, Description) VALUES (?, ?, 'Accountant24 kategorizasyon kurallari')",
                    ("accountant24_rules", val),
                    fetch=False,
                )
        except Exception as e:
            if self.logger:
                self.logger.error(f"Kural kayit hatasi: {e}")

    def export_to_text(self, output_dir: Optional[str] = None) -> str:
        """Export ledger data as plain text files (hledger-like format)"""
        db = self._get_db()
        if not db:
            return "Veritabanina erisilemiyor."

        if output_dir:
            out = Path(output_dir)
        else:
            out = Path(tempfile.mkdtemp(prefix="accountant24_"))
        out.mkdir(parents=True, exist_ok=True)

        try:
            journal_path = out / "journal.txt"
            with open(journal_path, "w", encoding="utf-8") as f:
                f.write("; Accountant24 - Hledger Formatli Yevmiye Defteri\n")
                f.write(f"; Olusturma: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
                f.write("\n")

                entries = db.execute_query(
                    """SELECT je.*, u1.FullName as CreatorName, u2.FullName as ApproverName
                       FROM JournalEntries je
                       LEFT JOIN Users u1 ON je.CreatedBy = u1.UserID
                       LEFT JOIN Users u2 ON je.ApprovedBy = u2.UserID
                       ORDER BY je.VoucherDate, je.JournalEntryID"""
                )

                for entry in entries:
                    f.write(f"{entry['VoucherDate']} {entry['Description'] or '(aciklama yok)'}\n")
                    f.write(f"    ; Voucher: {entry['VoucherNumber']}\n")
                    if entry.get("DocumentType"):
                        f.write(f"    ; DocumentType: {entry['DocumentType']}\n")

                    details = db.execute_query(
                        """SELECT jd.*, a.AccountCode, a.AccountName, c.CurrentAccountName
                           FROM JournalEntryDetails jd
                           JOIN ChartOfAccounts a ON jd.AccountID = a.AccountID
                           LEFT JOIN CurrentAccounts c ON jd.CurrentAccountID = c.CurrentAccountID
                           WHERE jd.JournalEntryID = ?
                           ORDER BY jd.LineNumber""",
                        (entry["JournalEntryID"],),
                    )

                    for detail in details:
                        account_ref = f"{detail['AccountCode']} {detail['AccountName']}"
                        if detail.get("CurrentAccountName"):
                            account_ref += f" [{detail['CurrentAccountName']}]"
                        debit = detail["DebitAmount"] or 0
                        credit = detail["CreditAmount"] or 0
                        desc = detail.get("Description") or ""
                        if desc:
                            f.write(f"    {account_ref}  {debit:>10.2f} TL  {credit:>10.2f} TL  ; {desc}\n")
                        else:
                            f.write(f"    {account_ref}  {debit:>10.2f} TL  {credit:>10.2f} TL\n")

                    f.write(f"    ; Balance: {entry['TotalDebit']:,.2f} TL\n")
                    f.write("\n")

            accounts_path = out / "accounts.txt"
            with open(accounts_path, "w", encoding="utf-8") as f:
                f.write("; Hesap Plani\n")
                f.write("\n")
                accounts = db.execute_query(
                    "SELECT * FROM ChartOfAccounts WHERE IsActive = 1 ORDER BY AccountCode"
                )
                for acc in accounts:
                    f.write(f"{acc['AccountCode']} {acc['AccountName']}\n")
                    f.write(f"    ; Type: {acc['AccountType']}\n")
                    if acc.get("AccountGroup"):
                        f.write(f"    ; Group: {acc['AccountGroup']}\n")
                    f.write("\n")

            balances_path = out / "balances.txt"
            with open(balances_path, "w", encoding="utf-8") as f:
                f.write("; Bakiye Bilgileri\n")
                f.write(f"; Tarih: {self._fmt_date()}\n")
                f.write("\n")
                f.write(";; Kasalar\n")
                kasalar = db.execute_query(
                    "SELECT CashRegisterName, CurrencyCode, CurrentBalance FROM CashRegisters WHERE IsActive = 1"
                )
                for k in kasalar:
                    f.write(f"  {k['CashRegisterName']}:  {k['CurrentBalance']:,.2f} {k['CurrencyCode']}\n")
                f.write("\n;; Bankalar\n")
                bankalar = db.execute_query(
                    "SELECT BankName, CurrencyCode, CurrentBalance FROM Banks WHERE IsActive = 1"
                )
                for b in bankalar:
                    f.write(f"  {b['BankName']}:  {b['CurrentBalance']:,.2f} {b['CurrencyCode']}\n")

            return str(out)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Disari aktarma hatasi: {e}")
            return ""


accountant24 = Accountant24Adapter()


def get_accountant24():
    return accountant24
