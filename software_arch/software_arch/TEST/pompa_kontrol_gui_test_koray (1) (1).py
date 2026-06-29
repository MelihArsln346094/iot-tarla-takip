"""
Su Pompası Kontrol Sistemi - Python GUI
HC-05 Bluetooth Modülü üzerinden Arduino ile iletişim

Kullanım:
    python pompa_kontrol_gui.py

Gereksinimler:
    - pyserial (pip install pyserial)
    - tkinter (genellikle Python ile birlikte gelir)
    - matplotlib (pip install matplotlib)
    
Özellikler:
    - Arduino MANUEL / OTOMATİK mod desteği ile çalışır
    - GUI:
        - Manuel modda: Pompayı A/K butonlarıyla NEMDEN BAĞIMSIZ kontrol et
        - Otomatik modda: Pompa durumu sadece izlenir, A/K pasif
    - Nem değeri her 5 saniyede bir otomatik güncellenir
    - Nem sensör değeri %0–%100 olarak ölçeklenip gösterilir
    - Geçmiş nem değerleri gerçek zamanlı grafikte gösterilir
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import serial
import serial.tools.list_ports
import threading
import time
from datetime import datetime
from collections import deque

# Matplotlib imports
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.dates as mdates


class PompaKontrolGUI:
    """
    Su pompası kontrolü için ana GUI sınıfı (Manuel / Otomatik Modlu + Grafik)
    """
    
    def __init__(self, root):
        self.root = root
        self.root.title("Su Pompası Kontrol Sistemi - Manuel / Otomatik Mod + Grafik")
        self.root.geometry("1100x850")
        self.merkeze_al()
        self.root.protocol("WM_DELETE_WINDOW", self.kapat)
        
        self.serial_connection = None
        self.pompa_durumu = False
        self.nem_degeri = 0
        self.nem_esik = 850
        
        # Sensör kalibrasyon değerleri
        self.sensor_min = 520      # en ıslak okuma
        self.sensor_max = 930   # en kuru okuma
        
        # GUI tarafı mod durumu
        self.otomatik_mod = True
        
        self.okuma_thread = None
        self.thread_calisiyor = False
        
        # Grafik için veri depolama (son 50 okuma)
        self.nem_gecmis = deque(maxlen=50)  # (datetime, yuzde) tuple'ları
        
        self.gui_olustur()
        self.com_portlari_tara()
        
        # Grafik güncelleme döngüsü (her 2 saniyede bir)
        self.grafik_guncelle_dongu()
    
    def merkeze_al(self):
        self.root.update_idletasks()
        genislik = self.root.winfo_width()
        yukseklik = self.root.winfo_height()
        ekran_genislik = self.root.winfo_screenwidth()
        ekran_yukseklik = self.root.winfo_screenheight()
        x = (ekran_genislik - genislik) // 2
        y = (ekran_yukseklik - yukseklik) // 2
        self.root.geometry(f"{genislik}x{yukseklik}+{x}+{y}")
    
    def gui_olustur(self):
        # Ana container - 2 sütunlu layout
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Sol panel (kontroller)
        sol_panel = ttk.Frame(main_container)
        sol_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10))
        
        # Sağ panel (grafik)
        sag_panel = ttk.Frame(main_container)
        sag_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # === SOL PANEL İÇERİĞİ ===
        
        # BAŞLIK
        ttk.Label(
            sol_panel,
            text="SU POMPASI KONTROL",
            font=("Arial", 14, "bold")
        ).pack(pady=(0, 5))
        
        ttk.Label(
            sol_panel,
            text="Nem Sensörü + Grafik",
            font=("Arial", 9, "italic"),
            foreground="gray"
        ).pack(pady=(0, 10))
        
        # COM PORT AYARLARI
        com_frame = ttk.LabelFrame(sol_panel, text="COM Port", padding="8")
        com_frame.pack(fill=tk.X, pady=(0, 8))
        
        port_row = ttk.Frame(com_frame)
        port_row.pack(fill=tk.X)
        
        self.com_port_var = tk.StringVar()
        self.com_port_combo = ttk.Combobox(
            port_row,
            textvariable=self.com_port_var,
            width=15,
            state="readonly"
        )
        self.com_port_combo.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            port_row,
            text="Tara",
            command=self.com_portlari_tara,
            width=6
        ).pack(side=tk.LEFT)
        
        self.baglan_butonu = ttk.Button(
            com_frame,
            text="Bağlan",
            command=self.baglan
        )
        self.baglan_butonu.pack(fill=tk.X, pady=(5, 0))
        
        self.baglanti_durumu_label = ttk.Label(
            com_frame,
            text="● Bağlı Değil",
            foreground="red",
            font=("Arial", 8)
        )
        self.baglanti_durumu_label.pack(pady=(3, 0))
        
        # MOD SEÇİMİ
        mod_frame = ttk.LabelFrame(sol_panel, text="Çalışma Modu", padding="8")
        mod_frame.pack(fill=tk.X, pady=(0, 8))
        
        mod_buton_frame = ttk.Frame(mod_frame)
        mod_buton_frame.pack()
        
        self.manuel_mod_butonu = tk.Button(
            mod_buton_frame,
            text="MANUEL",
            font=("Arial", 9, "bold"),
            bg="#2196F3",
            fg="white",
            activebackground="#0b7dda",
            activeforeground="white",
            relief=tk.RAISED,
            bd=2,
            padx=15,
            pady=8,
            command=self.manuel_mod_sec,
            state=tk.DISABLED
        )
        self.manuel_mod_butonu.pack(side=tk.LEFT, padx=3)
        
        self.otomatik_mod_butonu = tk.Button(
            mod_buton_frame,
            text="OTOMATİK",
            font=("Arial", 9, "bold"),
            bg="#FF9800",
            fg="white",
            activebackground="#e68900",
            activeforeground="white",
            relief=tk.RAISED,
            bd=2,
            padx=15,
            pady=8,
            command=self.otomatik_mod_sec,
            state=tk.DISABLED
        )
        self.otomatik_mod_butonu.pack(side=tk.LEFT, padx=3)
        
        self.mod_durum_label = ttk.Label(
            mod_frame,
            text="Aktif: OTOMATİK",
            font=("Arial", 9, "bold"),
            foreground="#FF9800"
        )
        self.mod_durum_label.pack(pady=(5, 0))
        
        # NEM BİLGİLERİ
        nem_frame = ttk.LabelFrame(sol_panel, text="Nem Sensörü", padding="8")
        nem_frame.pack(fill=tk.X, pady=(0, 8))
        
        self.nem_deger_label = ttk.Label(
            nem_frame,
            text="---",
            font=("Arial", 24, "bold"),
            foreground="#2196F3"
        )
        self.nem_deger_label.pack()
        
        self.son_guncelleme_label = ttk.Label(
            nem_frame,
            text="(Bekleniyor...)",
            font=("Arial", 7, "italic"),
            foreground="gray"
        )
        self.son_guncelleme_label.pack()
        
        self.nem_progress = ttk.Progressbar(
            nem_frame,
            length=280,
            mode='determinate',
            maximum=100
        )
        self.nem_progress.pack(pady=(8, 0))
        
        # POMPA KONTROLÜ
        kontrol_frame = ttk.LabelFrame(sol_panel, text="Pompa Kontrolü", padding="8")
        kontrol_frame.pack(fill=tk.X, pady=(0, 8))
        
        self.mod_uyari_label = ttk.Label(
            kontrol_frame,
            text="Otomatik modda A/K pasif",
            font=("Arial", 8, "italic"),
            foreground="#FF9800"
        )
        self.mod_uyari_label.pack(pady=(0, 5))
        
        buton_frame = ttk.Frame(kontrol_frame)
        buton_frame.pack()
        
        self.ac_butonu = tk.Button(
            buton_frame,
            text="AÇ",
            font=("Arial", 10, "bold"),
            bg="#4CAF50",
            fg="white",
            activebackground="#45a049",
            activeforeground="white",
            relief=tk.RAISED,
            bd=2,
            padx=20,
            pady=10,
            command=self.pompayi_ac,
            state=tk.DISABLED
        )
        self.ac_butonu.pack(side=tk.LEFT, padx=5)
        
        self.kapat_butonu = tk.Button(
            buton_frame,
            text="KAPAT",
            font=("Arial", 10, "bold"),
            bg="#f44336",
            fg="white",
            activebackground="#da190b",
            activeforeground="white",
            relief=tk.RAISED,
            bd=2,
            padx=20,
            pady=10,
            command=self.pompayi_kapat,
            state=tk.DISABLED
        )
        self.kapat_butonu.pack(side=tk.LEFT, padx=5)
        
        durum_frame = ttk.Frame(kontrol_frame)
        durum_frame.pack(pady=(10, 0))
        
        ttk.Label(
            durum_frame,
            text="Durum:",
            font=("Arial", 9)
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.durum_label = ttk.Label(
            durum_frame,
            text="KAPALI",
            font=("Arial", 9, "bold"),
            foreground="red"
        )
        self.durum_label.pack(side=tk.LEFT)
        
        # SERİ PORT ÇIKTISI
        cikti_frame = ttk.LabelFrame(sol_panel, text="Seri Port Çıktısı", padding="8")
        cikti_frame.pack(fill=tk.BOTH, expand=True)
        
        self.cikti_text = scrolledtext.ScrolledText(
            cikti_frame,
            height=10,
            wrap=tk.WORD,
            font=("Consolas", 8),
            bg="#f5f5f5",
            relief=tk.SUNKEN,
            bd=1
        )
        self.cikti_text.pack(fill=tk.BOTH, expand=True)
        self.cikti_text.config(state=tk.DISABLED)
        
        ttk.Button(
            cikti_frame,
            text="Temizle",
            command=self.ciktiyi_temizle
        ).pack(pady=(3, 0))
        
        # === SAĞ PANEL - GRAFİK ===
        
        grafik_baslik = ttk.Label(
            sag_panel,
            text="Nem Geçmişi Grafiği (Son 50 Okuma)",
            font=("Arial", 12, "bold")
        )
        grafik_baslik.pack(pady=(0, 10))
        
        # Matplotlib Figure oluştur
        self.fig = Figure(figsize=(7, 8), dpi=100, facecolor='white')
        self.ax = self.fig.add_subplot(111)
        
        # Grafik başlangıç ayarları
        self.ax.set_xlabel('Zaman', fontsize=10)
        self.ax.set_ylabel('Nem (%)', fontsize=10)
        self.ax.set_title('Toprak Nemi - Gerçek Zamanlı', fontsize=11, fontweight='bold')
        self.ax.grid(True, alpha=0.3)
        self.ax.set_ylim(0, 100)
        
        # Canvas oluştur ve GUI'ye ekle
        self.canvas = FigureCanvasTkAgg(self.fig, master=sag_panel)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Grafik temizleme butonu
        ttk.Button(
            sag_panel,
            text="Grafik Geçmişini Temizle",
            command=self.grafik_temizle
        ).pack(pady=(5, 0))
    
    # ---------- COM PORT / BAĞLANTI ----------
    
    def com_portlari_tara(self):
        portlar = serial.tools.list_ports.comports()
        hc05_portlari = []
        diger_portlar = []
        
        for port in portlar:
            aciklama = (port.description or "").upper()
            isim = (port.manufacturer or "").upper()
            if "HC-05" in aciklama or "HC-05" in isim or "HC05" in aciklama or "HC05" in isim:
                hc05_portlari.append(f"{port.device} - HC-05")
            else:
                diger_portlar.append(f"{port.device} - {port.description or 'Bilinmeyen'}")
        
        port_listesi = hc05_portlari + diger_portlar
        
        if not port_listesi:
            port_listesi = ["Port bulunamadı"]
            messagebox.showwarning(
                "Uyarı",
                "Hiçbir COM portu bulunamadı.\nHC-05 modülünüzün bağlı olduğundan emin olun."
            )
        
        self.com_port_combo['values'] = port_listesi
        
        if hc05_portlari:
            self.com_port_var.set(hc05_portlari[0])
            self.cikti_ekle(f"✓ HC-05 portu otomatik seçildi: {hc05_portlari[0]}")
        elif port_listesi and port_listesi[0] != "Port bulunamadı":
            self.com_port_var.set(port_listesi[0])
        
        if hc05_portlari:
            self.cikti_ekle(f"HC-05 portları bulundu: {len(hc05_portlari)} adet")
        self.cikti_ekle(f"Toplam taranan port: {len(port_listesi)} adet")
    
    def baglan(self):
        secilen_port_tam = self.com_port_var.get()
        if not secilen_port_tam or secilen_port_tam == "Port bulunamadı":
            messagebox.showerror("Hata", "Lütfen geçerli bir COM portu seçin!")
            return
        
        if " - " in secilen_port_tam:
            secilen_port = secilen_port_tam.split(" - ")[0]
        else:
            secilen_port = secilen_port_tam
        
        if self.serial_connection and self.serial_connection.is_open:
            self.baglantiyi_kapat()
            return
        
        try:
            if self.okuma_thread and self.okuma_thread.is_alive():
                self.thread_calisiyor = False
                self.okuma_thread.join(timeout=1.0)
            
            self.serial_connection = serial.Serial(
                port=secilen_port,
                baudrate=9600,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1,
                dsrdtr=False,
                rtscts=False
            )
            
            self.serial_connection.dtr = False
            self.serial_connection.rts = False
            self.serial_connection.reset_input_buffer()
            self.serial_connection.reset_output_buffer()
            time.sleep(2)
            self.serial_connection.dtr = False
            self.serial_connection.rts = False
            time.sleep(0.5)
            
            self.cikti_ekle(f"✓ {secilen_port} portuna başarıyla bağlandı!")
            self.baglanti_durumu_label.config(
                text=f"● Bağlı ({secilen_port})",
                foreground="green"
            )
            
            self.ac_butonu.config(state=tk.NORMAL if not self.otomatik_mod else tk.DISABLED)
            self.kapat_butonu.config(state=tk.NORMAL if not self.otomatik_mod else tk.DISABLED)
            self.manuel_mod_butonu.config(state=tk.NORMAL)
            self.otomatik_mod_butonu.config(state=tk.NORMAL)
            self.baglan_butonu.config(text="Bağlantıyı Kes")
            
            self.thread_calisiyor = True
            self.okuma_thread = threading.Thread(target=self.serial_oku, daemon=True)
            self.okuma_thread.start()
            
            time.sleep(0.5)
            self.durum_sorgula()
            
        except serial.SerialException as e:
            hata_mesaji = f"Seri port hatası: {str(e)}"
            messagebox.showerror("Bağlantı Hatası", hata_mesaji)
            self.cikti_ekle(f"✗ Hata: {hata_mesaji}")
            self.serial_connection = None
            
        except Exception as e:
            hata_mesaji = f"Beklenmeyen hata: {str(e)}"
            messagebox.showerror("Hata", hata_mesaji)
            self.cikti_ekle(f"✗ Hata: {hata_mesaji}")
            self.serial_connection = None
    
    def baglantiyi_kapat(self):
        self.thread_calisiyor = False
        if self.okuma_thread and self.okuma_thread.is_alive():
            self.okuma_thread.join(timeout=2.0)
        
        try:
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()
                self.cikti_ekle("Bağlantı kapatıldı.")
        except Exception as e:
            self.cikti_ekle(f"Bağlantı kapatılırken uyarı: {str(e)}")
        
        self.baglanti_durumu_label.config(
            text="● Bağlı Değil",
            foreground="red"
        )
        
        self.ac_butonu.config(state=tk.DISABLED)
        self.kapat_butonu.config(state=tk.DISABLED)
        self.manuel_mod_butonu.config(state=tk.DISABLED)
        self.otomatik_mod_butonu.config(state=tk.DISABLED)
        self.baglan_butonu.config(text="Bağlan")
        
        self.nem_deger_label.config(text="---")
        self.son_guncelleme_label.config(text="(Bağlantı yok)")
        
        self.serial_connection = None
        self.okuma_thread = None
    
    # ---------- MOD SEÇİMİ ----------
    
    def manuel_mod_sec(self):
        if not self.serial_connection or not self.serial_connection.is_open:
            messagebox.showerror("Hata", "Seri port bağlantısı yok!")
            return
        
        try:
            self.serial_connection.dtr = False
            self.serial_connection.rts = False
            self.serial_connection.reset_output_buffer()
            time.sleep(0.05)
            self.serial_connection.write(b'M')
            time.sleep(0.1)
            self.cikti_ekle("→ 'M' komutu gönderildi (Manuel Mod)")
            
            self.otomatik_mod = False
            self.mod_durum_label.config(text="Aktif: MANUEL", foreground="#2196F3")
            self.mod_uyari_label.config(
                text="Manuel mod: A/K butonları aktif",
                foreground="#2196F3"
            )
            
            self.ac_butonu.config(state=tk.NORMAL)
            self.kapat_butonu.config(state=tk.NORMAL)
            
        except Exception as e:
            hata_mesaji = f"Mod değiştirme hatası: {str(e)}"
            messagebox.showerror("Hata", hata_mesaji)
            self.cikti_ekle(f"✗ {hata_mesaji}")
    
    def otomatik_mod_sec(self):
        if not self.serial_connection or not self.serial_connection.is_open:
            messagebox.showerror("Hata", "Seri port bağlantısı yok!")
            return
        
        try:
            self.serial_connection.dtr = False
            self.serial_connection.rts = False
            self.serial_connection.reset_output_buffer()
            time.sleep(0.05)
            self.serial_connection.write(b'O')
            time.sleep(0.1)
            self.cikti_ekle("→ 'O' komutu gönderildi (Otomatik Mod)")
            
            self.otomatik_mod = True
            self.mod_durum_label.config(text="Aktif: OTOMATİK", foreground="#FF9800")
            self.mod_uyari_label.config(
                text="Otomatik modda A/K pasif",
                foreground="#FF9800"
            )
            
            self.ac_butonu.config(state=tk.DISABLED)
            self.kapat_butonu.config(state=tk.DISABLED)
            
        except Exception as e:
            hata_mesaji = f"Mod değiştirme hatası: {str(e)}"
            messagebox.showerror("Hata", hata_mesaji)
            self.cikti_ekle(f"✗ {hata_mesaji}")
    
    # ---------- SERİ OKUMA / MESAJ İŞLEME ----------
    
    def serial_oku(self):
        while self.thread_calisiyor:
            try:
                if self.serial_connection and self.serial_connection.is_open:
                    if self.serial_connection.in_waiting > 0:
                        try:
                            satir = self.serial_connection.readline().decode('utf-8', errors='ignore').strip()
                        except UnicodeDecodeError:
                            self.serial_connection.reset_input_buffer()
                            continue
                        except (serial.SerialException, OSError):
                            break
                        
                        if satir:
                            satir_kopya = satir
                            self.root.after(0, lambda s=satir_kopya: self.cikti_ekle(s))
                            self.mesaj_isle(satir)
                else:
                    break
            except serial.SerialException as e:
                if self.thread_calisiyor:
                    hata_mesaji = f"Seri port bağlantısı kesildi: {str(e)}"
                    self.root.after(0, lambda: self.cikti_ekle(hata_mesaji))
                    self.root.after(0, lambda: self.baglantiyi_kapat())
                break
            except (OSError, AttributeError) as e:
                if self.thread_calisiyor and not isinstance(e, AttributeError):
                    hata_mesaji = f"Bağlantı hatası: {str(e)}"
                    self.root.after(0, lambda: self.cikti_ekle(hata_mesaji))
                break
            except Exception as e:
                if self.thread_calisiyor:
                    hata_mesaji = f"Okuma hatası: {str(e)}"
                    self.root.after(0, lambda: self.cikti_ekle(hata_mesaji))
                    time.sleep(0.5)
                else:
                    break
            
            if self.thread_calisiyor:
                time.sleep(0.1)
            else:
                break
    
    def mesaj_isle(self, satir):
        satir_upper = satir.upper()
        
        # Pompa durumu
        if "ACILDI" in satir_upper or ("ACIK" in satir_upper and "KAPALI" not in satir_upper):
            self.root.after(0, lambda: self.durum_guncelle(True))
        elif "KAPATILDI" in satir_upper or ("KAPALI" in satir_upper and "ACILDI" not in satir_upper):
            self.root.after(0, lambda: self.durum_guncelle(False))
        
        # Nem değeri
        if "NEM:" in satir_upper:
            try:
                nem_str = satir.split(":")[-1].strip()
                nem_deger = int(nem_str)
                self.root.after(0, lambda d=nem_deger: self.nem_guncelle(d))
            except (ValueError, IndexError):
                pass
        
        # Mod değişikliği mesajları
        if "MANUEL MOD AKTIF" in satir_upper:
            self.root.after(0, lambda: self.cikti_ekle("✓ Arduino MANUEL moda geçti"))
        elif "OTOMATIK MOD AKTIF" in satir_upper:
            self.root.after(0, lambda: self.cikti_ekle("✓ Arduino OTOMATİK moda geçti"))
    
    def durum_sorgula(self):
        if not self.serial_connection or not self.serial_connection.is_open:
            return
        try:
            self.serial_connection.dtr = False
            self.serial_connection.rts = False
            self.serial_connection.reset_output_buffer()
            time.sleep(0.05)
            self.serial_connection.write(b'S')
            time.sleep(0.1)
            self.cikti_ekle("→ 'S' komutu gönderildi (Durum Sorgula)")
        except Exception as e:
            self.cikti_ekle(f"✗ Durum sorgulama hatası: {str(e)}")
    
    # ---------- NEM / POMPA / ÇIKTI ----------
    
    def nem_guncelle(self, deger):
        """
        Arduino'dan gelen ham sensör değerini (0–1023) al,
        %0–%100 aralığına ölçekle ve grafiğe ekle.
        """
        self.nem_degeri = deger

        # Ham değeri kalibrasyon aralığına sıkıştır
        raw = max(self.sensor_min, min(self.sensor_max, deger))

        # 0–1023 → %0–%100 ölçekleme
        oran = (self.sensor_max - raw) / (self.sensor_max - self.sensor_min) * 100.0
        oran = max(0, min(100, oran))

        # Sadece yüzde göster
        self.nem_deger_label.config(text=f"%{oran:.0f}")

        # Son güncelleme zamanı
        zaman = datetime.now()
        zaman_str = zaman.strftime("%H:%M:%S")
        self.son_guncelleme_label.config(text=f"(Güncellendi: {zaman_str})")

        # Progress bar
        self.nem_progress['value'] = oran

        # Renk mantığı
        if oran <= 30:
            self.nem_deger_label.config(foreground="#4CAF50")   # yeşil
        elif oran >= 70:
            self.nem_deger_label.config(foreground="#f44336")   # kırmızı
        else:
            self.nem_deger_label.config(foreground="#FF9800")   # turuncu
        
        # Grafiğe ekle (datetime, yüzde)
        self.nem_gecmis.append((zaman, oran))
    
    def pompayi_ac(self):
        if not self.serial_connection or not self.serial_connection.is_open:
            messagebox.showerror("Hata", "Seri port bağlantısı yok!")
            return
        
        if self.otomatik_mod:
            messagebox.showwarning(
                "Uyarı",
                "Otomatik modda manuel A/K komutları pasiftir.\n"
                "Önce MANUEL MOD'a geç."
            )
            return
        
        try:
            self.serial_connection.dtr = False
            self.serial_connection.rts = False
            self.serial_connection.reset_output_buffer()
            time.sleep(0.05)
            self.serial_connection.write(b'A')
            time.sleep(0.1)
            self.cikti_ekle("→ 'A' komutu gönderildi (Pompayı Aç - Manuel)")
            self.durum_guncelle(True)
        except serial.SerialException as e:
            hata_mesaji = f"Seri port hatası: {str(e)}"
            messagebox.showerror("Hata", hata_mesaji)
            self.cikti_ekle(f"✗ {hata_mesaji}")
            self.baglantiyi_kapat()
        except Exception as e:
            hata_mesaji = f"Komut gönderme hatası: {str(e)}"
            messagebox.showerror("Hata", hata_mesaji)
            self.cikti_ekle(f"✗ {hata_mesaji}")
    
    def pompayi_kapat(self):
        if not self.serial_connection or not self.serial_connection.is_open:
            messagebox.showerror("Hata", "Seri port bağlantısı yok!")
            return
        
        if self.otomatik_mod:
            messagebox.showwarning(
                "Uyarı",
                "Otomatik modda manuel A/K komutları pasiftir.\n"
                "Önce MANUEL MOD'a geç."
            )
            return
        
        try:
            self.serial_connection.dtr = False
            self.serial_connection.rts = False
            self.serial_connection.reset_output_buffer()
            time.sleep(0.05)
            self.serial_connection.write(b'K')
            time.sleep(0.1)
            self.cikti_ekle("→ 'K' komutu gönderildi (Pompayı Kapat - Manuel)")
            self.durum_guncelle(False)
        except serial.SerialException as e:
            hata_mesaji = f"Seri port hatası: {str(e)}"
            messagebox.showerror("Hata", hata_mesaji)
            self.cikti_ekle(f"✗ {hata_mesaji}")
            self.baglantiyi_kapat()
        except Exception as e:
            hata_mesaji = f"Komut gönderme hatası: {str(e)}"
            messagebox.showerror("Hata", hata_mesaji)
            self.cikti_ekle(f"✗ {hata_mesaji}")
    
    def durum_guncelle(self, durum):
        self.pompa_durumu = durum
        if durum:
            self.durum_label.config(text="AÇIK", foreground="green")
        else:
            self.durum_label.config(text="KAPALI", foreground="red")
    
    def cikti_ekle(self, mesaj):
        self.cikti_text.config(state=tk.NORMAL)
        zaman = datetime.now().strftime("%H:%M:%S")
        tam_mesaj = f"[{zaman}] {mesaj}\n"
        self.cikti_text.insert(tk.END, tam_mesaj)
        self.cikti_text.see(tk.END)
        self.cikti_text.config(state=tk.DISABLED)
    
    def ciktiyi_temizle(self):
        self.cikti_text.config(state=tk.NORMAL)
        self.cikti_text.delete(1.0, tk.END)
        self.cikti_text.config(state=tk.DISABLED)
    
    # ---------- GRAFİK FONKSİYONLARI ----------
    
    def grafik_guncelle_dongu(self):
        """
        Her 2 saniyede bir grafiği güncelle
        """
        self.grafik_ciz()
        self.root.after(2000, self.grafik_guncelle_dongu)
    
    def grafik_ciz(self):
        """
        Geçmiş nem verilerini grafiğe çiz
        """
        self.ax.clear()
        
        if len(self.nem_gecmis) == 0:
            # Veri yoksa boş grafik göster
            self.ax.text(
                0.5, 0.5, 
                'Veri Bekleniyor...',
                horizontalalignment='center',
                verticalalignment='center',
                transform=self.ax.transAxes,
                fontsize=14,
                color='gray'
            )
            self.ax.set_xlabel('Zaman', fontsize=10)
            self.ax.set_ylabel('Nem (%)', fontsize=10)
            self.ax.set_title('Toprak Nemi - Gerçek Zamanlı', fontsize=11, fontweight='bold')
            self.ax.set_ylim(0, 100)
            self.ax.grid(True, alpha=0.3)
        else:
            # Verileri ayır
            zamanlar = [item[0] for item in self.nem_gecmis]
            yüzdeler = [item[1] for item in self.nem_gecmis]
            
            # Çizgi grafiği çiz
            self.ax.plot(zamanlar, yüzdeler, 
                        color='#2196F3', 
                        linewidth=2, 
                        marker='o', 
                        markersize=4,
                        label='Nem %')
            
            # Eşik çizgisi ekle (opsiyonel - %50 örneği)
            self.ax.axhline(y=50, color='orange', linestyle='--', linewidth=1, alpha=0.7, label='Orta Seviye')
            
            # Grafik ayarları
            self.ax.set_xlabel('Zaman', fontsize=10)
            self.ax.set_ylabel('Nem (%)', fontsize=10)
            self.ax.set_title('Toprak Nemi - Gerçek Zamanlı', fontsize=11, fontweight='bold')
            self.ax.set_ylim(0, 100)
            self.ax.grid(True, alpha=0.3)
            self.ax.legend(loc='upper left', fontsize=8)
            
            # X ekseni zaman formatı
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
            self.fig.autofmt_xdate(rotation=45)
        
        # Canvas'ı güncelle
        self.canvas.draw()
    
    def grafik_temizle(self):
        """
        Grafik geçmişini temizle
        """
        self.nem_gecmis.clear()
        self.grafik_ciz()
        self.cikti_ekle("Grafik geçmişi temizlendi")
    
    def kapat(self):
        self.baglantiyi_kapat()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = PompaKontrolGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()