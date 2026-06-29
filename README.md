# 🌾 Field Tracker - Modern Tarım Yönetim Sistemi

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![UI Framework](https://img.shields.io/badge/UI-Tkinter-orange.svg)](https://docs.python.org/3/library/tkinter.html)
[![Database](https://img.shields.io/badge/database-SQLite-lightgrey.svg)](https://www.sqlite.org/)
[![Hardware](https://img.shields.io/badge/hardware-Arduino-00979D.svg)](https://www.arduino.cc/)

Field Tracker, modern tarım işletmelerinin ve çiftçilerin tarlalarını, ürünlerini, depolarını ve sulama sistemlerini tek bir merkezden akıllıca yönetebilmeleri için geliştirilmiş, donanım entegrasyonuna sahip **masaüstü ve web simülasyonu** tabanlı bir yönetim sistemidir.

Proje, Arduino tabanlı sensörlerle (toprak nem sensörü) doğrudan iletişim kurarak tarlanın anlık nem ihtiyacına göre su pompasını otomatik veya manuel olarak kontrol edebilen akıllı bir sulama altyapısına sahiptir.

---

## 🗺️ Öne Çıkan Özellikler

### 1. İnteraktif Harita ve Konum Yönetimi (`TkinterMapView`)
*   **Çift Katmanlı Harita:** Standart OpenStreetMap (OSM) ve ESRI Uydu Görüntüsü katmanları arasında hızlı geçiş yapabilme.
*   **Harita Üzerinden Alan Çizimi (Polygon):** Uydu görüntüsü üzerinden tarlanın sınırlarını tıklayarak çizebilme ve tarlanın gerçek yüzölçümünü (metrekare ve dönüm/acre cinsinden) otomatik hesaplama.
*   **Konum İşaretleme:** Tarla ve depoları harita üzerinde görsel pinler ile konumlandırabilme.

### 2. Akıllı Sulama ve Su Kontrolü (`WaterControl`)
*   **Ürüne Özel Hedef Nem Aralığı:** Farklı ürün tipleri için (Buğday, Mısır, Domates, Ayçiçeği, Pamuk, Arpa vb.) önceden tanımlanmış veya özelleştirilebilir ideal nem eşikleri.
*   **Histerezis Desteği:** Pompanın çok sık açılıp kapanmasını (dalgalanmayı) engellemek için akıllı histerezis (`±2%`) algoritması.
*   **Güvenli Manuel Müdahale:** Otomatik modu geçici olarak devre dışı bırakan ve 30 saniye sonra güvenli bir şekilde otomatik kontrole geri dönen akıllı zamanlayıcılı manuel sulama kontrolü.
*   **Canlı Grafik (Matplotlib):** Tarladan alınan son veriler doğrultusunda nem değişim trendini gösteren geriye dönük grafik analizleri.

### 3. Tarla ve Ürün Takibi (`FieldForm` & `FieldView`)
*   Tarlanın ekili olduğu ürün, ekim tarihi, kullanılan gübre türü ve gübreleme zamanlarının takibi.
*   Entegre **OpenWeatherMap API** ve reverse geocoding (**Nominatim**) servisleri sayesinde, seçilen tarlanın koordinatlarına ait anlık hava durumu bilgilerini (nem, yağış, rüzgar hızı, basınç) otomatik olarak çekme ve haritada tarla detayında gösterme.

### 4. Depo ve Stok Yönetimi (`StorageForm` & `StorageView`)
*   Depolardaki tohum (tür ve miktar), gübre ve tarım ilacı stoklarının takibi.
*   Depo ortamının nem ve sıcaklık değerlerinin geçmişe dönük kaydedilmesi.

### 5. Donanım (Arduino) Entegrasyonu
*   **COM** portu üzerinden (`COM5`, 9600 Baud) seri haberleşme altyapısı.
*   EEPROM kaydı sayesinde elektrik kesintilerinde bile çalışma modunu (otomatik/manuel) ve pompa durumunu hafızasında tutan kararlı Arduino yazılımı.
*   Hata toleranslı ve asenkron çalışan thread tabanlı seri okuma mekanizması.

### 6. Web Arayüzü Simülasyonu (`web/`)
*   Sistemle paralel çalışan, modern CSS tasarımlı ve **Chart.js** entegrasyonlu, tarayıcı üzerinden sulama durumunu ve nem grafiğini izlemeye olanak tanıyan bir web kontrol paneli arayüzü.

---

## 📐 Proje Mimarisi ve Dosya Yapısı

Proje dosyaları mantıksal katmanlara ayrılarak modüler bir yapıda tasarlanmıştır:

```text
software_arch/
│
├── software_arch/                  # Ana Kaynak Kod Dizini
│   ├── images/                     # Arayüzde kullanılan ürün ve görsel dosyaları
│   │
│   ├── TEST/                       # Test kodları ve donanım yazılımları
│   │   ├── pompa_kontrol_test_koray.ino    # Arduino taslağı (C++)
│   │   └── pompa_kontrol_gui_test_koray.py # Pompa arayüzü izole test scripti
│   │
│   ├── web/                        # Web Arayüzü Simülasyonu
│   │   ├── assets/
│   │   │   ├── css/styles.css      # Web paneli tasarımı
│   │   │   └── js/waterControl.js  # Nem simülasyonu ve grafik mantığı
│   │   └── index.html              # Web kontrol paneli ana sayfası
│   │
│   ├── main.py                     # Ana Uygulama Başlatıcı (Tkinter GUI)
│   ├── arduino_connection.py       # Arduino Seri Port Haberleşme Yöneticisi (Singleton)
│   ├── database.py                 # SQLite Veritabanı ve CRUD İşlemleri Katmanı
│   ├── field_form.py               # Tarla ekleme/düzenleme formu
│   ├── field_view.py               # Ekili tarlaların listesi, harita pinleri ve detaylar
│   ├── soil_monitor.py             # Toprak nem ve sıcaklık sensör veri ekranı
│   ├── storage_form.py             # Depo/Antrepo ekleme formu
│   ├── storage_view.py             # Depoların listesi ve stok durumları
│   ├── water_control.py            # Grafik analizli sulama ve pompa kontrol ünitesi
│   ├── weather.py                  # OpenWeatherMap API & Nominatim Konum Servisi
│   └── crop_info.py                # Ürün bilgi rehberi arayüzü
│
├── .gitignore                      # Git takip dışı bırakma kuralları
└── README.md                       # Proje tanıtım ve kılavuz dosyası
```

---

## 🛠️ Sistem Gereksinimleri ve Kurulum

### 1. Gerekli Python Kütüphaneleri
Uygulamanın çalışması için bilgisayarınızda Python 3.8 veya üzeri bir sürüm yüklü olmalıdır. Gerekli kütüphaneleri yüklemek için terminalde/komut satırında aşağıdaki komutu çalıştırın:

```bash
pip install pillow requests tkcalendar tkintermapview matplotlib pyserial
```

### 2. Projeyi Çalıştırma
Tüm bağımlılıklar yüklendikten sonra ana projeyi çalıştırmak için ana dizine giderek şu komutu çalıştırabilirsiniz:

```bash
python software_arch/software_arch/main.py
```

> [!NOTE]
> Proje ilk kez çalıştırıldığında `field_tracker.db` adında bir SQLite veritabanı dosyası otomatik olarak oluşturulacak ve gerekli tablolar kurulacaktır.

---

## 🔌 Donanım (Arduino) Kurulumu

Sistem, fiziksel bir Arduino kartı ve sensörlerle çalışmaya hazır durumdadır.

### Bağlantı Şeması
*   **Toprak Nem Sensörü (RC28 / Analog Çıkış):** Arduino **A0** pinine bağlanır.
*   **Sulama Rölesi (Su Pompası):** Arduino **Pin 9**'a bağlanır (Aktif Düşük Röle olarak konfigüre edilmiştir).
*   **Haberleşme:** Arduino bilgisayara USB üzerinden bağlanır. Varsayılan port `COM5` ve baud hızı `9600`'dür (Gerekirse `arduino_connection.py` üzerinden değiştirilebilir).

### Arduino Kodunun Yüklenmesi
1.  `software_arch/software_arch/TEST/pompa_kontrol_test_koray.ino` dosyasını Arduino IDE ile açın.
2.  Kart tipinizi (örn: Arduino Uno) ve bağlı olduğu Portu seçin.
3.  Kodu derleyip kartınıza yükleyin.
4.  Arduino seri haberleşme hattını Python uygulamasıyla paylaşacağı için Arduino IDE Seri Çizici / Seri Monitör ekranının kapalı olduğundan emin olun.

---

## 🗄️ Veritabanı Şeması

SQLite üzerinde aşağıdaki tablolar dinamik olarak yönetilir:

*   **`fields`**: Tarlaların isim, alan büyüklüğü, ekili ürün, ekim tarihi, gübre bilgileri, hava durumu geçmişi, koordinatları ve sınır çizgi koordinatlarını (GeoJSON formatında) saklar.
*   **`storage`**: Depoların isim, konum bilgileri ve mevcut gübre, ilaç, tohum stok miktarlarını saklar.
*   **`soil_data`**: Tarlalardan Arduino aracılığıyla okunan toprak nemi, sıcaklık ve hava nemi kayıtlarının zaman damgalı geçmişini tutar.
*   **`storage_conditions`**: Depoların zaman damgalı nem ve sıcaklık değerlerini saklar.

---

## 🤝 Katkıda Bulunma
1.  Bu depoyu forklayın (`fork`).
2.  Yeni bir özellik dalı oluşturun (`git checkout -b ozellik/yeniOzellik`).
3.  Değişikliklerinizi commit edin (`git commit -m 'Yeni özellik eklendi'`).
4.  Dalı push edin (`git push origin ozellik/yeniOzellik`).
5.  Bir Pull Request oluşturun.

