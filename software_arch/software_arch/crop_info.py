import tkinter as tk
from tkinter import ttk

class CropInfoView:
    def __init__(self, parent):
        self.parent = parent
        self.active_popup = None
        self.build_view()

    def show_detailed_info(self, title, content):
        """Show detailed information in a popup window"""
        # Close previous popup if exists
        if self.active_popup:
            self.active_popup.destroy()
        
        # Create new popup
        popup = tk.Toplevel(self.parent)
        popup.title(f"📋 {title}")
        popup.geometry("700x500")
        popup.configure(bg='#FFFFFF')
        
        self.active_popup = popup
        
        # Make popup resizable
        popup.resizable(True, True)
        
        # Header
        header = tk.Frame(popup, bg='#2E7D32', height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(header, text=title, font=("Segoe UI", 16, "bold"),
                bg='#2E7D32', fg='white').pack(side=tk.LEFT, padx=20, pady=15)
        
        # Close button
        close_btn = tk.Button(header, text="✕", font=("Segoe UI", 14),
                             bg='#C62828', fg='white', relief=tk.FLAT,
                             command=popup.destroy, cursor="hand2", padx=10)
        close_btn.pack(side=tk.RIGHT, padx=10, pady=10)
        
        # Content
        content_frame = tk.Frame(popup, bg='#FFFFFF')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Text widget with scrollbar
        canvas = tk.Canvas(content_frame, bg='#FFFFFF', highlightthickness=0)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#FFFFFF')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Text widget for formatted content
        text_widget = tk.Text(scrollable_frame, wrap=tk.WORD, font=("Segoe UI", 11),
                             bg='#FFFFFF', fg='#333333', relief=tk.FLAT,
                             padx=20, pady=20, selectbackground='#81C784')
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        # Insert formatted content
        text_widget.insert(tk.END, content)
        text_widget.configure(state=tk.DISABLED)
        
        # Center popup on screen
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (popup.winfo_width() // 2)
        y = (popup.winfo_screenheight() // 2) - (popup.winfo_height() // 2)
        popup.geometry(f"+{x}+{y}")
        
        # Close popup when destroyed
        popup.protocol("WM_DELETE_WINDOW", lambda: setattr(self, 'active_popup', None) or popup.destroy())

    def create_icon_card(self, parent, icon, title, short_info, full_content):
        """Create an interactive icon card that opens detailed info"""
        card = tk.Frame(parent, bg='white', relief=tk.RAISED, bd=2, cursor="hand2")
        
        # Add hover effect
        def on_enter(e):
            card.configure(relief=tk.SOLID, bd=3, bg='#E8F5E9')
        
        def on_leave(e):
            card.configure(relief=tk.RAISED, bd=2, bg='white')
        
        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)
        
        # Icon
        icon_label = tk.Label(card, text=icon, font=("Segoe UI", 48),
                             bg='white', fg='#2E7D32', cursor="hand2")
        icon_label.pack(pady=(20, 10))
        
        # Title
        title_label = tk.Label(card, text=title, font=("Segoe UI", 12, "bold"),
                              bg='white', fg='#212121', cursor="hand2")
        title_label.pack(pady=(0, 8))
        
        # Short info
        info_label = tk.Label(card, text=short_info, font=("Segoe UI", 9),
                             bg='white', fg='#616161', cursor="hand2",
                             wraplength=250, justify='center')
        info_label.pack(pady=(0, 5))
        
        # Click indicator
        click_label = tk.Label(card, text="📖 Click for details", font=("Segoe UI", 8, "italic"),
                              bg='white', fg='#757575', cursor="hand2")
        click_label.pack(pady=(0, 15))
        
        # Bind click to all elements
        for widget in [card, icon_label, title_label, info_label, click_label]:
            widget.bind("<Button-1>", lambda e, t=title, c=full_content: self.show_detailed_info(t, c))
        
        return card

    def build_view(self):
        # Main container
        main_container = tk.Frame(self.parent, bg='#ECEFF1')
        main_container.pack(fill=tk.BOTH, expand=True)

        # Create notebook for different categories
        style = ttk.Style()
        style.configure('Modern.TNotebook.Tab', font=('Segoe UI', 10, 'bold'), padding=[20, 10])
        style.map('Modern.TNotebook.Tab',
                 background=[('selected', '#4CAF50'), ('!selected', '#E0E0E0')],
                 foreground=[('selected', 'white'), ('!selected', '#555555')])

        self.info_notebook = ttk.Notebook(main_container, style='Modern.TNotebook')
        self.info_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tab 1: Plant Diseases
        diseases_tab = tk.Frame(self.info_notebook, bg='#ECEFF1')
        self.info_notebook.add(diseases_tab, text="🦠 DISEASES")
        self.build_diseases_tab(diseases_tab)
        
        # Tab 2: Seeds
        seeds_tab = tk.Frame(self.info_notebook, bg='#ECEFF1')
        self.info_notebook.add(seeds_tab, text="🌱 SEEDS")
        self.build_seeds_tab(seeds_tab)
        
        # Tab 3: Greenhouse
        greenhouse_tab = tk.Frame(self.info_notebook, bg='#ECEFF1')
        self.info_notebook.add(greenhouse_tab, text="🏢 GREENHOUSE")
        self.build_greenhouse_tab(greenhouse_tab)
        
        # Tab 4: Fruit Growing
        fruit_tab = tk.Frame(self.info_notebook, bg='#ECEFF1')
        self.info_notebook.add(fruit_tab, text="🍎 FRUITS")
        self.build_fruit_tab(fruit_tab)
        
        # Tab 5: Irrigation & Water Management
        irrigation_tab = tk.Frame(self.info_notebook, bg='#ECEFF1')
        self.info_notebook.add(irrigation_tab, text="💧 IRRIGATION")
        self.build_irrigation_tab(irrigation_tab)

    def build_diseases_tab(self, parent):
        """Build diseases tab with icon cards"""
        canvas = tk.Canvas(parent, bg='#ECEFF1', highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#ECEFF1')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Header
        header = tk.Frame(scrollable_frame, bg='#ECEFF1')
        header.pack(fill=tk.X, padx=20, pady=(20, 30))
        tk.Label(header, text="🦠 Common Plant Diseases & Solutions",
                font=("Segoe UI", 18, "bold"), bg='#ECEFF1', fg='#C62828').pack()
        tk.Label(header, text="Click on any disease to learn more about symptoms and treatment",
                font=("Segoe UI", 10), bg='#ECEFF1', fg='#616161').pack(pady=(5, 0))
        
        # Icon cards container
        cards_container = tk.Frame(scrollable_frame, bg='#ECEFF1')
        cards_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)
        
        # Disease cards data
        diseases = [
            {
                'icon': '🌿',
                'title': 'Leaf Spot',
                'info': 'Brown spots on leaves',
                'content': 'SYMPTOMS:\n• Brown/black/yellow ringed spots on leaves\n• Defoliation over time\n• Reduced photosynthesis and yield\n\nPREVENTION:\n• Irrigate at the root (not foliage)\n• Increase ventilation and spacing\n• Use preventive fungicides in spring (Mancozeb, Captan)\n• Remove and destroy infected leaves immediately\n• Rotate crops (3-4 year intervals)\n• Use resistant varieties when available\n\nTREATMENT:\n• Propiconazole, Tebuconazole (systemic)\n• Apply 2–3 times at 7–10 day intervals\n• Start treatment at first sign of disease\n• Follow label instructions for dosage\n\nECONOMIC IMPACT: Can reduce yield by 20-40% if untreated.'
            },
            {
                'icon': '❄️',
                'title': 'Powdery Mildew',
                'info': 'White coating on leaves',
                'content': 'SYMPTOMS:\n• White powdery coating on leaves and stems\n• Plants weaken and yield drops significantly\n• Premature leaf drop\n• Reduced fruit quality\n\nPREVENTION:\n• Avoid early-morning overhead irrigation\n• Provide adequate spacing (improve air circulation)\n• Do not overuse nitrogen fertilizers\n• Plant resistant varieties\n• Maintain proper humidity levels (below 70%)\n\nTREATMENT:\n• Sulfur-based fungicides (preventive)\n• Systemic fungicides: Myclobutanil, Tebuconazole\n• Bio-friendly: Garlic–pepper extract spray\n• Neem oil applications (organic option)\n• Apply at 7-14 day intervals during high-risk periods\n\nTIMING: Most active in warm, humid conditions (20-25°C)'
            },
            {
                'icon': '⚫',
                'title': 'Blight',
                'info': 'Black lesions, wilting',
                'content': 'SYMPTOMS:\n• Necrosis from leaf edges\n• Black/brown lesions on leaves and stems\n• Sudden wilting and plant collapse\n• Water-soaked appearance\n\nPREVENTION:\n• Immediately remove and destroy infected plant parts\n• Disinfect tools between uses (10% bleach solution)\n• Use clean, certified seed/seedlings\n• Avoid working in fields when wet\n• Implement crop rotation (minimum 3 years)\n• Improve drainage\n\nTREATMENT:\n• Preventive copper-based sprays (Cuprofix, Champion)\n• On outbreak: Maneb or Ziram\n• Systemic: Metalaxyl, Propamocarb\n• Apply every 7-10 days during high-risk periods\n• Start before disease appears in your region\n\nWARNING: Highly contagious - isolate affected areas immediately'
            },
            {
                'icon': '🍂',
                'title': 'Root Rot',
                'info': 'Root decay, wilting',
                'content': 'SYMPTOMS:\n• Root decay/browning\n• Sudden wilting despite adequate water\n• Plant death, especially in young plants\n• Stunted growth\n• Yellowing leaves\n\nPREVENTION:\n• Ensure good drainage (avoid waterlogging)\n• Avoid overwatering\n• Soil disinfection before planting\n• Balanced nitrogen use (avoid excess)\n• Use well-draining soil mixes\n• Sterilize containers and tools\n• Plant at proper depth\n\nTREATMENT:\n• Trichoderma-based biologicals (preventive)\n• Root drench applications: Thiophanate-methyl\n• Remove and destroy affected plants\n• Improve soil drainage\n• Reduce irrigation frequency\n• Apply beneficial fungi (Mycorrhizae)\n\nCAUSE: Usually caused by waterlogged soil and fungal pathogens'
            },
            {
                'icon': '🧡',
                'title': 'Rust',
                'info': 'Orange pustules on leaves',
                'content': 'SYMPTOMS:\n• Orange/brown pustules on leaves\n• Yellowing and premature leaf drop\n• Reduced photosynthesis\n• Weakened plants\n\nPREVENTION:\n• Remove affected parts immediately\n• Clean planting (remove crop residues)\n• Improve air circulation\n• Use resistant varieties\n• Avoid overhead irrigation\n• Maintain proper plant spacing\n\nTREATMENT:\n• Tebuconazole, Propiconazole (systemic)\n• Early sprays are critical in cereals\n• Apply at first sign of disease\n• Repeat every 10-14 days if needed\n• Azoxystrobin (strobilurin class)\n\nSPECIAL NOTE: Early detection and treatment in cereals (wheat, barley) is crucial for yield protection'
            },
            {
                'icon': '🟤',
                'title': 'Anthracnose',
                'info': 'Brown lesions, fruit rot',
                'content': 'SYMPTOMS:\n• Brown, sunken lesions on leaves/stems\n• Fruit rot and premature drop\n• Dark spots on fruits\n• Twig dieback\n\nPREVENTION:\n• Remove infected residues from field\n• Prune correctly (clean cuts, proper timing)\n• Avoid work at peak humidity\n• Use drip irrigation (avoid wetting foliage)\n• Apply preventive fungicides\n• Maintain proper spacing\n\nTREATMENT:\n• Chlorothalonil, Mancozeb (protective)\n• Systemic: Azoxystrobin, Propiconazole\n• Apply every 7-10 days during high-risk periods\n• Observe pre-harvest intervals (check label)\n• Start treatment before flowering\n\nHARVEST: Follow pre-harvest waiting periods to ensure food safety'
            },
            {
                'icon': '🦠',
                'title': 'Bacterial Wilt',
                'info': 'Sudden wilting, vascular disease',
                'content': 'SYMPTOMS:\n• Sudden wilting of entire plant\n• Brown discoloration in vascular tissue\n• Sticky bacterial ooze from cut stems\n• No recovery after watering\n\nPREVENTION:\n• Use disease-free seed and transplants\n• Rotate crops (4-5 year intervals)\n• Control insect vectors (thrips, beetles)\n• Avoid working in wet fields\n• Disinfect tools regularly\n• Remove and destroy infected plants immediately\n\nTREATMENT:\n• No effective chemical treatment once infected\n• Remove affected plants immediately\n• Copper-based bactericides (preventive only)\n• Biological control: Bacillus subtilis\n• Focus on prevention - this disease is difficult to control\n\nWARNING: Highly destructive - can wipe out entire fields. Prevention is key.'
            },
            {
                'icon': '🟡',
                'title': 'Downy Mildew',
                'info': 'Yellow patches, fuzzy growth',
                'content': 'SYMPTOMS:\n• Yellow patches on upper leaf surface\n• White/gray fuzzy growth on underside\n• Leaf distortion and death\n• Reduced yield and quality\n\nPREVENTION:\n• Avoid overhead irrigation\n• Improve air circulation\n• Use resistant varieties\n• Remove infected plant debris\n• Maintain proper spacing\n• Apply preventive fungicides\n\nTREATMENT:\n• Metalaxyl, Propamocarb (systemic)\n• Copper-based fungicides\n• Apply every 7-10 days during cool, wet periods\n• Start treatment early in season\n• Rotate fungicide classes to prevent resistance\n\nCONDITIONS: Favored by cool temperatures (15-20°C) and high humidity'
            },
            {
                'icon': '🕷️',
                'title': 'Spider Mites',
                'info': 'Tiny pests, webbing on leaves',
                'content': 'SYMPTOMS:\n• Tiny yellow/white spots on leaves\n• Fine webbing on undersides\n• Leaf yellowing and drop\n• Stunted growth\n\nPREVENTION:\n• Maintain proper humidity (mites prefer dry conditions)\n• Regular monitoring with magnifying glass\n• Introduce beneficial predators (Phytoseiulus persimilis)\n• Avoid broad-spectrum insecticides (kill beneficials)\n• Keep plants well-watered\n\nTREATMENT:\n• Miticides: Abamectin, Bifenthrin\n• Horticultural oils (smothering effect)\n• Neem oil (organic option)\n• Apply to undersides of leaves (where mites live)\n• Repeat treatment 7-10 days later\n• Biological control: Predatory mites\n\nNOTE: Mites develop resistance quickly - rotate control methods'
            }
        ]
        
        # Create cards in grid
        for i, disease in enumerate(diseases):
            row = i // 3
            col = i % 3
            card = self.create_icon_card(
                cards_container,
                disease['icon'],
                disease['title'],
                disease['info'],
                disease['content']
            )
            card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")
        
        # Configure grid weights
        for i in range(3):
            cards_container.grid_columnconfigure(i, weight=1)
    
    def build_irrigation_tab(self, parent):
        """Build irrigation and water management tab with icon cards"""
        canvas = tk.Canvas(parent, bg='#ECEFF1', highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#ECEFF1')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Header
        header = tk.Frame(scrollable_frame, bg='#ECEFF1')
        header.pack(fill=tk.X, padx=20, pady=(20, 30))
        tk.Label(header, text="💧 Professional Irrigation & Water Management",
                font=("Segoe UI", 18, "bold"), bg='#ECEFF1', fg='#0277BD').pack()
        tk.Label(header, text="Modern techniques for efficient water use and optimal crop growth",
                font=("Segoe UI", 10), bg='#ECEFF1', fg='#616161').pack(pady=(5, 0))
        
        # Icon cards container
        cards_container = tk.Frame(scrollable_frame, bg='#ECEFF1')
        cards_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)
        
        # Irrigation cards data
        irrigation = [
            {
                'icon': '💧',
                'title': 'Drip Irrigation',
                'info': 'Most efficient method',
                'content': 'ADVANTAGES:\n• 60-70% water savings vs traditional methods\n• Precise water delivery to root zone\n• Reduces weed growth (dry between rows)\n• Prevents leaf wetting (reduces disease)\n• Can apply fertilizers (fertigation)\n• Works on slopes and irregular terrain\n\nSYSTEM COMPONENTS:\n• Main line (PVC or PE pipe)\n• Drip lines (emitters every 30-50 cm)\n• Filters (prevent clogging)\n• Pressure regulators\n• Valves and controllers\n\nINSTALLATION:\n• Spacing: 50-100 cm between lines\n• Emitter flow: 2-4 L/hour\n• Operating pressure: 1-2 bar\n• Filter mesh: 120-200 microns\n\nMAINTENANCE:\n• Regular filter cleaning\n• Flush lines monthly\n• Check emitters for clogging\n• Monitor pressure\n\nCOST: 15,000-30,000 TL per decare (pays back in 2-3 years)'
            },
            {
                'icon': '🌡️',
                'title': 'Soil Moisture Monitoring',
                'info': 'Real-time sensor technology',
                'content': 'SENSOR TYPES:\n\nTENSIONMETERS:\n• Measures soil water tension\n• Range: 0-100 centibars\n• Best for: Field crops\n• Installation: Root zone depth\n\nCAPACITANCE SENSORS:\n• Measures volumetric water content\n• Range: 0-100%\n• Best for: All soil types\n• Installation: Multiple depths\n\nTIME DOMAIN REFLECTOMETRY (TDR):\n• Most accurate\n• Measures soil moisture and EC\n• Best for: Research and precision agriculture\n• Cost: Higher investment\n\nAUTOMATIC SYSTEMS:\n• Real-time data logging\n• Mobile app monitoring\n• Automated irrigation triggers\n• Weather integration\n• Cloud-based analytics\n\nOPTIMAL MOISTURE LEVELS:\n• Field capacity: 100% (after irrigation)\n• Optimal range: 50-80% of field capacity\n• Wilting point: 20-30% (irrigation needed)\n• Monitor at multiple depths (15, 30, 60 cm)\n\nBENEFITS:\n• Prevent over/under irrigation\n• Improve water use efficiency\n• Increase yield by 15-25%\n• Reduce disease risk'
            },
            {
                'icon': '⏰',
                'title': 'Irrigation Scheduling',
                'info': 'When and how much to irrigate',
                'content': 'SCHEDULING METHODS:\n\nSOIL MOISTURE-BASED:\n• Monitor soil moisture sensors\n• Irrigate when moisture drops below threshold\n• Most accurate method\n• Prevents water stress\n\nEVAPOTRANSPIRATION (ET):\n• Calculate crop water needs\n• ET = Evaporation + Transpiration\n• Use weather station data\n• Adjust for crop growth stage\n\nCROP COEFFICIENT METHOD:\n• ETc = ETo × Kc\n• ETo: Reference evapotranspiration\n• Kc: Crop coefficient (varies by stage)\n• Stage-specific water needs\n\nTIMING:\n• Early morning (4-8 AM): Best time\n• Avoid midday (high evaporation)\n• Avoid evening (disease risk)\n• Frequency: 2-3 times per week (summer)\n\nWATER REQUIREMENTS BY CROP:\n• Wheat: 400-600 mm/season\n• Corn: 500-800 mm/season\n• Sunflower: 400-600 mm/season\n• Cotton: 600-900 mm/season\n• Barley: 350-550 mm/season\n\nSIGNS OF WATER STRESS:\n• Wilting leaves\n• Slow growth\n• Reduced yield\n• Premature maturity'
            },
            {
                'icon': '🌊',
                'title': 'Water Quality Management',
                'info': 'Ensure optimal water quality',
                'content': 'WATER QUALITY PARAMETERS:\n\npH LEVEL:\n• Optimal: 6.0-7.5\n• Too acidic (<5.5): Add lime\n• Too alkaline (>8.0): Add acid\n• Affects nutrient availability\n\nELECTRICAL CONDUCTIVITY (EC):\n• Measures total dissolved salts\n• Optimal: 0.5-2.0 dS/m\n• High EC (>3.0): Salinity problem\n• Leaching may be needed\n\nTOTAL DISSOLVED SOLIDS (TDS):\n• Optimal: <500 ppm\n• High TDS: Can cause salt buildup\n• Monitor regularly\n\nHARDNESS:\n• Calcium and magnesium content\n• Can cause emitter clogging\n• Use softeners if needed\n\nBIOLOGICAL CONTAMINANTS:\n• Test for bacteria, algae\n• Use filters and UV treatment\n• Prevent biofilm formation\n\nTREATMENT METHODS:\n• Filtration (sand, screen, disc filters)\n• Chemical treatment (chlorine)\n• UV sterilization\n• Reverse osmosis (high salinity)\n\nTESTING:\n• Test water source annually\n• More frequent if problems occur\n• Use certified laboratories\n• Keep records'
            },
            {
                'icon': '💾',
                'title': 'Water Conservation',
                'info': 'Sustainable water management',
                'content': 'CONSERVATION STRATEGIES:\n\nMULCHING:\n• Organic mulch (straw, compost)\n• Plastic mulch (vegetables)\n• Reduces evaporation by 30-50%\n• Maintains soil temperature\n• Suppresses weeds\n\nCOVER CROPS:\n• Reduce soil erosion\n• Improve water infiltration\n• Add organic matter\n• Protect soil structure\n\nSOIL MANAGEMENT:\n• Increase organic matter (improves water retention)\n• Reduce tillage (conserves moisture)\n• Improve soil structure\n• Use compost and organic amendments\n\nIRRIGATION EFFICIENCY:\n• Use drip or sprinkler systems\n• Maintain equipment properly\n• Fix leaks immediately\n• Schedule irrigation optimally\n• Use automation systems\n\nRAINWATER HARVESTING:\n• Collect from greenhouse roofs\n• Storage tanks (underground or aboveground)\n• Use for irrigation\n• Reduces water costs\n\nWATER RECYCLING:\n• Collect and reuse runoff\n• Treat if necessary\n• Greenhouse condensate collection\n• Closed-loop systems\n\nBENEFITS:\n• 30-50% water savings\n• Reduced costs\n• Environmental sustainability\n• Better crop quality\n• Improved soil health'
            },
            {
                'icon': '📊',
                'title': 'Smart Irrigation Systems',
                'info': 'IoT and automation technology',
                'content': 'AUTOMATED SYSTEMS:\n\nSENSOR-BASED AUTOMATION:\n• Soil moisture sensors trigger irrigation\n• Weather station integration\n• Evapotranspiration calculations\n• Automatic scheduling\n• Remote monitoring and control\n\nMOBILE APPLICATIONS:\n• Real-time monitoring\n• Remote control from smartphone\n• Alerts and notifications\n• Data logging and analysis\n• Historical trends\n\nCLOUD-BASED ANALYTICS:\n• Data storage and backup\n• Advanced analytics\n• Predictive irrigation\n• Crop water use modeling\n• Performance reports\n\nINTEGRATION FEATURES:\n• Weather forecast integration\n• Crop growth stage tracking\n• Fertilizer application (fertigation)\n• Multiple zone control\n• Scheduling optimization\n\nBENEFITS:\n• 40-60% water savings\n• Labor reduction\n• Improved crop quality\n• Better yield consistency\n• Data-driven decisions\n\nINVESTMENT:\n• Basic system: 5,000-10,000 TL per decare\n• Advanced system: 15,000-25,000 TL per decare\n• ROI: 2-3 years through water and labor savings\n\nFUTURE TRENDS:\n• AI-powered irrigation\n• Satellite imagery integration\n• Drone monitoring\n• Machine learning optimization'
            }
        ]
        
        # Create cards in grid
        for i, item in enumerate(irrigation):
            row = i // 3
            col = i % 3
            card = self.create_icon_card(
                cards_container,
                item['icon'],
                item['title'],
                item['info'],
                item['content']
            )
            card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")
        
        # Configure grid weights
        for i in range(3):
            cards_container.grid_columnconfigure(i, weight=1)
    
    def build_seeds_tab(self, parent):
        """Build seeds tab with icon cards"""
        canvas = tk.Canvas(parent, bg='#ECEFF1', highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#ECEFF1')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Header
        header = tk.Frame(scrollable_frame, bg='#ECEFF1')
        header.pack(fill=tk.X, padx=20, pady=(20, 30))
        tk.Label(header, text="🌱 Professional Seed Management",
                font=("Segoe UI", 18, "bold"), bg='#ECEFF1', fg='#FF8F00').pack()
        tk.Label(header, text="Learn best practices for seed quality, storage, and planting",
                font=("Segoe UI", 10), bg='#ECEFF1', fg='#616161').pack(pady=(5, 0))
        
        # Icon cards container
        cards_container = tk.Frame(scrollable_frame, bg='#ECEFF1')
        cards_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)
        
        # Seeds cards data
        seeds = [
            {
                'icon': '⭐',
                'title': 'Seed Quality',
                'info': '90%+ germination rate',
                'content': '✓ High germination rate (90%+)\n✓ Choose certified seed (labeled, registered)\n✓ Use clean, disease-free seed\n✓ Check expiration date\n✓ Research the producer\n✓ Remove broken/rotten seeds during grading\n\nQuality seed is the basis of yield. 1 kg poor seed can cost 10 kg harvest.'
            },
            {
                'icon': '🏠',
                'title': 'Seed Storage',
                'info': 'Cool, dry conditions',
                'content': '✓ Cool (<15°C), dry (<50% RH) conditions\n✓ Keep away from direct sunlight\n✓ Store in airtight glass/plastic containers\n✓ Label variety and year\n✓ Monthly checks (mold, insects)\n✓ Avoid cloth/burlap bags (absorb moisture)\n✓ Prefer refrigerator over freezer (species-dependent)\n\nProper storage preserves viability for 2–3 years.'
            },
            {
                'icon': '🔧',
                'title': 'Pre-sowing Prep',
                'info': 'Critical for germination',
                'content': '✓ Soaking: Beans, corn 12–24h; tiny seeds often not needed\n✓ Seed treatment: Fungicide (Thiram, Captan) + insecticide\n✓ Soil prep: pH 6.0–7.5, well-drained, firmed seedbed\n✓ Sowing depth: 2–3× seed size rule\n✓ Row spacing: Adjust to crop vigor\n✓ Soil temperature: Typically at least 10–15°C\n\nGood preparation is critical for germination. Do not rush.'
            },
            {
                'icon': '⏱️',
                'title': 'Germination Times',
                'info': '7-21 days typically',
                'content': '• Wheat: 7–14 days | Slow in cold soils\n• Corn: 7–10 days | Temperature is critical\n• Tomato: 7–14 days | Prefer seedlings\n• Pepper: 10–21 days | Slowest\n• Cucumber: 7–10 days | Fast grower\n• Lettuce: 4–10 days | Shallow sowing\n\nTemperature and moisture affect timing. If >2× normal, investigate.'
            },
            {
                'icon': '💰',
                'title': 'Pricing & Economics',
                'info': 'ROI analysis important',
                'content': '✓ Hybrid seeds are costly but high-yield (+30–50%)\n✓ Open-pollinated: cheaper, can save seed\n✓ Organic-certified: premium price\n✓ Bulk discount: >5 kg often 15–20% off\n✓ Seed cost: target 5–10% of total cost\n✓ Financing: consider subsidized credit programs\n\nAnalyze ROI: seed price vs potential harvest revenue.'
            },
            {
                'icon': '💧',
                'title': 'Soil Moisture Ranges',
                'info': 'Optimal moisture for each crop',
                'content': '🌾 Wheat: 60-70% moisture\n• Ideal range for healthy growth\n• Below 60%: irrigation needed\n• Above 70%: risk of root rot\n\n🌽 Corn: 55-65% moisture\n• Critical during tasseling and silking\n• Consistent moisture improves yield\n\n🌻 Sunflower: 50-60% moisture\n• Drought tolerant but needs water during flowering\n• Lower range than other crops\n\n☁ Cotton: 55-65% moisture\n• Sensitive to water stress during boll development\n• Avoid waterlogging\n\n🌿 Barley: 55-70% moisture\n• Similar to wheat but slightly wider range\n• Good drought tolerance\n\n💡 Tip: Monitor soil moisture regularly and maintain within these ranges for optimal yield. Automatic irrigation systems help maintain ideal conditions.'
            },
            {
                'icon': '🌍',
                'title': 'Soil Types & pH Requirements',
                'info': 'Optimal soil conditions for crops',
                'content': 'SOIL TYPE PREFERENCES:\n\n🌾 Wheat: Loamy soil, well-drained\n• pH: 6.0-7.5 (optimal 6.5-7.0)\n• Tolerates various soil types\n• Avoid heavy clay or sandy soils\n\n🌽 Corn: Deep, fertile loam\n• pH: 5.8-7.0 (optimal 6.0-6.8)\n• Requires good drainage\n• High organic matter preferred\n\n🌻 Sunflower: Well-drained loam or sandy loam\n• pH: 6.0-7.5 (optimal 6.5-7.0)\n• Tolerates slightly alkaline soils\n• Deep root system needs deep soil\n\n☁ Cotton: Sandy loam to clay loam\n• pH: 5.8-8.0 (optimal 6.0-7.0)\n• Good drainage essential\n• Tolerates moderate salinity\n\n🌿 Barley: Well-drained loam\n• pH: 6.0-8.0 (optimal 6.5-7.5)\n• More tolerant of alkaline soils than wheat\n• Avoid waterlogged conditions\n\nSOIL PREPARATION:\n• Test soil pH annually\n• Adjust pH 6 months before planting\n• Add lime to raise pH (if acidic)\n• Add sulfur to lower pH (if alkaline)\n• Incorporate organic matter (compost, manure)'
            },
            {
                'icon': '🌡️',
                'title': 'Climate & Temperature',
                'info': 'Optimal growing conditions',
                'content': 'TEMPERATURE REQUIREMENTS:\n\n🌾 Wheat:\n• Germination: 3-4°C minimum\n• Growth: 15-25°C optimal\n• Maturity: 20-25°C\n• Winter wheat: Tolerates -15°C\n• Spring wheat: Plant when soil >5°C\n\n🌽 Corn:\n• Germination: 10°C minimum (soil temp)\n• Growth: 21-27°C optimal\n• Critical: 18-24°C during pollination\n• Heat stress above 35°C\n• Frost sensitive\n\n🌻 Sunflower:\n• Germination: 8-10°C\n• Growth: 20-25°C optimal\n• Tolerates heat up to 35°C\n• Frost sensitive\n• Needs warm, sunny conditions\n\n☁ Cotton:\n• Germination: 15°C minimum\n• Growth: 21-30°C optimal\n• Requires long growing season (150-180 days)\n• Heat tolerant (up to 40°C)\n• Frost kills plants\n\n🌿 Barley:\n• Germination: 1-2°C minimum\n• Growth: 15-20°C optimal\n• More cold tolerant than wheat\n• Spring barley: Plant early (March-April)\n• Winter barley: Plant autumn\n\nCLIMATE ZONES:\n• Consider your region\'s average temperatures\n• Check last frost dates\n• Monitor growing degree days (GDD)'
            },
            {
                'icon': '🧪',
                'title': 'Fertilization & Nutrients',
                'info': 'Essential nutrients for optimal growth',
                'content': 'MACRO NUTRIENTS (N-P-K):\n\n🌾 Wheat:\n• Nitrogen (N): 120-180 kg/ha\n  - Apply 50% at planting, 50% at tillering\n  - Critical for yield and protein content\n• Phosphorus (P): 40-60 kg/ha\n  - Apply at planting (root development)\n• Potassium (K): 60-100 kg/ha\n  - Apply before planting\n\n🌽 Corn:\n• Nitrogen (N): 150-250 kg/ha\n  - Split application: 30% at planting, 70% at V6-V8\n  - Critical during tasseling and silking\n• Phosphorus (P): 50-80 kg/ha\n  - Essential for root and ear development\n• Potassium (K): 100-150 kg/ha\n  - Important for stalk strength\n\n🌻 Sunflower:\n• Nitrogen (N): 80-120 kg/ha\n  - Apply 50% at planting, 50% at bud stage\n• Phosphorus (P): 40-60 kg/ha\n  - Critical for seed development\n• Potassium (K): 60-100 kg/ha\n\n☁ Cotton:\n• Nitrogen (N): 100-150 kg/ha\n  - Split: 40% at planting, 60% during flowering\n• Phosphorus (P): 30-50 kg/ha\n• Potassium (K): 80-120 kg/ha\n\n🌿 Barley:\n• Nitrogen (N): 100-140 kg/ha\n  - Lower than wheat (affects malting quality)\n• Phosphorus (P): 40-60 kg/ha\n• Potassium (K): 60-100 kg/ha\n\nMICRO NUTRIENTS:\n• Zinc (Zn): Critical for cereals\n• Boron (B): Important for flowering\n• Iron (Fe): Prevents chlorosis\n• Apply based on soil test results'
            },
            {
                'icon': '📅',
                'title': 'Planting & Harvest Calendar',
                'info': 'Optimal timing for each crop',
                'content': 'PLANTING TIMES:\n\n🌾 Wheat:\n• Winter wheat: October-November (Turkey)\n• Spring wheat: March-April\n• Depth: 2-4 cm\n• Row spacing: 15-20 cm\n• Seeding rate: 150-200 kg/ha\n\n🌽 Corn:\n• Planting: April-May (when soil temp >10°C)\n• Depth: 3-5 cm\n• Row spacing: 70-75 cm\n• Plant spacing: 20-25 cm\n• Seeding rate: 20-25 kg/ha\n\n🌻 Sunflower:\n• Planting: April-May\n• Depth: 3-4 cm\n• Row spacing: 70-75 cm\n• Plant spacing: 25-30 cm\n• Seeding rate: 5-7 kg/ha\n\n☁ Cotton:\n• Planting: April-May\n• Depth: 2-3 cm\n• Row spacing: 70-90 cm\n• Plant spacing: 15-20 cm\n• Seeding rate: 15-20 kg/ha\n\n🌿 Barley:\n• Winter barley: October-November\n• Spring barley: March-April\n• Depth: 2-4 cm\n• Row spacing: 15-20 cm\n• Seeding rate: 120-180 kg/ha\n\nHARVEST TIMES:\n• Wheat: June-July (winter), August (spring)\n• Corn: September-October\n• Sunflower: August-September\n• Cotton: September-November (multiple pickings)\n• Barley: June-July\n\nHARVEST INDICATORS:\n• Moisture content: 12-14% for grains\n• Color change and maturity\n• Test weight and quality parameters'
            }
        ]
        
        # Create cards in grid
        for i, seed in enumerate(seeds):
            row = i // 3
            col = i % 3
            card = self.create_icon_card(
                cards_container,
                seed['icon'],
                seed['title'],
                seed['info'],
                seed['content']
            )
            card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")
        
        # Configure grid weights
        for i in range(3):
            cards_container.grid_columnconfigure(i, weight=1)
    
    def build_irrigation_tab(self, parent):
        """Build irrigation and water management tab with icon cards"""
        canvas = tk.Canvas(parent, bg='#ECEFF1', highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#ECEFF1')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Header
        header = tk.Frame(scrollable_frame, bg='#ECEFF1')
        header.pack(fill=tk.X, padx=20, pady=(20, 30))
        tk.Label(header, text="💧 Professional Irrigation & Water Management",
                font=("Segoe UI", 18, "bold"), bg='#ECEFF1', fg='#0277BD').pack()
        tk.Label(header, text="Modern techniques for efficient water use and optimal crop growth",
                font=("Segoe UI", 10), bg='#ECEFF1', fg='#616161').pack(pady=(5, 0))
        
        # Icon cards container
        cards_container = tk.Frame(scrollable_frame, bg='#ECEFF1')
        cards_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)
        
        # Irrigation cards data
        irrigation = [
            {
                'icon': '💧',
                'title': 'Drip Irrigation',
                'info': 'Most efficient method',
                'content': 'ADVANTAGES:\n• 60-70% water savings vs traditional methods\n• Precise water delivery to root zone\n• Reduces weed growth (dry between rows)\n• Prevents leaf wetting (reduces disease)\n• Can apply fertilizers (fertigation)\n• Works on slopes and irregular terrain\n\nSYSTEM COMPONENTS:\n• Main line (PVC or PE pipe)\n• Drip lines (emitters every 30-50 cm)\n• Filters (prevent clogging)\n• Pressure regulators\n• Valves and controllers\n\nINSTALLATION:\n• Spacing: 50-100 cm between lines\n• Emitter flow: 2-4 L/hour\n• Operating pressure: 1-2 bar\n• Filter mesh: 120-200 microns\n\nMAINTENANCE:\n• Regular filter cleaning\n• Flush lines monthly\n• Check emitters for clogging\n• Monitor pressure\n\nCOST: 15,000-30,000 TL per decare (pays back in 2-3 years)'
            },
            {
                'icon': '🌡️',
                'title': 'Soil Moisture Monitoring',
                'info': 'Real-time sensor technology',
                'content': 'SENSOR TYPES:\n\nTENSIONMETERS:\n• Measures soil water tension\n• Range: 0-100 centibars\n• Best for: Field crops\n• Installation: Root zone depth\n\nCAPACITANCE SENSORS:\n• Measures volumetric water content\n• Range: 0-100%\n• Best for: All soil types\n• Installation: Multiple depths\n\nTIME DOMAIN REFLECTOMETRY (TDR):\n• Most accurate\n• Measures soil moisture and EC\n• Best for: Research and precision agriculture\n• Cost: Higher investment\n\nAUTOMATIC SYSTEMS:\n• Real-time data logging\n• Mobile app monitoring\n• Automated irrigation triggers\n• Weather integration\n• Cloud-based analytics\n\nOPTIMAL MOISTURE LEVELS:\n• Field capacity: 100% (after irrigation)\n• Optimal range: 50-80% of field capacity\n• Wilting point: 20-30% (irrigation needed)\n• Monitor at multiple depths (15, 30, 60 cm)\n\nBENEFITS:\n• Prevent over/under irrigation\n• Improve water use efficiency\n• Increase yield by 15-25%\n• Reduce disease risk'
            },
            {
                'icon': '⏰',
                'title': 'Irrigation Scheduling',
                'info': 'When and how much to irrigate',
                'content': 'SCHEDULING METHODS:\n\nSOIL MOISTURE-BASED:\n• Monitor soil moisture sensors\n• Irrigate when moisture drops below threshold\n• Most accurate method\n• Prevents water stress\n\nEVAPOTRANSPIRATION (ET):\n• Calculate crop water needs\n• ET = Evaporation + Transpiration\n• Use weather station data\n• Adjust for crop growth stage\n\nCROP COEFFICIENT METHOD:\n• ETc = ETo × Kc\n• ETo: Reference evapotranspiration\n• Kc: Crop coefficient (varies by stage)\n• Stage-specific water needs\n\nTIMING:\n• Early morning (4-8 AM): Best time\n• Avoid midday (high evaporation)\n• Avoid evening (disease risk)\n• Frequency: 2-3 times per week (summer)\n\nWATER REQUIREMENTS BY CROP:\n• Wheat: 400-600 mm/season\n• Corn: 500-800 mm/season\n• Sunflower: 400-600 mm/season\n• Cotton: 600-900 mm/season\n• Barley: 350-550 mm/season\n\nSIGNS OF WATER STRESS:\n• Wilting leaves\n• Slow growth\n• Reduced yield\n• Premature maturity'
            },
            {
                'icon': '🌊',
                'title': 'Water Quality Management',
                'info': 'Ensure optimal water quality',
                'content': 'WATER QUALITY PARAMETERS:\n\npH LEVEL:\n• Optimal: 6.0-7.5\n• Too acidic (<5.5): Add lime\n• Too alkaline (>8.0): Add acid\n• Affects nutrient availability\n\nELECTRICAL CONDUCTIVITY (EC):\n• Measures total dissolved salts\n• Optimal: 0.5-2.0 dS/m\n• High EC (>3.0): Salinity problem\n• Leaching may be needed\n\nTOTAL DISSOLVED SOLIDS (TDS):\n• Optimal: <500 ppm\n• High TDS: Can cause salt buildup\n• Monitor regularly\n\nHARDNESS:\n• Calcium and magnesium content\n• Can cause emitter clogging\n• Use softeners if needed\n\nBIOLOGICAL CONTAMINANTS:\n• Test for bacteria, algae\n• Use filters and UV treatment\n• Prevent biofilm formation\n\nTREATMENT METHODS:\n• Filtration (sand, screen, disc filters)\n• Chemical treatment (chlorine)\n• UV sterilization\n• Reverse osmosis (high salinity)\n\nTESTING:\n• Test water source annually\n• More frequent if problems occur\n• Use certified laboratories\n• Keep records'
            },
            {
                'icon': '💾',
                'title': 'Water Conservation',
                'info': 'Sustainable water management',
                'content': 'CONSERVATION STRATEGIES:\n\nMULCHING:\n• Organic mulch (straw, compost)\n• Plastic mulch (vegetables)\n• Reduces evaporation by 30-50%\n• Maintains soil temperature\n• Suppresses weeds\n\nCOVER CROPS:\n• Reduce soil erosion\n• Improve water infiltration\n• Add organic matter\n• Protect soil structure\n\nSOIL MANAGEMENT:\n• Increase organic matter (improves water retention)\n• Reduce tillage (conserves moisture)\n• Improve soil structure\n• Use compost and organic amendments\n\nIRRIGATION EFFICIENCY:\n• Use drip or sprinkler systems\n• Maintain equipment properly\n• Fix leaks immediately\n• Schedule irrigation optimally\n• Use automation systems\n\nRAINWATER HARVESTING:\n• Collect from greenhouse roofs\n• Storage tanks (underground or aboveground)\n• Use for irrigation\n• Reduces water costs\n\nWATER RECYCLING:\n• Collect and reuse runoff\n• Treat if necessary\n• Greenhouse condensate collection\n• Closed-loop systems\n\nBENEFITS:\n• 30-50% water savings\n• Reduced costs\n• Environmental sustainability\n• Better crop quality\n• Improved soil health'
            },
            {
                'icon': '📊',
                'title': 'Smart Irrigation Systems',
                'info': 'IoT and automation technology',
                'content': 'AUTOMATED SYSTEMS:\n\nSENSOR-BASED AUTOMATION:\n• Soil moisture sensors trigger irrigation\n• Weather station integration\n• Evapotranspiration calculations\n• Automatic scheduling\n• Remote monitoring and control\n\nMOBILE APPLICATIONS:\n• Real-time monitoring\n• Remote control from smartphone\n• Alerts and notifications\n• Data logging and analysis\n• Historical trends\n\nCLOUD-BASED ANALYTICS:\n• Data storage and backup\n• Advanced analytics\n• Predictive irrigation\n• Crop water use modeling\n• Performance reports\n\nINTEGRATION FEATURES:\n• Weather forecast integration\n• Crop growth stage tracking\n• Fertilizer application (fertigation)\n• Multiple zone control\n• Scheduling optimization\n\nBENEFITS:\n• 40-60% water savings\n• Labor reduction\n• Improved crop quality\n• Better yield consistency\n• Data-driven decisions\n\nINVESTMENT:\n• Basic system: 5,000-10,000 TL per decare\n• Advanced system: 15,000-25,000 TL per decare\n• ROI: 2-3 years through water and labor savings\n\nFUTURE TRENDS:\n• AI-powered irrigation\n• Satellite imagery integration\n• Drone monitoring\n• Machine learning optimization'
            }
        ]
        
        # Create cards in grid
        for i, item in enumerate(irrigation):
            row = i // 3
            col = i % 3
            card = self.create_icon_card(
                cards_container,
                item['icon'],
                item['title'],
                item['info'],
                item['content']
            )
            card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")
        
        # Configure grid weights
        for i in range(3):
            cards_container.grid_columnconfigure(i, weight=1)
    
    def build_greenhouse_tab(self, parent):
        """Build greenhouse tab with icon cards"""
        canvas = tk.Canvas(parent, bg='#ECEFF1', highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#ECEFF1')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Header
        header = tk.Frame(scrollable_frame, bg='#ECEFF1')
        header.pack(fill=tk.X, padx=20, pady=(20, 30))
        tk.Label(header, text="🏢 Modern Greenhouse Management",
                font=("Segoe UI", 18, "bold"), bg='#ECEFF1', fg='#1976D2').pack()
        tk.Label(header, text="Professional techniques for year-round production",
                font=("Segoe UI", 10), bg='#ECEFF1', fg='#616161').pack(pady=(5, 0))
        
        # Icon cards container
        cards_container = tk.Frame(scrollable_frame, bg='#ECEFF1')
        cards_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)
        
        # Greenhouse cards data
        greenhouse = [
            {
                'icon': '🏗️',
                'title': 'Setup & Investment',
                'info': '150-300k TL per decare',
                'content': '• Location: Sunny area, accessible, near water source\n• Orientation: North-south (solar efficiency)\n• Size: Minimum 500 m² (economically efficient)\n• Infrastructure: Concrete or reinforced concrete foundation, galvanized steel frame\n• Covering: Double-layer polyethylene or polycarbonate glass\n• Cost: 150,000-300,000 TL per decare (depending on materials)\n• Government support: Grants available up to 50-70%\n\nProper setup enables year-round production and pays for itself in 5-7 years.'
            },
            {
                'icon': '🌡️',
                'title': 'Temperature Control',
                'info': 'Day 20-30°C, Night 15-20°C',
                'content': '• Target temperature: Daytime 20-30°C, Night 15-20°C (depending on crop)\n• Monitoring: Digital thermometer, automatic recording\n• Heating: LPG/natural gas burners, solar water system\n• Cooling: Automatic ventilation, fan-pad system\n• Shading: Automatic shading curtain (40-60%)\n• Alarm: SMS notification smart systems\n\nOptimal temperature provides 20-30% yield increase. Investment pays back in 2 years.'
            },
            {
                'icon': '💧',
                'title': 'Humidity & Irrigation',
                'info': '60-80% humidity ideal',
                'content': '• Ideal humidity: 60-80%\n• Measurement: Hygrometer monitoring, automatic systems\n• Ventilation: Morning routine, avoid humidity buildup\n• Evaporation: Fan-pad system (summer months)\n• Irrigation: Drip hose, automatic timer\n• Water quality: EC and pH control (pH 6.5-7.0 ideal)\n• Water savings: 60-70% savings with drip irrigation\n\nBalanced humidity reduces disease risk by 50% and improves quality.'
            },
            {
                'icon': '🌿',
                'title': 'Soil & Nutrition',
                'info': 'Quality produce +10-20%',
                'content': '• Soil analysis: Twice a year (spring-autumn)\n• pH value: 6.0-7.0 ideal\n• Nitrogen-Phosphorus-Potassium balance\n• Micro elements: Iron, zinc, boron supplementation\n• Organic fertilizer: Compost, worm castings (monthly)\n• Foliar fertilization: Liquid fertilizers every 15 days\n• Greenhouse soil: Recommended to replace every 3-5 years\n\nNutrition management means quality produce and 10-20% yield increase.'
            },
            {
                'icon': '🍅',
                'title': 'Crops & Profitability',
                'info': '40-60% profitability',
                'content': '• Tomato: 12-15 ton/decare yield, 40-60% profitability\n• Cucumber: Fast growing, 8-12 ton/decare\n• Pepper: High value, 5-8 ton/decare\n• Lettuce: 30-40 day cycle, short-term cash flow\n• Strawberry: High profitability, labor intensive\n• Cactus/ornamental plants: Niche market, high margin\n\nConduct market analysis, determine your region\'s needs. Identify customers.'
            },
            {
                'icon': '🛡️',
                'title': 'Disease & Pest Control',
                'info': '3-4x more economical',
                'content': '• Preventive: Regular fungicide (weekly)\n• Traps: Yellow sticky traps (viral, thrips)\n• Biological control: Beneficial insects (predator mites)\n• Cleanliness: Regular plant cleaning and maintenance\n• Quarantine: Isolation before new seedling application\n• Integrated pest control: Multi-method approach\n• Residue management: Follow pre-harvest waiting periods\n\nPreventive approach is 3-4 times more economical than crisis management.'
            },
            {
                'icon': '💡',
                'title': 'Smart Technology',
                'info': 'IoT and automation systems',
                'content': 'MODERN GREENHOUSE TECHNOLOGY:\n\nAUTOMATION SYSTEMS:\n• Climate control: Automated temperature, humidity, ventilation\n• Irrigation: Drip systems with timers and sensors\n• Lighting: LED grow lights with spectrum control\n• CO2 enrichment: Automated injection systems\n• Shading: Automatic curtain systems\n\nSENSOR NETWORKS:\n• Soil moisture sensors (real-time monitoring)\n• Temperature/humidity sensors (multiple zones)\n• Light sensors (PAR measurement)\n• pH and EC sensors (nutrient solution)\n• Weather stations (external conditions)\n\nSMART FEATURES:\n• Mobile app control and monitoring\n• SMS/email alerts for critical conditions\n• Data logging and analysis\n• Remote access and control\n• Energy management systems\n\nBENEFITS:\n• 30-50% water savings\n• 20-30% yield increase\n• Reduced labor costs\n• Better quality control\n• Year-round production\n\nINVESTMENT: Smart systems pay back in 2-3 years through increased efficiency.'
            },
            {
                'icon': '⚡',
                'title': 'Energy Efficiency',
                'info': 'Reduce costs, increase sustainability',
                'content': 'ENERGY-SAVING STRATEGIES:\n\nHEATING OPTIMIZATION:\n• Double-layer covering (reduces heat loss by 40%)\n• Thermal screens (close at night)\n• Heat storage systems (water tanks)\n• Geothermal heating (long-term investment)\n• Solar water heating systems\n\nCOOLING EFFICIENCY:\n• Evaporative cooling (fan-pad systems)\n• Shading systems (reduce solar load)\n• Natural ventilation (roof vents)\n• Reflective materials (whitewash in summer)\n\nLIGHTING:\n• LED grow lights (50-70% energy savings vs HPS)\n• Light spectrum optimization\n• Photoperiod control\n• Motion sensors for lighting\n\nINSULATION:\n• Proper sealing (doors, vents)\n• Thermal curtains\n• Windbreaks\n• Foundation insulation\n\nENERGY MONITORING:\n• Smart meters\n• Energy usage tracking\n• Cost analysis per crop\n• Optimization recommendations\n\nSAVINGS: Proper energy management can reduce costs by 30-40%.'
            }
        ]
        
        # Create cards in grid
        for i, item in enumerate(greenhouse):
            row = i // 3
            col = i % 3
            card = self.create_icon_card(
                cards_container,
                item['icon'],
                item['title'],
                item['info'],
                item['content']
            )
            card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")
        
        # Configure grid weights
        for i in range(3):
            cards_container.grid_columnconfigure(i, weight=1)
    
    def build_irrigation_tab(self, parent):
        """Build irrigation and water management tab with icon cards"""
        canvas = tk.Canvas(parent, bg='#ECEFF1', highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#ECEFF1')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Header
        header = tk.Frame(scrollable_frame, bg='#ECEFF1')
        header.pack(fill=tk.X, padx=20, pady=(20, 30))
        tk.Label(header, text="💧 Professional Irrigation & Water Management",
                font=("Segoe UI", 18, "bold"), bg='#ECEFF1', fg='#0277BD').pack()
        tk.Label(header, text="Modern techniques for efficient water use and optimal crop growth",
                font=("Segoe UI", 10), bg='#ECEFF1', fg='#616161').pack(pady=(5, 0))
        
        # Icon cards container
        cards_container = tk.Frame(scrollable_frame, bg='#ECEFF1')
        cards_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)
        
        # Irrigation cards data
        irrigation = [
            {
                'icon': '💧',
                'title': 'Drip Irrigation',
                'info': 'Most efficient method',
                'content': 'ADVANTAGES:\n• 60-70% water savings vs traditional methods\n• Precise water delivery to root zone\n• Reduces weed growth (dry between rows)\n• Prevents leaf wetting (reduces disease)\n• Can apply fertilizers (fertigation)\n• Works on slopes and irregular terrain\n\nSYSTEM COMPONENTS:\n• Main line (PVC or PE pipe)\n• Drip lines (emitters every 30-50 cm)\n• Filters (prevent clogging)\n• Pressure regulators\n• Valves and controllers\n\nINSTALLATION:\n• Spacing: 50-100 cm between lines\n• Emitter flow: 2-4 L/hour\n• Operating pressure: 1-2 bar\n• Filter mesh: 120-200 microns\n\nMAINTENANCE:\n• Regular filter cleaning\n• Flush lines monthly\n• Check emitters for clogging\n• Monitor pressure\n\nCOST: 15,000-30,000 TL per decare (pays back in 2-3 years)'
            },
            {
                'icon': '🌡️',
                'title': 'Soil Moisture Monitoring',
                'info': 'Real-time sensor technology',
                'content': 'SENSOR TYPES:\n\nTENSIONMETERS:\n• Measures soil water tension\n• Range: 0-100 centibars\n• Best for: Field crops\n• Installation: Root zone depth\n\nCAPACITANCE SENSORS:\n• Measures volumetric water content\n• Range: 0-100%\n• Best for: All soil types\n• Installation: Multiple depths\n\nTIME DOMAIN REFLECTOMETRY (TDR):\n• Most accurate\n• Measures soil moisture and EC\n• Best for: Research and precision agriculture\n• Cost: Higher investment\n\nAUTOMATIC SYSTEMS:\n• Real-time data logging\n• Mobile app monitoring\n• Automated irrigation triggers\n• Weather integration\n• Cloud-based analytics\n\nOPTIMAL MOISTURE LEVELS:\n• Field capacity: 100% (after irrigation)\n• Optimal range: 50-80% of field capacity\n• Wilting point: 20-30% (irrigation needed)\n• Monitor at multiple depths (15, 30, 60 cm)\n\nBENEFITS:\n• Prevent over/under irrigation\n• Improve water use efficiency\n• Increase yield by 15-25%\n• Reduce disease risk'
            },
            {
                'icon': '⏰',
                'title': 'Irrigation Scheduling',
                'info': 'When and how much to irrigate',
                'content': 'SCHEDULING METHODS:\n\nSOIL MOISTURE-BASED:\n• Monitor soil moisture sensors\n• Irrigate when moisture drops below threshold\n• Most accurate method\n• Prevents water stress\n\nEVAPOTRANSPIRATION (ET):\n• Calculate crop water needs\n• ET = Evaporation + Transpiration\n• Use weather station data\n• Adjust for crop growth stage\n\nCROP COEFFICIENT METHOD:\n• ETc = ETo × Kc\n• ETo: Reference evapotranspiration\n• Kc: Crop coefficient (varies by stage)\n• Stage-specific water needs\n\nTIMING:\n• Early morning (4-8 AM): Best time\n• Avoid midday (high evaporation)\n• Avoid evening (disease risk)\n• Frequency: 2-3 times per week (summer)\n\nWATER REQUIREMENTS BY CROP:\n• Wheat: 400-600 mm/season\n• Corn: 500-800 mm/season\n• Sunflower: 400-600 mm/season\n• Cotton: 600-900 mm/season\n• Barley: 350-550 mm/season\n\nSIGNS OF WATER STRESS:\n• Wilting leaves\n• Slow growth\n• Reduced yield\n• Premature maturity'
            },
            {
                'icon': '🌊',
                'title': 'Water Quality Management',
                'info': 'Ensure optimal water quality',
                'content': 'WATER QUALITY PARAMETERS:\n\npH LEVEL:\n• Optimal: 6.0-7.5\n• Too acidic (<5.5): Add lime\n• Too alkaline (>8.0): Add acid\n• Affects nutrient availability\n\nELECTRICAL CONDUCTIVITY (EC):\n• Measures total dissolved salts\n• Optimal: 0.5-2.0 dS/m\n• High EC (>3.0): Salinity problem\n• Leaching may be needed\n\nTOTAL DISSOLVED SOLIDS (TDS):\n• Optimal: <500 ppm\n• High TDS: Can cause salt buildup\n• Monitor regularly\n\nHARDNESS:\n• Calcium and magnesium content\n• Can cause emitter clogging\n• Use softeners if needed\n\nBIOLOGICAL CONTAMINANTS:\n• Test for bacteria, algae\n• Use filters and UV treatment\n• Prevent biofilm formation\n\nTREATMENT METHODS:\n• Filtration (sand, screen, disc filters)\n• Chemical treatment (chlorine)\n• UV sterilization\n• Reverse osmosis (high salinity)\n\nTESTING:\n• Test water source annually\n• More frequent if problems occur\n• Use certified laboratories\n• Keep records'
            },
            {
                'icon': '💾',
                'title': 'Water Conservation',
                'info': 'Sustainable water management',
                'content': 'CONSERVATION STRATEGIES:\n\nMULCHING:\n• Organic mulch (straw, compost)\n• Plastic mulch (vegetables)\n• Reduces evaporation by 30-50%\n• Maintains soil temperature\n• Suppresses weeds\n\nCOVER CROPS:\n• Reduce soil erosion\n• Improve water infiltration\n• Add organic matter\n• Protect soil structure\n\nSOIL MANAGEMENT:\n• Increase organic matter (improves water retention)\n• Reduce tillage (conserves moisture)\n• Improve soil structure\n• Use compost and organic amendments\n\nIRRIGATION EFFICIENCY:\n• Use drip or sprinkler systems\n• Maintain equipment properly\n• Fix leaks immediately\n• Schedule irrigation optimally\n• Use automation systems\n\nRAINWATER HARVESTING:\n• Collect from greenhouse roofs\n• Storage tanks (underground or aboveground)\n• Use for irrigation\n• Reduces water costs\n\nWATER RECYCLING:\n• Collect and reuse runoff\n• Treat if necessary\n• Greenhouse condensate collection\n• Closed-loop systems\n\nBENEFITS:\n• 30-50% water savings\n• Reduced costs\n• Environmental sustainability\n• Better crop quality\n• Improved soil health'
            },
            {
                'icon': '📊',
                'title': 'Smart Irrigation Systems',
                'info': 'IoT and automation technology',
                'content': 'AUTOMATED SYSTEMS:\n\nSENSOR-BASED AUTOMATION:\n• Soil moisture sensors trigger irrigation\n• Weather station integration\n• Evapotranspiration calculations\n• Automatic scheduling\n• Remote monitoring and control\n\nMOBILE APPLICATIONS:\n• Real-time monitoring\n• Remote control from smartphone\n• Alerts and notifications\n• Data logging and analysis\n• Historical trends\n\nCLOUD-BASED ANALYTICS:\n• Data storage and backup\n• Advanced analytics\n• Predictive irrigation\n• Crop water use modeling\n• Performance reports\n\nINTEGRATION FEATURES:\n• Weather forecast integration\n• Crop growth stage tracking\n• Fertilizer application (fertigation)\n• Multiple zone control\n• Scheduling optimization\n\nBENEFITS:\n• 40-60% water savings\n• Labor reduction\n• Improved crop quality\n• Better yield consistency\n• Data-driven decisions\n\nINVESTMENT:\n• Basic system: 5,000-10,000 TL per decare\n• Advanced system: 15,000-25,000 TL per decare\n• ROI: 2-3 years through water and labor savings\n\nFUTURE TRENDS:\n• AI-powered irrigation\n• Satellite imagery integration\n• Drone monitoring\n• Machine learning optimization'
            }
        ]
        
        # Create cards in grid
        for i, item in enumerate(irrigation):
            row = i // 3
            col = i % 3
            card = self.create_icon_card(
                cards_container,
                item['icon'],
                item['title'],
                item['info'],
                item['content']
            )
            card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")
        
        # Configure grid weights
        for i in range(3):
            cards_container.grid_columnconfigure(i, weight=1)
    
    def build_fruit_tab(self, parent):
        """Build fruit growing tab with icon cards"""
        canvas = tk.Canvas(parent, bg='#ECEFF1', highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#ECEFF1')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Header
        header = tk.Frame(scrollable_frame, bg='#ECEFF1')
        header.pack(fill=tk.X, padx=20, pady=(20, 30))
        tk.Label(header, text="🍎 Professional Fruit Growing",
                font=("Segoe UI", 18, "bold"), bg='#ECEFF1', fg='#7B1FA2').pack()
        tk.Label(header, text="Expert guide to orchard management and profit",
                font=("Segoe UI", 10), bg='#ECEFF1', fg='#616161').pack(pady=(5, 0))
        
        # Icon cards container
        cards_container = tk.Frame(scrollable_frame, bg='#ECEFF1')
        cards_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)
        
        # Fruit cards data
        fruits = [
            {
                'icon': '🌳',
                'title': 'Orchard Setup',
                'info': '20-30 years productivity',
                'content': '• Soil analysis: Depth, pH (6.0-7.5 ideal), nutrients, drainage\n• Planting distance: Apple/pear 6-8m, peach/cherry 4-5m, dwarf 2-3m\n• Sapling quality: Certified, 2-3 years old, well-rooted, disease-free\n• Planting time: Autumn (November-December) or Spring (March-April)\n• Irrigation: Drip or mini-sprinkler system should be installed\n• Soil preparation: Deep tillage, drainage channels, marking\n• Fence/perimeter: For wind protection and security\n\nGood start means 20-30 years of productivity. Don\'t rush, make a plan.'
            },
            {
                'icon': '✂️',
                'title': 'Pruning Techniques',
                'info': '15-25% yield increase',
                'content': '• Young tree (1-5 years): Shaping pruning, skeleton formation\n• Productive age (5-20 years): Yield increase pruning, ensuring light penetration\n• Old tree: Rejuvenation pruning, removing old branches\n• Timing: Dormant period (November-March), air temperature above 10°C\n• Pruning shapes: Vase, goblet, spindle form\n• Tools: Disinfected saw, shears, grafting knife\n• After pruning: Apply paste to wounds\n\nCorrect pruning guarantees 15-25% yield increase and quality fruit.'
            },
            {
                'icon': '🍃',
                'title': 'Fertilization',
                'info': 'Quality fruit, longer shelf',
                'content': '• Spring (March-April): Nitrogen (N) focused, growth period\n• Summer (May-June): Potassium (K) supplementation, fruit development\n• Autumn (October-November): Phosphorus (P) and organic fertilizer, winter preparation\n• Soil analysis: Once a year, prevents unnecessary fertilizer use\n• Micro elements: Iron (Fe), zinc (Zn), boron (B) through foliar fertilization\n• Organic fertilizer: Manure (autumn), compost, worm castings\n• Fertilizer amount: Varies according to tree age and size\n\nBalanced nutrition provides quality fruit, taste, and extended shelf life.'
            },
            {
                'icon': '🐛',
                'title': 'Pest Control',
                'info': '30-40% yield loss prevention',
                'content': '• Winter control (December-February): Agricultural oil (mineral oil), overwintering pests\n• Spring (March-April): Fungicides, flowering period diseases\n• Summer (May-August): Insecticides, leaf diseases\n• Growth monitoring: Weekly checks, trap usage\n• Biological control: Beneficial insect release, pheromone traps\n• Integrated control: Environmentally friendly, residue-free production\n• Treatment records: Note all applications\n\nTimely intervention prevents 30-40% yield loss and improves product quality.'
            },
            {
                'icon': '🍎',
                'title': 'Popular Species',
                'info': '15-20 ton/decare',
                'content': '• Apple: 15-20 ton/decare, winter hardy, various climates, long shelf life\n• Plum: 8-12 ton/decare, early yield (3rd year), wide market\n• Peach: 10-15 ton/decare, warm regions, export potential\n• Cherry: High value, high export value, early yield\n• Apricot: Drought tolerant, Malatya is the apricot city, processing industry\n• Olive: 4-6 ton/decare, very drought tolerant, high margin\n• Walnut/Almond: Long-term investment, value-added\n\nChoose according to your region\'s climate, market, and water resources.'
            },
            {
                'icon': '📦',
                'title': 'Harvest & Marketing',
                'info': '70% waste reduction',
                'content': '• Harvest time: Determined by color, taste, firmness values\n• Harvest method: Hand picking, without damage, using baskets-crates\n• Storage: Cold storage (1-4°C, 85-90% humidity)\n• Packaging: Labeling, branding, quality classification\n• Marketing channels: Wholesale, retail, export, online sales\n• Valuation: Good packaging provides 20-30% price increase\n• Tracking: Sales records, cost analysis, profit margin\n\nPlanned harvest and storage reduces waste loss by 70%.'
            },
            {
                'icon': '🌱',
                'title': 'Pollination & Fruit Set',
                'info': 'Maximize fruit production',
                'content': 'POLLINATION METHODS:\n\nNATURAL POLLINATION:\n• Bees: Most effective (honeybees, bumblebees)\n• Wind pollination (some species)\n• Attract pollinators with flowering plants\n• Avoid pesticides during flowering\n\nHAND POLLINATION:\n• For greenhouse production\n• Use soft brush or cotton swab\n• Transfer pollen between flowers\n• Time: Early morning (pollen most viable)\n\nPOLLINATOR MANAGEMENT:\n• Maintain bee hives (1-2 hives per hectare)\n• Provide water sources\n• Plant pollinator-friendly flowers\n• Avoid harmful pesticides\n\nFRUIT SET OPTIMIZATION:\n• Ensure adequate pollination\n• Maintain proper temperature during flowering\n• Avoid water stress during bloom\n• Apply boron (improves fruit set)\n• Thinning: Remove excess fruits for quality\n\nCOMMON ISSUES:\n• Poor fruit set: Inadequate pollination\n• Small fruits: Too many fruits, insufficient thinning\n• Misshapen fruits: Poor pollination or nutrient imbalance\n• Drop: Water stress, nutrient deficiency\n\nTIPS:\n• Monitor pollinator activity\n• Supplement with hand pollination if needed\n• Maintain optimal conditions during flowering'
            },
            {
                'icon': '📈',
                'title': 'Yield Optimization',
                'info': 'Maximize production efficiency',
                'content': 'YIELD FACTORS:\n\nGENETIC FACTORS:\n• Choose high-yielding varieties\n• Disease-resistant cultivars\n• Climate-adapted varieties\n• Certified planting material\n\nENVIRONMENTAL MANAGEMENT:\n• Optimal temperature control\n• Proper light exposure\n• Adequate water supply\n• Good air circulation\n• CO2 enrichment (greenhouses)\n\nNUTRITION MANAGEMENT:\n• Balanced fertilization program\n• Foliar feeding (quick nutrient uptake)\n• Micronutrient supplementation\n• Soil pH optimization\n• Regular soil testing\n\nCROP MANAGEMENT:\n• Proper spacing (avoid overcrowding)\n• Timely pruning\n• Pest and disease control\n• Weed management\n• Support systems (trellising)\n\nTECHNOLOGY:\n• Precision agriculture tools\n• Sensor-based monitoring\n• Automated systems\n• Data-driven decisions\n• Performance tracking\n\nEXPECTED YIELDS:\n• Apple: 15-25 ton/decare (commercial orchards)\n• Peach: 12-18 ton/decare\n• Cherry: 8-12 ton/decare\n• Apricot: 10-15 ton/decare\n• Plum: 10-15 ton/decare\n\nOPTIMIZATION TIPS:\n• Keep detailed records\n• Analyze yield data\n• Identify limiting factors\n• Continuous improvement\n• Benchmark against best practices'
            },
            {
                'icon': '🔬',
                'title': 'Post-Harvest Technology',
                'info': 'Preserve quality and value',
                'content': 'COLD STORAGE:\n\nTEMPERATURE CONTROL:\n• Apples: 0-4°C (long-term storage)\n• Stone fruits: 0-2°C\n• Berries: 0-1°C\n• Citrus: 4-8°C\n• Controlled atmosphere (CA) storage\n\nHUMIDITY MANAGEMENT:\n• Optimal: 85-95% relative humidity\n• Prevents shriveling\n• Maintains freshness\n• Reduces weight loss\n\nCONTROLLED ATMOSPHERE (CA):\n• Reduced oxygen (2-3%)\n• Increased CO2 (1-5%)\n• Extends storage life by 2-3x\n• Maintains quality\n• Investment: Higher cost, better returns\n\nPACKAGING:\n• Modified atmosphere packaging (MAP)\n• Protective packaging\n• Proper ventilation\n• Labeling and traceability\n• Branding and marketing\n\nPROCESSING:\n• Sorting and grading\n• Washing and sanitizing\n• Waxing (apples, citrus)\n• Quality control\n• Value-added products\n\nTRANSPORTATION:\n• Refrigerated transport\n• Proper handling\n• Minimize damage\n• Quick delivery\n• Cold chain maintenance\n\nQUALITY STANDARDS:\n• Size and color grading\n• Brix (sugar content)\n• Firmness testing\n• Defect tolerance\n• Certification programs\n\nBENEFITS:\n• Extended shelf life\n• Reduced waste (70% reduction)\n• Higher market prices\n• Export opportunities\n• Year-round availability'
            }
        ]
        
        # Create cards in grid
        for i, fruit in enumerate(fruits):
            row = i // 3
            col = i % 3
            card = self.create_icon_card(
                cards_container,
                fruit['icon'],
                fruit['title'],
                fruit['info'],
                fruit['content']
            )
            card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")
        
        # Configure grid weights
        for i in range(3):
            cards_container.grid_columnconfigure(i, weight=1)
    
    def build_irrigation_tab(self, parent):
        """Build irrigation and water management tab with icon cards"""
        canvas = tk.Canvas(parent, bg='#ECEFF1', highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#ECEFF1')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Header
        header = tk.Frame(scrollable_frame, bg='#ECEFF1')
        header.pack(fill=tk.X, padx=20, pady=(20, 30))
        tk.Label(header, text="💧 Professional Irrigation & Water Management",
                font=("Segoe UI", 18, "bold"), bg='#ECEFF1', fg='#0277BD').pack()
        tk.Label(header, text="Modern techniques for efficient water use and optimal crop growth",
                font=("Segoe UI", 10), bg='#ECEFF1', fg='#616161').pack(pady=(5, 0))
        
        # Icon cards container
        cards_container = tk.Frame(scrollable_frame, bg='#ECEFF1')
        cards_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)
        
        # Irrigation cards data
        irrigation = [
            {
                'icon': '💧',
                'title': 'Drip Irrigation',
                'info': 'Most efficient method',
                'content': 'ADVANTAGES:\n• 60-70% water savings vs traditional methods\n• Precise water delivery to root zone\n• Reduces weed growth (dry between rows)\n• Prevents leaf wetting (reduces disease)\n• Can apply fertilizers (fertigation)\n• Works on slopes and irregular terrain\n\nSYSTEM COMPONENTS:\n• Main line (PVC or PE pipe)\n• Drip lines (emitters every 30-50 cm)\n• Filters (prevent clogging)\n• Pressure regulators\n• Valves and controllers\n\nINSTALLATION:\n• Spacing: 50-100 cm between lines\n• Emitter flow: 2-4 L/hour\n• Operating pressure: 1-2 bar\n• Filter mesh: 120-200 microns\n\nMAINTENANCE:\n• Regular filter cleaning\n• Flush lines monthly\n• Check emitters for clogging\n• Monitor pressure\n\nCOST: 15,000-30,000 TL per decare (pays back in 2-3 years)'
            },
            {
                'icon': '🌡️',
                'title': 'Soil Moisture Monitoring',
                'info': 'Real-time sensor technology',
                'content': 'SENSOR TYPES:\n\nTENSIONMETERS:\n• Measures soil water tension\n• Range: 0-100 centibars\n• Best for: Field crops\n• Installation: Root zone depth\n\nCAPACITANCE SENSORS:\n• Measures volumetric water content\n• Range: 0-100%\n• Best for: All soil types\n• Installation: Multiple depths\n\nTIME DOMAIN REFLECTOMETRY (TDR):\n• Most accurate\n• Measures soil moisture and EC\n• Best for: Research and precision agriculture\n• Cost: Higher investment\n\nAUTOMATIC SYSTEMS:\n• Real-time data logging\n• Mobile app monitoring\n• Automated irrigation triggers\n• Weather integration\n• Cloud-based analytics\n\nOPTIMAL MOISTURE LEVELS:\n• Field capacity: 100% (after irrigation)\n• Optimal range: 50-80% of field capacity\n• Wilting point: 20-30% (irrigation needed)\n• Monitor at multiple depths (15, 30, 60 cm)\n\nBENEFITS:\n• Prevent over/under irrigation\n• Improve water use efficiency\n• Increase yield by 15-25%\n• Reduce disease risk'
            },
            {
                'icon': '⏰',
                'title': 'Irrigation Scheduling',
                'info': 'When and how much to irrigate',
                'content': 'SCHEDULING METHODS:\n\nSOIL MOISTURE-BASED:\n• Monitor soil moisture sensors\n• Irrigate when moisture drops below threshold\n• Most accurate method\n• Prevents water stress\n\nEVAPOTRANSPIRATION (ET):\n• Calculate crop water needs\n• ET = Evaporation + Transpiration\n• Use weather station data\n• Adjust for crop growth stage\n\nCROP COEFFICIENT METHOD:\n• ETc = ETo × Kc\n• ETo: Reference evapotranspiration\n• Kc: Crop coefficient (varies by stage)\n• Stage-specific water needs\n\nTIMING:\n• Early morning (4-8 AM): Best time\n• Avoid midday (high evaporation)\n• Avoid evening (disease risk)\n• Frequency: 2-3 times per week (summer)\n\nWATER REQUIREMENTS BY CROP:\n• Wheat: 400-600 mm/season\n• Corn: 500-800 mm/season\n• Sunflower: 400-600 mm/season\n• Cotton: 600-900 mm/season\n• Barley: 350-550 mm/season\n\nSIGNS OF WATER STRESS:\n• Wilting leaves\n• Slow growth\n• Reduced yield\n• Premature maturity'
            },
            {
                'icon': '🌊',
                'title': 'Water Quality Management',
                'info': 'Ensure optimal water quality',
                'content': 'WATER QUALITY PARAMETERS:\n\npH LEVEL:\n• Optimal: 6.0-7.5\n• Too acidic (<5.5): Add lime\n• Too alkaline (>8.0): Add acid\n• Affects nutrient availability\n\nELECTRICAL CONDUCTIVITY (EC):\n• Measures total dissolved salts\n• Optimal: 0.5-2.0 dS/m\n• High EC (>3.0): Salinity problem\n• Leaching may be needed\n\nTOTAL DISSOLVED SOLIDS (TDS):\n• Optimal: <500 ppm\n• High TDS: Can cause salt buildup\n• Monitor regularly\n\nHARDNESS:\n• Calcium and magnesium content\n• Can cause emitter clogging\n• Use softeners if needed\n\nBIOLOGICAL CONTAMINANTS:\n• Test for bacteria, algae\n• Use filters and UV treatment\n• Prevent biofilm formation\n\nTREATMENT METHODS:\n• Filtration (sand, screen, disc filters)\n• Chemical treatment (chlorine)\n• UV sterilization\n• Reverse osmosis (high salinity)\n\nTESTING:\n• Test water source annually\n• More frequent if problems occur\n• Use certified laboratories\n• Keep records'
            },
            {
                'icon': '💾',
                'title': 'Water Conservation',
                'info': 'Sustainable water management',
                'content': 'CONSERVATION STRATEGIES:\n\nMULCHING:\n• Organic mulch (straw, compost)\n• Plastic mulch (vegetables)\n• Reduces evaporation by 30-50%\n• Maintains soil temperature\n• Suppresses weeds\n\nCOVER CROPS:\n• Reduce soil erosion\n• Improve water infiltration\n• Add organic matter\n• Protect soil structure\n\nSOIL MANAGEMENT:\n• Increase organic matter (improves water retention)\n• Reduce tillage (conserves moisture)\n• Improve soil structure\n• Use compost and organic amendments\n\nIRRIGATION EFFICIENCY:\n• Use drip or sprinkler systems\n• Maintain equipment properly\n• Fix leaks immediately\n• Schedule irrigation optimally\n• Use automation systems\n\nRAINWATER HARVESTING:\n• Collect from greenhouse roofs\n• Storage tanks (underground or aboveground)\n• Use for irrigation\n• Reduces water costs\n\nWATER RECYCLING:\n• Collect and reuse runoff\n• Treat if necessary\n• Greenhouse condensate collection\n• Closed-loop systems\n\nBENEFITS:\n• 30-50% water savings\n• Reduced costs\n• Environmental sustainability\n• Better crop quality\n• Improved soil health'
            },
            {
                'icon': '📊',
                'title': 'Smart Irrigation Systems',
                'info': 'IoT and automation technology',
                'content': 'AUTOMATED SYSTEMS:\n\nSENSOR-BASED AUTOMATION:\n• Soil moisture sensors trigger irrigation\n• Weather station integration\n• Evapotranspiration calculations\n• Automatic scheduling\n• Remote monitoring and control\n\nMOBILE APPLICATIONS:\n• Real-time monitoring\n• Remote control from smartphone\n• Alerts and notifications\n• Data logging and analysis\n• Historical trends\n\nCLOUD-BASED ANALYTICS:\n• Data storage and backup\n• Advanced analytics\n• Predictive irrigation\n• Crop water use modeling\n• Performance reports\n\nINTEGRATION FEATURES:\n• Weather forecast integration\n• Crop growth stage tracking\n• Fertilizer application (fertigation)\n• Multiple zone control\n• Scheduling optimization\n\nBENEFITS:\n• 40-60% water savings\n• Labor reduction\n• Improved crop quality\n• Better yield consistency\n• Data-driven decisions\n\nINVESTMENT:\n• Basic system: 5,000-10,000 TL per decare\n• Advanced system: 15,000-25,000 TL per decare\n• ROI: 2-3 years through water and labor savings\n\nFUTURE TRENDS:\n• AI-powered irrigation\n• Satellite imagery integration\n• Drone monitoring\n• Machine learning optimization'
            }
        ]
        
        # Create cards in grid
        for i, item in enumerate(irrigation):
            row = i // 3
            col = i % 3
            card = self.create_icon_card(
                cards_container,
                item['icon'],
                item['title'],
                item['info'],
                item['content']
            )
            card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")
        
        # Configure grid weights
        for i in range(3):
            cards_container.grid_columnconfigure(i, weight=1)