"""
Accura Finance - GitHub Entegrasyon Modülü
- GitHub reposundan fatura dosyalarını otomatik işleme
- GitHub Issues üzerinden muhasebe talepleri
- Otomatik senkronizasyon
"""

import json
import os
import re
import base64
import threading
from datetime import datetime, date
import traceback

class GitHubIntegration:
    def __init__(self, db_manager=None, token=None, repo_owner="CodeByPinar", repo_name="accura-finance"):
        self.db_manager = db_manager
        self.token = token or os.environ.get("GITHUB_TOKEN", "")
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.api_base = "https://api.github.com"
        self.logger = self._setup_logger()

    def _setup_logger(self):
        try:
            from src.utils.logger import setup_logger
            return setup_logger("GitHubIntegration")
        except:
            return None

    def _api_call(self, endpoint, method="GET", data=None):
        """GitHub API çağrısı yap"""
        try:
            import urllib.request
            import urllib.parse

            url = f"{self.api_base}{endpoint}"
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "AccuraFinance/1.0"
            }
            if self.token:
                headers["Authorization"] = f"token {self.token}"

            if data:
                data = json.dumps(data).encode()
                headers["Content-Type"] = "application/json"

            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read())
        except Exception as e:
            if self.logger:
                self.logger.error(f"GitHub API hatası ({endpoint}): {e}")
            return {"error": str(e)}

    def list_invoice_files(self):
        """GitHub reposundaki fatura dosyalarını listele"""
        try:
            contents = self._api_call(f"/repos/{self.repo_owner}/{self.repo_name}/contents/data/invoices")
            if "error" in contents:
                return {"error": contents["error"], "files": []}

            invoice_files = []
            for item in contents:
                if item["type"] == "file" and item["name"].endswith((".txt", ".json", ".csv", ".xml")):
                    invoice_files.append({
                        "name": item["name"],
                        "path": item["path"],
                        "url": item["download_url"],
                        "size": item["size"]
                    })
            return {"files": invoice_files}
        except Exception as e:
            return {"error": str(e), "files": []}

    def download_invoice_file(self, file_path):
        """GitHub'dan fatura dosyasını indir"""
        try:
            content = self._api_call(f"/repos/{self.repo_owner}/{self.repo_name}/contents/{file_path}")
            if "error" in content:
                return None
            if content.get("encoding") == "base64":
                return base64.b64decode(content["content"]).decode("utf-8")
            return content.get("content", "")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Dosya indirme hatası: {e}")
            return None

    def upload_invoice_file(self, file_path, content, commit_message="Yeni fatura eklendi [Accura AI]"):
        """GitHub reposuna fatura dosyası yükle"""
        try:
            encoded = base64.b64encode(content.encode()).decode()

            data = {
                "message": commit_message,
                "content": encoded,
                "branch": "main"
            }

            result = self._api_call(
                f"/repos/{self.repo_owner}/{self.repo_name}/contents/{file_path}",
                method="PUT",
                data=data
            )
            return result
        except Exception as e:
            if self.logger:
                self.logger.error(f"Dosya yükleme hatası: {e}")
            return {"error": str(e)}

    def create_issue(self, title, body, labels=["muhasebe"]):
        """GitHub Issues'e muhasebe talebi oluştur"""
        try:
            data = {
                "title": title,
                "body": body,
                "labels": labels
            }
            result = self._api_call(
                f"/repos/{self.repo_owner}/{self.repo_name}/issues",
                method="POST",
                data=data
            )
            return result
        except Exception as e:
            if self.logger:
                self.logger.error(f"Issue oluşturma hatası: {e}")
            return {"error": str(e)}

    def list_issues(self, state="open", labels=["muhasebe"]):
        """Muhasebe ile ilgili GitHub Issues'leri listele"""
        try:
            labels_str = ",".join(labels)
            issues = self._api_call(
                f"/repos/{self.repo_owner}/{self.repo_name}/issues?state={state}&labels={labels_str}"
            )
            if "error" in issues:
                return []
            return [{
                "number": i["number"],
                "title": i["title"],
                "body": i["body"],
                "state": i["state"],
                "created_at": i["created_at"],
                "url": i["html_url"]
            } for i in issues]
        except Exception as e:
            return []

    def close_issue(self, issue_number, comment="İşlem tamamlandı [Accura AI]"):
        """Issues'i kapat"""
        try:
            self._api_call(
                f"/repos/{self.repo_owner}/{self.repo_name}/issues/{issue_number}/comments",
                method="POST",
                data={"body": comment}
            )
            result = self._api_call(
                f"/repos/{self.repo_owner}/{self.repo_name}/issues/{issue_number}",
                method="PATCH",
                data={"state": "closed"}
            )
            return result
        except Exception as e:
            return {"error": str(e)}

    def sync_invoices_from_github(self):
        """GitHub'daki faturaları senkronize et"""
        result = self.list_invoice_files()
        invoices = []

        for file_info in result.get("files", []):
            content = self.download_invoice_file(file_info["path"])
            if content:
                invoices.append({
                    "filename": file_info["name"],
                    "content": content,
                    "path": file_info["path"]
                })

        return invoices

    def auto_process_invoice(self, invoice_data):
        """Faturayı otomatik işle - AI ile analiz et ve veritabanına kaydet"""
        try:
            from src.ai_agent import get_ai_agent
            ai = get_ai_agent()

            invoice_text = invoice_data.get("content", "")
            filename = invoice_data.get("filename", "bilinmeyen.txt")

            ai_result = ai.process_invoice_text(invoice_text)
            if "raw" in ai_result:
                return {"status": "error", "message": "Fatura işlenemedi", "raw": ai_result["raw"]}

            invoice_record = {
                "fatura_no": ai_result.get("fatura_no", f"GH-{datetime.now().strftime('%Y%m%d%H%M%S')}"),
                "fatura_turu": ai_result.get("fatura_turu", "Satis"),
                "tarih": ai_result.get("tarih", datetime.now().strftime("%d.%m.%Y")),
                "cari_unvan": ai_result.get("cari_unvan", ""),
                "vergi_no": ai_result.get("vergi_no", ""),
                "ara_toplam": ai_result.get("ara_toplam", 0),
                "kdv_toplam": ai_result.get("kdv_toplam", 0),
                "genel_toplam": ai_result.get("genel_toplam", 0),
                "kaynak": f"github:{filename}",
                "islenme_tarihi": datetime.now().isoformat()
            }

            try:
                if self.db_manager:
                    self._save_to_database(invoice_record)
            except Exception as db_err:
                invoice_record["db_error"] = str(db_err)
                return {"status": "error", "message": "Veritabanina kayit basarisiz", "invoice": invoice_record}

            return {"status": "success", "invoice": invoice_record}

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _save_to_database(self, invoice_record):
        """Fatura kaydını veritabanına ekle"""
        try:
            # Cari hesap kontrolü
            cari_query = "SELECT CurrentAccountID FROM CurrentAccounts WHERE TaxNumber = ?"
            cari_result = self.db_manager.execute_query(cari_query, (invoice_record["vergi_no"],))

            if cari_result:
                cari_id = cari_result[0]["CurrentAccountID"]
            else:
                cari_id = None

            # Fatura numarası oluştur
            invoice_no = f"GH-{datetime.now().strftime('%Y%m%d%H%M%S')}"

            inv_type = "Satis" if invoice_record["fatura_turu"] in ["Satis", "satış", "Sale"] else "Alis"

            invoice_query = """
            INSERT INTO Invoices (InvoiceNumber, InvoiceType, InvoiceDate, CurrentAccountID,
                SubTotal, VATAmount, TotalAmount, Notes, CreatedDate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
            """
            self.db_manager.execute_query(invoice_query, (
                invoice_no,
                inv_type,
                invoice_record["tarih"],
                cari_id,
                invoice_record["ara_toplam"],
                invoice_record["kdv_toplam"],
                invoice_record["genel_toplam"],
                f"GitHub'dan otomatik işlendi - {invoice_record.get('kaynak', '')}"
            ), fetch=False)

        except Exception as e:
            if self.logger:
                self.logger.error(f"Veritabanı kayıt hatası: {e}")
            raise

_github_integration_instance = None
_github_lock = threading.Lock()

def get_github_integration(db_manager=None):
    global _github_integration_instance
    if _github_integration_instance is None:
        with _github_lock:
            if _github_integration_instance is None:
                _github_integration_instance = GitHubIntegration()
    if db_manager is not None:
        _github_integration_instance.db_manager = db_manager
    return _github_integration_instance
