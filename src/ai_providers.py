"""
Accura Finance - Multi-Model AI Provider
- GitHub Models API (Meta Llama 3.1, Microsoft Phi-3, Mistral)
- Gemini API (fallback)
- Turkish prompt engineering for accounting queries
"""

import json
import os
import re
import urllib.request
import urllib.parse

GITHUB_API_BASE = "https://models.inference.ai.azure.com"

AVAILABLE_MODELS = {
    "github:Meta-Llama-3.1-70B-Instruct": {
        "name": "Llama 3.1 70B",
        "provider": "Meta",
        "api": "github",
        "description": "Meta Llama 3.1 70B (GitHub Models)",
    },
    "github:Meta-Llama-3.1-8B-Instruct": {
        "name": "Llama 3.1 8B",
        "provider": "Meta",
        "api": "github",
        "description": "Meta Llama 3.1 8B (GitHub Models)",
    },
    "github:Phi-3-mini-4k-instruct": {
        "name": "Phi-3 Mini",
        "provider": "Microsoft",
        "api": "github",
        "description": "Microsoft Phi-3 Mini 4K (GitHub Models)",
    },
    "github:Phi-3-medium-4k-instruct": {
        "name": "Phi-3 Medium",
        "provider": "Microsoft",
        "api": "github",
        "description": "Microsoft Phi-3 Medium 4K (GitHub Models)",
    },
    "github:Mistral-large-2407": {
        "name": "Mistral Large",
        "provider": "Mistral",
        "api": "github",
        "description": "Mistral Large 2407 (GitHub Models)",
    },
    "github:Mistral-small": {
        "name": "Mistral Small",
        "provider": "Mistral",
        "api": "github",
        "description": "Mistral Small (GitHub Models)",
    },
    "gemini:gemini-2.0-flash": {
        "name": "Gemini 2.0 Flash",
        "provider": "Google",
        "api": "gemini",
        "description": "Google Gemini 2.0 Flash (fallback)",
    },
}

