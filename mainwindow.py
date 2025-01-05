import sys, re
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QGridLayout, QTabWidget,  QWidget, QComboBox, QVBoxLayout, QPushButton, QHBoxLayout, QLabel, QLineEdit, QScrollArea, QSpacerItem, QSizePolicy
from PyQt5.QtGui import QDoubleValidator, QValidator
from PyQt5.QtCore import Qt, QLocale

from nachgiebigkeit import NachgiebigkeitWidget
from gewinde import GewindeWidget
from kraefte import KraefteWidget
from werkstoff import WerkstoffWidget
from dauerfestigkeit import DauerfestigkeitWidget
from wirkungsgrad import WirkungsgradWidget
from nachgiebigkeit import SvgWidget

# Zur Erstellung der Exe
# pyinstaller --onefile --windowed --exclude-module PySide6 --exclude-module pythoncom --add-data "stor;stor" mainwindow.py
# Dokumentation im Ordner "Projektarbeit/docs/_build/html/index.html"


class MainWindow(QMainWindow):
    """
    Hauptfenster für das Schraubenberechnungsprogramm.

    Attributes:
        validator (QDoubleValidator): Validator für Eingabefelder.
        gewinde_widget (GewindeWidget): Widget für Gewindeeingaben.
        werkstoff_widget (WerkstoffWidget): Widget für Werkstoffeingaben.
        nachgiebigkeit_widget (NachgiebigkeitWidget): Widget für Nachgiebigkeitseingaben.
        kraefte_widget (KraefteWidget): Widget für Krafteingaben.
        dauerfestigkeit_widget (DauerfestigkeitWidget): Widget für Dauerfestigkeitseingaben.
        wirkungsgrad_widget (WirkungsgradWidget): Widget für Wirkungsgradeingaben.
    """

    def __init__(self):
        """
        Initialisiert das Hauptfenster und richtet die Benutzeroberfläche ein.
        """
        super().__init__()

        self.setWindowTitle("Schraubenberechnung")
        self.resize(800, 600)

        #Setze das Gebietsschema auf Deutsch
        german_locale = QLocale(QLocale.German)
        QLocale.setDefault(german_locale)
        self.validator = CustomDoubleValidator(-9999999.0, 9999999.0, 4)
        #self.validator = QDoubleValidator(-999999.0, 999999.0, 4)
        #self.validator.setLocale(german_locale)

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
        home_layout.addWidget(self.svg_widget,0,0,Qt.AlignCenter)
        label = QLabel(label_text)
        label.setAlignment(Qt.AlignCenter)  # Zentrieren des Textes
        home_layout.addWidget(label)

        # GewindeWidget
        self.gewinde_widget = GewindeWidget(self.validator, self)
        home_layout.addWidget(self.gewinde_widget)

        #WirkungsgradWidget
        self.wirkungsgrad_widget = WirkungsgradWidget(self.validator, self)
        home_layout.addWidget(self.wirkungsgrad_widget)

        # WerkstoffWidget
        self.werkstoff_widget = WerkstoffWidget(self)
        home_layout.addWidget(self.werkstoff_widget)

        # NachgiebigkeitWidget
        self.nachgiebigkeit_widget = NachgiebigkeitWidget(self.validator, self)
        home_layout.addWidget(self.nachgiebigkeit_widget)

        # KraefteWidget
        self.kraefte_widget = KraefteWidget(self.validator, self)
        home_layout.addWidget(self.kraefte_widget)

        #DauerfestigkeitWidget
        self.dauerfestigkeit_widget = DauerfestigkeitWidget(self.validator, self)
        home_layout.addWidget(self.dauerfestigkeit_widget)

        # Signalverbindungen zwischen Kräfte
        self.gewinde_widget.changed_d.connect(lambda value:  self.nachgiebigkeit_widget.update(value, "d"))
        self.gewinde_widget.changed_a_s.connect(lambda value: self.nachgiebigkeit_widget.update(value, "a_s"))
        self.nachgiebigkeit_widget.deltaValuesChanged.connect(self.kraefte_widget.update_delta_values)
        self.wirkungsgrad_widget.changed_my.connect(lambda value:  self.kraefte_widget.set_value("my", value))

        # Hinzufügen der scroll area zum Zentralen Layout 
        self.central_layout.addWidget(scroll_area)

        # Knöpfe initialisieren
        about_button = QPushButton("Über")
        clear_button = QPushButton("Leeren")
        example_button = QPushButton("Beispiel")

        # Platzhalter
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        # werden verbunden wenn man sie anklickt zu den Funktionen clear_tab oder load_example
        about_button.clicked.connect(self.about)
        clear_button.clicked.connect(self.clear_tab)
        example_button.clicked.connect(self.load_example)

        # Füge Schaltflächen und Abstandshalter zu einem Container-Widget hinzu
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)   # Horizontales Layout  Platzhalter --> Buttons

        # QComboBox zur Auswahl der Beispiele
        self.example_selector = QComboBox()
        self.example_selector.addItems(["F20", "H19", "F19", "H22", "Ü 3.1", "Ü 3.5",  "Ü 3.7"])
        #"Ü 3.2", "Ü 3.3", "Ü 3.4","Ü 3.6","F22", 

        button_layout.addWidget(about_button)
        button_layout.addItem(spacer)                   # Spacers sind Items keine Widgets, deswegen addItem
        button_layout.addWidget(clear_button)
        button_layout.addWidget(self.example_selector)
        button_layout.addWidget(example_button)

        # den Button Container hinzufügen
        self.central_layout.addWidget(button_container) 

        central_widget = QWidget()
        central_widget.setLayout(self.central_layout)
        self.setCentralWidget(central_widget)

    def about(self):
        QMessageBox.about(self, "Über Uns", "Dieses Tool wurde innerhalb einer Projektarbeit von<br>Hannah Meuriße und Oliver Simon Kania entwickelt<br><br>Version 1.0<br>22.07.2024<br><br><br> P.S.: Wenn du das hier ließt, weil du eine Übung prokrastinierst: Nicht verzweifeln du schaffst das!!!")

    def calculate(self):
        """
        Berechnet die Werte für alle Widgets. Zu Testzwecken.
        """
        self.gewinde_widget.calculate()
        self.werkstoff_widget.calculate()
        self.nachgiebigkeit_widget.calculate()
        self.nachgiebigkeit_widget.delta_calc()
        self.kraefte_widget.calculate()
        self.dauerfestigkeit_widget.calculate()

    def clear_tab(self):
        """
        Leert alle Eingabefelder im ganzen Fenster.
        """
        # Findet alle QLineEdit-Widgets und lösche ihren Text
        for line_edit in self.findChildren(QLineEdit):
            line_edit.clear()

    def closeEvent(self, event):
        """
        Zum ordnungsgemäßen schließen des Fensters.
        """
        print("Programm wird geschlossen")
        event.accept()

    def load_example(self):
        """
        Lädt ein ausgewähltes Beispiel in die Eingabefelder und berechnet automatisch das Ergebnis. 
        Verknüpft mit load_example_1 bis load_example_5
        """
        selected_example = self.example_selector.currentText()

        if selected_example == "F20":
            self.load_example_1()
        elif selected_example == "H19":
            self.load_example_2()
        elif selected_example == "F19":
            self.load_example_3()
        elif selected_example == "F22":
           self.load_example_4()
        elif selected_example == "H22":
            self.load_example_5()
        elif selected_example == "Ü 3.1":
            self.load_example_6()
        elif selected_example == "Ü 3.2":
           self.load_example_7()
        elif selected_example == "Ü 3.3":
            self.load_example_8()
        elif selected_example == "Ü 3.4":
           self.load_example_9()
        elif selected_example == "Ü 3.5":
           self.load_example_10()
        elif selected_example == "Ü 3.6":
           self.load_example_11()
        elif selected_example == "Ü 3.7":
            self.load_example_12()

    def load_example_1(self):
        """
        Lädt Beispiel 1 (F20) in die Eingabefelder.
        """
        self.gewinde_widget.set_value("d", 12)
        self.gewinde_widget.set_value("P", 1.75)
        self.gewinde_widget.calculate()
        self.werkstoff_widget.festigkeitsklasse_lineedit.setText("12.9")
        self.werkstoff_widget.calculate()
        self.nachgiebigkeit_widget.set_value("d_k", 18)
        self.nachgiebigkeit_widget.set_value("D_B", 13.5)
        self.nachgiebigkeit_widget.calculate()
        self.kraefte_widget.set_value("F_A", 24946)
        self.kraefte_widget.set_value("F_Ao", 24946)
        self.kraefte_widget.set_value("F_Au", 0)
        self.kraefte_widget.set_value("F_Kerf", 3477)
        self.kraefte_widget.set_value("F_Z", 0)
        self.kraefte_widget.set_value("Phi", 0)
        self.kraefte_widget.set_value("alpha_A", 1.6)  
        self.kraefte_widget.calculate()
        self.dauerfestigkeit_widget.set_werkstoff("Cq 45")
        self.dauerfestigkeit_widget.set_value("T_Mmax", 64500)
        self.dauerfestigkeit_widget.calculate()

    def load_example_2(self):
        """
        Lädt Beispiel 2 (H19) in die Eingabefelder.
        """
        self.gewinde_widget.set_value("d", 6)
        self.gewinde_widget.calculate()
        self.werkstoff_widget.festigkeitsklasse_lineedit.setText("10.9")
        self.werkstoff_widget.calculate()
        self.nachgiebigkeit_widget.set_value("d_k", 10)
        self.nachgiebigkeit_widget.set_value("D_B", 8)
        self.nachgiebigkeit_widget.calculate()
        self.nachgiebigkeit_widget.delta_calc()
        self.kraefte_widget.set_value("kopf_mutterauflagen", 2)
        self.kraefte_widget.set_value("trennfugen", 1)
        self.kraefte_widget.set_value("R_z", 30)
        self.kraefte_widget.set_value("F_A", 6000)
        self.kraefte_widget.set_value("F_KR", 4000)
        self.kraefte_widget.calculate()
        self.dauerfestigkeit_widget.calculate()

    def load_example_3(self):
        """
        Lädt Beispiel 3 (F19) in die Eingabefelder.
        """
        self.gewinde_widget.set_value("d", 6)
        self.gewinde_widget.calculate()
        self.werkstoff_widget.festigkeitsklasse_lineedit.setText("8.8")
        self.werkstoff_widget.calculate()
        self.nachgiebigkeit_widget.set_value("d_k", 10)
        self.nachgiebigkeit_widget.set_value("D_A", 20)
        self.nachgiebigkeit_widget.set_value("D_B", 7)
        self.nachgiebigkeit_widget.set_value("l", 24.2)
        self.nachgiebigkeit_widget.set_value("delta_s", 5.72e-6)
        self.nachgiebigkeit_widget.fall.setCurrentIndex(1)
        self.nachgiebigkeit_widget.set_checkbox_states([True, True, True, True, True, False, True])
        self.nachgiebigkeit_widget.calculate()
        self.nachgiebigkeit_widget.delta_calc()
        self.kraefte_widget.set_value("F_Ao", 1500)
        self.kraefte_widget.set_value("F_Ao", 0)
        self.kraefte_widget.calculate()

    def load_example_4(self):       # TODO Hinzufügen
        """
        Lädt Beispiel 4 (F22) in die Eingabefelder.
        """
        self.gewinde_widget.set_value("d", 14)
        self.gewinde_widget.set_value("P", 2)

    def load_example_5(self):
        """
        Lädt Beispiel 5 (H22) in die Eingabefelder.
        """
        self.gewinde_widget.set_value("d", 14)
        self.gewinde_widget.set_value("P", 2)
        self.gewinde_widget.calculate()
        self.werkstoff_widget.festigkeitsklasse_lineedit.setText("12.9")
        self.werkstoff_widget.calculate()
        self.nachgiebigkeit_widget.set_bauteil_param("E", "freies Gewinde", 210000)
        self.nachgiebigkeit_widget.set_bauteil_param("l", "freies Gewinde", 6)
        self.nachgiebigkeit_widget.set_value("d_k", 22)
        self.nachgiebigkeit_widget.set_value("D_B", 15.5)
        self.nachgiebigkeit_widget.calculate()
        self.nachgiebigkeit_widget.delta_calc()
        self.kraefte_widget.set_value("alpha_A", 1.5)
        self.kraefte_widget.set_value("my", 0.2)        # ausgedacht, nicht in der Klausur aber zur Demonstration der Vordimensionierung (F_Mtab)
        self.kraefte_widget.set_value("F_Mmin", 2500)
        self.kraefte_widget.set_value("F_A", 5000)
        self.kraefte_widget.set_value("F_Ao", 5000)
        self.kraefte_widget.set_value("F_Au", 5000)
        self.kraefte_widget.set_value("F_Z", 0)
        self.kraefte_widget.set_value("F_Kerf", 2000)
        self.kraefte_widget.set_value("Phi", 1.2)
        self.kraefte_widget.calculate()
        self.dauerfestigkeit_widget.set_werkstoff("GJL-250")
        self.dauerfestigkeit_widget.set_value("tau_t", 439.2)
        self.dauerfestigkeit_widget.calculate()

    def load_example_6(self):
        """
        Lädt Beispiel 6 (Ü 3.1) in die Eingabefelder.
        """
         #F_ges=p_in*pi/4*D_in
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
         
        self.kraefte_widget.set_value("R_z", 16)
        self.kraefte_widget.set_value("F_A", 16300)
        self.kraefte_widget.set_value("F_Kerf", 6000)
        self.kraefte_widget.set_value("alpha_A", 1.6)

        self.gewinde_widget.calculate()
        self.wirkungsgrad_widget.calculate()
        self.werkstoff_widget.calculate()
        self.werkstoff_widget.calculate()
        self.nachgiebigkeit_widget.calculate()
        self.nachgiebigkeit_widget.delta_calc()
        self.kraefte_widget.calculate()
        self.dauerfestigkeit_widget.calculate()
        

        pass
    def load_example_7(self):
        """
        Lädt Beispiel 7 (Ü 3.2) in die Eingabefelder.
        """
        pass
    def load_example_8(self):
        """
        Lädt Beispiel 7 (Ü 3.3) in die Eingabefelder.
        """
        pass
    def load_example_9(self):
        """
        Lädt Beispiel 7 (Ü 3.4) in die Eingabefelder.
        """
        pass
    def load_example_10(self):
        """
        Lädt Beispiel 7 (Ü 3.5) in die Eingabefelder.
        """
        # ohne Teil a)
        self.gewinde_widget.set_value("d", 8)
        self.gewinde_widget.set_value("n", 2)
        self.gewinde_widget.set_value("P", 1.25)
        self.gewinde_widget.calculate()
        self.wirkungsgrad_widget.set_value("my", 0.135)
        self.wirkungsgrad_widget.calculate()
        self.kraefte_widget.set_value("alpha_A", 1.4)
        self.kraefte_widget.set_value("R_z", 20)
        self.kraefte_widget.set_value("F_KR", 4500)
        self.kraefte_widget.calculate()

    def load_example_11(self):
        """
        Lädt Beispiel 7 (Ü 3.6) in die Eingabefelder.
        """
        pass
    def load_example_12(self):
        """
        Lädt Beispiel 7 (Ü 3.7) in die Eingabefelder.
        """
        # eigentlich nur c-d aber mit der Nachgiebigkeitsrechnung aus a
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
        # Allow initial input states for intermediate validation
        if input in ["", "-", ",", ".", "-.", "-,", "e", "E", "e-", "E-", "-e", "-E", "-e-", "-E-"]:
            return (QValidator.Intermediate, input, pos)

        # Replace comma with dot for internal processing
        modified_input = input.replace(',', '.')

        # Allow intermediate states that could be valid scientific notation
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
    """
    Hauptfunktion zum Starten der Anwendung.
    """
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()