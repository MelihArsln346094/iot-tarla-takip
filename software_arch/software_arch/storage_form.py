import tkinter as tk
from tkinter import ttk, messagebox

class StorageForm:
    def __init__(self, parent, map_widget, db, on_save_callback=None):
        self.parent = parent
        self.map_widget = map_widget
        self.db = db
        self.on_save_callback = on_save_callback
        self.editing_storage_id = None
        self.lat = None
        self.lon = None
        self.current_marker = None

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
        header_frame = tk.Frame(scrollable_frame, bg='#1565C0', height=80)
        header_frame.pack(fill=tk.X)
        header_label = tk.Label(header_frame, text="📦 Add New Warehouse", 
                               font=("Segoe UI", 20, "bold"), bg='#1565C0', fg='white')
        header_label.pack(pady=20)
        
        # Main content frame with padding
        content_frame = tk.Frame(scrollable_frame, bg='#F5F5F5')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Card 1: Basic Information
        card1 = tk.Frame(content_frame, bg='white', relief=tk.FLAT, bd=0)
        card1.pack(fill=tk.X, pady=(0, 15))
        self._add_shadow(card1)
        
        card1_header = tk.Frame(card1, bg='#E3F2FD', height=50)
        card1_header.pack(fill=tk.X)
        tk.Label(card1_header, text="📝 Basic Information", font=("Segoe UI", 14, "bold"),
                bg='#E3F2FD', fg='#1565C0').pack(anchor='w', padx=20, pady=12)
        
        card1_content = tk.Frame(card1, bg='white')
        card1_content.pack(fill=tk.X, padx=20, pady=20)
        
        self._create_input_field(card1_content, "Warehouse Name:", "entry_storage_name")
        self._create_combo_field(card1_content, "Seed Type:", "entry_seed_type",
                                ["🌾 Wheat", "🌻 Sunflower", "🌿 Barley", "🌽 Corn", "☁ Cotton", "Other"])
        
        # Card 2: Stock Information
        card2 = tk.Frame(content_frame, bg='white', relief=tk.FLAT, bd=0)
        card2.pack(fill=tk.X, pady=(0, 15))
        self._add_shadow(card2)
        
        card2_header = tk.Frame(card2, bg='#FFF3E0', height=50)
        card2_header.pack(fill=tk.X)
        tk.Label(card2_header, text="📊 Stock Information", font=("Segoe UI", 14, "bold"),
                bg='#FFF3E0', fg='#F57C00').pack(anchor='w', padx=20, pady=12)
        
        card2_content = tk.Frame(card2, bg='white')
        card2_content.pack(fill=tk.X, padx=20, pady=20)
        
        self._create_input_field(card2_content, "Seed Quantity (Tonne):", "entry_seed_amount")
        self._create_input_field(card2_content, "Fertilizer Amount (Tonne):", "entry_fertilizer_amount")
        self._create_input_field(card2_content, "Liquid Fertilizer Amount (Liter):", "entry_pesticide_amount")
        
        # Card 3: Location
        card3 = tk.Frame(content_frame, bg='white', relief=tk.FLAT, bd=0)
        card3.pack(fill=tk.X, pady=(0, 15))
        self._add_shadow(card3)
        
        card3_header = tk.Frame(card3, bg='#E8F5E9', height=50)
        card3_header.pack(fill=tk.X)
        tk.Label(card3_header, text="📍 Location", font=("Segoe UI", 14, "bold"),
                bg='#E8F5E9', fg='#2E7D32').pack(anchor='w', padx=20, pady=12)
        
        card3_content = tk.Frame(card3, bg='white')
        card3_content.pack(fill=tk.X, padx=20, pady=20)
        
        self.location_label = tk.Label(card3_content, text="📍 No location selected", 
                                       font=("Segoe UI", 12), bg='#FAFAFA', fg='#757575',
                                       relief=tk.SOLID, borderwidth=1, pady=15)
        self.location_label.pack(fill=tk.X, pady=10)
        
        location_btn = tk.Button(card3_content, text="📍 Select Location from Map",
                                command=self.show_map_selection_info,
                                bg='#4CAF50', fg='white', font=("Segoe UI", 11, "bold"),
                                relief=tk.FLAT, padx=20, pady=10, cursor="hand2")
        location_btn.pack(pady=10)
        
        # Save and Cancel Buttons
        save_frame = tk.Frame(content_frame, bg='#F5F5F5')
        save_frame.pack(fill=tk.X, pady=20)
        
        button_container = tk.Frame(save_frame, bg='#F5F5F5')
        button_container.pack()
        
        self.cancel_button = tk.Button(button_container, text="❌ İPTAL", command=self.cancel_form,
                                       bg='#757575', fg='white', font=("Segoe UI", 12, "bold"),
                                       relief=tk.FLAT, padx=30, pady=12, cursor="hand2")
        self.cancel_button.pack(side=tk.LEFT, padx=5)
        
        self.save_button = tk.Button(button_container, text="💾 SAVE WAREHOUSE", command=self.save_storage,
                                     bg='#2196F3', fg='white', font=("Segoe UI", 14, "bold"),
                                     relief=tk.FLAT, padx=40, pady=15, cursor="hand2")
        self.save_button.pack(side=tk.LEFT, padx=5)
    
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

    def show_map_selection_info(self):
        messagebox.showinfo("Location Selection",
                           "Right-click on the desired location on the map and use the 'Add Warehouse' option.")

    def set_location(self, lat, lon):
        self.lat = lat
        self.lon = lon
        self.location_label.config(text=f"📍 Location: {lat:.6f}, {lon:.6f}", 
                                  bg='#E8F5E9', fg='#2E7D32')

        if self.current_marker:
            self.current_marker.delete()

        name = self.entry_storage_name.get().strip() or "New Warehouse"
        self.current_marker = self.map_widget.set_marker(lat, lon, text=name)

    def load_storage_for_edit(self, storage_id):
        storage = self.db.get_storage(storage_id)

        if storage:
            self.editing_storage_id = storage_id

            self.entry_storage_name.delete(0, tk.END)
            self.entry_storage_name.insert(0, storage[1])

            self.entry_seed_type.delete(0, tk.END)
            self.entry_seed_type.insert(0, storage[2])

            self.entry_seed_amount.delete(0, tk.END)
            self.entry_seed_amount.insert(0, storage[3])

            self.entry_fertilizer_amount.delete(0, tk.END)
            self.entry_fertilizer_amount.insert(0, storage[4])

            self.entry_pesticide_amount.delete(0, tk.END)
            self.entry_pesticide_amount.insert(0, storage[5])

            self.lat = storage[6]
            self.lon = storage[7]

            if self.lat and self.lon:
                self.location_label.config(text=f"📍 Location: {self.lat:.6f}, {self.lon:.6f}",
                                          bg='#E8F5E9', fg='#2E7D32')

                if self.current_marker:
                    self.current_marker.delete()

            self.save_button.config(text="💾 UPDATE WAREHOUSE", command=self.update_storage)

    def save_storage(self):
        try:
            name = self.entry_storage_name.get()
            seed_type = self.entry_seed_type.get()

            try:
                seed_amount = float(self.entry_seed_amount.get())
                fertilizer_amount = float(self.entry_fertilizer_amount.get())
                pesticide_amount = float(self.entry_pesticide_amount.get())
            except ValueError:
                messagebox.showerror("Invalid Entry", "Please enter valid numeric values.")
                return

            if self.lat is None or self.lon is None:
                messagebox.showwarning("Warning", "Please select a location from the map.")
                return

            storage_data = (name, seed_type, seed_amount, fertilizer_amount,
                            pesticide_amount, self.lat, self.lon)

            result = self.db.save_storage(storage_data)

            if result is not None:
                messagebox.showinfo("Success", "Warehouse saved successfully!")
                self.clear_form()

                if self.on_save_callback:
                    self.on_save_callback()
            else:
                messagebox.showerror("Error", "Failed to save warehouse.")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred:\n{e}")
            print(f"Error details: {e}")
            
    def update_storage(self):
        try:
            name = self.entry_storage_name.get()
            seed_type = self.entry_seed_type.get()
            seed_amount = float(self.entry_seed_amount.get())
            fertilizer_amount = float(self.entry_fertilizer_amount.get())
            pesticide_amount = float(self.entry_pesticide_amount.get())

            storage_data = (name, seed_type, seed_amount, fertilizer_amount,
                           pesticide_amount, self.lat, self.lon)

            self.db.update_storage(storage_data, self.editing_storage_id)

            messagebox.showinfo("Success", "Warehouse updated successfully!")
            self.clear_form()

            if self.on_save_callback:
                self.on_save_callback()

            self.save_button.config(text="💾 SAVE WAREHOUSE", command=self.save_storage)
            self.editing_storage_id = None

        except ValueError:
            messagebox.showerror("Invalid Entry", "Please enter valid numeric values.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during update:\n{e}")

    def cancel_form(self):
        """Cancel form entry - clears form and removes marker"""
        if self.lat is not None or self.lon is not None or self.current_marker is not None:
            result = messagebox.askyesno(
                "İptal Et",
                "Kaydetmeden çıkmak istediğinizden emin misiniz?\nTüm girilen bilgiler silinecek.",
                icon='question'
            )
            if result:
                self.clear_form()
                messagebox.showinfo("İptal Edildi", "İşlem iptal edildi.")
        else:
            self.clear_form()

    def clear_form(self):
        self.entry_storage_name.delete(0, tk.END)
        self.entry_seed_type.set('')
        self.entry_seed_amount.delete(0, tk.END)
        self.entry_fertilizer_amount.delete(0, tk.END)
        self.entry_pesticide_amount.delete(0, tk.END)
        self.location_label.config(text="📍 No location selected", bg='#FAFAFA', fg='#757575')
        self.lat = None
        self.lon = None

        if self.current_marker:
            self.current_marker.delete()
            self.current_marker = None
        
        # Reset save button text and command if it was in edit mode
        self.save_button.config(text="💾 SAVE WAREHOUSE", command=self.save_storage)
        self.editing_storage_id = None
