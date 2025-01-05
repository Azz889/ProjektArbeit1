from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QLineEdit, QComboBox, QGroupBox
from PyQt5.QtCore import Qt
 

from numpy import pi, arctan, tan

class GewindeWidget(QWidget):
    

    """
    Widget zur Berechnung von Durchmessern und Gewinden.

    Args:
        P (float): Teilung
        n (float): Gangzahl
        p_h (float): Gewindesteigung P<sub>h</sub>
        alpha (float): Steigungswinkel \u03B1
        d (float): Außendurchmesser d
        d_2 (float): Flankendurchmesser d<sub>2</sub>
        d_3 (float): Kerndurchmesser d<sub>3</sub>
        d_s (float): Nenndurchmesser d<sub>s</sub>
        A_s (float): Spannungsquerschnitt A<sub>s</sub>
        a_c (float): Spiel im Gewinde (nur bei ISO-Trapezgewinde

    Attributes:
        validator (QDoubleValidator): Validator für Eingabefelder.
        mainwindow (Parent): Das Elternobjekt, das als Hauptfenster fungiert.
        line_edits (dict): Ein Wörterbuch, das die Eingabefelder enthält.
        gewindeart (str): Die aktuelle Gewindeart, standardmäßig "ISO-Spitzgewinde".
        spiel_edit (QLineEdit): Eingabefeld für das Spiel im Gewinde.
        spiel_label (QLabel): Label für das Spiel im Gewinde.
        spiel_unit_label (QLabel): Einheiten-Label für das Spiel im Gewinde.
        changed_d (pyqtSignal): Signal, das den neuen Durchmesserwert übermittelt.
        changed_a_s (pyqtSignal): Signal, das den neuen Spannungsquerschnittswert übermittelt.
    """
    changed_d = pyqtSignal(float) # Siehe am Ende von calculate 
    changed_a_s = pyqtSignal(float) 

    def __init__(self, validator, parent=None):
        """
        Initialisiert das Widget mit einem Validator und einem optionalen Elternobjekt.
        """
        super().__init__(parent)
        self.validator = validator
        self.mainwindow = parent
        self.setup_ui()
        self.gewindeart = "ISO-Spitzgewinde" # Default Gewindeart
        for line_edit in self.line_edits.values():
            line_edit.editingFinished.connect(self.calculate)

    def setup_ui(self):
        """
        Initialisiert das Benutzeroberflächen-Layout für die Gewindeberechnung.
        Fügt alle erforderlichen UI-Elemente (Titel, Untertitel, Eingabefelder) zum Scrollbereich hinzu.
        """
        layout = QGridLayout(self)

        # Erstellen des Scrollbereichs
        scroll_content = QWidget()
        scroll_layout = QGridLayout(scroll_content)
        layout.addWidget(scroll_content)

        # LineEdits 
        eingaben = [  
        [1,"Teilung P","","P",f"Siehe Tabelle 3.9  P=P<sub>h</sub>/n (3.1)"],  #die formel hier ist eigentlich useless
        [1,"Gangzahl n","","n"," n=P<sub>h</sub>/P (3.1)"],                    #die formel hier ist eigentlich useless
        [0,"Gewindesteigung P<sub>h</sub>","","p_h","P<sub>h</sub>=n*P (3.1)"],     
        [0,"Steigungswinkel \u03B1","°","alpha","\u03B1=arctan(P<sub>h</sub>/(pi*d<sub>2</sub>))(3.2)"],               
        [1,"Außendurchmesser d","mm","d",""],                                 
        [0,"Flankendurchmesser d<sub>2</sub>","mm","d_2","Spitzgewinde :<br>d<sub>2</sub>= d-0,650*P <br>Trapezgewinde :<br>d<sub>2</sub>= d-0,5*P<br>(Bild 3.8 oder Bild 3.9)"],
        [0,"Kerndurchmesser d<sub>3</sub>","mm","d_3","Spitzgewinde :<br>d<sub>3</sub>= d-1,227*P<br> Trapezgewinde :<br>d<sub>3</sub>= d-2*h<sub>3</sub><br>mit h<sub>3</sub>=0,5*P+ a<sub>c</sub><br> (Bild 3.8 oder Bild 3.9)"],
        [0,"Nenndurchmesser d<sub>s</sub>","mm","d_s","d<sub>2</sub>=(d<sub>2</sub>+d<sub>3</sub>)/2 (3.3)"],
        [0,"Spannungsquerschnitt A<sub>s</sub>", "mm<sup>2</sup>","A_s","A<sub>s</sub>=pi*d<sub>s</sub><sup>2</sup>/4"],
        [0,"Spiel im Gewinde a<sub>c</sub>", "mm", "a_c",""]]

        k=0
        self.line_edits = {}
        titel = QLabel("""<p style="font-size:12pt;">Durchmesser und Gewinde</p>""")
        scroll_layout.addWidget(titel)

         # ComboBox für Gewindearat
        gewinde_label = QLabel("Gewindeart")
        self.gewindeart_box = QComboBox()
        self.gewindeart_box.addItems(["ISO-Spitzgewinde", "ISO-Trapezgewinde"])
        self.gewindeart_box.currentIndexChanged.connect(self.gewindeart_changed)
        scroll_layout.addWidget(gewinde_label, 1, 0)
        scroll_layout.addWidget(self.gewindeart_box, 1, 1)

        for pflicht,name,unit,param, verweis in eingaben:
            k=k+1
            if pflicht == 1:
                name_label = QLabel('<span style="color: red;">*</span> ' + name)
            else:
                name_label = QLabel(name)
    
            line_edit = QLineEdit()
            line_edit.setObjectName(param)
            line_edit.setValidator(self.validator)
            line_edit.setToolTip(verweis)
            unit_label = QLabel(unit)
            scroll_layout.addWidget(name_label, 1+k, 0)
            scroll_layout.addWidget(line_edit, 1+k, 1)
            scroll_layout.addWidget(unit_label, 1+k, 2)
            self.line_edits[param] = line_edit
            
            if param == "a_c":
                self.spiel_edit = line_edit
                self.spiel_label = name_label
                self.spiel_unit_label = unit_label
                line_edit.hide()
                name_label.hide()
                unit_label.hide()

    def calculate(self):
        """
        Berechnet verschiedene Parameter basierend auf den Werten der Eingabefelder.
        Die berechneten Werte werden dann mithilfe der Methode 'set_value' in die noch offenen Felder der Benutzeroberfläche eingetragen.
        Die berechneten Parameter sind alle in der Klassenbeschreibung aufgelistet.

        Aktualisiert d und A_s in Nachgiebigkeit. Lässt calculate von Dauerfestigkeit laufen, da es von Gewinde-Werten abhängt.
        """
        max_iterations = 10  # um  Endlosschleifen zu verhindern 
        changes = True
        iteration = 0
        
        while changes and iteration < max_iterations:
            changes = False  # Setze das change flag auf jeder Iteration zurück
            iteration += 1
            P = self.get_value("P")
            n = self.get_value("n")
            d = self.get_value("d")
            d_2 = self.get_value("d_2")
            d_3 = self.get_value("d_3")
            d_s = self.get_value("d_s")
            A_s = self.get_value("A_s")
            alpha = self.get_value("alpha")
            p_h = self.get_value("p_h")
            if self.gewindeart == "ISO-Trapezgewinde":
                a_c = self.get_value("a_c")

            #  Berechnet p_h, p und n
            if P != None and n != None:
                p_h = P * n
                self.set_value("p_h", p_h)
                changes = True
            elif p_h != None and n != None and n != 0:
                P = p_h / n
                self.set_value("P", P)
                changes = True
            elif p_h != None and P != None and P != 0:
                n = p_h / P
                self.set_value("n", n)
                changes = True

            # d_2 und d_3 aus d und p und vice versa
            if self.gewindeart == "ISO-Spitzgewinde":
                if P != None and d != None:
                    d_2 = d - 0.650 * P
                    self.set_value("d_2", d_2)
                    d_3 = d - 1.227 * P
                    self.set_value("d_3", d_3)
                    changes = True
                elif d_2 != None and P != None:
                    d = d_2 + 0.650 * P
                    self.set_value("d", d)
                    changes = True
                elif d_3 != None and P != None:
                    d = d_3 + 1.227 * P
                    self.set_value("d", d)
                    changes = True
            elif self.gewindeart == "ISO-Trapezgewinde": # Trapezgewindeberechnung mit a_c
                if P != None and d != None:
                    d_2 = d - 0.5 * P
                    self.set_value("d_2", d_2)
                    changes = True
                elif d_2 != None and P != None:
                    d = d_2 + 0.650 * P
                    self.set_value("d", d)
                    changes = True
                if d_3 != None and P != None and a_c != None:
                    h_3 = 0.5 * P + a_c
                    d = d_3 + 2 * h_3
                    self.set_value("d", d)
                    changes = True
                elif P != None and a_c != None and d != None:
                    h_3 = 0.5 * P + a_c
                    d_3 = d - 2 * h_3
                    self.set_value("d_3", d_3)
                    changes = True

            #  d_s aus d_2 und d_3 und vice versa
            if d_2 != None and d_3 != None:
                d_s = (d_2 + d_3) / 2
                self.set_value("d_s", d_s)
                changes = True
            elif d_s != None and d_2 != None:
                d_3 = 2 * d_s - d_2
                self.set_value("d_3", d_3)
                changes = True
            elif d_s != None and d_3 != None:
                d_2 = 2 * d_s - d_3
                self.set_value("d_2", d_2)
                changes = True

            #  A_s aus d_s und vice versa
            if d_s != None:
                A_s = pi * d_s**2 / 4
                self.set_value("A_s", A_s)
                changes = True
            elif A_s != None:
                d_s = (A_s * 4 / pi )**0.5
                self.set_value("d_s", d_s)
                changes = True

            #  alpha aus p_h und d_2, und vice versa
            if p_h != None and d_2 != None and d_2 != 0:
                alpha = arctan(p_h / (pi * d_2))
                self.set_value("alpha", alpha)
                changes = True
            elif alpha != None and d_2 != None:
                p_h = tan(alpha) * pi * d_2
                self.set_value("p_h", p_h)
                changes = True
            elif alpha != None and p_h != None:
                d_2 = p_h / (tan(alpha) * pi)
                self.set_value("d_2", d_2)
                changes = True
        # Am Ende der Kalkulation werden die Signal-Werte nochmals ausgelesen und an die anderen Widgets übergeben
        d = self.get_value("d")
        if d != None:
            self.changed_d.emit(d)  # Emittiert neuen d-Wert
        A_s = self.get_value("A_s")
        if A_s != None:
            self.changed_a_s.emit(A_s)
        # Berechnet Dauerfestigkeit, da es von d und P abhängig ist
        self.mainwindow.wirkungsgrad_widget.calculate()
        self.mainwindow.dauerfestigkeit_widget.calculate()

    def gewindeart_changed(self):
        """
        Aktualisiert die Benutzeroberfläche basierend auf der ausgewählten Gewindeart.
        Versteckt oder zeigt das Eingabefeld für das Spiel im Gewinde basierend auf der Gewindeart.
        """
        # Gewindeart setzen
        self.gewindeart = self.gewindeart_box.currentText()
        if self.gewindeart == "ISO-Spitzgewinde":
            # Hide "Spiel im Gewinde"
            self.spiel_edit.hide()
            self.spiel_label.hide()
            self.spiel_unit_label.hide()
        elif self.gewindeart == "ISO-Trapezgewinde":
            # Show "Spiel im Gewinde"
            self.spiel_edit.show()
            self.spiel_label.show()
            self.spiel_unit_label.show()

    def get_value(self, param):
        """
        Gibt den Wert eines bestimmten Parameters aus den Eingabefeldern zurück.

        Args:
            param (str): Der Name des Parameters, dessen Wert zurückgegeben werden soll.

        Returns:
            float: Der Wert des Parameters als float. Wenn das Eingabefeld leer ist, wird None zurückgegeben.
        """
        line_edit = self.line_edits[param]
        text = line_edit.text()
        if text:
            # Ersetze das Komma durch einen Punkt für die korrekte Gleitkommazahlen-Konvertierung
            text = text.replace(',', '.')
            return float(text)
        return None

    def set_value(self, param, value):
        """
        Setzt den Wert eines bestimmten Parameters in den Eingabefeldern.

        Args:
            param (str): Der Name des Parameters, dessen Wert gesetzt werden soll.
            value (float or int): Der Wert, der gesetzt werden soll.
        """
        line_edit = self.line_edits[param]
        # Ersetze das Komma durch einen Punkt für die korrekte Gleitkommazahlen-Konvertierung
        if isinstance(value, int):
            formatted_value = str(value)
        elif isinstance(value, float):
            # Ersetze das Komma durch einen Punkt für die korrekte Gleitkommazahlen-Konvertierung
            if value.is_integer():
                formatted_value = f"{int(value)}"
            else:
                formatted_value = f"{value:.4f}".rstrip('0').rstrip(',')
                formatted_value = formatted_value.replace('.', ',')
        line_edit.setText(formatted_value)