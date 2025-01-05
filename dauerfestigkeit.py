from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QLineEdit, QComboBox, QGroupBox
from PyQt5.QtCore import Qt

# Vordimensionierung und Dauerfestigkeitsberechnung einer Schraubenverbindung 
from numpy import pi, arctan, tan, cos, sqrt
from pandas import read_excel, DataFrame

class DauerfestigkeitWidget(QWidget):
    
    """
    Widget zur Vordimensionierung und Dauerfestigkeitsberechnung einer Schraubenverbindung.

    Args:
        F_MTab (float): Montagevorspannkraft F<sub>SP</sub>
        s (float): Kleinste tragende Länge s
        d_schmin (float): Minimaler Schaftdurchmesser d<sub>sch min</sub>
        k_tau (float): Reduktionskoeffizient k<sub>\u03C4</sub>
        W_s (float): Widerstandsmoment W<sub>s</sub>
        sigma_l (float): Lochleibungsdruck \u03C3<sub>l</sub>
        sigma_z (float): Zugspannung \u03C3<sub>z</sub>
        sigma_vs (float): Vergleichsspannung \u03C3<sub>vs</sub>
        T_Mmax (float): Maximales Torsionsmoment T<sub>Mmax</sub>
        tau_t (float): Torsionsspannung \u03C4<sub>t</sub>
        tau (float): Scherspannung \u03C4
        sigma_a (float): Ausschlagsspannung \u03C3<sub>a</sub>
        sigma_A (float): zulässige Ausschlagsspannung \u03C3<sub>A</sub>
        p_Gzul (float): zulässige Grenzflächenpressung p<sub>Gzul</sub>
        p (float): Flächenpressung p
        A_p (float): Auflagefläche A<sub>p</sub>

    Attributes:
        validator (QDoubleValidator): Validator für Eingabefelder.
        mainwindow (Parent): Das Elternobjekt, das als Hauptfenster fungiert.
        line_edits (dict): Ein Wörterbuch, das die Eingabefelder enthält.
    """
    def __init__(self, validator, parent=None):
        """
        Initialisiert das Widget mit einem Validator und einem optionalen Elternobjekt.
        """
        super().__init__(parent)
        self.mainwindow = parent
        self.validator=validator
        self.setup_ui()
        for line_edit in self.line_edits.values():
            line_edit.editingFinished.connect(self.calculate)

    def setup_ui(self):
        """
        Initialisiert das Benutzeroberflächen-Layout für die Dauerfestigkeitsberechnung.
        Fügt alle erforderlichen UI-Elemente (Titel, Untertitel, Eingabefelder) zum Scrollbereich hinzu.
        """
        layout = QGridLayout(self)

        # Erstellen des Scrollbereichs
        scroll_content = QWidget()
        scroll_layout = QGridLayout(scroll_content)
        layout.addWidget(scroll_content)

        titel = QLabel("""<p style="font-size:12pt;">Dauerfestigkeit</p>""")
        scroll_layout.addWidget(titel, 0, 0, 1, 3)  # Add titel to the first row, spanning 3 columns

        # Combobox Querbeanspruchung
        fallunterscheidung_label = QLabel("Fallunterscheidung Beanspruchung")
        self.beanspruchung = QComboBox()
        self.beanspruchung.addItems(["Längsbeanspruchung", "Querbeanspruchung"])
        self.beanspruchung.currentIndexChanged.connect(self.update_ui_for_querbeanspruchung)
        scroll_layout.addWidget(fallunterscheidung_label, 1, 0)
        scroll_layout.addWidget(self.beanspruchung, 1, 1)

        # Combobox for "Fallunterscheidung Schraubenquerschnitt"
        fallunterscheidung_label = QLabel("Fallunterscheidung Schraubenquerschnitt")
        self.schraubenquerschnitt_combobox = QComboBox()
        self.schraubenquerschnitt_combobox.addItems(["Schaftschrauben", "Taillenschrauben", "Dickschaftschrauben"])
        self.schraubenquerschnitt_combobox.currentIndexChanged.connect(self.update_ui_for_taillenschrauben)
        scroll_layout.addWidget(fallunterscheidung_label, 2, 0)
        scroll_layout.addWidget(self.schraubenquerschnitt_combobox, 2, 1)

        # Hilfsfunkton zum Hinzufügen der LineEdits
        def add_line_edits(eingaben, start_row, scroll_layout):
            for row_offset, (pflicht, param, unit, name, verweis) in enumerate(eingaben):
                name_label = QLabel('<span style="color: red;">*</span> ' + name if pflicht == 1 else name)
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

        # Teil 0 Vordimensionierung einer Schraube
        eingabe0 = [
            [0, "F_MTab", "N", "Montagevorspannkraft F<sub>SP</sub>", " F<sub>SP</sub>= F<sub>M Tab</sub> <br>(Tabelle 3.9-3.12)<br> F<sub>Smax</sub>  &le; F<sub>SP</sub>"],
        ]
        k = add_line_edits(eingabe0, 3, scroll_layout)
        
        self.vordim = QLabel("")
        scroll_layout.addWidget(self.vordim, k, 0, 1, 3)
        k += 1

        # Teil a statischer Belastungsteil
        eingabea = [
            [0, "s", "mm", "Kleinste tragende Länge s", "nur bei Querbeanspruchung"],
            [0, "d_schmin", "", "Minimaler Schaftdurchmesser d<sub>sch min</sub>", "nur bei Taillenschrauben"],
            [0, "k_tau", "", "Reduktionskoeffizient k<sub>\u03C4</sub>", "Annahme 0,5 (Die Eingabe eine Wertes überschreibt diesen Wert automatisch )"],
            [0, "W_s", "mm<sup>3</sup>", "Widerstandsmoment W<sub>s</sub>", "W<sub>s</sub>=pi*p<sub>s</sub><sup>3</sup>/16"],
            [0, "sigma_l", "N/mm<sup>2</sup>", "Lochleibungsdruck \u03C3<sub>l</sub>", "\u03C3<sub>l</sub>=F<sub>Q</sub>/(d*s) (3.57)"],
            [0, "sigma_z", "N/mm<sup>2</sup>", "Zugspannung \u03C3<sub>z</sub>", "\u03C3<sub>z</sub>=F<sub>Smax</sub>/A<sub>s</sub> (3.48)"],
            [0, "sigma_vs", "N/mm<sup>2</sup>", "Vergleichsspannung \u03C3<sub>vs</sub>", "\u03C3<sub>vs</sub>=sqrt(\u03C3<sub>z</sub><sup>2</sup> +3*(k<sub>\u03C4</sub>*\u03C4<sub>t</sub>)<sup>2</sup>)<br>(3.47)"],
            [0, "T_Mmax", "Nmm", "Maximales Torsionsmoment T<sub>Mmax</sub>", "T<sub>Mmax</sub>=F<sub>Mmax</sub>*d<sub>3</sub>*tan(\u03B1+\u03C1')/2 <br>(3.49)"],
            [0, "tau_t", "N/mm<sup>2</sup>", "Torsionsspannung \u03C4<sub>t</sub>", "\u03C4<sub>t</sub>=T<sub>Mmax</sub>/W<sub>s</sub>"],
            [0, "tau", "N/mm<sup>2</sup>", "Scherspannung \u03C4", "\u03C4=F<sub>Q</sub>/A"],
        ]
        k = add_line_edits(eingabea, k, scroll_layout)


        self.belastung_label = QLabel("Art der Querbeanspruchung")
        self.belastung = QComboBox()
        self.belastung.addItems(["ruhend","schwellend","wechselnd"])
        self.belastung.currentIndexChanged.connect(self.calculate)
        scroll_layout.addWidget(self.belastung_label, k, 0)
        scroll_layout.addWidget(self.belastung, k, 1)
        k += 1

        self.stat_belastung = QLabel("")
        scroll_layout.addWidget(self.stat_belastung, k, 0, 1, 3)
        k += 1

        # Teil b dynamischer Belastungsteil
        verg_label = QLabel("Vergütung")
        self.verg = QComboBox()
        self.verg.addItems(["Schlussvergütet SV", "Schlussgewalzte/gerollte SG"])
        self.verg.setObjectName("verg")
        scroll_layout.addWidget(verg_label, k, 0)
        scroll_layout.addWidget(self.verg, k, 1)
        k += 1

        eingabeb = [
            [0, "sigma_a", "N/mm<sup>2</sup>", "Ausschlagsspannung \u03C3<sub>a</sub>", "\u03C3<sub>a</sub>=|F<sub>SAa</sub>|/A<sub>s</sub> (3.50)"],
            [0, "sigma_A", "N/mm<sup>2</sup>", "zulässige Ausschlagsspannung \u03C3<sub>A</sub>", "Für schlussvergütet SV:<br> \u03C3<sub>A</sub>=\u03C3<sub>ASV</sub>=0.85*(150/d+45) (3.51) <br><br>Für schlussgewalzte/gerollte SG: <br>\u03C3<sub>A</sub>=\u03C3<sub>ASG</sub>=(2-(F<sub>Smzul</sub>/F<sub>02min</sub>))*\u03C3<sub>ASV</sub> (3.52)<br> mit F<sub>Smzul</sub>=F<sub>SAa</sub>*F<sub>M Tab</sub> und F<sub>02min</sub>=R<sub>p02</sub>*A<sub>s</sub> "],
        ]
        k = add_line_edits(eingabeb, k, scroll_layout)

        self.dyn_belastung = QLabel("")
        scroll_layout.addWidget(self.dyn_belastung, k, 0, 1, 3)
        k += 1

        self.werkstoff = QComboBox()
        werkstoff_label = QLabel("Auflagewerkstoff auswählen")
        file_path = 'stor/3.13.xlsx'
        df = read_excel(file_path)
        row_b = df.iloc[:, 1].dropna().tolist()
        self.werkstoff.addItems(row_b)
        self.werkstoff.currentIndexChanged.connect(self.update_werkstoff)
        scroll_layout.addWidget(werkstoff_label,k,0)
        scroll_layout.addWidget(self.werkstoff,k,1)
        k += 1

        # Teil c Flächenpressung
        eingabec = [
            [0, "p_Gzul", "N/mm<sup>2</sup>", "zulässige Grenzflächenpressung p<sub>Gzul</sub>", " aus Tabelle 3.13"],
            [0, "p", "N/mm<sup>2</sup>", "Flächenpressung p", "p=F<sub>Smax</sub>/A<sub>p</sub> (3.55)"],
            [0, "A_p", "mm<sup>2</sup>", "Auflagefläche A<sub>p</sub>", "A<sub>p</sub>=pi*(d<sub>k</sub><sup>2</sup>-D<sub>B</sub><sup>2</sup>)/4"],
        ]
        k = add_line_edits(eingabec, k, scroll_layout)

        self.flaechenp = QLabel("")
        scroll_layout.addWidget(self.flaechenp, k, 0, 1, 3)
        
       

        # Initialisiert die Elemente von d_schmin, und verbirgt sie.
        self.d_schmin_label = scroll_layout.itemAtPosition(6, 0).widget()
        self.d_schmin_edit = scroll_layout.itemAtPosition(6, 1).widget()
        self.d_schmin_unit_label = scroll_layout.itemAtPosition(6, 2).widget()

        self.d_schmin_label.setVisible(False)
        self.d_schmin_edit.setVisible(False)
        self.d_schmin_unit_label.setVisible(False)

        # Querbeanspruchung verstecken

        # Initialisiert die Elemente von s, und verbirgt sie.
        self.s_label = scroll_layout.itemAtPosition(5, 0).widget()
        self.s_edit = scroll_layout.itemAtPosition(5, 1).widget()
        self.s_unit_label = scroll_layout.itemAtPosition(5, 2).widget()

        self.s_label.setVisible(False)
        self.s_edit.setVisible(False)
        self.s_unit_label.setVisible(False)

        # Initialisiert die Elemente von sigma_l, und verbirgt sie.
        self.sigma_l_label = scroll_layout.itemAtPosition(9, 0).widget()
        self.sigma_l_edit = scroll_layout.itemAtPosition(9, 1).widget()
        self.sigma_l_unit_label = scroll_layout.itemAtPosition(9, 2).widget()

        self.sigma_l_label.setVisible(False)
        self.sigma_l_edit.setVisible(False)
        self.sigma_l_unit_label.setVisible(False)

        # Initialisiert die Elemente von tau, und verbirgt sie
        self.tau_label = scroll_layout.itemAtPosition(14, 0).widget()
        self.tau_edit = scroll_layout.itemAtPosition(14, 1).widget()
        self.tau_unit_label = scroll_layout.itemAtPosition(14, 2).widget()

        self.tau_label.setVisible(False)
        self.tau_edit.setVisible(False)
        self.tau_unit_label.setVisible(False)

        # Initialisiert die Belastungsart, und verbirgt sie.
        self.belastung.setVisible(False)
        self.belastung_label.setVisible(False)

        self.calculate()

    def calculate(self):
        """
        Berechnet verschiedene Parameter basierend auf den Werten der Eingabefelder.
        Die berechneten Werte werden dann mithilfe der Methode 'set_value' in die noch offenen Felder der Benutzeroberfläche eingetragen.
        
        Die berechneten Parameter sind alle in der Klassenbeschreibung aufgelistet.
        """
        d_schmin = self.get_value("d_schmin")
        sigma_a = self.get_value("sigma_a")
        sigma_A = self.get_value("sigma_A")
        sigma_z = self.get_value("sigma_z")
        T_Mmax = self.get_value("T_Mmax")
        tau_t = self.get_value("tau_t")
        k_tau = self.get_value("k_tau")
        p_Gzul = self.get_value("p_Gzul")
        F_MTab = self.get_value("F_MTab")
        p = self.get_value("p")
        W_s = self.get_value("W_s")
        A_p = self.get_value("A_p")
        s = self.get_value("s")

        my = self.get_kraefte("my")
        F_Mmax= self.get_kraefte("F_Mmax")
        F_SAa= self.get_kraefte("F_SAa")
        Phi=self.get_kraefte("Phi")
        F_A= self.get_kraefte("F_A")
        F_Smax = self.get_kraefte("F_Smax")
        F_Q = self.get_kraefte("F_Q")

        alpha = self.get_gewinde("alpha")
        d = self.get_gewinde("d")
        P = self.get_gewinde("P")
        d_s=self.get_gewinde("d_s") 
        d_2=self.get_gewinde("d_2")
        A_s=self.get_gewinde("A_s")

        festigkeitsklasse = self.get_werkstoff("festigkeitsklasse")
        R_p02 = self.get_werkstoff("R_p02")

        roh_strich = self.get_wirkungsgrad("roh_strich")

        d_k= self.get_nachgiebigkeit("d_k")
        D_B= self.get_nachgiebigkeit("D_B")

        # Querbeanspruchung
        tau = self.get_value("tau")
        sigma_l = self.get_value("sigma_l")
        F_SP = F_MTab

        for i in range(3):

            if d != None and P != None and my != None and festigkeitsklasse != None:
                F_MTab = self.get_fmtab(d, festigkeitsklasse,my,P)
                self.set_value("F_MTab", F_MTab)
            else:
                missing_values = []
                if d == None:
                    missing_values.append("d")
                if P == None:
                    missing_values.append("P")
                if my == None:
                    missing_values.append("my")
                if festigkeitsklasse == None:
                    missing_values.append("Festigkeitsklasse")
                
                if len(missing_values) == 1:
                    missing_string = f"Es fehlt der Wert {missing_values[0]}"
                elif len(missing_values) == 2:
                    missing_string = "Es fehlen die Werte " + " und ".join(missing_values)
                else:
                    missing_string = "Es fehlen die Werte " + ", ".join(missing_values[:-1]) + " und " + missing_values[-1]
                
                self.vordim.setText(missing_string)

            # Teil 0 Vordimensionierung einer Schraube
            if F_Smax != None and F_SP != None:
                if F_Smax <= F_SP:                                                            
                    self.vordim.setText("Die Vordimensionierung war erfolgreich")    
                else:
                    self.vordim.setText("Die Vordimensionierung war nicht erfolgreich")

            # Teil a statischer Belastungsteil 
            if k_tau == None:                                                                
                k_tau=0.5
                self.set_value("k_tau", k_tau)
                self.set_color("k_tau", "default")
            if k_tau != 0.5:
                self.set_color("k_tau", "normal")

            if sigma_z != None and  k_tau !=None and tau_t != None and R_p02 != None:
                sigma_vs=sqrt(sigma_z**2+3*(k_tau*tau_t)**2)
                self.set_value("sigma_vs", sigma_vs)
                if sigma_vs <= R_p02:    
                    self.stat_belastung.setText(f"Die statische Belastung \u03C3<sub>vs</sub> {round(sigma_vs,4)} N/mm<sup>2</sup> ist kleiner als die Dehngrenze R<sub>p02</sub> {round(R_p02,4)} N/mm<sup>2</sup>. Der statische Anteil ist dauerfest.")    
                else:
                    self.stat_belastung.setText(f"Die statische Belastung \u03C3<sub>vs</sub> {round(sigma_vs,4)} N/mm<sup>2</sup> ist größer als die Dehngrenze R<sub>p02</sub> {round(R_p02,4)} N/mm<sup>2</sup>. Die Schraubenverbindung ist nicht dauerfest!")

            if F_Smax != None and A_s != 0 and A_s != None:
                sigma_z=F_Smax/A_s
                self.set_value("sigma_z", sigma_z)

            if W_s != None and W_s != 0 and T_Mmax != None:
                tau_t=T_Mmax/W_s
                self.set_value("tau_t", tau_t)

            if F_Mmax!= None and Phi!=None and F_A!=None and roh_strich != None and alpha != None and d_2 != None:
                T_Mmax = F_Mmax + d_2*tan((alpha+roh_strich)*pi/180)
                self.set_value("T_Mmax", T_Mmax)

            
            if d_s != None:
                W_s = pi*d_s**3/16
                self.set_value("W_s", W_s)

            # Dauerfestigkeit bei Querbeanspruchung
            if F_Q != None and d != None and s != None:
                sigma_l = F_Q/(d*s)
                self.set_value("sigma_l", sigma_l)
                
            if A_s != None and F_Q != None:
                tau = F_Q/A_s
                self.set_value("tau", tau)

            if self.beanspruchung.currentText() == "Querbeanspruchung":
                if sigma_l != None and tau != None:
                    name = self.belastung.currentText()
                    if name == "ruhend":
                        if sigma_l <= R_p02*0.75 and tau <= 0.6*R_p02:
                            self.stat_belastung.setText(f"""Der Lochleibungsdruck \u03C3<sub>l</sub> {round(sigma_l,4)} N/mm<sup>2</sup> ist kleiner als der zul. Druck \u03C3<sub>zul</sub> = 0,75*R<sub>p02</sub> {round(0.75*R_p02,4)} N/mm<sup>2</sup>. 
                                                        <br>Die Scherspannung \u03C4 {round(tau,4)} ist kleiner als die zul. Spannung \u03C4<sub>zul</sub> = 0,6*R<sub>p02</sub>  {round(0.6*R_p02,4)}. Der statische Anteil ist dauerfest.""")    
                        else:
                            self.stat_belastung.setText(f"""Der Lochleibungsdruck \u03C3<sub>l</sub> {round(sigma_l,4)} N/mm<sup>2</sup> ist größer als der zul. Druck \u03C3<sub>zul</sub> = 0,75*R<sub>p02</sub> {round(0.75*R_p02,4)} N/mm<sup>2</sup>. 
                                                        <br>Und oder die Scherspannung \u03C4 {round(tau,4)} ist größer als die zul. Spannung \u03C4<sub>zul</sub> = 0,6*R<sub>p02</sub>  {round(0.6*R_p02,4)}. Der statische Anteil ist nicht dauerfest.""")
                    elif name == "schwellend":
                        if sigma_l <= R_p02*0.6 and tau <= 0.5*R_p02:
                            self.stat_belastung.setText(f"""Der Lochleibungsdruck \u03C3<sub>l</sub> {round(sigma_l,4)} N/mm<sup>2</sup> ist kleiner als der zul. Druck \u03C3<sub>zul</sub> = 0,75*R<sub>p02</sub> {round(0.6*R_p02,4)} N/mm<sup>2</sup>. 
                                                        <br>Die Scherspannung \u03C4 {round(tau,4)} ist kleiner als die zul. Spannung \u03C4<sub>zul</sub> = 0,6*R<sub>p02</sub>  {round(0.5*R_p02,4)}. Der statische Anteil ist dauerfest.""")    
                        else:
                            self.stat_belastung.setText(f"""Der Lochleibungsdruck \u03C3<sub>l</sub> {round(sigma_l,4)} N/mm<sup>2</sup> ist größer als der zul. Druck \u03C3<sub>zul</sub> = 0,75*R<sub>p02</sub> {round(0.6*R_p02,4)} N/mm<sup>2</sup>. 
                                                        <br>Und oder die Scherspannung \u03C4 {round(tau,4)} ist größer als die zul. Spannung \u03C4<sub>zul</sub> = 0,6*R<sub>p02</sub>  {round(0.5*R_p02,4)}. Der statische Anteil ist nicht dauerfest.""")
                    elif name == "wechselnd":
                        if sigma_l <= R_p02*0.6 and tau <= 0.4*R_p02:
                            self.stat_belastung.setText(f"""Der Lochleibungsdruck \u03C3<sub>l</sub> {round(sigma_l,4)} N/mm<sup>2</sup> ist kleiner als der zul. Druck \u03C3<sub>zul</sub> = 0,75*R<sub>p02</sub> {round(0.6*R_p02,4)} N/mm<sup>2</sup>. 
                                                        <br>Die Scherspannung \u03C4 {round(tau,4)} ist kleiner als die zul. Spannung \u03C4<sub>zul</sub> = 0,6*R<sub>p02</sub>  {round(0.4*R_p02,4)}. Der statische Anteil ist dauerfest.""")    
                        else:
                            self.stat_belastung.setText(f"""Der Lochleibungsdruck \u03C3<sub>l</sub> {round(sigma_l,4)} N/mm<sup>2</sup> ist größer als der zul. Druck \u03C3<sub>zul</sub> = 0,75*R<sub>p02</sub> {round(0.6*R_p02,4)} N/mm<sup>2</sup>. 
                                                        <br>Und oder die Scherspannung \u03C4 {round(tau,4)} ist größer als die zul. Spannung \u03C4<sub>zul</sub> = 0,6*R<sub>p02</sub>  {round(0.4*R_p02,4)}. Der statische Anteil ist nicht dauerfest.""")                        
            # Teil b dynamischer Belastungsteil 

            if F_SAa != None and A_s!=0 and A_s != None:
                sigma_a=F_SAa/A_s
                self.set_value("sigma_a", sigma_a)

            if self.verg.currentText() =="Schlussvergütet SV" and d!=None :
                
                    sigma_A=0.85*(150/d+45)
                    self.set_value("sigma_A", sigma_A)

            if self.verg.currentText() =="Schlussgewalzte/gerollte SG" and d!=None and F_SAa!=None and F_MTab!=None and R_p02!=None and A_s!=None:
                sigma_ASV=0.85*(150/d+45)
                F_Smzul = F_SAa * F_MTab
                if self.schraubenquerschnitt_combobox.currentText() == "Schaftschrauben" or self.schraubenquerschnitt_combobox.currentText() == "Dickschaftschrauben":
                    F_02min = R_p02 * A_s                   # Schaftschraube A_0 = A_s
                else:
                    F_02min = R_p02 * pi * d_schmin**2 / 4  # Taillenschraube A_o = A_schmin
                sigma_A=(2-(F_Smzul/F_02min))*sigma_ASV
                self.set_value("sigma_A", sigma_A)

            if sigma_a != None and  sigma_A!=None:
                if sigma_a <= sigma_A:
                    self.dyn_belastung.setText(f"Die dynamische Belastung σ<sub>a</sub> {round(sigma_a,4)} N/mm<sup>2</sup> ist kleiner als die zulässige Ausschlagsspannung σ<sub>A</sub> {round(sigma_A,4)} N/mm<sup>2</sup>.")
                else:
                    self.dyn_belastung.setText(f"Die dynamische Belastung σ<sub>a</sub> {round(sigma_a,4)} N/mm<sup>2</sup> ist größer als die zulässige Ausschlagsspannung σ<sub>A</sub> {round(sigma_A,4)} N/mm<sup>2</sup>. Die Schraubenverbindung ist nicht dauerfest!")


            # Teil c Flächenpressung

            if d_k!=None and D_B!=None:
                A_p = pi*(d_k**2-D_B**2)/4
                self.set_value("A_p", A_p)

            if A_p != None and A_p != 0 and F_Smax!=None :
                p = F_Smax / A_p
                self.set_value("p", p)
            
            if p != None and  p_Gzul!=None:
                if p <= p_Gzul:
                    self.flaechenp.setText(f"Die Flächenpressung an der Auflagefläche {round(p,4)} N/mm<sup>2</sup> ist kleiner als die zulässige Flächenpressung {round(p_Gzul,4)} N/mm<sup>2</sup>.")
                else:
                    self.flaechenp.setText(f"Die Flächenpressung an der Auflagefläche {round(p,4)} N/mm<sup>2</sup> ist größer als die zulässige Flächenpressung {round(p_Gzul,4)} N/mm<sup>2</sup>.")
 
    def update_ui_for_taillenschrauben(self):
        """
        Aktualisiert die Benutzeroberfläche, um das Feld 'd_schmin' anzuzeigen, wenn 'Taillenschrauben' ausgewählt ist.
        """
        if self.schraubenquerschnitt_combobox.currentText() == "Taillenschrauben":
            self.d_schmin_label.setVisible(True)
            self.d_schmin_edit.setVisible(True)
            self.d_schmin_unit_label.setVisible(True)
        else:
            self.d_schmin_label.setVisible(False)
            self.d_schmin_edit.setVisible(False)
            self.d_schmin_unit_label.setVisible(False)
            
    def update_ui_for_querbeanspruchung(self):
        """
        Aktualisiert die Benutzeroberfläche, um die Felder 's', 'tau' und 'sigma_l' anzuzeigen, wenn 'Querbeanspruchung' ausgewählt ist.
        """
        if self.beanspruchung.currentText() == "Querbeanspruchung":
            self.s_label.setVisible(True)
            self.s_edit.setVisible(True)
            self.s_unit_label.setVisible(True)
            self.sigma_l_label.setVisible(True)
            self.sigma_l_edit.setVisible(True)
            self.sigma_l_unit_label.setVisible(True)
            self.tau_label.setVisible(True)
            self.tau_edit.setVisible(True)
            self.tau_unit_label.setVisible(True)
            self.belastung.setVisible(True)
            self.belastung_label.setVisible(True)
        else:
            self.s_label.setVisible(False)
            self.s_edit.setVisible(False)
            self.s_unit_label.setVisible(False)
            self.sigma_l_label.setVisible(False)
            self.sigma_l_edit.setVisible(False)
            self.sigma_l_unit_label.setVisible(False)
            self.tau_label.setVisible(False)
            self.tau_edit.setVisible(False)
            self.tau_unit_label.setVisible(False)
            self.belastung.setVisible(False)
            self.belastung_label.setVisible(False)

    def update_werkstoff(self):
        """
        Aktualisiert den Wert der zulässigen Grenzflächenpressung 'p_Gzul' basierend auf der Auswahl des Werkstoffs.
        """
        index = self.werkstoff.currentIndex()
        file_path = 'stor/3.13.xlsx'
        df = read_excel(file_path)
        p_Gzul = df.iloc[index, 2]
        p_Gzul = float(p_Gzul)
        self.set_value("p_Gzul", p_Gzul)

    def set_werkstoff(self, name):
        """
        Setzt den ausgewählten Werkstoff in der ComboBox basierend auf dem übergebenen Namen.

        Args:
            name (str): Der Name des auszuwählenden Werkstoffs.
        """
        # Findet den Index des Items mit gegebenem Name
        index = self.werkstoff.findText(name)
        
        # Wenn der Name in der ComboBox exestiert, wird der Index gesetzt
        if index != -1:
            self.werkstoff.setCurrentIndex(index)
        else:
            print(f"'{name}' not found in the combo box")

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
    
    def get_fmtab(self, d, festigkeitsklasse, my, p):
        """
        Berechnet den Wert von F_MTab basierend auf den übergebenen Parametern.

        Args:
            d (float): Durchmesser.
            festigkeitsklasse (float): Festigkeitsklasse.
            my (float): Reibungskoeffizient.
            p (float): Steigung.

        Returns:
            float: Der Wert von F_MTab.
        """
        # Definiert den Excel Pfad
        if self.schraubenquerschnitt_combobox.currentText() in ["Schaftschrauben", "Dickschaftschrauben"]:
            excel_paths = [
                'stor/3b_37_Fm_Schaftschraube_Feingewinde.xls',
                'stor/3b_37_Fm_Schaftschraube_Regelgewinde.xls'
            ]
        else:
            excel_paths = [
                'stor/3b_37_Fm_Schaftschraube_Feingewinde.xls',
                'stor/3b_37_Fm_Taillenschraube_Regelgewinde.xls'
            ]

        # Formatiert p passend
        p_str = f"{p:.1f}".rstrip('0').rstrip('.') if isinstance(p, float) else str(p)
        d_str = f"{d:.1f}".rstrip('0').rstrip('.') if isinstance(d, float) else str(d)
        
        # definiert abm_value und my_column vor der Schleife
        abm_value = f'M{d_str}x{p_str}'.replace('.', ',').replace(' ', '')
        my_column = f"{my:.2f}".rstrip('0')

        # Liest die Excel data in ein pandas DataFrame
        for excel_path in excel_paths:
            self.df = read_excel(excel_path, sheet_name="Tabelle")

            # Extrahiere die Zeilenüberschriften aus der dritten Zeile (Index 1).
            headers = self.df.iloc[1]
            df_without_headers = DataFrame(self.df.values[3:], columns=headers)

            # Bereinigt die 'Abm.'-Spalte, indem Leerzeichen entfernt werden
            self.df['Abm.'] = self.df['Abm.'].str.replace(' ', '')

            # Findet die Zeile basierend auf d und p 
            row = self.df[self.df['Abm.'] == abm_value]
            if row.empty:
                continue  # Versuche den nächsten Excel-Pfad, wenn keine gültige Zeile gefunden wird

            # Bestimmt die Differenz basierend auf festigkeitsklasse
            festigkeitsklasse_diff = {
                8.8: 0,
                10.9: 1,
                12.9: 2
            }

            diff = festigkeitsklasse_diff.get(festigkeitsklasse, None)
            if diff is None:
                self.vordim.setText("Ungültige Festigkeitsklasse")
                return None

            # Verschiebe die Zeilenauswahl um den Wert der Differenz nach unten
            row_index = row.index[0] + diff
            if row_index >= len(self.df):
                self.vordim.setText(f"Index {row_index} out of range, cannot move down by {diff} rows")
                return None

            adjusted_row = self.df.iloc[row_index]

             # Findet die Spalte basierend auf 'my'
            df_without_headers.columns = df_without_headers.columns.map(str).str.strip()
            df_without_headers.columns = df_without_headers.columns.fillna('NaN')

            if my_column not in df_without_headers.columns:
                continue  # Versucht den nächsten Excel-Pfad, falls keine gültige Spalte gefunden wird
            else:
                # Findet den Index der ersten Spalte, die mit dem angegeben String beginnt
                column_index = next((i for i, col in enumerate(df_without_headers.columns) if col.startswith(my_column)), None)

            # Get F_mtab Wert
            F_mtab = adjusted_row.iloc[column_index]
            return F_mtab

        # Ausgabe, wenn in keinem Excel-Pfad eine gültige Zeile oder Spalte gefunden wird
        self.vordim.setText(f"Keine gültige Zeile oder Spalte für {abm_value} und my = {my_column} in den angegebenen Dateien gefunden")
        return None