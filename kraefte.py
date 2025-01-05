from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QLineEdit, QComboBox, QGroupBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator
from pandas import read_excel

class KraefteWidget(QWidget):
    """
    Klasse zur Berechnung der Schraubenkräfte.

    Args:
        delta_s (float): Nachgiebigkeit Schraube \u03B4<sub>s</sub>, aus NachgiebigkeitWidget
        delta_p (float): Nachgiebigkeit Zwischenlage \u03B4<sub>p</sub>, aus NachgiebigkeitWidget
        Phi (float): Verspannungsfaktor \u03C6, aus NachgiebigkeitWidget
        F_Mmin (float): Minimale Montagekraft F<sub>Mmin</sub>
        F_Mmax (float): Maximale Montagekraft F<sub>Mmax</sub>
        alpha_A (float): Anziehfaktor
        F_Z (float): Setzkraft F<sub>Z</sub>
        f_Z (float): Setzbetrag f<sub>Z</sub>
        F_A (float): Betriebskraft F<sub>A</sub>
        F_V (float): Vorspannkraft F<sub>V</sub>
        F_Smax (float): Maximale Schraubenkraft F<sub>Smax</sub>
        F_SA (float): Schraubenzusatzkraft F<sub>SA</sub>
        F_KR (float): Restklemmkraft F<sub>KR</sub>
        F_Ao (float): Obergrenze Dynamischer Betriebsfaktor F<sub>Ao</sub>
        F_Au (float): Untergrenze Dynamischer Betriebsfaktor F<sub>Au</sub>
        F_Verf (float): Erforderliche Vorspannkraft F<sub>Verf</sub>
        F_Kerf (float): Erforderliche Restklemmkraft F<sub>Kerf</sub>
        F_Q (float): Querkraft F<sub>Q</sub>
        my (float): Reibwert μ
        R_Z (float): Gemittelte Rautiefe
        F_Sm (float): Konstante Mittellast F<sub>Sm</sub>
        F_Sa (float): Schraubenausschlagskraft F<sub>SAa</sub> \u00B1
        belastung (str): Zug/Druck, Schub
        kopf_mutterauflagen (int): Anzahl Kopf- oder Mutterauflagen
        trennfugen (int): Anzahl innerer Trennfugen

    Attributes:
        validator (QDoubleValidator): Validator für Eingabefelder. Erlaubt nur Gleitkommazahlen in einem bestimmten Bereich.
        mainwindow (Parent): Das Elternobjekt, das als Hauptfenster fungiert.
    """
    def __init__(self, validator, parent=None):
        """
        Initialisiert das Widget mit einem Validator und einem optionalen Elternobjekt.
        """
        super().__init__(parent)
        self.validator = validator
        self.mainwindow = parent
        self.setup_ui()
        for line_edit in self.line_edits.values():
            line_edit.editingFinished.connect(self.calculate)
        
    def setup_ui(self):
        """
        Initialisiert das Benutzeroberflächen-Layout für die Berechnung von Kräften.
        Fügt alle erforderlichen UI-Elemente (Titel, Untertitel, Eingabefelder) zum Scrollbereich hinzu.
        """
        self.line_edits = {}

        layout = QGridLayout(self)

        # Erstellen des Scrollbereichs
        scroll_content = QWidget()
        scroll_layout = QGridLayout(scroll_content)
        layout.addWidget(scroll_content)

        title = QLabel("""<p style="font-size:12pt;">Kräfte</p>""")
        scroll_layout.addWidget(title)

        # Anziehfaktorberechnung alpha_A
        subtitle_alpha_A = QLabel("""<p style="font-size:10pt;"><u>Anziehfaktorberechnung</u></p>""")
        scroll_layout.addWidget(subtitle_alpha_A)

        # Anziehfaktor alpha_A Comboboxes
        alpha_a_label = QLabel('<span style="color: red;">*</span> ' +"Anziehfaktor auswählen")
        self.alpha_a = QComboBox()
        alpha_a_2_label = QLabel('<span style="color: red;">*</span> ' +"Berechnung für")
        self.alpha_a_2 = QComboBox()
        self.alpha_a_2.addItems(["Anwendungsfall/Sicherheit", "Festigkeit"])
        self.load_alpha_a()
        scroll_layout.addWidget(alpha_a_label, 3, 0)
        scroll_layout.addWidget(self.alpha_a, 3, 1)
        scroll_layout.addWidget(alpha_a_2_label, 4, 0)
        scroll_layout.addWidget(self.alpha_a_2, 4, 1)
        self.alpha_a.currentIndexChanged.connect(self.set_alpha_a)
        self.alpha_a_2.currentIndexChanged.connect(self.set_alpha_a)
        #Anziehfaktor Lineedit-Zeile
        self.add_lineedits(4, scroll_layout, [[1,"alpha_A", "", "Anziefaktor \u03B1<sub>A</sub>","aus Tabelle 3.7 \u03B1<sub>A</sub>=F<sub>Mmax</sub>/F<sub>Mmin</sub> (3.23)"]])

        # Setzkraftberechnung
        subtitle_F_Z = QLabel("""<p style="font-size:10pt;"><u>Setzkraftberechnung</u></p>""")
        scroll_layout.addWidget(subtitle_F_Z)

        # gemittelte Rautiefe Eingabe
        self.add_lineedits(6, scroll_layout, [[0, "R_z", "", "Gemittelte Rautiefe R<sub>z</sub>:", ""]])
                           
        # Belastung Zug/Druck oder Schub als ComboBox
        belastung_label = QLabel("Belastung Zug/Druck oder Schub:")
        self.belastung = QComboBox()
        self.belastung.addItems(["Zug/Druck", "Schub"])
        scroll_layout.addWidget(belastung_label, 8, 0)
        scroll_layout.addWidget(self.belastung, 8, 1)
        self.belastung.currentIndexChanged.connect(self.calculate)

        #Setzkraft Lineedit-Zeile
        self.add_lineedits(8, scroll_layout, [
            [0, "kopf_mutterauflagen", "", "Anzahl Kopf- oder Mutterauflagen:", ""],
            [0, "trennfugen", "", "Anzahl innerer Trennfugen:", ""],
            [0, "gewinde", "", "Anzahl Gewinde:", ""],
            [0, "f_Z", "µm", "Setzbetrag f<sub>Z</sub> = ∑f<sub>ZF</sub>", "F<sub>Z</sub>=f<sub>Z</sub> / (\u03B4<sub>s</sub> + \u03B4<sub>p</sub>) (3.31)"],
            [0, "F_Z", "N", "Setzkraft F<sub>Z</sub>"," F<sub>Z</sub>=f<sub>Z</sub> / (\u03B4<sub>s</sub> + \u03B4<sub>p</sub>) (3.31)"]])

        # Parameter
        subtitle_par = QLabel("""<p style="font-size:10pt;"><u>Parameter</u></p>""")
        scroll_layout.addWidget(subtitle_par)

        self.add_lineedits(14, scroll_layout, [ 
                                                [1,"my", "", "Reibwert μ",""],
                                                [0,"delta_s", "", "Nachgiebigkeit Schraube \u03B4<sub>s</sub>","Aus Nachgiebigkeit"],
                                                [0,"delta_p", "", "Nachgiebigkeit Zwischenlage \u03B4<sub>p</sub>","Aus Nachgiebigkeit"],
                                                [0,"Phi", "", "Verspannungsfaktor \u03C6"," \u03C6 = \u03B4<sub>p</sub> / (\u03B4<sub>s</sub> + \u03B4<sub>p</sub>)(3.26)"],
                                              ])
        
        # Betriebskräfte
        subtitle_F_A= QLabel("""<p style="font-size:10pt;"><u>Betriebskräfte</u></p>""")
        scroll_layout.addWidget(subtitle_F_A)

        self.add_lineedits(19, scroll_layout, [ 
                                                [1,"F_A", "N", "Betriebskraft F<sub>A</sub>",""],
                                                [1,"F_Ao", "N", "Obergerneze Dynamischer Betriebsfaktor F<sub>Ao</sub>",""],  
                                                [1,"F_Au", "N", "Untergrenze Dynamischer Betriebsfaktor F<sub>Au</sub>",""],
                                                [1,"F_Q", "N", "Querkraft F<sub>Q</sub>",""]
                                              ])

        # Weitere Kräfte
        subtitle_F= QLabel("""<p style="font-size:10pt;"><u>Weitere Kräfte</u></p>""")
        scroll_layout.addWidget(subtitle_F)

        eingaben = [
            [0,"F_V", "N", "Vorspannkraft F<sub>V</sub>","F<sub>V</sub> = F<sub>KR</sub>+(1-\u03C6)*F<sub>A</sub>  (3.28)   <br> F<sub>V</sub>=F<sub>Mmin</sub>-F<sub>Z</sub> (Bild 3.27)"],
            [0,"F_KR", "N", "Restklemmkraft F<sub>KR</sub>","F<sub>KR</sub>=F<sub>V</sub>+(1-\u03C6)*F<sub>A</sub> (3.28) <br> F<sub>KR</sub>=F<sub>Smax</sub>-F<sub>A</sub> (Bild 3.26)"],
            [0,"F_SA", "N", "Schraubenzusatzkraft F<sub>SA</sub>","F<sub>SA</sub>=\u03C6*F<sub>A</sub>"],
            [0,"F_PA", "N", "Hilfswert F<sub>PA</sub>","F<sub>PA</sub>=F<sub>SA</sub>-F<sub>A</sub>"],
            [0,"F_Smax", "N", "Maximale Schraubenkraft F<sub>Smax</sub>","F<sub>Smax</sub> = F<sub>Mmax</sub> + F<sub>SA</sub> <br>(Bild 3.27,3.25)  <br>F<sub>Smax</sub> = F<sub>KR</sub> + F<sub>A</sub> (Bild 3.26)  "],
            [0,"F_Mmin", "N", "Minimale Montagekraft F<sub>Mmin</sub>"," F<sub>Mmin</sub>=F<sub>Mmax</sub>/\u03B1<sub>A</sub> (3.23) <br> F<sub>Mmin</sub>= F<sub>V</sub>+F<sub>Z</sub> (Bild 3.27)"],
            [0,"F_Mmax", "N", "Maximale Montagekraft F<sub>Mmax</sub>"," F<sub>Mmax</sub>=\u03B1<sub>A</sub>*F<sub>Mmin</sub> (3.23) <br>F<sub>Mmax</sub> = F<sub>Smax</sub> - F<sub>SA</sub> (Bild 3.27)"],
            [0,"F_Kerf", "N", "Erforderliche Restklemmkraft F<sub>Kerf</sub>"," F<sub>Kerf</sub>=F<sub>Verf</sub>-(1-\u03C6)*F<sub>Ao</sub>(3.30)<br>F<sub>Kerf</sub> = F<sub>Mmin</sub> -F<sub>Z</sub> - (1-\u03C6)*F<sub>Ao</sub> (Bild 3.27)<br> oft =F<sub>Verf</sub>"],
            [0,"F_Verf", "N", "Erforderliche Vorspannkraft F<sub>Verf</sub> ","F<sub>Verf</sub>=F<sub>Kerf</sub>+(1-\u03C6)*F<sub>Ao</sub> (3.30)"],
            [0,"F_Sm", "N", "Konstante Mittellast F<sub>Sm</sub> "," F<sub>Sm</sub>=F<sub>V</sub>+\u03C6*(F<sub>Ao</sub>+F<sub>Au</sub>)/2<br> (3.36)"],
            [0,"F_SAa", "N", "Schraubenausschlagskraft F<sub>SAa</sub> \u00B1","F<sub>SAa</sub> =\u00B1 \u03C6*(F<sub>Ao</sub>-F<sub>Au</sub>)/2 (3.37)"]
        ]

        self.add_lineedits(24, scroll_layout, eingaben)

    def add_lineedits(self, index, layout, eingaben):
        """
        Fügt der Benutzeroberfläche die LineEdits aus setup_ui hinzu.

        Args:
            index (int): Der aktuelle Index in der Layout-Tabelle, um die Position der neuen Widgets anzugeben.
            layout (QGridLayout): Das Layout, zu dem die LineEdits hinzugefügt werden.
            eingaben (list): Eine Liste von Listen, die jeweils Informationen zu den LineEdits enthalten.
                Jede Liste innerhalb von 'eingaben' hat folgendes Format:
                    - pflicht (int): Gibt an, ob das Eingabefeld ein Pflichtfeld ist (1) oder nicht (0).
                    - param (str): Der Name des Parameters, der dem LineEdit zugewiesen wird.
                    - unit (str): Die Einheit des Parameters, die neben dem LineEdit angezeigt wird.
                    - name (str): Der angezeigte Name des Parameters oder des Eingabefelds.
                    - verweis (str): Ein Verweis oder eine Erklärung, die als Tooltip für das LineEdit gesetzt wird.

        Die Methode erstellt für jede Liste in 'eingaben' ein Label ('name_label'), ein LineEdit ('line_edit') und ein
        Label für die Einheit ('unit_label'). Ist der Wert von 'pflicht' (1), wird das Label 'name_label' mit einem roten
        Sternchen als Pflichtfeld markiert. Der Verweis wird als Tooltip hinzugefügt.

        Die erstellten Widgets werden dem übergebenen 'layout' hinzugefügt und das LineEdit wird zusätzlich in
        'self.line_edits' gespeichert, wobei der Parametername als Schlüssel verwendet wird.
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
        Die berechneten Werte werden dann mithilfe der Methode 'set_value' in die noch offenen Felder der Benutzeroberfläche eingetragen.
        
        Die berechneten Parameter sind alle in der Klassenbeschreibung aufgelistet.
        Da viele Parameter von vorherigen Ergebnissen aus anderen Klassen abhängig sind, wird auch die Methode 'calculate' anderer Widgets
        aufgerufen. Hier von Dauerfestigkeit. 
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
        
        for i in range(3):
            
            # alpha_A F_Mmin F_Mmax Dreieck 
            if alpha_A != None and alpha_A != 0 and F_Mmax != None:
                F_Mmin = F_Mmax / alpha_A
                self.set_value("F_Mmin", F_Mmin)

            
            elif alpha_A != None and F_Mmin != None:
                F_Mmax = alpha_A * F_Mmin
                self.set_value("F_Mmax", F_Mmax)

           
            if (delta_s != 0 or delta_p != 0) and (delta_s != None and delta_p != None):
                Phi = delta_p / (delta_s + delta_p)
                self.set_value("Phi", Phi)
                
                if f_Z != None:
                    F_Z = f_Z*0.001 / (delta_s + delta_p)
                    self.set_value("F_Z", F_Z)

            # F_KR, F_V, F_A, F_SA, F_PA

            if Phi != None and (F_A != None or F_Ao != None) and F_Z != None and F_KR != None:
                if F_A != None:
                    F_V = F_KR + (1 - Phi) * F_A          #Annahme F_KR = F_Kerf
                    self.set_value("F_V", F_V)
                elif F_Ao != None:
                    F_V = F_KR + (1 - Phi) * F_Ao
                    self.set_value("F_V", F_V)

            if Phi != None and F_A != None and F_V  != None:
                F_KR = F_V + (1 - Phi) * F_A
                self.set_value("F_KR", F_KR)

            if Phi != None and (F_A != None or F_Ao != None):
                if F_A != None:
                    F_SA = Phi * F_A
                    self.set_value("F_SA", F_SA)
                elif F_Ao != None:
                    F_SA = Phi * F_Ao
                    self.set_value("F_SA", F_SA)

            if F_SA != None and F_A != None:
                    F_PA = F_A-F_SA
                    self.set_value("F_PA", F_PA)


            if F_Mmin != None and F_Z != None :
                F_V = F_Mmin - F_Z
                self.set_value("F_V", F_V)

            # F_Mmin aus F_Z und F_V/Verf

            if F_V != None and F_Z != None :
                F_Mmin = F_V + F_Z
                self.set_value("F_Mmin", F_Mmin)  

            if F_Mmax != None and F_SA != None:
                F_Smax = F_Mmax + F_SA
                self.set_value("F_Smax", F_Smax)

            if F_Smax != None and F_SA != None:
                F_Mmax = F_Smax - F_SA
                self.set_value("F_Mmax", F_Mmax)

            if F_Smax != None and F_A != None:
                F_KR = F_Smax - F_A
                self.set_value("F_KR", F_KR)

            # F_SAa 
            if (Phi != None and  F_Ao != None and F_Au != None):
                F_SAa = Phi * (F_Ao-F_Au) / 2
                self.set_value("F_SAa", F_SAa)

            # F_Sm 
            if (Phi != None and F_V != None and  F_Ao != None and F_Au != None):
                F_Sm = F_V + Phi * (F_Ao + F_Au) / 2
                self.set_value("F_Sm", F_Sm)

            # F_Kerf 
            if F_Mmin != None and F_Z != None and F_A != None and Phi != None:      
                F_Kerf = F_Mmin - F_Z - (1-Phi)*F_A
                self.set_value("F_Kerf", F_Kerf)

            elif F_Verf != None and  Phi != None and F_Ao != None:
                F_Kerf = F_Verf- (1 - Phi) * F_Ao
                self.set_value("F_Kerf", F_Kerf)

            elif F_Verf != None and F_Ao == 0:    # Falls F_Ao = 0
                F_Kerf = F_Verf
                self.set_value("F_Kerf", F_Kerf)
                self.set_value("F_Verf", F_Kerf) 

            # F_Verf 
            if (F_Kerf != None and Phi != None and F_Ao != None):
                F_Verf = F_Kerf + (1 - Phi) * F_Ao
                self.set_value("F_Verf", F_Verf)

            elif my != None and F_Q != None:
                F_Verf = F_Q / my
                self.set_value("F_Verf", F_Verf)
                self.set_value("F_Kerf", F_Verf)    # Klausur Annahme F_Kerf = F_Verf

            if R_Z != None and gewinde != None and kopf_mutterauflagen != None and trennfugen != None:
                f_ZF = {1: {"Zug/Druck": [3, 2.5, 1.5], "Schub": [3, 3, 2]},
                        2: {"Zug/Druck": [3, 3, 2],     "Schub": [3, 4.5, 2.5]}, 
                        3: {"Zug/Druck": [3, 4, 3],     "Schub": [3, 6.5, 3.5]}}

                # Bestimme den Index basierend auf R_Z
                if R_Z < 10:
                    index = 1
                elif R_Z < 40:
                    index = 2
                elif R_Z < 160:
                    index = 3
                else:
                    print("Ungültige Rautiefe")
                    return None

                # Hole die Werte aus dem f_ZF-dictionary
                f_Z_values = f_ZF[index][belastung]

                # Berechnet f_Z
                f_Z = f_Z_values[0] * gewinde + f_Z_values[1] * kopf_mutterauflagen + f_Z_values[2] * trennfugen

                # Zeiget das Ergebnis an oder gibt es zurück
                self.set_value("f_Z",f_Z)
        # Berechen Dauerfestigkeit da es von my und Kräften abhängig ist
        self.mainwindow.dauerfestigkeit_widget.calculate()

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

        # Setzt die Elemente und Tooltips in die QComboBox
        for item, tooltip in zip(items, tooltips):
            self.alpha_a.addItem(item)
            index = self.alpha_a.findText(item)
            self.alpha_a.setItemData(index, tooltip, Qt.ToolTipRole)

    def set_alpha_a(self):
        """
        Setzt den Wert von alpha_A basierend auf der Auswahl in den ComboBoxen.
        """
        range = self.alpha_a.currentText().replace(',', '.')
        parts = range.split(' bis ')
        # Konvertiere die Zahlen in Gleitkommazahlen
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
        # Formatieren des Werts mit Komma als Dezimaltrennzeichen
        if isinstance(value, int):
            formatted_value = str(value)
        elif isinstance(value, float):
            # Wissenschaftliche Notation für sehr kleine oder sehr große Werte
            if abs(value) < 1e-3 or abs(value) > 1e4:
                formatted_value = f"{value:.4e}".replace('e', 'E')
            else:
                # Formatiert Werte mit bis zu vier Dezimalstellen und entfernt unnötige Nullen.
                formatted_value = f"{value:.4f}".rstrip('0').rstrip('.')
            # Ersetzen Sie den Punkt durch ein Komma als Dezimaltrennzeichen.
            formatted_value = formatted_value.replace('.', ',')
        else:
            formatted_value = str(value)  # umgang mit andern Types
        line_edit.setText(formatted_value)
