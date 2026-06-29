"""
FinRobot entegrasyon modulu - coklu ajan finans analizi
8 ozel ajan ile sirket analizi, DCF degerleme, risk degerlendirme ve raporlama
Kaynak: github.com/AI4Finance-Foundation/FinRobot
"""

import csv
import io
import json
import math
import os
import re
import tempfile
import textwrap
import traceback
from collections import defaultdict
from datetime import datetime, date
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"


class FinRobotAdapter:
    """FinRobot entegrasyonu - coklu ajan finans analizi

    Iki modda calisir:
    1. AI Mode (varsayilan) - Gemini API ile dogal dil analizi
    2. Computation Mode - Saf Python hesaplama (API gerektirmez)
    """

    def __init__(self, main_app=None, db_manager=None, ai_mode=True):
        self.main_app = main_app
        self.db_manager = db_manager
        self.ai_mode = ai_mode
        self.api_key = GEMINI_API_KEY
        self.api_url = GEMINI_API_URL
        self.logger = self._setup_logger()
        self._agent_chain_log = []

    def _setup_logger(self):
        try:
            from src.utils.logger import setup_logger as sl
            return sl("FinRobot")
        except Exception:
            import logging
            logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            return logging.getLogger("FinRobot")

    def _log_agent(self, agent_name: str, status: str, detail: str = ""):
        entry = {"ajan": agent_name, "durum": status, "detay": detail, "zaman": datetime.now().isoformat()}
        self._agent_chain_log.append(entry)
        if self.logger:
            self.logger.info(f"[{agent_name}] {status} - {detail}")

    # ------------------------------------------------------------------
    # AI Helpers
    # ------------------------------------------------------------------

    def _call_gemini(self, prompt: str) -> str:
        if not self.ai_mode:
            return ""
        try:
            import urllib.request
            import urllib.parse

            data = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.2,
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
            with urllib.request.urlopen(req, timeout=90) as resp:
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

    # ------------------------------------------------------------------
    # DB Helpers
    # ------------------------------------------------------------------

    def _get_db(self):
        if self.db_manager:
            return self.db_manager
        try:
            from src.database.sqlite_adapter import get_database_manager
            return get_database_manager()
        except Exception:
            return None

    def _query(self, sql: str, params: tuple = ()) -> list:
        db = self._get_db()
        if not db:
            return []
        try:
            return db.execute_query(sql, params) or []
        except Exception:
            return []

    def _fmt_date(self, d=None):
        if d is None:
            d = date.today()
        if isinstance(d, str):
            return d
        return d.strftime("%Y-%m-%d")

    def _tr_currency(self, value: float) -> str:
        return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def _fmt_pct(self, value: float) -> str:
        return f"%{value:+.2f}".replace(".", ",")

    # ==================================================================
    # 8 OZEL AJAN - FinRobot Multi-Agent Sistemi
    # ==================================================================

    # ------------------------------------------------------------------
    # Agent 1: DataCollector - Finansal verileri DB'den topla
    # ------------------------------------------------------------------

    def data_collector(self, company_data: Optional[Dict] = None) -> Dict:
        """Agent 1: DataCollector - Finansal verileri veritabanindan toplar"""
        self._log_agent("DataCollector", "calisiyor", "Finansal veriler toplaniyor")

        try:
            company_id = None
            if company_data:
                company_id = company_data.get("CompanyID") or company_data.get("sirket_id")

            q_firma = self._query("SELECT * FROM Companies WHERE IsActive = 1 ORDER BY CompanyID LIMIT 1")
            firma = q_firma[0] if q_firma else {}

            q_kasalar = self._query("SELECT * FROM CashRegisters WHERE IsActive = 1")
            q_bankalar = self._query("SELECT * FROM Banks WHERE IsActive = 1")
            q_cariler = self._query("SELECT * FROM CurrentAccounts WHERE IsActive = 1")

            q_hesaplar = self._query("SELECT * FROM ChartOfAccounts WHERE IsActive = 1 ORDER BY AccountCode")

            q_faturalar = self._query(
                "SELECT InvoiceType, COUNT(*) as adet, COALESCE(SUM(TotalAmount), 0) as toplam, "
                "COALESCE(SUM(PaidAmount), 0) as odenen FROM Invoices WHERE IsPosted = 1 GROUP BY InvoiceType"
            )

            q_yevmiye = self._query(
                "SELECT COUNT(*) as adet, COALESCE(SUM(TotalDebit), 0) as toplam FROM JournalEntries"
            )

            q_stok = self._query(
                "SELECT COUNT(*) as adet, COALESCE(SUM(CurrentStock), 0) as toplam FROM StockItems WHERE IsActive = 1"
            )

            q_personel = self._query("SELECT COUNT(*) as adet FROM Employees WHERE IsActive = 1")

            q_odeme = self._query(
                "SELECT COALESCE(SUM(TotalAmount - PaidAmount), 0) as alacak FROM Invoices "
                "WHERE InvoiceType = 'Satis' AND IsPosted = 1"
            )
            q_borc = self._query(
                "SELECT COALESCE(SUM(TotalAmount - PaidAmount), 0) as borc FROM Invoices "
                "WHERE InvoiceType = 'Alis' AND IsPosted = 1"
            )

            hesap_bakiyeleri = self._hesap_bakiyeleri()
            donem_verileri = self._donem_verileri()

            result = {
                "sirket": dict(firma) if firma else {},
                "kasalar": [dict(r) for r in q_kasalar],
                "bankalar": [dict(r) for r in q_bankalar],
                "cariler": [dict(r) for r in q_cariler],
                "hesaplar": [dict(r) for r in q_hesaplar],
                "faturalar": [dict(r) for r in q_faturalar],
                "yevmiye": dict(q_yevmiye[0]) if q_yevmiye else {},
                "stok": dict(q_stok[0]) if q_stok else {},
                "personel": dict(q_personel[0]) if q_personel else {},
                "alacak": float(q_odeme[0]["alacak"]) if q_odeme else 0,
                "borc": float(q_borc[0]["borc"]) if q_borc else 0,
                "hesap_bakiyeleri": hesap_bakiyeleri,
                "donem_verileri": donem_verileri,
                "toplama_tarihi": self._fmt_date(),
            }

            nakit = sum(float(r["CurrentBalance"]) for r in q_kasalar)
            bakiye = sum(float(r["CurrentBalance"]) for r in q_bankalar)
            result["toplam_nakit"] = nakit + bakiye

            self._log_agent("DataCollector", "tamam", f"{len(q_hesaplar)} hesap, {len(q_faturalar)} fatura grubu")
            return result

        except Exception as e:
            self._log_agent("DataCollector", "hata", str(e))
            return {"hata": str(e)}

    def _hesap_bakiyeleri(self) -> Dict:
        rows = self._query(
            """SELECT a.AccountCode, a.AccountName, a.AccountType,
                      COALESCE(SUM(COALESCE(jd.DebitAmount, 0) - COALESCE(jd.CreditAmount, 0)), 0) as bakiye
               FROM ChartOfAccounts a
               LEFT JOIN JournalEntryDetails jd ON a.AccountID = jd.AccountID
               WHERE a.IsActive = 1
               GROUP BY a.AccountID
               ORDER BY a.AccountCode"""
        )
        sonuc = {"donen_varlik": 0, "duran_varlik": 0, "kisa_vadeli_borc": 0, "uzun_vadeli_borc": 0, "ozkaynak": 0}
        for r in rows:
            b = float(r["bakiye"])
            tip = (r["AccountType"] or "")
            kod = (r["AccountCode"] or "")
            if kod.startswith("1"):
                sonuc["donen_varlik"] += b
            elif kod.startswith("2"):
                sonuc["duran_varlik"] += b
            elif kod.startswith("3"):
                sonuc["kisa_vadeli_borc"] += abs(b) if b < 0 else b
            elif kod.startswith("4"):
                sonuc["uzun_vadeli_borc"] += abs(b) if b < 0 else b
            elif kod.startswith("5"):
                sonuc["ozkaynak"] += b
        return sonuc

    def _donem_verileri(self) -> Dict:
        rows = self._query("""
            SELECT strftime('%Y-%m', VoucherDate) as donem,
                   COUNT(*) as kayit_sayisi,
                   COALESCE(SUM(TotalDebit), 0) as toplam_borc,
                   COALESCE(SUM(TotalCredit), 0) as toplam_alacak
            FROM JournalEntries
            WHERE VoucherDate >= date('now', '-1 year')
            GROUP BY donem ORDER BY donem
        """)
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Agent 2: FinancialAnalyzer - Finansal oranlari hesapla
    # ------------------------------------------------------------------

    def financial_analyzer(self, financial_data: Dict) -> Dict:
        """Agent 2: FinancialAnalyzer - Finansal oranlari hesaplar"""
        self._log_agent("FinancialAnalyzer", "calisiyor", "Finansal oranlar hesaplaniyor")

        try:
            bakiye = financial_data.get("hesap_bakiyeleri", {})
            faturalar = financial_data.get("faturalar", [])

            dv = float(bakiye.get("donen_varlik", 0))
            kvb = float(bakiye.get("kisa_vadeli_borc", 0))
            duran_v = float(bakiye.get("duran_varlik", 0))
            uzun_vb = float(bakiye.get("uzun_vadeli_borc", 0))
            ozkaynak = float(bakiye.get("ozkaynak", 0))
            toplam_varlik = dv + duran_v
            toplam_yukum = kvb + uzun_vb

            kasalar = financial_data.get("kasalar", [])
            bankalar = financial_data.get("bankalar", [])
            nakit_deger = sum(float(r["CurrentBalance"]) for r in kasalar) + sum(float(r["CurrentBalance"]) for r in bankalar)
            stok_rows = financial_data.get("stok", {})
            stok_deger = float(stok_rows.get("toplam", 0)) if isinstance(stok_rows, dict) else 0

            satis_faturalari = [f for f in faturalar if f.get("InvoiceType") == "Satis"]
            alis_faturalari = [f for f in faturalar if f.get("InvoiceType") == "Alis"]
            satis_toplam = sum(float(f.get("toplam", 0)) for f in satis_faturalari)
            alis_toplam = sum(float(f.get("toplam", 0)) for f in alis_faturalari)

            brut_kar = satis_toplam - alis_toplam
            faaliyet_kar = brut_kar * 0.7

            ratios = {}

            ratios["cari_oran"] = round(dv / kvb, 2) if kvb else 0
            ratios["likidite_orani"] = round((dv - stok_deger) / kvb, 2) if kvb else 0
            ratios["nakit_orani"] = round(nakit_deger / kvb, 2) if kvb else 0

            ratios["kaldirac_orani"] = round(toplam_yukum / toplam_varlik, 4) if toplam_varlik else 0
            ratios["borc_ozkaynak"] = round(toplam_yukum / ozkaynak, 2) if ozkaynak else 0

            ratios["aktif_karlilik_roa"] = round(brut_kar / toplam_varlik, 4) if toplam_varlik else 0
            ratios["ozsermaye_karliligi_roe"] = round(brut_kar / ozkaynak, 4) if ozkaynak else 0

            ratios["brut_kar_marj"] = round(brut_kar / satis_toplam, 4) if satis_toplam else 0
            ratios["net_kar_marj"] = round(brut_kar / satis_toplam, 4) if satis_toplam else 0
            ratios["faaliyet_kar_marj"] = round(faaliyet_kar / satis_toplam, 4) if satis_toplam else 0

            result = {
                "oranlar": ratios,
                "ozet": {
                    "donen_varlik": dv,
                    "duran_varlik": duran_v,
                    "toplam_varlik": toplam_varlik,
                    "kisa_vadeli_borc": kvb,
                    "uzun_vadeli_borc": uzun_vb,
                    "toplam_yukumluluk": toplam_yukum,
                    "ozkaynak": ozkaynak,
                    "satis_geliri": satis_toplam,
                    "alis_maliyeti": alis_toplam,
                    "brut_kar": brut_kar,
                    "nakit_mevcudu": nakit_deger,
                },
            }
            result["degerlendirme"] = self._ratio_degerlendirme(ratios)

            self._log_agent("FinancialAnalyzer", "tamam", f"{len(ratios)} oran hesaplandi")
            return result

        except Exception as e:
            self._log_agent("FinancialAnalyzer", "hata", str(e))
            return {"hata": str(e)}

    def _ratio_degerlendirme(self, ratios: Dict) -> Dict:
        deger = {}
        cr = ratios.get("cari_oran", 0)
        if cr >= 2:
            deger["cari_oran"] = {"durum": "iyi", "yorum": "Likidite durumu guclu"}
        elif cr >= 1.5:
            deger["cari_oran"] = {"durum": "orta", "yorum": "Likidite durumu yeterli"}
        elif cr >= 1:
            deger["cari_oran"] = {"durum": "zayif", "yorum": "Likidite durumu sinirda"}
        else:
            deger["cari_oran"] = {"durum": "riskli", "yorum": "Likidite durumu zayif"}

        lr = ratios.get("likidite_orani", 0)
        if lr >= 1:
            deger["likidite_orani"] = {"durum": "iyi", "yorum": "Asit-test orani yeterli"}
        else:
            deger["likidite_orani"] = {"durum": "dusuk", "yorum": "Stok bagimliligi yuksek"}

        bk = ratios.get("borc_ozkaynak", 0)
        if bk <= 1:
            deger["borc_ozkaynak"] = {"durum": "iyi", "yorum": "Dusuk kaldirac"}
        elif bk <= 2:
            deger["borc_ozkaynak"] = {"durum": "orta", "yorum": "Kaldirac seviyesi normal"}
        else:
            deger["borc_ozkaynak"] = {"durum": "yuksek", "yorum": "Yuksek kaldirac riski"}

        roa = ratios.get("aktif_karlilik_roa", 0)
        deger["aktif_karlilik_roa"] = {"durum": "pozitif" if roa > 0 else "negatif", "yorum": f"ROA: {self._fmt_pct(roa)}"}

        roe = ratios.get("ozsermaye_karliligi_roe", 0)
        deger["ozsermaye_karliligi_roe"] = {"durum": "pozitif" if roe > 0 else "negatif", "yorum": f"ROE: {self._fmt_pct(roe)}"}

        return deger

    # ------------------------------------------------------------------
    # Agent 3: ValuationAgent - DCF degerleme
    # ------------------------------------------------------------------

    def valuation_agent(self, company_data: Dict) -> Dict:
        """Agent 3: ValuationAgent - DCF degerleme ve carpan analizi"""
        self._log_agent("ValuationAgent", "calisiyor", "DCF degerleme hesaplaniyor")

        try:
            fin_data = company_data.get("finansal_veriler", company_data)
            ozet = fin_data.get("ozet", fin_data) if isinstance(fin_data, dict) else {}

            satis = float(ozet.get("satis_geliri", ozet.get("gelir", 0)))
            brut_kar = float(ozet.get("brut_kar", satis * 0.3))
            toplam_varlik = float(ozet.get("toplam_varlik", 0))
            ozkaynak = float(ozet.get("ozkaynak", 0))
            nakit = float(ozet.get("nakit_mevcudu", 0))

            fcf_marj = 0.15
            fcf_tahmini = satis * fcf_marj
            if fcf_tahmini == 0:
                fcf_tahmini = toplam_varlik * 0.08

            wacc = 0.12
            terminal_buyume = 0.03
            projeksiyon_yili = 5

            fcf_projeksiyon = []
            bugunku_deger = 0
            for yil in range(1, projeksiyon_yili + 1):
                fcf = fcf_tahmini * (1.05 ** yil)
                iskonto = wacc ** yil
                bd = fcf / ((1 + wacc) ** yil)
                fcf_projeksiyon.append({"yil": yil, "fcf": round(fcf, 2), "iskonto_faktoru": round(iskonto, 4), "bugunku_deger": round(bd, 2)})
                bugunku_deger += bd

            terminal_fcf = fcf_tahmini * (1.05 ** projeksiyon_yili)
            terminal_deger = terminal_fcf * (1 + terminal_buyume) / (wacc - terminal_buyume)
            terminal_bugunku_deger = terminal_deger / ((1 + wacc) ** projeksiyon_yili)

            isletme_degeri = bugunku_deger + terminal_bugunku_deger
            net_borc = max(0, float(ozet.get("toplam_yukumluluk", 0)) - nakit)
            ozkaynak_degeri = isletme_degeri - net_borc

            carpan_analizi = {}
            if satis:
                carpan_analizi["fd_satis"] = round(isletme_degeri / satis, 2) if satis else 0
            if brut_kar:
                carpan_analizi["fd_fvok"] = round(isletme_degeri / brut_kar, 2) if brut_kar else 0
            if ozkaynak:
                carpan_analizi["fd_defter"] = round(isletme_degeri / ozkaynak, 2)

            result = {
                "varsayimlar": {
                    "wacc": wacc,
                    "terminal_buyume": terminal_buyume,
                    "fcf_marj": fcf_marj,
                    "projeksiyon_donemi": projeksiyon_yili,
                },
                "fcf_projeksiyonu": fcf_projeksiyon,
                "terminal_deger": round(terminal_deger, 2),
                "terminal_bugunku_deger": round(terminal_bugunku_deger, 2),
                "isletme_degeri": round(isletme_degeri, 2),
                "net_borc": round(net_borc, 2),
                "ozkaynak_degeri": round(ozkaynak_degeri, 2),
                "carpan_analizi": carpan_analizi,
                "hisse_basi_deger": round(ozkaynak_degeri / 100000, 2) if ozkaynak_degeri > 0 else 0,
            }

            self._log_agent("ValuationAgent", "tamam", f"Isletme degeri: {self._tr_currency(isletme_degeri)} TL")
            return result

        except Exception as e:
            self._log_agent("ValuationAgent", "hata", str(e))
            return {"hata": str(e)}

    # ------------------------------------------------------------------
    # Agent 4: RiskAssessor - Risk degerlendirme
    # ------------------------------------------------------------------

    def risk_assessor(self, financial_data: Dict) -> Dict:
        """Agent 4: RiskAssessor - Likidite, borc ve karlilik riskleri"""
        self._log_agent("RiskAssessor", "calisiyor", "Risk skorlari hesaplaniyor")

        try:
            oranlar = {}
            if "oranlar" in financial_data:
                oranlar = financial_data["oranlar"]
            elif "finansal_veriler" in financial_data:
                fd = financial_data.get("finansal_veriler", {})
                oranlar = fd.get("oranlar", {})
            else:
                analyzer = self.financial_analyzer(financial_data)
                oranlar = analyzer.get("oranlar", {})

            likidite_skor = 0
            cr = oranlar.get("cari_oran", 0)
            if cr >= 2:
                likidite_skor = 10
            elif cr >= 1.5:
                likidite_skor = 7
            elif cr >= 1:
                likidite_skor = 4
            else:
                likidite_skor = 1

            lr = oranlar.get("likidite_orani", 0)
            if lr >= 1:
                likidite_skor += 2
            elif lr >= 0.5:
                likidite_skor += 1

            borc_skor = 0
            bk = oranlar.get("borc_ozkaynak", 0)
            if bk <= 0.5:
                borc_skor = 10
            elif bk <= 1:
                borc_skor = 8
            elif bk <= 2:
                borc_skor = 5
            elif bk <= 3:
                borc_skor = 3
            else:
                borc_skor = 1

            kaldirac = oranlar.get("kaldirac_orani", 0)
            if kaldirac <= 0.3:
                borc_skor += 2
            elif kaldirac <= 0.6:
                borc_skor += 1

            karlilik_skor = 0
            roa = oranlar.get("aktif_karlilik_roa", 0)
            if roa > 0.10:
                karlilik_skor = 10
            elif roa > 0.05:
                karlilik_skor = 7
            elif roa > 0:
                karlilik_skor = 4
            else:
                karlilik_skor = 1

            roe = oranlar.get("ozsermaye_karliligi_roe", 0)
            if roe > 0.20:
                karlilik_skor += 2
            elif roe > 0.10:
                karlilik_skor += 1

            nakit_skor = 0
            no = oranlar.get("nakit_orani", 0)
            if no >= 0.5:
                nakit_skor = 10
            elif no >= 0.2:
                nakit_skor = 6
            elif no >= 0.1:
                nakit_skor = 3
            else:
                nakit_skor = 1

            toplam_skor = (likidite_skor * 0.30 + borc_skor * 0.25 + karlilik_skor * 0.25 + nakit_skor * 0.20)
            max_skor = 10 * 0.30 + 12 * 0.25 + 12 * 0.25 + 10 * 0.20
            normalized = round((toplam_skor / max_skor) * 100, 1)

            if normalized >= 70:
                seviye = "Dusuk Risk"
                renk = "yesil"
            elif normalized >= 50:
                seviye = "Orta Risk"
                renk = "sari"
            elif normalized >= 30:
                seviye = "Yuksek Risk"
                renk = "turuncu"
            else:
                seviye = "Kritik Risk"
                renk = "kirmizi"

            result = {
                "genel_risk_skoru": normalized,
                "genel_risk_seviyesi": seviye,
                "renk_kodu": renk,
                "bilesenler": {
                    "likidite_riski": {"skor": likidite_skor, "max": 12, "yuzde": round(likidite_skor / 12 * 100, 1)},
                    "borc_riski": {"skor": borc_skor, "max": 12, "yuzde": round(borc_skor / 12 * 100, 1)},
                    "karlilik_riski": {"skor": karlilik_skor, "max": 12, "yuzde": round(karlilik_skor / 12 * 100, 1)},
                    "nakit_riski": {"skor": nakit_skor, "max": 10, "yuzde": round(nakit_skor / 10 * 100, 1)},
                },
                "detayli_analiz": {
                    "likidite": f"Cari Oran: {cr}, Likidite Orani: {lr}",
                    "borcluluk": f"Borc/Ozkaynak: {bk}, Kaldirac: {self._fmt_pct(kaldirac)}",
                    "karlilik": f"ROA: {self._fmt_pct(roa)}, ROE: {self._fmt_pct(roe)}",
                    "nakit_durumu": f"Nakit Orani: {no}",
                },
            }

            self._log_agent("RiskAssessor", "tamam", f"Risk skoru: {normalized} - {seviye}")
            return result

        except Exception as e:
            self._log_agent("RiskAssessor", "hata", str(e))
            return {"hata": str(e)}

    # ------------------------------------------------------------------
    # Agent 5: MarketAnalyst - Pazar analizi
    # ------------------------------------------------------------------

    def market_analyst(self, company_name: str = "", sector: str = "") -> Dict:
        """Agent 5: MarketAnalyst - Sektor ve pazar konumlandirma"""
        self._log_agent("MarketAnalyst", "calisiyor", f"Sektor analizi: {sector or 'genel'}")

        try:
            db = self._get_db()
            cari_sayisi = 0
            musteri_sayisi = 0
            tedarikci_sayisi = 0
            toplam_ciro = 0
            toplam_fatura = 0

            if db:
                cariler = self._query("SELECT CurrentAccountType, COUNT(*) as adet FROM CurrentAccounts WHERE IsActive = 1 GROUP BY CurrentAccountType")
                for c in cariler:
                    tip = c.get("CurrentAccountType", "")
                    if tip == "Musteri":
                        musteri_sayisi = c["adet"]
                    elif tip == "Tedarikci":
                        tedarikci_sayisi = c["adet"]
                cari_sayisi = musteri_sayisi + tedarikci_sayisi

                fatura = self._query("SELECT COUNT(*) as adet, COALESCE(SUM(TotalAmount), 0) as toplam FROM Invoices WHERE InvoiceType = 'Satis' AND IsPosted = 1")
                if fatura:
                    toplam_fatura = fatura[0]["adet"]
                    toplam_ciro = float(fatura[0]["toplam"])

            veri = {
                "sirket_adi": company_name or "Sirket",
                "sektor": sector or "Genel",
                "musteri_sayisi": musteri_sayisi,
                "tedarikci_sayisi": tedarikci_sayisi,
                "toplam_cari": cari_sayisi,
                "toplam_fatura": toplam_fatura,
                "toplam_ciro": toplam_ciro,
                "ortalama_fatura_tutari": round(toplam_ciro / toplam_fatura, 2) if toplam_fatura else 0,
            }

            pazar_payi_tahmini = "0.1% - 0.5%"
            rekabet_durumu = "Kucuk olcekli isletme"
            if toplam_ciro > 10000000:
                pazar_payi_tahmini = "%1 - %5"
                rekabet_durumu = "Orta olcekli isletme"
            if toplam_ciro > 50000000:
                pazar_payi_tahmini = "%5 - %15"
                rekabet_durumu = "Buyuk olcekli isletme"

            veri["tahmini_pazar_payi"] = pazar_payi_tahmini
            veri["olceklendirme"] = rekabet_durumu

            if self.ai_mode and sector:
                prompt = f"""
Sen bir finansal pazar analistisin. Su sirket ve sektor hakkinda pazar analizi yap:

Sirket: {company_name}
Sektor: {sector}
Musteri Sayisi: {musteri_sayisi}
Tedarikci Sayisi: {tedarikci_sayisi}
Tahmini Yillik Ciro: {self._tr_currency(toplam_ciro)} TL

Asagidaki basliklari iceren bir pazar analizi JSON formatinda hazirla:
- sektor_genel_durum
- rekabet_avantajlari
- buyume_firsatlari
- tehditler
- stratejik_oneriler
"""
                ai_response = self._call_gemini(prompt)
                parsed = self._parse_ai_json(ai_response)
                if "raw" not in parsed:
                    veri["ai_pazar_analizi"] = parsed

            self._log_agent("MarketAnalyst", "tamam", f"{musteri_sayisi} musteri, {self._tr_currency(toplam_ciro)} TL ciro")
            return veri

        except Exception as e:
            self._log_agent("MarketAnalyst", "hata", str(e))
            return {"hata": str(e)}

    # ------------------------------------------------------------------
    # Agent 6: ReportGenerator - Rapor olustur
    # ------------------------------------------------------------------

    def report_generator(self, analysis_results: Dict, report_type: str = "ozet") -> Dict:
        """Agent 6: ReportGenerator - Profesyonel rapor olusturur"""
        self._log_agent("ReportGenerator", "calisiyor", f"Rapor olusturuluyor: {report_type}")

        try:
            rapor = {
                "baslik": "FinRobot Finansal Analiz Raporu",
                "tarih": self._fmt_date(),
                "tip": report_type,
                "ozet": self._ozet_rapor(analysis_results),
                "icerik": {},
                "dosyalar": {},
            }

            if report_type in ("ozet", "tam"):
                rapor["icerik"]["finansal_durum"] = analysis_results.get("finansal_analiz", {})
                rapor["icerik"]["degerleme"] = analysis_results.get("degerleme", {})
                rapor["icerik"]["risk"] = analysis_results.get("risk", {})

            if report_type in ("tam", "rapor"):
                rapor["icerik"]["pazar"] = analysis_results.get("pazar", {})

            html = self._generate_html_report(rapor)
            pdf = self._generate_pdf_report(rapor)

            if html:
                rapor["dosyalar"]["html"] = html
            if pdf:
                rapor["dosyalar"]["pdf"] = pdf

            chart_dir = self._generate_charts(analysis_results)
            if chart_dir:
                rapor["dosyalar"]["grafikler"] = chart_dir

            self._log_agent("ReportGenerator", "tamam", f"Rapor hazir: {len(rapor['icerik'])} bolum")
            return rapor

        except Exception as e:
            self._log_agent("ReportGenerator", "hata", str(e))
            return {"hata": str(e)}

    def _ozet_rapor(self, analysis_results: Dict) -> str:
        satirlar = []
        satirlar.append("=" * 60)
        satirlar.append("FinRobot COKLU AJAN FINANSAL ANALIZ RAPORU")
        satirlar.append("=" * 60)
        satirlar.append(f"Rapor Tarihi: {self._fmt_date()}")
        satirlar.append(f"Ajan Sayisi: 8/8")
        satirlar.append("")

        fa = analysis_results.get("finansal_analiz", {})
        oranlar = fa.get("oranlar", {})
        if oranlar:
            satirlar.append("--- Finansal Ozet ---")
            satirlar.append(f"Cari Oran: {oranlar.get('cari_oran', 'N/A')}")
            satirlar.append(f"Borc/Ozkaynak: {oranlar.get('borc_ozkaynak', 'N/A')}")
            satirlar.append(f"ROA: {self._fmt_pct(oranlar.get('aktif_karlilik_roa', 0))}")
            satirlar.append(f"ROE: {self._fmt_pct(oranlar.get('ozsermaye_karliligi_roe', 0))}")
            satirlar.append("")

        risk = analysis_results.get("risk", {})
        if risk:
            satirlar.append(f"Risk Skoru: {risk.get('genel_risk_skoru', 'N/A')}/100")
            satirlar.append(f"Risk Seviyesi: {risk.get('genel_risk_seviyesi', 'N/A')}")
            satirlar.append("")

        deger = analysis_results.get("degerleme", {})
        if deger:
            satirlar.append(f"Isletme Degeri: {self._tr_currency(deger.get('isletme_degeri', 0))} TL")
            satirlar.append(f"Ozkaynak Degeri: {self._tr_currency(deger.get('ozkaynak_degeri', 0))} TL")

        return "\n".join(satirlar)

    def _generate_html_report(self, rapor: Dict) -> Optional[str]:
        try:
            tmp = Path(tempfile.mkdtemp(prefix="finrobot_"))
            html_path = tmp / "finrobot_rapor.html"

            css = """
            <style>
                body { font-family: 'Segoe UI', Arial, sans-serif; margin: 40px; color: #333; }
                h1 { color: #1a237e; border-bottom: 3px solid #1a237e; padding-bottom: 10px; }
                h2 { color: #283593; margin-top: 30px; }
                h3 { color: #3949ab; }
                .meta { color: #666; font-size: 14px; margin-bottom: 20px; }
                table { border-collapse: collapse; width: 100%; margin: 15px 0; }
                th { background: #1a237e; color: white; padding: 10px; text-align: left; }
                td { padding: 8px 10px; border-bottom: 1px solid #ddd; }
                tr:hover { background: #f5f5f5; }
                .skor { display: inline-block; padding: 5px 15px; border-radius: 15px; color: white; font-weight: bold; }
                .yesil { background: #4caf50; }
                .sari { background: #ff9800; }
                .turuncu { background: #ff5722; }
                .kirmizi { background: #f44336; }
                .ozet { background: #e8eaf6; padding: 20px; border-radius: 8px; margin: 20px 0; }
                .grafik { text-align: center; margin: 20px 0; }
                .grafik img { max-width: 100%; border: 1px solid #ddd; border-radius: 5px; }
                .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #999; }
                .agent-log { background: #fafafa; padding: 10px; border-left: 4px solid #1a237e; margin: 5px 0; font-size: 13px; }
            </style>
            """

            html = f"""<!DOCTYPE html>
<html lang="tr">
<head><meta charset="UTF-8"><title>{rapor['baslik']}</title>{css}</head>
<body>
<h1>{rapor['baslik']}</h1>
<div class="meta">Rapor Tarihi: {rapor['tarih']} | Tur: {rapor['tip'].upper()}</div>
"""

            html += '<div class="ozet"><pre>' + rapor.get("ozet", "") + '</pre></div>'

            icerik = rapor.get("icerik", {})
            fa = icerik.get("finansal_durum", {})
            oranlar = fa.get("oranlar", {})
            if oranlar:
                html += '<h2>Finansal Oranlar</h2><table><tr><th>Oran</th><th>Deger</th><th>Durum</th></tr>'
                degerlendirme = fa.get("degerlendirme", {})
                for key, label in [("cari_oran", "Cari Oran"), ("likidite_orani", "Likidite Orani"),
                                    ("nakit_orani", "Nakit Orani"), ("borc_ozkaynak", "Borc/Ozkaynak"),
                                    ("aktif_karlilik_roa", "Aktif Karlilik (ROA)"),
                                    ("ozsermaye_karliligi_roe", "Ozsermaye Karliligi (ROE)"),
                                    ("brut_kar_marj", "Brut Kar Marj"),
                                    ("net_kar_marj", "Net Kar Marj"),
                                    ("faaliyet_kar_marj", "Faaliyet Kar Marj")]:
                    val = oranlar.get(key, "")
                    if isinstance(val, float):
                        val_str = f"%{val*100:.2f}".replace(".", ",") if "marj" in key or "karlilik" in key or "ro" in key.lower() else f"{val:.2f}"
                    else:
                        val_str = str(val)
                    durum = degerlendirme.get(key, {}).get("durum", "-")
                    html += f"<tr><td>{label}</td><td>{val_str}</td><td>{durum}</td></tr>"
                html += "</table>"

            risk = icerik.get("risk", {})
            if risk:
                skor = risk.get("genel_risk_skoru", 0)
                seviye = risk.get("genel_risk_seviyesi", "Belirsiz")
                renk = risk.get("renk_kodu", "sari")
                html += f'<h2>Risk Degerlendirme</h2><p>Risk Skoru: <span class="skor {renk}">{skor}/100 - {seviye}</span></p>'
                bilesen = risk.get("bilesenler", {})
                if bilesen:
                    html += "<table><tr><th>Bilesen</th><th>Skor</th><th>Yuzde</th></tr>"
                    for key, label in [("likidite_riski", "Likidite"), ("borc_riski", "Borcluluk"),
                                        ("karlilik_riski", "Karlilik"), ("nakit_riski", "Nakit")]:
                        b = bilesen.get(key, {})
                        html += f"<tr><td>{label}</td><td>{b.get('skor', 0)}/{b.get('max', 10)}</td><td>%{b.get('yuzde', 0)}</td></tr>"
                    html += "</table>"

            deger = icerik.get("degerleme", {})
            if deger:
                html += '<h2>DCF Degerleme</h2><table><tr><th>Kalem</th><th>Deger (TL)</th></tr>'
                for key, label in [("isletme_degeri", "Isletme Degeri"), ("ozkaynak_degeri", "Ozkaynak Degeri"),
                                    ("net_borc", "Net Borc"), ("terminal_deger", "Terminal Degeri")]:
                    html += f"<tr><td>{label}</td><td>{self._tr_currency(deger.get(key, 0))}</td></tr>"
                html += "</table>"

            html += f"""
<div class="footer">
<p>FinRobot Multi-Agent Sistemi ile olusturulmustur | Accura Finance Entegrasyonu</p>
<p>Kaynak: github.com/AI4Finance-Foundation/FinRobot</p>
</div></body></html>"""

            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html)

            return str(html_path)

        except Exception as e:
            if self.logger:
                self.logger.error(f"HTML rapor hatasi: {e}")
            return None

    def _generate_pdf_report(self, rapor: Dict) -> Optional[str]:
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import mm
            from reportlab.lib import colors
            from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                            PageBreak, ListFlowable, ListItem)
            from reportlab.lib.enums import TA_CENTER, TA_LEFT

            tmp = Path(tempfile.mkdtemp(prefix="finrobot_"))
            pdf_path = tmp / "finrobot_rapor.pdf"

            doc = SimpleDocTemplate(str(pdf_path), pagesize=A4,
                                    leftMargin=20*mm, rightMargin=20*mm,
                                    topMargin=20*mm, bottomMargin=20*mm)

            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle(name='TurkishTitle', parent=styles['Title'],
                                       fontName='Helvetica', fontSize=18, spaceAfter=12,
                                       textColor=colors.HexColor("#1a237e")))
            styles.add(ParagraphStyle(name='TurkishH1', parent=styles['Heading1'],
                                       fontName='Helvetica', fontSize=14, spaceAfter=8,
                                       textColor=colors.HexColor("#283593")))
            styles.add(ParagraphStyle(name='TurkishH2', parent=styles['Heading2'],
                                       fontName='Helvetica', fontSize=12, spaceAfter=6,
                                       textColor=colors.HexColor("#3949ab")))
            styles.add(ParagraphStyle(name='TurkishBody', parent=styles['Normal'],
                                       fontName='Helvetica', fontSize=9, leading=13,
                                       spaceAfter=6))

            elements = []
            elements.append(Paragraph(rapor["baslik"], styles["TurkishTitle"]))
            elements.append(Paragraph(f"Rapor Tarihi: {rapor['tarih']} | Tur: {rapor['tip'].upper()}",
                                       styles["TurkishBody"]))
            elements.append(Spacer(1, 10))

            ozet = rapor.get("ozet", "")
            for satir in ozet.split("\n"):
                if satir.strip():
                    elements.append(Paragraph(satir.replace("|", "&nbsp;"*3), styles["TurkishBody"]))
            elements.append(Spacer(1, 10))

            icerik = rapor.get("icerik", {})
            fa = icerik.get("finansal_durum", {})
            oranlar = fa.get("oranlar", {})
            if oranlar:
                elements.append(Paragraph("Finansal Oranlar", styles["TurkishH1"]))
                data = [["Oran", "Deger", "Durum"]]
                degerlendirme = fa.get("degerlendirme", {})
                for key, label in [("cari_oran", "Cari Oran"), ("likidite_orani", "Likidite Orani"),
                                    ("nakit_orani", "Nakit Orani"), ("borc_ozkaynak", "Borc/Ozkaynak"),
                                    ("aktif_karlilik_roa", "Aktif Karlilik"),
                                    ("ozsermaye_karliligi_roe", "Ozsermaye Karliligi"),
                                    ("brut_kar_marj", "Brut Kar Marj"), ("net_kar_marj", "Net Kar Marj")]:
                    val = oranlar.get(key, "")
                    if isinstance(val, float):
                        val_str = f"%{val*100:.1f}" if val < 1 else f"{val:.2f}"
                    else:
                        val_str = str(val)
                    durum = degerlendirme.get(key, {}).get("durum", "-")
                    data.append([label, val_str, durum])

                t = Table(data, colWidths=[120, 80, 80])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1a237e")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
                ]))
                elements.append(t)
                elements.append(Spacer(1, 10))

            risk = icerik.get("risk", {})
            if risk:
                elements.append(Paragraph("Risk Degerlendirme", styles["TurkishH1"]))
                skor = risk.get("genel_risk_skoru", 0)
                seviye = risk.get("genel_risk_seviyesi", "Belirsiz")
                elements.append(Paragraph(f"Risk Skoru: {skor}/100 - {seviye}", styles["TurkishBody"]))
                bilesen = risk.get("bilesenler", {})
                if bilesen:
                    data = [["Bilesen", "Skor", "Yuzde"]]
                    for key, label in [("likidite_riski", "Likidite"), ("borc_riski", "Borcluluk"),
                                        ("karlilik_riski", "Karlilik"), ("nakit_riski", "Nakit")]:
                        b = bilesen.get(key, {})
                        data.append([label, f"{b.get('skor', 0)}/{b.get('max', 10)}", f"%{b.get('yuzde', 0)}"])
                    t = Table(data, colWidths=[100, 80, 80])
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#c62828")),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('FONTSIZE', (0, 0), (-1, -1), 8),
                        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ]))
                    elements.append(t)

            elements.append(Spacer(1, 15))
            elements.append(Paragraph("FinRobot Multi-Agent Sistemi ile olusturulmustur | Accura Finance",
                                       styles["TurkishBody"]))

            doc.build(elements)
            return str(pdf_path)

        except ImportError:
            try:
                return self._generate_pdf_fallback(rapor)
            except Exception:
                return None
        except Exception as e:
            if self.logger:
                self.logger.error(f"PDF rapor hatasi: {e}")
            return None

    def _generate_pdf_fallback(self, rapor: Dict) -> Optional[str]:
        try:
            from fpdf import FPDF

            tmp = Path(tempfile.mkdtemp(prefix="finrobot_"))
            pdf_path = tmp / "finrobot_rapor.pdf"

            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)

            pdf.set_font("Helvetica", "B", 16)
            pdf.cell(0, 10, rapor["baslik"], new_x="LMARGIN", new_y="NEXT", align="C")
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(0, 6, f"Rapor Tarihi: {rapor['tarih']}", new_x="LMARGIN", new_y="NEXT", align="C")
            pdf.ln(5)

            pdf.set_font("Courier", "", 8)
            ozet = rapor.get("ozet", "")
            for satir in ozet.split("\n"):
                pdf.cell(0, 4, satir, new_x="LMARGIN", new_y="NEXT")

            pdf.ln(5)
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, "Finansal Oranlar", new_x="LMARGIN", new_y="NEXT")

            icerik = rapor.get("icerik", {})
            fa = icerik.get("finansal_durum", {})
            oranlar = fa.get("oranlar", {})
            if oranlar:
                col_w = [60, 40, 40]
                pdf.set_font("Helvetica", "B", 9)
                for hw, hd in zip(col_w, ["Oran", "Deger", "Durum"]):
                    pdf.cell(hw, 7, hd, border=1, align="C")
                pdf.ln()
                pdf.set_font("Helvetica", "", 9)
                degerlendirme = fa.get("degerlendirme", {})
                for key, label in [("cari_oran", "Cari Oran"), ("likidite_orani", "Likidite Orani"),
                                    ("nakit_orani", "Nakit Orani"), ("borc_ozkaynak", "Borc/Ozkaynak"),
                                    ("aktif_karlilik_roa", "Aktif Karlilik"),
                                    ("ozsermaye_karliligi_roe", "Ozsermaye Karliligi")]:
                    val = oranlar.get(key, "")
                    if isinstance(val, float):
                        val_str = f"%{val*100:.1f}" if val < 1 else f"{val:.2f}"
                    else:
                        val_str = str(val)
                    durum = degerlendirme.get(key, {}).get("durum", "-")
                    for hw, v in zip(col_w, [label, val_str, durum]):
                        pdf.cell(hw, 6, v, border=1, align="C")
                    pdf.ln()

            risk = icerik.get("risk", {})
            if risk:
                pdf.ln(5)
                pdf.set_font("Helvetica", "B", 12)
                pdf.cell(0, 8, "Risk Degerlendirme", new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", "", 9)
                skor = risk.get("genel_risk_skoru", 0)
                seviye = risk.get("genel_risk_seviyesi", "Belirsiz")
                pdf.cell(0, 6, f"Risk Skoru: {skor}/100 - {seviye}", new_x="LMARGIN", new_y="NEXT")

            pdf.set_font("Helvetica", "I", 7)
            pdf.ln(10)
            pdf.cell(0, 5, "FinRobot Multi-Agent Sistemi ile olusturulmustur | Accura Finance",
                     new_x="LMARGIN", new_y="NEXT", align="C")

            pdf.output(str(pdf_path))
            return str(pdf_path)

        except Exception as e:
            if self.logger:
                self.logger.error(f"FPDF rapor hatasi: {e}")
            return None

    def _generate_charts(self, analysis_results: Dict) -> Optional[str]:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            import matplotlib.ticker as mticker

            tmp = Path(tempfile.mkdtemp(prefix="finrobot_charts_"))
            plt.rcParams.update({
                "font.family": "sans-serif",
                "font.size": 9,
                "axes.titlesize": 12,
                "axes.labelsize": 10,
            })
            try:
                plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]
            except Exception:
                pass

            deger = analysis_results.get("degerleme", {})
            fcf_proj = deger.get("fcf_projeksiyonu", [])
            if fcf_proj:
                fig, ax = plt.subplots(figsize=(8, 4))
                yillar = [str(p["yil"]) for p in fcf_proj]
                fcf = [p["fcf"] for p in fcf_proj]
                bd = [p["bugunku_deger"] for p in fcf_proj]
                ax.bar(yillar, fcf, alpha=0.7, label="Tahmini FCF")
                ax.plot(yillar, bd, "r-o", label="Bugunku Deger", linewidth=2)
                ax.set_xlabel("Yil")
                ax.set_ylabel("TL")
                ax.set_title("DCF Projeksiyonu")
                ax.legend()
                ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f"{x:,.0f}"))
                fig.tight_layout()
                fig.savefig(tmp / "dcf_projeksiyon.png", dpi=150)
                plt.close(fig)

            risk = analysis_results.get("risk", {})
            bilesen = risk.get("bilesenler", {})
            if bilesen:
                fig, ax = plt.subplots(figsize=(6, 4))
                kategoriler = []
                skorlar = []
                for key, label in [("likidite_riski", "Likidite"), ("borc_riski", "Borcluluk"),
                                    ("karlilik_riski", "Karlilik"), ("nakit_riski", "Nakit")]:
                    b = bilesen.get(key, {})
                    kategoriler.append(label)
                    skorlar.append(b.get("yuzde", 0))
                renkler = ["#4caf50" if s >= 70 else "#ff9800" if s >= 50 else "#f44336" for s in skorlar]
                bars = ax.barh(kategoriler, skorlar, color=renkler)
                ax.set_xlim(0, 100)
                ax.set_xlabel("Skor (%)")
                ax.set_title("Risk Bilesenleri")
                for bar, skor in zip(bars, skorlar):
                    ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                            f"%{skor:.0f}", va="center", fontsize=9)
                fig.tight_layout()
                fig.savefig(tmp / "risk_radar.png", dpi=150)
                plt.close(fig)

            oranlar = analysis_results.get("finansal_analiz", {}).get("oranlar", {})
            if oranlar:
                fig, ax = plt.subplots(figsize=(6, 4))
                oran_etiket = ["Cari Oran", "Likidite", "Nakit"]
                oran_deger = [oranlar.get("cari_oran", 0), oranlar.get("likidite_orani", 0), oranlar.get("nakit_orani", 0)]
                ax.bar(oran_etiket, oran_deger, color=["#1565c0", "#42a5f5", "#90caf9"])
                ax.axhline(y=1.5, color="orange", linestyle="--", label="Sinir (1.5)")
                ax.axhline(y=1.0, color="red", linestyle="--", label="Risk (1.0)")
                ax.set_ylabel("Oran")
                ax.set_title("Likidite Oranlari")
                ax.legend()
                fig.tight_layout()
                fig.savefig(tmp / "likidite_oran.png", dpi=150)
                plt.close(fig)

            return str(tmp)

        except Exception as e:
            if self.logger:
                self.logger.error(f"Grafik olusturma hatasi: {e}")
            return None

    # ------------------------------------------------------------------
    # Agent 7: RecommendationAgent - Yatirim tavsiyesi
    # ------------------------------------------------------------------

    def recommendation_agent(self, analysis_results: Dict) -> Dict:
        """Agent 7: RecommendationAgent - Yatirim tavsiyesi ve strateji"""
        self._log_agent("RecommendationAgent", "calisiyor", "Yatirim tavsiyesi hazirlaniyor")

        try:
            risk = analysis_results.get("risk", {})
            deger = analysis_results.get("degerleme", {})
            fa = analysis_results.get("finansal_analiz", {})
            oranlar = fa.get("oranlar", {})

            risk_skoru = risk.get("genel_risk_skoru", 50)
            isletme_degeri = deger.get("isletme_degeri", 0)
            ozkaynak_degeri = deger.get("ozkaynak_degeri", 0)

            if risk_skoru >= 70 and ozkaynak_degeri > 0:
                tavsiye = "GUCLU AL"
                guven = "Yuksek"
            elif risk_skoru >= 50 and ozkaynak_degeri > 0:
                tavsiye = "AL"
                guven = "Orta"
            elif risk_skoru >= 30:
                tavsiye = "TUT"
                guven = "Dusuk"
            else:
                tavsiye = "KAÇIN"
                guven = "Riskli"

            gerekce = []
            cr = oranlar.get("cari_oran", 0)
            if cr >= 2:
                gerekce.append("Guclu likidite pozisyonu")
            elif cr < 1:
                gerekce.append("Zayif likidite - dikkatli olunmali")

            bk = oranlar.get("borc_ozkaynak", 0)
            if bk <= 1:
                gerekce.append("Dusuk borcluluk avantaji")
            elif bk > 2:
                gerekce.append("Yuksek kaldirac riski")

            roe = oranlar.get("ozsermaye_karliligi_roe", 0)
            if roe > 0.15:
                gerekce.append("Guclu ozsermaye karliligi")
            elif roe < 0:
                gerekce.append("Negatif ozsermaye karliligi")

            if isletme_degeri > 0 and ozkaynak_degeri > 0:
                gerekce.append(f"Isletme degeri: {self._tr_currency(isletme_degeri)} TL")

            result = {
                "tavsiye": tavsiye,
                "guven_seviyesi": guven,
                "risk_skoru": risk_skoru,
                "gerekceler": gerekce,
                "yatirim_temasi": self._yatirim_temasi(oranlar, risk_skoru),
                "eylem_maddeleri": [],
            }

            if tavsiye in ("GUCLU AL", "AL"):
                result["eylem_maddeleri"] = [
                    "Portfoyde pozisyon artirilabilir",
                    "Uzun vadeli tutma stratejisi onerilir",
                    "Kar satisi icin hedef fiyat belirlenmeli",
                ]
            elif tavsiye == "TUT":
                result["eylem_maddeleri"] = [
                    "Mevcut pozisyon korunmali",
                    "Yeni alim icin daha uygun fiyat beklenmeli",
                    "Sirket performansi yakindan izlenmeli",
                ]
            else:
                result["eylem_maddeleri"] = [
                    "Pozisyon azaltilmasi degerlendirilmeli",
                    "Alternatif yatirim araclarina yonelinmeli",
                    "Riskli durum netlesene kadar beklenmeli",
                ]

            if self.ai_mode:
                ozet_json = json.dumps({
                    "tavsiye": tavsiye,
                    "risk_skoru": risk_skoru,
                    "cari_oran": oranlar.get("cari_oran", 0),
                    "borc_ozkaynak": oranlar.get("borc_ozkaynak", 0),
                    "degerleme": isletme_degeri,
                }, ensure_ascii=False)

                prompt = f"""
Sen bir finansal danismansin. Asagidaki analiz sonuclarina gore yatirim tezi olustur.

Veriler:
{ozet_json}

Tavsiye: {tavsiye}
Risk Skoru: {risk_skoru}/100

Su formatta JSON cikti ver (sadece JSON):
{{
    "yatirim_tezi": "kisa paragraf",
    "guclu_yonler": ["madde1", "madde2"],
    "zayif_yanlar": ["madde1", "madde2"],
    "firsatlar": ["madde1"],
    "tehditler": ["madde1"],
    "sonuc": "kisa sonuc"
}}
"""
                ai_response = self._call_gemini(prompt)
                parsed = self._parse_ai_json(ai_response)
                if "raw" not in parsed:
                    result["ai_yorum"] = parsed

            self._log_agent("RecommendationAgent", "tamam", f"Tavsiye: {tavsiye} (Guven: {guven})")
            return result

        except Exception as e:
            self._log_agent("RecommendationAgent", "hata", str(e))
            return {"hata": str(e)}

    def _yatirim_temasi(self, oranlar: Dict, risk_skoru: float) -> str:
        roe = oranlar.get("ozsermaye_karliligi_roe", 0)
        cr = oranlar.get("cari_oran", 0)

        if risk_skoru >= 70 and roe > 0.15:
            return "Buyume ve Deger Yatirimi"
        elif risk_skoru >= 50 and cr >= 1.5:
            return "Dengeli Portfoy"
        elif risk_skoru >= 30:
            return "Toparlanma Beklentisi"
        else:
            return "Yeniden Yapilandirma"

    # ------------------------------------------------------------------
    # Agent 8: ReviewAgent - Kalite kontrol
    # ------------------------------------------------------------------

    def review_agent(self, output: Any) -> Dict:
        """Agent 8: ReviewAgent - Cikti kalite kontrolu"""
        self._log_agent("ReviewAgent", "calisiyor", "Kalite kontrol yapiliyor")

        try:
            puan = 100
            uyarilar = []
            oneriler = []

            if isinstance(output, dict):
                hata = output.get("hata")
                if hata:
                    puan -= 40
                    uyarilar.append(f"Hata tespit edildi: {hata}")

                eksik_alanlar = []
                for anahtar in ["finansal_analiz", "degerleme", "risk", "pazar"]:
                    if anahtar not in output:
                        eksik_alanlar.append(anahtar)

                if eksik_alanlar:
                    puan -= 10 * len(eksik_alanlar)
                    uyarilar.append(f"Eksik analiz alanlari: {', '.join(eksik_alanlar)}")
                    oneriler.append(f"Tum ajanlarin calistirilmasi onerilir")

                fa = output.get("finansal_analiz", {})
                oranlar = fa.get("oranlar", {})
                if not oranlar:
                    puan -= 15
                    uyarilar.append("Finansal oranlar hesaplanmamis")
                else:
                    gerekli = ["cari_oran", "borc_ozkaynak", "aktif_karlilik_roa"]
                    eksik_oran = [o for o in gerekli if o not in oranlar]
                    if eksik_oran:
                        puan -= 5 * len(eksik_oran)
                        uyarilar.append(f"Eksik oranlar: {', '.join(eksik_oran)}")

                risk = output.get("risk", {})
                if risk and risk.get("genel_risk_skoru") is None:
                    puan -= 10
                    uyarilar.append("Risk skoru hesaplanmamis")

                deger = output.get("degerleme", {})
                if deger and not deger.get("isletme_degeri"):
                    puan -= 10
                    uyarilar.append("DCF degerleme yapilmamis")

            elif isinstance(output, str):
                if len(output) < 50:
                    puan -= 30
                    uyarilar.append("Cok kisa cikti")
            else:
                puan -= 20
                uyarilar.append("Beklenmeyen cikti formati")

            puan = max(0, min(100, puan))

            if puan >= 90:
                kalite = "Mukemmel"
            elif puan >= 75:
                kalite = "Iyi"
            elif puan >= 50:
                kalite = "Orta"
            elif puan >= 25:
                kalite = "Dusuk"
            else:
                kalite = "Yetersiz"

            result = {
                "kalite_puani": puan,
                "kalite_seviyesi": kalite,
                "uyarilar": uyarilar,
                "oneriler": oneriler,
                "ajan_zinciri": list(self._agent_chain_log),
                "yeniden_analiz_gerekli": puan < 60,
            }

            self._log_agent("ReviewAgent", "tamam", f"Kalite puani: {puan}/100 - {kalite}")
            return result

        except Exception as e:
            self._log_agent("ReviewAgent", "hata", str(e))
            return {"kalite_puani": 0, "kalite_seviyesi": "Hata", "uyarilar": [str(e)]}

    # ==================================================================
    # PUBLIC API
    # ==================================================================

    def analyze_company(self, company_data: Optional[Dict] = None) -> Dict:
        """Full company analysis: financial health, ratios, trends

        8 ajani sirayla calistirarak kapsamli sirket analizi yapar.

        AI Mode: Gemini API ile dogal dil yorumlari eklenir
        Computation Mode: Sadece hesaplama yapilir (API gerektirmez)
        """
        self._agent_chain_log = []
        self._log_agent("FinRobot", "basladi", "8 ajanli sirket analizi baslatildi")

        sonuc = {}

        veri = self.data_collector(company_data)
        if "hata" in veri:
            return {"hata": veri["hata"], "ajan_zinciri": self._agent_chain_log}
        sonuc["veri"] = veri

        fa = self.financial_analyzer(veri)
        sonuc["finansal_analiz"] = fa

        deger = self.valuation_agent({"finansal_veriler": fa})
        sonuc["degerleme"] = deger

        risk = self.risk_assessor({"finansal_veriler": fa, "oranlar": fa.get("oranlar", {})})
        sonuc["risk"] = risk

        sirket_adi = ""
        sektor = ""
        if veri.get("sirket"):
            sirket_adi = veri["sirket"].get("CompanyName", "")
        pazar = self.market_analyst(sirket_adi, sektor)
        sonuc["pazar"] = pazar

        rapor = self.report_generator(sonuc, "tam")
        sonuc["rapor"] = rapor

        tavsiye = self.recommendation_agent(sonuc)
        sonuc["tavsiye"] = tavsiye

        review = self.review_agent(sonuc)
        sonuc["kalite_kontrol"] = review

        self._log_agent("FinRobot", "tamamlandi",
                         f"8 ajan basariyla calisti. Risk: {risk.get('genel_risk_skoru', '?')}/100, "
                         f"Tavsiye: {tavsiye.get('tavsiye', '?')}")

        return sonuc

    def valuation_analysis(self, company_data: Optional[Dict] = None) -> Dict:
        """Valuation analysis: DCF, multiples, peer comparison"""
        veri = self.data_collector(company_data)
        if "hata" in veri:
            return {"hata": veri["hata"]}

        if "finansal_analiz" not in company_data or not company_data.get("finansal_analiz"):
            fa = self.financial_analyzer(veri)
        else:
            fa = company_data["finansal_analiz"]

        deger = self.valuation_agent({"finansal_veriler": fa})
        return deger

    def risk_assessment(self, financial_data: Optional[Dict] = None) -> Dict:
        """Risk assessment: liquidity, solvency, profitability risks"""
        if not financial_data:
            veri = self.data_collector()
            fa = self.financial_analyzer(veri)
            finansal = fa
        else:
            finansal = financial_data

        return self.risk_assessor({"finansal_veriler": finansal,
                                    "oranlar": finansal.get("oranlar", {})})

    def market_analysis(self, company_name: str = "", sector: str = "") -> Dict:
        """Market analysis: sector position, competition, trends"""
        return self.market_analyst(company_name, sector)

    def generate_report(self, analysis_results: Optional[Dict] = None,
                        report_type: str = "ozet") -> Dict:
        """Generate professional report from analysis data"""
        if not analysis_results:
            analysis_results = self.analyze_company()
        return self.report_generator(analysis_results, report_type)

    def financial_ratios(self, financial_data: Optional[Dict] = None) -> Dict:
        """Calculate key financial ratios

        Hesaplanan oranlar:
        - Cari Oran, Likidite Orani, Nakit Oran
        - Borc/Ozkaynak, Aktif Karlilik (ROA), Ozsermaye Karliligi (ROE)
        - Brut Kar Marj, Net Kar Marj, Faaliyet Kar Marj
        """
        if not financial_data:
            veri = self.data_collector()
            return self.financial_analyzer(veri)
        return self.financial_analyzer(financial_data)

    def trend_analysis(self, historical_data: Optional[List] = None, periods: int = 3) -> Dict:
        """Analyze financial trends over multiple periods"""
        self._log_agent("TrendAnalizi", "calisiyor", f"{periods} donem trend analizi")

        try:
            if historical_data:
                donemler = historical_data
            else:
                donemler = self._query("""
                    SELECT strftime('%Y-%m', VoucherDate) as donem,
                           COUNT(*) as kayit,
                           COALESCE(SUM(TotalDebit), 0) as toplam_borc,
                           COALESCE(SUM(TotalCredit), 0) as toplam_alacak
                    FROM JournalEntries
                    GROUP BY donem ORDER BY donem DESC LIMIT ?
                """, (periods * 2,))
                donemler = [dict(r) for r in donemler]

            if not donemler:
                return {"hata": "Veri bulunamadi"}

            trend_data = []
            for d in donemler:
                borc = float(d.get("toplam_borc", d.get("borc", 0)))
                trend_data.append(borc)

            trend = self._trend_hesapla(trend_data)

            result = {
                "donem_sayisi": len(donemler),
                "donemler": donemler,
                "trend": trend,
                "yorum": self._trend_yorum(trend),
            }

            if self.ai_mode and len(donemler) >= 3:
                ozet = json.dumps(donemler[:periods], ensure_ascii=False)
                prompt = f"""
Su donemsel finansal verileri trend analizi yap:

Veriler:
{ozet}

Trend: {json.dumps(trend, ensure_ascii=False)}

JSON formatinda trend yorumu ver:
{{
    "genel_trend": "yukari/asaği/yatay",
    "ivme": "hizli/orta/yavas",
    "tahmin": "kisa vadeli beklenti",
    "eylem": "onerilen aksiyon"
}}
"""
                ai_response = self._call_gemini(prompt)
                parsed = self._parse_ai_json(ai_response)
                if "raw" not in parsed:
                    result["ai_yorum"] = parsed

            self._log_agent("TrendAnalizi", "tamam", f"Trend: {trend.get('yon', 'belirsiz')}")
            return result

        except Exception as e:
            self._log_agent("TrendAnalizi", "hata", str(e))
            return {"hata": str(e)}

    def _trend_hesapla(self, data: List[float]) -> Dict:
        if len(data) < 2:
            return {"yon": "yetersiz_veri", "degisim": 0}

        ilk = data[-1] if data else 0
        son = data[0] if data else 0

        if ilk == 0:
            return {"yon": "belirsiz", "degisim": 0}

        toplam_degisim = ((son - ilk) / abs(ilk)) * 100

        dilim_degisimleri = []
        for i in range(len(data) - 1):
            if data[i + 1] != 0:
                degisim = ((data[i] - data[i + 1]) / abs(data[i + 1])) * 100
                dilim_degisimleri.append(degisim)

        ortalama_degisim = sum(dilim_degisimleri) / len(dilim_degisimleri) if dilim_degisimleri else 0

        if toplam_degisim > 10:
            yon = "yukari"
        elif toplam_degisim > 3:
            yon = "hafif_yukari"
        elif toplam_degisim > -3:
            yon = "yatay"
        elif toplam_degisim > -10:
            yon = "hafif_asaği"
        else:
            yon = "asaği"

        return {
            "yon": yon,
            "toplam_degisim_yuzde": round(toplam_degisim, 2),
            "ortalama_donemsel_degisim": round(ortalama_degisim, 2),
            "ilk_deger": ilk,
            "son_deger": son,
            "ivme": "hizli" if abs(ortalama_degisim) > 15 else "orta" if abs(ortalama_degisim) > 5 else "yavas",
        }

    def _trend_yorum(self, trend: Dict) -> str:
        yon = trend.get("yon", "belirsiz")
        ivme = trend.get("ivme", "yavas")
        degisim = trend.get("toplam_degisim_yuzde", 0)

        yon_text = {
            "yukari": "guclu bir yukselis trendi",
            "hafif_yukari": "sinirli bir yukselis",
            "yatay": "yatay bir seyir",
            "hafif_asaği": "sinirli bir gerileme",
            "asaği": "guclu bir dusus trendi",
        }.get(yon, "belirsiz bir trend")

        return (f"Finansal verilerde {yon_text} gozlenmektedir. "
                f"Donem boyunca toplam degisim %{degisim:+.2f} olmustur. "
                f"Degisim hizi {ivme} seviyesindedir.")

    def comparative_analysis(self, company_data_list: Optional[List[Dict]] = None) -> Dict:
        """Compare multiple companies/periods side by side"""
        self._log_agent("KarsilastirmaliAnaliz", "calisiyor", "Sirket/donem karsilastirmasi")

        try:
            if not company_data_list:
                donemler = self._query("""
                    SELECT strftime('%Y', VoucherDate) as yil,
                           COUNT(*) as kayit,
                           COALESCE(SUM(TotalDebit), 0) as toplam
                    FROM JournalEntries
                    GROUP BY yil ORDER BY yil DESC LIMIT 5
                """)
                karsilastirilacak = [{"donem": dict(d)["yil"], "veri": dict(d)} for d in donemler]
            else:
                karsilastirilacak = company_data_list

            analizler = []
            for item in karsilastirilacak:
                if isinstance(item, dict):
                    veri = self.data_collector(item)
                    fa = self.financial_analyzer(veri)
                    analizler.append({
                        "etiket": item.get("CompanyName") or item.get("donem", "Bilinmeyen"),
                        "oranlar": fa.get("oranlar", {}),
                        "ozet": fa.get("ozet", {}),
                    })

            if not analizler:
                return {"hata": "Karsilastirma yapilacak veri bulunamadi"}

            karsilastirma = {
                "karsilastirilan_sayi": len(analizler),
                "analizler": analizler,
            }

            if len(analizler) >= 2:
                ilk = analizler[0]
                son = analizler[-1]
                fark = {}
                for k in ilk.get("oranlar", {}):
                    if k in son.get("oranlar", {}):
                        fark[k] = round(float(son["oranlar"].get(k, 0)) - float(ilk["oranlar"].get(k, 0)), 4)
                karsilastirma["farklar"] = fark

                en_iyi = max(analizler, key=lambda x: x.get("oranlar", {}).get("aktif_karlilik_roa", 0))
                karsilastirma["en_iyi_performans"] = en_iyi.get("etiket")

            if self.ai_mode:
                ozet_json = json.dumps([{
                    "etiket": a["etiket"],
                    "cari_oran": a["oranlar"].get("cari_oran"),
                    "roa": a["oranlar"].get("aktif_karlilik_roa"),
                    "roe": a["oranlar"].get("ozsermaye_karliligi_roe"),
                } for a in analizler], ensure_ascii=False)

                prompt = f"""
Su karsilastirmali finansal verileri analiz et:

{ozet_json}

JSON formatinda karsilastirma raporu hazirla:
{{
    "en_guclu_sirket": "ad",
    "en_zayif_sirket": "ad",
    "ortalama_cari_oran": sayi,
    "ortalama_roa": sayi,
    "genel_degerlendirme": "metin"
}}
"""
                ai_response = self._call_gemini(prompt)
                parsed = self._parse_ai_json(ai_response)
                if "raw" not in parsed:
                    karsilastirma["ai_yorum"] = parsed

            self._log_agent("KarsilastirmaliAnaliz", "tamam", f"{len(analizler)} kayit karsilastirildi")
            return karsilastirma

        except Exception as e:
            self._log_agent("KarsilastirmaliAnaliz", "hata", str(e))
            return {"hata": str(e)}

    # ------------------------------------------------------------------
    # Utility: Agent zincirini temizle
    # ------------------------------------------------------------------

    def clear_agent_chain(self):
        """Agent zincir logunu temizler"""
        self._agent_chain_log = []

    def get_agent_chain_log(self) -> List[Dict]:
        """Agent zincir logunu dondurur"""
        return list(self._agent_chain_log)

    def set_ai_mode(self, enabled: bool):
        """AI modunu ac/kapat"""
        self.ai_mode = enabled


finrobot = FinRobotAdapter()


def get_finrobot():
    return finrobot
