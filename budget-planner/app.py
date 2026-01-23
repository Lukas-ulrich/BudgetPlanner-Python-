import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog

from calculations import *
from data_manager import *

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import json
import os
import csv
from datetime import datetime, timedelta
from collections import defaultdict
import re
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np

# ------------------------------
# Konfiguration / Standard-Daten
# ------------------------------

    "Einnahmen": {
        "Gehalt": ["Gehalt Hauptjob", "Nebentätigkeit"],
        "Sonstiges": ["Geschenke", "Verkauf"]
    },
    "Fixkosten": {
        "Wohnen": ["Miete", "Strom", "Wasser"],
        "Versicherungen": ["Krankenversicherung", "Hausrat"]
    },
    "Variable Kosten": {
        "Essen": ["Supermarkt", "Restaurant"],
        "Freizeit": ["Abos", "Urlaub", "Kino"]
    },
    "Sparen": {
        "Ziele": ["Notgroschen", "Urlaub", "Rente"]
    }
}





# ------------------------------
# Hilfsfunktionen
# ------------------------------













# ------------------------------
# Hauptklasse / App
# ------------------------------
class BudgetApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BudgetPlanner Pro – Kostenrechner")
        self.root.geometry("1400x800")
        
        # Theme & Settings
        self.dark_mode = tk.BooleanVar(value=True)
        self.auto_fill_enabled = tk.BooleanVar(value=True)
        self.budget_warnings = {}
        
        self.structure = DEFAULT_STRUCTURE.copy()
        self.data = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))

        # UI-Variablen
        self.current_month = tk.StringVar(value=datetime.now().strftime("%Y-%m"))
        self.saving_note = tk.StringVar(value="")
        self.savings_goal = tk.StringVar(value="0")
        self.labels_by_item = {}
        self.totals_per_category = {}
        self.delete_mode = tk.BooleanVar(value=False)
        self.current_profile = tk.StringVar(value=DEFAULT_PROFILE)

        ensure_dir(profile_folder(DEFAULT_PROFILE))
        self.load_settings()
        
        self.apply_theme()
        self.build_ui()
        self.load_month(self.current_month.get())
        self.recalculate_all()

    def apply_theme(self):
        """Wendet Dark/Light Theme an"""
        if self.dark_mode.get():
            self.colors = {
                'bg': '#1a1a1a',
                'bg_secondary': '#252526',
                'bg_tertiary': '#2d2d30',
                'bg_input': '#3e3e42',
                'fg': 'white',
                'fg_secondary': '#e0e0e0',
                'fg_muted': '#b0b0b0',
                'accent': '#0078d4',
                'success': '#107c10',
                'danger': '#d13438',
                'warning': '#ffd700'
            }
        else:
            self.colors = {
                'bg': '#f5f5f5',
                'bg_secondary': '#ffffff',
                'bg_tertiary': '#e8e8e8',
                'bg_input': '#ffffff',
                'fg': '#000000',
                'fg_secondary': '#333333',
                'fg_muted': '#666666',
                'accent': '#0078d4',
                'success': '#107c10',
                'danger': '#d13438',
                'warning': '#ff8c00'
            }
        
        self.root.configure(bg=self.colors['bg'])

    def toggle_theme(self):
        """Wechselt zwischen Dark und Light Mode - OHNE Datenverlust"""
        self.dark_mode.set(not self.dark_mode.get())
        self.save_settings()
        
        # Speichere aktuellen Monat bevor UI neu aufgebaut wird
        current_values = {}
        for (mc, sc, item), refs in self.labels_by_item.items():
            current_values[(mc, sc, item)] = {
                "amt": refs["amt"].get(),
                "note": refs["note"].get()
            }
        
        # Theme anwenden und UI neu bauen
        self.apply_theme()
        for widget in self.root.winfo_children():
            widget.destroy()
        self.build_ui()
        
        # Daten wiederherstellen
        for (mc, sc, item), refs in self.labels_by_item.items():
            if (mc, sc, item) in current_values:
                refs["amt"].set(current_values[(mc, sc, item)]["amt"])
                refs["note"].set(current_values[(mc, sc, item)]["note"])
        
        self.recalculate_all()

    def load_settings(self):
        """Lädt App-Einstellungen"""
        settings_path = os.path.join(BASE_FOLDER, SETTINGS_FILE)
        if os.path.exists(settings_path):
            try:
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    self.dark_mode.set(settings.get('dark_mode', True))
                    self.auto_fill_enabled.set(settings.get('auto_fill', True))
                    self.budget_warnings = settings.get('budget_warnings', {})
                    if 'structure' in settings:
                        self.structure = settings['structure']
            except:
                pass

    def save_settings(self):
        """Speichert App-Einstellungen"""
        settings_path = os.path.join(BASE_FOLDER, SETTINGS_FILE)
        ensure_dir(BASE_FOLDER)
        settings = {
            'dark_mode': self.dark_mode.get(),
            'auto_fill': self.auto_fill_enabled.get(),
            'budget_warnings': self.budget_warnings,
            'structure': self.structure
        }
        try:
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        except:
            pass

    # ------------------------------
    # UI Aufbau
    # ------------------------------
    def build_ui(self):
        # Topbar
        top_frame = tk.Frame(self.root, bg=self.colors['bg_tertiary'], height=60)
        top_frame.pack(fill="x", padx=0, pady=0)
        
        # Linke Seite: Monat
        left_top = tk.Frame(top_frame, bg=self.colors['bg_tertiary'])
        left_top.pack(side="left", padx=15, pady=10)
        
        tk.Label(left_top, text="📅 Monat:", bg=self.colors['bg_tertiary'], 
                fg=self.colors['fg_secondary'], font=("Segoe UI", 11, "bold")).pack(side="left", padx=(0,8))
        month_entry = tk.Entry(left_top, textvariable=self.current_month, width=10, font=("Segoe UI", 11), 
                              bg=self.colors['bg_input'], fg=self.colors['fg'], 
                              insertbackground=self.colors['fg'], relief="flat", borderwidth=2)
        month_entry.pack(side="left", padx=5)
        
        # Navigation buttons
        self.create_button(left_top, "◀", lambda: self.navigate_month(-1), self.colors['accent'], width=3).pack(side="left", padx=2)
        self.create_button(left_top, "▶", lambda: self.navigate_month(1), self.colors['accent'], width=3).pack(side="left", padx=2)
        
        self.create_button(left_top, "📂 Laden", self.on_load_click, self.colors['accent']).pack(side="left", padx=3)
        self.create_button(left_top, "💾 Speichern", self.on_save_click, self.colors['success']).pack(side="left", padx=3)

        # Mitte: Quick Actions
        mid_top = tk.Frame(top_frame, bg=self.colors['bg_tertiary'])
        mid_top.pack(side="left", padx=20)
        
        self.create_button(mid_top, "🔄 Auto-Fill", self.auto_fill_fixed, "#5c2d91").pack(side="left", padx=3)
        self.create_button(mid_top, "⚙️ Budget-Limits", self.set_budget_limits, "#ff8c00").pack(side="left", padx=3)
        self.create_button(mid_top, "📥 CSV Import", self.import_bank_csv, "#ca5010").pack(side="left", padx=3)

        # Rechte Seite: Actions
        right_top = tk.Frame(top_frame, bg=self.colors['bg_tertiary'])
        right_top.pack(side="right", padx=15, pady=10)
        
        theme_icon = "🌙" if self.dark_mode.get() else "☀️"
        self.create_button(right_top, theme_icon, self.toggle_theme, "#5c2d91", width=3).pack(side="left", padx=3)
        
        self.create_button(right_top, "📄 PDF", self.export_pdf, "#ca5010").pack(side="left", padx=3)
        self.create_button(right_top, "📊 CSV", self.export_csv, "#107c10").pack(side="left", padx=3)
        
        # Löschmodus Toggle
        delete_check = tk.Checkbutton(
            right_top,
            text="🗑️ Löschmodus",
            variable=self.delete_mode,
            bg=self.colors['bg_tertiary'],
            fg=self.colors['danger'],
            selectcolor=self.colors['bg_tertiary'],
            activebackground=self.colors['bg_tertiary'],
            activeforeground=self.colors['danger'],
            font=("Segoe UI", 10, "bold"),
            command=self.toggle_delete_mode
        )
        delete_check.pack(side="left", padx=8)

        # Main area mit Tabs
        main_frame = tk.Frame(self.root, bg=self.colors['bg'])
        main_frame.pack(fill="both", expand=True, padx=0, pady=0)

        # Notebook für Tabs
        style = ttk.Style()
        style.theme_use('default')
        style.configure('TNotebook', background=self.colors['bg'], borderwidth=0)
        style.configure('TNotebook.Tab', background=self.colors['bg_tertiary'], 
                       foreground=self.colors['fg'], padding=[20, 10])
        style.map('TNotebook.Tab', background=[('selected', self.colors['accent'])])
        
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Tab 1: Budget-Eingabe
        self.budget_tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(self.budget_tab, text="💰 Budget-Eingabe")
        
        # Tab 2: Monatsvergleich
        self.stats_tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(self.stats_tab, text="📊 Monatsvergleich")
        
        # Tab 3: Jahresübersicht
        self.year_tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(self.year_tab, text="📅 Jahresübersicht")
        
        # Tab 4: Trends & Prognosen
        self.trends_tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(self.trends_tab, text="📈 Trends & Prognosen")

        self.build_budget_tab()
        self.build_stats_tab()
        self.build_year_tab()
        self.build_trends_tab()

    def build_budget_tab(self):
        """Erstellt das Budget-Eingabe Tab"""
        # Left side: Categories
        left = tk.Frame(self.budget_tab, bg=self.colors['bg'])
        left.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        # Right side: Summary
        right = tk.Frame(self.budget_tab, bg=self.colors['bg_secondary'])
        right.pack(side="right", fill="y", padx=(0,10), pady=10)

        # Scrollable canvas
        canvas = tk.Canvas(left, bg=self.colors['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(left, orient="vertical", command=canvas.yview)
        self.cat_frame = tk.Frame(canvas, bg=self.colors['bg'])
        self.cat_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0,0), window=self.cat_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        self.build_categories_ui()

        # Right panel: summary
        right_inner = tk.Frame(right, bg=self.colors['bg_secondary'], width=340)
        right_inner.pack(fill="both", expand=True, padx=15, pady=15)
        right_inner.pack_propagate(False)

        # Header
        header = tk.Frame(right_inner, bg=self.colors['bg_tertiary'], height=50)
        header.pack(fill="x", pady=(0,15))
        tk.Label(header, text="📊 Finanzübersicht", bg=self.colors['bg_tertiary'], 
                fg=self.colors['fg'], font=("Segoe UI", 14, "bold")).pack(pady=12)

        # Statistik Cards
        self.create_stat_card(right_inner, "💰 Gesamteinnahmen", "0.00 €", self.colors['success'], "income_label")
        self.create_stat_card(right_inner, "💸 Gesamtausgaben", "0.00 €", self.colors['danger'], "expense_label")
        
        # Saldo Card
        saldo_card = tk.Frame(right_inner, bg=self.colors['bg_tertiary'], relief="flat", borderwidth=0)
        saldo_card.pack(fill="x", pady=8)
        tk.Label(saldo_card, text="💵 Saldo", bg=self.colors['bg_tertiary'], 
                fg=self.colors['fg_muted'], font=("Segoe UI", 10)).pack(anchor="w", padx=12, pady=(10,2))
        self.balance_label = tk.Label(saldo_card, text="0.00 €", bg=self.colors['bg_tertiary'], 
                                     fg=self.colors['fg'], font=("Segoe UI", 18, "bold"))
        self.balance_label.pack(anchor="w", padx=12, pady=(0,10))

        # Sparziel
        ttk.Separator(right_inner, orient="horizontal").pack(fill="x", pady=15)
        
        goal_frame = tk.Frame(right_inner, bg=self.colors['bg_secondary'])
        goal_frame.pack(fill="x", pady=5)
        tk.Label(goal_frame, text="🎯 Monatliches Sparziel", bg=self.colors['bg_secondary'], 
                fg=self.colors['fg_secondary'], font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0,8))
        
        goal_entry = tk.Entry(goal_frame, textvariable=self.savings_goal, font=("Segoe UI", 11),
                            bg=self.colors['bg_input'], fg=self.colors['fg'], 
                            insertbackground=self.colors['fg'], relief="flat", borderwidth=2)
        goal_entry.pack(fill="x", pady=3)
        goal_entry.bind("<KeyRelease>", lambda e: self.recalculate_all())
        
        self.savings_progress = tk.Label(goal_frame, text="Fortschritt: 0 / 0 (0%)", 
                                        bg=self.colors['bg_secondary'], fg=self.colors['fg_muted'], 
                                        font=("Segoe UI", 9))
        self.savings_progress.pack(anchor="w", pady=5)

        # Top-3
        ttk.Separator(right_inner, orient="horizontal").pack(fill="x", pady=15)
        tk.Label(right_inner, text="🔝 Top-3 Ausgaben", bg=self.colors['bg_secondary'], 
                fg=self.colors['fg_secondary'], font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0,10))
        
        self.top3_boxes = []
        for i in range(3):
            box = tk.Frame(right_inner, bg=self.colors['bg_tertiary'], relief="flat")
            box.pack(fill="x", pady=3)
            lbl = tk.Label(box, text=f"{i+1}. -", bg=self.colors['bg_tertiary'], 
                          fg=self.colors['fg_secondary'], font=("Segoe UI", 9), anchor="w")
            lbl.pack(padx=10, pady=6, fill="x")
            self.top3_boxes.append(lbl)

        # Zusatzinfos
        ttk.Separator(right_inner, orient="horizontal").pack(fill="x", pady=15)
        
        info_frame = tk.Frame(right_inner, bg=self.colors['bg_secondary'])
        info_frame.pack(fill="x")
        
        self.saving_rate_label = tk.Label(info_frame, text="📈 Sparquote: 0.0 %", 
                                         bg=self.colors['bg_secondary'], fg=self.colors['fg_secondary'], 
                                         font=("Segoe UI", 9))
        self.saving_rate_label.pack(anchor="w", pady=3)
        
        self.fixed_var_label = tk.Label(info_frame, text="🔒 Fixkosten: 0.00 €", 
                                       bg=self.colors['bg_secondary'], fg=self.colors['fg_secondary'], 
                                       font=("Segoe UI", 9))
        self.fixed_var_label.pack(anchor="w", pady=3)
        
        self.variable_var_label = tk.Label(info_frame, text="🔄 Variable Kosten: 0.00 €", 
                                          bg=self.colors['bg_secondary'], fg=self.colors['fg_secondary'], 
                                          font=("Segoe UI", 9))
        self.variable_var_label.pack(anchor="w", pady=3)

    def build_stats_tab(self):
        """Erstellt das Monatsvergleich-Tab"""
        controls = tk.Frame(self.stats_tab, bg=self.colors['bg'])
        controls.pack(fill="x", padx=20, pady=10)
        
        tk.Label(controls, text="Vergleichsmonate:", bg=self.colors['bg'], 
                fg=self.colors['fg'], font=("Segoe UI", 11, "bold")).pack(side="left", padx=10)
        
        self.comparison_months = tk.StringVar(value="6")
        ttk.Spinbox(controls, from_=1, to=12, textvariable=self.comparison_months, 
                   width=5).pack(side="left", padx=5)
        
        self.create_button(controls, "🔄 Aktualisieren", self.update_charts, 
                          self.colors['accent']).pack(side="left", padx=10)

        # Charts container
        charts_frame = tk.Frame(self.stats_tab, bg=self.colors['bg'])
        charts_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Create matplotlib figures
        self.fig1 = Figure(figsize=(6, 4), facecolor=self.colors['bg'])
        self.fig2 = Figure(figsize=(6, 4), facecolor=self.colors['bg'])
        
        # Chart 1: Monatlicher Verlauf
        self.chart1_frame = tk.Frame(charts_frame, bg=self.colors['bg'])
        self.chart1_frame.pack(side="left", fill="both", expand=True, padx=5)
        
        tk.Label(self.chart1_frame, text="📈 Monatlicher Verlauf", bg=self.colors['bg'], 
                fg=self.colors['fg'], font=("Segoe UI", 12, "bold")).pack(pady=5)
        
        self.canvas1 = FigureCanvasTkAgg(self.fig1, self.chart1_frame)
        self.canvas1.get_tk_widget().pack(fill="both", expand=True)
        
        # Chart 2: Kategorien-Verteilung
        self.chart2_frame = tk.Frame(charts_frame, bg=self.colors['bg'])
        self.chart2_frame.pack(side="right", fill="both", expand=True, padx=5)
        
        tk.Label(self.chart2_frame, text="🥧 Ausgaben-Verteilung", bg=self.colors['bg'], 
                fg=self.colors['fg'], font=("Segoe UI", 12, "bold")).pack(pady=5)
        
        self.canvas2 = FigureCanvasTkAgg(self.fig2, self.chart2_frame)
        self.canvas2.get_tk_widget().pack(fill="both", expand=True)

    def build_year_tab(self):
        """Erstellt das Jahresübersicht-Tab"""
        controls = tk.Frame(self.year_tab, bg=self.colors['bg'])
        controls.pack(fill="x", padx=20, pady=10)
        
        tk.Label(controls, text="Jahr:", bg=self.colors['bg'], 
                fg=self.colors['fg'], font=("Segoe UI", 11, "bold")).pack(side="left", padx=10)
        
        self.year_select = tk.StringVar(value=str(datetime.now().year))
        ttk.Spinbox(controls, from_=2000, to=2100, textvariable=self.year_select, 
                   width=6).pack(side="left", padx=5)
        
        self.create_button(controls, "🔄 Laden", self.update_year_overview, 
                          self.colors['accent']).pack(side="left", padx=10)

        # Statistik-Bereich
        stats_frame = tk.Frame(self.year_tab, bg=self.colors['bg_secondary'])
        stats_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Summary Cards
        summary = tk.Frame(stats_frame, bg=self.colors['bg_secondary'])
        summary.pack(fill="x", pady=10)
        
        self.year_income_label = tk.Label(summary, text="Jahreseinnahmen: 0.00 €", 
                                          bg=self.colors['bg_secondary'], fg=self.colors['success'],
                                          font=("Segoe UI", 14, "bold"))
        self.year_income_label.pack(pady=5)
        
        self.year_expense_label = tk.Label(summary, text="Jahresausgaben: 0.00 €", 
                                           bg=self.colors['bg_secondary'], fg=self.colors['danger'],
                                           font=("Segoe UI", 14, "bold"))
        self.year_expense_label.pack(pady=5)
        
        self.year_balance_label = tk.Label(summary, text="Jahressaldo: 0.00 €", 
                                           bg=self.colors['bg_secondary'], fg=self.colors['accent'],
                                           font=("Segoe UI", 16, "bold"))
        self.year_balance_label.pack(pady=10)
        
        # Durchschnittswerte
        ttk.Separator(stats_frame).pack(fill="x", pady=10)
        
        avg_frame = tk.Frame(stats_frame, bg=self.colors['bg_secondary'])
        avg_frame.pack(fill="x", pady=10)
        
        tk.Label(avg_frame, text="📊 Durchschnittswerte (Monat)", bg=self.colors['bg_secondary'],
                fg=self.colors['fg'], font=("Segoe UI", 12, "bold")).pack(pady=5)
        
        self.avg_income_label = tk.Label(avg_frame, text="Ø Einnahmen: 0.00 €", 
                                         bg=self.colors['bg_secondary'], fg=self.colors['fg_secondary'],
                                         font=("Segoe UI", 11))
        self.avg_income_label.pack(pady=3)
        
        self.avg_expense_label = tk.Label(avg_frame, text="Ø Ausgaben: 0.00 €", 
                                          bg=self.colors['bg_secondary'], fg=self.colors['fg_secondary'],
                                          font=("Segoe UI", 11))
        self.avg_expense_label.pack(pady=3)
        
        self.avg_balance_label = tk.Label(avg_frame, text="Ø Saldo: 0.00 €", 
                                          bg=self.colors['bg_secondary'], fg=self.colors['fg_secondary'],
                                          font=("Segoe UI", 11))
        self.avg_balance_label.pack(pady=3)
        
        # Chart
        self.fig_year = Figure(figsize=(10, 5), facecolor=self.colors['bg'])
        self.canvas_year = FigureCanvasTkAgg(self.fig_year, stats_frame)
        self.canvas_year.get_tk_widget().pack(fill="both", expand=True, pady=10)

    def build_trends_tab(self):
        """Erstellt das Trends & Prognosen-Tab"""
        controls = tk.Frame(self.trends_tab, bg=self.colors['bg'])
        controls.pack(fill="x", padx=20, pady=10)
        
        tk.Label(controls, text="🔮 Prognose für nächste Monate:", bg=self.colors['bg'], 
                fg=self.colors['fg'], font=("Segoe UI", 11, "bold")).pack(side="left", padx=10)
        
        self.forecast_months = tk.StringVar(value="3")
        ttk.Spinbox(controls, from_=1, to=6, textvariable=self.forecast_months, 
                   width=5).pack(side="left", padx=5)
        
        self.create_button(controls, "🔄 Berechnen", self.update_trends, 
                          self.colors['accent']).pack(side="left", padx=10)

        # Info-Text
        info = tk.Label(self.trends_tab, 
                       text="Basierend auf den letzten 6 Monaten wird ein Trend berechnet.",
                       bg=self.colors['bg'], fg=self.colors['fg_muted'], 
                       font=("Segoe UI", 9, "italic"))
        info.pack(pady=5)

        # Charts
        self.fig_trend = Figure(figsize=(12, 6), facecolor=self.colors['bg'])
        self.canvas_trend = FigureCanvasTkAgg(self.fig_trend, self.trends_tab)
        self.canvas_trend.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=10)

    def create_button(self, parent, text, command, color, width=None):
        """Erstellt einen styled Button"""
        btn = tk.Button(parent, text=text, command=command, bg=color, fg="white",
                       font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2",
                       padx=12, pady=6, borderwidth=0)
        if width:
            btn.config(width=width)
        
        def on_enter(e):
            btn.config(bg=self.lighten_color(color))
        def on_leave(e):
            btn.config(bg=color)
        
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    def lighten_color(self, color):
        """Hellt eine Farbe auf"""
        color = color.lstrip('#')
        r, g, b = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        r = min(255, r + 20)
        g = min(255, g + 20)
        b = min(255, b + 20)
        return f'#{r:02x}{g:02x}{b:02x}'

    def create_stat_card(self, parent, title, value, color, var_name):
        """Erstellt eine Statistik-Karte"""
        card = tk.Frame(parent, bg=self.colors['bg_tertiary'], relief="flat", borderwidth=0)
        card.pack(fill="x", pady=5)
        
        tk.Label(card, text=title, bg=self.colors['bg_tertiary'], fg=self.colors['fg_muted'], 
                font=("Segoe UI", 9)).pack(anchor="w", padx=12, pady=(8,2))
        
        lbl = tk.Label(card, text=value, bg=self.colors['bg_tertiary'], fg=color, 
                      font=("Segoe UI", 14, "bold"))
        lbl.pack(anchor="w", padx=12, pady=(0,8))
        
        setattr(self, var_name, lbl)

    def build_categories_ui(self):
        """Erstellt die Kategorien-UI"""
        # Speichere aktuelle Werte
        current_values = {}
        for (mc, sc, item), refs in self.labels_by_item.items():
            current_values[(mc, sc, item)] = {
                "amt": refs["amt"].get(),
                "note": refs["note"].get()
            }
        
        for w in self.cat_frame.winfo_children():
            w.destroy()
        self.labels_by_item.clear()
        self.totals_per_category.clear()

        row = 0
        for main_cat, subs in self.structure.items():
            mc_frame = tk.LabelFrame(self.cat_frame, text="", bg=self.colors['bg_secondary'], 
                                    fg=self.colors['fg'], relief="flat", borderwidth=2, padx=12, pady=10)
            mc_frame.grid(row=row, column=0, sticky="we", padx=8, pady=8)
            mc_frame.columnconfigure(2, weight=1)
            
            header_frame = tk.Frame(mc_frame, bg=self.colors['bg_secondary'])
            header_frame.grid(row=0, column=0, columnspan=4, sticky="we", pady=(0,8))
            
            icon = "💰" if "Einnahmen" in main_cat else "🏠" if "Fix" in main_cat else "🛒" if "Variable" in main_cat else "🎯"
            
            tk.Label(header_frame, text=f"{icon} {main_cat}", bg=self.colors['bg_secondary'], 
                    fg=self.colors['fg'], font=("Segoe UI", 12, "bold")).pack(side="left")
            
            add_sub_btn = tk.Button(header_frame, text="➕ Unterkat.", 
                                   command=lambda mc=main_cat: self.quick_add_subcategory(mc),
                                   bg=self.colors['accent'], fg="white", font=("Segoe UI", 8, "bold"),
                                   relief="flat", cursor="hand2", padx=8, pady=3)
            add_sub_btn.pack(side="left", padx=10)
            
            budget_limit = self.budget_warnings.get(main_cat)
            if budget_limit:
                tk.Label(header_frame, text=f"⚠️ Limit: {budget_limit} €", 
                        bg=self.colors['bg_secondary'], fg=self.colors['warning'],
                        font=("Segoe UI", 9)).pack(side="left", padx=10)
            
            total_label = tk.Label(header_frame, text="Summe: 0.00 €", bg=self.colors['bg_secondary'], 
                                 fg=self.colors['warning'], font=("Segoe UI", 11, "bold"))
            total_label.pack(side="right")
            self.totals_per_category[main_cat] = total_label

            subrow = 1
            for subcat, items in subs.items():
                sc_frame = tk.Frame(mc_frame, bg=self.colors['bg_tertiary'])
                sc_frame.grid(row=subrow, column=0, columnspan=4, sticky="we", pady=(8,4))
                
                tk.Label(sc_frame, text=f"📁 {subcat}", bg=self.colors['bg_tertiary'], 
                        fg=self.colors['fg_secondary'], font=("Segoe UI", 10, "bold")).pack(side="left", padx=8, pady=4)
                
                add_item_btn = tk.Button(sc_frame, text="➕", 
                                        command=lambda mc=main_cat, sc=subcat: self.quick_add_item(mc, sc),
                                        bg=self.colors['success'], fg="white", font=("Segoe UI", 8, "bold"),
                                        relief="flat", cursor="hand2", width=3, height=1)
                add_item_btn.pack(side="left", padx=5)
                
                subrow += 1

                for item in items:
                    item_frame = tk.Frame(mc_frame, bg=self.colors['bg_secondary'])
                    item_frame.grid(row=subrow, column=0, columnspan=4, sticky="we", pady=2)
                    item_frame.columnconfigure(2, weight=1)
                    
                    name_label = tk.Label(item_frame, text=f"  • {item}", bg=self.colors['bg_secondary'], 
                                        fg=self.colors['fg'], font=("Segoe UI", 10), anchor="w", width=20)
                    name_label.grid(row=0, column=0, sticky="w", padx=(12,8))

                    amt_var = tk.StringVar(value="0")
                    amt_entry = tk.Entry(item_frame, textvariable=amt_var, width=12, 
                                       font=("Segoe UI", 10), bg=self.colors['bg_input'], 
                                       fg=self.colors['fg'], insertbackground=self.colors['fg'], 
                                       relief="flat", justify="right")
                    amt_entry.grid(row=0, column=1, sticky="w", padx=5)
                    
                    note_var = tk.StringVar(value="")
                    note_entry = tk.Entry(item_frame, textvariable=note_var, width=25,
                                        font=("Segoe UI", 9), bg=self.colors['bg_input'], 
                                        fg=self.colors['fg_muted'], insertbackground=self.colors['fg'], 
                                        relief="flat")
                    note_entry.grid(row=0, column=2, sticky="we", padx=5)
                    
                    if self.delete_mode.get():
                        del_btn = tk.Button(item_frame, text="❌", 
                                          command=lambda m=main_cat, s=subcat, i=item: self.delete_item(m, s, i),
                                          bg=self.colors['danger'], fg="white", font=("Segoe UI", 8, "bold"),
                                          relief="flat", cursor="hand2", width=3)
                        del_btn.grid(row=0, column=3, padx=5)

                    key = (main_cat, subcat, item)
                    self.labels_by_item[key] = {"amt": amt_var, "note": note_var}
                    
                    if key in current_values:
                        amt_var.set(current_values[key]["amt"])
                        note_var.set(current_values[key]["note"])
                    
                    amt_var.trace_add("write", lambda *_args, k=key: self.on_amount_change(k))

                    subrow += 1

            row += 1

    def toggle_delete_mode(self):
        """Schaltet Löschmodus um"""
        self.build_categories_ui()

    def navigate_month(self, direction):
        """Navigiert zum vorherigen/nächsten Monat"""
        try:
            current = self.current_month.get()
            year, month = map(int, current.split('-'))
            
            month += direction
            if month > 12:
                month = 1
                year += 1
            elif month < 1:
                month = 12
                year -= 1
            
            new_month = f"{year}-{month:02d}"
            self.current_month.set(new_month)
            self.load_month(new_month)
        except:
            messagebox.showerror("Fehler", "Ungültiges Monatsformat")

    def quick_add_subcategory(self, main_cat):
        """Schnelles Hinzufügen einer Unterkategorie"""
        subcat = simpledialog.askstring("Neue Unterkategorie", 
                                       f"Name der Unterkategorie in '{main_cat}':",
                                       parent=self.root)
        if subcat and subcat.strip():
            if subcat not in self.structure[main_cat]:
                self.structure[main_cat][subcat] = []
                self.save_settings()
                self.build_categories_ui()
                messagebox.showinfo("✅ Erfolg", f"Unterkategorie '{subcat}' hinzugefügt!")
            else:
                messagebox.showinfo("Info", "Unterkategorie existiert bereits.")

    def quick_add_item(self, main_cat, subcat):
        """Schnelles Hinzufügen eines Items"""
        item = simpledialog.askstring("Neuer Posten", 
                                     f"Name des Postens in '{subcat}':",
                                     parent=self.root)
        if item and item.strip():
            if item not in self.structure[main_cat][subcat]:
                self.structure[main_cat][subcat].append(item)
                self.save_settings()
                self.build_categories_ui()
                messagebox.showinfo("✅ Erfolg", f"Posten '{item}' hinzugefügt!")
                self.recalculate_all()
            else:
                messagebox.showinfo("Info", "Posten existiert bereits.")

    def delete_item(self, main_cat, subcat, item):
        """Löscht ein Item"""
        if not messagebox.askyesno("Löschen", f"'{item}' wirklich löschen?"):
            return

        if item in self.structure[main_cat][subcat]:
            self.structure[main_cat][subcat].remove(item)

        if not self.structure[main_cat][subcat]:
            del self.structure[main_cat][subcat]

        if not self.structure[main_cat]:
            del self.structure[main_cat]

        self.save_settings()
        self.build_categories_ui()
        self.recalculate_all()

    def auto_fill_fixed(self):
        """Auto-Fill für Fixkosten vom letzten Monat"""
        if not self.auto_fill_enabled.get():
            messagebox.showinfo("Info", "Auto-Fill ist deaktiviert.")
            return
        
        current_month = self.current_month.get()
        prev_month = get_previous_month(current_month)
        
        if not prev_month:
            messagebox.showerror("Fehler", "Vorheriger Monat konnte nicht ermittelt werden")
            return
        
        prev_file = filename_for_month(self.current_profile.get(), prev_month)
        
        if not os.path.exists(prev_file):
            messagebox.showinfo("Info", f"Keine Daten für {prev_month} gefunden")
            return
        
        try:
            with open(prev_file, 'r', encoding='utf-8') as f:
                prev_data = json.load(f)
            
            prev_values = prev_data.get('values', {})
            filled_count = 0
            
            for (mc, sc, item), refs in self.labels_by_item.items():
                if "Fix" in mc or mc.lower().startswith("fix"):
                    prev_val = prev_values.get(mc, {}).get(sc, {}).get(item, {})
                    if prev_val.get('amount'):
                        refs['amt'].set(prev_val['amount'])
                        refs['note'].set(prev_val.get('note', ''))
                        filled_count += 1
            
            messagebox.showinfo("✅ Auto-Fill", f"{filled_count} Fixkosten vom {prev_month} übernommen!")
            self.recalculate_all()
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Auto-Fill fehlgeschlagen: {str(e)}")

    def set_budget_limits(self):
        """Setzt Budget-Limits für Kategorien"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Budget-Limits festlegen")
        dialog.geometry("400x500")
        dialog.configure(bg=self.colors['bg'])
        
        tk.Label(dialog, text="⚠️ Budget-Limits pro Kategorie", bg=self.colors['bg'], 
                fg=self.colors['fg'], font=("Segoe UI", 12, "bold")).pack(pady=15)
        
        frame = tk.Frame(dialog, bg=self.colors['bg'])
        frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        limit_vars = {}
        for main_cat in self.structure.keys():
            if "Einnahmen" not in main_cat:
                cat_frame = tk.Frame(frame, bg=self.colors['bg_secondary'], relief="flat", borderwidth=1)
                cat_frame.pack(fill="x", pady=5, padx=5)
                
                tk.Label(cat_frame, text=main_cat, bg=self.colors['bg_secondary'], 
                        fg=self.colors['fg'], font=("Segoe UI", 10, "bold")).pack(side="left", padx=10, pady=8)
                
                var = tk.StringVar(value=str(self.budget_warnings.get(main_cat, "")))
                entry = tk.Entry(cat_frame, textvariable=var, width=12, bg=self.colors['bg_input'], 
                               fg=self.colors['fg'], insertbackground=self.colors['fg'])
                entry.pack(side="right", padx=10, pady=8)
                
                limit_vars[main_cat] = var
        
        def save_limits():
            for cat, var in limit_vars.items():
                val = var.get().strip()
                if val:
                    try:
                        self.budget_warnings[cat] = float(val)
                    except:
                        pass
                elif cat in self.budget_warnings:
                    del self.budget_warnings[cat]
            
            self.save_settings()
            self.build_categories_ui()
            dialog.destroy()
            messagebox.showinfo("✅", "Budget-Limits gespeichert!")
        
        tk.Button(dialog, text="💾 Speichern", command=save_limits, bg=self.colors['success'], 
                 fg="white", font=("Segoe UI", 10, "bold"), relief="flat", 
                 padx=20, pady=8).pack(pady=10)

    def import_bank_csv(self):
        """Importiert Konto-CSV-Datei"""
        file = filedialog.askopenfilename(
            title="Konto-CSV importieren",
            filetypes=[("CSV Dateien", "*.csv"), ("Alle Dateien", "*.*")]
        )
        
        if not file:
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("CSV Import - Spalten zuordnen")
        dialog.geometry("500x400")
        dialog.configure(bg=self.colors['bg'])
        
        tk.Label(dialog, text="📥 CSV Import - Spalten zuordnen", bg=self.colors['bg'], 
                fg=self.colors['fg'], font=("Segoe UI", 12, "bold")).pack(pady=15)
        
        # CSV lesen
        try:
            with open(file, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f, delimiter=';')
                headers = next(reader)
                sample_rows = [next(reader, None) for _ in range(3)]
                sample_rows = [r for r in sample_rows if r]
        except:
            try:
                with open(file, 'r', encoding='latin-1') as f:
                    reader = csv.reader(f, delimiter=';')
                    headers = next(reader)
                    sample_rows = [next(reader, None) for _ in range(3)]
                    sample_rows = [r for r in sample_rows if r]
            except Exception as e:
                messagebox.showerror("Fehler", f"CSV konnte nicht gelesen werden: {str(e)}")
                dialog.destroy()
                return
        
        frame = tk.Frame(dialog, bg=self.colors['bg'])
        frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        tk.Label(frame, text="Verfügbare Spalten:", bg=self.colors['bg'], 
                fg=self.colors['fg'], font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=5)
        
        tk.Label(frame, text=", ".join(headers), bg=self.colors['bg'], 
                fg=self.colors['fg_muted'], font=("Segoe UI", 9)).pack(anchor="w", pady=5)
        
        # Mapping
        mappings = {}
        
        for field, label in [("Betrag", "Betrag-Spalte:"), ("Beschreibung", "Beschreibung-Spalte:")]:
            tk.Label(frame, text=label, bg=self.colors['bg'], 
                    fg=self.colors['fg'], font=("Segoe UI", 10)).pack(anchor="w", pady=(10,2))
            
            var = tk.StringVar(value=headers[0] if headers else "")
            combo = ttk.Combobox(frame, textvariable=var, values=headers, state="readonly")
            combo.pack(fill="x", pady=2)
            mappings[field] = var
        
        def do_import():
            try:
                amount_col = mappings["Betrag"].get()
                desc_col = mappings["Beschreibung"].get()
                
                if not amount_col or not desc_col:
                    messagebox.showerror("Fehler", "Bitte alle Spalten zuordnen")
                    return
                
                amount_idx = headers.index(amount_col)
                desc_idx = headers.index(desc_col)
                
                # CSV nochmal einlesen
                with open(file, 'r', encoding='utf-8-sig') as f:
                    reader = csv.reader(f, delimiter=';')
                    next(reader)  # Skip header
                    
                    imported = 0
                    for row in reader:
                        if len(row) <= max(amount_idx, desc_idx):
                            continue
                        
                        amount_str = row[amount_idx].replace('.', '').replace(',', '.')
                        amount = ensure_float(amount_str)
                        desc = row[desc_idx]
                        
                        if amount != 0:
                            # Hier könntest du intelligentes Mapping implementieren
                            # Für jetzt: Zeige Dialog zum manuellen Zuordnen
                            pass
                            imported += 1
                
                dialog.destroy()
                messagebox.showinfo("✅ Import", f"{imported} Transaktionen erkannt.\n(Manuelle Zuordnung noch nicht implementiert)")
                
            except Exception as e:
                messagebox.showerror("Fehler", f"Import fehlgeschlagen: {str(e)}")
        
        tk.Button(dialog, text="📥 Importieren", command=do_import, bg=self.colors['success'], 
                 fg="white", font=("Segoe UI", 10, "bold"), relief="flat", 
                 padx=20, pady=8).pack(pady=15)

    def update_charts(self):
        """Aktualisiert Monatsvergleich-Charts"""
        try:
            num_months = int(self.comparison_months.get())
        except:
            num_months = 6
        
        months_data = []
        current = self.current_month.get()
        
        for i in range(num_months):
            month = current
            for _ in range(i):
                month = get_previous_month(month)
                if not month:
                    break
            
            if not month:
                break
            
            fname = filename_for_month(self.current_profile.get(), month)
            if os.path.exists(fname):
                try:
                    with open(fname, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    months_data.append((month, data))
                except:
                    pass
        
        months_data.reverse()
        
        # Chart 1: Verlauf
        self.fig1.clear()
        ax1 = self.fig1.add_subplot(111)
        
        if months_data:
            labels = [m[0] for m in months_data]
            incomes = []
            expenses = []
            balances = []
            
            for month, data in months_data:
                income = 0
                expense = 0
                values = data.get('values', {})
                
                for mc, subs in values.items():
                    for sc, items in subs.items():
                        for item, val in items.items():
                            amt = ensure_float(val.get('amount', 0))
                            if "Einnahmen" in mc:
                                income += amt
                            else:
                                expense += amt
                
                incomes.append(income)
                expenses.append(expense)
                balances.append(income - expense)
            
            x = range(len(labels))
            ax1.plot(x, incomes, marker='o', label='Einnahmen', color='#107c10', linewidth=2)
            ax1.plot(x, expenses, marker='s', label='Ausgaben', color='#d13438', linewidth=2)
            ax1.plot(x, balances, marker='^', label='Saldo', color='#0078d4', linewidth=2)
            
            ax1.set_xticks(x)
            ax1.set_xticklabels(labels, rotation=45)
            ax1.set_ylabel('Betrag (€)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            text_color = self.colors['fg']
            ax1.tick_params(colors=text_color)
            ax1.yaxis.label.set_color(text_color)
            ax1.xaxis.label.set_color(text_color)
            for spine in ax1.spines.values():
                spine.set_color(text_color)
        
        self.fig1.tight_layout()
        self.canvas1.draw()
        
        # Chart 2: Pie
        self.fig2.clear()
        ax2 = self.fig2.add_subplot(111)
        
        categories = {}
        for (mc, sc, item), refs in self.labels_by_item.items():
            if "Einnahmen" not in mc:
                amt = ensure_float(refs['amt'].get())
                if amt > 0:
                    categories[mc] = categories.get(mc, 0) + amt
        
        if categories:
            labels_pie = list(categories.keys())
            sizes = list(categories.values())
            colors_pie = ['#0078d4', '#107c10', '#d13438', '#ffd700', '#ca5010', '#5c2d91']
            
            ax2.pie(sizes, labels=labels_pie, autopct='%1.1f%%', startangle=90, 
                   colors=colors_pie[:len(labels_pie)])
            ax2.axis('equal')
        
        self.canvas2.draw()

    def update_year_overview(self):
        """Aktualisiert Jahresübersicht"""
        try:
            year = int(self.year_select.get())
        except:
            messagebox.showerror("Fehler", "Ungültiges Jahr")
            return
        
        yearly_data = []
        for month in range(1, 13):
            month_str = f"{year}-{month:02d}"
            fname = filename_for_month(self.current_profile.get(), month_str)
            
            if os.path.exists(fname):
                try:
                    with open(fname, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    yearly_data.append((month_str, data))
                except:
                    pass
        
        if not yearly_data:
            messagebox.showinfo("Info", f"Keine Daten für {year} gefunden")
            return
        
        # Berechne Jahreswerte
        total_income = 0
        total_expense = 0
        monthly_incomes = []
        monthly_expenses = []
        month_labels = []
        
        for month_str, data in yearly_data:
            income = 0
            expense = 0
            values = data.get('values', {})
            
            for mc, subs in values.items():
                for sc, items in subs.items():
                    for item, val in items.items():
                        amt = ensure_float(val.get('amount', 0))
                        if "Einnahmen" in mc:
                            income += amt
                        else:
                            expense += amt
            
            total_income += income
            total_expense += expense
            monthly_incomes.append(income)
            monthly_expenses.append(expense)
            month_labels.append(month_str)
        
        balance = total_income - total_expense
        num_months = len(yearly_data)
        
        # Update Labels
        self.year_income_label.config(text=f"Jahreseinnahmen: {total_income:.2f} €")
        self.year_expense_label.config(text=f"Jahresausgaben: {total_expense:.2f} €")
        self.year_balance_label.config(text=f"Jahressaldo: {balance:.2f} €",
                                       fg=self.colors['success'] if balance >= 0 else self.colors['danger'])
        
        avg_income = total_income / num_months if num_months > 0 else 0
        avg_expense = total_expense / num_months if num_months > 0 else 0
        avg_balance = balance / num_months if num_months > 0 else 0
        
        self.avg_income_label.config(text=f"Ø Einnahmen: {avg_income:.2f} €")
        self.avg_expense_label.config(text=f"Ø Ausgaben: {avg_expense:.2f} €")
        self.avg_balance_label.config(text=f"Ø Saldo: {avg_balance:.2f} €")
        
        # Chart
        self.fig_year.clear()
        ax = self.fig_year.add_subplot(111)
        
        x = range(len(month_labels))
        width = 0.35
        
        ax.bar([i - width/2 for i in x], monthly_incomes, width, label='Einnahmen', color='#107c10')
        ax.bar([i + width/2 for i in x], monthly_expenses, width, label='Ausgaben', color='#d13438')
        
        ax.set_xlabel('Monat')
        ax.set_ylabel('Betrag (€)')
        ax.set_title(f'Jahresübersicht {year}')
        ax.set_xticks(x)
        ax.set_xticklabels(month_labels, rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        
        text_color = self.colors['fg']
        ax.tick_params(colors=text_color)
        ax.title.set_color(text_color)
        ax.yaxis.label.set_color(text_color)
        ax.xaxis.label.set_color(text_color)
        for spine in ax.spines.values():
            spine.set_color(text_color)
        
        self.fig_year.tight_layout()
        self.canvas_year.draw()

    def update_trends(self):
        """Berechnet Trends und Prognosen"""
        try:
            forecast_months = int(self.forecast_months.get())
        except:
            forecast_months = 3
        
        # Sammle letzte 6 Monate für Trendberechnung
        months_data = []
        current = self.current_month.get()
        
        for i in range(6):
            month = current
            for _ in range(i):
                month = get_previous_month(month)
                if not month:
                    break
            
            if not month:
                break
            
            fname = filename_for_month(self.current_profile.get(), month)
            if os.path.exists(fname):
                try:
                    with open(fname, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    months_data.append((month, data))
                except:
                    pass
        
        if len(months_data) < 3:
            messagebox.showinfo("Info", "Mindestens 3 Monate Daten benötigt für Prognosen")
            return
        
        months_data.reverse()
        
        # Extrahiere Einnahmen/Ausgaben
        incomes = []
        expenses = []
        labels = []
        
        for month, data in months_data:
            income = 0
            expense = 0
            values = data.get('values', {})
            
            for mc, subs in values.items():
                for sc, items in subs.items():
                    for item, val in items.items():
                        amt = ensure_float(val.get('amount', 0))
                        if "Einnahmen" in mc:
                            income += amt
                        else:
                            expense += amt
            
            incomes.append(income)
            expenses.append(expense)
            labels.append(month)
        
        # Lineare Regression für Prognose
        x = np.arange(len(incomes))
        
        # Trend Einnahmen
        z_income = np.polyfit(x, incomes, 1)
        p_income = np.poly1d(z_income)
        
        # Trend Ausgaben
        z_expense = np.polyfit(x, expenses, 1)
        p_expense = np.poly1d(z_expense)
        
        # Prognose für kommende Monate
        future_x = np.arange(len(incomes), len(incomes) + forecast_months)
        future_labels = []
        next_month = get_next_month(labels[-1])
        for _ in range(forecast_months):
            future_labels.append(next_month)
            next_month = get_next_month(next_month)
        
        forecast_incomes = p_income(future_x)
        forecast_expenses = p_expense(future_x)
        
        # Chart erstellen
        self.fig_trend.clear()
        ax = self.fig_trend.add_subplot(111)
        
        all_x = np.concatenate([x, future_x])
        all_labels = labels + future_labels
        
        # Historische Daten
        ax.plot(x, incomes, marker='o', label='Einnahmen (Ist)', color='#107c10', linewidth=2)
        ax.plot(x, expenses, marker='s', label='Ausgaben (Ist)', color='#d13438', linewidth=2)
        
        # Trendlinien
        ax.plot(all_x, p_income(all_x), '--', label='Trend Einnahmen', color='#107c10', alpha=0.7)
        ax.plot(all_x, p_expense(all_x), '--', label='Trend Ausgaben', color='#d13438', alpha=0.7)
        
        # Prognose
        ax.plot(future_x, forecast_incomes, marker='o', label='Prognose Einnahmen', 
               color='#107c10', linestyle=':', linewidth=2, markersize=8)
        ax.plot(future_x, forecast_expenses, marker='s', label='Prognose Ausgaben', 
               color='#d13438', linestyle=':', linewidth=2, markersize=8)
        
        # Vertikale Linie zwischen Ist und Prognose
        ax.axvline(x=len(incomes)-0.5, color=self.colors['fg_muted'], linestyle='--', alpha=0.5)
        
        ax.set_xlabel('Monat')
        ax.set_ylabel('Betrag (€)')
        ax.set_title('Trends & Prognosen')
        ax.set_xticks(all_x)
        ax.set_xticklabels(all_labels, rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        text_color = self.colors['fg']
        ax.tick_params(colors=text_color)
        ax.title.set_color(text_color)
        ax.yaxis.label.set_color(text_color)
        ax.xaxis.label.set_color(text_color)
        for spine in ax.spines.values():
            spine.set_color(text_color)
        
        self.fig_trend.tight_layout()
        self.canvas_trend.draw()

    def on_save_click(self):
        """Speichert den aktuellen Monat"""
        ym = month_key_from_selection(self.current_month.get())
        if not validate_month_format(ym):
            messagebox.showerror("Ungültiges Format", "Bitte Format YYYY-MM verwenden (z.B. 2025-01)")
            return
            
        fname = filename_for_month(self.current_profile.get(), ym)
        payload = {"structure": self.structure, "values": {}}
        
        for (mc, sc, item), varsd in self.labels_by_item.items():
            amt = varsd["amt"].get().strip()
            note = varsd["note"].get().strip()
            payload["values"].setdefault(mc, {}).setdefault(sc, {})[item] = {"amount": amt, "note": note}
        
        try:
            ensure_dir(os.path.dirname(fname))
            with open(fname, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            self.save_settings()
            messagebox.showinfo("✅ Gespeichert", f"Daten gespeichert für {ym}")
        except Exception as e:
            messagebox.showerror("Fehler beim Speichern", str(e))

    def on_load_click(self):
        """Lädt einen Monat"""
        ym = self.current_month.get()
        if not validate_month_format(ym):
            messagebox.showerror("Ungültiges Format", "Bitte Format YYYY-MM verwenden (z.B. 2025-01)")
            return
        self.load_month(ym)

    def load_month(self, ym):
        """Lädt Monatsdaten"""
        fname = filename_for_month(self.current_profile.get(), ym)
        if not os.path.exists(fname):
            for refs in self.labels_by_item.values():
                refs["amt"].set("0")
                refs["note"].set("")
            messagebox.showinfo("Neu", f"Keine Daten für {ym} gefunden.\nNeuer Monat erstellt.")
            self.recalculate_all()
            return
        
        try:
            with open(fname, "r", encoding="utf-8") as f:
                payload = json.load(f)
            
            if "structure" in payload:
                self.structure = payload["structure"]
            
            self.build_categories_ui()
            values = payload.get("values", {})
            
            for (mc, sc, item), refs in self.labels_by_item.items():
                v = values.get(mc, {}).get(sc, {}).get(item, {})
                refs["amt"].set(v.get("amount", "0"))
                refs["note"].set(v.get("note", ""))
            
            messagebox.showinfo("✅ Geladen", f"Daten für {ym} geladen!")
            self.recalculate_all()
        except Exception as e:
            messagebox.showerror("Fehler beim Laden", str(e))

    def on_amount_change(self, key):
        """Callback bei Wertänderung"""
        self.recalculate_all()

    def recalculate_all(self):
        """Neuberechnung aller Werte"""
        total_income = 0.0
        total_expense = 0.0
        fixed_total = 0.0
        variable_total = 0.0
        per_item_amount = {}

        for (mc, sc, item), refs in self.labels_by_item.items():
            amt_str = refs["amt"].get()
            amt = ensure_float(amt_str)
            per_item_amount[(mc, sc, item)] = amt

            if "Einnahmen" in mc or mc.lower().startswith("ein"):
                total_income += amt
            elif "Fix" in mc or mc.lower().startswith("fix"):
                fixed_total += amt
                total_expense += amt
            elif "Variable" in mc or mc.lower().startswith("var"):
                variable_total += amt
                total_expense += amt
            elif mc == "Sparen":
                total_expense += amt
                variable_total += amt
            else:
                total_expense += amt
                variable_total += amt

        per_main = {}
        for (mc, sc, item), amt in per_item_amount.items():
            per_main.setdefault(mc, 0.0)
            per_main[mc] += amt

        self.income_label.config(text=f"{total_income:.2f} €")
        self.expense_label.config(text=f"{total_expense:.2f} €")
        balance = total_income - total_expense
        bal_color = self.colors['success'] if balance >= 0 else self.colors['danger']
        self.balance_label.config(text=f"{balance:.2f} €", foreground=bal_color)

        goal = ensure_float(self.savings_goal.get())
        progress = min(max(balance, 0.0), goal) if goal > 0 else 0.0
        pct = (progress / goal * 100.0) if goal > 0 else 0.0
        self.savings_progress.config(text=f"Fortschritt: {progress:.2f} / {goal:.2f} ({pct:.1f}%)")

        saving_rate = (balance / total_income * 100.0) if total_income > 0 else 0.0
        self.saving_rate_label.config(text=f"📈 Sparquote: {saving_rate:.1f} %")

        self.fixed_var_label.config(text=f"🔒 Fixkosten: {fixed_total:.2f} €")
        self.variable_var_label.config(text=f"🔄 Variable Kosten: {variable_total:.2f} €")

        # Update category sums mit Budget-Warnung
        for mc, lbl in self.totals_per_category.items():
            mc_sum = per_main.get(mc, 0.0)
            budget_limit = self.budget_warnings.get(mc)
            
            if budget_limit and mc_sum > budget_limit:
                lbl.config(text=f"⚠️ Summe: {mc_sum:.2f} € (Limit: {budget_limit})", 
                          fg=self.colors['danger'])
            else:
                lbl.config(text=f"Summe: {mc_sum:.2f} €", fg=self.colors['warning'])

        # Top-3
        expense_by_sub = {}
        for (mc, sc, item), amt in per_item_amount.items():
            if "Einnahmen" in mc or mc.lower().startswith("ein"):
                continue
            key = f"{mc} / {sc}"
            expense_by_sub.setdefault(key, 0.0)
            expense_by_sub[key] += amt

        top3 = sorted(expense_by_sub.items(), key=lambda x: x[1], reverse=True)[:3]
        for i in range(3):
            if i < len(top3):
                name, amt = top3[i]
                self.top3_boxes[i].config(text=f"{i+1}. {name}: {amt:.2f} €")
            else:
                self.top3_boxes[i].config(text=f"{i+1}. -")

    def export_csv(self):
        """CSV Export"""
        file = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Dateien", "*.csv")],
            initialfile=f"budget_{self.current_month.get()}.csv"
        )
        if not file:
            return

        try:
            with open(file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(["Hauptkategorie", "Unterkategorie", "Posten", "Betrag", "Notiz"])

                for (mc, sc, item), refs in self.labels_by_item.items():
                    writer.writerow([
                        mc,
                        sc,
                        item,
                        refs["amt"].get().replace('.', ','),
                        refs["note"].get()
                    ])

            messagebox.showinfo("✅ Export", f"CSV erfolgreich exportiert!")
        except Exception as e:
            messagebox.showerror("Fehler beim CSV Export", str(e))

    def export_pdf(self):
        """PDF Export"""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            from reportlab.lib.units import cm
            
            file = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF Dateien", "*.pdf")],
                initialfile=f"budget_{self.current_month.get()}.pdf"
            )
            if not file:
                return
            
            c = canvas.Canvas(file, pagesize=A4)
            width, height = A4
            
            # Header
            c.setFont("Helvetica-Bold", 20)
            c.drawString(2*cm, height - 2*cm, f"Budget-Report {self.current_month.get()}")
            
            y = height - 4*cm
            c.setFont("Helvetica", 12)
            
            # Summary
            total_income = sum(ensure_float(refs["amt"].get()) 
                             for (mc, sc, item), refs in self.labels_by_item.items() 
                             if "Einnahmen" in mc)
            total_expense = sum(ensure_float(refs["amt"].get()) 
                              for (mc, sc, item), refs in self.labels_by_item.items() 
                              if "Einnahmen" not in mc)
            
            c.drawString(2*cm, y, f"Einnahmen: {total_income:.2f} EUR")
            y -= 0.7*cm
            c.drawString(2*cm, y, f"Ausgaben: {total_expense:.2f} EUR")
            y -= 0.7*cm
            c.drawString(2*cm, y, f"Saldo: {total_income - total_expense:.2f} EUR")
            y -= 1.5*cm
            
            # Details
            c.setFont("Helvetica-Bold", 14)
            c.drawString(2*cm, y, "Details:")
            y -= 1*cm
            
            c.setFont("Helvetica", 10)
            for (mc, sc, item), refs in self.labels_by_item.items():
                amt = refs["amt"].get()
                if ensure_float(amt) > 0:
                    text = f"{mc} > {sc} > {item}: {amt} EUR"
                    if y < 2*cm:
                        c.showPage()
                        y = height - 2*cm
                    c.drawString(2*cm, y, text)
                    y -= 0.5*cm
            
            c.save()
            messagebox.showinfo("✅ Export", "PDF erfolgreich exportiert!")
            
        except ImportError:
            messagebox.showerror("Fehler", "reportlab nicht installiert.\nInstalliere mit: pip install reportlab")
        except Exception as e:
            messagebox.showerror("Fehler beim PDF Export", str(e))


# ------------------------------
# Unit Tests (optional ausführbar)
# ------------------------------
def run_tests():
    """Einfache Unit-Tests für Kernlogik"""
    print("🧪 Running Unit Tests...")
    
    # Test 1: ensure_float
    assert ensure_float("123.45") == 123.45, "Test 1a failed"
    assert ensure_float("123,45") == 123.45, "Test 1b failed"
    assert ensure_float("") == 0.0, "Test 1c failed"
    assert ensure_float("abc") == 0.0, "Test 1d failed"
    print("✅ Test 1: ensure_float passed")
    
    # Test 2: validate_month_format
    assert validate_month_format("2025-01") == True, "Test 2a failed"
    assert validate_month_format("2025-13") == False, "Test 2b failed"
    assert validate_month_format("2025-00") == False, "Test 2c failed"
    assert validate_month_format("abc") == False, "Test 2d failed"
    print("✅ Test 2: validate_month_format passed")
    
    # Test 3: get_previous_month
    assert get_previous_month("2025-03") == "2025-02", "Test 3a failed"
    assert get_previous_month("2025-01") == "2024-12", "Test 3b failed"
    print("✅ Test 3: get_previous_month passed")
    
    # Test 4: get_next_month
    assert get_next_month("2025-03") == "2025-04", "Test 4a failed"
    assert get_next_month("2025-12") == "2026-01", "Test 4b failed"
    print("✅ Test 4: get_next_month passed")
    
    print("✅ All tests passed!")


# ------------------------------
# App Entry
# ------------------------------
def main():
    import sys
    
    # Optional: Tests ausführen wenn --test Parameter
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        run_tests()
        return
    
    root = tk.Tk()
    app = BudgetApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()


# ------------------------------
# PyInstaller Build-Script (build.py)
# ------------------------------
"""
Um eine .exe zu erstellen, erstelle eine Datei 'build.py':

```python
import PyInstaller.__main__

PyInstaller.__main__.run([
    'budget_planner.py',
    '--onefile',
    '--windowed',
    '--name=BudgetPlanner',
    '--icon=icon.ico',  # Optional: eigenes Icon
    '--add-data=profiles;profiles',
])
```

Dann ausführen:
1. pip install pyinstaller reportlab matplotlib numpy
2. python build.py
3. Die .exe findet sich im 'dist' Ordner
"""
