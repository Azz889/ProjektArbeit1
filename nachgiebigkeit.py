from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QLineEdit, QComboBox, QGroupBox, QGraphicsView, QGraphicsScene, QSizePolicy, QMessageBox, QCheckBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtCore import pyqtSignal
from numpy import pi
from PyQt5.QtGui import QDoubleValidator

class NachgiebigkeitWidget(QWidget):
    """
    Widget zur Berechnung der Nachgiebigkeit von Schraubenverbindungen.

    Args:
        d (float): Durchmesser d
        d_k (float): Kopfdurchmesser d<sub>k</sub>
        D_A (float): Auflagendurchmesser D<sub>A</sub>
        D_B (float): Bohrungsdurchmesser D<sub>B</sub>
        l (float): Verspannte Schraubenlänge l
        m (float): Mutterhöhe m
        delta_s (float): Nachgiebigkeit Schraube \u03B4<sub>s</sub>
        delta_p (float): Nachgiebigkeit Zwischenlage \u03B4<sub>p</sub>
        delta_sn (float): Nachgiebigkeit Schraube normalisiert \u03B4<sub>sn</sub>
        delta_pn (float): Nachgiebigkeit Zwischenlage normalisiert \u03B4<sub>pn</sub>
        delta_ges (float): Gesamtnachgiebigkeit \u03B4<sub>ges</sub>
        Phi (float): Verspannungsfaktor \u03C6
        Phi_n (float): Normalisierter Verspannungsfaktor \u03C6<sub>n</sub>
        n (float): Verhältnis der Verspannungsfaktoren

    Attributes:
        validator (QDoubleValidator): Validator für Eingabefelder.
        mainwindow (Parent): Das Elternobjekt, das als Hauptfenster fungiert.
        line_edits (dict): Ein Wörterbuch, das die Eingabefelder enthält.
        deltaValuesChanged (pyqtSignal): Signal, das die neuen Delta-Werte übermittelt.
        svg_widget (SvgWidget): Widget zum Anzeigen einer SVG-Grafik.
        widgets (dict): Ein Wörterbuch, das die Bauteil-Widgets enthält.
        delta_labels (dict): Ein Wörterbuch, das die Delta-Labels enthält.
    """
    deltaValuesChanged = pyqtSignal(float, float, float)
    def __init__(self, validator, parent=None):
        """
        Initialisiert das Widget mit einem Validator und einem optionalen Elternobjekt.
        
        Args:
            validator (QDoubleValidator): Validator für Eingabefelder.
            parent (QWidget, optional): Das Elternobjekt des Widgets.
        """
        super().__init__(parent)
        self.validator = validator
        self.setup_ui()

    def setup_ui(self):
        """
        Initialisiert das Benutzeroberflächen-Layout für die Nachgiebigkeitsberechnung.
        Fügt alle erforderlichen UI-Elemente (Titel, Untertitel, Eingabefelder) zum Scrollbereich hinzu.
        """
        layout = QGridLayout(self)

        # Erstellen des Scrollbereichs
        scroll_content = QWidget()
        scroll_layout = QGridLayout(scroll_content)
        layout.addWidget(scroll_content)

        titel = QLabel("""<p style="font-size:12pt;">Nachgiebigkeit</p>""")
        scroll_layout.addWidget(titel)

        # Fallunterscheidung Bild
        self.svg_widget = SvgWidget("stor/3b_35_a_ers.svg")
        # Widget zum Layout hinzufügen
        scroll_layout.addWidget(self.svg_widget, 1, 0, 1, 4, Qt.AlignCenter)

        # LineEdits
        abc="d<sub>k</sub> ≥ D<sub>A</sub> -> Fall a <br> d<sub>k</sub> &lt; D<sub>A</sub> &le; 3*d<sub>k</sub> und l&le;8*d -> Fall b <br>D<sub>A</sub> &gt; 3*d<sub>k</sub> und l&le;8*d -> Fall c"
        eingaben = [  
            [0,"Durchmesser d", "mm","d",""],
            [1,"Kopfdurchmesser d<sub>k</sub>","mm","d_k",abc],
            [1,"Auflagendurchmesser D<sub>A</sub>","mm","D_A",abc],
            [1,"Bohrungsdurchmesser D<sub>B</sub>","mm","D_B",""],
            [1,"Verspannte Schraubenlänge l","mm","l",abc],
            [1,"Mutterhöhe m","mm","m",""]
        ]
        self.line_edits = {}
        for i, (pflicht, name, unit, param, verweis) in enumerate(eingaben, start=2):
            if pflicht == 1:
                name_label = QLabel('<span style="color: red;">*</span> ' + name)
            else:
                name_label = QLabel(name)
            
            line_edit = QLineEdit()
            line_edit.setObjectName(param)
            line_edit.setValidator(self.validator)
            line_edit.setToolTip(verweis)
            line_edit.editingFinished.connect(self.calculate)
            unit_label = QLabel(unit)
            scroll_layout.addWidget(name_label, i, 0)
            scroll_layout.addWidget(line_edit, i, 1)
            scroll_layout.addWidget(unit_label, i, 2)
            self.line_edits[param] = line_edit

        self.material_fall_label = QLabel("Fallunterschiedung Material:")
        self.material_fall = QComboBox()
        self.material_fall.addItems(["Stahl", "Grauguss", "Al-Legierung"])
        self.material_fall.currentIndexChanged.connect(self.calculate)
        scroll_layout.addWidget(self.material_fall_label, 8, 0)
        scroll_layout.addWidget(self.material_fall, 8, 1)

        self.fall_ersatzquerschnitt_titel = QLabel("Fall Eratzquerschnitt:")
        self.fall_ersatzquerschnitt = QLabel("weitere Eingaben erforderlich")
        scroll_layout.addWidget(self.fall_ersatzquerschnitt_titel, 9, 0)
        scroll_layout.addWidget(self.fall_ersatzquerschnitt, 9, 1)

        
        # Fallunterscheidung 1, 2, 3

        # Fallunterscheidung Bild
        self.svg_widget_2 = SvgWidget("stor/3b_36_einl_f.svg")
        self.svg_widget_2.setFixedSize(700,120)
        # Widget zum Layout hinzufügen
        scroll_layout.addWidget(self.svg_widget_2, 10, 0, 1, 4, Qt.AlignCenter)

        fall_label = QLabel('<span style="color: red;">*</span> ' +"Fall")
        self.fall = QComboBox()

        eingabe= [  ["1 -  Krafteinleitung an Auflagefläche","Eine an der Schraubenverbindung angreifende positive Betriebskraft (Zugkraft) bewirkt, wie bereits erläutert,  eine zusätzliche Dehnung der Schraube und eine Entlastung der Zwischenlage. Die bisherigen Betrachtungen beziehen sich auf den Fall, dass die Betriebskraft an den Auflageflächen von Schraubenkopf und Mutter eingeleitet wird. Die Schraubensteifigkeit c<sub>S</sub> und die Zwischenlagensteifigkeit c<sub>P</sub> beziehen sich auf diese Krafteinleitungsebenen."],
                    ["2 - Krafteinleitung innerhalb der verspannten Teile", "Müssen die Krafteinleitungsebenen jedoch aufgrund äußerer (konstruktiver) Bedingungen innerhalb der verspannten Teile angenommen werden, so werden die Steifigkeiten auf die nunmehr geänderten Verhältnisse bezogen. Die rechnerische Klemmlänge reduziert sich auf n*l, wobei 0 &#8804; n &lt; 1. Damit ändern sich die rechnerischen Steifigkeiten bzw. Nachgiebigkeiten von Schraube und Zwischenlage: &#948;<sub>S</sub> zu &#948;<sub>Sn</sub> und &#948;<sub>P</sub> zu &#948;<sub>Pn</sub>. Je mehr die Krafteinleitungsebenen nach innen wandern, desto größer wird die der Schraube zugewiesene Nachgiebigkeit &#948;<sub>Sn</sub> und desto kleiner wird die der Zwischenlage zuzurechnende Nachgiebigkeit &#948;<sub>Pn</sub>. Die dynamische Belastung der Schraube F<sub>SA</sub> wird ebenfalls kleiner. Die Nachgiebigkeit der Zwischenlage wird mit: &#948;<sub>Pn</sub>=n*&#948;<sub>P</sub> angesetzt, die Schraubennachgiebigkeit ergibt sich aus: &#948;<sub>Sn</sub> = &#948;<sub>S</sub> +(1-n) *&#948;<sub>P</sub>. Wird also ein Teil der Zwischenlage infolge einer positiven Betriebskraft (Zugkraft) zusätzlich gestaucht, so wird die Nachgiebigkeit dieses Anteils zur Schraubennachgiebigkeit addiert und die Nachgiebigkeit der Zwischenlage wird um diesen Betrag reduziert. Damit gilt &#948;<sub>S</sub> + &#948;<sub>P</sub> = &#948;<sub>Sn</sub> + &#948;<sub>Pn</sub> und für den Verspannungsfaktor &#966;<sub>n</sub> = &#948;<sub>Pn</sub> / (&#948;<sub>Sn</sub> + &#948;<sub>Pn</sub>) = &#948;<sub>P</sub>*n / (&#948;<sub>S</sub> + &#948;<sub>P</sub>) = &#966;*n"],
                    ["3 - Krafteinleitung in der Trennfuge","Für den Fall, dass F<sub>A</sub> in der Trennfuge der beiden Flansche angreift, entartet &#948;<sub>Pn</sub> bzw. c<sub>Pn</sub> in eine senkrechte Gerade, d.&#8239;h. es treten für F<sub>A</sub> &lt; F<sub>V</sub> keine Spannungsausschläge in der Schraube auf. Wird jedoch F<sub>A</sub> größer als F<sub>V</sub>, so kommt es zu einem Klaffen der Trennfuge. Zur Ermittlung der Vorspannkraft F<sub>V</sub> werden die Schraubennachgiebigkeit &#948;<sub>S</sub> und die Zwischenlagennachgiebigkeit &#948;<sub>P</sub> berücksichtigt, weil sich die diesbezüglichen Krafteinleitungsebenen tatsächlich an Kopf- und Mutternauf&#8203;lage befinden. Hinsichtlich der Betriebskraft F<sub>A</sub> müssen jedoch die Nachgiebigkeiten &#948;<sub>Sn</sub> und &#948;<sub>Pn</sub> angesetzt werden. Ist die Krafteinleitungsebene nicht genauer bekannt, so bleibt man bei der Festigkeitsberechnung mit &#948;<sub>S</sub> und &#948;<sub>P</sub> (n = 1) auf der sicheren Seite."] ]
        i=0
        for faelle, verweis in eingabe:
            self.fall.addItem(faelle)
            self.fall.setItemData(i, verweis, Qt.ToolTipRole)
            i+=1
        self.fall.currentIndexChanged.connect(self.krafteinleitung)
        scroll_layout.addWidget(fall_label, 11, 0)
        scroll_layout.addWidget(self.fall, 11, 1)

        
        # Fallunterscheidung Sechskantschrauben, Innensechskannt
        schraubenart_label = QLabel("Schraubenart")
        self.schraubenart = QComboBox()
        self.schraubenart.addItems(["Sechskantschraube", "Innensechskantschraube"])
        self.schraubenart.setObjectName("fall")
        self.schraubenart.currentIndexChanged.connect(self.calculate)
        scroll_layout.addWidget(schraubenart_label, 12, 0)
        scroll_layout.addWidget(self.schraubenart, 12, 1)


        # Gruppieren von Schraubenbauteilen
        self.group_box_schrauben = QGroupBox("Schraubenbauteile")
        group_layout_schrauben = QGridLayout()
        self.group_box_schrauben.setLayout(group_layout_schrauben)
        scroll_layout.addWidget(self.group_box_schrauben, 13, 0, 1, 3)

        # Gruppieren von Zwischenlagen
        self.group_box_zwischenlagen = QGroupBox("Zwischenlagen")
        group_layout_zwischenlagen = QGridLayout()
        self.group_box_zwischenlagen.setLayout(group_layout_zwischenlagen)
        scroll_layout.addWidget(self.group_box_zwischenlagen, 14, 0, 1, 3)

         # Weitere widgets für delta_pn, delta_sn, und Phi
        eingaben_2 = [
            [0,"Nachgiebigkeit der Schraube \u03B4<sub>s</sub>", "mm/N", "delta_s", " "],
            [0,"Nachgiebigkeit der Zwischenlage \u03B4<sub>p</sub>", "mm/N","delta_p", " "],
            [0,"Der Schraube zugerechnete Nachgiebeigkeit \u03B4<sub>sn</sub>", "mm/N", "delta_sn",""],
            [0,"Der Zwischenlage zugerechnete Nachgiebeigkeit\u03B4<sub>pn</sub>", "mm/N", "delta_pn"," "],
            [0,"Gesamte Nachgiebigkeit \u03B4<sub>ges</sub>", "mm/N","delta_ges", " "],
            [0,"Verspannungsfaktor \u03C6", " ", "Phi",""],
            [0,"Verspannungsfaktor nach Zurechnung \u03C6<sub>n</sub>", "", "Phi_n",""],
            [0,"Zurechnungsfaktor n", "", "n","Annahme 1 (Die Eingabe eine Wertes überschreibt diesen Wert automatisch )"]
            ]
        
        self.delta_labels = {}
        for i, (pflicht,name, unit, param,verweis) in enumerate(eingaben_2, start=16):
            name_label = QLabel(name)
            line_edit = QLineEdit()
            line_edit.setObjectName(param)
            line_edit.setValidator(self.validator)
            line_edit.setToolTip(verweis)
            line_edit.editingFinished.connect(self.calculate)
            unit_label = QLabel(unit)
            scroll_layout.addWidget(name_label, i, 0)
            scroll_layout.addWidget(line_edit, i, 1)
            scroll_layout.addWidget(unit_label, i, 2)
            self.line_edits[param] = line_edit
            self.delta_labels[param] = name_label
            self.line_edits[param] = line_edit

        # Initialisiere die GroupBox mit allen möglichen Widgets
        self.initialize_bauteile_widgets()                     

    def krafteinleitung(self):
        """
        Aktualisiert die Sichtbarkeit der Kontrollkästchen basierend auf der aktuellen Auswahl der Krafteinleitung.
        Zeigt eine Informationsnachricht an, wenn die Krafteinleitung innerhalb der verspannten Teile oder in der Trennfuge erfolgt.
        """
        current_index = self.fall.currentIndex()
        if current_index == 0:
            for bauteil in self.show_bauteile:
                elements = self.widgets[bauteil]
                elements['check'].hide()
        else:
            for bauteil in self.show_bauteile:
                elements = self.widgets[bauteil]
                elements['check'].show()
            QMessageBox.about(self, "Information", "Bitte alle Teile die zur Schraube (\u03B4<sub>sn</sub>)\n gehören mit einem Häkchen markieren")

    def initialize_bauteile_widgets(self):
        """
        Initialisiert die Widgets für die Bauteile und fügt sie der Benutzeroberfläche hinzu.
        Setzt die Standardansicht für die Bauteile.
        """
        self.widgets = {}
        l_notes="Schraubenkopflänge:<br> Sechskantschrauben: l<sub>k</sub>=0,5*d <br>Innensechskantschrauben: l<sub>k</sub>=0,4*d <br><br>Mutterkopflänge: m= Mutterhöhe<br>fürm/d=0,8=>l<sub>m</sub>=0,4*d<br>fürm/d=1,25=>l<sub>m</sub>=0,5*d<br>fürm/d=1,5=>l<sub>m</sub>=0,6*d"
        aers_notes=" A<sub>K</sub>=A<sub>Sch</sub>=A<sub>M</sub>= &pi;*d<sup>2</sup>/4<br>oder A<sub>s</sub><br>A<sub>ers</sub>:<br> Fall a :A=pi*(D<sub>A</sub><sup>2</sup>+D<sub>B</sub><sup>2</sup>)/4<br>Fall b: A=pi*(d<sub>K</sub><sup>2</sup>-D<sub>B</sub><sup>2</sup>)/4 <br> + pi*(D<sub>A</sub>/d<sub>k</sub>-1)*(d<sub>k</sub>*l/5+l<sup>2</sup>/100)/8<br><br>Fall c: Stahl:A=pi*((d<sub>k</sub>+l/10)<sup>2</sup>-D<sub>B</sub><sup>2</sup>)/4<br>Grauguss:A=pi*((d<sub>k</sub>+l/8)<sup>2</sup>-D<sub>B</sub><sup>2</sup>)/4<br>AL-Leg.:A=pi*((d<sub>k</sub>+l/6)<sup>2</sup>-D<sub>B</sub><sup>2</sup>)/4"
        labels = [["E","E-Modul aus Anhang A.1 "],["A", aers_notes], ["l",l_notes], ["δ","δ=1/c=l/(E*A)"]]
        units = ["N/mm²", "mm²", "mm", "mm/N"]
        bauteile = ["Kopf", "Schaft", "freies Gewinde", "Mutter/Verschraubung", "1 (z.B. Deckel)", "2 (z.B. Gehäuse)", "3 (z.B. Boden)", "4 (z.B. Hülse)"]

        # Zuordnen der Bauteile zu den entsprechenden GroupBoxes
        for i, bauteil in enumerate(bauteile):
            self.widgets[bauteil] = {}
            check_box = QCheckBox()
            check_box.stateChanged.connect(self.delta_calc)
            bauteil_name = QLabel(bauteil)
            self.widgets[bauteil]['check'] = check_box
            self.widgets[bauteil]['name'] = bauteil_name

            # Hier entscheiden, zu welcher GroupBox das Bauteil gehört
            if bauteil in ["Kopf", "Schaft", "freies Gewinde", "Mutter/Verschraubung"]:
                layout_to_use = self.group_box_schrauben.layout()
            else:
                layout_to_use = self.group_box_zwischenlagen.layout()

            layout_to_use.addWidget(check_box, i, 0)
            layout_to_use.addWidget(bauteil_name, i, 1)

            for j, (label, verweis) in enumerate(labels):
                name_label = QLabel(label)
                line_edit = QLineEdit()
                line_edit.setValidator(self.validator)
                line_edit.setToolTip(verweis)
                line_edit.setObjectName(f"{label.lower()}_{i+1}")
                unit_label = QLabel(units[j])
                self.widgets[bauteil][label] = (name_label, line_edit, unit_label)
                layout_to_use.addWidget(name_label, i, j*3 + 2)
                layout_to_use.addWidget(line_edit,  i, j*3 + 3)
                layout_to_use.addWidget(unit_label, i, j*3 + 4)
                line_edit.editingFinished.connect(self.delta_calc)

        self.set_bauteile("Standard")  # Initialisiert zu "Standard"

    def set_bauteile(self, text):
        """
        Aktualisiert die Sichtbarkeit der Widgets basierend auf der ausgewählten Bauteilanzahl.
        
        Args:
            text (str): Der ausgewählte Text, der die Anzahl der Bauteile bestimmt.
        """
        # Blendet als erstes alle Widgets aus
        for bauteil, elements in self.widgets.items():
            elements['name'].hide()
            elements['check'].hide()
            if bauteil == "Schraube":
                elements['calculation'].hide()
                elements['line_edit'].hide()
            else:
                for label, widgets in elements.items():
                    if label != 'name' and label != 'check':
                        widgets[0].hide()  # QLabel
                        widgets[1].hide()  # QLineEdit
                        widgets[2].hide()  # QLabel Unit

        # Zeige Widgets basierend auf dem ausgewählten Typ an
        self.show_bauteile = ["Kopf", "Schaft", "freies Gewinde", "Mutter/Verschraubung", "1 (z.B. Deckel)", "2 (z.B. Gehäuse)", "3 (z.B. Boden)", "4 (z.B. Hülse)"]

        for bauteil in self.show_bauteile:
            elements = self.widgets[bauteil]
            elements['name'].show()
            elements['check'].show()
            for label, widgets in elements.items():
                if label != 'name' and label != 'check':
                    widgets[0].show()  # QLabel Name
                    widgets[1].show()  # QLineEdit
                    widgets[2].show()  # QLabel Unit

        self.krafteinleitung()
        self.set_e_values()

    def delta_calc(self):
        """
        Berechnet die Nachgiebigkeit basierend auf den eingegebenen Werten.
        Aktualisiert die entsprechenden Felder und übermittelt die neuen Werte.
        """
        deltas = []

        # Sammelt Werte l, E, A aus den line edits
        for bauteil in self.show_bauteile:
            E_line_edit = self.widgets[bauteil]['E'][1]
            A_line_edit = self.widgets[bauteil]['A'][1]
            l_line_edit = self.widgets[bauteil]['l'][1]
            delta_line_edit = self.widgets[bauteil]['δ'][1]

            l_value = l_line_edit.text().replace(',', '.')
            E_value = E_line_edit.text().replace(',', '.')
            A_value = A_line_edit.text().replace(',', '.')
            delta_value = delta_line_edit.text().replace(',', '.')

            if l_value and E_value and A_value and not delta_value:
                delta = float(l_value) / (float(E_value) * float(A_value))
                delta_line_edit.setText(str(format(delta, ".4e")).replace('.', ','))
            elif l_value and E_value and delta_value and not A_value:
                A = float(l_value) / (float(E_value) * float(delta_value))
                A_line_edit.setText(str(format(A, ".4e")).replace('.', ','))
            elif l_value and A_value and delta_value and not E_value:
                E = float(l_value) / (float(A_value) * float(delta_value))
                E_line_edit.setText(str(format(E, ".4e")).replace('.', ','))
            elif A_value and E_value and delta_value and not l_value:
                l = float(E_value) * float(delta_value) * float(A_value)
                l_line_edit.setText(str(format(l, ".4e")).replace('.', ','))

            if delta_line_edit.text() != '':
                deltas.append(float(delta_line_edit.text().replace(',', '.')))
            else:
                deltas.append("empty")

        if "empty" not in deltas[:4]:
            delta_schraube = sum(deltas[:4])
            self.set_value("delta_s", delta_schraube)
            self.calculate()
        non_empty_count = sum(1 for value in deltas[4:] if value != "empty")    # Berechnet delta_p wenn mindestens zwei delta-Werte eingegeben wurden
        if non_empty_count >= 2:                                                # z.B. Gehäuse und Deckel
            delta_p = sum(value for value in deltas[4:] if value != "empty")
            self.set_value("delta_p", delta_p)
            self.calculate()
        if self.fall.currentIndex() != 0:
            # Berechnet und gibt delta_sn und delta_pn aus
            delta_sn = 0
            delta_pn = 0

            first_four_checked = all(self.widgets[self.show_bauteile[i]]['check'].isChecked() for i in range(4))

            if first_four_checked and self.get_value("delta_s") != None:
                delta_sn += self.get_value("delta_s")
            else:
                for i in range(4):
                    if deltas[i] != "empty":
                        if self.widgets[self.show_bauteile[i]]['check'].isChecked():
                            delta_sn += deltas[i]
                        else:
                            delta_pn += deltas[i]

            for i in range(4, len(self.show_bauteile)):
                check_box = self.widgets[self.show_bauteile[i]]['check']
                delta_value = deltas[i]

                if delta_value != "empty":
                    if check_box.isChecked():
                        delta_sn += delta_value
                    else:
                        delta_pn += delta_value

            self.set_value("delta_sn", delta_sn)
            self.set_value("delta_pn", delta_pn)
            self.calculate()

    def calculate(self):
        """
        Berechnet verschiedene Parameter basierend auf den Werten der Eingabefelder.
        Die berechneten Werte werden dann mithilfe der Methode 'set_value' in die noch offenen Felder der Benutzeroberfläche eingetragen.
        Die berechneten Parameter sind alle in der Klassenbeschreibung aufgelistet.
        """
        d = self.get_value("d")
        d_k = self.get_value("d_k")
        D_A = self.get_value("D_A")
        D_B = self.get_value("D_B")
        l = self.get_value("l")
        m = self.get_value("m")
        
        delta_s = self.get_value("delta_s")
        delta_p = self.get_value("delta_p")
        delta_sn = self.get_value("delta_sn")
        delta_pn = self.get_value("delta_pn")
        Phi = self.get_value("Phi")
        Phi_n = self.get_value("Phi_n")
        n = self.get_value("n")

        # Nochmals (hier und in update) die Fallunterscheidungen für die Länge Schraubenkopf und Mutter
        if d != 0.0 and d != None and m != None:
            if self.schraubenart.currentText() == "Sechskantschraube":
                self.set_bauteil_param('l', 'Kopf', d*0.5)
            else:
                self.set_bauteil_param('l', 'Kopf', d*0.4)
            if m/d == 0.8:
                self.set_bauteil_param('l', 'Mutter/Verschraubung', d*0.4)
            elif m/d == 1.25:
                self.set_bauteil_param('l', 'Mutter/Verschraubung', d*0.5)
            elif m/d == 1.5:
                self.set_bauteil_param('l', 'Mutter/Verschraubung', d*0.6)

        # mit delta s und delta p Phi berechnen
        if (delta_s != 0 or delta_p != 0) and (delta_s != None and delta_p != None):
            Phi = delta_p / (delta_s + delta_p)
            self.set_value("Phi", Phi)
            self.deltaValuesChanged.emit(delta_s, delta_p, Phi)

        # mit delta sn und delta pn Phi_n berechnen
        if (delta_sn != 0 or delta_pn != 0) and (delta_sn != None and delta_pn != None):
            Phi_n = delta_pn / (delta_sn + delta_pn)

            self.set_value("Phi_n", Phi_n)
            self.deltaValuesChanged.emit(delta_sn, delta_pn, Phi_n)
        
        if self.fall.currentIndex() == 0 or self.fall.currentIndex() == 2:
             n = 1
             self.set_value("n", n)
        elif Phi != None and Phi_n != None and Phi != 0:
            n = Phi_n / Phi
            self.set_value("n", n)
        elif delta_pn != None and delta_p != None and delta_p != 0:
            n = delta_pn / delta_p
            self.set_value("n", n)
        elif n==None:
            n=1
            self.set_value("n", n)

        if self.fall.currentIndex() == 1 and n!=1 and n!=None and (delta_s != 0 or delta_p != 0):
            delta_sn = delta_s +(1-n)*delta_p 
            delta_pn=n*delta_p
            Phi_n=delta_p*n/ (delta_s + delta_p)
            self.set_value("delta_sn", delta_sn)
            self.set_value("delta_pn", delta_pn)
            self.set_value("Phi_n", Phi_n)



        if (delta_s != None and delta_p != None) or (delta_sn != None and delta_pn != None):
            if delta_s != None and delta_p != None:
                delta_ges = delta_s + delta_p
            else:
                delta_ges = delta_sn + delta_pn
            self.set_value("delta_ges", delta_ges)
        

        if d and l and D_A and d_k:
            if l <= 8*d:
                if D_A >= 3*d_k:
                    self.fall_ersatzquerschnitt.setText("Fall C")
                elif d_k < D_A and D_A <= 3*d_k:
                    self.fall_ersatzquerschnitt.setText("Fall B")
                else:
                    self.fall_ersatzquerschnitt.setText("Kein Fall")
            else:
                if d_k >= D_A:
                    self.fall_ersatzquerschnitt.setText("Fall A")
                else: 
                    self.fall_ersatzquerschnitt.setText("Kein Fall")
        else:
            self.fall_ersatzquerschnitt.setText("weitere Eingaben erforderlich")

        if self.fall_ersatzquerschnitt.text() == "Fall A":
            self.A_ers = pi/4*(D_A**2-D_B**2)
            self.update_A_ers()
        elif self.fall_ersatzquerschnitt.text() == "Fall B":
            self.A_ers = pi/4*(d_k**2-D_B**2) + pi/8*(D_A/d_k-1)*(d_k*l/5 + l**2/100)
            self.update_A_ers()
        elif self.fall_ersatzquerschnitt.text() == "Fall C":
            if self.material_fall.currentText() == "Stahl":
                self.A_ers = pi/4*((d_k+l/10)**2-D_B**2)
                self.update_A_ers()
            elif self.material_fall.currentText() == "Grauguss":
                self.A_ers = pi/4*((d_k+l/8)**2-D_B**2)
                self.update_A_ers()
            elif self.material_fall.currentText() == "Al-Legierung":
                self.A_ers = pi/4*((d_k+l/6)**2-D_B**2)
                self.update_A_ers()

        
    def update_A_ers(self):
        """
        Aktualisiert den Ersatzquerschnitt (A_ers) basierend auf den aktuellen Werten.
        """
        # Specify the bauteile for which the A_ers value needs to be updated.
        bauteile_to_update = ["1 (z.B. Deckel)", "2 (z.B. Gehäuse)"]

        for bauteil in bauteile_to_update:
            self.set_bauteil_param('A', bauteil, self.A_ers)

    def set_checkbox_states(self, states):
        """
        Setzt den Zustand der Kontrollkästchen basierend auf der bereitgestellten Liste von booleschen Werten.
        
        Args:
            states (list of bool): Liste von booleschen Werten, wobei True für aktiviert und False für deaktiviert steht. Die Liste sollte der Anzahl der Kontrollkästchen entsprechen oder kürzer sein.
        """
        
        
        # Durchlaufe die Liste der booleschen Zustände und die entsprechenden Kontrollkästchen.
        # Verwende die zip-Funktion, um die Schleife auf die kürzere der beiden Listen zu beschränken.
        for state, key in zip(states, list(self.widgets.keys())):
            checkbox = self.widgets[key]['check']
            checkbox.setChecked(state)   #Setzt den Zustand der checkbox 

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

    def set_bauteil_param(self, param, bauteil, value):
        """
        Setzt den Wert eines bestimmten Parameters für ein spezifisches Bauteil.

        Args:
            param (str): Der Name des Parameters, dessen Wert gesetzt werden soll.
            bauteil (str): Der Name des Bauteils, für das der Wert gesetzt werden soll.
            value (float or int): Der Wert, der gesetzt werden soll.
        """
        widgets = self.widgets[bauteil]
        line_edit = widgets[param][1]
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

    def set_e_values(self):
        """
        Setzt alle E-Werte auf 210000.
        """
        for bauteil, elements in self.widgets.items():
            if 'E' in elements:
                e_widget = elements['E'][1]  # QLineEdit für E-Wert
                e_widget.setText("210000")

    def update(self, value, name):
        """
        Aktualisiert die Werte der Eingabefelder basierend auf dem übergebenen Namen und Wert.

        Args:
            value (float): Der neue Wert für das Eingabefeld.
            name (str): Der Name des Parameters, dessen Wert aktualisiert werden soll.
        """
        if name == "d":
            self.set_value("d", value)  # Updatet den Wert von d
            self.set_bauteil_param('A', 'Kopf', pi * value**2 / 4)  # Assuming you have 'A' as the parameter for area in 'Kopf'
            self.set_bauteil_param('A', 'Schaft', pi * value**2 / 4)
            self.set_bauteil_param('A', 'Mutter/Verschraubung', pi * value**2 / 4)
            if self.schraubenart.currentText() == "Sechskantschraube":
                self.set_bauteil_param('l', 'Kopf', value * 0.5)
            else:
                self.set_bauteil_param('l', 'Kopf', value * 0.4)
        elif name == "a_s":
            self.set_bauteil_param('A', 'freies Gewinde', value) # Update den Wert von A_ers Gewinde

class SvgWidget(QSvgWidget):
    """
    Widget zum Anzeigen von SVG-Grafiken.

    Args:
        path (str): Pfad zur SVG-Datei.
        parent (QWidget, optional): Das Elternobjekt des Widgets.

    Attributes:
        view (QGraphicsView): Grafikansicht für die SVG-Anzeige.
        scene (QGraphicsScene): Szene für die Grafikansicht.
    """
    def __init__(self, path, parent = None):
        """
        Initialisiert das Widget mit dem Pfad zur SVG-Datei und einem optionalen Elternobjekt.

        Args:
            path (str): Pfad zur SVG-Datei.
            parent (QWidget, optional): Das Elternobjekt des Widgets.
        """
        QSvgWidget.__init__(self, path, parent)

        self.view = QGraphicsView()
        self.view.setStyleSheet("background: transparent; border: none;")  # Setzt den Hintergrund der Ansicht auf transparent.
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)

        
        #Setzt die Größenrichtlinie, um das Layout zu überschreiben
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # Setzt die größe des Widgets
        self.setFixedSize(500, 300)