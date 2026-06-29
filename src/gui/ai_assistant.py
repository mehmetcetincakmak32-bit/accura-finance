"""
Accura Finance - AI Muhasebe Asistanı
Gemini AI ile akıllı muhasebe danışmanı
"""

import customtkinter as ctk
from datetime import datetime
import threading
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class AIAssistantFrame(ctk.CTkFrame):
    def __init__(self, parent, main_app):
        super().__init__(parent)
        self.parent = parent
        self.main_app = main_app
        self.ai_agent = None
        self.db_manager = main_app.db_manager
        self.chat_history = []

        self._init_ai()
        self.pack(fill="both", expand=True)
        self.create_interface()

    def _init_ai(self):
        try:
            from src.ai_agent import get_ai_agent
            self.ai_agent = get_ai_agent()
        except:
            pass

    def create_interface(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, height=60, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(header, text="🤖 AI Muhasebe Asistanı",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=("#7b1fa2", "#ce93d8")).pack(side="left", padx=20, pady=15)

        status = ctk.CTkLabel(header, text="✅ AI Aktif",
            font=ctk.CTkFont(size=12), text_color="#2e7d32")
        status.pack(side="right", padx=20)

        chat_frame = ctk.CTkFrame(self, corner_radius=10)
        chat_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        chat_frame.grid_columnconfigure(0, weight=1)
        chat_frame.grid_rowconfigure(0, weight=1)

        self.chat_display = ctk.CTkTextbox(chat_frame, font=ctk.CTkFont(size=13),
            wrap="word", state="disabled")
        self.chat_display.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self._add_system_message(
            "🤖 Merhaba! Ben Accura Finance AI Asistanı.\n\n"
            "Size şu konularda yardımcı olabilirim:\n"
            "• 💰 Muhasebe kaydı önerme\n"
            "• 📊 Finansal analiz\n"
            "• 📄 Fatura işleme\n"
            "• 📈 Rapor oluşturma\n"
            "• ❓ Genel muhasebe bilgisi"
        )

        input_frame = ctk.CTkFrame(chat_frame, height=100, corner_radius=8)
        input_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        input_frame.grid_columnconfigure(0, weight=1)

        self.message_entry = ctk.CTkTextbox(input_frame, height=60,
            font=ctk.CTkFont(size=13), wrap="word")
        self.message_entry.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        self.message_entry.bind("<Control-Return>", self.send_message)

        send_btn = ctk.CTkButton(input_frame, text="🚀 Gönder",
            command=self.send_message, fg_color="#7b1fa2",
            height=40, width=100, font=ctk.CTkFont(size=13, weight="bold"))
        send_btn.grid(row=0, column=1, padx=(0, 10), pady=10)

    def _add_message(self, sender, message):
        self.chat_display.configure(state="normal")
        timestamp = datetime.now().strftime("%H:%M")
        if sender == "user":
            self.chat_display.insert("end", f"\n🧑‍💼 Siz ({timestamp}):\n{message}\n\n",
                "user_message")
            self.chat_display.tag_config("user_message",
                foreground=("#1565c0", "#64b5f6"))
        else:
            self.chat_display.insert("end", f"\n🤖 AI Asistan ({timestamp}):\n{message}\n\n",
                "ai_message")
            self.chat_display.tag_config("ai_message",
                foreground=("#7b1fa2", "#ce93d8"))
        self.chat_display.see("end")
        self.chat_display.configure(state="disabled")

    def _add_system_message(self, message):
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", f"\n{message}\n\n", "system_message")
        self.chat_display.tag_config("system_message",
            foreground=("#546e7a", "#90a4ae"),
            font=ctk.CTkFont(size=12, slant="italic"))
        self.chat_display.see("end")
        self.chat_display.configure(state="disabled")

    def send_message(self, event=None):
        message = self.message_entry.get("1.0", "end-1c").strip()
        if not message:
            return

        self._add_message("user", message)
        self.message_entry.delete("1.0", "end")

        def get_ai_response():
            if self.ai_agent:
                context = self._get_financial_context()
                response = self.ai_agent.chat(message, context)
            else:
                response = self._local_response(message)

            self.after(0, lambda: self._add_message("ai", response))

        threading.Thread(target=get_ai_response, daemon=True).start()

    def _get_financial_context(self):
        context = {"tarih": datetime.now().isoformat()}
        try:
            if self.db_manager:
                sales = self.db_manager.execute_query(
                    "SELECT COALESCE(SUM(TotalAmount),0) as total FROM Invoices WHERE InvoiceType='Satis'")
                purchases = self.db_manager.execute_query(
                    "SELECT COALESCE(SUM(TotalAmount),0) as total FROM Invoices WHERE InvoiceType='Alis'")
                context["aylik_satis"] = sales[0]["total"] if sales else 0
                context["aylik_alis"] = purchases[0]["total"] if purchases else 0
        except:
            pass
        return context

    def _local_response(self, message):
        message_lower = message.lower()

        if any(k in message_lower for k in ["merhaba", "selam", "hello", "hi"]):
            return "Merhaba! Size nasıl yardımcı olabilirim? Muhasebe, fatura, raporlama veya finansal analiz konularında sorularınızı bekliyorum."

        if any(k in message_lower for k in ["fatura", "invoice"]):
            return ("📄 Fatura işlemleri:\n\n"
                    "1. Yeni fatura oluşturma\n"
                    "2. Fatura listeleme\n"
                    "3. AI ile fatura işleme\n"
                    "4. GitHub'dan fatura içe aktarma\n\n"
                    "Hangi işlemi yapmak istersiniz?")

        if any(k in message_lower for k in ["rapor", "report", "mizan"]):
            return ("📊 Raporlama seçenekleri:\n\n"
                    "• Mizan raporu\n"
                    "• Gelir tablosu\n"
                    "• Bilanço\n"
                    "• KDV raporu\n"
                    "• Cari hesap ekstresi\n\n"
                    "Hangi raporu oluşturmak istersiniz?")

        if any(k in message_lower for k in ["muhasebe", "kayıt", "kaydet"]):
            return ("📝 Muhasebe kaydı için:\n\n"
                    "İşlem türünü ve tutarını belirtin, ben uygun muhasebe kaydını önereyim.\n\n"
                    "Örnek: '1000 TL kira ödemesi yapıldı'")

        if any(k in message_lower for k in ["analiz", "analiz et", "finans"]):
            return ("📈 Finansal analiz için:\n\n"
                    "Mevcut verilerinizle kapsamlı bir analiz yapabilirim.\n"
                    "Lütfen hangi dönemi analiz etmek istediğinizi belirtin.")

        return ("Anladım. Size yardımcı olabilmem için lütfen daha spesifik bir soru sorun.\n\n"
                "Önerilen konular:\n"
                "• 💰 'Kira ödemesi kaydı' gibi muhasebe işlemleri\n"
                "• 📄 'Faturayı işle' gibi fatura talepleri\n"
                "• 📊 'Rapor oluştur' gibi rapor talepleri\n"
                "• 📈 'Analiz yap' gibi finansal analiz talepleri")
