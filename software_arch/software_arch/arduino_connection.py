"""
Shared Arduino Connection Manager
Manages a single serial connection to Arduino that can be shared between multiple modules.
"""
import serial
import threading
import time
from typing import Callable, Optional


class ArduinoConnection:
    """Singleton-like Arduino connection manager."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ArduinoConnection, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.serial_connection = None
        self.serial_thread = None
        self.thread_calisiyor = False
        self.port = 'COM5'
        self.baudrate = 9600
        
        # Data storage
        self.last_nem_degeri = 0
        self.pump_on = False
        self.arduino_auto_mode = True
        
        # Callbacks for data updates
        self.moisture_callbacks = []  # List of callbacks for moisture data
        self.pump_callbacks = []  # List of callbacks for pump status updates
        self.mode_callbacks = []  # List of callbacks for mode updates
        
        self._initialized = True
        self.connect()
    
    def connect(self):
        """Connect to Arduino on COM5."""
        try:
            if self.serial_connection and self.serial_connection.is_open:
                return True
            
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
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
            
            # Start serial reading thread
            self.thread_calisiyor = True
            self.serial_thread = threading.Thread(target=self.serial_oku, daemon=True)
            self.serial_thread.start()
            
            print(f"Arduino connected on {self.port}")
            return True
        except serial.SerialException as e:
            print(f"Error connecting to Arduino on {self.port}: {e}")
            self.serial_connection = None
            return False
        except Exception as e:
            print(f"Unexpected error connecting to Arduino: {e}")
            self.serial_connection = None
            return False
    
    def is_connected(self):
        """Check if Arduino is connected."""
        return self.serial_connection is not None and self.serial_connection.is_open
    
    def serial_oku(self):
        """Read serial data from Arduino."""
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
                            self.mesaj_isle(satir)
                else:
                    break
            except serial.SerialException as e:
                if self.thread_calisiyor:
                    print(f"Serial port connection lost: {str(e)}")
                break
            except (OSError, AttributeError) as e:
                if self.thread_calisiyor and not isinstance(e, AttributeError):
                    print(f"Connection error: {str(e)}")
                break
            except Exception as e:
                if self.thread_calisiyor:
                    print(f"Reading error: {str(e)}")
                    time.sleep(0.5)
                else:
                    break
            
            if self.thread_calisiyor:
                time.sleep(0.1)
            else:
                break
    
    def mesaj_isle(self, satir):
        """Process messages from Arduino."""
        satir_upper = satir.upper()
        
        # Nem değeri
        if "NEM:" in satir_upper:
            try:
                nem_str = satir.split(":")[-1].strip()
                nem_deger = int(nem_str)
                self.last_nem_degeri = nem_deger
                
                # Notify all moisture callbacks
                for callback in self.moisture_callbacks:
                    try:
                        callback(nem_deger)
                    except Exception as e:
                        print(f"Error in moisture callback: {e}")
            except (ValueError, IndexError):
                pass
        
        # Pompa durumu
        if "ACILDI" in satir_upper or ("ACIK" in satir_upper and "KAPALI" not in satir_upper):
            self.pump_on = True
            # Notify all pump callbacks
            for callback in self.pump_callbacks:
                try:
                    callback(True)
                except Exception as e:
                    print(f"Error in pump callback: {e}")
        elif "KAPATILDI" in satir_upper or ("KAPALI" in satir_upper and "ACILDI" not in satir_upper):
            self.pump_on = False
            # Notify all pump callbacks
            for callback in self.pump_callbacks:
                try:
                    callback(False)
                except Exception as e:
                    print(f"Error in pump callback: {e}")
        
        # Mod değişikliği
        if "MANUEL MOD AKTIF" in satir_upper:
            self.arduino_auto_mode = False
            # Notify all mode callbacks
            for callback in self.mode_callbacks:
                try:
                    callback(False)
                except Exception as e:
                    print(f"Error in mode callback: {e}")
        elif "OTOMATIK MOD AKTIF" in satir_upper:
            self.arduino_auto_mode = True
            # Notify all mode callbacks
            for callback in self.mode_callbacks:
                try:
                    callback(True)
                except Exception as e:
                    print(f"Error in mode callback: {e}")
    
    def register_moisture_callback(self, callback: Callable[[int], None]):
        """Register a callback for moisture data updates."""
        if callback not in self.moisture_callbacks:
            self.moisture_callbacks.append(callback)
    
    def unregister_moisture_callback(self, callback: Callable[[int], None]):
        """Unregister a moisture callback."""
        if callback in self.moisture_callbacks:
            self.moisture_callbacks.remove(callback)
    
    def register_pump_callback(self, callback: Callable[[bool], None]):
        """Register a callback for pump status updates."""
        if callback not in self.pump_callbacks:
            self.pump_callbacks.append(callback)
    
    def unregister_pump_callback(self, callback: Callable[[bool], None]):
        """Unregister a pump callback."""
        if callback in self.pump_callbacks:
            self.pump_callbacks.remove(callback)
    
    def register_mode_callback(self, callback: Callable[[bool], None]):
        """Register a callback for mode updates."""
        if callback not in self.mode_callbacks:
            self.mode_callbacks.append(callback)
    
    def unregister_mode_callback(self, callback: Callable[[bool], None]):
        """Unregister a mode callback."""
        if callback in self.mode_callbacks:
            self.mode_callbacks.remove(callback)
    
    def write_command(self, command: bytes):
        """Write a command to Arduino."""
        if self.serial_connection and self.serial_connection.is_open:
            try:
                self.serial_connection.dtr = False
                self.serial_connection.rts = False
                self.serial_connection.reset_output_buffer()
                time.sleep(0.05)
                self.serial_connection.write(command)
                time.sleep(0.1)
                return True
            except Exception as e:
                print(f"Error writing command to Arduino: {e}")
                return False
        return False
    
    def get_moisture_value(self):
        """Get the last moisture value."""
        return self.last_nem_degeri
    
    def get_pump_status(self):
        """Get the current pump status."""
        return self.pump_on
    
    def get_mode(self):
        """Get the current Arduino mode (True = Auto, False = Manual)."""
        return self.arduino_auto_mode
    
    def cleanup(self):
        """Cleanup resources."""
        self.thread_calisiyor = False
        
        # Clear all callbacks
        self.moisture_callbacks.clear()
        self.pump_callbacks.clear()
        self.mode_callbacks.clear()
        
        if self.serial_thread and self.serial_thread.is_alive():
            self.serial_thread.join(timeout=2.0)
        
        try:
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()
        except Exception:
            pass
        
        self.serial_connection = None

