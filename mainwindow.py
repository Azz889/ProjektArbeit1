import sys, re
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
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

        # Matplotlib canvas
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumHeight(400)
        
        # Calculate values for the plot
        self.update_plot()
        
        layout.addWidget(self.canvas)
        self.setCentralWidget(central_widget)
        
    def update_plot(self):
        """Update the force-displacement diagram with displacement on X-axis and force on Y-axis."""
        self.ax.clear()

        try:
            # Get force values from KraefteWidget
            F_A = float(self.kraefte_widget.get_value("F_A") or 0)
            F_Kerf = float(self.kraefte_widget.get_value("F_Kerf") or 0)
            F_Mmin = float(self.kraefte_widget.get_value("F_Mmin") or 0)
            F_Mmax = float(self.kraefte_widget.get_value("F_Mmax") or 0)
            F_V = float(self.kraefte_widget.get_value("F_V") or 0)
            F_Smax = float(self.kraefte_widget.get_value("F_Smax") or 0)
            F_SA = float(self.kraefte_widget.get_value("F_SA") or 0)
            F_Z = float(self.kraefte_widget.get_value("F_Z") or 0)  # Set force

            # Use provided delta values
            delta_s = self.delta_s if self.delta_s != 0 else 1e-6
            delta_p = self.delta_p if self.delta_p != 0 else 1e-6
            Phi = self.phi

            # Calculate additional forces
            F_SA = Phi * F_A
            F_PA = (1 - Phi) * F_A  # Force on the intermediate parts
            F_KR = F_V - (1 - Phi) * F_A  # Restklemmkraft
            F_Smax = F_V + F_SA  # Ensure F_Smax is consistent

            # Calculate displacements using the compliances
            f_s_max = F_Smax * delta_s  # Displacement for screw at F_Smax
            f_p_max = F_Mmax * delta_p  # Displacement for clamped parts at F_Mmax
            f_v = F_V * delta_s  # Displacement at preload force
            f_a = F_A * delta_s * Phi  # Displacement under operating force F_A
            delta_ges = delta_s + delta_p
            f_smax_total = F_Smax * delta_ges  # Total displacement at F_Smax

            # Plot spring characteristics with displacement on X-axis and force on Y-axis
            # Schraube (screw) line - blue - fixed from origin
            self.ax.plot([0, f_s_max], [0, F_Smax], 'b-', linewidth=2, label=f'Cs = {1/delta_s:.2e} 1/Nmm')
            
            # Bauteil (part) line - red - fixed from origin
            self.ax.plot([0, f_p_max], [0, F_Mmax], 'r-', linewidth=2, label=f'Cp = {1/delta_p:.2e} 1/Nmm')
            
            # Extended Schraube line (dashed)
            self.ax.plot([f_v, f_smax_total], [F_V, F_Smax], 'b--', linewidth=1.5)

            # Add second sloping line for c-p insertion (red dashed)
            # This is the falling/negative slope line for the clamped parts
            self.ax.plot([f_v, f_v + f_a], [F_V, F_V - F_PA], 'r--', linewidth=1.5, 
                       label='Entlastungslinie Bauteil')
            
            # Calculate additional points for better visualization
            max_displacement = max(f_s_max, f_p_max, f_smax_total, 1e-6)
            x_annotate = max_displacement * 1.1  # Position for annotations on the right
            
            # Define all forces to display with their styles and labels
            forces = [
                {'name': 'F_A', 'value': F_A, 'color': 'green', 'linestyle': '--', 'alpha': 0.7,
                 'label': 'Betriebskraft'},
                {'name': 'F_Kerf', 'value': F_Kerf, 'color': 'purple', 'linestyle': ':', 'alpha': 0.7,
                 'label': 'Erforderliche Klemmkraft'},
                {'name': 'F_Mmin', 'value': F_Mmin, 'color': 'orange', 'linestyle': '--', 'alpha': 0.7,
                 'label': 'Min. Montagekraft'},
                {'name': 'F_Mmax', 'value': F_Mmax, 'color': 'red', 'linestyle': '-', 'alpha': 0.9,
                 'label': 'Max. Montagekraft'},
                {'name': 'F_V', 'value': F_V, 'color': 'black', 'linestyle': '-', 'alpha': 0.8,
                 'label': 'Vorspannkraft'},
                {'name': 'F_Smax', 'value': F_Smax, 'color': 'blue', 'linestyle': '-', 'alpha': 0.8,
                 'label': 'Max. Schraubenkraft'},
                {'name': 'F_SA', 'value': F_SA, 'color': 'teal', 'linestyle': '--', 'alpha': 0.7,
                 'label': 'Schraubenzusatzkraft'},
                {'name': 'F_KR', 'value': F_KR, 'color': 'brown', 'linestyle': ':', 'alpha': 0.7,
                 'label': 'Restklemmkraft'},
                {'name': 'F_PA', 'value': F_PA, 'color': 'magenta', 'linestyle': '--', 'alpha': 0.7,
                 'label': 'Kraft auf Zwischenteil'},
                {'name': 'F_Z', 'value': F_Z, 'color': 'darkgreen', 'linestyle': '-.', 'alpha': 0.7,
                 'label': 'Setzkraft'}
            ]
            
            # Sort forces by value in descending order (biggest first)
            forces = [f for f in forces if f['value'] > 0]  # Only keep positive forces
            forces.sort(key=lambda x: x['value'], reverse=True)
            
            # Calculate max_force and max_displacement for scaling
            max_force = max((force['value'] for force in forces), default=1)
            
            # Calculate positions for arrows (from smallest on left to largest on right)
            num_forces = len(forces)
            if num_forces > 0:
                # Reverse the order to have largest forces on the right
                # Sort forces from smallest to largest
                forces.sort(key=lambda x: x['value'])  # Smallest to largest
                x_positions = np.linspace(0.1 * max_displacement, 0.9 * max_displacement, num_forces)
            else:
                x_positions = []
            
            # Plot vertical lines for each force with arrows at top
            for i, (force, x_pos) in enumerate(zip(forces, x_positions)):
                # Draw a vertical line from top downward
                line_top = max_force * 1.05  # Position for the top of the line
                force_height = line_top - force['value']
                self.ax.plot([x_pos, x_pos], [line_top, force_height], 
                           color=force['color'], linewidth=2, alpha=force['alpha'])
                
                # Add label directly above the arrowhead
                self.ax.text(x_pos, line_top + max_force * 0.02,
                           f"{force['name']} = {force['value']:.1f} N",
                           va='bottom', ha='center', fontsize=9, fontweight='bold',
                           bbox=dict(facecolor='white', alpha=0.9, 
                                  edgecolor=force['color'], boxstyle='round,pad=0.2'))
                
                # Add an arrow exactly at the top of the vertical line
                # The arrow head is exactly at the top of the force line
                self.ax.annotate('', 
                              xy=(x_pos, force_height),  # Arrow tip at exact top of line 
                              xytext=(x_pos, force_height - max_force * 0.05),  # Arrow starts below
                              arrowprops=dict(
                                  arrowstyle='-|>',
                                  lw=3,
                                  color=force['color'],
                                  shrinkA=0,
                                  shrinkB=0,
                                  mutation_scale=15  # Larger arrowhead
                              ),
                              zorder=10)
                
                # Add a small marker at the exact point where the force ends
                self.ax.plot(x_pos, line_top - force['value'], 'o', 
                           markersize=6, 
                           markerfacecolor=force['color'],
                           markeredgecolor='black',
                           markeredgewidth=1,
                           alpha=0.9,
                           zorder=11)
            
            # Add Cp and Cs as red dots with values
            cp = 1/delta_p if delta_p != 0 else float('inf')
            cs = 1/delta_s if delta_s != 0 else float('inf')
            
            # Plot Cp point (1/delta_p)
            if delta_p != 0:
                cp_point = 1/delta_p
                self.ax.plot(0.05 * max_displacement, cp_point, 'ro', markersize=8, label='Cp (Bauteil)')  # Red dot for Cp
                self.ax.text(0.05 * max_displacement, cp_point, f' Cp = {cp:.2e} 1/Nmm', 
                           va='center', ha='left', fontsize=10,
                           bbox=dict(facecolor='white', alpha=0.8, edgecolor='red', boxstyle='round,pad=0.2'))
            
            # Plot Cs point (1/delta_s)
            if delta_s != 0:
                cs_point = 1/delta_s
                self.ax.plot(0.05 * max_displacement, cs_point, 'bo', markersize=8, label='Cs (Schraube)')  # Blue dot for Cs
                self.ax.text(0.05 * max_displacement, cs_point, f' Cs = {cs:.2e} 1/Nmm', 
                           va='center', ha='left', fontsize=10,
                           bbox=dict(facecolor='white', alpha=0.8, edgecolor='blue', boxstyle='round,pad=0.2'))
            
            # Mark important points
            points = [
                {'x': 0, 'y': 0, 'label': 'Ursprung', 'color': 'black'},
                {'x': f_v, 'y': F_V, 'label': f'Schnittpunkt\nF_V = {F_V:.1f} N', 'color': 'red'}
            ]
            
            for point in points:
                self.ax.plot(point['x'], point['y'], 'o', color=point['color'], markersize=8)
                self.ax.annotate(
                    point['label'],
                    xy=(point['x'], point['y']),
                    xytext=(10, 10),
                    textcoords='offset points',
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="none", alpha=0.8)
                )
            
            # Add vertical line at F_V to show the working point
            self.ax.axvline(x=f_v, color='gray', linestyle='--', alpha=0.5)
            
            # Add shaded areas for better visualization
            self.ax.fill_between([0, f_v], [0, F_V], [F_V, F_V], 
                               color='blue', alpha=0.1, label='Arbeitsbereich Schraube')
            self.ax.fill_between([0, f_v], [F_V, F_V], [F_V + F_PA, F_V + F_PA], 
                               color='red', alpha=0.1, label='Arbeitsbereich Bauteil')
            
            # Add annotations for length fractions (displacements)
            # f_smax - length fraction on the screw
            self.ax.annotate(f'f_smax = {f_s_max:.3e} mm',
                           xy=(f_s_max/2, F_Smax/2),
                           xytext=(0.6*f_s_max, 0.3*F_Smax),
                           arrowprops=dict(arrowstyle='->'),
                           bbox=dict(boxstyle="round,pad=0.3", fc="lightyellow", ec="blue", alpha=0.8))
            
            # f_pmax - length fraction on the intermediate
            self.ax.annotate(f'f_pmax = {f_p_max:.3e} mm',
                           xy=(f_p_max/2, F_Mmax/2),
                           xytext=(0.4*f_p_max, 0.7*F_Mmax),
                           arrowprops=dict(arrowstyle='->'),
                           bbox=dict(boxstyle="round,pad=0.3", fc="lightyellow", ec="red", alpha=0.8))
            
            # f_s = f_p - difference in length under operating force F_A
            self.ax.annotate(f'f_s = f_p = {f_a:.3e} mm',
                           xy=(f_v + f_a/2, F_V),
                           xytext=(f_v + 0.7*f_a, F_V - 0.2*F_PA),
                           arrowprops=dict(arrowstyle='->'),
                           bbox=dict(boxstyle="round,pad=0.3", fc="lightyellow", ec="green", alpha=0.8))

            # Set axis labels and legend
            self.ax.set_xlabel('Verschiebung f [mm]')
            self.ax.set_ylabel('Kraft F [N]')
            self.ax.legend(loc='upper right', bbox_to_anchor=(1.0, 1.0), 
                         frameon=True, framealpha=0.9)
            
            # Set grid and axis limits
            self.ax.grid(True, linestyle='--', alpha=0.6)
            self.ax.set_xlim(0, max_displacement * 1.2)
            # Get the maximum force value from the list of force dictionaries
            max_force = max((force['value'] for force in forces), default=1)
            # Increase top limit to make room for arrows and labels
            self.ax.set_ylim(0, max_force * 1.25)
            
            # Configure spines
            for spine in ['top', 'right']:
                self.ax.spines[spine].set_visible(False)
                
            # Add title
            self.ax.set_title('Kraft-Verschiebungs-Diagramm (Bild 3.27)', pad=20, fontsize=12)
            
            # Adjust layout
            self.figure.tight_layout()

            # Rotate the plot to have force on Y-axis and displacement on X-axis
            # (This is already the case based on your axis labels)
            
            # Stack the plots on top of each other
            # This is achieved by layering the various components as we've done above

            self.canvas.draw()

        except (ValueError, TypeError):
            self.ax.text(0.5, 0.5, "Ungültige Werte",
                         ha="center", va="center", transform=self.ax.transAxes)
            self.canvas.draw()

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

        # Platzhalter
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        # Verbindungen der Knöpfe
        about_button.clicked.connect(self.about)
        clear_button.clicked.connect(self.clear_tab)
        example_button.clicked.connect(self.load_example)

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
