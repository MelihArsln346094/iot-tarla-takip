import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime, timedelta
import time


# Default ideal moisture ranges by crop (percent)
DEFAULT_CROP_TARGETS = {
    "Wheat": (60, 70),
    "🌾 Wheat": (60, 70),
    "Corn": (55, 65),
    "🌽 Corn": (55, 65),
    "Tomato": (70, 80),
    "Sunflower": (50, 60),
    "🌻 Sunflower": (50, 60),
    "Cotton": (55, 65),
    "☁ Cotton": (55, 65),
    "Barley": (55, 70),
    "🌿 Barley": (55, 70),
}

class WaterControl:
    def __init__(self, parent, db, arduino_connection=None):
        self.parent = parent
        self.db = db
        self.arduino_connection = arduino_connection

        # State
        self.manual_override = False
        self.manual_timer_id = None
        self.pump_on = False
        self.running = True
        self.last_value = 0
        self.auto_mode = True  # Auto irrigation mode
        
        # Hysteresis to prevent rapid on/off cycling
        self.hysteresis = 2.0  # 2% hysteresis band
        
        # Sensor calibration values
        self.sensor_min = 520      # en ıslak okuma
        self.sensor_max = 930      # en kuru okuma
        
        # Last read values from Arduino
        self.last_nem_degeri = 0
        self.arduino_auto_mode = True  # Arduino's current mode

        self._build_ui()
        self._load_fields()
        self._on_field_selected(None)
        
        # Register callbacks for Arduino data
        if self.arduino_connection:
            self.arduino_connection.register_moisture_callback(self.on_moisture_received)
            self.arduino_connection.register_pump_callback(self.on_pump_status_changed)
            self.arduino_connection.register_mode_callback(self.on_mode_changed)
            # Initialize from shared connection
            self.last_nem_degeri = self.arduino_connection.get_moisture_value()
            self.pump_on = self.arduino_connection.get_pump_status()
            self.arduino_auto_mode = self.arduino_connection.get_mode()
            # Set initial mode when connection is available
            if self.arduino_connection.is_connected():
                if self.auto_mode:
                    self.arduino_connection.write_command(b'O')
                else:
                    self.arduino_connection.write_command(b'M')

        # Start periodic loop
        self._tick()

    # ---------------- UI ----------------
    def _build_ui(self):
        root = ttk.Frame(self.parent)
        root.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        header = ttk.LabelFrame(root, text="Water & Moisture Control")
        header.pack(fill=tk.X)

        ttk.Label(header, text="Field:").grid(row=0, column=0, padx=6, pady=8, sticky=tk.W)
        self.field_var = tk.StringVar()
        self.field_combo = ttk.Combobox(header, textvariable=self.field_var, width=28, state="readonly")
        self.field_combo.grid(row=0, column=1, padx=6, pady=8, sticky=tk.W)
        self.field_combo.bind("<<ComboboxSelected>>", self._on_field_selected)

        ttk.Label(header, text="Crop:").grid(row=0, column=2, padx=6, pady=8, sticky=tk.E)
        self.current_crop_lbl = ttk.Label(header, text="-")
        self.current_crop_lbl.grid(row=0, column=3, padx=6, pady=8, sticky=tk.W)

        ttk.Label(header, text="Target Range:").grid(row=1, column=0, padx=6, pady=8, sticky=tk.E)
        # Modern target range display with visual indicator
        target_frame = tk.Frame(header, bg='white')
        target_frame.grid(row=1, column=1, padx=6, pady=8, sticky=tk.W)
        self.target_lbl = tk.Label(target_frame, text="--% – --%", 
                                  font=("Segoe UI", 11, "bold"), bg='white', fg='#2E7D32')
        self.target_lbl.pack(side=tk.LEFT, padx=(0, 8))
        # Visual range indicator
        self.target_indicator = tk.Canvas(target_frame, width=120, height=35, highlightthickness=0, bg='white')
        self.target_indicator.pack(side=tk.LEFT)
        
        # Mode selection (Automatic/Manual)
        ttk.Label(header, text="Mode:").grid(row=1, column=2, padx=6, pady=8, sticky=tk.E)
        self.mode_var = tk.StringVar(value="Automatic")
        mode_frame = ttk.Frame(header)
        mode_frame.grid(row=1, column=3, padx=6, pady=8, sticky=tk.W)
        ttk.Radiobutton(mode_frame, text="Automatic", variable=self.mode_var, 
                       value="Automatic", command=self._on_mode_changed).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="Manual", variable=self.mode_var, 
                       value="Manual", command=self._on_mode_changed).pack(side=tk.LEFT, padx=5)
        
        # Connection status
        self.connection_status_lbl = ttk.Label(header, text="● Arduino: Disconnected", foreground="red", font=("Segoe UI", 8))
        self.connection_status_lbl.grid(row=2, column=0, columnspan=4, padx=6, pady=4, sticky=tk.W)

        # Indicators
        ind = ttk.LabelFrame(root, text="Live Sensor & Pump")
        ind.pack(fill=tk.X, pady=8)

        # Current value
        left = ttk.Frame(ind)
        left.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=6, pady=6)
        ttk.Label(left, text="Current Soil Moisture (%)", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W)
        self.current_lbl = ttk.Label(left, text="--", font=("Segoe UI", 22, "bold"))
        self.current_lbl.pack(anchor=tk.W)
        self.status_lbl = ttk.Label(left, text="Waiting for sensor…")
        self.status_lbl.pack(anchor=tk.W, pady=(4, 0))

        # Pump block
        right = ttk.Frame(ind)
        right.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=6, pady=6)
        self.pump_status_label = ttk.Label(right, text="Pump Status", font=("Segoe UI", 10, "bold"))
        self.pump_status_label.pack(anchor=tk.W)
        self.pump_indicator = tk.Canvas(right, width=16, height=16, highlightthickness=0)
        self.pump_indicator.pack(anchor=tk.W, pady=2)
        self.pump_label = ttk.Label(right, text="OFF")
        self.pump_label.pack(anchor=tk.W)

        # Controls
        controls = ttk.Frame(root)
        controls.pack(fill=tk.X)
        self.btn_start = ttk.Button(controls, text="💧 Start Watering", command=self._manual_start)
        self.btn_start.pack(side=tk.LEFT, padx=4, pady=6)
        self.btn_stop = ttk.Button(controls, text="🛑 Stop Watering", command=self._manual_stop)
        self.btn_stop.pack(side=tk.LEFT, padx=4, pady=6)
        self.manual_help_label = ttk.Label(controls, text="Manual controls for manual mode.", foreground="#555")
        self.manual_help_label.pack(side=tk.LEFT, padx=12)

        # Graph frame for historical soil moisture data
        graph_frame = ttk.LabelFrame(root, text="Historical Soil Moisture")
        graph_frame.pack(fill=tk.BOTH, expand=True, pady=8)

        # Time range selector
        time_frame = ttk.Frame(graph_frame)
        time_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(time_frame, text="Time Range:").pack(side=tk.LEFT, padx=5)
        self.time_var = tk.StringVar(value="Last 24 Hours")
        time_options = ["Last 1 Hour", "Last 6 Hours", "Last 24 Hours", "Last 7 Days"]
        time_selector = ttk.Combobox(time_frame, textvariable=self.time_var, values=time_options, width=15, state="readonly")
        time_selector.pack(side=tk.LEFT, padx=5)
        time_selector.bind("<<ComboboxSelected>>", self._update_graph)

        # Create matplotlib figure
        self.fig, self.ax = plt.subplots(1, 1, figsize=(10, 4), dpi=80)
        self.canvas_widget = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas_widget.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Data storage for graph
        self.graph_timestamps = []
        self.graph_moisture_data = []
        
        # Initialize mode state
        self._on_mode_changed()
        
        # Initialize target range display
        self._draw_target_range(55, 70)  # Default range

    # ------------- Data / Targets -------------
    def _load_fields(self):
        """Load fields from database and update the combo. If current selection is deleted, clear it."""
        try:
            fields = self.db.get_all_fields()
        except Exception:
            fields = []
        items = [f"{row[0]} - {row[1]}" for row in fields] if fields else []
        self.field_combo["values"] = items
        
        # Check if currently selected field still exists
        current_selection = self.field_var.get()
        if current_selection:
            current_field_id = current_selection.split(" - ")[0]
            # Check if this field still exists in the new list
            field_ids = [f"{row[0]}" for row in fields]
            if current_field_id not in field_ids:
                # Selected field was deleted - clear selection and data
                self.field_var.set("")
                self.current_crop_lbl.config(text="-")
                self.target_lbl.config(text="--% – --%")
                # Clear graph data
                self.graph_timestamps = []
                self.graph_moisture_data = []
                self._update_graph(None)
                # Clear current moisture value display
                self.current_lbl.config(text="--")
                self.status_lbl.config(text="No field selected")
                # Select first field if available
                if items:
                    self.field_combo.current(0)
                    self._on_field_selected(None)
            else:
                # Field still exists, keep selection but refresh data
                # Find the index of current field in new list
                try:
                    idx = items.index(current_selection)
                    self.field_combo.current(idx)
                    # Refresh historical data
                    self._load_historical_moisture_data()
                except ValueError:
                    # Field name might have changed, select first
                    if items:
                        self.field_combo.current(0)
                        self._on_field_selected(None)
        else:
            # No current selection
            if items:
                self.field_combo.current(0)
                self._on_field_selected(None)
            else:
                self.field_var.set("")
                self.current_crop_lbl.config(text="-")
                self.target_lbl.config(text="--% – --%")
                # Clear graph data
                self.graph_timestamps = []
                self.graph_moisture_data = []
                self._update_graph(None)
                # Clear current moisture value display
                self.current_lbl.config(text="--")
                self.status_lbl.config(text="No field selected")

    def _target_for_crop(self, crop_name):
        # Try defaults first; if unknown crop, use a sane default
        if crop_name in DEFAULT_CROP_TARGETS:
            return DEFAULT_CROP_TARGETS[crop_name]
        # Remove emoji and try again
        crop_clean = crop_name.replace("🌾", "").replace("🌻", "").replace("🌿", "").replace("🌽", "").replace("☁", "").strip()
        if crop_clean in DEFAULT_CROP_TARGETS:
            return DEFAULT_CROP_TARGETS[crop_clean]
        # Heuristic defaults for unknown crops
        return (55, 70)

    def _update_targets(self, crop_name):
        low, high = self._target_for_crop(crop_name)
        self.target_lbl.config(text=f"{low}% – {high}%")
        self.current_crop_lbl.config(text=crop_name)
        # Update visual indicator
        self._draw_target_range(low, high)
    
    def _draw_target_range(self, low, high):
        """Draw a modern visual indicator for target moisture range"""
        self.target_indicator.delete("all")
        canvas = self.target_indicator
        width = 120
        height = 20
        
        # Draw background gradient (dry to wet)
        for i in range(width):
            # Color gradient from red (dry) to green (wet)
            ratio = i / width
            if ratio < 0.3:
                r, g, b = 255, int(100 + ratio * 155 / 0.3), 100
            elif ratio < 0.7:
                r, g, b = int(255 - (ratio - 0.3) * 255 / 0.4), 255, 100
            else:
                r, g, b = 100, 255, int(100 + (ratio - 0.7) * 155 / 0.3)
            color = f"#{r:02x}{g:02x}{b:02x}"
            canvas.create_line(i, 0, i, height, fill=color, width=1)
        
        # Draw target range zone
        low_x = int((low / 100) * width)
        high_x = int((high / 100) * width)
        # Highlight target range with a semi-transparent overlay
        canvas.create_rectangle(low_x, 2, high_x, height-2, 
                              fill='#4CAF50', outline='#2E7D32', width=2, stipple='gray25')
        # Add range markers
        canvas.create_line(low_x, 0, low_x, height, fill='#2E7D32', width=2)
        canvas.create_line(high_x, 0, high_x, height, fill='#2E7D32', width=2)
        # Add labels
        canvas.create_text(low_x, height+2, text=f"{low}%", 
                          font=("Segoe UI", 7), fill='#2E7D32', anchor='n')
        canvas.create_text(high_x, height+2, text=f"{high}%", 
                          font=("Segoe UI", 7), fill='#2E7D32', anchor='n')

    def _on_field_selected(self, event):
        sel = self.field_var.get() or (self.field_combo["values"][0] if self.field_combo["values"] else "")
        if not sel:
            self.current_crop_lbl.config(text="-")
            self.target_lbl.config(text="--% – --%")
            return
        try:
            field_id = sel.split(" - ")[0]
            field = self.db.get_field(field_id)
            crop_name = field[3] if field and len(field) > 3 and field[3] else "Wheat"
        except Exception:
            crop_name = "Wheat"
        self._update_targets(crop_name)
        # Load historical data for graph
        self._load_historical_moisture_data()

    # ------------- Control -------------

    def on_moisture_received(self, nem_deger):
        """Callback when moisture data is received from Arduino."""
        self.last_nem_degeri = nem_deger
    
    def on_pump_status_changed(self, pump_on):
        """Callback when pump status changes."""
        self.pump_on = pump_on
        self._render_pump()
    
    def on_mode_changed(self, auto_mode):
        """Callback when Arduino mode changes."""
        self.arduino_auto_mode = auto_mode
    
    def _on_mode_changed(self):
        """Handle mode change (Automatic/Manual)."""
        mode = self.mode_var.get()
        self.auto_mode = (mode == "Automatic")
        
        # Send mode command to Arduino
        if self.arduino_connection and self.arduino_connection.is_connected():
            try:
                if self.auto_mode:
                    # Send 'O' for Otomatik (Automatic) mode
                    self.arduino_connection.write_command(b'O')
                    self.arduino_auto_mode = True
                else:
                    # Send 'M' for Manuel (Manual) mode
                    self.arduino_connection.write_command(b'M')
                    self.arduino_auto_mode = False
            except Exception as e:
                print(f"Error sending mode command to Arduino: {e}")
        
        if self.auto_mode:
            # Automatic mode: Enable pump status, disable manual buttons
            self._enable_pump_status(True)
            self._enable_manual_controls(False)
            # Turn off pump if it was manually controlled
            if self.manual_override:
                self._turn_pump_off("auto")
                self.manual_override = False
                if self.manual_timer_id:
                    self.parent.after_cancel(self.manual_timer_id)
                    self.manual_timer_id = None
        else:
            # Manual mode: Enable pump status (always visible), enable manual buttons
            self._enable_pump_status(True)
            self._enable_manual_controls(True)
            # Turn off pump if it was auto controlled
            if self.pump_on and not self.manual_override:
                self._turn_pump_off("manual")
    
    def _enable_pump_status(self, enable):
        """Enable or disable pump status display."""
        # Pump status is always visible now (both in auto and manual mode)
        # Just re-render it
        self._render_pump()
    
    def _enable_manual_controls(self, enable):
        """Enable or disable manual control buttons."""
        state = "normal" if enable else "disabled"
        self.btn_start.config(state=state)
        self.btn_stop.config(state=state)
        if enable:
            self.manual_help_label.config(text="Manual controls for manual mode.", foreground="#555")
        else:
            self.manual_help_label.config(text="Manual controls disabled in automatic mode.", foreground="#999")

    def read_soil_moisture(self):
        """Read soil moisture from Arduino (real-time only)."""
        # Only read from Arduino if connected and has data
        if self.arduino_connection and self.arduino_connection.is_connected() and self.last_nem_degeri > 0:
            # Convert raw sensor value (0-1023) to percentage
            raw = max(self.sensor_min, min(self.sensor_max, self.last_nem_degeri))
            moisture = (self.sensor_max - raw) / (self.sensor_max - self.sensor_min) * 100.0
            moisture = max(0, min(100, moisture))
            
            # Update graph data
            now = datetime.now()
            if not self.graph_timestamps or (now - self.graph_timestamps[-1]).total_seconds() > 5:
                self.graph_timestamps.append(now)
                self.graph_moisture_data.append(moisture)
                # Keep only last 1000 points
                if len(self.graph_timestamps) > 1000:
                    self.graph_timestamps.pop(0)
                    self.graph_moisture_data.pop(0)
                self._update_graph(None)
            
            return moisture
        
        # Fallback to database (only historical data, no simulation)
        sel = self.field_var.get() or (self.field_combo["values"][0] if self.field_combo["values"] else "")
        if sel:
            try:
                field_id = sel.split(" - ")[0]
                latest_data = self.db.get_latest_soil_data(field_id)
                if latest_data and latest_data[3]:  # moisture value exists
                    # Update graph data
                    if latest_data[2]:  # timestamp exists
                        try:
                            timestamp = datetime.fromisoformat(latest_data[2])
                            # Only add if it's a new reading (not duplicate)
                            if not self.graph_timestamps or self.graph_timestamps[-1] != timestamp:
                                self.graph_timestamps.append(timestamp)
                                self.graph_moisture_data.append(latest_data[3])
                                # Keep only last 1000 points
                                if len(self.graph_timestamps) > 1000:
                                    self.graph_timestamps.pop(0)
                                    self.graph_moisture_data.pop(0)
                                self._update_graph(None)
                        except Exception:
                            pass
                    return latest_data[3]
            except Exception as e:
                print(f"Error reading from database: {e}")
        
        # No data available - return None (no simulation)
        return None

    def activate_water_pump(self):
        """Activate water pump via Arduino."""
        if self.arduino_connection and self.arduino_connection.is_connected():
            try:
                # Send 'A' command to Arduino (Aç - Open)
                if self.arduino_connection.write_command(b'A'):
                    self.pump_on = True
                    return True
            except Exception as e:
                print(f"Error activating pump: {e}")
                return False
        return False

    def deactivate_water_pump(self):
        """Deactivate water pump via Arduino."""
        if self.arduino_connection and self.arduino_connection.is_connected():
            try:
                # Send 'K' command to Arduino (Kapat - Close)
                if self.arduino_connection.write_command(b'K'):
                    self.pump_on = False
                    return True
            except Exception as e:
                print(f"Error deactivating pump: {e}")
                return False
        return False

    def _render_pump(self):
        """Render pump status indicator."""
        self.pump_indicator.delete("all")
        
        # Pompa açıkken yeşil, kapalıyken kırmızı
        if self.pump_on:
            color = "#22c55e"  # Yeşil
            text = "ON"
            text_color = "#22c55e"  # Yeşil yazı rengi
        else:
            color = "#ef4444"  # Kırmızı
            text = "OFF"
            text_color = "#ef4444"  # Kırmızı yazı rengi
        
        self.pump_indicator.create_oval(1, 1, 15, 15, fill=color, outline="")
        self.pump_label.config(text=text, foreground=text_color, font=("Segoe UI", 10, "bold"))

    def _manual_start(self):
        self.manual_override = True
        if self.manual_timer_id:
            self.parent.after_cancel(self.manual_timer_id)
        self._turn_pump_on(reason="manual")
        self.manual_timer_id = self.parent.after(30000, self._manual_expire)

    def _manual_stop(self):
        self.manual_override = True
        if self.manual_timer_id:
            self.parent.after_cancel(self.manual_timer_id)
        self._turn_pump_off(reason="manual")
        self.manual_timer_id = self.parent.after(30000, self._manual_expire)

    def _manual_expire(self):
        self.manual_override = False
        self.manual_timer_id = None

    def _turn_pump_on(self, reason="auto"):
        """Turn pump on."""
        if not self.pump_on:
            success = self.activate_water_pump()
            if success:
                self.pump_on = True
                self._render_pump()

    def _turn_pump_off(self, reason="auto"):
        """Turn pump off."""
        if self.pump_on:
            success = self.deactivate_water_pump()
            if success:
                self.pump_on = False
                self._render_pump()

    def _tick(self):
        if not self.running:
            return
        value = self.read_soil_moisture()
        
        # Update connection status
        if self.arduino_connection and self.arduino_connection.is_connected():
            self.connection_status_lbl.config(text="● Arduino: Connected (COM5)", foreground="green")
        else:
            self.connection_status_lbl.config(text="● Arduino: Disconnected", foreground="red")
        
        # Check if reading is valid
        if value is None:
            # No data available - Arduino not connected or no sensor data
            self.current_lbl.config(text="--")
            if not self.arduino_connection or not self.arduino_connection.is_connected():
                self.status_lbl.config(text="⚠ Arduino not connected - Connect to COM5")
            elif self.last_nem_degeri == 0:
                self.status_lbl.config(text="⚠ Waiting for sensor data from Arduino...")
            else:
                self.status_lbl.config(text="⚠ No data available")
            self._render_pump()
            self.parent.after(2000, self._tick)
            return
        
        self.last_value = value
        self.current_lbl.config(text=f"{value:.1f}%")

        sel = self.field_var.get() or (self.field_combo["values"][0] if self.field_combo["values"] else "")
        if not sel:
            # No field selected, show waiting status
            self.status_lbl.config(text="No field selected")
            self._render_pump()
            # Schedule next sample (~2s)
            self.parent.after(2000, self._tick)
            return
        
        crop = "Wheat"
        try:
            field_id = sel.split(" - ")[0]
            field = self.db.get_field(field_id)
            if field and len(field) > 3 and field[3]:
                crop = field[3]
        except Exception:
            crop = "Wheat"
        
        low, high = self._target_for_crop(crop)

        # Status + control decisions
        if not self.auto_mode:
            # Manual mode - user controls via buttons
            if self.pump_on:
                self.status_lbl.config(text="Manual Mode — Pump ON")
            else:
                self.status_lbl.config(text="Manual Mode — Pump OFF")
        else:
            # Automatic mode - control pump based on target range with hysteresis
            # Use hysteresis to prevent rapid on/off cycling
            low_threshold = low - self.hysteresis  # Turn ON when below this
            high_threshold = high + self.hysteresis  # Turn OFF when above this
            
            if value < low_threshold:
                # Too dry - turn pump ON
                self.status_lbl.config(text=f"⚠ Too Dry ({value:.1f}% < {low}%) — Starting Irrigation")
                if not self.pump_on and not self.manual_override:
                    self._turn_pump_on("auto")
            elif value > high_threshold:
                # Too wet - turn pump OFF
                self.status_lbl.config(text=f"⚠ Too Wet ({value:.1f}% > {high}%) — Stopping Irrigation")
                if self.pump_on and not self.manual_override:
                    self._turn_pump_off("auto")
            elif value < low:
                # Below target - turn pump ON if not already on
                self.status_lbl.config(text=f"⚠ Below Target ({value:.1f}% < {low}%) — Irrigation Active")
                if not self.pump_on and not self.manual_override:
                    self._turn_pump_on("auto")
            elif value > high:
                # Above target - turn pump OFF if currently on
                self.status_lbl.config(text=f"⚠ Above Target ({value:.1f}% > {high}%) — Irrigation Stopped")
                if self.pump_on and not self.manual_override:
                    self._turn_pump_off("auto")
            else:
                # Optimal range - maintain current state, but turn off if well within range
                self.status_lbl.config(text=f"✓ Optimal Moisture ({value:.1f}% in {low}%-{high}% range)")
                # If pump is on and we're in the middle of optimal range, turn it off
                optimal_mid = (low + high) / 2
                if self.pump_on and value > optimal_mid and not self.manual_override:
                    self._turn_pump_off("auto")

        # Keep updating the pump indicator
        self._render_pump()
        
        # Schedule next sample (~2s)
        self.parent.after(2000, self._tick)

    def _load_historical_moisture_data(self):
        """Load historical soil moisture data from database for the selected field."""
        sel = self.field_var.get() or (self.field_combo["values"][0] if self.field_combo["values"] else "")
        if not sel:
            self.graph_timestamps = []
            self.graph_moisture_data = []
            self._update_graph(None)
            return
        
        try:
            field_id = sel.split(" - ")[0]
            # Load last 1000 records
            data = self.db.get_soil_data(field_id, limit=1000)
            
            self.graph_timestamps = []
            self.graph_moisture_data = []
            
            if data:
                # Parse database records: (id, field_id, timestamp, moisture, temperature, air_humidity)
                for record in data:  # Already ordered DESC, but we want chronological
                    try:
                        if record[2] and record[3]:  # timestamp and moisture exist
                            timestamp = datetime.fromisoformat(record[2])
                            self.graph_timestamps.append(timestamp)
                            self.graph_moisture_data.append(record[3])
                    except Exception as e:
                        print(f"Error parsing historical record: {e}")
                
                # Sort by timestamp (oldest to newest)
                if self.graph_timestamps:
                    sorted_data = sorted(zip(self.graph_timestamps, self.graph_moisture_data))
                    self.graph_timestamps = [t for t, _ in sorted_data]
                    self.graph_moisture_data = [m for _, m in sorted_data]
            
            self._update_graph(None)
        except Exception as e:
            print(f"Error loading historical data: {e}")
            self.graph_timestamps = []
            self.graph_moisture_data = []

    def _update_graph(self, event):
        """Update the soil moisture graph."""
        if not self.graph_timestamps or not self.graph_moisture_data:
            self.ax.clear()
            self.ax.text(0.5, 0.5, 'No data available', 
                       horizontalalignment='center', verticalalignment='center',
                       transform=self.ax.transAxes, fontsize=12)
            self.ax.set_xlabel('Time')
            self.ax.set_ylabel('Soil Moisture (%)')
            self.ax.set_title('Historical Soil Moisture')
            self.canvas_widget.draw()
            return

        time_range = self.time_var.get()
        now = datetime.now()

        if time_range == "Last 1 Hour":
            start_time = now - timedelta(hours=1)
        elif time_range == "Last 6 Hours":
            start_time = now - timedelta(hours=6)
        elif time_range == "Last 24 Hours":
            start_time = now - timedelta(hours=24)
        else:  # Last 7 Days
            start_time = now - timedelta(days=7)

        # Filter data by time range
        valid_indices = [i for i, t in enumerate(self.graph_timestamps) if t >= start_time]

        if not valid_indices:
            self.ax.clear()
            self.ax.text(0.5, 0.5, 'No data in selected time range', 
                       horizontalalignment='center', verticalalignment='center',
                       transform=self.ax.transAxes, fontsize=12)
            self.ax.set_xlabel('Time')
            self.ax.set_ylabel('Soil Moisture (%)')
            self.ax.set_title('Historical Soil Moisture')
            self.canvas_widget.draw()
            return

        filtered_times = [self.graph_timestamps[i] for i in valid_indices]
        filtered_moisture = [self.graph_moisture_data[i] for i in valid_indices]

        # Clear and plot
        self.ax.clear()
        self.ax.plot(filtered_times, filtered_moisture, 'b-', linewidth=2, label='Soil Moisture')
        self.ax.set_xlabel('Time')
        self.ax.set_ylabel('Soil Moisture (%)')
        self.ax.set_title('Historical Soil Moisture')
        self.ax.grid(True, alpha=0.3)
        self.ax.legend()
        
        # Format x-axis
        self.ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%H:%M' if time_range in ["Last 1 Hour", "Last 6 Hours"] else '%m/%d %H:%M'))
        plt.setp(self.ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        self.fig.tight_layout()
        self.canvas_widget.draw()
    
    
    def cleanup(self):
        """Cleanup resources."""
        self.running = False
        
        # Unregister callbacks
        if self.arduino_connection:
            self.arduino_connection.unregister_moisture_callback(self.on_moisture_received)
            self.arduino_connection.unregister_pump_callback(self.on_pump_status_changed)
            self.arduino_connection.unregister_mode_callback(self.on_mode_changed)


