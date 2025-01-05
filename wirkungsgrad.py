from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QLineEdit, QComboBox, QGroupBox, QGraphicsView, QGraphicsScene, QSizePolicy, QApplication
from PyQt5.QtCore import pyqtSignal
from numpy import pi,tan, arctan, cos

class WirkungsgradWidget(QWidget):

    changed_my = pyqtSignal(float) 

    """
    Klasse zur Berechnung des Wirkungsgrad.
    Args:
        alpha(float): Winkel des Gewindes, aus Gewinde
        P(float): Gewindeprofil, aus Gewinde
        my(float): Reibungskoeffizient
        F(float): Kraft
        F_t(float): Tangentialkraft
        beta(float): Winkel
        roh_strich(float): modifizierter Reibungswinkel
        eta(float):Wirkungsgrad \u03B7
        eta_strich(float):Wirkungsgrad \u03B7'

    Attributes:
        validator (QDoubleValidator): Validator für Eingabefelder. Erlaubt nur Gleitkommazahlen in einem bestimmten Bereich.
        mainwindow (Parent): Das Elternobjekt, das als Hauptfenster fungiert.
    """
    def __init__(self, validator, parent=None):
        """
        Initialisiert das Widget mit einem Validator und einem optionalen Elternobjekt.
        """
        super().__init__(parent)
        self.mainwindow = parent
        self.validator = validator
        self.setup_ui()
        for line_edit in self.line_edits.values():
            line_edit.editingFinished.connect(self.calculate)
            
    def setup_ui(self):

        """
        Richtet die Benutzeroberfläche (UI) ein und fügt Widgets in einem scrollbaren Layout hinzu.

        Diese Methode erstellt ein Grid-Layout und fügt verschiedene Eingabefelder (QLineEdit) mit zugehörigen Einheiten
        und Beschriftungen (QLabel) hinzu. Die Methode verwendet eine Hilfsfunktion, um die Eingabefelder dynamisch
        zu erzeugen und im Layout zu platzieren.

        Die Benutzeroberfläche besteht aus folgenden Abschnitten:
        1. Ein Titel, der den Wirkungsgrad des Gewindes beschreibt.
        2. Eingabefelder für die Berechnung des Wirkungsgrads bei der Umsetzung einer Drehbewegung in eine translatorische Bewegung.
        3. Eingabefelder für die Berechnung des Wirkungsgrads bei der Umsetzung einer translatorischen Bewegung in eine Drehbewegung.

        Hilfsfunktion:
        - add_line_edits: Fügt die Eingabefelder und zugehörigen Labels zum Layout hinzu.
    """
        layout = QGridLayout(self)

        # Erstellen des Scrollbereichs
        scroll_content = QWidget()
        scroll_layout = QGridLayout(scroll_content)
        layout.addWidget(scroll_content)

        titel = QLabel("""<p style="font-size:12pt;">Wirkungsgrad des Gewindes</p>""")
        scroll_layout.addWidget(titel)


        #  LineEdits 
        def add_line_edits(eingaben, start_row, scroll_layout):
            for row_offset, (pflicht,name, unit, param,verweis) in enumerate(eingaben):
                if pflicht == 1:
                    name_label = QLabel('<span style="color: red;">*</span> ' + name)
                else:
                    name_label = QLabel(name)
                line_edit = QLineEdit()
                line_edit.setObjectName(param)
                line_edit.setToolTip(verweis)
                line_edit.setValidator(self.validator)
                unit_label = QLabel(unit)
                scroll_layout.addWidget(name_label, start_row + row_offset, 0)
                scroll_layout.addWidget(line_edit, start_row + row_offset, 1)
                scroll_layout.addWidget(unit_label, start_row + row_offset, 2)
                self.line_edits[param] = line_edit
            return start_row + len(eingaben)
    
        self.line_edits = {}
        k=1
        self.lable1=QLabel("""<p style="font-size:8pt;">Umsetzung einer Drehbewegung in eine translatorische Bewegung</p>""")
        scroll_layout.addWidget(self.lable1, k, 0, 1, 3)
        k+=1

        eingabe1 = [   
            [0,"Wirkungsgrad \u03B7", "","eta","\u03B7=W<sub>N</sub>/W<sub>A</sub> <br>=tan(\u03B1)/tan(\u03B1-\u03C1') (3.13)"] # Umsetzung einer Drehbewegung in eine translatorische Bewegung
        ]
        k=add_line_edits(eingabe1, k, scroll_layout)
        
        self.lable2=QLabel("""<p style="font-size:8pt;">Umsetzung einer translatorische Bewegung in eine Drehbewegung</p>""")
        scroll_layout.addWidget(self.lable2, k, 0, 1, 3)
        k+=1

        eingabe2= [
            [0,"Wirkungsgrad \u03B7'", "","eta_strich","\u03B7'=W<sub>A</sub>/W<sub>N</sub> <br>=tan(\u03B1-\u03C1')/tan(\u03B1) (3.14)"], # Umsetzung einer translatorische Bewegung in eine Drehbewegung
            [0,"Nutzarbeit je Gewindeganag W<sub>N</sub>","=W_A'","W_N"," W<sub>N</sub>=F*P"],
            [0,"Aufgewendete Arbeit je Gewindegang W<sub>A</sub>" ,"=W_N'","W_A"," W<sub>A</sub>= F<sub>t</sub>*p/tan(\u03B1)<br>mit  F<sub>t</sub>= f*tan(\u03B1+\u03C1') "],
            [0,"Längskraft F= F<sub>A</sub> ","N","F","Annahme: keine Querbeanspruchung"],   # verknüpfung zu F_A? mit Auswahlfeld längs / quer besnapruchung oder seperater Reiter 
            [0,"Translatorische Kraft F<sub>t</sub> ","N","F_t","Annahme: keine Querbeanspruchung"],
            [1,"Reibwert \u03BC","","my",""], # s.140 verweis ???
            [0,"\u03C1'","","roh_strich","arctan(\u03BC/cos(\u03B2/2)) (3.5)"],
            [0,"\u03B2","°","beta","Annahme 60° (Die Eingabe eine Wertes überschreibt diesen Wert automatisch )"]
        ]  
        k=add_line_edits(eingabe2, k, scroll_layout)

        self.calculate()
    
    def calculate(self):
        """
        Berechnet verschiedene Parameter basierend auf den Werten der Eingabefelder.
        Die berechneten Werte werden dann mithilfe der Methode 'set_value' in die noch offenen Felder der Benutzeroberfläche eingetragen.
        Die berechneten Parameter sind alle in der Klassenbeschreibung aufgelistet.

        Aktualisiert my in Kräfte
        """
        
        alpha=self.get_gewinde("alpha")
        P=self.get_gewinde("P")
        my=self.get_value("my")
        F=self.get_value("F")
        beta=self.get_value("beta")
        roh_strich = self.get_value("roh_strich")
        F_t= self.get_value("F_t")
        W_N = self.get_value("W_N")
        W_A = self.get_value("W_A")

        if F!= None and P!=None:
            W_N=F*P
            self.set_value("W_N", W_N)

        if F_t==None and F!=None and alpha!=None and roh_strich!=None:
            F_t=F*tan(alpha+roh_strich)
            self.set_value("F_t", F_t)


        if  alpha!=0 and F_t!=None and P!=None:
            if tan(alpha)!=0 :
                W_A=F_t*P/tan(alpha)
                self.set_value("W_A", W_A)

        if beta == None:
            beta=60
            self.set_value("beta", beta)
            self.set_color("beta", "default")
        if beta != 60:
            self.set_color("beta", "normal")
            
        if my != None and beta!=None:
            if cos((beta*pi/180)/2)!=0:
                roh_strich= arctan(my/cos((beta*pi/180)/2))
                self.set_value("roh_strich", roh_strich)

        if alpha!=None and roh_strich!=None :
            if tan(alpha+roh_strich)!=0 :
                eta=tan(alpha)/tan(alpha+roh_strich)
                self.set_value("eta", eta)
        
        if W_N!=None and W_A!=None:
            eta=W_N/W_A
            self.set_value("eta", eta)
            eta_strich=W_A/W_N
            self.set_value("eta_strich", eta_strich)

        if alpha!=None and roh_strich!=None :
            if tan(alpha)!=0 :
                eta_strich=tan(alpha+roh_strich)/tan(alpha)
                self.set_value("eta_strich", eta_strich)

        # Am Ende der Kalkulation werden die Signal-Werte nochmals ausgelesen und an die anderen Widgets übergeben
        my = self.get_value("my")
        if my != None:
            self.changed_my.emit(my)  # Emittiert neuen my-Wert

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
            # Formatieren des Werts mit Komma als Dezimaltrennzeichen
            if value.is_integer():
                formatted_value = f"{int(value)}"
            else:
                formatted_value = f"{value:.4f}".rstrip('0').rstrip(',')
                formatted_value = formatted_value.replace('.', ',')
        if value != None:
            line_edit.setText(formatted_value)

    def set_color(self, param, color):
        """
        Setzt die Farbe des Eingabefeldes, um es wie deaktiviert aussehen zu lassen.

        Args:
            param (str): Der Name des Parameters, dessen Farbe gesetzt werden soll.
            color (str): Die Farbe, die gesetzt werden soll (z.B. "grau").
        """
        line_edit = self.line_edits[param]
        if color == "default":
            line_edit.setStyleSheet("background-color: #f0f0f0; color: #a0a0a0;")
        elif color == "normal":
            # Reset to default style if not setting to grey
            line_edit.setStyleSheet("")

    def get_kraefte(self, param):
        """
        Gibt den Wert eines Parameters aus dem 'KraefteWidget' des Hauptfensters zurück.

        Args:
            param (str): Der Name des Parameters, dessen Wert zurückgegeben werden soll.

        Returns:
            float: Der Wert des Parameters als float.
        """
        text = self.mainwindow.kraefte_widget.get_value(param)
        try:
            return float(text)
        except:
            return None
    
    def get_gewinde(self, param):
        """
        Gibt den Wert eines Parameters aus dem 'GewindeWidget' des Hauptfensters zurück.

        Args:
            param (str): Der Name des Parameters, dessen Wert zurückgegeben werden soll.

        Returns:
            float: Der Wert des Parameters als float.
        """
        text = self.mainwindow.gewinde_widget.get_value(param)
        try:
            return float(text)
        except:
            return None
    
    def get_werkstoff(self, param):
        """
        Gibt den Wert eines Parameters aus dem 'WerkstoffWidget' des Hauptfensters zurück.

        Args:
            param (str): Der Name des Parameters, dessen Wert zurückgegeben werden soll.

        Returns:
            float: Der Wert des Parameters als float.
        """
        if param == "R_p02":
            text = self.mainwindow.werkstoff_widget.R_p02
        elif param == "R_m":
            text = self.mainwindow.werkstoff_widget.R_m
        elif param == "festigkeitsklasse":
            text = self.mainwindow.werkstoff_widget.festigkeitsklasse
        try:
            return float(text)
        except:
            return None
    
    def get_nachgiebigkeit(self, param):
        """
        Gibt den Wert eines Parameters aus dem 'NachgiebigkeitWidget' des Hauptfensters zurück.

        Args:
            param (str): Der Name des Parameters, dessen Wert zurückgegeben werden soll.

        Returns:
            float: Der Wert des Parameters als float.
        """
        text = self.mainwindow.nachgiebigkeit_widget.get_value(param)
        try:
            return float(text)
        except:
            return None
    
    def get_wirkungsgrad(self, param):
        """
        Gibt den Wert eines Parameters aus dem 'WirkungsgradWidget' des Hauptfensters zurück.

        Args:
            param (str): Der Name des Parameters, dessen Wert zurückgegeben werden soll.

        Returns:
            float: Der Wert des Parameters als float.
        """
        text = self.mainwindow.wirkungsgrad_widget.get_value(param)
        try:
            return float(text)
        except:
            return None
    