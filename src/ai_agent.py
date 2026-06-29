"""
Accura Finance AI Agent Sistemi
- Gemini AI ile akıllı muhasebe asistanı
- Fatura otomatik işleme
- Akıllı rapor oluşturma
- Doğal dil ile sorgulama
"""

import json
import os
import re
from datetime import datetime, date
import traceback

class AIAgent:
    def __init__(self, db_manager=None, api_key=None):
        self.db_manager = db_manager
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        self.logger = self._setup_logger()

    def _setup_logger(self):
        try:
            from src.utils.logger import setup_logger
            return setup_logger("AIAgent")
        except:
            return None

    def _call_gemini(self, prompt):
        try:
            import urllib.request
            import urllib.parse

            data = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.1,
                    "topK": 1,
                    "topP": 1,
                    "maxOutputTokens": 4096
                }
            }

            req = urllib.request.Request(
                f"{self.api_url}?key={self.api_key}",
                data=json.dumps(data).encode(),
                headers={
                    "Content-Type": "application/json",
                    "X-Goog-Api-Key": self.api_key
                }
            )
            response = urllib.request.urlopen(req, timeout=30)
            result = json.loads(response.read())

            if "candidates" in result and result["candidates"]:
                text = result["candidates"][0]["content"]["parts"][0]["text"]
                return text
            return "Üzgünüm, AI yanıt veremedi."
        except Exception as e:
            error_msg = f"AI çağrı hatası: {e}"
            if self.logger:
                self.logger.error(error_msg)
            return f"⚠️ {error_msg}"

    def process_invoice_text(self, invoice_text):
        prompt = f"""
Sen bir muhasebe uzmanı AI asistanısın. Aşağıdaki fatura metnini analiz et ve JSON formatında çıktı ver:

Fatura Metni:
{invoice_text}

Şu formatta JSON çıktısı ver (sadece JSON, başka metin yok):
{{
    "fatura_turu": "Alis" veya "Satis",
    "fatura_no": "fatura numarası",
    "tarih": "GG.AA.YYYY",
    "cari_unvan": "müşteri/tedarikçi adı",
    "vergi_no": "vergi numarası",
    "vergi_dairesi": "vergi dairesi",
    "urunler": [
        {{"urun_adi": "...", "miktar": sayı, "birim": "...", "birim_fiyat": sayı, "kdv_orani": sayı, "toplam": sayı}}
    ],
    "ara_toplam": sayı,
    "kdv_toplam": sayı,
    "genel_toplam": sayı
}}
"""
        response = self._call_gemini(prompt)
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {"raw": response}
        except:
            return {"raw": response}

    def generate_report(self, report_type="mizan", data=None):
        prompt = f"""
Sen bir mali müşavir AI asistanısın. Aşağıdaki verilere göre profesyonel bir {report_type} raporu oluştur.

Veriler:
{json.dumps(data, indent=2, ensure_ascii=False) if data else "Henüz veri yok"}

Raporda şunlar olmalı:
1. Rapor başlığı ve tarih
2. Özet tablo
3. Analiz ve yorumlar
4. Öneriler
"""
        return self._call_gemini(prompt)

    def analyze_financial_status(self, data):
        prompt = f"""
Sen bir finansal analist AI asistanısın. Şirketin finansal durumunu analiz et.

Finansal Veriler:
{json.dumps(data, indent=2, ensure_ascii=False)}

Analizinde şunları değerlendir:
1. Likidite durumu
2. Karlılık analizi
3. Borç/Alacak dengesi
4. Risk faktörleri
5. Öneriler
"""
        return self._call_gemini(prompt)

    def suggest_accounting_entry(self, description, amount):
        prompt = f"""
Sen bir muhasebe uzmanı AI asistanısın. Aşağıdaki işlem için uygun muhasebe kaydını öner.

İşlem: {description}
Tutar: {amount} TL

Şu formatta JSON çıktısı ver (sadece JSON):
{{
    "aciklama": "kayıt açıklaması",
    "maddeler": [
        {{"hesap_kodu": "XXX", "borc": sayı, "alacak": sayı, "aciklama": "..."}}
    ]
}}
"""
        response = self._call_gemini(prompt)
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {"raw": response}
        except:
            return {"raw": response}

    def chat(self, message, context=None):
        context_text = ""
        if context:
            context_text = f"\n\nBağlam bilgisi:\n{json.dumps(context, indent=2, ensure_ascii=False)}"

        prompt = f"""
Sen Accura Finance muhasebe yazılımının AI asistanısın.
Kullanıcıya muhasebe, finans ve şirket yönetimi konularında yardımcı ol.

Kullanıcı: {message}{context_text}

Yardımcı ve profesyonel bir şekilde yanıtla:
"""
        return self._call_gemini(prompt)

ai_agent = AIAgent()

def get_ai_agent():
    return ai_agent
