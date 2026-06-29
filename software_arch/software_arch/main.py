import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import Calendar
from tkintermapview import TkinterMapView
import os

from database import Database
from weather import WeatherService
from field_form import FieldForm
from storage_form import StorageForm
from field_view import FieldView
from soil_monitor import SoilMonitor
from water_control import WaterControl
from storage_view import StorageView
from crop_info import CropInfoView
from arduino_connection import ArduinoConnection

# ---- CONFIG ----
DB_PATH = "field_tracker.db"
WEATHER_API_KEY = "e65666e8661b2fca4cf997f780f3fdce"

class FieldTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🌾 Field Tracker - Modern Agriculture Management System")
        self.root.geometry("1600x900")
        try:
            self.root.state('zoomed')  # Start maximized
        except:
            pass
        
        # Configure modern style
        self.configure_modern_style()

        self.db = Database(DB_PATH)
        self.weather_service = WeatherService(WEATHER_API_KEY)
        
        # Create shared Arduino connection
        self.arduino_connection = ArduinoConnection()

        # Main container with modern styling
        main_container = tk.Frame(root, bg='#ECEFF1')
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Title bar
        title_bar = tk.Frame(main_container, bg='#1565C0', height=60)
        title_bar.pack(fill=tk.X)
        title_bar.pack_propagate(False)
        
        tk.Label(title_bar, text="🌾 FIELD TRACKER", 
                font=("Segoe UI", 18, "bold"), bg='#1565C0', fg='white').pack(side=tk.LEFT, padx=30, pady=15)
        
        tk.Label(title_bar, text="Modern Agriculture Management System", 
                font=("Segoe UI", 10), bg='#1565C0', fg='#BBDEFB').pack(side=tk.LEFT, pady=15)
        
        # Content area
        content_area = tk.Frame(main_container, bg='#ECEFF1')
        content_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left side: Map view
        self.left_frame = tk.Frame(content_area, bg='white', relief=tk.SOLID, borderwidth=1)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Map header
        map_header = tk.Frame(self.left_frame, bg='#2E7D32', height=45)
        map_header.pack(fill=tk.X)
        map_header.pack_propagate(False)
        
        tk.Label(map_header, text="🗺️ Interactive Map View", 
                font=("Segoe UI", 13, "bold"), bg='#2E7D32', fg='white').pack(side=tk.LEFT, padx=20, pady=10)

        # Layer switcher (OSM / Satellite)
        layer_btn_frame = tk.Frame(map_header, bg='#2E7D32')
        layer_btn_frame.pack(side=tk.RIGHT, padx=10)
        self.is_satellite_mode = False  # Track current mode
        
        # Create Draw Point button first
        self.btn_draw_point = ttk.Button(layer_btn_frame, text="Draw Point", command=self.start_draw_in_satellite)
        
        def set_osm():
            # Standard OSM
            self.is_satellite_mode = False
            self.map_widget.set_tile_server("https://a.tile.openstreetmap.org/{z}/{x}/{y}.png")
            # Hide Draw Point button in OSM mode
            self.btn_draw_point.pack_forget()
            # Disable polygon drawing UI in OSM
            try:
                self.field_form.set_polygon_enabled(False)
            except Exception:
                pass
        
        def set_sat():
            # Esri World Imagery
            self.is_satellite_mode = True
            self.map_widget.set_tile_server("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}")
            # Show Draw Point button in Satellite mode
            self.btn_draw_point.pack(side=tk.LEFT, padx=4, pady=6)
            # Enable polygon drawing UI in Satellite
            try:
                self.field_form.set_polygon_enabled(True)
            except Exception:
                pass
        
        ttk.Button(layer_btn_frame, text="OSM", command=set_osm).pack(side=tk.LEFT, padx=4, pady=6)
        ttk.Button(layer_btn_frame, text="Satellite", command=set_sat).pack(side=tk.LEFT, padx=4, pady=6)
        
        # Map widget - defer heavy initialization
        self.map_widget = TkinterMapView(self.left_frame, corner_radius=0)
        self.map_widget.pack(fill=tk.BOTH, expand=True)
        # Defer map position setting to avoid blocking
        self.root.after(50, lambda: self.map_widget.set_position(39.92077, 32.85411))
        self.root.after(50, lambda: self.map_widget.set_zoom(6))

        self.map_widget.add_right_click_menu_command(
            label="🌱 Add Field",
            command=self.on_map_click,
            pass_coords=True
        )
        
        # Right side: Notebook
        right_container = tk.Frame(content_area, bg='#ECEFF1')
        right_container.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        
        self.right_frame = ttk.Notebook(right_container, width=550)
        self.right_frame.pack(fill=tk.BOTH, expand=True)

        self.tab_field = ttk.Frame(self.right_frame)
        self.tab_storage = ttk.Frame(self.right_frame)
        self.tab_view = ttk.Frame(self.right_frame)
        self.tab_soil = ttk.Frame(self.right_frame)
        self.tab_storage_view = ttk.Frame(self.right_frame)
        self.tab_info = ttk.Frame(self.right_frame)
        self.tab_water = ttk.Frame(self.right_frame)

        self.right_frame.add(self.tab_field, text=" 🌱 ADD FIELD ")
        self.right_frame.add(self.tab_view, text=" 📊 FIELDS ")
        self.right_frame.add(self.tab_storage, text=" 📦 ADD WAREHOUSE ")
        self.right_frame.add(self.tab_storage_view, text=" 🏭 WAREHOUSES ")
        self.right_frame.add(self.tab_soil, text=" 🌍 SOIL DATA ")
        self.right_frame.add(self.tab_water, text=" 💧 WATER & MOISTURE ")
        self.right_frame.add(self.tab_info, text=" 📖 CROP INFO ")

        self.field_form = FieldForm(self.tab_field, self.map_widget, self.weather_service, self.db, self.on_field_saved)
        # Initialize polygon drawing as disabled (OSM mode is default)
        self.field_form.set_polygon_enabled(False)
        self.storage_form = StorageForm(self.tab_storage, self.map_widget, self.db, self.on_storage_saved)
        self.field_view = FieldView(self.tab_view, self.map_widget, self.db, self.weather_service,
                                    self.on_field_edit, self.on_field_deleted)
        self.storage_view = StorageView(self.tab_storage_view, self.map_widget, self.db,
                                        self.on_storage_edit, self.on_storage_deleted)
        self.soil_monitor = SoilMonitor(self.tab_soil, self.db, 
                                        weather_service=self.weather_service,
                                        arduino_connection=self.arduino_connection)
        self.crop_info = CropInfoView(self.tab_info)
        self.water_control = WaterControl(self.tab_water, self.db,
                                          arduino_connection=self.arduino_connection)

        # Defer loading to avoid blocking startup - load after UI is rendered
        self.root.after(100, self._deferred_initial_load)
    
    def _deferred_initial_load(self):
        """Load data after UI is rendered"""
        self.field_view.load_all_fields()
        self.storage_view.load_all_storages()
    
    def configure_modern_style(self):
        """Configure modern, elegant appearance"""
        style = ttk.Style()
        style.theme_use("clam")
        
        # Modern color palette
        colors = {
            'primary': '#2E7D32',
            'secondary': '#1565C0',
            'accent': '#F57C00',
            'background': '#FAFAFA',
            'surface': '#FFFFFF',
            'text': '#212121'
        }
        
        # Configure styles
        style.configure("TLabel", 
                       font=("Segoe UI", 10),
                       background=colors['background'],
                       foreground=colors['text'])
        
        style.configure("TEntry", 
                       font=("Segoe UI", 10),
                       fieldbackground=colors['surface'],
                       borderwidth=2)
        
        style.configure("TButton", 
                       font=("Segoe UI", 10, "bold"),
                       borderwidth=0,
                       relief="flat")
        
        style.configure("TCombobox", 
                       font=("Segoe UI", 10),
                       fieldbackground=colors['surface'],
                       borderwidth=2)
        
        style.configure("TNotebook.Tab", 
                       font=("Segoe UI", 9, "bold"),
                       padding=[12, 10])
        
        style.map("TNotebook.Tab",
                 background=[('selected', colors['primary']), ('!selected', '#E0E0E0')],
                 foreground=[('selected', 'white'), ('!selected', colors['text'])],
                 expand=[('selected', [1, 1, 1, 0])])
        
        style.configure("TFrame", background=colors['background'])
        style.configure("TLabelFrame", background=colors['background'])
        style.configure("TLabelframe.Label", font=("Segoe UI", 11, "bold"), foreground=colors['primary'])
        
        # Configure root background
        self.root.configure(bg=colors['background'])

    def on_map_click(self, coords):
        self.right_frame.select(0)
        self.field_form.set_location(*coords)

    def start_draw_in_satellite(self):
        """Start drawing in satellite mode - switch to Add Field tab and start drawing"""
        if not self.is_satellite_mode:
            messagebox.showwarning("Warning", "Please switch to Satellite view first.")
            return
        
        # Switch to Add Field tab
        self.right_frame.select(0)
        # Start polygon drawing
        self.field_form.start_polygon_drawing()

    def on_field_saved(self):
        """Called when a field is saved (created or updated). Refresh all modules that depend on field list."""
        self.field_view.load_all_fields()
        # Reload field lists in soil monitor and water control modules
        if hasattr(self, 'soil_monitor'):
            self.soil_monitor.load_fields()
        if hasattr(self, 'water_control'):
            self.water_control._load_fields()

    def on_storage_saved(self):
        self.storage_view.load_all_storages()

    def on_field_edit(self, field_id):
        self.right_frame.select(0)
        self.field_view.load_all_fields()
        self.storage_view.load_all_storages()
        self.field_form.load_field_for_edit(field_id)

    def on_storage_edit(self, storage_id, lat=None, lon=None):
        self.right_frame.select(2)
        self.field_view.load_all_fields()
        self.storage_view.load_all_storages()

        if storage_id:
            self.storage_form.load_storage_for_edit(storage_id)
        elif lat and lon:
            self.storage_form.set_location(lat, lon)

    def on_field_deleted(self):
        """Called when a field is deleted. Refresh all modules that depend on field list."""
        # Reload field lists in soil monitor and water control modules
        if hasattr(self, 'soil_monitor'):
            self.soil_monitor.load_fields()
        if hasattr(self, 'water_control'):
            self.water_control._load_fields()

    def on_storage_deleted(self):
        pass
    
    def cleanup(self):
        """Cleanup resources on application exit."""
        # Cleanup soil monitor
        if hasattr(self, 'soil_monitor'):
            self.soil_monitor.cleanup()
        
        # Cleanup water control
        if hasattr(self, 'water_control'):
            self.water_control.cleanup()
        
        # Cleanup Arduino connection
        if hasattr(self, 'arduino_connection'):
            self.arduino_connection.cleanup()

if __name__ == "__main__":
    root = tk.Tk()
    app = FieldTrackerApp(root)
    
    # Handle cleanup on window close
    def on_closing():
        app.cleanup()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
