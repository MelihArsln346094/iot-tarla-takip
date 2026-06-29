import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os
import threading
from tkintermapview import TkinterMapView

class FieldView:
    def __init__(self, parent, map_widget, db, weather_service, on_edit_callback, on_delete_callback):
        self.parent = parent
        self.map_widget = map_widget
        self.db = db
        self.weather_service = weather_service
        self.on_edit_callback = on_edit_callback
        self.on_delete_callback = on_delete_callback
        self.field_markers = []
        self.field_polygons = []
        self.field_cards = {}  # Store card widgets: {field_id: card_frame}
        self.selected_field_id = None
        self._location_cache = {}  # Cache for location info

        self.build_view()

    def build_view(self):
        # Header frame with refresh button
        header_frame = tk.Frame(self.parent, bg='#ECEFF1')
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        title_label = tk.Label(
            header_frame,
            text="🌾 My Fields",
            font=("Segoe UI", 16, "bold"),
            bg='#ECEFF1',
            fg='#2E7D32'
        )
        title_label.pack(side=tk.LEFT)
        
        refresh_btn = tk.Button(
            header_frame,
            text="🔄 Refresh",
            font=("Segoe UI", 9),
            bg='#2E7D32',
            fg='white',
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor="hand2",
            command=self.load_all_fields
        )
        refresh_btn.pack(side=tk.RIGHT)
        refresh_btn.bind("<Enter>", lambda e: refresh_btn.config(bg='#1B5E20'))
        refresh_btn.bind("<Leave>", lambda e: refresh_btn.config(bg='#2E7D32'))

        # Scrollable canvas for cards
        canvas_frame = tk.Frame(self.parent, bg='#ECEFF1')
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.canvas = tk.Canvas(canvas_frame, bg='#ECEFF1', highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg='#ECEFF1')
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel to canvas
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Empty state info
        self.empty_label = tk.Label(
            self.scrollable_frame,
            text="No fields found.\nAdd a new field from the '🌱 ADD FIELD' tab.",
            font=("Segoe UI", 11),
            bg='#ECEFF1',
            fg='#757575',
            justify="center"
        )
    
    def _load_location_info_async(self, label, lat, lon):
        """Load location info asynchronously without blocking UI"""
        cache_key = f"{lat:.4f},{lon:.4f}"
        if cache_key in self._location_cache:
            location_text = self._location_cache[cache_key]
            if location_text and location_text != "Location Could Not Be Retrieved":
                display_text = location_text[:30] + "..." if len(location_text) > 30 else location_text
                label.config(text=display_text)
            return
        
        def fetch_location():
            try:
                location_info = self.weather_service.get_location_info(lat, lon)
                self._location_cache[cache_key] = location_info
                if location_info and location_info != "Location Could Not Be Retrieved":
                    display_text = location_info[:30] + "..." if len(location_info) > 30 else location_info
                    # Update UI in main thread
                    label.after(0, lambda: label.config(text=display_text))
            except Exception:
                pass
        
        # Run in background thread
        thread = threading.Thread(target=fetch_location, daemon=True)
        thread.start()

    def create_field_card(self, field_data, full_field=None):
        """Create a modern card widget for a field
        
        Args:
            field_data: Tuple of (field_id, name, lat, lon, polygon_geojson)
            full_field: Optional full field data to avoid extra DB call
        """
        field_id, name, lat, lon, polygon_geojson = field_data
        
        # Get full field details only if not provided
        if full_field is None:
            full_field = self.db.get_field(field_id)
            if not full_field:
                return None
        
        # Card container with border for shadow effect
        card_frame = tk.Frame(
            self.scrollable_frame,
            bg='white',
            relief=tk.FLAT,
            borderwidth=1,
            highlightbackground='#E0E0E0',
            highlightthickness=1
        )
        card_frame.pack(fill=tk.X, padx=10, pady=8)
        
        # Card content frame
        content_frame = tk.Frame(card_frame, bg='white')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        # Header section with field name and crop
        header_frame = tk.Frame(content_frame, bg='white')
        header_frame.pack(fill=tk.X, pady=(0, 12))
        
        # Field icon and name
        name_frame = tk.Frame(header_frame, bg='white')
        name_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        field_icon = tk.Label(
            name_frame,
            text="🌾",
            font=("Segoe UI", 20),
            bg='white'
        )
        field_icon.pack(side=tk.LEFT, padx=(0, 10))
        
        name_label = tk.Label(
            name_frame,
            text=name or "Unnamed Field",
            font=("Segoe UI", 14, "bold"),
            bg='white',
            fg='#212121',
            anchor="w"
        )
        name_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Crop type badge
        crop_type = full_field[3] if full_field and len(full_field) > 3 else "N/A"
        crop_badge = tk.Label(
            header_frame,
            text=crop_type,
            font=("Segoe UI", 9, "bold"),
            bg='#E8F5E9',
            fg='#2E7D32',
            padx=12,
            pady=4,
            relief=tk.FLAT
        )
        crop_badge.pack(side=tk.RIGHT)
        
        # Information grid
        info_frame = tk.Frame(content_frame, bg='white')
        info_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Size/Area
        if full_field and len(full_field) > 2 and full_field[2]:
            size_frame = tk.Frame(info_frame, bg='#F5F5F5', relief=tk.FLAT)
            size_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
            
            tk.Label(
                size_frame,
                text="📏 Size",
                font=("Segoe UI", 8),
                bg='#F5F5F5',
                fg='#757575'
            ).pack(anchor="w", padx=10, pady=(8, 2))
            
            size_value = f"{full_field[2]} acres"
            if len(full_field) > 15 and full_field[15]:  # area_acres
                size_value = f"{full_field[15]:.2f} acres"
            
            tk.Label(
                size_frame,
                text=size_value,
                font=("Segoe UI", 11, "bold"),
                bg='#F5F5F5',
                fg='#212121'
            ).pack(anchor="w", padx=10, pady=(0, 8))
        
        # Planting Date
        if full_field and len(full_field) > 4 and full_field[4]:
            date_frame = tk.Frame(info_frame, bg='#F5F5F5', relief=tk.FLAT)
            date_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
            
            tk.Label(
                date_frame,
                text="📅 Planting Date",
                font=("Segoe UI", 8),
                bg='#F5F5F5',
                fg='#757575'
            ).pack(anchor="w", padx=10, pady=(8, 2))
            
            tk.Label(
                date_frame,
                text=full_field[4],
                font=("Segoe UI", 11, "bold"),
                bg='#F5F5F5',
                fg='#212121'
            ).pack(anchor="w", padx=10, pady=(0, 8))
        
        # Location - load asynchronously
        if lat and lon:
            loc_frame = tk.Frame(info_frame, bg='#F5F5F5', relief=tk.FLAT)
            loc_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            tk.Label(
                loc_frame,
                text="📍 Location",
                font=("Segoe UI", 8),
                bg='#F5F5F5',
                fg='#757575'
            ).pack(anchor="w", padx=10, pady=(8, 2))
            
            location_label = tk.Label(
                loc_frame,
                text=f"{lat:.4f}, {lon:.4f}",
                font=("Segoe UI", 10),
                bg='#F5F5F5',
                fg='#212121'
            )
            location_label.pack(anchor="w", padx=10, pady=(0, 8))
            
            # Load location info asynchronously
            self._load_location_info_async(location_label, lat, lon)
        
        # Action buttons
        button_frame = tk.Frame(content_frame, bg='white')
        button_frame.pack(fill=tk.X)
        
        def create_action_button(text, bg_color, hover_color, command):
            btn = tk.Button(
                button_frame,
                text=text,
                font=("Segoe UI", 9, "bold"),
                bg=bg_color,
                fg='white',
                relief=tk.FLAT,
                padx=15,
                pady=8,
                cursor="hand2",
                command=command
            )
            btn.pack(side=tk.LEFT, padx=(0, 8))
            btn.bind("<Enter>", lambda e, c=hover_color: btn.config(bg=c))
            btn.bind("<Leave>", lambda e, c=bg_color: btn.config(bg=c))
            return btn
        
        create_action_button(
            "📝 Edit",
            '#1976D2',
            '#1565C0',
            lambda: self.edit_field(field_id)
        )
        
        create_action_button(
            "👁️ View Details",
            '#388E3C',
            '#2E7D32',
            lambda: self.show_field_details(field_id)
        )
        
        create_action_button(
            "🗑️ Delete",
            '#D32F2F',
            '#C62828',
            lambda: self.delete_field(field_id)
        )
        
        # Store card reference
        self.field_cards[field_id] = card_frame
        
        return card_frame

    def load_all_fields(self):
        """Load all fields with optimized batch queries"""
        # Clear existing cards
        for card_frame in self.field_cards.values():
            card_frame.destroy()
        self.field_cards = {}
        self.selected_field_id = None

        # Clear map markers and polygons
        for marker in self.field_markers:
            marker.delete()
        self.field_markers = []
        for poly in getattr(self, 'field_polygons', []):
            try:
                poly.delete()
            except Exception:
                pass
        self.field_polygons = []

        # Get all fields with details in one query instead of N+1 queries
        if hasattr(self.db, 'get_all_fields_with_details'):
            all_fields = self.db.get_all_fields_with_details()
        else:
            # Fallback to old method
            basic_fields = self.db.get_all_fields()
            all_fields = []
            for field in basic_fields:
                full_field = self.db.get_field(field[0])
                if full_field:
                    all_fields.append(full_field)
        
        # Create a mapping: (id, name, lat, lon, polygon_geojson) -> full_field
        field_map = {}
        basic_fields_list = []
        for full_field in all_fields:
            field_id = full_field[0]
            name = full_field[1] if len(full_field) > 1 else ""
            lat = full_field[12] if len(full_field) > 12 else None
            lon = full_field[13] if len(full_field) > 13 else None
            polygon_geojson = full_field[14] if len(full_field) > 14 else None
            basic_field = (field_id, name, lat, lon, polygon_geojson)
            basic_fields_list.append(basic_field)
            field_map[basic_field] = full_field

        if not basic_fields_list:
            # Show empty state
            if hasattr(self, 'empty_label') and self.empty_label:
                if not self.empty_label.winfo_ismapped():
                    self.empty_label.pack(pady=30)
        else:
            if hasattr(self, 'empty_label') and self.empty_label:
                if self.empty_label.winfo_ismapped():
                    self.empty_label.pack_forget()

            # Process fields in batches to avoid blocking UI
            self._load_fields_batch(basic_fields_list, field_map, batch_size=5)
    
    def _load_fields_batch(self, fields, field_map, batch_size=5):
        """Load fields in batches to avoid blocking UI"""
        if not fields:
            # Update canvas scroll region when done
            self.canvas.update_idletasks()
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            return
        
        # Process one batch
        batch = fields[:batch_size]
        remaining = fields[batch_size:]
        
        for field in batch:
            field_id, name, lat, lon, polygon_geojson = field
            full_field = field_map.get(field)
            
            # Create card with pre-fetched data
            self.create_field_card(field, full_field)
            
            # Add to map
            if polygon_geojson:
                try:
                    import json
                    gj = json.loads(polygon_geojson)
                    coords = gj.get("geometry", {}).get("coordinates", [])
                    if coords and coords[0]:
                        points = [(latv, lonv) for lonv, latv in coords[0]]
                        try:
                            poly = self.map_widget.set_polygon(points, outline_color="green", fill_color="lightgreen", border_width=2)
                        except Exception:
                            poly = self.map_widget.set_path(points + [points[0]])
                        self.field_polygons.append(poly)
                except Exception:
                    pass
            
            if lat and lon:
                marker = self.map_widget.set_marker(
                    lat, lon,
                    text=f"🌾 {name}",
                    marker_color_circle="green",
                    marker_color_outside="darkgreen"
                )
                self.field_markers.append(marker)
        
        # Schedule next batch
        if remaining:
            self.parent.after(10, lambda: self._load_fields_batch(remaining, field_map, batch_size))
        else:
            # Update canvas scroll region when done
            self.canvas.update_idletasks()
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def edit_field(self, field_id):
        """Edit field - called from card button"""
        for marker in self.field_markers:
            marker.delete()
        self.field_markers = []
        self.on_edit_callback(field_id)

    def show_field_details(self, field_id):
        """Show modern, detailed field information window"""
        field = self.db.get_field(field_id)
        if not field:
            messagebox.showwarning("Error", "Field data could not be retrieved.")
            return

        # Safely get field values with proper length checks
        def safe_get(index, default=None):
            if field and len(field) > index:
                value = field[index]
                return value if value is not None and value != "" else default
            return default

        field_name = safe_get(1, "Unnamed Field")
        field_size = safe_get(2)
        crop_type = safe_get(3, "N/A")
        planting_date = safe_get(4)
        fertilizer_type = safe_get(5)
        fertilizer_date = safe_get(6)
        humidity = safe_get(7)
        rainfall = safe_get(8)
        wind = safe_get(9)
        pressure = safe_get(10)
        image_url = safe_get(11)
        lat = safe_get(12)
        lon = safe_get(13)
        polygon_geojson = safe_get(14)
        area_sqm = safe_get(15)  # area_sqm is at index 15
        area_acres = safe_get(16)  # area_acres is at index 16

        # Create modern detail window
        detail_window = tk.Toplevel(self.parent)
        detail_window.title(f"📋 {field_name}")
        detail_window.geometry("900x700")
        detail_window.configure(bg='#FFFFFF')
        detail_window.resizable(True, True)

        # Header with gradient effect
        header = tk.Frame(detail_window, bg='#2E7D32', height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        # Header content
        header_content = tk.Frame(header, bg='#2E7D32')
        header_content.pack(fill=tk.BOTH, expand=True, padx=30, pady=15)

        # Field name and icon
        title_frame = tk.Frame(header_content, bg='#2E7D32')
        title_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(title_frame, text="🌾", font=("Segoe UI", 24),
                bg='#2E7D32', fg='white').pack(side=tk.LEFT, padx=(0, 10))

        name_label = tk.Label(title_frame, 
                text=field_name,
                font=("Segoe UI", 18, "bold"),
                bg='#2E7D32', fg='white')
        name_label.pack(side=tk.LEFT)

        # Crop badge in header
        crop_badge = tk.Label(header_content,
                text=crop_type,
                font=("Segoe UI", 11, "bold"),
                bg='#4CAF50',
                fg='white',
                padx=15,
                pady=8,
                relief=tk.FLAT)
        crop_badge.pack(side=tk.RIGHT, padx=(10, 0))

        # Close button
        close_btn = tk.Button(header_content, text="✕", font=("Segoe UI", 16),
                             bg='#C62828', fg='white', relief=tk.FLAT,
                             command=detail_window.destroy, cursor="hand2",
                             padx=12, pady=5)
        close_btn.pack(side=tk.RIGHT, padx=(10, 0))

        # Main content area with scrollbar
        content_frame = tk.Frame(detail_window, bg='#F5F5F5')
        content_frame.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(content_frame, bg='#F5F5F5', highlightthickness=0)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#F5F5F5')

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=20)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Information cards
        main_container = tk.Frame(scrollable_frame, bg='#F5F5F5')
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Card 1: Basic Information
        card1 = tk.Frame(main_container, bg='white', relief=tk.FLAT, bd=0)
        card1.pack(fill=tk.X, pady=(0, 15))
        card1.config(highlightbackground='#E0E0E0', highlightthickness=1)

        card1_header = tk.Frame(card1, bg='#E8F5E9', height=50)
        card1_header.pack(fill=tk.X)
        tk.Label(card1_header, text="📝 Basic Information", font=("Segoe UI", 14, "bold"),
                bg='#E8F5E9', fg='#2E7D32').pack(anchor='w', padx=20, pady=12)

        card1_content = tk.Frame(card1, bg='white')
        card1_content.pack(fill=tk.X, padx=20, pady=20)

        # Create info rows
        def create_info_row(parent, label, value, icon=""):
            row = tk.Frame(parent, bg='white')
            row.pack(fill=tk.X, pady=8)
            tk.Label(row, text=icon, font=("Segoe UI", 12), bg='white', fg='#616161').pack(side=tk.LEFT, padx=(0, 10))
            tk.Label(row, text=label, font=("Segoe UI", 10), bg='white', fg='#757575', width=20, anchor='w').pack(side=tk.LEFT)
            display_value = str(value) if value is not None and value != "" else "N/A"
            tk.Label(row, text=display_value, font=("Segoe UI", 11, "bold"),
                    bg='white', fg='#212121', anchor='w').pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Calculate size value safely
        size_value = "N/A"
        if area_acres:
            try:
                area_acres_float = float(area_acres) if area_acres not in [None, ""] else None
                if area_acres_float is not None:
                    size_value = f"{area_acres_float:.2f} acres"
                    if area_sqm:
                        try:
                            area_sqm_float = float(area_sqm) if area_sqm not in [None, ""] else None
                            if area_sqm_float is not None:
                                size_value += f" ({area_sqm_float:,.0f} m²)".replace(',', '.')
                        except (ValueError, TypeError):
                            pass
            except (ValueError, TypeError):
                pass
        elif field_size:
            try:
                field_size_float = float(field_size) if field_size not in [None, ""] else None
                if field_size_float is not None:
                    size_value = f"{field_size_float:.2f} acres"
                else:
                    size_value = str(field_size) if field_size else "N/A"
            except (ValueError, TypeError):
                size_value = str(field_size) if field_size else "N/A"

        create_info_row(card1_content, "Field Name:", field_name, "🏷️")
        create_info_row(card1_content, "Size:", size_value, "📏")
        create_info_row(card1_content, "Crop Type:", crop_type, "🌾")
        create_info_row(card1_content, "Planting Date:", planting_date, "📅")

        # Card 2: Fertilizer Information
        if fertilizer_type or fertilizer_date:
            card2 = tk.Frame(main_container, bg='white', relief=tk.FLAT, bd=0)
            card2.pack(fill=tk.X, pady=(0, 15))
            card2.config(highlightbackground='#E0E0E0', highlightthickness=1)

            card2_header = tk.Frame(card2, bg='#FFF3E0', height=50)
            card2_header.pack(fill=tk.X)
            tk.Label(card2_header, text="🧪 Fertilizer Information", font=("Segoe UI", 14, "bold"),
                    bg='#FFF3E0', fg='#F57C00').pack(anchor='w', padx=20, pady=12)

            card2_content = tk.Frame(card2, bg='white')
            card2_content.pack(fill=tk.X, padx=20, pady=20)

            create_info_row(card2_content, "Fertilizer Type:", fertilizer_type, "💊")
            create_info_row(card2_content, "Fertilizer Date:", fertilizer_date, "📆")

        # Card 3: Location Information
        if lat is not None and lon is not None:
            try:
                lat_float = float(lat)
                lon_float = float(lon)
                
                card3 = tk.Frame(main_container, bg='white', relief=tk.FLAT, bd=0)
                card3.pack(fill=tk.X, pady=(0, 15))
                card3.config(highlightbackground='#E0E0E0', highlightthickness=1)

                card3_header = tk.Frame(card3, bg='#E3F2FD', height=50)
                card3_header.pack(fill=tk.X)
                tk.Label(card3_header, text="📍 Location Information", font=("Segoe UI", 14, "bold"),
                        bg='#E3F2FD', fg='#1565C0').pack(anchor='w', padx=20, pady=12)

                card3_content = tk.Frame(card3, bg='white')
                card3_content.pack(fill=tk.X, padx=20, pady=20)

                location_text = f"{lat_float:.6f}, {lon_float:.6f}"
                try:
                    location = self.weather_service.get_location_info(lat_float, lon_float)
                    if location and location != "Location Could Not Be Retrieved":
                        location_text = location
                except:
                    pass

                create_info_row(card3_content, "Coordinates:", f"{lat_float:.6f}, {lon_float:.6f}", "🌍")
                create_info_row(card3_content, "Address:", location_text, "🏠")

                # Update map position
                self.map_widget.set_position(lat_float, lon_float)
            except (ValueError, TypeError):
                pass

        # Card 4: Field Photos
        if image_url:
            photos = [p.strip() for p in image_url.split(',') if p.strip()]
            if photos:
                card4 = tk.Frame(main_container, bg='white', relief=tk.FLAT, bd=0)
                card4.pack(fill=tk.X, pady=(0, 15))
                card4.config(highlightbackground='#E0E0E0', highlightthickness=1)

                card4_header = tk.Frame(card4, bg='#FCE4EC', height=50)
                card4_header.pack(fill=tk.X)
                tk.Label(card4_header, text="📷 Field Photos", font=("Segoe UI", 14, "bold"),
                        bg='#FCE4EC', fg='#C2185B').pack(anchor='w', padx=20, pady=12)

                card4_content = tk.Frame(card4, bg='white')
                card4_content.pack(fill=tk.X, padx=20, pady=20)

                photos_frame = tk.Frame(card4_content, bg='white')
                photos_frame.pack(fill=tk.BOTH, expand=True)

                for photo_path in photos:
                    if os.path.exists(photo_path):
                        try:
                            img = Image.open(photo_path)
                            # Resize maintaining aspect ratio
                            img.thumbnail((250, 200), Image.Resampling.LANCZOS)
                            photo = ImageTk.PhotoImage(img)
                            
                            photo_container = tk.Frame(photos_frame, bg='white', relief=tk.RAISED, bd=1)
                            photo_container.pack(side=tk.LEFT, padx=10, pady=10)
                            
                            img_label = tk.Label(photo_container, image=photo, bg='white')
                            img_label.image = photo  # Keep a reference
                            img_label.pack(padx=5, pady=5)
                        except Exception as e:
                            print(f"Error loading image {photo_path}: {e}")

        # Center window on screen
        detail_window.update_idletasks()
        x = (detail_window.winfo_screenwidth() // 2) - (detail_window.winfo_width() // 2)
        y = (detail_window.winfo_screenheight() // 2) - (detail_window.winfo_height() // 2)
        detail_window.geometry(f"+{x}+{y}")

    def delete_field(self, field_id):
        """Delete field - called from card button"""
        result = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete this field?\nThis action cannot be undone.",
            icon='warning'
        )
        
        if result:
            delete_result = self.db.delete_field(field_id)
            
            if delete_result:
                lat, lon = delete_result
                for marker in self.field_markers:
                    if marker.position == (lat, lon):
                        marker.delete()
                        self.field_markers.remove(marker)
                        break
            
            self.load_all_fields()
            self.on_delete_callback()
            messagebox.showinfo("Successful", "The field was deleted.")