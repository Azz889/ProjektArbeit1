import sys, re
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QGridLayout, QTabWidget, QWidget, QComboBox, QVBoxLayout, QPushButton, QHBoxLayout, QLabel, QLineEdit, QScrollArea, QSpacerItem, QSizePolicy, QGroupBox
from PyQt5.QtGui import QDoubleValidator, QValidator
from PyQt5.QtCore import Qt, QLocale

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
        
    def closeEvent(self, event):
        """Clean up matplotlib figure when closing the plot window."""
        try:
            plt.close(self.figure)
        except:
            pass
        event.accept()
        
    def update_plot(self):
        """Update the force-displacement diagram with all missing elements including F_PA, F_z, f_smax, f_pmax, f_s=f_p."""
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
            F_PA = float(self.kraefte_widget.get_value("F_PA") or 0)  # Force on intermediate layer
            F_Z = float(self.kraefte_widget.get_value("F_Z") or 0)  # Set force
            Fz = float(self.kraefte_widget.get_value("Fz") or 0)  # Additional set force

            # Use provided delta values
            delta_s = self.delta_s if self.delta_s != 0 else 1e-6
            delta_p = self.delta_p if self.delta_p != 0 else 1e-6
            Phi = self.phi

            # Calculate displacement components
            f_smax = F_Smax * delta_s  # Displacement component for screw at max force
            f_pmax = F_Mmax * delta_p  # Displacement component for intermediate layer at max force
            f_s = F_A * delta_s  # Displacement of screw under operating force F_A
            f_p = F_A * delta_p  # Displacement of intermediate layer under operating force F_A (f_s = f_p concept)
            f_v = F_V * delta_s  # Displacement at preload force
            f_SA = F_SA * delta_s  # Displacement due to additional screw force
            
            # Calculate spring constants
            c_S = 1/delta_s if delta_s != 0 else 0  # Spring constant for screw
            c_P = 1/delta_p if delta_p != 0 else 0  # Spring constant for clamped parts

            # Set up plot dimensions
            max_displacement = max(f_smax, f_pmax, f_v, f_SA, f_s, f_p, 0.01) * 1.3
            max_force = max(F_Smax, F_Mmax, F_V, F_A, F_PA, F_Z, 1) * 1.3

            # Plot the main spring characteristics
            # Screw line (c_S) - positive slope (blue)
            if f_smax > 0 and F_Smax > 0:
                self.ax.plot([0, f_smax], [0, F_Smax], 'b-', linewidth=3, label='Schraubenlinie (c_S)')
            
            # Clamped parts line (c_P) - negative slope (falling line, red)
            if f_pmax > 0 and F_Mmax > 0:
                # Start from maximum force and go down with negative slope
                f_end = F_Mmax / c_P if c_P > 0 else f_pmax
                self.ax.plot([0, f_end], [F_Mmax, 0], 'r-', linewidth=3, label='Bauteilkennlinie (c_P) - fallend')
            
            # Extended screw line from preload point (dashed blue)
            if f_v > 0 and F_V > 0 and f_smax > f_v:
                self.ax.plot([f_v, f_smax], [F_V, F_Smax], 'b--', linewidth=2, alpha=0.8, label='Erweiterte Schraubenlinie')

            # Plot key points with different markers
            key_points = [
                (f_v, F_V, 'F_V (Vorspannkraft)', 'black', 'o', 10),
                (f_smax, F_Smax, 'F_Smax', 'blue', 's', 8),
                (f_pmax, F_Mmax, 'F_Mmax', 'red', 's', 8),
                (f_SA, F_SA, 'F_SA', 'green', '^', 8),
                (f_s, F_A, 'F_A', 'orange', 'v', 8),
                (f_p, F_PA, 'F_PA (Zwischenlage)', 'cyan', 'D', 8),  # New: Force on intermediate layer
            ]
            
            for x, y, label, color, marker, size in key_points:
                if x > 0 and y > 0:
                    self.ax.plot(x, y, marker, color=color, markersize=size, 
                               markeredgecolor='black', markeredgewidth=1, label=label)
                    self.ax.annotate(f'{label}\n({x:.3f}, {y:.1f})', (x, y), 
                                   xytext=(10, 10), textcoords='offset points',
                                   fontsize=9, ha='left', va='bottom',
                                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

            # Add displacement annotations with vertical lines
            displacement_annotations = [
                (f_smax, 'f_smax', 'blue', 'Längenanteil Schraube'),
                (f_pmax, 'f_pmax', 'red', 'Längenanteil Zwischenlage'),
                (f_s, 'f_s', 'orange', 'Verschiebung Schraube unter F_A'),
                (f_p, 'f_p', 'cyan', 'Verschiebung Zwischenlage unter F_A'),
                (f_v, 'f_V', 'black', 'Verschiebung bei Vorspannkraft'),
                (f_SA, 'f_SA', 'green', 'Verschiebung durch F_SA'),
            ]
            
            for i, (displacement, label, color, description) in enumerate(displacement_annotations):
                if displacement > 0:
                    # Draw vertical dashed line
                    self.ax.axvline(x=displacement, color=color, linestyle=':', alpha=0.6, linewidth=1)
                    # Add label at top
                    y_pos = max_force * (0.9 - i * 0.05)
                    self.ax.text(displacement, y_pos, f'{label}\n{displacement:.3f}mm', 
                               ha='center', va='center', fontsize=8, color=color,
                               bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.7))

            # Add force arrows (stacked/rotated as requested)
            forces_to_show = [
                (F_A, 'F_A', 'orange', 'Betriebskraft'),
                (F_Kerf, 'F_Kerf', 'purple', 'Erforderliche Klemmkraft'),
                (F_Mmin, 'F_Mmin', 'brown', 'Min. Montagekraft'),
                (F_Mmax, 'F_Mmax', 'red', 'Max. Montagekraft'),
                (F_V, 'F_V', 'black', 'Vorspannkraft'),
                (F_Smax, 'F_Smax', 'blue', 'Max. Schraubenkraft'),
                (F_SA, 'F_SA', 'green', 'Schraubenzusatzkraft'),
                (F_PA, 'F_PA', 'cyan', 'Kraft auf Zwischenlage'),  # New
                (F_Z, 'F_Z', 'magenta', 'Setzkraft'),  # New
                (Fz, 'F_z', 'magenta', 'Zusätzliche Setzkraft'),  # New
            ]
            
            # Draw horizontal force arrows at the bottom (stacked)
            arrow_base_y = -max_force * 0.15
            for i, (force, label, color, description) in enumerate(forces_to_show):
                if force > 0:
                    arrow_y = arrow_base_y - i * max_force * 0.03
                    # Draw horizontal arrow
                    self.ax.annotate('', xy=(force * 0.8, arrow_y), xytext=(0, arrow_y),
                                   arrowprops=dict(arrowstyle='->', color=color, lw=2))
                    # Add label
                    self.ax.text(force * 0.4, arrow_y + max_force * 0.01, 
                               f'{label} = {force:.1f}N', 
                               ha='center', va='bottom', fontsize=8, color=color, 
                               fontweight='bold')

            # Add information box about improvements
            info_text = (
                'Vervollständigtes Diagramm:\n'
                '✓ F_PA: Kraft auf Zwischenlage\n'
                '✓ F_z: Setzkraft\n'
                '✓ f_smax: Längenanteil Schraube\n'
                '✓ f_pmax: Längenanteil Zwischenlage\n'
                '✓ f_s = f_p: Verschiebung unter F_A\n'
                '✓ Fallende Linie c_P\n'
                '✓ Gestapelte Kraftpfeile\n'
                '✓ Rotierte Darstellung'
            )
            
            self.ax.text(0.02, 0.98, info_text, transform=self.ax.transAxes, fontsize=9,
                        verticalalignment='top', horizontalalignment='left',
                        bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgreen', alpha=0.8))

            # Configure plot appearance
            self.ax.set_xlabel('Verschiebung f (mm)', fontsize=12, fontweight='bold')
            self.ax.set_ylabel('Kraft F (N)', fontsize=12, fontweight='bold')
            self.ax.set_title('Vollständiges Kraft-Verschiebungs-Diagramm (Bild 3.27)\n'
                            'mit allen fehlenden Elementen', fontsize=14, fontweight='bold')
            
            # Set axis limits
            self.ax.set_xlim(-max_displacement * 0.05, max_displacement)
            self.ax.set_ylim(arrow_base_y * 1.2, max_force)
            
            # Add grid
            self.ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
            
            # Add legend
            self.ax.legend(loc='upper right', bbox_to_anchor=(0.98, 0.85), fontsize=9)
            
            # Tight layout
            plt.tight_layout()
            self.canvas.draw()

        except (ValueError, TypeError, AttributeError) as e:
            # Clear the plot and show error message
            self.ax.clear()
            self.ax.text(0.5, 0.5, f"Fehler bei der Darstellung:\n{str(e)}\n\nBitte alle erforderlichen Werte eingeben.",
                         ha="center", va="center", transform=self.ax.transAxes, fontsize=12,
                         bbox=dict(boxstyle='round,pad=0.5', facecolor='lightcoral', alpha=0.8))
            self.ax.set_title('Fehler im Diagramm')
            self.canvas.draw()
        except Exception as e:
            # Handle any other unexpected errors
            print(f"Unexpected error in plot update: {e}")
            self.ax.clear()
            self.ax.text(0.5, 0.5, f"Unerwarteter Fehler:\n{str(e)}\n\nBitte prüfen Sie die Eingaben.",
                         ha="center", va="center", transform=self.ax.transAxes, fontsize=12,
                         bbox=dict(boxstyle='round,pad=0.5', facecolor='lightcoral', alpha=0.8))
            self.ax.set_title('Unerwarteter Fehler')
            self.canvas.draw()

class MainWindow(QMainWindow):
    """
    Hauptfenster für das Schraubenberechnungsprogramm.
    """
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Schraubenberechnung")
        self.resize(800, 600)

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
        variables = ["F_A", "F_Kerf", "F_Mmin", "F_Mmax", "F_V", "F_Smax", "F_PA", "F_Z", "Fz", 
                    "delta_s", "delta_p", "Phi", "f_smax", "f_pmax", "f_s", "f_p"]
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
        self._updating_fields = False  # Flag to prevent recursion

    def show_plot(self):
        """Show the plot in a new window if all required fields are filled."""
        # Core required fields for basic plot functionality
        required_fields = ["F_A", "F_Mmin", "F_Mmax", "F_V", "F_Smax", "delta_s", "delta_p", "Phi"]
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
            self.plot_window = PlotWindow(self.kraefte_widget, self.nachgiebigkeit_widget, delta_s, delta_p, phi, self)  # Fixed: Changed 'Phi' to 'phi'
        else:
            # Update the existing plot window with new values
            self.plot_window.delta_s = delta_s
            self.plot_window.delta_p = delta_p
            self.plot_window.phi = phi
            self.plot_window.update_plot()
            
        self.plot_window.show()
        self.plot_window.raise_()  # Bring window to front
        self.plot_window.activateWindow()  # Activate the window

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
        """
        # Prevent recursion
        if self._updating_fields:
            return
            
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
            # Recalculate to update dependent values
            self.calculate()
        except Exception as e:
            print(f"Error updating value: {e}")  # Debugging output

    def update_input_fields(self):
        """
        Updates the input fields with the current values from KraefteWidget and NachgiebigkeitWidget.
        """
        # Set flag to prevent recursion
        self._updating_fields = True
        
        try:
            for var in self.input_fields:
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
                if value is not None:
                    formatted_value = f"{value:.4e}" if (abs(value) < 1e-3 or abs(value) > 1e4) else f"{value:.4f}".rstrip('0').rstrip('.')
                    formatted_value = formatted_value.replace('.', ',')
                    self.input_fields[var].setText(formatted_value)
                else:
                    self.input_fields[var].setText("")
        finally:
            # Always reset flag, even if an exception occurs
            self._updating_fields = False

    def about(self):
        QMessageBox.about(self, "Über Uns", "Dieses Tool wurde innerhalb einer Projektarbeit von<br>Hannah Meuriße und Oliver Simon Kania entwickelt<br><br>Version 1.0<br>22.07.2024<br><br><br> P.S.: Wenn du das hier ließt, weil du eine Übung prokrastinierst: Nicht verzweifeln du schaffst das!!!")

    def calculate(self):
        self.gewinde_widget.calculate()
        self.werkstoff_widget.calculate()
        self.nachgiebigkeit_widget.calculate()
        self.nachgiebigkeit_widget.delta_calc()
        self.kraefte_widget.calculate()
        self.dauerfestigkeit_widget.calculate()

    def clear_tab(self):
        # Temporarily disable updates to prevent recursion
        self._updating_fields = True
        try:
            for line_edit in self.findChildren(QLineEdit):
                line_edit.clear()
            if self.plot_window is not None:
                self.plot_window.close()
                self.plot_window = None
        finally:
            self._updating_fields = False

    def closeEvent(self, event):
        """Clean up resources when closing the main window."""
        try:
            if self.plot_window is not None:
                self.plot_window.close()
                self.plot_window = None
        except:
            pass
        
        try:
            # Close any remaining matplotlib figures
            plt.close('all')
        except:
            pass
            
        print("Programm wird geschlossen")
        event.accept()

    def load_example(self):
        selected_example = self.example_selector.currentText()
        self.clear_tab()  # Clear previous values
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
        self.calculate()  # Recalculate all values

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

    def validate(self, input, pos):
        if input in ["", "-", ",", ".", "-.", "-,", "e", "E", "e-", "E-", "-e", "-E", "-e-", "-E-"]:
            return (QValidator.Intermediate, input, pos)
        modified_input = input.replace(',', '.')
        if any(modified_input.endswith(suffix) for suffix in ["e", "E", "e-", "E-", "e+", "E+"]):
            return (QValidator.Intermediate, input, pos)
        try:
            value = float(modified_input)
        except ValueError:
            return (QValidator.Invalid, input, pos)
        if self.bottom() <= value <= self.top():
            return (QValidator.Acceptable, input, pos)
        return (QValidator.Invalid, input, pos)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