class AIProvider:
    def __init__(self, main_app=None):
        self.main_app = main_app
        self.github_token = os.environ.get("GITHUB_TOKEN", "")
        self.gemini_api_key = os.environ.get("GEMINI_API_KEY", "")
        self.active_model = "github:Meta-Llama-3.1-8B-Instruct"
        self.chat_history = []
        self.max_history = 50
        self.logger = self._setup_logger()
        self._detect_available_models()

    def _setup_logger(self):
        try:
            from src.utils.logger import setup_logger
            return setup_logger("AIProvider")
        except Exception:
            return None

    def _log(self, level, msg):
        if self.logger:
            getattr(self.logger, level, print)(msg)

    def _detect_available_models(self):
        for mid, info in AVAILABLE_MODELS.items():
            info["available"] = self._check_model_available(mid)

    def _check_model_available(self, model_id):
        if model_id.startswith("github:"):
            return bool(self.github_token)
        elif model_id.startswith("gemini:"):
            return bool(self.gemini_api_key)
        return False

    def get_available_models(self):
        return {mid: dict(info) for mid, info in AVAILABLE_MODELS.items()}

    def set_model(self, model_id):
        if model_id in AVAILABLE_MODELS:
            self.active_model = model_id
            self._log("info", f"Active model changed to: {model_id}")
        else:
            raise ValueError(f"Unknown model: {model_id}")

    def get_active_model(self):
        return self.active_model

    def _call_github_api(self, model, messages, stream=False, temperature=0.1, max_tokens=4096):
        url = f"{GITHUB_API_BASE}/chat/completions"
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.github_token}",
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode("utf-8"),
            headers=headers,
        )
        if stream:
            return self._stream_github(req)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read())
            return result["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            self._log("error", f"GitHub API HTTP {e.code}: {body}")
            return None
        except Exception as e:
            self._log("error", f"GitHub API error: {e}")
            return None

    def _stream_github(self, req):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                buffer = ""
                while True:
                    chunk = resp.read(1).decode("utf-8", errors="replace")
                    if not chunk:
                        break
                    buffer += chunk
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if line.startswith("data: "):
                            payload = line[6:]
                            if payload == "[DONE]":
                                return
                            try:
                                obj = json.loads(payload)
                                delta = obj.get("choices", [{}])[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                pass
        except Exception as e:
            self._log("error", f"GitHub stream error: {e}")

    def _call_gemini(self, messages, stream=False, temperature=0.1, max_tokens=4096):
        system = None
        chat_messages = []
        for msg in messages:
            if msg.get("role") == "system":
                system = msg["content"]
            else:
                chat_messages.append(msg)

        last_user = ""
        for msg in reversed(chat_messages):
            if msg.get("role") == "user":
                last_user = msg["content"]
                break

        prompt = last_user
        if system:
            prompt = f"{system}\n\nKullanici: {last_user}"

        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "topK": 1,
                "topP": 1,
                "maxOutputTokens": max_tokens,
            },
        }
        req = urllib.request.Request(
            f"{url}?key={self.gemini_api_key}",
            data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read())
            if "candidates" in result and result["candidates"]:
                return result["candidates"][0]["content"]["parts"][0]["text"]
            return None
        except Exception as e:
            self._log("error", f"Gemini API error: {e}")
            return None

    def _stream_gemini(self, messages):
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:streamGenerateContent?alt=sse"
        last_user = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user = msg["content"]
                break

        data = {
            "contents": [{"parts": [{"text": last_user}]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 4096},
        }
        req = urllib.request.Request(
            f"{url}&key={self.gemini_api_key}",
            data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                buffer = ""
                while True:
                    chunk = resp.read(1).decode("utf-8", errors="replace")
                    if not chunk:
                        break
                    buffer += chunk
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if line.startswith("data: "):
                            payload = line[6:]
                            try:
                                obj = json.loads(payload)
                                candidates = obj.get("candidates", [])
                                if candidates:
                                    parts = candidates[0].get("content", {}).get("parts", [])
                                    for part in parts:
                                        text = part.get("text", "")
                                        if text:
                                            yield text
                            except json.JSONDecodeError:
                                pass
        except Exception as e:
            self._log("error", f"Gemini stream error: {e}")

    def _build_system_prompt(self, task_context=""):
        return f"""Sen Accura Finance muhasebe yaziliminin yapay zeka asistanisin.
Türkiye muhasebe standartlarina (TMS/TFRS) ve Vergi Usul Kanunu'na (VUK) hakimsin.
Kullanicilara Turkce olarak yardimci oluyorsun.
Cevap verirken kisa, oz ve profesyonel ol.
{task_context}

Finansal terimleri Turkce kullan:
- Gelir tablosu, bilanco, mizan
- Borc, alacak, bakiye
- KDV, gelir vergisi, kurumlar vergisi
- Fatura, irsaliye, makbuz"""

    def chat(self, messages, stream=False):
        """Send chat messages to active model.

        messages: list of dicts with 'role' and 'content' keys
        stream: if True, returns generator for streaming response
        """
        model_info = AVAILABLE_MODELS.get(self.active_model, {})
        api_type = model_info.get("api", "")

        full_messages = list(messages)

        if api_type == "github":
            model_name = self.active_model.replace("github:", "", 1)
            if stream:
                return self._call_github_api(model_name, full_messages, stream=True)
            return self._call_github_api(model_name, full_messages)
        elif api_type == "gemini":
            if stream:
                return self._stream_gemini(full_messages)
            return self._call_gemini(full_messages)
        return None

    def _get_json_from_response(self, response):
        if not response:
            return {"raw": ""}
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {"raw": response}
        except Exception:
            return {"raw": response}

    def analyze_invoice(self, invoice_text):
        model_info = AVAILABLE_MODELS.get(self.active_model, {})
        api_type = model_info.get("api", "")
        system = self._build_system_prompt("Fatura analizi ve bilgi cikarimi uzmanisin.")

        prompt = f"""Asagidaki fatura metnini analiz et ve JSON formatinda cikti ver:

Fatura Metni:
{invoice_text}

Su formatta JSON ciktisi ver (sadece JSON, baska metin yok):
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
}}"""

        messages = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]

        if api_type == "github":
            model_name = self.active_model.replace("github:", "", 1)
            response = self._call_github_api(model_name, messages)
        else:
            response = self._call_gemini(messages)

        return self._get_json_from_response(response)

    def analyze_financial(self, financial_data, analysis_type="genel"):
        analysis_prompts = {
            "genel": "Genel finansal durum analizi yap.",
            "likidite": "Likidite analizi yap (cari oran, likidite orani, nakit orani).",
            "karlilik": "Karlilik analizi yap (brut kar, net kar, ROS, ROA, ROE).",
            "borc": "Borcluluk analizi yap (kaldirac orani, borc/ozkaynak).",
            "nakit": "Nakit akis analizi yap.",
        }
        instruction = analysis_prompts.get(analysis_type, analysis_prompts["genel"])
        system = self._build_system_prompt(f"Finansal analiz uzmanisin. {instruction}")

        prompt = f"""Asagidaki finansal verileri analiz et:

Veriler:
{json.dumps(financial_data, indent=2, ensure_ascii=False) if isinstance(financial_data, (dict, list)) else financial_data}

Analizinde su hususlari degerlendir:
1. Genel durum degerlendirmesi
2. Oran analizi
3. Trend degerlendirmesi
4. Risk faktorleri
5. Oneriler"""

        messages = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]

        model_info = AVAILABLE_MODELS.get(self.active_model, {})
        api_type = model_info.get("api", "")
        if api_type == "github":
            model_name = self.active_model.replace("github:", "", 1)
            return self._call_github_api(model_name, messages)
        else:
            return self._call_gemini(messages)

    def calculate_payroll(self, employee_data):
        system = self._build_system_prompt(
            "Bordro ve maas hesaplama uzmanisin. 2025 yili Turk vergi mevzuatina gore hesaplama yap."
        )

        prompt = f"""Asagidaki personel verilerine gore bordro hesaplamasi yap:

Personel Bilgileri:
{json.dumps(employee_data, indent=2, ensure_ascii=False) if isinstance(employee_data, (dict, list)) else employee_data}

Su kalemleri hesapla:
1. Brut maas
2. SGK isci payi (%14)
3. Issizlik sigortasi isci payi (%1)
4. Gelir vergisi matrahi
5. Gelir vergisi
6. Damga vergisi
7. Kesintiler toplami
8. Net maas
9. Isveren maliyeti (SGK %15.5 + issizlik %2)

JSON formatinda cikti ver (sadece JSON):"""

        messages = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]

        model_info = AVAILABLE_MODELS.get(self.active_model, {})
        api_type = model_info.get("api", "")
        if api_type == "github":
            model_name = self.active_model.replace("github:", "", 1)
            response = self._call_github_api(model_name, messages)
        else:
            response = self._call_gemini(messages)

        return self._get_json_from_response(response)

    def test_connection(self):
        model_info = AVAILABLE_MODELS.get(self.active_model, {})
        api_type = model_info.get("api", "")
        messages = [
            {"role": "system", "content": "Kisa bir selamlama mesaji ver."},
            {"role": "user", "content": "Merhaba, test mesaji."},
        ]
        if api_type == "github":
            if not self.github_token:
                return False, "GitHub token ayarlanmamis."
            model_name = self.active_model.replace("github:", "", 1)
            response = self._call_github_api(model_name, messages)
        else:
            if not self.gemini_api_key:
                return False, "Gemini API key ayarlanmamis."
            response = self._call_gemini(messages)
        if response:
            return True, response.strip()
        return False, "Baglanti basarisiz."


ai_provider = AIProvider()

def get_ai_provider():
    return ai_provider
