import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime, timedelta
import threading
import time


class SoilMonitor:
    def __init__(self, parent, db, weather_service=None, arduino_connection=None):
        self.parent = parent
        self.db = db
        self.weather_service = weather_service
        self.arduino_connection = arduino_connection
        self.monitoring_active = False
        self.monitoring_thread = None
        self.selected_field_id = None

        # Data storage
        self.timestamps = []
        self.moisture_data = []  # Soil humidity
        self.air_humidity_data = []  # Air humidity
        self.temperature_data = []
        
        # Current field info for temperature
        self.current_field = None
        
        # Current weather data (from API, doesn't require Arduino)
        self.current_temperature = None
        self.current_air_humidity = None
        
        # Sensor calibration values (from test code)
        self.sensor_min = 520      # en ıslak okuma
        self.sensor_max = 930      # en kuru okuma
        
        # Last read values
        self.last_nem_degeri = 0

        self.build_ui()
        
        # Register callback for moisture data
        if self.arduino_connection:
            self.arduino_connection.register_moisture_callback(self.on_moisture_received)

    def build_ui(self):

        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)


        control_frame = ttk.LabelFrame(main_frame, text="Soil Sensor Control")
        control_frame.pack(fill=tk.X, pady=5)


        ttk.Label(control_frame, text="Select Field:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.field_selector = ttk.Combobox(control_frame, width=30)
        self.field_selector.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.field_selector.bind("<<ComboboxSelected>>", self.on_field_selected)


        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=0, column=2, padx=5, pady=5)

        self.start_button = ttk.Button(button_frame, text="Start Tracking", command=self.start_monitoring)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(button_frame, text="Stop Tracking", command=self.stop_monitoring, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)


        values_frame = ttk.LabelFrame(main_frame, text="Instant Soil Values")
        values_frame.pack(fill=tk.X, pady=5)


        indicators_frame = ttk.Frame(values_frame)
        indicators_frame.pack(fill=tk.X, padx=10, pady=5)


        # Soil Humidity
        soil_humidity_frame = ttk.Frame(indicators_frame)
        soil_humidity_frame.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        ttk.Label(soil_humidity_frame, text="Soil Humidity (%)", font=("Arial", 10, "bold")).pack()
        self.moisture_value = ttk.Label(soil_humidity_frame, text="--", font=("Arial", 14))
        self.moisture_value.pack()
        
        # Status label for sensor validation messages
        self.status_lbl = ttk.Label(soil_humidity_frame, text="", font=("Arial", 9), foreground="gray")
        self.status_lbl.pack(anchor=tk.W, pady=(2, 0))

        # Air Humidity
        air_humidity_frame = ttk.Frame(indicators_frame)
        air_humidity_frame.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        ttk.Label(air_humidity_frame, text="Air Humidity (%)", font=("Arial", 10, "bold")).pack()
        self.air_humidity_value = ttk.Label(air_humidity_frame, text="--", font=("Arial", 14))
        self.air_humidity_value.pack()

        # Temperature
        temp_frame = ttk.Frame(indicators_frame)
        temp_frame.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        ttk.Label(temp_frame, text="Temperature (°C)", font=("Arial", 10, "bold")).pack()
        self.temp_value = ttk.Label(temp_frame, text="--", font=("Arial", 14))
        self.temp_value.pack()


        graph_frame = ttk.LabelFrame(main_frame, text="Soil Data Graph")
        graph_frame.pack(fill=tk.BOTH, expand=True, pady=5)


        self.fig, self.ax = plt.subplots(2, 1, figsize=(10, 6), dpi=80)
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)


        options_frame = ttk.Frame(graph_frame)
        options_frame.pack(fill=tk.X, pady=5)

        ttk.Label(options_frame, text="Graph 1:").pack(side=tk.LEFT, padx=5)

        self.graph_var1 = tk.StringVar(value="Soil Humidity")
        self.graph_var2 = tk.StringVar(value="Air Humidity")
        self.graph_var3 = tk.StringVar(value="Temperature")

        graph_options = ["Soil Humidity", "Air Humidity", "Temperature"]

        graph_selector1 = ttk.Combobox(options_frame, textvariable=self.graph_var1, values=graph_options, width=15)
        graph_selector1.pack(side=tk.LEFT, padx=5)
        graph_selector1.bind("<<ComboboxSelected>>", self.update_graph)

        ttk.Label(options_frame, text="Graph 2:").pack(side=tk.LEFT, padx=5)
        graph_selector2 = ttk.Combobox(options_frame, textvariable=self.graph_var2, values=graph_options, width=15)
        graph_selector2.pack(side=tk.LEFT, padx=5)
        graph_selector2.bind("<<ComboboxSelected>>", self.update_graph)


        ttk.Label(options_frame, text="Time Range:").pack(side=tk.LEFT, padx=5)
        self.time_var = tk.StringVar(value="Last 1 Hour")
        time_options = ["Last 10 Minutes", "Last 30 Minutes", "Last 1 Hour", "Last 6 Hour", "Last 24 Hour"]
        time_selector = ttk.Combobox(options_frame, textvariable=self.time_var, values=time_options, width=15)
        time_selector.pack(side=tk.LEFT, padx=5)
        time_selector.bind("<<ComboboxSelected>>", self.update_graph)


        self.load_fields()
    
    def on_moisture_received(self, nem_deger):
        """Callback when moisture data is received from Arduino."""
        self.last_nem_degeri = nem_deger
        
        # If monitoring is active, process the data
        if self.monitoring_active and self.selected_field_id:
            self.get_soil_data()

    def load_fields(self):
        """Load fields from database and update the selector. If current selection is deleted, clear it."""
        try:
            fields = self.db.get_all_fields()
            print(f"Number of fields loaded from database: {len(fields)}")

            if not fields:
                # No fields available - clear selection and data
                self.field_selector['values'] = []
                self.field_selector.set("")
                self.selected_field_id = None
                self.current_field = None
                # Stop monitoring if active
                if self.monitoring_active:
                    self.stop_monitoring()
                self.clear_data()
                return

            field_names = [f"{field[0]} - {field[1]}" for field in fields]
            self.field_selector['values'] = field_names

            print(f"Values loaded into the Combobox: {field_names}")

            # Check if currently selected field still exists
            current_selection = self.field_selector.get()
            if current_selection:
                current_field_id = current_selection.split(" - ")[0]
                # Check if this field still exists in the new list
                field_ids = [f"{field[0]}" for field in fields]
                if current_field_id not in field_ids:
                    # Selected field was deleted - clear selection and data
                    self.field_selector.set("")
                    self.selected_field_id = None
                    self.current_field = None
                    # Stop monitoring if active
                    if self.monitoring_active:
                        self.stop_monitoring()
                    self.clear_data()
                    # Select first field if available
                    if field_names:
                        self.field_selector.current(0)
                        self.on_field_selected(None)
                else:
                    # Field still exists, keep selection but refresh data
                    # Find the index of current field in new list
                    try:
                        idx = field_names.index(current_selection)
                        self.field_selector.current(idx)
                    except ValueError:
                        # Field name might have changed, select first
                        if field_names:
                            self.field_selector.current(0)
                            self.on_field_selected(None)
            else:
                # No current selection, select first field if available
                if field_names:
                    self.field_selector.current(0)
                    self.on_field_selected(None)
        except Exception as e:
            print(f"Error loading fields: {e}")
            # On error, clear selection
            self.field_selector['values'] = []
            self.field_selector.set("")
            self.selected_field_id = None
            self.current_field = None
            # Stop monitoring if active
            if self.monitoring_active:
                self.stop_monitoring()
            self.clear_data()

    def on_field_selected(self, event):
        if self.field_selector.get():
            self.selected_field_id = self.field_selector.get().split(" - ")[0]
            try:
                self.current_field = self.db.get_field(self.selected_field_id)
            except Exception as e:
                print(f"Error loading field: {e}")
                self.current_field = None
            self.clear_data()
            
            # Load weather data from API (doesn't require Arduino)
            self.load_weather_data()
            
            # Load historical data from database
            self.load_historical_data()
            
            # Update UI to show weather data
            self.update_ui()

    def load_weather_data(self):
        """Load current weather data from API (doesn't require Arduino)."""
        if not self.weather_service or not self.selected_field_id:
            self.current_temperature = None
            self.current_air_humidity = None
            return
        
        try:
            field = self.db.get_field(self.selected_field_id)
            # Check if field has coordinates (latitude and longitude are at indices 12 and 13)
            if field and len(field) > 13:
                lat = field[12]  # latitude
                lon = field[13]  # longitude
                if lat is not None and lon is not None:
                    weather_data = self.weather_service.get_weather_by_coords(lat, lon)
                    if weather_data:
                        self.current_temperature = weather_data.get('temp', None)
                        self.current_air_humidity = weather_data.get('humidity', None)
                        print(f"Weather data loaded - Temp: {self.current_temperature}°C, Humidity: {self.current_air_humidity}%")
                    else:
                        print("Weather API returned no data")
                        self.current_temperature = None
                        self.current_air_humidity = None
                else:
                    print(f"Field {self.selected_field_id} has no coordinates (lat: {lat}, lon: {lon})")
                    self.current_temperature = None
                    self.current_air_humidity = None
            else:
                print(f"Field {self.selected_field_id} data incomplete or missing")
                self.current_temperature = None
                self.current_air_humidity = None
        except Exception as e:
            print(f"Error loading weather data from API: {e}")
            import traceback
            traceback.print_exc()
            self.current_temperature = None
            self.current_air_humidity = None
    
    def clear_data(self):
        self.timestamps = []
        self.moisture_data = []
        self.air_humidity_data = []
        self.temperature_data = []

        # Clear all displayed values
        self.moisture_value.config(text="--")
        self.air_humidity_value.config(text="--")
        self.temp_value.config(text="--")
        
        # Clear current weather data
        self.current_temperature = None
        self.current_air_humidity = None

        for a in self.ax:
            a.clear()
        self.canvas.draw()

    def start_monitoring(self):
        if not self.selected_field_id:
            tk.messagebox.showerror("Warning", "Please select a field first")
            return
        
        if not self.arduino_connection or not self.arduino_connection.is_connected():
            tk.messagebox.showerror("Warning", "Arduino connection not available. Please check COM5 connection.")
            return

        self.monitoring_active = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.field_selector.config(state=tk.DISABLED)

        # Start monitoring thread
        self.monitoring_thread = threading.Thread(target=self.monitor_soil_data)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()

    def stop_monitoring(self):
        self.monitoring_active = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.field_selector.config(state=tk.NORMAL)
    
    def cleanup(self):
        """Cleanup resources."""
        self.monitoring_active = False
        
        # Unregister callback
        if self.arduino_connection:
            self.arduino_connection.unregister_moisture_callback(self.on_moisture_received)
        

    def monitor_soil_data(self):
        """Monitor soil data from Arduino."""
        last_weather_update = 0
        weather_update_interval = 300  # Update weather every 5 minutes
        
        while self.monitoring_active:
            # Arduino'dan nem değeri otomatik olarak serial_oku thread'i tarafından okunuyor
            # Burada sadece UI'ı güncelle
            
            # Update weather data periodically (every 5 minutes)
            current_time = time.time()
            if current_time - last_weather_update >= weather_update_interval:
                self.load_weather_data()
                last_weather_update = current_time
            
            self.parent.after(0, self.update_ui)
            time.sleep(5)  # Check every 5 seconds
    
    def load_historical_data(self):
        """Load historical soil data from database for the selected field."""
        if not self.selected_field_id:
            return
        
        try:
            # Load last 100 records
            data = self.db.get_soil_data(self.selected_field_id, limit=100)
            
            if data:
                # Clear existing data
                self.timestamps = []
                self.moisture_data = []
                self.air_humidity_data = []
                self.temperature_data = []
                
                # Parse database records: (id, field_id, timestamp, moisture, temperature, air_humidity)
                # Handle old records that might have different structure
                for record in reversed(data):  # Reverse to get chronological order
                    try:
                        from datetime import datetime
                        timestamp = datetime.fromisoformat(record[2])
                        self.timestamps.append(timestamp)
                        self.moisture_data.append(record[3] or 0)
                        self.temperature_data.append(record[4] or 0)
                        # Check if air_humidity exists (new column)
                        if len(record) > 5:
                            self.air_humidity_data.append(record[5] or 0)
                        else:
                            self.air_humidity_data.append(0)
                    except Exception as e:
                        print(f"Error parsing historical record: {e}")
                
                # Update graph if we have data
                if self.timestamps:
                    self.update_graph(None)
        except Exception as e:
            print(f"Error loading historical data: {e}")


    def get_soil_data(self):
        """Get soil data from Arduino and weather API (real data only, no simulation)."""
        # Only process if Arduino is connected and has data
        if not self.arduino_connection or not self.arduino_connection.is_connected():
            return  # Don't process if Arduino not connected
        
        if self.last_nem_degeri <= 0:
            return  # Don't process if no sensor data
        
        now = datetime.now()
        self.timestamps.append(now)

        # Soil humidity (moisture) from Arduino
        # Convert raw sensor value (0-1023) to percentage
        raw_nem = self.last_nem_degeri
        # Kalibrasyon aralığına sıkıştır
        raw = max(self.sensor_min, min(self.sensor_max, raw_nem))
        # 0–1023 → %0–%100 ölçekleme
        moisture = (self.sensor_max - raw) / (self.sensor_max - self.sensor_min) * 100.0
        moisture = max(0, min(100, moisture))
        
        self.moisture_data.append(moisture)

        # Get temperature and air humidity from weather API if available
        temperature = None
        air_humidity = None
        if self.weather_service and self.selected_field_id:
            try:
                field = self.db.get_field(self.selected_field_id)
                # Check if field has coordinates (latitude and longitude are at indices 12 and 13)
                if field and len(field) > 13:
                    lat = field[12]  # latitude
                    lon = field[13]  # longitude
                    if lat is not None and lon is not None:
                        weather_data = self.weather_service.get_weather_by_coords(lat, lon)
                        if weather_data:
                            temperature = weather_data.get('temp', None)
                            air_humidity = weather_data.get('humidity', None)
                            print(f"Weather data retrieved - Temp: {temperature}°C, Humidity: {air_humidity}%")
                        else:
                            print("Weather API returned no data")
                    else:
                        print(f"Field {self.selected_field_id} has no coordinates (lat: {lat}, lon: {lon})")
                else:
                    print(f"Field {self.selected_field_id} data incomplete or missing")
            except Exception as e:
                print(f"Error getting weather data from API: {e}")
                import traceback
                traceback.print_exc()
        
        # Only use real weather data, no simulation
        if temperature is not None:
            self.temperature_data.append(temperature)
        else:
            self.temperature_data.append(None)  # No simulation, use None

        if air_humidity is not None:
            self.air_humidity_data.append(air_humidity)
        else:
            self.air_humidity_data.append(None)  # No simulation, use None
        
        # Save to database (only if we have moisture data from Arduino)
        try:
            self.db.save_soil_data(
                field_id=self.selected_field_id,
                moisture=moisture,
                temperature=self.temperature_data[-1] if self.temperature_data else None,
                air_humidity=self.air_humidity_data[-1] if self.air_humidity_data else None
            )
        except Exception as e:
            print(f"Error saving soil data to database: {e}")

    def update_ui(self):
        # Update moisture value (only if we have real data from Arduino)
        if self.moisture_data and len(self.moisture_data) > 0:
            self.moisture_value.config(text=f"{self.moisture_data[-1]:.1f}")
        else:
            self.moisture_value.config(text="--")
        
        # Update air humidity - show current weather data if available, otherwise show from historical data
        if self.air_humidity_data and len(self.air_humidity_data) > 0 and self.air_humidity_data[-1] is not None:
            self.air_humidity_value.config(text=f"{self.air_humidity_data[-1]:.1f}")
        elif self.current_air_humidity is not None:
            # Show current weather data from API (doesn't require Arduino)
            self.air_humidity_value.config(text=f"{self.current_air_humidity:.1f}")
        else:
            self.air_humidity_value.config(text="--")
        
        # Update temperature - show current weather data if available, otherwise show from historical data
        if self.temperature_data and len(self.temperature_data) > 0 and self.temperature_data[-1] is not None:
            self.temp_value.config(text=f"{self.temperature_data[-1]:.1f}")
        elif self.current_temperature is not None:
            # Show current weather data from API (doesn't require Arduino)
            self.temp_value.config(text=f"{self.current_temperature:.1f}")
        else:
            self.temp_value.config(text="--")
        
        # Update status label
        if self.arduino_connection and self.arduino_connection.is_connected():
            if self.last_nem_degeri > 0:
                self.status_lbl.config(text="✓ Sensor Connected - Data Available", foreground="green")
            else:
                self.status_lbl.config(text="⚠ Sensor Connected - Waiting for Data", foreground="orange")
        else:
            self.status_lbl.config(text="⚠ Sensor Disconnected - Connect Arduino to COM5", foreground="red")

        self.update_graph(None)

    def update_graph(self, event):
        if not self.timestamps:
            return

        time_range = self.time_var.get()
        now = datetime.now()

        if time_range == "Last 10 Minutes":
            start_time = now - timedelta(minutes=10)
        elif time_range == "Last 30 Minutes":
            start_time = now - timedelta(minutes=30)
        elif time_range == "Last 1 Hour":
            start_time = now - timedelta(hours=1)
        elif time_range == "Last 6 Hour":
            start_time = now - timedelta(hours=6)
        else:  # Last 24 Hour
            start_time = now - timedelta(hours=24)

        valid_indices = [i for i, t in enumerate(self.timestamps) if t >= start_time]

        if not valid_indices:
            return

        data_type1 = self.graph_var1.get()
        data1, times1 = self.get_data_by_type(data_type1, valid_indices)

        data_type2 = self.graph_var2.get()
        data2, times2 = self.get_data_by_type(data_type2, valid_indices)

        for a in self.ax:
            a.clear()

        if data1 and times1:
            self.ax[0].plot(times1, data1, 'b-', linewidth=2)
            self.ax[0].set_title(data_type1)
            self.ax[0].grid(True)
            self.ax[0].set_ylabel(self.get_y_label(data_type1))
            # Set appropriate y-axis limits based on data type
            if data1:
                y_min, y_max = min(data1), max(data1)
                y_range = y_max - y_min
                if y_range > 0:
                    self.ax[0].set_ylim(y_min - y_range * 0.1, y_max + y_range * 0.1)
                else:
                    self.ax[0].set_ylim(y_min - 1, y_max + 1)

        if data2 and times2:
            self.ax[1].plot(times2, data2, 'r-', linewidth=2)
            self.ax[1].set_title(data_type2)
            self.ax[1].grid(True)
            self.ax[1].set_ylabel(self.get_y_label(data_type2))
            # Set appropriate y-axis limits based on data type
            if data2:
                y_min, y_max = min(data2), max(data2)
                y_range = y_max - y_min
                if y_range > 0:
                    self.ax[1].set_ylim(y_min - y_range * 0.1, y_max + y_range * 0.1)
                else:
                    self.ax[1].set_ylim(y_min - 1, y_max + 1)

        for a in self.ax:
            a.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%H:%M'))

        self.fig.tight_layout()
        self.canvas.draw()

    def get_y_label(self, data_type):
        """Get appropriate y-axis label for data type."""
        if data_type == "Soil Humidity" or data_type == "Air Humidity":
            return "Humidity (%)"
        elif data_type == "Temperature":
            return "Temperature (°C)"
        return "Value"

    def get_data_by_type(self, data_type, indices):
        """Get data and corresponding timestamps for a specific data type.
        Returns (data_list, timestamps_list) where both lists have the same length
        and only include valid (non-None) data points."""
        data_list = []
        times_list = []
        
        for i in indices:
            # Ensure index is within bounds for all arrays
            if i >= len(self.timestamps):
                continue
                
            timestamp = self.timestamps[i]
            value = None
            
            if data_type == "Soil Humidity":
                if i < len(self.moisture_data):
                    value = self.moisture_data[i]
            elif data_type == "Air Humidity":
                if i < len(self.air_humidity_data):
                    value = self.air_humidity_data[i]
            elif data_type == "Temperature":
                if i < len(self.temperature_data):
                    value = self.temperature_data[i]
            
            # Only add valid (non-None) values to maintain data integrity
            if value is not None:
                data_list.append(value)
                times_list.append(timestamp)
        
        return data_list, times_list