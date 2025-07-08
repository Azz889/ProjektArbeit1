from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QLineEdit, QComboBox, QSplitter, QTreeView
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDoubleValidator
from pandas import read_excel
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class KraefteWidget(QWidget):
    """
    Klasse zur Berechnung der Schraubenkräfte.
    """
    # Define the signal to notify when values change
    valuesChanged = pyqtSignal()

    def __init__(self, validator, parent=None):
        """
        Initialisiert das Widget mit einem Validator und einem optionalen Elternobjekt.
        """
        super().__init__(parent)
        self.validator = validator
        self.mainwindow = parent
        self.line_edits = {}
        self.setup_ui()
        for line_edit in self.line_edits.values():
            line_edit.editingFinished.connect(self.calculate)

    def setup_ui(self):
        """
        Initialisiert das Benutzeroberflächen-Layout für die Berechnung von Kräften.
        Fügt alle erforderlichen UI-Elemente (Titel, Untertitel, Eingabefelder) zum Scrollbereich hinzu.
        """
        self.line_edits = {}

        # Main splitter for file structure and force widget
        main_splitter = QSplitter(Qt.Horizontal)
        layout = QGridLayout(self)
        layout.addWidget(main_splitter)

        # File structure (left panel)
        from PyQt5.QtWidgets import QFileSystemModel
        file_model = QFileSystemModel()
        file_model.setRootPath("")  # Set to your project directory (e.g., "PROJEKTARBEIT1-MAIN1")
        tree_view = QTreeView()
        tree_view.setModel(file_model)
        tree_view.setRootIndex(file_model.index("PROJEKTARBEIT1-MAIN1"))  # Adjust path to your project
        main_splitter.addWidget(tree_view)

        # Scroll content for force calculations (right panel)
        scroll_content = QWidget()
        scroll_layout = QGridLayout(scroll_content)
        main_splitter.addWidget(scroll_content)

        title = QLabel("""<p style="font-size:12pt;">Kräfte</p>""")
        scroll_layout.addWidget(title)

        # Anziehfaktorberechnung alpha_A
        subtitle_alpha_A = QLabel("""<p style="font-size:10pt;"><u>Anziehfaktorberechnung</u></p>""")
        scroll_layout.addWidget(subtitle_alpha_A)

        # Anziehfaktor alpha_A Comboboxes
        alpha_a_label = QLabel('<span style="color: red;">*</span> ' + "Anziehfaktor auswählen")
        self.alpha_a = QComboBox()
        alpha_a_2_label = QLabel('<span style="color: red;">*</span> ' + "Berechnung für")
        self.alpha_a_2 = QComboBox()
        self.alpha_a_2.addItems(["Anwendungsfall/Sicherheit", "Festigkeit"])
        self.load_alpha_a()
        scroll_layout.addWidget(alpha_a_label, 3, 0)
        scroll_layout.addWidget(self.alpha_a, 3, 1)
        scroll_layout.addWidget(alpha_a_2_label, 4, 0)
        scroll_layout.addWidget(self.alpha_a_2, 4, 1)
        self.alpha_a.currentIndexChanged.connect(self.set_alpha_a)
        self.alpha_a_2.currentIndexChanged.connect(self.set_alpha_a)
        # Anziehfaktor Lineedit-Zeile
        self.add_lineedits(4, scroll_layout, [[1, "alpha_A", "", "Anziefaktor \u03B1<sub>A</sub>", "aus Tabelle 3.7 \u03B1<sub>A</sub>=F<sub>Mmax</sub>/F<sub>Mmin</sub> (3.23)"]])

        # Setzkraftberechnung
        subtitle_F_Z = QLabel("""<p style="font-size:10pt;"><u>Setzkraftberechnung</u></p>""")
        scroll_layout.addWidget(subtitle_F_Z)

        # Gemittelte Rautiefe Eingabe
        self.add_lineedits(6, scroll_layout, [[0, "R_z", "", "Gemittelte Rautiefe R<sub>z</sub>:", ""]])

        # Belastung Zug/Druck oder Schub als ComboBox
        belastung_label = QLabel("Belastung Zug/Druck oder Schub:")
        self.belastung = QComboBox()
        self.belastung.addItems(["Zug/Druck", "Schub"])
        scroll_layout.addWidget(belastung_label, 8, 0)
        scroll_layout.addWidget(self.belastung, 8, 1)
        self.belastung.currentIndexChanged.connect(self.calculate)

        # Setzkraft Lineedit-Zeile
        self.add_lineedits(8, scroll_layout, [
            [0, "kopf_mutterauflagen", "", "Anzahl Kopf- oder Mutterauflagen:", ""],
            [0, "trennfugen", "", "Anzahl innerer Trennfugen:", ""],
            [0, "gewinde", "", "Anzahl Gewinde:", ""],
            [0, "f_Z", "µm", "Setzbetrag f<sub>Z</sub> = ∑f<sub>ZF</sub>", "F<sub>Z</sub>=f<sub>Z</sub> / (\u03B4<sub>s</sub> + \u03B4<sub>p</sub>) (3.31)"],
            [0, "F_Z", "N", "Setzkraft F<sub>Z</sub>", " F<sub>Z</sub>=f<sub>Z</sub> / (\u03B4<sub>s</sub> + \u03B4<sub>p</sub>) (3.31)"]])

        # Parameter
        subtitle_par = QLabel("""<p style="font-size:10pt;"><u>Parameter</u></p>""")
        scroll_layout.addWidget(subtitle_par)

        self.add_lineedits(14, scroll_layout, [
            [1, "my", "", "Reibwert μ", ""],
            [0, "delta_s", "", "Nachgiebigkeit Schraube \u03B4<sub>s</sub>", "Aus Nachgiebigkeit"],
            [0, "delta_p", "", "Nachgiebigkeit Zwischenlage \u03B4<sub>p</sub>", "Aus Nachgiebigkeit"],
            [0, "Phi", "", "Verspannungsfaktor \u03C6", " \u03C6 = \u03B4<sub>p</sub> / (\u03B4<sub>s</sub> + \u03B4<sub>p</sub>)(3.26)"],
            [0, "Phi_n", "", "Verspannungsfaktor \u03C6<sub>n</sub>", "Verspannungsfaktor für nicht gestützte Verbindung"],
        ])

        # Betriebskräfte
        subtitle_F_A = QLabel("""<p style="font-size:10pt;"><u>Betriebskräfte</u></p>""")
        scroll_layout.addWidget(subtitle_F_A)

        self.add_lineedits(19, scroll_layout, [
            [1, "F_A", "N", "Betriebskraft F<sub>A</sub>", ""],
            [1, "F_Ao", "N", "Obergrenze Dynamischer Betriebsfaktor F<sub>Ao</sub>", ""],
            [1, "F_Au", "N", "Untergrenze Dynamischer Betriebsfaktor F<sub>Au</sub>", ""],
            [1, "F_Q", "N", "Querkraft F<sub>Q</sub>", ""]
        ])

        # Weitere Kräfte
        subtitle_F = QLabel("""<p style="font-size:10pt;"><u>Weitere Kräfte</u></p>""")
        scroll_layout.addWidget(subtitle_F)

        eingaben = [
            [0, "F_V", "N", "Vorspannkraft F<sub>V</sub>", "F<sub>V</sub> = F<sub>KR</sub>+(1-\u03C6)*F<sub>A</sub>  (3.28)   <br> F<sub>V</sub>=F<sub>Mmin</sub>-F<sub>Z</sub> (Bild 3.27)"],
            [0, "F_KR", "N", "Restklemmkraft F<sub>KR</sub>", "F<sub>KR</sub>=F<sub>V</sub>+(1-\u03C6)*F<sub>A</sub> (3.28) <br> F<sub>KR</sub>=F<sub>Smax</sub>-F<sub>A</sub> (Bild 3.26)"],
            [0, "F_SA", "N", "Schraubenzusatzkraft F<sub>SA</sub>", "F<sub>SA</sub>=\u03C6*F<sub>A</sub>"],
            [0, "F_PA", "N", "Hilfswert F<sub>PA</sub>", "F<sub>PA</sub>=F<sub>SA</sub>-F<sub>A</sub>"],
            [0, "F_Smax", "N", "Maximale Schraubenkraft F<sub>Smax</sub>", "F<sub>Smax</sub> = F<sub>Mmax</sub> + F<sub>SA</sub> <br>(Bild 3.27,3.25)  <br>F<sub>Smax</sub> = F<sub>KR</sub> + F<sub>A</sub> (Bild 3.26)"],
            [0, "F_Mmin", "N", "Minimale Montagekraft F<sub>Mmin</sub>", " F<sub>Mmin</sub>=F<sub>Mmax</sub>/ \u03B1<sub>A</sub> (3.23) <br> F<sub>Mmin</sub>= F<sub>V</sub>+F<sub>Z</sub> (Bild 3.27)"],
            [0, "F_Mmax", "N", "Maximale Montagekraft F<sub>Mmax</sub>", " F<sub>Mmax</sub>=\u03B1<sub>A</sub>*F<sub>Mmin</sub> (3.23) <br>F<sub>Mmax</sub> = F<sub>Smax</sub> - F<sub>SA</sub> (Bild 3.27)"],
            [0, "F_Kerf", "N", "Erforderliche Restklemmkraft F<sub>Kerf</sub>", " F<sub>Kerf</sub>=F<sub>Verf</sub>-(1-\u03C6)*F<sub>Ao</sub>(3.30)<br>F<sub>Kerf</sub> = F<sub>Mmin</sub> -F<sub>Z</sub> - (1-\u03C6)*F<sub>Ao</sub> (Bild 3.27)<br> oft =F<sub渣erf</sub>"],
            [0, "F_Verf", "N", "Erforderliche Vorspannkraft F<sub>Verf</sub> ", "F<sub>Verf</sub>=F<sub>Kerf</sub>+(1-\u03C6)*F<sub>Ao</sub> (3.30)"],
            [0, "F_Sm", "N", "Konstante Mittellast F<sub>Sm</sub> ", " F<sub>Sm</sub>=F<sub>V</sub>+\u03C6*(F<sub>Ao</sub>+F<sub>Au</sub>)/2<br> (3.36)"],
            [0, "F_SAa", "N", "Schraubenausschlagskraft F<sub>SAa</sub> \u00B1", "F<sub>SAa</sub> =\u00B1 \u03C6*(F<sub>Ao</sub>-F<sub>Au</sub>)/2 (3.37)"],
            [0, "F", "N", "Externe Betriebskraft F", "Extern angelegte Kraft auf das System"],
            [0, "F_S", "N", "Zusatzkraft Schraube F<sub>S</sub>", "F<sub>S</sub> = \u03C6 * F"],
            [0, "F_P", "N", "Entlastung Bauteile F<sub>P</sub>", "F<sub>P</sub> = (1 - \u03C6) * F"],
            [0, "F_Erv", "N", "Ergibekraft Schraube F<sub>Erv</sub>", "Maximale Kraft vor plastischer Verformung der Schraube"],
            [0, "F_Erf", "N", "Erforderliche Kraft F<sub>Erf</sub>", "Mindestkraft für die Verbindung"],
            [0, "F_PM", "N", "Bauteilanteil der maximalen Kraft F<sub>PM</sub>", "F<sub>PM</sub> = F_Mmax - F_SA"],
            [0, "Fz", "N", "Zusätzliche Kraft F<sub>z</sub>", "Zusätzliche Kraft basierend auf Setzbetrag (abhängig von F_Z)"],
            [0, "f_SMmax", "mm", "Abszisse f<sub>SMmax</sub>", "Abszisse der Schraubenkennlinie"],
            [0, "f_PMmax", "mm", "Abszisse f<sub>PMmax</sub>", "Abszisse der Bauteilkennlinie"],
            [0, "f_smax", "mm", "Längenanteil Schraube f<sub>smax</sub>", "Verschiebung der Schraube bei maximaler Kraft"],
            [0, "f_pmax", "mm", "Längenanteil Zwischenlage f<sub>pmax</sub>", "Verschiebung der Zwischenlage bei maximaler Kraft"],
            [0, "f_s", "mm", "Verschiebung Schraube f<sub>s</sub>", "Verschiebung der Schraube unter Betriebskraft F_A"],
            [0, "f_p", "mm", "Verschiebung Zwischenlage f<sub>p</sub>", "Verschiebung der Zwischenlage unter Betriebskraft F_A"],
            [0, "c_S", "N/mm", "Steigung Schraubenlinie c<sub>S</sub>", "c<sub>S</sub> = ΔF/Δf Schraube"],
            [0, "c_P", "N/mm", "Steigung Bauteillinie c<sub>P</sub>", "c<sub>P</sub> = ΔF/Δf Bauteil"],
            [0, "f_SA", "mm", "Abszisse f<sub>SA</sub>", "Abszisse durch Zusatzkraft Schraube"],
            [0, "f_V", "mm", "Verschiebung f bei F<sub>V</sub> (Schraube)", "Verschiebung der Schraube bei Vorspannkraft"],
            [0, "f_Smax_total", "mm", "Verschiebung f bei F<sub>Smax</sub> (Gesamt)", "Gesamtverschiebung bei maximaler Schraubenkraft"],
        ]

        self.add_lineedits(24, scroll_layout, eingaben)

        # Add plot area
        self.figure = plt.Figure()
        self.canvas = FigureCanvas(self.figure)
        scroll_layout.addWidget(self.canvas, 40, 0, 1, 3)  # Adjust row and span as needed

    def add_lineedits(self, index, layout, eingaben):
        """
        Fügt der Benutzeroberfläche die LineEdits aus setup_ui hinzu.
        """
        for pflicht, param, unit, name, verweis in eingaben:
            index += 1
            if pflicht == 1:
                name_label = QLabel('<span style="color: red;">*</span> ' + name)
            else:
                name_label = QLabel(name)

            line_edit = QLineEdit()
            line_edit.setObjectName(param)
            line_edit.setValidator(self.validator)
            line_edit.setToolTip(verweis)
            unit_label = QLabel(unit)

            layout.addWidget(name_label, index, 0)
            layout.addWidget(line_edit, index, 1)
            layout.addWidget(unit_label, index, 2)
            self.line_edits[param] = line_edit

    def calculate(self):
        """
        Berechnet verschiedene Parameter basierend auf den Werten der Eingabefelder.
        """
        delta_s = self.get_value("delta_s")
        delta_p = self.get_value("delta_p")
        Phi = self.get_value("Phi")
        F_Mmin = self.get_value("F_Mmin")
        F_Mmax = self.get_value("F_Mmax")
        alpha_A = self.get_value("alpha_A")
        F_Z = self.get_value("F_Z")
        f_Z = self.get_value("f_Z")
        F_A = self.get_value("F_A")
        F_V = self.get_value("F_V")
        F_Smax = self.get_value("F_Smax")
        F_SA = self.get_value("F_SA")
        F_PA = self.get_value("F_PA")
        F_KR = self.get_value("F_KR")
        F_Ao = self.get_value("F_Ao")
        F_Au = self.get_value("F_Au")
        F_Verf = self.get_value("F_Verf")
        F_Kerf = self.get_value("F_Kerf")
        F_Q = self.get_value("F_Q")
        my = self.get_value("my")
        R_Z = self.get_value("R_z")
        belastung = self.belastung.currentText()
        kopf_mutterauflagen = self.get_value("kopf_mutterauflagen")
        trennfugen = self.get_value("trennfugen")
        gewinde = self.get_value("gewinde")
        F = self.get_value("F")
        F_S = self.get_value("F_S")
        F_P = self.get_value("F_P")
        F_Erv = self.get_value("F_Erv")
        F_Erf = self.get_value("F_Erf")
        F_PM = self.get_value("F_PM")
        Fz = self.get_value("Fz")
        f_SMmax = self.get_value("f_SMmax")
        f_PMmax = self.get_value("f_PMmax")
        c_S = self.get_value("c_S")
        c_P = self.get_value("c_P")
        f_SA = self.get_value("f_SA")
        f_V = self.get_value("f_V")
        f_Smax_total = self.get_value("f_Smax_total")

        for i in range(3):
            if alpha_A is not None and alpha_A != 0 and F_Mmax is not None:
                F_Mmin = F_Mmax / alpha_A
                self.set_value("F_Mmin", F_Mmin)
            elif alpha_A is not None and F_Mmin is not None:
                F_Mmax = alpha_A * F_Mmin
                self.set_value("F_Mmax", F_Mmax)

            if (delta_s != 0 or delta_p != 0) and (delta_s is not None and delta_p is not None):
                Phi = delta_p / (delta_s + delta_p)
                self.set_value("Phi", Phi)

                if f_Z is not None:
                    F_Z = f_Z * 0.001 / (delta_s + delta_p)
                    self.set_value("F_Z", F_Z)

            if Phi is not None and (F_A is not None or F_Ao is not None) and F_Z is not None and F_KR is not None:
                if F_A is not None:
                    F_V = F_KR + (1 - Phi) * F_A
                    self.set_value("F_V", F_V)
                elif F_Ao is not None:
                    F_V = F_KR + (1 - Phi) * F_Ao
                    self.set_value("F_V", F_V)

            if Phi is not None and F_A is not None and F_V is not None:
                F_KR = F_V + (1 - Phi) * F_A
                self.set_value("F_KR", F_KR)

            if Phi is not None and (F_A is not None or F_Ao is not None):
                if F_A is not None:
                    F_SA = Phi * F_A
                    self.set_value("F_SA", F_SA)
                elif F_Ao is not None:
                    F_SA = Phi * F_Ao
                    self.set_value("F_SA", F_SA)

            if F_SA is not None and F_A is not None:
                F_PA = F_A - F_SA
                self.set_value("F_PA", F_PA)

            if F is not None and Phi is not None:
                F_S = Phi * F
                F_P = (1 - Phi) * F
                self.set_value("F_S", F_S)
                self.set_value("F_P", F_P)

            if F_Mmin is not None and F_Z is not None:
                F_V = F_Mmin - F_Z
                self.set_value("F_V", F_V)

            if F_V is not None and F_Z is not None:
                F_Mmin = F_V + F_Z
                self.set_value("F_Mmin", F_Mmin)

            if F_Mmax is not None and F_SA is not None:
                F_Smax = F_Mmax + F_SA
                self.set_value("F_Smax", F_Smax)

            if F_Smax is not None and F_SA is not None:
                F_Mmax = F_Smax - F_SA
                self.set_value("F_Mmax", F_Mmax)

            if F_Smax is not None and F_A is not None:
                F_KR = F_Smax - F_A
                self.set_value("F_KR", F_KR)

            if Phi is not None and F_Ao is not None and F_Au is not None:
                F_SAa = Phi * (F_Ao - F_Au) / 2
                self.set_value("F_SAa", F_SAa)

            if Phi is not None and F_V is not None and F_Ao is not None and F_Au is not None:
                F_Sm = F_V + Phi * (F_Ao + F_Au) / 2
                self.set_value("F_Sm", F_Sm)

            if F_Mmin is not None and F_Z is not None and F_A is not None and Phi is not None:
                F_Kerf = F_Mmin - F_Z - (1 - Phi) * F_A
                self.set_value("F_Kerf", F_Kerf)
            elif F_Verf is not None and Phi is not None and F_Ao is not None:
                F_Kerf = F_Verf - (1 - Phi) * F_Ao
                self.set_value("F_Kerf", F_Kerf)
            elif F_Verf is not None and F_Ao == 0:
                F_Kerf = F_Verf
                self.set_value("F_Kerf", F_Kerf)
                self.set_value("F_Verf", F_Kerf)

            if F_Kerf is not None and Phi is not None and F_Ao is not None:
                F_Verf = F_Kerf + (1 - Phi) * F_Ao
                self.set_value("F_Verf", F_Verf)
            elif my is not None and F_Q is not None:
                F_Verf = F_Q / my
                self.set_value("F_Verf", F_Verf)
                self.set_value("F_Kerf", F_Verf)

            if R_Z is not None and gewinde is not None and kopf_mutterauflagen is not None and trennfugen is not None:
                f_ZF = {
                    1: {"Zug/Druck": [3, 2.5, 1.5], "Schub": [3, 3, 2]},
                    2: {"Zug/Druck": [3, 3, 2], "Schub": [3, 4.5, 2.5]},
                    3: {"Zug/Druck": [3, 4, 3], "Schub": [3, 6.5, 3.5]}
                }

                if R_Z < 10:
                    index = 1
                elif R_Z < 40:
                    index = 2
                elif R_Z < 160:
                    index = 3
                else:
                    print("Ungültige Rautiefe")
                    return None

                f_Z_values = f_ZF[index][belastung]
                f_Z = f_Z_values[0] * gewinde + f_Z_values[1] * kopf_mutterauflagen + f_Z_values[2] * trennfugen
                self.set_value("f_Z", f_Z)

            if F_Mmax is not None and F_SA is not None:
                F_PM = F_Mmax - F_SA
                self.set_value("F_PM", F_PM)

            if F_Z is not None:
                Fz = F_Z
                self.set_value("Fz", Fz)

            if F_Smax is not None and F_Erv is None:
                F_Erv = 1.5 * F_Smax
                self.set_value("F_Erv", F_Erv)

            if F_Kerf is not None:
                F_Erf = F_Kerf
                self.set_value("F_Erf", F_Erf)

            if F_Smax is not None and delta_s is not None and delta_s != 0:
                f_SMmax = F_Smax * delta_s
                self.set_value("f_SMmax", f_SMmax)

            if F_Mmax is not None and delta_p is not None and delta_p != 0:
                f_PMmax = F_Mmax * delta_p
                self.set_value("f_PMmax", f_PMmax)

            # Calculate f_smax and f_pmax (displacement components at max forces)
            if F_Smax is not None and delta_s is not None and delta_s != 0:
                f_smax = F_Smax * delta_s
                self.set_value("f_smax", f_smax)

            if F_Mmax is not None and delta_p is not None and delta_p != 0:
                f_pmax = F_Mmax * delta_p
                self.set_value("f_pmax", f_pmax)

            # Calculate f_s = f_p (displacement under operating force F_A)
            if F_A is not None and delta_s is not None and delta_p is not None:
                f_s_fp = F_A * (delta_s + delta_p) / 2  # Equal displacement under F_A
                self.set_value("f_s", f_s_fp)
                self.set_value("f_p", f_s_fp)

            if F_Smax is not None and f_SMmax is not None and f_SMmax != 0:
                c_S = F_Smax / f_SMmax
                self.set_value("c_S", c_S)

            if F_Mmax is not None and f_PMmax is not None and f_PMmax != 0:
                c_P = F_Mmax / f_PMmax
                self.set_value("c_P", c_P)

            if F_SA is not None and delta_s is not None and delta_s != 0:
                f_SA = F_SA * delta_s
                self.set_value("f_SA", f_SA)

            if F_V is not None and delta_s is not None and delta_s != 0:
                f_V = F_V * delta_s
                self.set_value("f_V", f_V)

            if F_Smax is not None and delta_s is not None and delta_s != 0:
                f_Smax_total = F_Smax * delta_s
                self.set_value("f_Smax_total", f_Smax_total)

        self.mainwindow.dauerfestigkeit_widget.calculate()
        self.update_plot()

    def update_plot(self):
        """
        Updates the Matplotlib plot with the calculated force-displacement diagram.
        This creates a comprehensive force-displacement diagram (Bild 3.27) with all missing elements.
        """
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # Get calculated values with fallbacks
        delta_s = self.get_value("delta_s") or 1e-6
        delta_p = self.get_value("delta_p") or 1e-6
        Phi = self.get_value("Phi") or 0
        f_Z = self.get_value("f_Z") or 0
        F_V = self.get_value("F_V") or 0
        F_Smax = self.get_value("F_Smax") or 0
        F_KR = self.get_value("F_KR") or 0
        F_Mmin = self.get_value("F_Mmin") or 0
        F_Mmax = self.get_value("F_Mmax") or 0
        F_SA = self.get_value("F_SA") or 0
        F_PA = self.get_value("F_PA") or 0
        F_A = self.get_value("F_A") or 0
        F_Kerf = self.get_value("F_Kerf") or 0
        F_Z = self.get_value("F_Z") or 0
        Fz = self.get_value("Fz") or 0
        
        # Calculate displacement values
        f_smax = self.get_value("f_smax") or (F_Smax * delta_s if F_Smax and delta_s else 0)
        f_pmax = self.get_value("f_pmax") or (F_Mmax * delta_p if F_Mmax and delta_p else 0)
        f_s = self.get_value("f_s") or (F_A * delta_s if F_A and delta_s else 0)
        f_p = self.get_value("f_p") or (F_A * delta_p if F_A and delta_p else 0)
        f_V = self.get_value("f_V") or (F_V * delta_s if F_V and delta_s else 0)
        f_SA = self.get_value("f_SA") or (F_SA * delta_s if F_SA and delta_s else 0)
        
        # Calculate spring constants
        c_S = 1/delta_s if delta_s != 0 else 0  # Spring constant for screw
        c_P = 1/delta_p if delta_p != 0 else 0  # Spring constant for clamped parts
        
        # Set up the plot with displacement on X-axis and force on Y-axis
        max_displacement = max(f_smax, f_pmax, f_V, f_SA, 0.01) * 1.2
        max_force = max(F_Smax, F_Mmax, F_V, F_A, 1) * 1.2
        
        # Plot the main spring characteristics
        # Screw line (c_S) - positive slope
        if f_smax > 0 and F_Smax > 0:
            ax.plot([0, f_smax], [0, F_Smax], 'b-', linewidth=2, label='Schraubenlinie (c_S)')
        
        # Clamped parts line (c_P) - negative slope (falling line)
        if f_pmax > 0 and F_Mmax > 0:
            # Start from maximum force and go down (negative slope)
            ax.plot([0, f_pmax], [F_Mmax, F_Mmax - c_P * f_pmax], 'r-', linewidth=2, label='Bauteilkennlinie (c_P)')
        
        # Extended screw line from preload point
        if f_V > 0 and F_V > 0 and f_smax > f_V:
            ax.plot([f_V, f_smax], [F_V, F_Smax], 'b--', linewidth=1.5, alpha=0.7)
        
        # Plot key points
        key_points = [
            (f_V, F_V, 'F_V', 'black', 'o'),
            (f_smax, F_Smax, 'F_Smax', 'blue', 's'),
            (f_pmax, F_Mmax, 'F_Mmax', 'red', 's'),
            (f_SA, F_SA, 'F_SA', 'green', '^'),
            (f_s, F_A, 'F_A', 'orange', 'v'),
        ]
        
        for x, y, label, color, marker in key_points:
            if x > 0 and y > 0:
                ax.plot(x, y, marker, color=color, markersize=8, label=label)
                ax.annotate(label, (x, y), xytext=(5, 5), textcoords='offset points',
                           fontsize=10, ha='left', va='bottom')
        
        # Add force arrows at the bottom (rotated as requested)
        arrow_y = -max_force * 0.08
        forces_to_annotate = [
            (F_A, 'F_A', 'orange'),
            (F_Kerf, 'F_Kerf', 'purple'),
            (F_Mmin, 'F_Mmin', 'brown'),
            (F_Mmax, 'F_Mmax', 'red'),
            (F_V, 'F_V', 'black'),
            (F_Smax, 'F_Smax', 'blue'),
            (F_SA, 'F_SA', 'green'),
            (F_PA, 'F_PA', 'cyan'),
            (F_Z, 'F_Z', 'magenta'),
        ]
        
        # Draw stacked arrows (übereinander-stecken)
        for i, (force, label, color) in enumerate(forces_to_annotate):
            if force > 0:
                arrow_offset = arrow_y - i * max_force * 0.02
                # Draw horizontal arrow
                ax.annotate('', xy=(force, arrow_offset), xytext=(0, arrow_offset),
                           arrowprops=dict(arrowstyle='->', color=color, lw=2))
                # Add label
                ax.text(force/2, arrow_offset + max_force * 0.01, label, 
                       ha='center', va='bottom', fontsize=9, color=color, fontweight='bold')
        
        # Add displacement annotations on X-axis
        displacement_annotations = [
            (f_smax, 'f_smax', 'blue'),
            (f_pmax, 'f_pmax', 'red'),
            (f_s, 'f_s', 'orange'),
            (f_p, 'f_p', 'orange'),
            (f_V, 'f_V', 'black'),
            (f_SA, 'f_SA', 'green'),
        ]
        
        for i, (displacement, label, color) in enumerate(displacement_annotations):
            if displacement > 0:
                y_pos = max_force + i * max_force * 0.05
                ax.plot([displacement, displacement], [0, y_pos], '--', color=color, alpha=0.5)
                ax.text(displacement, y_pos, label, ha='center', va='bottom', 
                       fontsize=9, color=color, rotation=90)
        
        # Add grid and labels
        ax.grid(True, alpha=0.3)
        ax.set_xlabel('Verschiebung f (mm)', fontsize=12)
        ax.set_ylabel('Kraft F (N)', fontsize=12)
        ax.set_title('Kraft-Verschiebungs-Diagramm (Bild 3.27)\nmit allen Elementen', fontsize=14, fontweight='bold')
        
        # Set axis limits
        ax.set_xlim(-max_displacement * 0.1, max_displacement)
        ax.set_ylim(arrow_y * 1.5, max_force * 1.3)
        
        # Add legend
        ax.legend(loc='upper right', fontsize=10)
        
        # Add annotations for missing elements
        info_text = (
            'Ergänzte Elemente:\n'
            '• F_PA: Kraft auf Zwischenlage\n'
            '• F_z: Setzkraft\n'
            '• f_smax: Längenanteil Schraube\n'
            '• f_pmax: Längenanteil Zwischenlage\n'
            '• f_s = f_p: Verschiebung unter F_A\n'
            '• Fallende Linie c_P (Bauteilkennlinie)\n'
            '• Gestapelte Kraftpfeile'
        )
        
        ax.text(0.02, 0.98, info_text, transform=ax.transAxes, fontsize=8,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

        # Update canvas
        self.canvas.draw()

    def update_delta_values(self, delta_s, delta_p, Phi):
        """
        Aktualisiert die aus Nachgiebigkeit übergebenen Werte für die Deltas und Phi.
        """
        self.set_value("delta_s", delta_s)
        self.set_value("delta_p", delta_p)
        self.set_value("Phi", Phi)

    def load_alpha_a(self):
        """
        Speist die Excel-Daten in ein pandas DataFrame ein und setzt daraus die ToolTips (Hover-Overs) für alpha<sub>A</sub>.
        """
        df = read_excel("stor/3.7.xlsx", header=None)

        items = df.iloc[1:, 0].tolist()
        tooltips = df.iloc[1:, 1].tolist()

        for item, tooltip in zip(items, tooltips):
            self.alpha_a.addItem(item)
            index = self.alpha_a.findText(item)
            self.alpha_a.setItemData(index, tooltip, Qt.ToolTipRole)

    def set_alpha_a(self):
        """
        Setzt den Wert von alpha_A basierend auf der Auswahl in den ComboBoxen.
        """
        range_str = self.alpha_a.currentText().replace(',', '.')
        parts = range_str.split(' bis ')
        if len(parts) == 2:
            lower_range = float(parts[0])
            upper_range = float(parts[1])
        else:
            raise ValueError("Input string != in the expected format 'x,y bis a,b'")
        if self.alpha_a_2.currentText() == "Festigkeit":
            self.set_value('alpha_A', upper_range)
        else:
            self.set_value('alpha_A', lower_range)

    def get_value(self, param):
        """
        Gibt den Wert eines bestimmten Parameters aus den Eingabefeldern zurück.
        """
        line_edit = self.line_edits[param]
        text = line_edit.text().strip()
        if text:
            if '*' in text and '-' in text:
                try:
                    base, exponent = text.split('*')
                    base = float(base)
                    exp = int(exponent.replace('-', ''))
                    return base * (10 ** -exp)
                except ValueError:
                    pass
            text = text.replace(',', '.').replace('e', 'E')
            try:
                return float(text)
            except ValueError:
                return None
        return None

    def set_value(self, param, value):
        """
        Setzt den Wert eines bestimmten Parameters in den Eingabefeldern.
        """
        line_edit = self.line_edits[param]
        if isinstance(value, (int, float)):
            if abs(value) < 1e-3 or abs(value) > 1e4:
                formatted_value = f"{value:.4e}".replace('e', 'E')
            else:
                formatted_value = f"{value:.4f}".rstrip('0').rstrip('.')
            formatted_value = formatted_value.replace('.', ',')
        else:
            formatted_value = str(value)
        line_edit.setText(formatted_value)
        self.valuesChanged.emit()
