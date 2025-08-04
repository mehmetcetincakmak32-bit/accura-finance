<div align="center">

# 🏢 Accura Finance
### 💼 Profesyonel Muhasebe Yazılımı

<img width="1300" height="1024" alt="logo" src="https://github.com/user-attachments/assets/137c0448-143e-4155-b4e8-4f55235a70a1" />


[![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-00D4AA.svg?style=for-the-badge&logo=tkinter)](https://github.com/TomSchimansky/CustomTkinter)
[![SQL Server](https://img.shields.io/badge/Database-SQL%20Server-CC2927.svg?style=for-the-badge&logo=microsoft-sql-server&logoColor=white)](https://www.microsoft.com/sql-server)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

[![GitHub Stars](https://img.shields.io/github/stars/ThecoderPinar/accura-finance?style=for-the-badge&logo=github&color=gold)](https://github.com/ThecoderPinar/accura-finance/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/ThecoderPinar/accura-finance?style=for-the-badge&logo=github&color=blue)](https://github.com/ThecoderPinar/accura-finance/network)
[![GitHub Issues](https://img.shields.io/github/issues/ThecoderPinar/accura-finance?style=for-the-badge&logo=github&color=red)](https://github.com/ThecoderPinar/accura-finance/issues)
[![GitHub Downloads](https://img.shields.io/github/downloads/ThecoderPinar/accura-finance/total?style=for-the-badge&logo=github&color=green)](https://github.com/ThecoderPinar/accura-finance/releases)

**Modern, kullanıcı dostu ve tam kapsamlı muhasebe yazılımı**  
*Küçük ve orta ölçekli işletmeler için tasarlanmış profesyonel finansal yönetim çözümü*

🌟 [**Demo İzle**](https://github.com/ThecoderPinar/accura-finance#-demo) | 📚 [**Dokümantasyon**](docs/) | 🚀 [**Hızlı Başlangıç**](#-kurulum) | 💬 [**Destek**](https://github.com/ThecoderPinar/accura-finance/discussions)

</div>

---

## 📸 Ekran Görüntüleri

<div align="center">

### 🔐 Giriş Ekranı
<img src="docs/images/login.png" alt="Login Screen" width="600"/>

*Temiz ve minimal tasarım ile güvenli giriş*

### 📊 Ana Dashboard
<img src="docs/images/dashboard.png" alt="Dashboard" width="800"/>

*Finansal özetler, grafikler ve hızlı erişim butonları*

</div>

---

## ✨ Özellikler

<div align="center">
<table>
<tr>
<td align="center" width="33%">

### 🎯 Ana Modüller
🏠 **Dashboard** - Finansal özet ve grafikler  
👥 **Cari Hesaplar** - Müşteri/tedarikçi yönetimi  
💰 **Kasa & Banka** - Nakit akışı yönetimi  
📝 **Fatura Yönetimi** - Alış/satış faturaları  
📦 **Stok Yönetimi** - Envanter takibi  
📈 **Raporlama** - Mali tablolar ve analizler  
⚙️ **Muhasebe** - Hesap planı ve kayıtlar

</td>
<td align="center" width="33%">

### 🛠️ Teknik Özellikler
🖥️ **Modern GUI** - CustomTkinter arayüz  
🗄️ **Güçlü Veritabanı** - SQL Server entegrasyonu  
📊 **Grafik Desteği** - Matplotlib charts  
🔒 **Güvenlik** - Authentication sistemi  
💾 **Yedekleme** - Otomatik backup  
🌍 **Türkçe** - Tam Türkçe dil desteği  
⚡ **Performans** - Hızlı ve kararlı

</td>
<td align="center" width="33%">

### 📋 İş Süreçleri
💼 **KOBİ Odaklı** - Küçük/orta işletmeler  
📊 **Raporlama** - PDF/Excel çıktıları  
🔄 **Entegrasyon** - E-fatura hazırlığı  
👤 **Kullanıcı Dostu** - Kolay öğrenme  
🎨 **Modern Tasarım** - Şık arayüz  
📱 **Responsive** - Esnek pencere boyutu  
🔧 **Özelleştirilebilir** - Modüler yapı

</td>
</tr>
</table>
</div>

---

## 🚀 Hızlı Başlangıç

<div align="center">

### ⚡ 3 Adımda Kurulum

[![Step 1](https://img.shields.io/badge/1-İndir-blue?style=for-the-badge)](#1-projeyi-indirin)
[![Step 2](https://img.shields.io/badge/2-Kurulum-orange?style=for-the-badge)](#2-kurulum)
[![Step 3](https://img.shields.io/badge/3-Çalıştır-green?style=for-the-badge)](#3-çalıştırma)

</div>

## � Kurulum

<details>
<summary><b>📋 Sistem Gereksinimleri</b></summary>

| Gereksinim | Minimum | Önerilen |
|------------|---------|----------|
| **İşletim Sistemi** | Windows 10 | Windows 11 |
| **Python** | 3.8+ | 3.11+ |
| **RAM** | 4 GB | 8 GB |
| **Disk Alanı** | 1 GB | 2 GB |
| **Veritabanı** | SQL Server Express | SQL Server 2019+ |

</details>

### 1. 📥 Projeyi İndirin

```bash
# Git ile klonlayın
git clone https://github.com/ThecoderPinar/accura-finance.git
cd accura-finance

# Veya ZIP olarak indirin
# https://github.com/ThecoderPinar/accura-finance/archive/main.zip
```

### 2. 🔧 Kurulum

<details>
<summary><b>🐍 Sanal Ortam Oluşturma (Önerilen)</b></summary>

```bash
# Sanal ortam oluşturun
python -m venv venv

# Sanal ortamı aktifleştirin
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

</details>

```bash
# Bağımlılıkları yükleyin
pip install -r requirements.txt

# Veritabanını kurun
python setup_database.py
```

### 3. 🚀 Çalıştırma

```bash
/.run.bat # veya
```
```bash
python main.py 
```

<div align="center">

### 🔑 **Varsayılan Giriş Bilgileri**

| Kullanıcı Adı | Şifre |
|----------------|-------|
| `admin` | `admin123` |

⚠️ **İlk girişten sonra şifrenizi değiştirmeyi unutmayın!**

</div>

---

## 📁 Proje Yapısı

<details>
<summary><b>🗂️ Detaylı Klasör Yapısı</b></summary>

```
🏢 accura-finance/
├── 📂 src/                     # 🔧 Kaynak Kodlar
│   ├── 📂 gui/                 # 🖥️ Kullanıcı Arayüzü
│   │   ├── 🔐 login_window.py  # Giriş ekranı
│   │   ├── 📊 dashboard.py     # Ana dashboard
│   │   ├── 👥 customers.py     # Cari hesaplar
│   │   ├── 📝 accounting.py    # Muhasebe işlemleri
│   │   ├── 📦 inventory.py     # Stok yönetimi
│   │   ├── 📈 reports.py       # Raporlar
│   │   ├── ⚙️ settings.py      # Ayarlar
│   │   └── 🖼️ main_window.py   # Ana pencere
│   ├── 📂 database/            # 🗄️ Veritabanı
│   │   ├── 🔗 connection.py    # Bağlantı yönetimi
│   │   ├── 📋 models.py        # Veri modelleri
│   │   ├── 📊 initial_data.sql # Başlangıç verileri
│   │   └── 🔧 setup.py         # Kurulum scripti
│   ├── 📂 utils/               # 🛠️ Yardımcı Araçlar
│   │   ├── ⚙️ config.py        # Konfigürasyon
│   │   ├── 📝 logger.py        # Log yönetimi
│   │   ├── 🔒 security.py      # Güvenlik fonksiyonları
│   │   └── � pdf_generator.py # PDF oluşturucu
│   └── 📂 business/            # 💼 İş Mantığı
│       ├── 💰 accounting.py    # Muhasebe işlemleri
│       ├── 📝 invoice.py       # Fatura işlemleri
│       └── 📊 reporting.py     # Rapor işlemleri
├── 📂 data/                    # 📊 Veri Dosyaları
│   ├── 📂 exports/             # Dışa aktarılan dosyalar
│   ├── 📂 backups/             # Yedek dosyaları
│   ├── 📂 temp/                # Geçici dosyalar
│   └── ⚙️ user_config.json     # Kullanıcı ayarları
├── 📂 docs/                    # 📚 Dokümantasyon
│   ├── 📂 images/              # Ekran görüntüleri
│   ├── 📂 user_guide/          # Kullanıcı kılavuzu
│   └── 📂 api/                 # API dokümantasyonu
├── 📂 tests/                   # 🧪 Test Dosyaları
│   ├── 📂 unit/                # Birim testler
│   ├── 📂 integration/         # Entegrasyon testleri
│   └── 📂 fixtures/            # Test verileri
├── � scripts/                 # 📜 Betik Dosyaları
│   ├── 🔧 setup_database.py    # Veritabanı kurulumu
│   ├── 📦 build.py             # Derleme scripti
│   └── 🚀 deploy.py            # Yayınlama scripti
├── �📄 requirements.txt         # 📋 Python bağımlılıkları
├── 📄 requirements-dev.txt     # �️ Geliştirme bağımlılıkları
├── �🚀 main.py                  # 🏁 Ana uygulama dosyası
├── ⚙️ config.ini               # 🔧 Konfigürasyon dosyası
├── 🏃 run.bat                  # 🪟 Windows başlatıcı
├── 📄 .gitignore               # 🙈 Git ignore kuralları
├── 📄 LICENSE                  # ⚖️ MIT Lisansı
├── 📖 README.md                # 📚 Bu dosya
├── 📋 CHANGELOG.md             # 📝 Versiyon geçmişi
└── 🤝 CONTRIBUTING.md          # 👥 Katkı rehberi
```

</details>

---

## 🎮 Kullanım Kılavuzu

<div align="center">
<table>
<tr>
<td align="center" width="25%">

### 📊 Dashboard
![Dashboard Icon](https://img.shields.io/badge/📊-Dashboard-blue?style=for-the-badge)

✅ Finansal özetleri görüntüleyin  
✅ Grafiklerde satış/alış trendlerini takip edin  
✅ Hızlı erişim butonlarıyla işlem yapın  
✅ Güncel bakiyeleri kontrol edin

</td>
<td align="center" width="25%">

### 👥 Cari Hesaplar
![Customers Icon](https://img.shields.io/badge/👥-Cari_Hesaplar-green?style=for-the-badge)

✅ Müşteri ve tedarikçi kartları oluşturun  
✅ Borç/alacak durumlarını takip edin  
✅ Cari hesap ekstrelerini görüntüleyin  
✅ Risk limitlerini yönetin

</td>
<td align="center" width="25%">

### 📝 Fatura Yönetimi
![Invoice Icon](https://img.shields.io/badge/📝-Faturalar-orange?style=for-the-badge)

✅ Alış ve satış faturaları oluşturun  
✅ KDV hesaplamalarını otomatik yapın  
✅ Fatura yazdırma ve PDF çıktısı alın  
✅ E-fatura entegrasyonu

</td>
<td align="center" width="25%">

### ⚙️ Muhasebe
![Accounting Icon](https://img.shields.io/badge/⚙️-Muhasebe-red?style=for-the-badge)

✅ Hesap planını yönetin  
✅ Yevmiye kayıtları yapın  
✅ Mizan ve mali tabloları oluşturun  
✅ Defteri kebir takibi

</td>
</tr>
</table>
</div>

### 🚀 Hızlı İşlemler

<details>
<summary><b>💡 İpuçları ve Kısayollar</b></summary>

| Kısayol | Açıklama |
|---------|----------|
| `Ctrl + N` | Yeni kayıt oluştur |
| `Ctrl + S` | Kaydet |
| `Ctrl + P` | Yazdır / PDF |
| `Ctrl + F` | Arama |
| `F5` | Yenile |
| `Ctrl + Q` | Çıkış |

</details>

---

## 🔧 Geliştirme

<div align="center">

### 🤝 Katkıda Bulunun!

[![Contribute](https://img.shields.io/badge/🤝-Katkıda_Bulun-purple?style=for-the-badge)](CONTRIBUTING.md)
[![Issues](https://img.shields.io/badge/🐛-Hata_Bildirin-red?style=for-the-badge)](https://github.com/ThecoderPinar/accura-finance/issues/new)
[![Feature Request](https://img.shields.io/badge/💡-Özellik_İsteyin-blue?style=for-the-badge)](https://github.com/ThecoderPinar/accura-finance/issues/new?template=feature_request.md)

</div>

### 🏗️ Geliştirme Ortamı Kurulumu

```bash
# Proje deposunu klonlayın
git clone https://github.com/ThecoderPinar/accura-finance.git
cd accura-finance

# Development branch'e geçin
git checkout develop

# Geliştirme bağımlılıklarını yükleyin
pip install -r requirements-dev.txt

# Pre-commit hook'larını kurun
pre-commit install
```

### 📝 Kod Standartları

```bash
# Kod formatı kontrolü
black src/
flake8 src/
isort src/

# Type checking
mypy src/

# Testleri çalıştırın
pytest tests/ -v --coverage
```

### 🔄 Pull Request Süreci

1. **Fork** edin ve **feature branch** oluşturun
   ```bash
   git checkout -b feature/amazing-feature
   ```

2. **Test yazın** ve **mevcut testleri** çalıştırın
   ```bash
   pytest tests/
   ```

3. **Commit** edin ve **push** yapın
   ```bash
   git commit -m "Add amazing feature"
   git push origin feature/amazing-feature
   ```

4. **Pull Request** açın

---

## 🗺️ Yol Haritası

<div align="center">

### 📅 Geliştirme Planı

</div>

<details>
<summary><b>🚀 Version 1.0.1 (Geliştirmede)</b></summary>

| Özellik | Durum | Tamamlanma |
|---------|-------|------------|
| 👥 Tam işlevsel Cari Hesaplar modülü | 🟡 Devam ediyor | 60% |
| 📝 Fatura yönetimi sistemi | 🟡 Devam ediyor | 40% |
| 💰 Kasa & Banka işlemleri | 🔴 Beklemede | 20% |
| 📊 Gelişmiş raporlama | 🔴 Beklemede | 10% |
| 🔒 Kullanıcı yetkilendirme | 🟡 Devam ediyor | 70% |

**Tahmini Yayın Tarihi:** Ağustos 2025

</details>

<details>
<summary><b>⭐ Version 1.1.0 (Planlanan)</b></summary>

- [ ] 📧 E-fatura entegrasyonu
- [ ] 💼 Maaş bordrosu modülü
- [ ] 📈 İleri düzey analitik ve grafik
- [ ] 📱 Mobile-responsive web arayüzü
- [ ] 🌐 Multi-tenant (çoklu firma) desteği
- [ ] 🔄 API entegrasyonları
- [ ] 🤖 AI destekli özellikler

**Tahmini Yayın Tarihi:** Ekim 2025

</details>

<details>
<summary><b>🌟 Version 2.0.0 (Gelecek)</b></summary>

- [ ] ☁️ Cloud desteği
- [ ] 🔐 Blockchain entegrasyonu
- [ ] 🤝 CRM entegrasyonu
- [ ] 📊 Business Intelligence dashboard
- [ ] 🌍 Çoklu dil desteği
- [ ] 📱 Mobile uygulama

**Tahmini Yayın Tarihi:** 2026

</details>

---

## 📊 İstatistikler ve Topluluk

<div align="center">

### 📈 Proje İstatistikleri

![GitHub repo size](https://img.shields.io/github/repo-size/ThecoderPinar/accura-finance?style=for-the-badge&color=blue)
![GitHub code size](https://img.shields.io/github/languages/code-size/ThecoderPinar/accura-finance?style=for-the-badge&color=green)
![GitHub commit activity](https://img.shields.io/github/commit-activity/m/ThecoderPinar/accura-finance?style=for-the-badge&color=orange)
![GitHub last commit](https://img.shields.io/github/last-commit/ThecoderPinar/accura-finance?style=for-the-badge&color=red)

### 🌟 Topluluk

[![GitHub stars](https://img.shields.io/github/stars/ThecoderPinar/accura-finance?style=for-the-badge&logo=github&color=yellow)](https://github.com/ThecoderPinar/accura-finance/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/ThecoderPinar/accura-finance?style=for-the-badge&logo=github&color=blue)](https://github.com/ThecoderPinar/accura-finance/network)
[![GitHub watchers](https://img.shields.io/github/watchers/ThecoderPinar/accura-finance?style=for-the-badge&logo=github&color=green)](https://github.com/ThecoderPinar/accura-finance/watchers)
[![GitHub contributors](https://img.shields.io/github/contributors/ThecoderPinar/accura-finance?style=for-the-badge&logo=github&color=purple)](https://github.com/ThecoderPinar/accura-finance/graphs/contributors)

### 📊 Kod Kalitesi

[![CodeFactor](https://img.shields.io/codefactor/grade/github/ThecoderPinar/accura-finance?style=for-the-badge)](https://www.codefactor.io/repository/github/thecoderpinar/accura-finance)
[![Maintainability](https://img.shields.io/codeclimate/maintainability/ThecoderPinar/accura-finance?style=for-the-badge)](https://codeclimate.com/github/ThecoderPinar/accura-finance)
[![Test Coverage](https://img.shields.io/codecov/c/github/ThecoderPinar/accura-finance?style=for-the-badge)](https://codecov.io/gh/ThecoderPinar/accura-finance)

</div>

---

## 🏆 Teşekkürler

<div align="center">

### 💝 Destekçilerimiz

[![Stargazers](https://reporoster.com/stars/ThecoderPinar/accura-finance)](https://github.com/ThecoderPinar/accura-finance/stargazers)

[![Forkers](https://reporoster.com/forks/ThecoderPinar/accura-finance)](https://github.com/ThecoderPinar/accura-finance/network/members)

</div>

### 🙏 Kullanılan Teknolojiler

<div align="center">

[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![CustomTkinter](https://img.shields.io/badge/CustomTkinter-00D4AA?style=for-the-badge&logo=tkinter&logoColor=white)](https://github.com/TomSchimansky/CustomTkinter)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)](https://sqlalchemy.org)
[![Matplotlib](https://img.shields.io/badge/Matplotlib-11557c?style=for-the-badge&logo=matplotlib&logoColor=white)](https://matplotlib.org)
[![SQL Server](https://img.shields.io/badge/SQL_Server-CC2927?style=for-the-badge&logo=microsoft-sql-server&logoColor=white)](https://www.microsoft.com/sql-server)

</div>

**Özel Teşekkürler:**
- 🎨 [**CustomTkinter**](https://github.com/TomSchimansky/CustomTkinter) - Modern GUI framework için
- 🗄️ [**SQLAlchemy**](https://sqlalchemy.org/) - Güçlü ORM desteği için  
- 📊 [**Matplotlib**](https://matplotlib.org/) - Grafik ve görselleştirme için
- 🚀 [**Python Community**](https://python.org) - Sürekli gelişim için

---

## 📞 İletişim ve Destek

<div align="center">

### 👨‍💻 Geliştirici İletişim

<table>
<tr>
<td align="center">
<img src="https://github.com/ThecoderPinar.png" width="100px" style="border-radius: 50%"/><br>
<b>Pınar Topuz</b><br>
<i>Lead Developer</i>
</td>
</tr>
</table>

[![Email](https://img.shields.io/badge/📧-piinartp@gmail.com-red?style=for-the-badge&logo=gmail&logoColor=white)](mailto:piinartp@gmail.com)
[![LinkedIn](https://img.shields.io/badge/💼-LinkedIn-blue?style=for-the-badge&logo=linkedin&logoColor=white)](https://linkedin.com/in/piinartp)
[![GitHub](https://img.shields.io/badge/🐙-GitHub-black?style=for-the-badge&logo=github&logoColor=white)](https://github.com/ThecoderPinar)
[![Twitter](https://img.shields.io/badge/🐦-Twitter-blue?style=for-the-badge&logo=twitter&logoColor=white)](https://twitter.com/ThecoderPinar)

### 💬 Topluluk ve Destek

[![Discussions](https://img.shields.io/badge/💭-GitHub_Discussions-purple?style=for-the-badge&logo=github&logoColor=white)](https://github.com/ThecoderPinar/accura-finance/discussions)

### 🆘 Yardım ve Dokümantasyon

[![Documentation](https://img.shields.io/badge/📚-Dokümantasyon-blue?style=for-the-badge&logo=bookstack&logoColor=white)](docs/)
[![Wiki](https://img.shields.io/badge/📖-Wiki-green?style=for-the-badge&logo=wikipedia&logoColor=white)](https://github.com/ThecoderPinar/accura-finance/wiki)
[![FAQ](https://img.shields.io/badge/❓-SSS-orange?style=for-the-badge&logo=questdb&logoColor=white)](docs/FAQ.md)
[![Support](https://img.shields.io/badge/🎧-Destek-red?style=for-the-badge&logo=livechat&logoColor=white)](https://github.com/ThecoderPinar/accura-finance/issues/new?template=support.md)

</div>

---

## 📄 Lisans

<div align="center">

Bu proje **MIT Lisansı** altında lisanslanmıştır.  
Detaylar için [LICENSE](LICENSE) dosyasına bakınız.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

**Özgürce kullanabilir, değiştirebilir ve dağıtabilirsiniz!**

</div>

---

<div align="center">

## 🌟 Bu Projeyi Beğendiyseniz

### ⭐ **Yıldız vermeyi unutmayın!**

[![GitHub stars](https://img.shields.io/github/stars/ThecoderPinar/accura-finance?style=social)](https://github.com/ThecoderPinar/accura-finance/stargazers)

### 🔔 **Güncellemelerden haberdar olmak için "Watch" edin**

[![GitHub watchers](https://img.shields.io/github/watchers/ThecoderPinar/accura-finance?style=social)](https://github.com/ThecoderPinar/accura-finance/watchers)

### 🤝 **Fork edip katkıda bulunun**

[![GitHub forks](https://img.shields.io/github/forks/ThecoderPinar/accura-finance?style=social)](https://github.com/ThecoderPinar/accura-finance/network)

---

### 💖 Made with ❤️ in Turkey

![Made with Love](https://img.shields.io/badge/Made%20with-❤️-red?style=for-the-badge)
![Made in Turkey](https://img.shields.io/badge/Made%20in-🇹🇷%20Turkey-red?style=for-the-badge)

**© 2025 Pınar Topuz. Tüm hakları saklıdır.**

</div>
