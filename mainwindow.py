import sys, re
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.text
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QGridLayout, QTabWidget, QWidget, QComboBox, QVBoxLayout, QPushButton, QHBoxLayout, QLabel, QLineEdit, QScrollArea, QSpacerItem, QSizePolicy, QGroupBox
from PyQt5.QtGui import QDoubleValidator, QValidator
from PyQt5.QtCore import Qt, QLocale, QTimer

from nachgiebigkeit import NachgiebigkeitWidget
from gewinde import GewindeWidget
from kraefte import KraefteWidget
from werkstoff import WerkstoffWidget
from dauerfestigkeit import DauerfestigkeitWidget
from wirkungsgrad import WirkungsgradWidget
from nachgiebigkeit import SvgWidget

class PlotWindow(QMainWindow):
    """Separates Fenster zur Anzeige des Kraft-Weg-Diagramms."""
    def __init__(self, kraefte_widget, nachgiebigkeit_widget, delta_s, delta_p, phi, parent=None):
        print("PlotWindow initialized - Debug check")
        super().__init__(parent)
        self.setWindowTitle("Kraft-Verschiebungs-Diagramm (Bild 3.27)")
        self.resize(800, 600)
        self.kraefte_widget = kraefte_widget
        self.nachgiebigkeit_widget = nachgiebigkeit_widget
        self.delta_s = delta_s
        self.delta_p = delta_p
        self.phi = phi

        # Central widget and layout
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)

        # Matplotlib canvas with larger figure size for better visibility
        # Use a 4:3 aspect ratio which works better for most diagrams
        # make figure taller for a larger rectangular plot area
        self.figure = plt.figure(figsize=(12, 8.5), dpi=100)
        # disable automatic tight layout so fixed axis position is preserved
        self.figure.set_tight_layout(False)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self.figure)
        # increase canvas minimum height so the rectangular plot has more vertical pixels
        self.canvas.setMinimumHeight(800)

        # place the plotting axes as a horizontal rectangle at the top of the figure
        # values are [left, bottom, width, height] in figure coordinates
        # make the rectangle noticeably taller (increase height and lower bottom)
        # adjust bottom from 0.75 -> 0.55 and height from 0.20 -> 0.40 (taller band)
        self.ax.set_position([0.03, 0.55, 0.94, 0.40])

        # create a visible rectangular border inside the axes (in axes coordinates)
        self.plot_border = Rectangle((0, 0), 1, 1, transform=self.ax.transAxes,
                                     fill=False, linewidth=1.2, edgecolor='black', zorder=20)
        self.ax.add_patch(self.plot_border)

        # Add widgets to layout
        layout.addWidget(self.canvas)
        
        # Calculate values for the plot
        self.update_plot()
        
        self.setCentralWidget(central_widget)
        
    def update_plot(self):
        """Update the force-displacement diagram to match the provided sketch (forces aligned on top)."""
        self.ax.clear()

        # re-apply the fixed axes position and re-add the border after clearing
        self.ax.set_position([0.03, 0.55, 0.94, 0.40])
        self.plot_border = Rectangle((0, 0), 1, 1, transform=self.ax.transAxes,
                                     fill=False, linewidth=1.2, edgecolor='black', zorder=20)
        self.ax.add_patch(self.plot_border)

        try:
            # === 1. Get all relevant values ===
            F_A = float(self.kraefte_widget.get_value("F_A") or 0)
            F_Kerf = float(self.kraefte_widget.get_value("F_Kerf") or 0)
            F_Mmin = float(self.kraefte_widget.get_value("F_Mmin") or 0)
            F_Mmax = float(self.kraefte_widget.get_value("F_Mmax") or 0)
            F_V = float(self.kraefte_widget.get_value("F_V") or 0)
            F_Smax = float(self.kraefte_widget.get_value("F_Smax") or 0)
            F_Z = float(self.kraefte_widget.get_value("F_Z") or 0)
            phi = float(self.phi or 0)
            delta_s = max(self.delta_s, 1e-12)
            delta_p = max(self.delta_p, 1e-12)

            # Derived values
            F_SA = phi * F_A
            F_PA = (1 - phi) * F_A
            F_sp = F_Smax if F_Smax else (F_V + F_SA)
            F_V_minus_F_PA = F_V - F_PA

            # Displacements
            f_sm_max = F_SA * delta_s
            f_pm_max = F_Mmax * delta_p
            f_V = F_V * delta_s
            f_Mmin = F_Mmin * delta_s
            f_Mmax = F_Mmax * delta_s
            f_sp = F_sp * delta_s

            # --- Determine a safe y (force) limit to avoid exploding values when delta is tiny ---
            candidates = [v for v in (F_sp, F_Mmax, F_V, F_Kerf, F_Z, F_V_minus_F_PA, F_SA, F_PA) if v is not None]
            y_data_max = max(candidates) if candidates else 1.0
            # Add a minimum so we don't get near-zero limits
            y_limit = max(1.0, y_data_max * 1.15)
            # Clamp to a sane absolute maximum to avoid plotting astronomic lines
            ABSOLUTE_Y_MAX = 1e6
            y_limit = min(y_limit, ABSOLUTE_Y_MAX)

            # Compute a reasonable x range estimate from meaningful displacements (avoid huge x caused by tiny deltas)
            est_f_candidates = [f_sm_max, f_pm_max, f_sp, f_V, f_Mmax * delta_s]
            est_f_max = max([c for c in est_f_candidates if c is not None] + [1e-6])
            max_f_ext_guess = est_f_max * 1.35
            # But also ensure we consider where c_S would hit y_limit: x_cs_at_y_limit = delta_s * y_limit
            x_cs_cap = delta_s * y_limit
            # Choose final x max as the smaller of the guess and the cap (prevents extremely long x when delta is tiny)
            max_f_ext = min(max_f_ext_guess, max(x_cs_cap * 1.2, max_f_ext_guess))
            # ensure a sensible minimum
            max_f_ext = max(max_f_ext, 1e-4)

            # === stiffness line c_S: limit to where it reaches y_limit (so it doesn't go to astronomical y) ===
            x_cs_end = min(max_f_ext, delta_s * y_limit)
            if x_cs_end <= 0:
                x_cs_end = max_f_ext * 0.5
            x_cs = np.array([0.0, x_cs_end])
            y_cs = (1.0 / delta_s) * x_cs
            # but clip y_cs to y_limit for plotting safety
            y_cs = np.clip(y_cs, -ABSOLUTE_Y_MAX, y_limit)
            self.ax.plot(x_cs, y_cs, color='royalblue', linewidth=3, label='c_S (Schraube)', zorder=2)

            # c_P line: compute start so it does not go above y_limit; solve for x when y = y_limit:
            # y = F_V - (1/delta_p)*(x - f_V)  =>  x_at_y_limit = f_V - delta_p*(y_limit - F_V)
            x_cp_start = max(0.0, f_V - delta_p * (y_limit - F_V))
            x_cp_end = max_f_ext
            # Ensure start < end
            if x_cp_start >= x_cp_end:
                x_cp_start = max(0.0, f_V - 0.1 * max_f_ext)
                x_cp_end = max(0.02, max_f_ext)
            x_cp = np.array([x_cp_start, x_cp_end])
            y_cp = F_V - (1.0 / delta_p) * (x_cp - f_V)
            # Clip c_P y values to the y_limit range for safety
            y_cp = np.clip(y_cp, -ABSOLUTE_Y_MAX, y_limit)
            self.ax.plot(x_cp, y_cp, color='red', linewidth=3, label='c_P (Bauteil)', zorder=3)

            # === top horizontal line at F_sp (highlighted) ===
            if F_sp and F_sp > 0:
                top_y = min(F_sp, y_limit)
            else:
                top_y = y_limit
            top_x_start = max(0.0, f_V - 0.02 * max_f_ext)  # start slightly left of the intersection
            top_x_end = min(max_f_ext * 0.98, max_f_ext)
            self.ax.hlines(top_y, top_x_start, top_x_end, colors='black', linewidth=1.6, zorder=4)
            # small cap to emphasize right end
            cap_half = 0.02 * (top_y if top_y != 0 else y_limit)
            self.ax.plot([top_x_end, top_x_end], [top_y - cap_half, top_y + cap_half], color='black', linewidth=1.6, zorder=4)

            # === stepped horizontal lines kept to the right (unchanged logic but placed below the top) ===
            stepped_forces = [
                ("F_Kerf", F_Kerf),
                ("F_V - F_PA", F_V_minus_F_PA),
                ("F_Z", F_Z),
                ("F_sp", F_sp)
            ]
            x_step_start = f_V + 0.07 * max_f_ext
            x_step_end = max_f_ext * 0.98
            y_offset = 0.012 * y_limit
            used_forces = set()
            for label, force in stepped_forces:
                if force and force not in used_forces:
                    f_display = min(force, y_limit)
                    self.ax.hlines(f_display, x_step_start, x_step_end, colors='gray', linestyles='dashed', lw=1.0, zorder=1)
                    self.ax.text(x_step_end + 0.01 * max_f_ext, f_display + y_offset, label, va='center', fontsize=9, color='gray', bbox=dict(facecolor='white', edgecolor='none', alpha=0.9))
                    used_forces.add(force)

            # === arrows aligned on the SAME TOP (heads at top_y) ===
            forces_for_arrows = [
                ("F_sp", F_sp, f_sp),
                ("F_Mmax", F_Mmax, f_Mmax),
                ("F_Mmin", F_Mmin, f_Mmin),
                ("F_V", F_V, f_V),
                # F_PA, F_SA handled separately in combined segment arrow
            ]
            valid = [(lab, float(val), float(xd)) for lab, val, xd in forces_for_arrows if val and val > 0]
            if valid:
                valid_sorted = sorted(valid, key=lambda t: t[1], reverse=True)
                n = len(valid_sorted)
                right = top_x_end * 0.96
                left = f_V + 0.05 * max_f_ext
                if left >= right:
                    left = max(0.0, f_V - 0.05 * max_f_ext)
                x_positions = np.linspace(right, left, n)
                def y_on_cp(x):
                    return np.clip(F_V - (1.0 / delta_p) * (x - f_V), -ABSOLUTE_Y_MAX, y_limit)
                for (label, val, _), x_pos in zip(valid_sorted, x_positions):
                    base_y = y_on_cp(x_pos)
                    self.ax.annotate('', xy=(x_pos, top_y), xytext=(x_pos, base_y),
                                     arrowprops=dict(arrowstyle='->', color='black', lw=1.4, mutation_scale=14), zorder=6)
                    self.ax.text(x_pos + 0.01 * max_f_ext, top_y + 0.02 * y_limit, label,
                                 ha='left', va='bottom', fontsize=9, fontweight='bold',
                                 bbox=dict(facecolor='white', edgecolor='none', alpha=0.95), zorder=7)

            # === combined F_PA / F_SA vertical segmented arrow (single arrow, two labels) ===
            if (F_PA and F_PA > 0) or (F_SA and F_SA > 0):
                # Choose x so it aligns neatly with other arrows (slightly more to the left)
                x_seg = f_V + 0.03 * max_f_ext
                if x_seg >= top_x_end * 0.95:
                    x_seg = top_x_end * 0.85

                # Base on c_P line at this x
                def y_on_cp_local(x):
                    return np.clip(F_V - (1.0 / delta_p) * (x - f_V), -ABSOLUTE_Y_MAX, y_limit)

                base_y = y_on_cp_local(x_seg)

                # Heights
                h_pa = F_PA if (F_PA and F_PA > 0) else 0.0
                h_sa = F_SA if (F_SA and F_SA > 0) else 0.0
                total_h = h_pa + h_sa
                if total_h <= 0:
                    pass
                else:
                    top_total = min(base_y + total_h, y_limit)
                    # Draw single full arrow (total)
                    self.ax.annotate(
                        '', xy=(x_seg, top_total), xytext=(x_seg, base_y),
                        arrowprops=dict(arrowstyle='->', color='black', lw=1.5, mutation_scale=16),
                        zorder=6
                    )

                    # Intermediate tick at F_PA boundary (only if both parts present and visible)
                    boundary_y = base_y + h_pa
                    if h_pa > 0 and h_sa > 0 and boundary_y < top_total:
                        tick_w = 0.012 * max_f_ext
                        self.ax.plot([x_seg - tick_w/2, x_seg + tick_w/2],
                                     [boundary_y, boundary_y],
                                     color='black', lw=1.2, zorder=6)

                    # Label F_PA segment (center of lower part)
                    if h_pa > 0:
                        mid_pa = base_y + h_pa / 2.0
                        if base_y < y_limit:
                            self.ax.text(
                                x_seg + 0.01 * max_f_ext, mid_pa,
                                "F_PA",
                                ha='left', va='center', fontsize=9, fontweight='bold',
                                bbox=dict(facecolor='white', edgecolor='none', alpha=0.9),
                                zorder=7
                            )

                    # Label F_SA segment (center of upper part)
                    if h_sa > 0:
                        mid_sa = base_y + h_pa + h_sa / 2.0
                        if mid_sa <= y_limit:
                            self.ax.text(
                                x_seg + 0.01 * max_f_ext, mid_sa,
                                "F_SA",
                                ha='left', va='center', fontsize=9, fontweight='bold',
                                bbox=dict(facecolor='white', edgecolor='none', alpha=0.9),
                                zorder=7
                            )

                    # Optional total F_A label at top
                    if top_total <= y_limit:
                        self.ax.text(
                            x_seg + 0.01 * max_f_ext, top_total + 0.015 * y_limit,
                            "F_A",
                            ha='left', va='bottom', fontsize=9, fontweight='bold',
                            bbox=dict(facecolor='white', edgecolor='none', alpha=0.9),
                            zorder=7
                        )

            # === intersection marker and other annotations (kept similar) ===
            # Only plot if in the visible y-range
            if 0 <= F_V <= y_limit:
                self.ax.plot([f_V], [F_V], 'ko', markersize=6, zorder=8)
                self.ax.text(f_V + 0.01 * max_f_ext, min(F_V + 0.02 * y_limit, y_limit), "(f_V, F_V)", va='bottom', ha='left', fontsize=9, bbox=dict(facecolor='white', edgecolor='none', alpha=0.9), zorder=8)

            # c_S / c_P labels (place within visible area)
            self.ax.text(0.30 * max_f_ext, min((1.0 / delta_s) * 0.30 * max_f_ext + 0.03 * y_limit, y_limit*0.98), "c_S", color='royalblue', fontsize=11, fontweight='bold', bbox=dict(facecolor='white', edgecolor='none', alpha=0.9))
            self.ax.text(min(f_V + 0.16 * max_f_ext, max_f_ext*0.98), max(F_V - 0.16 * max_f_ext / delta_p - 0.03 * y_limit, -0.05 * y_limit), "c_P", color='red', fontsize=11, fontweight='bold', bbox=dict(facecolor='white', edgecolor='none', alpha=0.9))

            # axes, legend, layout
            x_margin = max(0.02 * max_f_ext, 1e-6)
            self.ax.set_xlabel('f (Verschiebung) [mm]', fontsize=12, fontweight='bold')
            self.ax.set_ylabel('F (Kraft) [N]', fontsize=12, fontweight='bold')
            self.ax.set_xlim(-x_margin, max_f_ext * 1.02)
            self.ax.set_ylim(-0.05 * y_limit, y_limit * 1.05)
            self.ax.grid(True, linestyle=':', alpha=0.6)
            self.ax.legend(loc='upper left', fontsize=9, frameon=True)

            # draw the canvas (do NOT call tight_layout here, it would move our fixed axes)
            self.canvas.draw()

        except Exception as e:
            print(f"Error in update_plot: {e}")

    def load_optimal_values(self):
        """Load optimal example values for a clear, well-proportioned diagram."""
        try:
            # Set optimal values in the KraefteWidget
            self.kraefte_widget.set_value("F_V", "25000")
            self.kraefte_widget.set_value("F_A", "15000")
            self.kraefte_widget.set_value("F_Kerf", "10000")
            self.kraefte_widget.set_value("F_Mmin", "30000")
            self.kraefte_widget.set_value("F_Mmax", "40000")
            self.kraefte_widget.set_value("F_Z", "5000")
            
            # Set optimal compliance values 
            # These values provide a good visualization with clear lines and intersection points
            self.delta_s = 3e-5  # Higher compliance for screw
            self.delta_p = 1e-5  # Lower compliance for part
            self.phi = 0.25      # Typical phi value
            
            # Update the plot with the new values
            self.update_plot()
            
            QMessageBox.information(self, "Optimale Darstellung", 
                                   "Optimale Werte für eine klare Darstellung wurden geladen.")
        except Exception as e:
            QMessageBox.warning(self, "Fehler", f"Fehler beim Laden der optimalen Werte: {str(e)}")

