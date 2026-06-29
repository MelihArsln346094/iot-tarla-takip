/*
 * Su Pompası Kontrol Sistemi - Arduino Kodu
 * HC-05 Bluetooth + RC28 Nem Sensörü (Manuel/Otomatik Mod Destekli)
 * 
 * Özellikler:
 * - MANUEL MOD: Pompa sadece A/K komutlarıyla kontrol edilir, nem oranına BAKILMAZ
 * - OTOMATİK MOD: Pompa nem sensörü değerine göre otomatik kontrol edilir
 * - Bluetooth bağlantısı olmasa bile sistem çalışmaya devam eder
 * - Mod seçimi EEPROM'a kaydedilir (elektrik gitse bile korunur)
 * 
 * Bağlantılar:
 * - HC-05 RX → Arduino TX (Pin 1)
 * - HC-05 TX → Arduino RX (Pin 0)
 * - Röle → Arduino Pin 9
 * - RC28 Nem Sensörü → Arduino A0
 * - Röle LOW = Pompa AÇIK, HIGH = Pompa KAPALI (Aktif Düşük Röle)
 * 
 * Komutlar:
 * - 'A' → Pompayı Aç (Manuel modda çalışır)
 * - 'K' → Pompayı Kapat (Manuel modda çalışır)
 * - 'M' → Manuel Mod (Nem oranına bakılmaz, sadece A/K komutları)
 * - 'O' → Otomatik Mod (Nem sensörüne göre otomatik çalışır)
 * - 'S' → Durum Sorgula
 * - 'N' → Nem Değerini Oku (anlık)
 */

#include <EEPROM.h>

// Pin tanımlamaları
const int RELAY_PIN = 9;
const int NEM_SENSOR_PIN = A0;

// EEPROM adresleri
const int EEPROM_VERSION_ADRES = 1;
const int EEPROM_POMPA_DURUM_ADRES = 0;
const int EEPROM_MOD_ADRES = 2;  // 0 = Manuel, 1 = Otomatik
const int EEPROM_VERSION = 4;  // Yeni versiyon (mod desteği eklendi)

// Nem sensörü eşik değeri
const int NEM_ESIK_DEGERI = 850;

// Histerezis (pompanın sürekli aç/kapa yapmaması için)
const int NEM_HISTEREZIS = 20; // ±20

// Okuma aralıkları
const unsigned long NEM_OKUMA_ARALIGI   = 1000;  // 1 sn'de bir nem oku
const unsigned long NEM_RAPOR_ARALIGI   = 5000;  // 5 sn'de bir seri porttan nem gönder

unsigned long sonNemOkumaZamani  = 0;
unsigned long sonNemRaporZamani  = 0;

int sonNemDegeri = 0;

// Pompa durumu ve mod
bool pompaDurumu = false;  // false = KAPALI, true = AÇIK
bool otomatikMod = true;   // false = Manuel, true = Otomatik (varsayılan otomatik)

// Seri port
char gelenKomut;
unsigned long sonKomutZamani = 0;
const unsigned long KOMUT_DEBOUNCE_SURESI = 100;

void setup() {
  Serial.begin(9600);
  delay(500);

  pinMode(RELAY_PIN, OUTPUT);
  pinMode(NEM_SENSOR_PIN, INPUT);

  // Güvenlik: İlk açılışta pompa KAPALI
  digitalWrite(RELAY_PIN, HIGH);
  pompaDurumu = false;

  // EEPROM versiyon kontrolü
  int kayitliVersiyon = EEPROM.read(EEPROM_VERSION_ADRES);
  if (kayitliVersiyon != EEPROM_VERSION) {
    // Versiyon farklıysa EEPROM'u sıfırla
    EEPROM.write(EEPROM_VERSION_ADRES, EEPROM_VERSION);
    EEPROM.write(EEPROM_POMPA_DURUM_ADRES, 0);  // Pompa kapalı
    EEPROM.write(EEPROM_MOD_ADRES, 1);          // Varsayılan: Otomatik mod
    otomatikMod = true;
  } else {
    // EEPROM'dan mod bilgisini oku
    int kayitliMod = EEPROM.read(EEPROM_MOD_ADRES);
    otomatikMod = (kayitliMod == 1);
    
    // Manuel modda ise pompa durumunu da EEPROM'dan oku
    if (!otomatikMod) {
      int kayitliDurum = EEPROM.read(EEPROM_POMPA_DURUM_ADRES);
      pompaDurumu = (kayitliDurum == 1);
      if (pompaDurumu) {
        digitalWrite(RELAY_PIN, LOW);
      }
    }
  }

  Serial.println("=== SISTEM HAZIR ===");
  Serial.print("Calisma Modu: ");
  Serial.println(otomatikMod ? "OTOMATIK" : "MANUEL");
  Serial.print("Baslangic Pompa Durumu: ");
  Serial.println(pompaDurumu ? "ACIK" : "KAPALI");
  Serial.print("Nem Esik Degeri: ");
  Serial.println(NEM_ESIK_DEGERI);
  Serial.println("Komutlar:");
  Serial.println("  'M' = Manuel Mod (Nem oranina bakilmaz)");
  Serial.println("  'O' = Otomatik Mod (Nem sensorune gore)");
  Serial.println("  'A' = Pompa AC (Manuel modda)");
  Serial.println("  'K' = Pompa KAPAT (Manuel modda)");
  Serial.println("  'S' = Durum Sorgula");
  Serial.println("  'N' = Anlik Nem Degeri");
  Serial.println("===================");
  delay(100);
}

