import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import Calendar
import os
from PIL import Image, ImageTk

class FieldForm:
    def __init__(self, parent, map_widget, weather_service, db, on_save_callback):
        self.parent = parent
        self.map_widget = map_widget
        self.weather_service = weather_service
        self.db = db
        self.on_save_callback = on_save_callback

        self.lat = None
        self.lon = None
        self.humidity = None
        self.rainfall = None
        self.wind = None
        self.pressure = None
        self.current_marker = None
        self.editing_field_id = None
        self.image_path = None
        self.image_preview =None
        self.image_paths = []
        # Polygon drawing state
        self.is_drawing_polygon = False
        self.polygon_points = []  # list of (lat, lon)
        self.polygon_shape = None
        self.area_sqm_value = None
        self.area_acres_value = None
        self.polygon_geojson_value = None
        self._vertex_markers = []
        self._canvas_click_bind_id = None
        self.polygon_enabled = False  # Start disabled (OSM mode is default)
        self.build_form()

    def build_form(self):
        # Modern scrollable container
        self.canvas = tk.Canvas(self.parent, bg='#F5F5F5', highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.parent, orient="vertical", command=self.canvas.yview)
        scrollable_frame = tk.Frame(self.canvas, bg='#F5F5F5')
        
        self.canvas_window_id = self.canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        def configure_scroll(event):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
        def configure_canvas(event):
            canvas_width = event.width
            self.canvas.itemconfig(self.canvas_window_id, width=canvas_width)
        
        scrollable_frame.bind("<Configure>", configure_scroll)
        self.canvas.bind('<Configure>', configure_canvas)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Enable mouse wheel scrolling
        self._bind_mousewheel(scrollable_frame)
        
        # Header with gradient effect
        header_frame = tk.Frame(scrollable_frame, bg='#2E7D32', height=80)
        header_frame.pack(fill=tk.X)
        header_label = tk.Label(header_frame, text="🌱 Add New Field", 
                               font=("Segoe UI", 20, "bold"), bg='#2E7D32', fg='white')
        header_label.pack(pady=20)
        
        # Main content frame with padding
        content_frame = tk.Frame(scrollable_frame, bg='#F5F5F5')
        content_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # Card 1: Basic Information
        card1 = tk.Frame(content_frame, bg='white', relief=tk.FLAT, bd=0)
        card1.pack(fill=tk.X, pady=(0, 15))
        self._add_shadow(card1)
        
        card1_header = tk.Frame(card1, bg='#E8F5E9', height=50)
        card1_header.pack(fill=tk.X)
        tk.Label(card1_header, text="📝 Basic Information", font=("Segoe UI", 14, "bold"),
                bg='#E8F5E9', fg='#2E7D32').pack(anchor='w', padx=20, pady=12)
        
        card1_content = tk.Frame(card1, bg='white')
        card1_content.pack(fill=tk.X, padx=20, pady=20)
        
        self._create_input_field(card1_content, "Field Name:", "entry_name")
        self._create_combo_field(card1_content, "Cultivated Product:", "entry_crop",
                                ["🌾 Wheat", "🌻 Sunflower", "🌿 Barley", "🌽 Corn", "☁ Cotton", "Other"])
        self._create_combo_field(card1_content, "Fertilizer Type:", "fertilizer_type",
                                ["Nitrogenous Fertilizer", "Phosphorous Fertilizer", 
                                 "Potassium Fertilizer", "Organic Fertilizer", "Other"])
        
        # Card 2: Important Dates
        card2 = tk.Frame(content_frame, bg='white', relief=tk.FLAT, bd=0)
        card2.pack(fill=tk.X, pady=(0, 15))
        self._add_shadow(card2)
        
        card2_header = tk.Frame(card2, bg='#E3F2FD', height=50)
        card2_header.pack(fill=tk.X)
        tk.Label(card2_header, text="📆 Important Dates", font=("Segoe UI", 14, "bold"),
                bg='#E3F2FD', fg='#1565C0').pack(anchor='w', padx=20, pady=12)
        
        card2_content = tk.Frame(card2, bg='white')
        card2_content.pack(fill=tk.X, padx=20, pady=20)
        
        # Planting Date
        sow_container = tk.Frame(card2_content, bg='white')
        sow_container.pack(fill=tk.X, pady=(0, 15))
        self.sowing_calendar_button = tk.Button(sow_container, text="📆 Select Planting Date",
                                               command=self.toggle_sowing_calendar,
                                               bg='#4CAF50', fg='white', font=("Segoe UI", 11, "bold"),
                                               relief=tk.FLAT, padx=20, pady=10, cursor="hand2")
        self.sowing_calendar_button.pack()
        self.sowing_calendar_frame = tk.Frame(sow_container, bg='white')
        self.sowing_calendar = Calendar(self.sowing_calendar_frame, selectmode="day", date_pattern="yyyy-mm-dd")
        self.sowing_calendar.pack(padx=5, pady=5)
        
        # Fertilization Date
        fert_container = tk.Frame(card2_content, bg='white')
        fert_container.pack(fill=tk.X)
        self.fertilizer_calendar_button = tk.Button(fert_container, text="📆 Select Fertilization Date",
                                                    command=self.toggle_fertilizer_calendar,
                                                    bg='#FF9800', fg='white', font=("Segoe UI", 11, "bold"),
                                                    relief=tk.FLAT, padx=20, pady=10, cursor="hand2")
        self.fertilizer_calendar_button.pack()
        self.fertilizer_calendar_frame = tk.Frame(fert_container, bg='white')
        self.fertilizer_calendar = Calendar(self.fertilizer_calendar_frame, selectmode="day", date_pattern="yyyy-mm-dd")
        self.fertilizer_calendar.pack(padx=5, pady=5)
        
        # Card 3: Field Photos
        card3 = tk.Frame(content_frame, bg='white', relief=tk.FLAT, bd=0)
        card3.pack(fill=tk.X, pady=(0, 15))
        self._add_shadow(card3)
        
        card3_header = tk.Frame(card3, bg='#FFF3E0', height=50)
        card3_header.pack(fill=tk.X)
        tk.Label(card3_header, text="📷 Field Photos", font=("Segoe UI", 14, "bold"),
                bg='#FFF3E0', fg='#F57C00').pack(anchor='w', padx=20, pady=12)
        
        card3_content = tk.Frame(card3, bg='white')
        card3_content.pack(fill=tk.X, padx=20, pady=20)
        
        button_frame = tk.Frame(card3_content, bg='white')
        button_frame.pack(pady=10)
        
        upload_btn = tk.Button(button_frame, text="📷 Upload Photos", command=self.upload_image,
                              bg='#2196F3', fg='white', font=("Segoe UI", 11, "bold"),
                              relief=tk.FLAT, padx=20, pady=10, cursor="hand2")
        upload_btn.pack(side=tk.LEFT, padx=5)
        
        delete_btn = tk.Button(button_frame, text="🗑️ Delete All", command=self.remove_current_photo,
                              bg='#F44336', fg='white', font=("Segoe UI", 11, "bold"),
                              relief=tk.FLAT, padx=20, pady=10, cursor="hand2")
        delete_btn.pack(side=tk.LEFT, padx=5)
        
        self.image_label = tk.Label(card3_content, bg='#FAFAFA', text="No photos uploaded",
                                    font=("Segoe UI", 10), fg='#757575',
                                    relief=tk.SOLID, borderwidth=1)
        self.image_label.pack(pady=10, ipady=10)
        
        # Photo thumbnails frame
        self.photo_frame = tk.Frame(card3_content, bg='white')
        self.photo_frame.pack(pady=10)
        
        # Card 4: Weather Information
        card4 = tk.Frame(content_frame, bg='white', relief=tk.FLAT, bd=0)
        card4.pack(fill=tk.X, pady=(0, 15))
        self._add_shadow(card4)
        
        card4_header = tk.Frame(card4, bg='#E1F5FE', height=50)
        card4_header.pack(fill=tk.X)
        tk.Label(card4_header, text="⛅ Weather Information", font=("Segoe UI", 14, "bold"),
                bg='#E1F5FE', fg='#0277BD').pack(anchor='w', padx=20, pady=12)
        
        card4_content = tk.Frame(card4, bg='white')
        card4_content.pack(fill=tk.X, padx=20, pady=20)
        
        self.weather_label = tk.Label(card4_content, 
                                      text="Select a location on the map to view weather data",
                                      font=("Segoe UI", 11), bg='white', fg='#616161',
                                      justify=tk.LEFT, anchor='w')
        self.weather_label.pack(fill=tk.X, pady=10)

        # Card 5: Field Boundary (Polygon) - Only visible in Satellite mode
        self.card5 = tk.Frame(content_frame, bg='white', relief=tk.FLAT, bd=0)
        self._add_shadow(self.card5)
        # Don't pack initially - will be packed when polygon_enabled is True
        card5_header = tk.Frame(self.card5, bg='#E8F5E9', height=50)
        card5_header.pack(fill=tk.X)
        tk.Label(card5_header, text="🗺️ Field Boundary (Polygon)", font=("Segoe UI", 14, "bold"),
                bg='#E8F5E9', fg='#2E7D32').pack(anchor='w', padx=20, pady=12)
        card5_content = tk.Frame(self.card5, bg='white')
        card5_content.pack(fill=tk.X, padx=20, pady=16)
        btns = tk.Frame(card5_content, bg='white')
        btns.pack(fill=tk.X)
        self.btn_start_draw = tk.Button(btns, text="✏️ Start Drawing", command=self.start_polygon_drawing,
                                       bg='#4CAF50', fg='white', font=("Segoe UI", 10, "bold"),
                                       relief=tk.FLAT, padx=14, pady=8, cursor="hand2")
        self.btn_start_draw.pack(side=tk.LEFT)
        self.btn_finish_draw = tk.Button(btns, text="✓ Finish", command=self.finish_polygon_drawing,
                                        bg='#1565C0', fg='white', font=("Segoe UI", 10, "bold"),
                                        relief=tk.FLAT, padx=14, pady=8, cursor="hand2")
        self.btn_finish_draw.pack(side=tk.LEFT, padx=8)
        self.btn_clear_draw = tk.Button(btns, text="🗑️ Clear", command=self.clear_polygon,
                                       bg='#F44336', fg='white', font=("Segoe UI", 10, "bold"),
                                       relief=tk.FLAT, padx=14, pady=8, cursor="hand2")
        self.btn_clear_draw.pack(side=tk.LEFT)
        self.area_label = tk.Label(card5_content, text="Area: -", font=("Segoe UI", 11), bg='white', fg='#424242')
        self.area_label.pack(anchor='w', pady=10)
        
        # Save and Cancel Buttons (Fixed at bottom, after all cards)
        save_frame = tk.Frame(content_frame, bg='#F5F5F5')
        save_frame.pack(fill=tk.X, pady=(20, 0))
        
        button_container = tk.Frame(save_frame, bg='#F5F5F5')
        button_container.pack()
        
        self.cancel_button = tk.Button(button_container, text="❌ CANCEL", command=self.cancel_form,
                                       bg='#757575', fg='white', font=("Segoe UI", 14, "bold"),
                                       relief=tk.FLAT, padx=40, pady=15, cursor="hand2", width=15)
        self.cancel_button.pack(side=tk.LEFT, padx=5)
        
        self.save_button = tk.Button(button_container, text="💾 SAVE FIELD", command=self.save_field,
                                     bg='#4CAF50', fg='white', font=("Segoe UI", 14, "bold"),
                                     relief=tk.FLAT, padx=40, pady=15, cursor="hand2", width=15)
        self.save_button.pack(side=tk.LEFT, padx=5)

    def set_polygon_enabled(self, enabled: bool):
        """Enable/disable and show/hide Field Boundary drawing UI.

        When disabled (OSM view), hide the card and cancel any active drawing.
        When enabled (Satellite view), show the card again.
        """
        self.polygon_enabled = enabled
        if not enabled:
            # Cancel any drawing and hide UI
            try:
                self.clear_polygon()
            except Exception:
                pass
            # Hide the card completely in OSM mode
            if self.card5.winfo_ismapped():
                self.card5.pack_forget()
        else:
            # Show UI only in Satellite mode
            if not self.card5.winfo_ismapped():
                # Pack card5 in its proper position (before save buttons)
                self.card5.pack(fill=tk.X, pady=(0, 15))
    
    def _bind_mousewheel(self, widget):
        widget.bind("<Enter>", lambda e: self._enable_mousewheel())
        widget.bind("<Leave>", lambda e: self._disable_mousewheel())

    def _enable_mousewheel(self):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_linux_scroll)
        self.canvas.bind_all("<Button-5>", self._on_linux_scroll)

    def _disable_mousewheel(self):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        # Windows/macOS
        delta = int(-1 * (event.delta / 120))
        self.canvas.yview_scroll(delta, "units")

    def _on_linux_scroll(self, event):
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
    def _add_shadow(self, widget):
        """Add a shadow effect to widgets"""
        widget.config(highlightbackground='#BDBDBD', highlightthickness=1)
    
    def _create_input_field(self, parent, label_text, attr_name):
        """Create a modern input field"""
        container = tk.Frame(parent, bg='white')
        container.pack(fill=tk.X, pady=8)
        
        label = tk.Label(container, text=label_text, font=("Segoe UI", 11, "bold"),
                        bg='white', fg='#424242')
        label.pack(anchor='w', pady=(0, 5))
        
        entry = ttk.Entry(container, font=("Segoe UI", 11))
        entry.pack(fill=tk.X, ipady=8)
        setattr(self, attr_name, entry)
    
    def _create_combo_field(self, parent, label_text, attr_name, values):
        """Create a modern combobox field"""
        container = tk.Frame(parent, bg='white')
        container.pack(fill=tk.X, pady=8)
        
        label = tk.Label(container, text=label_text, font=("Segoe UI", 11, "bold"),
                        bg='white', fg='#424242')
        label.pack(anchor='w', pady=(0, 5))
        
        combo = ttk.Combobox(container, values=values, font=("Segoe UI", 11))
        combo.pack(fill=tk.X, ipady=8)
        setattr(self, attr_name, combo)

    def toggle_sowing_calendar(self):
        if self.sowing_calendar_frame.winfo_ismapped():
            self.sowing_calendar_frame.pack_forget()
        else:
            self.sowing_calendar_frame.pack(pady=5)

    def toggle_fertilizer_calendar(self):
        if self.fertilizer_calendar_frame.winfo_ismapped():
            self.fertilizer_calendar_frame.pack_forget()
        else:
            self.fertilizer_calendar_frame.pack(pady=5)

    def upload_image(self):
        paths = filedialog.askopenfilenames(filetypes=[("Image Files", "*.jpg *.png")])
        if paths:

            if not hasattr(self, 'image_paths'):
                self.image_paths = []

            os.makedirs("images", exist_ok=True)

            for path in paths:
                filename = os.path.basename(path)
                dest_path = os.path.join("images", filename)


                with open(path, 'rb') as fsrc, open(dest_path, 'wb') as fdst:
                    fdst.write(fsrc.read())


                self.image_paths.append(dest_path)


            self.show_photos()
        if self.image_paths:
            self.show_selected_photo(self.image_paths[-1])

    def show_photos(self):

        for widget in self.photo_frame.winfo_children():
            widget.destroy()


        for idx, path in enumerate(self.image_paths):
            img = Image.open(path)
            img.thumbnail((100, 100))
            photo = ImageTk.PhotoImage(img)

            frame = tk.Frame(self.photo_frame)
            frame.pack(side="left", padx=5)

            label = tk.Label(frame, image=photo)
            label.image = photo
            label.pack()

            btn = ttk.Button(frame, text="Delete", command=lambda p=path: self.delete_photo(p))
            btn.pack(pady=2)

    def show_selected_photo(self, photo_path):
        if photo_path and os.path.exists(photo_path):
            image = Image.open(photo_path)
            image = image.resize((300, 200))
            photo = ImageTk.PhotoImage(image)

            self.image_label.config(image=photo, text="")
            self.image_label.image = photo  #
        else:
            self.image_label.config(text="No Photo", image="", bg="lightgrey")

    def load_field_photo(self, photo_path):
        if photo_path and os.path.exists(photo_path):
            self.show_selected_photo(photo_path)
        else:
            self.image_label.config(text="No Photo", image="", bg="lightgrey")

    def delete_photo(self, photo_path):
        if photo_path in self.image_paths:
            self.image_paths.remove(photo_path)

            if os.path.exists(photo_path):
                os.remove(photo_path)

            self.show_photos()

            if self.image_paths:
                self.show_selected_photo(self.image_paths[0])
            else:
                self.image_label.config(text="No Photo", image="", background="lightgrey")
                self.image_label.image = None

    def remove_current_photo(self):
        if messagebox.askyesno("Delete All Photos", "Are you sure you want to remove all photos?"):
            self.image_paths = []
            self.show_photos()
            self.image_label.config(text="No Photo", image="", background="lightgrey")

    def update_weather_display(self, weather_data):
        self.humidity = weather_data['humidity']
        self.rainfall = weather_data['rainfall']
        self.wind = weather_data['wind']
        self.pressure = weather_data['pressure']

        self.weather_label.config(text=f"🌡 Temperature: {weather_data['temp']}°C\n💧 Humidity: {self.humidity}%\n🌧 Rain: {self.rainfall} mm\n💨 Wind: {self.wind} m/s\n📊 Pressure: {self.pressure} hPa")

    def set_location(self, lat, lon):
        self.lat = lat
        self.lon = lon
        name = self.entry_name.get().strip() or "Selected Point"

        if self.current_marker:
            self.current_marker.delete()

        self.current_marker = self.map_widget.set_marker(self.lat, self.lon, text=name)

        # Load weather data asynchronously to avoid blocking UI
        import threading
        def fetch_weather():
            try:
                weather_data = self.weather_service.get_weather_by_coords(lat, lon)
                # Update UI in main thread
                self.weather_label.after(0, lambda: self.update_weather_display(weather_data))
            except Exception:
                pass
        
        thread = threading.Thread(target=fetch_weather, daemon=True)
        thread.start()

    def start_polygon_drawing(self):
        if not self.polygon_enabled:
            messagebox.showwarning("Warning", "Field Boundary drawing is disabled in OSM view.")
            return
        self.is_drawing_polygon = True
        self.polygon_points = []
        self.area_sqm_value = None
        self.area_acres_value = None
        self.polygon_geojson_value = None
        if self.polygon_shape:
            self.polygon_shape.delete()
            self.polygon_shape = None
        for m in self._vertex_markers:
            try:
                m.delete()
            except Exception:
                pass
        self._vertex_markers = []
        self.area_label.config(text="Area: - (Click on map to add points)")
        # Bind map click for vertices
        try:
            self.map_widget.add_left_click_map_command(self._on_map_left_click_polygon)
        except Exception as e:
            pass  # Left click command not available in this version
        # Fallback: direct canvas binding
        try:
            if self._canvas_click_bind_id is None:
                self._canvas_click_bind_id = self.map_widget.canvas.bind('<Button-1>', self._on_canvas_click_polygon)
        except Exception:
            self._canvas_click_bind_id = None

    def finish_polygon_drawing(self):
        if not self.polygon_points or len(self.polygon_points) < 3:
            messagebox.showwarning("Warning", "Draw at least 3 points to create a polygon.")
            return
        self.is_drawing_polygon = False
        # Unbind
        try:
            self.map_widget.add_left_click_map_command(lambda *_: None)
        except Exception:
            pass
        try:
            if self._canvas_click_bind_id is not None:
                self.map_widget.canvas.unbind('<Button-1>', self._canvas_click_bind_id)
                self._canvas_click_bind_id = None
        except Exception:
            pass
        # Close polygon and draw
        self._draw_or_update_polygon()
        # Compute area and centroid
        self.area_sqm_value = self._compute_area_sqm(self.polygon_points)
        self.area_acres_value = self.area_sqm_value / 4046.8564224
        centroid_lat, centroid_lon = self._polygon_centroid(self.polygon_points)
        # Basic farmland validation
        valid, reason = self._validate_farmland_overpass(self.polygon_points)
        if not valid:
            # If there is explicit overlap with residential/building, block.
            if reason == "residential_or_building_area":
                messagebox.showwarning("Warning", "This area is not suitable for cultivation: " + self._translate_reason(reason))
                return
            # If farmland is simply not mapped or validation skipped, allow but inform.
            if reason in ("no_farmland_found", "validation_skipped"):
                messagebox.showinfo("Info", "OSM data may not label farmland in this region. The field can still be saved.")
        # Update labels and current location to centroid
        self.area_label.config(text=f"Area: {int(self.area_sqm_value):,} m² • {self.area_acres_value:.2f} acres".replace(',', '.'))
        self.lat = centroid_lat
        self.lon = centroid_lon
        
        # Automatically fetch weather information for the polygon centroid
        try:
            weather_data = self.weather_service.get_weather_by_coords(centroid_lat, centroid_lon)
            self.update_weather_display(weather_data)
        except Exception as e:
            # If weather fetch fails, just update the label with a message
            self.weather_label.config(text=f"Select a location on the map to view weather data\n(Weather data unavailable for this location)")
        
        # Do not keep a centroid marker persistent unless the field is saved.
        # Keep only the shaded polygon visible to satisfy UX requirement.
        if self.current_marker:
            try:
                self.current_marker.delete()
            except Exception:
                pass
        self.current_marker = None
        
        # Build GeoJSON
        coords = [[lon, lat] for lat, lon in self.polygon_points]
        # Ensure closed ring
        if coords[0] != coords[-1]:
            coords.append(coords[0])
        # Use current field name from input (fallback to default)
        name = self.entry_name.get().strip() or "Selected Area"
        self.polygon_geojson_value = {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [coords]},
            "properties": {"name": name}
        }

    def _translate_reason(self, code):
        mapping = {
            "validation_skipped": "Validation skipped (network).",
            "residential_or_building_area": "Overlaps with residential/building area.",
            "no_farmland_found": "No farmland landuse found.",
            "polygon_invalid": "Invalid polygon.",
            "ok": "Suitable"
        }
        return mapping.get(code, code)

    def clear_polygon(self):
        self.is_drawing_polygon = False
        self.polygon_points = []
        self.polygon_geojson_value = None
        self.area_sqm_value = None
        self.area_acres_value = None
        if self.polygon_shape:
            self.polygon_shape.delete()
            self.polygon_shape = None
        for m in self._vertex_markers:
            try:
                m.delete()
            except Exception:
                pass
        self._vertex_markers = []
        self.area_label.config(text="Area: -")
        try:
            self.map_widget.add_left_click_map_command(lambda *_: None)
        except Exception:
            pass
        try:
            if self._canvas_click_bind_id is not None:
                self.map_widget.canvas.unbind('<Button-1>', self._canvas_click_bind_id)
                self._canvas_click_bind_id = None
        except Exception:
            pass

    def _on_map_left_click_polygon(self, coords):
        if not self.is_drawing_polygon:
            return
        lat, lon = coords
        self.polygon_points.append((lat, lon))
        # Add a small vertex marker for visual feedback
        try:
            vm = self.map_widget.set_marker(lat, lon, text="•")
            self._vertex_markers.append(vm)
        except Exception:
            pass
        self._draw_or_update_polygon(open_shape=True)

    def _on_canvas_click_polygon(self, event):
        # Convert canvas pixel to lat/lon if API is available
        if not self.is_drawing_polygon:
            return
        try:
            # Use the correct method name from TkinterMapView
            conv = getattr(self.map_widget, 'convert_canvas_coords_to_decimal_coords', None)
            if conv is not None:
                lat, lon = conv(event.x, event.y)
                self._on_map_left_click_polygon((lat, lon))
                return
        except Exception as e:
            pass

    def _draw_or_update_polygon(self, open_shape=False):
        if self.polygon_shape:
            self.polygon_shape.delete()
            self.polygon_shape = None
        pts = self.polygon_points
        if len(pts) >= 2:
            # TkinterMapView supports set_polygon; if not, fallback to set_path
            try:
                self.polygon_shape = self.map_widget.set_polygon(pts, outline_color="green", fill_color="lightgreen", border_width=2)
            except Exception:
                path_pts = pts + ([pts[0]] if not open_shape and len(pts) > 2 else [])
                self.polygon_shape = self.map_widget.set_path(path_pts)

    # --- Geometry helpers ---
    def _compute_area_sqm(self, latlon_points):
        import math
        # Spherical excess method
        if len(latlon_points) < 3:
            return 0.0
        R = 6378137.0
        total = 0.0
        points = [(math.radians(lat), math.radians(lon)) for lat, lon in latlon_points]
        # Ensure closed
        if points[0] != points[-1]:
            points = points + [points[0]]
        for i in range(len(points) - 1):
            lat1, lon1 = points[i]
            lat2, lon2 = points[i + 1]
            total += (lon2 - lon1) * (2 + math.sin(lat1) + math.sin(lat2))
        area = abs(total) * (R * R) / 2.0
        return area

    def _polygon_centroid(self, latlon_points):
        # Approximate centroid on plane
        if not latlon_points:
            return None, None
        lat_sum = sum(p[0] for p in latlon_points)
        lon_sum = sum(p[1] for p in latlon_points)
        return lat_sum / len(latlon_points), lon_sum / len(latlon_points)

    def _point_in_poly(self, lat, lon, poly_points):
        # Ray casting
        x = lon
        y = lat
        inside = False
        n = len(poly_points)
        for i in range(n):
            lat1, lon1 = poly_points[i]
            lat2, lon2 = poly_points[(i + 1) % n]
            xi, yi = lon1, lat1
            xj, yj = lon2, lat2
            intersect = ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / ((yj - yi) if (yj - yi) != 0 else 1e-12) + xi)
            if intersect:
                inside = not inside
        return inside

    def _validate_farmland_overpass(self, user_poly_points):
        """Validate user polygon using OSM Overpass.

        Rules:
          - Reject if polygon significantly overlaps with residential/building/industrial/commercial.
          - Accept if farmland coverage is sufficient.

        Returns (ok: bool, reason: str)
        """
        import json
        import urllib.request
        import urllib.parse

        # Compute bounding box
        lats = [p[0] for p in user_poly_points]
        lons = [p[1] for p in user_poly_points]
        minLat, maxLat = min(lats), max(lats)
        minLon, maxLon = min(lons), max(lons)

        # Query farmland + residential + buildings in one request
        query = f"""
            [out:json][timeout:25];
            (
              way["landuse"="farmland"]({minLat},{minLon},{maxLat},{maxLon});
              relation["landuse"="farmland"]({minLat},{minLon},{maxLat},{maxLon});
              way["landuse"="residential"]({minLat},{minLon},{maxLat},{maxLon});
              relation["landuse"="residential"]({minLat},{minLon},{maxLat},{maxLon});
              way["landuse"~"industrial|commercial|retail"]({minLat},{minLon},{maxLat},{maxLon});
              way["building"]({minLat},{minLon},{maxLat},{maxLon});
            );
            out geom;
        """

        try:
            data = urllib.parse.urlencode({"data": query}).encode("utf-8")
            req = urllib.request.Request("https://overpass-api.de/api/interpreter", data=data)
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except Exception:
            # Network fail → don't block the user, but allow with warning
            return True, "validation_skipped"

        elements = payload.get("elements", [])
        farmland_polys = []
        residential_polys = []
        building_polys = []

        for el in elements:
            tags = el.get("tags", {})
            geom = el.get("geometry")
            if not geom or len(geom) < 3:
                continue
            coords = [(g["lat"], g["lon"]) for g in geom]
            if coords[0] != coords[-1]:
                coords.append(coords[0])
            if tags.get("landuse") == "farmland":
                farmland_polys.append(coords)
            elif tags.get("landuse") in {"residential", "industrial", "commercial", "retail"}:
                residential_polys.append(coords)
            elif "building" in tags:
                building_polys.append(coords)

        # If there are many buildings/residential overlaps, reject
        if not farmland_polys and (residential_polys or building_polys):
            # No farmland mapped but residential/buildings present
            # Sample quickly to ensure overlap
            GRID = 10
            total_user = 0
            res_or_bld_inside = 0
            for i in range(GRID + 1):
                for j in range(GRID + 1):
                    lat = minLat + (maxLat - minLat) * i / GRID
                    lon = minLon + (maxLon - minLon) * j / GRID
                    if self._point_in_poly(lat, lon, user_poly_points):
                        total_user += 1
                        if any(self._point_in_poly(lat, lon, rp) for rp in (residential_polys + building_polys)):
                            res_or_bld_inside += 1
            if total_user > 0 and (res_or_bld_inside / total_user) >= 0.15:
                return False, "residential_or_building_area"

        # Coverage based decision
        GRID = 12
        samples_in_user = 0
        samples_in_farmland = 0
        samples_in_res = 0
        for i in range(GRID + 1):
            for j in range(GRID + 1):
                lat = minLat + (maxLat - minLat) * i / GRID
                lon = minLon + (maxLon - minLon) * j / GRID
                if self._point_in_poly(lat, lon, user_poly_points):
                    samples_in_user += 1
                    if any(self._point_in_poly(lat, lon, fp) for fp in farmland_polys):
                        samples_in_farmland += 1
                    if any(self._point_in_poly(lat, lon, rp) for rp in (residential_polys + building_polys)):
                        samples_in_res += 1

        if samples_in_user == 0:
            return False, "polygon_invalid"

        farmland_ratio = samples_in_farmland / samples_in_user
        residential_ratio = samples_in_res / samples_in_user

        # Decision thresholds
        if residential_ratio >= 0.15:
            return False, "residential_or_building_area"

        if farmland_ratio >= 0.4:
            return True, "ok"

        # Not enough evidence of farmland
        return False, "no_farmland_found"

    def _validate_point_not_residential(self, lat, lon):
        """Validate a single point is not inside residential/building area using Overpass.

        Returns (ok: bool, reason: str)
        """
        import json
        import urllib.request
        import urllib.parse

        # Small bbox (~80-100m) around the point
        delta = 0.0008
        minLat, maxLat = lat - delta, lat + delta
        minLon, maxLon = lon - delta, lon + delta

        query = f"""
            [out:json][timeout:20];
            (
              way["landuse"="residential"]({minLat},{minLon},{maxLat},{maxLon});
              relation["landuse"="residential"]({minLat},{minLon},{maxLat},{maxLon});
              way["landuse"~"industrial|commercial|retail"]({minLat},{minLon},{maxLat},{maxLon});
              way["building"]({minLat},{minLon},{maxLat},{maxLon});
            );
            out geom;
        """

        try:
            data = urllib.parse.urlencode({"data": query}).encode("utf-8")
            req = urllib.request.Request("https://overpass-api.de/api/interpreter", data=data)
            with urllib.request.urlopen(req, timeout=25) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except Exception:
            return True, "validation_skipped"

        elements = payload.get("elements", [])
        polys = []
        for el in elements:
            geom = el.get("geometry")
            if not geom:
                continue
            coords = [(g["lat"], g["lon"]) for g in geom]
            if len(coords) >= 3:
                if coords[0] != coords[-1]:
                    coords.append(coords[0])
                polys.append(coords)
        # If point falls in any of these polygons, reject
        for poly in polys:
            if self._point_in_poly(lat, lon, poly):
                return False, "residential_or_building_area"
        return True, "ok"

    def load_field_for_edit(self, field_id):
        field = self.db.get_field(field_id)

        if field:

            self.editing_field_id = field[0]


            self.entry_name.delete(0, tk.END)
            self.entry_name.insert(0, field[1])

            self.entry_crop.set(field[3])


            self.sowing_calendar.selection_set(field[4])


            self.fertilizer_type.set(field[5])


            if field[6]:
                self.fertilizer_calendar.selection_set(field[6])


            self.humidity = field[7]
            self.rainfall = field[8]
            self.wind = field[9]
            self.pressure = field[10]
            self.image_paths = field[11].split(',') if field[11] else []

            if self.image_paths:
                self.load_field_photo(self.image_paths[0])


                for widget in self.photo_frame.winfo_children():
                    widget.destroy()


                self.photo_thumbnails = []
                for img_path in self.image_paths:
                    if os.path.exists(img_path):
                        try:
                            img = Image.open(img_path)
                            img.thumbnail((50, 50))
                            img_tk = ImageTk.PhotoImage(img)
                            label = tk.Label(self.photo_frame, image=img_tk)
                            label.image = img_tk
                            label.pack(side=tk.LEFT, padx=5)
                            self.photo_thumbnails.append(img_tk)
                        except Exception as e:
                            print(f"Error while uploading photo:{e}")



            self.lat = field[12]
            self.lon = field[13]

            # Polygon fields if present
            try:
                polygon_geojson = field[14] if len(field) > 14 else None
                area_sqm = field[15] if len(field) > 15 else None
                area_acres = field[16] if len(field) > 16 else None
            except Exception:
                polygon_geojson = None
                area_sqm = None
                area_acres = None
            if polygon_geojson:
                import json
                try:
                    gj = json.loads(polygon_geojson)
                    coords = gj.get("geometry", {}).get("coordinates", [])
                    if coords and coords[0]:
                        self.polygon_points = [(lat, lon) for lon, lat in coords[0]]
                        self._draw_or_update_polygon()
                        self.area_sqm_value = area_sqm
                        self.area_acres_value = area_acres
                        if area_sqm and area_acres:
                            self.area_label.config(text=f"Area: {int(area_sqm):,} m² • {float(area_acres):.2f} acres".replace(',', '.'))
                except Exception:
                    pass


            if self.lat and self.lon:
                self.map_widget.set_position(self.lat, self.lon)
                if self.current_marker:
                    self.current_marker.delete()



            weather_text = f"💧 Humidity: {self.humidity}%\n🌧 Rain: {self.rainfall} mm\n💨 Wind: {self.wind} m/s\n📊 Pressure: {self.pressure} hPa"
            self.weather_label.config(text=weather_text)


            self.save_button.config(text="Update Field", command=self.update_field)

    def save_field(self):
        try:
            name = self.entry_name.get()

            crop = self.entry_crop.get()
            sowing_date = self.sowing_calendar.get_date()
            fertilizer_type = self.fertilizer_type.get()
            fertilizer_dates = self.fertilizer_calendar.get_date()

            if self.polygon_geojson_value is None and None in [self.lat, self.lon]:
                messagebox.showerror("Warning", "Please select a point on the map or draw a polygon.")
                return
            # If only a point is selected, validate it is not in residential/building area
            if self.polygon_geojson_value is None and self.lat is not None and self.lon is not None:
                ok, reason = self._validate_point_not_residential(self.lat, self.lon)
                if not ok:
                    messagebox.showwarning("Warning", "The selected point is not suitable: " + self._translate_reason(reason))
                    return

            # If polygon exists, prefer centroid lat/lon and computed area to override size
            save_lat = self.lat
            save_lon = self.lon
            polygon_geojson_str = None
            area_sqm = None
            area_acres = None
            size = 0.0  # Default size
            if self.polygon_geojson_value is not None:
                import json
                polygon_geojson_str = json.dumps(self.polygon_geojson_value)
                area_sqm = float(self.area_sqm_value or 0.0)
                area_acres = float(self.area_acres_value or 0.0)
                if area_acres > 0:
                    size = area_acres

            field_data = (
                name, size, crop, sowing_date, fertilizer_type, fertilizer_dates,
                self.humidity, self.rainfall, self.wind, self.pressure,
                ','.join(self.image_paths), save_lat, save_lon, polygon_geojson_str, area_sqm, area_acres
            )

            self.db.save_field(field_data)


            if self.current_marker:
                self.current_marker.delete()
                self.current_marker = None


            messagebox.showinfo("Successful", "The field was recorded.")
            self.clear_form()
            self.on_save_callback()

        except Exception as e:
            messagebox.showerror("Warning", f"An error occurred during registration:\n{e}")

    def update_field(self):
        try:
            name = self.entry_name.get()
            size = 0.0  # Default size
            crop = self.entry_crop.get()
            sowing_date = self.sowing_calendar.get_date()
            fertilizer_type = self.fertilizer_type.get()
            fertilizer_dates = self.fertilizer_calendar.get_date()

            if self.polygon_geojson_value is None and None in [self.lat, self.lon]:
                messagebox.showerror("Warning", "Please select a point on the map or draw a polygon.")
                return
            # Validate single-point update as well
            if self.polygon_geojson_value is None and self.lat is not None and self.lon is not None:
                ok, reason = self._validate_point_not_residential(self.lat, self.lon)
                if not ok:
                    messagebox.showwarning("Warning", "The selected point is not suitable: " + self._translate_reason(reason))
                    return

            save_lat = self.lat
            save_lon = self.lon
            polygon_geojson_str = None
            area_sqm = None
            area_acres = None
            if self.polygon_geojson_value is not None:
                import json
                polygon_geojson_str = json.dumps(self.polygon_geojson_value)
                area_sqm = float(self.area_sqm_value or 0.0)
                area_acres = float(self.area_acres_value or 0.0)
                if area_acres > 0:
                    size = area_acres

            field_data = (
                name, size, crop, sowing_date, fertilizer_type, fertilizer_dates,
                self.humidity, self.rainfall, self.wind, self.pressure,
                ','.join(self.image_paths), save_lat, save_lon, polygon_geojson_str, area_sqm, area_acres
            )

            self.db.update_field(field_data, self.editing_field_id)


            if self.current_marker:
                self.current_marker.delete()
                self.current_marker = None


            messagebox.showinfo("Successful", "The field has been updated.")
            self.clear_form()
            self.on_save_callback()


            self.save_button.config(text="Save Field", command=self.save_field)


            self.editing_field_id = None

        except Exception as e:
            messagebox.showerror("Warning", f"An error occurred during the update:\n{e}")

    def cancel_form(self):
        """Cancel form entry - clears form and removes marker"""
        if self.lat is not None or self.lon is not None or self.current_marker is not None:
            result = messagebox.askyesno(
                "Cancel",
                "Are you sure you want to cancel without saving?\nAll entered information will be deleted.",
                icon='question'
            )
            if result:
                self.clear_form()
                messagebox.showinfo("Cancelled", "Operation cancelled.")
        else:
            self.clear_form()

    def clear_form(self):
        self.entry_name.delete(0, tk.END)
        self.entry_crop.set('')
        self.sowing_calendar.selection_clear()
        self.fertilizer_type.set('')
        self.fertilizer_calendar.selection_clear()


        self.lat = None
        self.lon = None
        self.humidity = None
        self.rainfall = None
        self.wind = None
        self.pressure = None


        self.weather_label.config(text="Select a location on the map to view weather data")


        self.image_paths = []
        for widget in self.photo_frame.winfo_children():
            widget.destroy()


        self.image_label.config(image='', text="No photos uploaded")
        self.image_label.image = None


        if self.current_marker:
            self.current_marker.delete()
            self.current_marker=None
        # Clear polygon
        self.clear_polygon()
        # Reset save button text and command if it was in edit mode
        self.save_button.config(text="💾 SAVE FIELD", command=self.save_field)
        self.editing_field_id = None