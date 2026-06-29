import tkinter as tk
from tkinter import ttk, messagebox
from tkintermapview import TkinterMapView

class StorageView:
    def __init__(self, parent, map_widget, db, on_edit_callback=None, on_delete_callback=None):
        self.parent = parent
        self.map_widget = map_widget
        self.db = db
        self.on_edit_callback = on_edit_callback
        self.on_delete_callback = on_delete_callback
        self.storage_markers = {}  # {id: marker}
        self.storage_cards = {}  # Store card widgets: {storage_id: card_frame}
        self.selected_storage_id = None

        self.map_widget.add_right_click_menu_command(
            label="🏭 Add Warehouse",
            command=self.on_map_right_click_storage,
            pass_coords=True
        )

        self.build_view()

    def build_view(self):
        # Header frame with refresh button
        header_frame = tk.Frame(self.parent, bg='#ECEFF1')
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        title_label = tk.Label(
            header_frame,
            text="🏭 My Warehouses",
            font=("Segoe UI", 16, "bold"),
            bg='#ECEFF1',
            fg='#1565C0'
        )
        title_label.pack(side=tk.LEFT)
        
        refresh_btn = tk.Button(
            header_frame,
            text="🔄 Refresh",
            font=("Segoe UI", 9),
            bg='#1565C0',
            fg='white',
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor="hand2",
            command=self.load_all_storages
        )
        refresh_btn.pack(side=tk.RIGHT)
        refresh_btn.bind("<Enter>", lambda e: refresh_btn.config(bg='#0D47A1'))
        refresh_btn.bind("<Leave>", lambda e: refresh_btn.config(bg='#1565C0'))

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
            text="No warehouses found.\nAdd a new one from the '🏭 ADD WAREHOUSE' tab.",
            font=("Segoe UI", 11),
            bg='#ECEFF1',
            fg='#757575',
            justify="center"
        )

    def create_storage_card(self, storage_data):
        """Create a modern card widget for a warehouse"""
        storage_id, name, lat, lon = storage_data
        
        # Get full storage details
        full_storage = self.db.get_storage(storage_id)
        if not full_storage:
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
        
        # Header section with warehouse name and seed type
        header_frame = tk.Frame(content_frame, bg='white')
        header_frame.pack(fill=tk.X, pady=(0, 12))
        
        # Warehouse icon and name
        name_frame = tk.Frame(header_frame, bg='white')
        name_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        warehouse_icon = tk.Label(
            name_frame,
            text="🏭",
            font=("Segoe UI", 20),
            bg='white'
        )
        warehouse_icon.pack(side=tk.LEFT, padx=(0, 10))
        
        name_label = tk.Label(
            name_frame,
            text=name or "Unnamed Warehouse",
            font=("Segoe UI", 14, "bold"),
            bg='white',
            fg='#212121',
            anchor="w"
        )
        name_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Seed type badge
        seed_type = full_storage[2] if full_storage and len(full_storage) > 2 else "N/A"
        seed_badge = tk.Label(
            header_frame,
            text=seed_type,
            font=("Segoe UI", 9, "bold"),
            bg='#E3F2FD',
            fg='#1565C0',
            padx=12,
            pady=4,
            relief=tk.FLAT
        )
        seed_badge.pack(side=tk.RIGHT)
        
        # Information grid
        info_frame = tk.Frame(content_frame, bg='white')
        info_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Seed Quantity
        if full_storage and len(full_storage) > 3 and full_storage[3]:
            seed_frame = tk.Frame(info_frame, bg='#F5F5F5', relief=tk.FLAT)
            seed_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
            
            tk.Label(
                seed_frame,
                text="🌱 Seed Quantity",
                font=("Segoe UI", 8),
                bg='#F5F5F5',
                fg='#757575'
            ).pack(anchor="w", padx=10, pady=(8, 2))
            
            tk.Label(
                seed_frame,
                text=f"{full_storage[3]} tonne",
                font=("Segoe UI", 11, "bold"),
                bg='#F5F5F5',
                fg='#212121'
            ).pack(anchor="w", padx=10, pady=(0, 8))
        
        # Fertilizer Amount
        if full_storage and len(full_storage) > 4 and full_storage[4]:
            fert_frame = tk.Frame(info_frame, bg='#F5F5F5', relief=tk.FLAT)
            fert_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
            
            tk.Label(
                fert_frame,
                text="💊 Fertilizer",
                font=("Segoe UI", 8),
                bg='#F5F5F5',
                fg='#757575'
            ).pack(anchor="w", padx=10, pady=(8, 2))
            
            tk.Label(
                fert_frame,
                text=f"{full_storage[4]} tonne",
                font=("Segoe UI", 11, "bold"),
                bg='#F5F5F5',
                fg='#212121'
            ).pack(anchor="w", padx=10, pady=(0, 8))
        
        # Liquid Fertilizer / Pesticide
        if full_storage and len(full_storage) > 5 and full_storage[5]:
            liquid_frame = tk.Frame(info_frame, bg='#F5F5F5', relief=tk.FLAT)
            liquid_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            tk.Label(
                liquid_frame,
                text="💧 Liquid Fertilizer",
                font=("Segoe UI", 8),
                bg='#F5F5F5',
                fg='#757575'
            ).pack(anchor="w", padx=10, pady=(8, 2))
            
            tk.Label(
                liquid_frame,
                text=f"{full_storage[5]} liter",
                font=("Segoe UI", 11, "bold"),
                bg='#F5F5F5',
                fg='#212121'
            ).pack(anchor="w", padx=10, pady=(0, 8))
        
        # Location
        if lat and lon:
            loc_frame = tk.Frame(info_frame, bg='#F5F5F5', relief=tk.FLAT)
            loc_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))
            
            tk.Label(
                loc_frame,
                text="📍 Location",
                font=("Segoe UI", 8),
                bg='#F5F5F5',
                fg='#757575'
            ).pack(anchor="w", padx=10, pady=(8, 2))
            
            location_text = f"{lat:.4f}, {lon:.4f}"
            tk.Label(
                loc_frame,
                text=location_text,
                font=("Segoe UI", 10),
                bg='#F5F5F5',
                fg='#212121'
            ).pack(anchor="w", padx=10, pady=(0, 8))
        
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
            lambda: self.edit_storage(storage_id)
        )
        
        create_action_button(
            "👁️ View Details",
            '#388E3C',
            '#2E7D32',
            lambda: self.view_storage(storage_id)
        )
        
        create_action_button(
            "🗑️ Delete",
            '#D32F2F',
            '#C62828',
            lambda: self.delete_storage(storage_id)
        )
        
        # Store card reference
        self.storage_cards[storage_id] = card_frame
        
        return card_frame

    def load_all_storages(self):
        # Clear existing cards
        for card_frame in self.storage_cards.values():
            card_frame.destroy()
        self.storage_cards = {}
        self.selected_storage_id = None

        # Clear map markers
        for marker in self.storage_markers.values():
            marker.delete()
        self.storage_markers = {}

        storages = self.db.get_all_storages()

        if not storages:
            # Show empty state
            if not self.empty_label.winfo_ismapped():
                self.empty_label.pack(pady=30)
        else:
            if self.empty_label.winfo_ismapped():
                self.empty_label.pack_forget()

            for storage in storages:
                # Create card
                self.create_storage_card(storage)
                
                # Add to map
                storage_id, name, lat, lon = storage
                if lat and lon:
                    marker = self.map_widget.set_marker(
                        lat, lon,
                        text=f"🏭 {name}"
                    )
                    self.storage_markers[storage_id] = marker
        
        # Update canvas scroll region
        self.canvas.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_map_right_click_storage(self, coords):

        lat, lon = coords
        if self.on_edit_callback:

            self.on_edit_callback(None, lat, lon)

    def edit_storage(self, storage_id):
        """Edit storage - called from card button"""
        for marker in self.storage_markers.values():
            marker.delete()
        self.storage_markers = {}
        if self.on_edit_callback:
            self.on_edit_callback(storage_id)

    def delete_storage(self, storage_id):
        """Delete storage - called from card button"""
        result = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete this warehouse?\nThis action cannot be undone.",
            icon='warning'
        )
        
        if result:
            delete_result = self.db.delete_storage(storage_id)
            
            if int(storage_id) in self.storage_markers:
                self.storage_markers[int(storage_id)].delete()
                del self.storage_markers[int(storage_id)]
            
            messagebox.showinfo("Successful", "The warehouse was deleted.")
            self.load_all_storages()
            
            if self.on_delete_callback:
                self.on_delete_callback()

    def view_storage(self, storage_id):
        """View storage details - called from card button"""
        storage = self.db.get_storage(storage_id)

        if storage:
            details = (
                f"Warehouse Name : {storage[1]}\n"
                f"Seed Type: {storage[2]}\n"
                f"Seed Quantity: {storage[3]} tonne\n"
                f"Fertilizer Amount: {storage[4]} tonne\n"
                f"Liquid Fertilizer Amount: {storage[5]} liter"
            )

            detail_window = tk.Toplevel(self.parent)
            detail_window.title("Warehouse Details")
            ttk.Label(detail_window, text=details, justify="left").pack(padx=10, pady=10)

            lat, lon = storage[6], storage[7]
            if lat and lon:
                self.map_widget.set_position(lat, lon)