void loop() {
  unsigned long simdi = millis();

  // 1) NEM SENSORU OKUMA (Her zaman oku, ama sadece otomatik modda kullan)
  if (simdi - sonNemOkumaZamani >= NEM_OKUMA_ARALIGI) {
    sonNemOkumaZamani = simdi;
    sonNemDegeri = analogRead(NEM_SENSOR_PIN);

    // OTOMATİK MODDA: Python target range kontrolü yapıyor, Arduino sadece nem okur
    // Arduino'nun kendi eşik kontrolü devre dışı (Python kontrol ediyor)
    // MANUEL MODDA: Nem okuması yapılır ama pompa kontrolü yapılmaz
  }

  // 2) HER 5 SANİYEDE BİR NEM VERİSİNİ RAPORLA
  if (simdi - sonNemRaporZamani >= NEM_RAPOR_ARALIGI) {
    sonNemRaporZamani = simdi;
    Serial.print("NEM: ");
    Serial.println(sonNemDegeri);
  }

  // 3) POMPA DURUMUNU HER ZAMAN UYGULA (EMNİYET)
  if (pompaDurumu) {
    digitalWrite(RELAY_PIN, LOW);
  } else {
    digitalWrite(RELAY_PIN, HIGH);
  }

  // 4) SERI PORTTAN KOMUT KONTROLÜ
  if (Serial.available() > 0) {
    gelenKomut = Serial.read();

    unsigned long simdiKomut = millis();
    if (simdiKomut - sonKomutZamani < KOMUT_DEBOUNCE_SURESI) {
      while (Serial.available() > 0) {
        Serial.read();
      }
      return;
    }
    sonKomutZamani = simdiKomut;

    gelenKomut = toupper(gelenKomut);

    switch (gelenKomut) {
      case 'M': // Manuel Moda Geç
        otomatikMod = false;
        EEPROM.write(EEPROM_MOD_ADRES, 0);
        Serial.println("OK: MANUEL MOD AKTIF");
        Serial.println("Pompa sadece 'A' ve 'K' komutlariyla kontrol edilir.");
        Serial.println("Nem oranina BAKILMAZ.");
        break;

      case 'O': // Otomatik Moda Geç
        otomatikMod = true;
        EEPROM.write(EEPROM_MOD_ADRES, 1);
        Serial.println("OK: OTOMATIK MOD AKTIF");
        Serial.print("Nem Esik Degeri: ");
        Serial.println(NEM_ESIK_DEGERI);
        Serial.println("Pompa nem sensorune gore otomatik calisacak.");
        break;

      case 'A': // Pompa AC (Manuel modda veya Otomatik modda Python kontrolü için)
        // Otomatik modda da Python'dan gelen komutları kabul et
        pompaDurumu = true;
        digitalWrite(RELAY_PIN, LOW);
        EEPROM.write(EEPROM_POMPA_DURUM_ADRES, 1);
        if (otomatikMod) {
          Serial.println("OK: Pompa ACILDI (Otomatik Mod - Python Kontrolu)");
        } else {
          Serial.println("OK: Pompa ACILDI (Manuel Komut)");
        }
        Serial.print("Durum: ");
        Serial.println("ACIK");
        delay(50);
        break;

      case 'K': // Pompa KAPAT (Manuel modda veya Otomatik modda Python kontrolü için)
        // Otomatik modda da Python'dan gelen komutları kabul et
        pompaDurumu = false;
        digitalWrite(RELAY_PIN, HIGH);
        EEPROM.write(EEPROM_POMPA_DURUM_ADRES, 0);
        if (otomatikMod) {
          Serial.println("OK: Pompa KAPATILDI (Otomatik Mod - Python Kontrolu)");
        } else {
          Serial.println("OK: Pompa KAPATILDI (Manuel Komut)");
        }
        Serial.print("Durum: ");
        Serial.println("KAPALI");
        delay(50);
        break;

      case 'S': // Durum sorgula
        Serial.println("=== SISTEM DURUMU ===");
        Serial.print("Mod: ");
        Serial.println(otomatikMod ? "OTOMATIK" : "MANUEL");
        Serial.print("Pompa: ");
        Serial.println(pompaDurumu ? "ACIK" : "KAPALI");
        Serial.print("Nem Degeri: ");
        Serial.println(sonNemDegeri);
        Serial.print("Nem Esik: ");
        Serial.println(NEM_ESIK_DEGERI);
        if (otomatikMod) {
          Serial.println("Calisma: Nem sensorune gore OTOMATIK");
        } else {
          Serial.println("Calisma: Sadece A/K komutlariyla MANUEL");
        }
        Serial.println("====================");
        break;

      case 'N': // Nem değerini oku (anlık)
      {
        int nemDegeri = analogRead(NEM_SENSOR_PIN);
        sonNemDegeri = nemDegeri; // Güncel tut
        Serial.print("NEM: ");
        Serial.println(nemDegeri);
        break;
      }

      default:
        Serial.print("HATA: Taninmayan komut: '");
        Serial.print(gelenKomut);
        Serial.println("'");
        Serial.println("Gecerli komutlar: 'M', 'O', 'A', 'K', 'S', 'N'");
        break;
    }

    // Buffer temizle
    while (Serial.available() > 0) {
      Serial.read();
    }
  }

  delay(10);
}