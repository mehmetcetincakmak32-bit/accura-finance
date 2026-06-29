import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os

PRIMARY = "#1565c0"
PRIMARY_DARK = "#0d47a1"
SUCCESS = "#2e7d32"
DANGER = "#c62828"
WARNING = "#f57f17"
TEXT_DARK = "#1a1a2e"
TEXT_MUTED = "#6c757d"
BORDER = "#e8eaed"


class AIProviderSelector(ctk.CTkToplevel):
    def __init__(self, parent, main_app, on_model_change=None):
        super().__init__(parent)
        self.parent = parent
        self.main_app = main_app
        self.on_model_change = on_model_change
        self.ai_provider = None
        self._init_provider()

        self.title("AI Model Secici")
        self.geometry("540x500")
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)

        self.grid_columnconfigure(0, weight=1)

        self.create_widgets()
        self.refresh_status()

    def _init_provider(self):
        try:
            from src.ai_providers import get_ai_provider
            self.ai_provider = get_ai_provider()
        except Exception as e:
            messagebox.showerror("Hata", f"AI provider yuklenemedi: {e}")
            self.destroy()

    def create_widgets(self):
        header = ctk.CTkFrame(self, height=50, corner_radius=10, fg_color="#ffffff")
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        header.grid_propagate(False)
        ctk.CTkLabel(
            header, text="AI MODEL SECICI",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=PRIMARY_DARK
        ).pack(side="left", padx=20, pady=10)
        ctk.CTkLabel(
            header, text="GitHub Models / Gemini",
            font=ctk.CTkFont(size=11), text_color=TEXT_MUTED
        ).pack(side="left", padx=5, pady=10)

        content = ctk.CTkFrame(self, corner_radius=10, fg_color="#ffffff",
                                border_width=1, border_color=BORDER)
        content.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        content.grid_columnconfigure(0, weight=1)

        # Model selection
        ctk.CTkLabel(content, text="Aktif Model",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=TEXT_DARK).grid(row=0, column=0, sticky="w", padx=20, pady=(16, 5))

        self.model_var = tk.StringVar()
        models = list(self.ai_provider.get_available_models().keys())
        self.model_combo = ctk.CTkComboBox(
            content, values=models,
            variable=self.model_var,
            command=self._on_model_select,
            height=38, font=ctk.CTkFont(size=13), state="readonly"
        )
        self.model_combo.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 5))
        self.model_var.set(self.ai_provider.get_active_model())

        # Status frame
        status_frame = ctk.CTkFrame(content, fg_color="transparent")
        status_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=5)
        status_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(status_frame, text="Model Durumu:",
                     font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, sticky="w")

        self.status_label = ctk.CTkLabel(
            status_frame, text="Kontrol ediliyor...",
            font=ctk.CTkFont(size=12), text_color=TEXT_MUTED
        )
        self.status_label.grid(row=0, column=1, sticky="w", padx=10)

        # Model info
        self.model_info_text = ctk.CTkTextbox(
            content, height=60, wrap="word",
            font=ctk.CTkFont(size=11), fg_color="#f8f9fa",
            border_width=1, border_color=BORDER
        )
        self.model_info_text.grid(row=3, column=0, sticky="ew", padx=20, pady=5)
        self.model_info_text.configure(state="disabled")

        # Separator
        ttk.Separator(content, orient="horizontal").grid(
            row=4, column=0, sticky="ew", padx=20, pady=(15, 5)
        )

        # GitHub Token section
        ctk.CTkLabel(content, text="GitHub Token Yapilandirmasi",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=TEXT_DARK).grid(row=5, column=0, sticky="w", padx=20, pady=(10, 5))

        token_frame = ctk.CTkFrame(content, fg_color="transparent")
        token_frame.grid(row=6, column=0, sticky="ew", padx=20, pady=5)
        token_frame.grid_columnconfigure(1, weight=1)

        self.token_entry = ctk.CTkEntry(
            token_frame, height=35, font=ctk.CTkFont(size=12),
            placeholder_text="github_pat_... veya GITHUB_TOKEN env degiskeni", show="*"
        )
        self.token_entry.grid(row=0, column=0, columnspan=3, sticky="ew", pady=3)

        env_token = os.environ.get("GITHUB_TOKEN", "")
        if env_token:
            self.token_entry.insert(0, env_token)
            self.token_entry.configure(state="readonly")

        ctk.CTkButton(
            token_frame, text="Tokeni Kaydet", command=self._save_token,
            fg_color=PRIMARY, height=32, font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=1, column=0, sticky="w", padx=(0, 5), pady=5)

        ctk.CTkButton(
            token_frame, text="Test Baglantisi", command=self._test_connection,
            fg_color=WARNING, height=32, font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=1, column=1, sticky="w", padx=5, pady=5)

        # Available models list
        ctk.CTkLabel(content, text="Kullanilabilir Modeller",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=TEXT_DARK).grid(row=7, column=0, sticky="w", padx=20, pady=(10, 5))

        columns = ("Model", "Saglayici", "Durum")
        self.models_tree = ttk.Treeview(
            content, columns=columns, show="headings", height=5, selectmode="browse"
        )
        for col, w in zip(columns, [220, 120, 100]):
            self.models_tree.heading(col, text=col)
            self.models_tree.column(col, width=w, anchor="center")

        scroll = ttk.Scrollbar(content, orient="vertical", command=self.models_tree.yview)
        self.models_tree.configure(yscrollcommand=scroll.set)
        self.models_tree.grid(row=8, column=0, sticky="ew", padx=20, pady=5)
        scroll.grid(row=8, column=1, sticky="ns", pady=5)

        # Close button
        ctk.CTkButton(
            self, text="Kapat", command=self.destroy,
            fg_color=TEXT_MUTED, height=38, font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=2, column=0, pady=(5, 10))

    def _on_model_select(self, choice):
        if not choice:
            return
        try:
            self.ai_provider.set_model(choice)
            if self.on_model_change:
                self.on_model_change(choice)
            self._update_model_info(choice)
            self.status_label.configure(text="Model degistirildi", text_color=SUCCESS)
        except ValueError as e:
            messagebox.showerror("Hata", str(e))

    def _update_model_info(self, model_id):
        models = self.ai_provider.get_available_models()
        info = models.get(model_id, {})
        text = f"  {info.get('description', model_id)}"
        if info.get("available"):
            text += "\n  Durum: Baglanti hazir"
        else:
            text += "\n  Durum: Token/API anahtari eksik"
        self.model_info_text.configure(state="normal")
        self.model_info_text.delete("0.0", "end")
        self.model_info_text.insert("0.0", text)
        self.model_info_text.configure(state="disabled")

    def refresh_status(self):
        models = self.ai_provider.get_available_models()
        active = self.ai_provider.get_active_model()
        active_info = models.get(active, {})

        for item in self.models_tree.get_children():
            self.models_tree.delete(item)

        for mid, info in models.items():
            durum = "Hazir" if info.get("available") else "Anahtar Eksik"
            tag = "available" if info.get("available") else "unavailable"
            self.models_tree.insert("", "end", iid=mid, values=(
                info.get("name", mid), info.get("provider", ""), durum
            ), tags=(tag,))

        self.models_tree.tag_configure("available", foreground="#2e7d32")
        self.models_tree.tag_configure("unavailable", foreground="#c62828")

        if active_info.get("available"):
            self.status_label.configure(text="Baglanti hazir", text_color=SUCCESS)
        else:
            self.status_label.configure(text="Anahtar eksik - Gemini fallback kullanilacak", text_color=DANGER)

        self._update_model_info(active)

    def _save_token(self):
        token = self.token_entry.get().strip()
        if not token:
            messagebox.showwarning("Uyari", "Lutfen bir GitHub token girin.")
            return
        try:
            import json
            import os
            config_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "data"
            )
            os.makedirs(config_dir, exist_ok=True)
            config_path = os.path.join(config_dir, ".env")
            env_data = {}
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if "=" in line:
                            k, v = line.split("=", 1)
                            env_data[k.strip()] = v.strip()
            env_data["GITHUB_TOKEN"] = token
            with open(config_path, "w", encoding="utf-8") as f:
                for k, v in env_data.items():
                    f.write(f"{k}={v}\n")
            os.environ["GITHUB_TOKEN"] = token
            self.ai_provider.github_token = token
            self.ai_provider._detect_available_models()
            self.refresh_status()
            messagebox.showinfo("Basarili", "GitHub token kaydedildi. Yeniden baslatmaya gerek yok.")
        except Exception as e:
            messagebox.showerror("Hata", f"Token kaydedilemedi: {e}")

    def _test_connection(self):
        def run_test():
            success, result = self.ai_provider.test_connection()
            self.after(0, lambda: self._show_test_result(success, result))

        self.status_label.configure(text="Test ediliyor...", text_color=WARNING)
        threading.Thread(target=run_test, daemon=True).start()

    def _show_test_result(self, success, result):
        if success:
            self.status_label.configure(text="Baglanti basarili", text_color=SUCCESS)
            messagebox.showinfo("Basari", f"AI modeline baglanti basarili!\n\nYanit:\n{result[:200]}")
        else:
            self.status_label.configure(text="Baglanti hatasi", text_color=DANGER)
            messagebox.showerror("Hata", f"Baglanti basarisiz:\n{result}")
