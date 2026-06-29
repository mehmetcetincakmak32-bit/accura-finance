"""
Accura Finance - Bildirim Servisi
E-posta ve SMS bildirim işlemleri
"""

import os
import smtplib
import ssl
import json
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any
from pathlib import Path

from src.utils.logger import setup_logger
from src.database.connection import get_database_manager


class NotificationService:
    """E-posta ve SMS bildirim servisi"""

    def __init__(self, db_manager=None):
        self.db = db_manager or get_database_manager()
        self.logger = setup_logger('NotificationService')

    def get_email_settings(self) -> Dict:
        try:
            settings = {}
            rows = self.db.execute_query(
                "SELECT SettingKey, SettingValue FROM SystemSettings WHERE SettingKey LIKE 'email.%'"
            )
            for row in rows:
                key = row['SettingKey'].replace('email.', '', 1)
                settings[key] = row['SettingValue']
            return settings
        except Exception as e:
            self.logger.error(f"E-posta ayarlari alinamadi: {e}")
            return {}

    def _save_email_settings(self, settings: Dict):
        for key, value in settings.items():
            try:
                full_key = f"email.{key}"
                existing = self.db.execute_query(
                    "SELECT COUNT(*) as cnt FROM SystemSettings WHERE SettingKey = ?", (full_key,)
                )
                if existing and existing[0]['cnt'] > 0:
                    self.db.execute_query(
                        "UPDATE SystemSettings SET SettingValue = ?, UpdatedDate = datetime('now','localtime') WHERE SettingKey = ?",
                        (str(value), full_key), fetch=False
                    )
                else:
                    self.db.execute_query(
                        "INSERT INTO SystemSettings (SettingKey, SettingValue, Description) VALUES (?, ?, 'E-posta ayari')",
                        (full_key, str(value)), fetch=False
                    )
            except Exception as e:
                self.logger.error(f"Ayar kaydedilemedi: {key} - {e}")

    def test_email_connection(self) -> Dict:
        settings = self.get_email_settings()
        if not settings.get('smtp_server') or not settings.get('smtp_port'):
            return {'success': False, 'message': 'SMTP ayarlari eksik'}

        try:
            smtp_port = int(settings.get('smtp_port', 587))
            use_tls = settings.get('use_tls', 'true').lower() == 'true'
            use_ssl = settings.get('use_ssl', 'false').lower() == 'true'

            if use_ssl:
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(
                    settings['smtp_server'], smtp_port, context=context, timeout=10
                )
            else:
                server = smtplib.SMTP(settings['smtp_server'], smtp_port, timeout=10)
                if use_tls:
                    context = ssl.create_default_context()
                    server.starttls(context=context)

            username = settings.get('smtp_username', '')
            password = settings.get('smtp_password', '')
            if username and password:
                server.login(username, password)

            server.quit()
            return {'success': True, 'message': 'Baglanti basarili'}

        except smtplib.SMTPAuthenticationError:
            return {'success': False, 'message': 'Kullanici adi veya sifre hatali'}
        except smtplib.SMTPException as e:
            return {'success': False, 'message': f'SMTP hatasi: {str(e)}'}
        except Exception as e:
            return {'success': False, 'message': f'Baglanti hatasi: {str(e)}'}

    def send_email(self, to: str, subject: str, body: str,
                   attachments: List[str] = None) -> bool:
        settings = self.get_email_settings()
        if not settings.get('smtp_server'):
            self.logger.error("SMTP ayarlari yapilmamis")
            return False

        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = settings.get('from_address', settings.get('smtp_username', ''))
            msg['To'] = to if isinstance(to, str) else ', '.join(to)
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'html' if '<html>' in body or '<p>' in body else 'plain', 'utf-8'))

            if attachments:
                for filepath in attachments:
                    if os.path.exists(filepath):
                        with open(filepath, 'rb') as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename="{os.path.basename(filepath)}"'
                            )
                            msg.attach(part)

            smtp_port = int(settings.get('smtp_port', 587))
            use_tls = settings.get('use_tls', 'true').lower() == 'true'
            use_ssl = settings.get('use_ssl', 'false').lower() == 'true'

            if use_ssl:
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(
                    settings['smtp_server'], smtp_port, context=context, timeout=30
                )
            else:
                server = smtplib.SMTP(settings['smtp_server'], smtp_port, timeout=30)
                if use_tls:
                    context = ssl.create_default_context()
                    server.starttls(context=context)

            username = settings.get('smtp_username', '')
            password = settings.get('smtp_password', '')
            if username and password:
                server.login(username, password)

            server.send_message(msg)
            server.quit()

            recipient_list = [to] if isinstance(to, str) else to
            self.logger.info(f"E-posta gonderildi: {subject} -> {', '.join(recipient_list)}")
            return True

        except Exception as e:
            self.logger.error(f"E-posta gonderilemedi: {e}")
            return False

    def send_sms(self, phone: str, message: str) -> bool:
        settings = {}
        try:
            rows = self.db.execute_query(
                "SELECT SettingKey, SettingValue FROM SystemSettings WHERE SettingKey LIKE 'sms.%'"
            )
            for row in rows:
                key = row['SettingKey'].replace('sms.', '', 1)
                settings[key] = row['SettingValue']
        except Exception:
            pass

        if not settings.get('api_url'):
            self.logger.error("SMS ayarlari yapilmamis")
            return False

        try:
            import requests
            payload = {
                'api_key': settings.get('api_key', ''),
                'api_secret': settings.get('api_secret', ''),
                'sender': settings.get('sender', ''),
                'to': phone,
                'message': message[:160]
            }
            response = requests.post(
                settings['api_url'],
                json=payload,
                timeout=10
            )
            if response.ok:
                self.logger.info(f"SMS gonderildi: {phone}")
                return True
            else:
                self.logger.error(f"SMS hatasi: {response.text}")
                return False

        except ImportError:
            self.logger.warning("requests kutuphanesi yok. SMS gonderilemedi.")
            return False
        except Exception as e:
            self.logger.error(f"SMS gonderilemedi: {e}")
            return False

    def send_report_via_email(self, to: str, report_path: str,
                              subject: str = None, body: str = None) -> bool:
        report_name = os.path.basename(report_path)
        if not subject:
            subject = f"Rapor: {report_name}"
        if not body:
            body = f"""
            <html><body>
            <p>Merhaba,</p>
            <p>Talep ettiginiz rapor ekte yer almaktadir.</p>
            <p><b>Dosya:</b> {report_name}<br>
            <b>Tarih:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
            <hr>
            <p style="color: #888; font-size: 11px;">Accura Finance - Otomatik Rapor Gonderimi</p>
            </body></html>
            """
        return self.send_email(to, subject, body, attachments=[report_path])

    def send_daily_summary(self) -> bool:
        try:
            today = date.today().isoformat()
            recipients_setting = self.db.execute_query(
                "SELECT SettingValue FROM SystemSettings WHERE SettingKey = 'email.summary_recipients'"
            )
            if not recipients_setting:
                self.logger.warning("Gunluk ozet alicilari tanimlanmamis")
                return False

            recipients = recipients_setting[0]['SettingValue'].split(',')
            recipients = [r.strip() for r in recipients if r.strip()]

            sales = self.db.execute_query("""
                SELECT COALESCE(COUNT(*), 0) as count, COALESCE(SUM(TotalAmount), 0) as total
                FROM Invoices WHERE InvoiceDate = ? AND InvoiceType = 'Satis'
            """, (today,))

            purchases = self.db.execute_query("""
                SELECT COALESCE(COUNT(*), 0) as count, COALESCE(SUM(TotalAmount), 0) as total
                FROM Invoices WHERE InvoiceDate = ? AND InvoiceType = 'Alis'
            """, (today,))

            cash_total = self.db.execute_query("""
                SELECT COALESCE(SUM(Amount), 0) as total
                FROM CashMovements WHERE date(MovementDate) = ?
            """, (today,))

            overdue = self.db.execute_query("""
                SELECT COUNT(*) as count, COALESCE(SUM(RemainingAmount), 0) as total
                FROM Invoices WHERE RemainingAmount > 0 AND DueDate < ?
            """, (today,))

            s = sales[0] if sales else {'count': 0, 'total': 0}
            p = purchases[0] if purchases else {'count': 0, 'total': 0}
            c = cash_total[0] if cash_total else {'total': 0}
            o = overdue[0] if overdue else {'count': 0, 'total': 0}

            body = f"""
            <html><body>
            <h2>Gunluk Ozet - {today}</h2>
            <table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse;">
                <tr style="background:#2C3E50;color:white;">
                    <th>Metrik</th><th>Deger</th>
                </tr>
                <tr><td><b>Satis Adedi</b></td><td>{s['count']}</td></tr>
                <tr><td><b>Satis Tutari</b></td><td>{float(s['total']):,.2f} TL</td></tr>
                <tr><td><b>Alis Adedi</b></td><td>{p['count']}</td></tr>
                <tr><td><b>Alis Tutari</b></td><td>{float(p['total']):,.2f} TL</td></tr>
                <tr><td><b>Kasa Hareketi</b></td><td>{float(c['total']):,.2f} TL</td></tr>
                <tr style="background:#FDEDEC;"><td><b>Gecikmis Fatura</b></td><td>{o['count']} adet - {float(o['total']):,.2f} TL</td></tr>
            </table>
            <hr>
            <p style="color: #888; font-size: 11px;">Accura Finance - Otomatik Gunluk Ozet</p>
            </body></html>
            """

            success = True
            for recipient in recipients:
                if not self.send_email(recipient, f"Gunluk Ozet - {today}", body):
                    success = False

            return success

        except Exception as e:
            self.logger.error(f"Gunluk ozet gonderilemedi: {e}")
            return False