class MainWindow(QMainWindow):
    """
    Hauptfenster für das Schraubenberechnungsprogramm.
    """
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Schraubenberechnung")
        self.resize(800, 600)
        
        # Initialize debounce timer for calculations
        self.calc_timer = QTimer()
        self.calc_timer.setSingleShot(True)
        self.calc_timer.timeout.connect(self.calculate)
        self.pending_updates = set()
        
        # Setze das Gebietsschema auf Deutsch
        german_locale = QLocale(QLocale.German)
        QLocale.setDefault(german_locale)
        self.validator = CustomDoubleValidator(-9999999.0, 9999999.0, 4)

        # Zentrales Layout
        self.central_layout = QVBoxLayout()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        home_tab = QWidget()
        home_layout = QGridLayout(home_tab)
        scroll_area.setWidget(home_tab)

        # Label über den Widgets
        label_text = """
                    <p style="font-size:20pt;">Schrauben & Schraubverbindungen</p>
                    <p style="font-size:12pt;">IGMR RWTH Aachen</p>
                    <p style="font-size: 10pt;">Aufbauend auf dem Vorlesungsumdruck</p>
                    <p style="font-size: 8pt;">Es sind sowohl '.' als auch ',' als Dezimalzeichen zulässig</p>
                    <p style="font-size: 8pt;">Formeln und Hinweise aus und zum Skript sind als Hover hinterlegt</p>
                    <p style="font-size: 8pt;"><span style="color: red;">*</span> kennzeichnen Empfolene Pflichtfelder, diese sind nur für das vollständige Ausrechen wichtig. </p>
                    """
        self.svg_widget = SvgWidget("stor/rwth_igmr_de_cmyk.svg")
        self.svg_widget.setFixedSize(700, 230)
        home_layout.addWidget(self.svg_widget, 0, 0, Qt.AlignCenter)
        label = QLabel(label_text)
        label.setAlignment(Qt.AlignCenter)
        home_layout.addWidget(label, 1, 0)

        # GewindeWidget
        self.gewinde_widget = GewindeWidget(self.validator, self)
        home_layout.addWidget(self.gewinde_widget, 2, 0)

        # WirkungsgradWidget
        self.wirkungsgrad_widget = WirkungsgradWidget(self.validator, self)
        home_layout.addWidget(self.wirkungsgrad_widget, 3, 0)

        # WerkstoffWidget
        self.werkstoff_widget = WerkstoffWidget(self)
        home_layout.addWidget(self.werkstoff_widget, 4, 0)

        # NachgiebigkeitWidget
        self.nachgiebigkeit_widget = NachgiebigkeitWidget(self.validator, self)
        home_layout.addWidget(self.nachgiebigkeit_widget, 5, 0)

        # KraefteWidget
        self.kraefte_widget = KraefteWidget(self.validator, self)
        home_layout.addWidget(self.kraefte_widget, 6, 0)

        # DauerfestigkeitWidget
        self.dauerfestigkeit_widget = DauerfestigkeitWidget(self.validator, self)
        home_layout.addWidget(self.dauerfestigkeit_widget, 7, 0)

        # === Separate Section: Force-Displacement Plot Inputs ===
        plot_group = QGroupBox("Kraft-Verschiebungs-Diagramm Eingaben (Bild 3.27)")
        plot_layout = QVBoxLayout()

        # Input fields for key variables
        input_widget = QWidget()
        input_layout = QGridLayout(input_widget)
        self.input_fields = {}
        variables = ["F_A", "F_Kerf", "F_Mmin", "F_Mmax", "F_V", "F_Smax", "F_PA", "F_Z", "delta_s", "delta_p", "Phi"]
        row = 0
        col = 0
        for var in variables:
            label = QLabel(f"{var}:")
            input_field = QLineEdit()
            input_field.setValidator(self.validator)
            input_field.textChanged.connect(lambda text, v=var: self.update_widget_value(v, text))
            input_layout.addWidget(label, row, col)
            input_layout.addWidget(input_field, row, col + 1)
            self.input_fields[var] = input_field
            col += 2
            if col >= 6:  # Move to next row after 3 variables
                row += 1
                col = 0

        plot_layout.addWidget(input_widget)

        # Button to show plot
        show_plot_button = QPushButton("Diagramm anzeigen")
        show_plot_button.clicked.connect(self.show_plot)
        plot_layout.addWidget(show_plot_button)

        plot_group.setLayout(plot_layout)
        home_layout.addWidget(plot_group, 8, 0)

        # Signalverbindungen zwischen Widgets
        self.gewinde_widget.changed_d.connect(lambda value: self.nachgiebigkeit_widget.update(value, "d"))
        self.gewinde_widget.changed_a_s.connect(lambda value: self.nachgiebigkeit_widget.update(value, "a_s"))
        self.nachgiebigkeit_widget.deltaValuesChanged.connect(self.kraefte_widget.update_delta_values)
        self.nachgiebigkeit_widget.deltaValuesChanged.connect(self.update_input_fields)
        self.wirkungsgrad_widget.changed_my.connect(lambda value: self.kraefte_widget.set_value("my", value))
        self.kraefte_widget.valuesChanged.connect(self.update_input_fields)

        # Hinzufügen der scroll area zum Zentralen Layout 
        self.central_layout.addWidget(scroll_area)

        # Knöpfe initialisieren
        about_button = QPushButton("Über")
        clear_button = QPushButton("Leeren")
        example_button = QPushButton("Beispiel")
        optimal_diagram_button = QPushButton("Optimales Diagramm")

        # Platzhalter
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        # Verbindungen der Knöpfe
        about_button.clicked.connect(self.about)
        clear_button.clicked.connect(self.clear_tab)
        example_button.clicked.connect(self.load_example)
        optimal_diagram_button.clicked.connect(self.load_optimal_diagram_example)

        # QComboBox zur Auswahl der Beispiele
        self.example_selector = QComboBox()
        self.example_selector.addItems(["F20", "H19", "F19", "H22", "Ü 3.1", "Ü 3.5", "Ü 3.7"])

        # Button layout
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.addWidget(about_button)
        button_layout.addItem(spacer)
        button_layout.addWidget(clear_button)
        button_layout.addWidget(self.example_selector)
        button_layout.addWidget(example_button)
        button_layout.addWidget(optimal_diagram_button)

        # Den Button Container hinzufügen
        self.central_layout.addWidget(button_container)

        central_widget = QWidget()
        central_widget.setLayout(self.central_layout)
        self.setCentralWidget(central_widget)

        self.plot_window = None  # Reference to plot window

    def show_plot(self):
        """Show the plot in a new window if all required fields are filled."""
        required_fields = ["F_A", "F_Kerf", "F_Mmin", "F_Mmax", "F_V", "F_Smax", "delta_s", "delta_p", "Phi"]
        # F_PA and F_Z are optional but should be used if provided
        missing_fields = []
        for field in required_fields:
            value = self.input_fields[field].text()
            if not value or not self.is_valid_float(value):
                missing_fields.append(field)

        if missing_fields:
            QMessageBox.warning(self, "Fehlende Eingaben", f"Bitte füllen Sie folgende Felder aus: {', '.join(missing_fields)}")
            return

        delta_s = float(self.nachgiebigkeit_widget.get_value("delta_s") or 1e-6)
        delta_p = float(self.nachgiebigkeit_widget.get_value("delta_p") or 1e-6)
        phi = float(self.kraefte_widget.get_value("Phi") or 0)  # Fixed: Changed 'Phi' to 'phi' to match PlotWindow
        if self.nachgiebigkeit_widget.fall.currentIndex() in [1, 2]:
            delta_s = float(self.nachgiebigkeit_widget.get_value("delta_sn") or delta_s)
            delta_p = float(self.nachgiebigkeit_widget.get_value("delta_pn") or delta_p)
            phi = float(self.kraefte_widget.get_value("Phi_n") or phi)  # Fixed: Changed 'Phi' to 'phi'

        if self.plot_window is None:
            self.plot_window = PlotWindow(self.kraefte_widget, self.nachgiebigkeit_widget, delta_s, delta_p, phi, self)
        else:
            # Update the existing plot window with new values
            self.plot_window.delta_s = delta_s
            self.plot_window.delta_p = delta_p
            self.plot_window.phi = phi
            self.plot_window.update_plot()
        self.plot_window.show()

    def is_valid_float(self, text):
        """Check if the text can be converted to a valid float."""
        try:
            float(text.replace(',', '.'))
            return True
        except ValueError:
            return False

    def update_widget_value(self, var, text):
        """
        Updates the corresponding widget value when an input field is changed.
        Uses a debounce timer to prevent excessive calculations.
        """
        if not text.strip():
            # If the field is empty, set the value to 0 and update the widget
            value = 0.0
        else:
            try:
                # Try to convert the text to a float, using dot as decimal separator
                value = float(text.replace(',', '.'))
            except ValueError:
                # If conversion fails, don't update the value
                return
        
        # Update the appropriate widget with the new value
        try:
            if var in ["delta_s", "delta_p", "Phi"]:
                self.nachgiebigkeit_widget.set_value(var, value)
            else:
                self.kraefte_widget.set_value(var, value)
            
            # Add to pending updates and restart debounce timer
            self.pending_updates.add(var)
            
            # Stop any running timer and start a new 500ms delay
            self.calc_timer.stop()
            self.calc_timer.start(500)  # 500ms debounce time
            
        except Exception as e:
            print(f"Error updating value: {e}")  # Debugging output

    def update_input_fields(self):
        """
        Updates the input fields with the current values from KraefteWidget and NachgiebigkeitWidget.
        Optimized for better performance by avoiding unnecessary updates.
        """
        # Block all signals temporarily for better performance
        self.blockSignals(True)
        
        for var in self.input_fields:
            input_field = self.input_fields[var]
            
            # Get current value in the field
            current_text = input_field.text()
            
            # Get new value from widgets
            if var in ["delta_s", "delta_p", "Phi"]:
                value = self.nachgiebigkeit_widget.get_value(var)
                # Use delta_sn, delta_pn, and Phi_n if applicable
                if self.nachgiebigkeit_widget.fall.currentIndex() in [1, 2]:
                    if var == "delta_s":
                        value = self.nachgiebigkeit_widget.get_value("delta_sn") or value
                    elif var == "delta_p":
                        value = self.nachgiebigkeit_widget.get_value("delta_pn") or value
                    elif var == "Phi":
                        value = self.nachgiebigkeit_widget.get_value("Phi_n") or value
            else:
                value = self.kraefte_widget.get_value(var)
                # Calculate F_PA if it's needed
                if var == "F_PA" and value is None:
                    F_A = self.kraefte_widget.get_value("F_A") or 0
                    phi = self.kraefte_widget.get_value("Phi") or 0
                    if self.nachgiebigkeit_widget.fall.currentIndex() in [1, 2]:
                        phi = self.kraefte_widget.get_value("Phi_n") or phi
                    value = (1 - phi) * F_A
            
            # Format the new value
            if value is not None:
                formatted_value = f"{value:.4e}" if (abs(value) < 1e-3 or abs(value) > 1e4) else f"{value:.4f}".rstrip('0').rstrip('.')
                formatted_value = formatted_value.replace('.', ',')
                
                # Only update if the value has actually changed (avoids unnecessary redraws)
                if formatted_value != current_text:
                    input_field.blockSignals(True)
                    input_field.setText(formatted_value)
                    input_field.blockSignals(False)
            elif current_text:  # Only clear if not already empty
                input_field.blockSignals(True)
                input_field.setText("")
                input_field.blockSignals(False)
        
        # Unblock signals
        self.blockSignals(False)

    def about(self):
        QMessageBox.about(self, "Über Uns", "Dieses Tool wurde innerhalb einer Projektarbeit von<br>Hannah Meuriße und Oliver Simon Kania entwickelt<br><br>Version 1.0<br>22.07.2024<br><br><br> P.S.: Wenn du das hier ließt, weil du eine Übung prokrastinierst: Nicht verzweifeln du schaffst das!!!")

    def calculate(self):
        """
        Performs calculations in a performance-optimized way.
        Only recalculates what's necessary based on which values have changed.
        """
        # Clear pending updates
        pending = self.pending_updates.copy()
        self.pending_updates.clear()
        
        # Always calculate in dependency order
        self.gewinde_widget.calculate()
        self.werkstoff_widget.calculate()
        
        # Only recalculate nachgiebigkeit if related values have changed
        nachgiebigkeit_params = {"delta_s", "delta_p", "Phi", "d", "a_s"}
        if pending.intersection(nachgiebigkeit_params) or not pending:
            self.nachgiebigkeit_widget.calculate()
            self.nachgiebigkeit_widget.delta_calc()
        
        # Calculate forces
        self.kraefte_widget.calculate()
        
        # Dauerfestigkeit depends on all the above
        self.dauerfestigkeit_widget.calculate()

    def clear_tab(self, suppress_calculation=False):
        """
        Clears all input fields and optionally suppresses calculations.
        
        Args:
            suppress_calculation (bool): If True, no calculation is triggered after clearing
        """
        # Block signals if we want to suppress calculation
        if suppress_calculation:
            self.blockSignals(True)
            
        # Clear all line edits
        for line_edit in self.findChildren(QLineEdit):
            line_edit.clear()
            
        # Close any plot window
        if self.plot_window is not None:
            self.plot_window.close()
            self.plot_window = None
            
        # Restore signals if we suppressed them
        if suppress_calculation:
            self.blockSignals(False)

    def closeEvent(self, event):
        if self.plot_window is not None:
            self.plot_window.close()
        print("Programm wird geschlossen")
        event.accept()

    def load_example(self):
        """
        Loads an example configuration and performs a single calculation at the end.
        Optimized to prevent multiple intermediate calculations.
        """
        # Block signals to prevent recalculation during loading
        self.blockSignals(True)
        
        selected_example = self.example_selector.currentText()
        self.clear_tab(suppress_calculation=True)  # Clear previous values without triggering calculation
        
        # Load the selected example
        if selected_example == "F20":
            self.load_example_1()
        elif selected_example == "H19":
            self.load_example_2()
        elif selected_example == "F19":
            self.load_example_3()
        elif selected_example == "H22":
            self.load_example_5()
        elif selected_example == "Ü 3.1":
            self.load_example_6()
        elif selected_example == "Ü 3.5":
            self.load_example_10()
        elif selected_example == "Ü 3.7":
            self.load_example_12()
            
        # Re-enable signals and perform a single calculation
        self.blockSignals(False)
        self.calculate()  # Recalculate all values
        self.update_input_fields()  # Update UI fields once

    def load_example_1(self):
        # GewindeWidget
        self.gewinde_widget.set_value("d", 12)  # M12 bolt
        self.gewinde_widget.set_value("P", 1.75)
        self.gewinde_widget.calculate()

        # WerkstoffWidget
        self.werkstoff_widget.festigkeitsklasse_lineedit.setText("12.9")
        self.werkstoff_widget.calculate()
        # For a 12.9 bolt: R_p0.2 = 1080 MPa, R_m = 1200 MPa

        # NachgiebigkeitWidget
        self.nachgiebigkeit_widget.set_value("d_k", 18)
        self.nachgiebigkeit_widget.set_value("D_B", 13.5)
        self.nachgiebigkeit_widget.set_value("D_A", 20)
        self.nachgiebigkeit_widget.set_value("l", 30)
        self.nachgiebigkeit_widget.set_value("m", 10)
        self.nachgiebigkeit_widget.set_bauteil_param("l", "Schaft", 20)
        self.nachgiebigkeit_widget.set_bauteil_param("l", "freies Gewinde", 10)
        self.nachgiebigkeit_widget.set_bauteil_param("l", "1 (z.B. Deckel)", 15)
        self.nachgiebigkeit_widget.set_bauteil_param("l", "2 (z.B. Gehäuse)", 15)
        self.nachgiebigkeit_widget.set_bauteil_param("E", "Kopf", 210000)
        self.nachgiebigkeit_widget.set_bauteil_param("E", "Schaft", 210000)
        self.nachgiebigkeit_widget.set_bauteil_param("E", "freies Gewinde", 210000)
        self.nachgiebigkeit_widget.set_bauteil_param("E", "Mutter/Verschraubung", 210000)
        self.nachgiebigkeit_widget.set_bauteil_param("E", "1 (z.B. Deckel)", 210000)
        self.nachgiebigkeit_widget.set_bauteil_param("E", "2 (z.B. Gehäuse)", 210000)
        # Set realistic compliances
        self.nachgiebigkeit_widget.set_value("delta_s", 2e-6)  # Bolt compliance
        self.nachgiebigkeit_widget.set_value("delta_p", 5e-6)  # Clamped parts compliance
        self.nachgiebigkeit_widget.calculate()
        self.nachgiebigkeit_widget.delta_calc()

        # KraefteWidget
        self.kraefte_widget.set_value("F_A", 24946)  # Working load
        self.kraefte_widget.set_value("F_Ao", 24946)
        self.kraefte_widget.set_value("F_Au", 0)
        self.kraefte_widget.set_value("F_Kerf", 3477)  # Required residual clamping force
        self.kraefte_widget.set_value("F_Z", 0)
        # Calculate F_V (preload) based on 90% of yield strength
        F_V = 0.9 * 1080 * 84.3  # F_V ≈ 81959 N
        self.kraefte_widget.set_value("F_V", F_V)
        # Set assembly forces
        self.kraefte_widget.set_value("F_Mmin", 0.8 * F_V)  # F_Mmin ≈ 65567 N
        self.kraefte_widget.set_value("F_Mmax", 1.2 * F_V)  # F_Mmax ≈ 98351 N
        # Set Phi
        delta_s = 2e-6
        delta_p = 5e-6
        n = 0.5  # Load introduction factor
        Phi = (delta_p / (delta_s + delta_p)) * n  # Phi ≈ 0.357
        self.kraefte_widget.set_value("Phi", Phi)
        self.kraefte_widget.set_value("alpha_A", 1.6)
        self.kraefte_widget.set_value("R_z", 16)
        self.kraefte_widget.set_value("kopf_mutterauflagen", 2)
        self.kraefte_widget.set_value("trennfugen", 1)
        self.kraefte_widget.set_value("gewinde", 1)
        self.kraefte_widget.calculate()

        # DauerfestigkeitWidget
        self.dauerfestigkeit_widget.set_werkstoff("Cq 45")
        self.dauerfestigkeit_widget.set_value("T_Mmax", 64500)
        self.dauerfestigkeit_widget.calculate()

    def load_example_2(self):
        self.gewinde_widget.set_value("d", 6)
        self.gewinde_widget.calculate()
        self.werkstoff_widget.festigkeitsklasse_lineedit.setText("10.9")
        self.werkstoff_widget.calculate()
        self.nachgiebigkeit_widget.set_value("d_k", 10)
        self.nachgiebigkeit_widget.set_value("D_B", 8)
        self.nachgiebigkeit_widget.set_value("D_A", 15)
        self.nachgiebigkeit_widget.set_value("l", 20)
        self.nachgiebigkeit_widget.set_value("m", 5)
        self.nachgiebigkeit_widget.set_bauteil_param("l", "Schaft", 15)
        self.nachgiebigkeit_widget.set_bauteil_param("l", "freies Gewinde", 5)
        self.nachgiebigkeit_widget.set_bauteil_param("l", "1 (z.B. Deckel)", 10)
        self.nachgiebigkeit_widget.set_bauteil_param("l", "2 (z.B. Gehäuse)", 10)
        self.nachgiebigkeit_widget.set_bauteil_param("E", "Kopf", 210000)
        self.nachgiebigkeit_widget.set_bauteil_param("E", "Schaft", 210000)
        self.nachgiebigkeit_widget.set_bauteil_param("E", "freies Gewinde", 210000)
        self.nachgiebigkeit_widget.set_bauteil_param("E", "Mutter/Verschraubung", 210000)
        self.nachgiebigkeit_widget.set_bauteil_param("E", "1 (z.B. Deckel)", 210000)
        self.nachgiebigkeit_widget.set_bauteil_param("E", "2 (z.B. Gehäuse)", 210000)
        self.nachgiebigkeit_widget.calculate()
        self.nachgiebigkeit_widget.delta_calc()
        self.kraefte_widget.set_value("kopf_mutterauflagen", 2)
        self.kraefte_widget.set_value("trennfugen", 1)
        self.kraefte_widget.set_value("gewinde", 1)
        self.kraefte_widget.set_value("R_z", 30)
        self.kraefte_widget.set_value("F_A", 6000)
        self.kraefte_widget.set_value("F_KR", 4000)
        self.kraefte_widget.set_value("alpha_A", 1.4)
        self.kraefte_widget.calculate()
        self.dauerfestigkeit_widget.calculate()

    def load_example_3(self):
        self.gewinde_widget.set_value("d", 6)
        self.gewinde_widget.calculate()
        self.werkstoff_widget.festigkeitsklasse_lineedit.setText("8.8")
        self.werkstoff_widget.calculate()
        self.nachgiebigkeit_widget.set_value("d_k", 10)
        self.nachgiebigkeit_widget.set_value("D_A", 20)
        self.nachgiebigkeit_widget.set_value("D_B", 7)
        self.nachgiebigkeit_widget.set_value("l", 24.2)
        self.nachgiebigkeit_widget.set_value("m", 5)
        self.nachgiebigkeit_widget.set_bauteil_param("l", "Schaft", 15)
        self.nachgiebigkeit_widget.set_bauteil_param("l", "freies Gewinde", 9.2)
        self.nachgiebigkeit_widget.set_bauteil_param("l", "1 (z.B. Deckel)", 12)
        self.nachgiebigkeit_widget.set_bauteil_param("l", "2 (z.B. Gehäuse)", 12)
        self.nachgiebigkeit_widget.set_bauteil_param("E", "Kopf", 210000)
        self.nachgiebigkeit_widget.set_bauteil_param("E", "Schaft", 210000)
        self.nachgiebigkeit_widget.set_bauteil_param("E", "freies Gewinde", 210000)
        self.nachgiebigkeit_widget.set_bauteil_param("E", "Mutter/Verschraubung", 210000)
        self.nachgiebigkeit_widget.set_bauteil_param("E", "1 (z.B. Deckel)", 210000)
        self.nachgiebigkeit_widget.set_bauteil_param("E", "2 (z.B. Gehäuse)", 210000)
        self.nachgiebigkeit_widget.set_value("delta_s", 5.72e-6)
        self.nachgiebigkeit_widget.fall.setCurrentIndex(1)
        self.nachgiebigkeit_widget.set_checkbox_states([True, True, True, True, True, False, True])
        self.nachgiebigkeit_widget.calculate()
        self.nachgiebigkeit_widget.delta_calc()
        self.kraefte_widget.set_value("F_Ao", 1500)
        self.kraefte_widget.set_value("F_Au", 0)
        self.kraefte_widget.set_value("alpha_A", 1.4)
        self.kraefte_widget.set_value("R_z", 16)
        self.kraefte_widget.set_value("kopf_mutterauflagen", 2)
        self.kraefte_widget.set_value("trennfugen", 1)
        self.kraefte_widget.set_value("gewinde", 1)
        self.kraefte_widget.calculate()

    def load_example_5(self):
        self.gewinde_widget.set_value("d", 14)
        self.gewinde_widget.set_value("P", 2)
        self.gewinde_widget.calculate()
        self.werkstoff_widget.festigkeitsklasse_lineedit.setText("12.9")
        self.werkstoff_widget.calculate()
        self.nachgiebigkeit_widget.set_value("d_k", 22)
        self.nachgiebigkeit_widget.set_value("D_B", 15.5)
        self.nachgiebigkeit_widget.set_value("D_A", 25)
        self.nachgiebigkeit_widget.set_value("l", 35)
        self.nachgiebigkeit_widget.set_value("m", 11)
        self.nachgiebigkeit_widget.set_bauteil_param("l", "Schaft", 25)
        self.nachgiebigkeit_widget.set_bauteil_param("l", "freies Gewinde", 10)
        self.nachgiebigkeit_widget.set_bauteil_param("l", "1 (z.B. Deckel)", 17)
        self.nachgiebigkeit_widget.set_bauteil_param("l", "2 (z.B. Gehäuse)", 18)
        self.nachgiebigkeit_widget.set_bauteil_param("E", "Kopf", 210000)
        self.nachgiebigkeit_widget.set_bauteil_param("E", "Schaft", 210000)
        self.nachgiebigkeit_widget.set_bauteil_param("E", "freies Gewinde", 210000)
        self.nachgiebigkeit_widget.set_bauteil_param("E", "Mutter/Verschraubung", 210000)
        self.nachgiebigkeit_widget.set_bauteil_param("E", "1 (z.B. Deckel)", 210000)
        self.nachgiebigkeit_widget.set_bauteil_param("E", "2 (z.B. Gehäuse)", 210000)
        self.nachgiebigkeit_widget.calculate()
        self.nachgiebigkeit_widget.delta_calc()
        self.kraefte_widget.set_value("alpha_A", 1.5)
        self.kraefte_widget.set_value("my", 0.2)
        self.kraefte_widget.set_value("F_Mmin", 2500)
        self.kraefte_widget.set_value("F_A", 5000)
        self.kraefte_widget.set_value("F_Ao", 5000)
        self.kraefte_widget.set_value("F_Au", 5000)
        self.kraefte_widget.set_value("F_Z", 0)
        self.kraefte_widget.set_value("F_Kerf", 2000)
        self.kraefte_widget.set_value("Phi", 1.2)
        self.kraefte_widget.set_value("R_z", 16)
        self.kraefte_widget.set_value("kopf_mutterauflagen", 2)
        self.kraefte_widget.set_value("trennfugen", 1)
        self.kraefte_widget.set_value("gewinde", 1)
        self.kraefte_widget.calculate()
        self.dauerfestigkeit_widget.set_werkstoff("GJL-250")
        self.dauerfestigkeit_widget.set_value("tau_t", 439.2)
        self.dauerfestigkeit_widget.calculate()

    def load_example_6(self):
        self.gewinde_widget.set_value("d", 8)
        self.gewinde_widget.set_value("P", 1.25)
        self.werkstoff_widget.festigkeitsklasse_lineedit.setText("8.8")
        self.wirkungsgrad_widget.set_value("my", 0.125)
        self.nachgiebigkeit_widget.set_value("m", 10)
        self.nachgiebigkeit_widget.set_value("D_B", 9)
        self.nachgiebigkeit_widget.set_value("D_A", 25)
        self.nachgiebigkeit_widget.set_value("d_k", 13)
        self.nachgiebigkeit_widget.set_value("l", 30)
        self.nachgiebigkeit_widget.fall.setCurrentIndex(2)
        self.nachgiebigkeit_widget.set_checkbox_states([True, True, True, True, False, False, False])
        self.nachgiebigkeit_widget.schraubenart.setCurrentIndex(1)
        self.nachgiebigkeit_widget.set_bauteil_param("l", "freies Gewinde", 18)
        self.nachgiebigkeit_widget.set_bauteil_param("l", "Schaft", 12)
        self.nachgiebigkeit_widget.set_bauteil_param("E", "Kopf", 210000)
        self.nachgiebigkeit_widget.set_bauteil_param("E", "Schaft", 210000)
        self.nachgiebigkeit_widget.set_bauteil_param("E", "freies Gewinde", 210000)
        self.nachgiebigkeit_widget.set_bauteil_param("E", "Mutter/Verschraubung", 210000)
        self.nachgiebigkeit_widget.set_bauteil_param("E", "1 (z.B. Deckel)", 210000)
        self.nachgiebigkeit_widget.set_bauteil_param("E", "2 (z.B. Gehäuse)", 210000)
        self.nachgiebigkeit_widget.set_bauteil_param("l", "1 (z.B. Deckel)", 10)
        self.nachgiebigkeit_widget.set_bauteil_param("l", "2 (z.B. Gehäuse)", 20)
        self.nachgiebigkeit_widget.set_value("n", 0.666)
        self.nachgiebigkeit_widget.calculate()
        self.nachgiebigkeit_widget.delta_calc()
        self.kraefte_widget.set_value("R_z", 16)
        self.kraefte_widget.set_value("F_A", 16300)
        self.kraefte_widget.set_value("F_Kerf", 6000)
        self.kraefte_widget.set_value("alpha_A", 1.6)
        self.kraefte_widget.set_value("kopf_mutterauflagen", 2)
        self.kraefte_widget.set_value("trennfugen", 1)
        self.kraefte_widget.set_value("gewinde", 1)
        self.kraefte_widget.calculate()
        self.dauerfestigkeit_widget.calculate()

    def load_example_10(self):
        self.gewinde_widget.set_value("d", 8)
        self.gewinde_widget.set_value("n", 2)
        self.gewinde_widget.set_value("P", 1.25)
        self.gewinde_widget.calculate()
        self.wirkungsgrad_widget.set_value("my", 0.135)
        self.wirkungsgrad_widget.calculate()
        self.nachgiebigkeit_widget.set_value("d_k", 13)
        self.nachgiebigkeit_widget.set_value("D_B", 9)
        self.nachgiebigkeit_widget.set_value("D_A", 20)
        self.nachgiebigkeit_widget.set_value("l", 25)
        self.nachgiebigkeit_widget.set_value("m", 6)
        self.nachgiebigkeit_widget.set_bauteil_param("l", "Schaft", 15)
        self.nachgiebigkeit_widget.set_bauteil_param("l", "freies Gewinde", 10)
        self.nachgiebigkeit_widget.set_bauteil_param("l", "1 (z.B. Deckel)", 12)
        self.nachgiebigkeit_widget.set_bauteil_param("l", "2 (z.B. Gehäuse)", 13)
        self.nachgiebigkeit_widget.set_bauteil_param("E", "Kopf", 210000)
        self.nachgiebigkeit_widget.set_bauteil_param("E", "Schaft", 210000)
        self.nachgiebigkeit_widget.set_bauteil_param("E", "freies Gewinde", 210000)
        self.nachgiebigkeit_widget.set_bauteil_param("E", "Mutter/Verschraubung", 210000)
        self.nachgiebigkeit_widget.set_bauteil_param("E", "1 (z.B. Deckel)", 210000)
        self.nachgiebigkeit_widget.set_bauteil_param("E", "2 (z.B. Gehäuse)", 210000)
        self.nachgiebigkeit_widget.calculate()
        self.nachgiebigkeit_widget.delta_calc()
        self.kraefte_widget.set_value("alpha_A", 1.4)
        self.kraefte_widget.set_value("R_z", 20)
        self.kraefte_widget.set_value("F_KR", 4500)
        self.kraefte_widget.set_value("kopf_mutterauflagen", 2)
        self.kraefte_widget.set_value("trennfugen", 1)
        self.kraefte_widget.set_value("gewinde", 2)
        self.kraefte_widget.calculate()

    def load_example_12(self):
        self.gewinde_widget.set_value("d", 10)
        self.gewinde_widget.set_value("P", 1.5)
        self.gewinde_widget.calculate()
        self.werkstoff_widget.festigkeitsklasse_lineedit.setText("10.9")
        self.werkstoff_widget.calculate()
        self.nachgiebigkeit_widget.set_value("m", 8)
        self.nachgiebigkeit_widget.set_value("D_B", 10.5)
        self.nachgiebigkeit_widget.set_value("D_A", 40)
        self.nachgiebigkeit_widget.set_value("d_k", 15)
        self.nachgiebigkeit_widget.set_value("l", 18)
        self.nachgiebigkeit_widget.set_bauteil_param("l", "freies Gewinde", 5)
        self.nachgiebigkeit_widget.set_bauteil_param("l", "Schaft", 38)
        self.nachgiebigkeit_widget.set_bauteil_param("E", "Kopf", 210000)
        self.nachgiebigkeit_widget.set_bauteil_param("E", "Schaft", 210000)
        self.nachgiebigkeit_widget.set_bauteil_param("E", "freies Gewinde", 210000)
        self.nachgiebigkeit_widget.set_bauteil_param("E", "Mutter/Verschraubung", 210000)
        self.nachgiebigkeit_widget.fall.setCurrentIndex(1)
        self.nachgiebigkeit_widget.set_checkbox_states([True, True, True, True, True, False, True])
        self.nachgiebigkeit_widget.set_bauteil_param("E", "3 (z.B. Boden)", 210000)
        self.nachgiebigkeit_widget.set_bauteil_param("l", "3 (z.B. Boden)", 25)
        self.nachgiebigkeit_widget.set_bauteil_param("E", "1 (z.B. Deckel)", 100000)
        self.nachgiebigkeit_widget.set_bauteil_param("l", "1 (z.B. Deckel)", 10)
        self.nachgiebigkeit_widget.set_bauteil_param("E", "2 (z.B. Gehäuse)", 100000)
        self.nachgiebigkeit_widget.set_bauteil_param("l", "2 (z.B. Gehäuse)", 8)
        self.nachgiebigkeit_widget.set_bauteil_param("A", "3 (z.B. Boden)", 90.124)
        self.nachgiebigkeit_widget.calculate()
        self.nachgiebigkeit_widget.delta_calc()
        self.kraefte_widget.set_value("alpha_A", 1)
        self.kraefte_widget.set_value("R_z", 24)
        self.kraefte_widget.set_value("kopf_mutterauflagen", 1)
        self.kraefte_widget.set_value("trennfugen", 2)
        self.kraefte_widget.set_value("gewinde", 2)
        self.kraefte_widget.set_value("F_Kerf", 8000)
        self.kraefte_widget.set_value("F_KR", 8000)
        self.kraefte_widget.set_value("F_A", 30918)
        self.kraefte_widget.calculate()

    def load_optimal_diagram_example(self):
        """Load optimal values for the force-displacement diagram."""
        # This calls the set_optimal_plot_values method we already implemented
        self.set_optimal_plot_values()
        
        # If the plot window is already open, update it
        if self.plot_window is not None:
            self.plot_window.close()
            self.plot_window = None
        
        # Show the plot with the optimal values
        self.show_plot()

    def set_optimal_plot_values(self):
        """Set optimal values for a clear, well-proportioned diagram."""
        # Set optimal values in input fields
        optimal_values = {
            "F_V": "25000",
            "F_A": "15000",
            "F_Kerf": "10000",
            "F_Mmin": "30000",
            "F_Mmax": "40000", 
            "F_Z": "5000",
            "delta_s": "0.00003",  # 3e-5
            "delta_p": "0.00001",  # 1e-5
            "Phi": "0.25"
        }
        
        # Update all input fields with the optimal values
        for var, value in optimal_values.items():
            if var in self.input_fields:
                self.input_fields[var].setText(value)
        
        # Trigger calculation
        self.calc_timer.start(100)
        
        # Show a message to confirm
        QMessageBox.information(self, "Optimale Werte", 
                               "Optimale Werte für eine klare Diagrammdarstellung wurden geladen.")

class CustomDoubleValidator(QDoubleValidator):
    def __init__(self, bottom, top, decimals, parent=None):
        super().__init__(bottom, top, decimals, parent)
        self.setNotation(QDoubleValidator.StandardNotation)
        self.setLocale(QLocale(QLocale.German))

    def validate(self, input_str, pos):
        # Check for empty or special intermediate inputs
        if input_str in ["", "-", ",", ".", "-.", "-,", "e", "E", "e-", "E-", "-e", "-E", "-e-", "-E-"]:
            return (QValidator.Intermediate, input_str, pos)
        
        # Replace comma with dot for decimal point
        modified_input = input_str.replace(',', '.')
        
        # Check for scientific notation inputs which are still being typed
        suffixes = ["e", "E", "e-", "E-", "e+", "E+"]
        for suffix in suffixes:
            if modified_input.endswith(suffix):
                return (QValidator.Intermediate, input_str, pos)
                
        # Try to convert to float
        try:
            value = float(modified_input)
        except ValueError:
            return (QValidator.Invalid, input_str, pos)
            
        # Check if value is within the specified range
        if self.bottom() <= value <= self.top():
            return (QValidator.Acceptable, input_str, pos)
        return (QValidator.Invalid, input_str, pos)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
