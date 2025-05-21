from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout,
    QPushButton, QDialog, QTableWidget, QTableWidgetItem, QVBoxLayout,QGridLayout,QScrollArea
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt


class WerkstoffWidget(QWidget):
    """
    Widget zur Eingabe und Berechnung der Werkstoffdaten.

    Attributes:
        mainwindow (Parent): Das Elternobjekt, das als Hauptfenster fungiert.
        festigkeitsklasse (str): Die Festigkeitsklasse des Werkstoffs.
        R_p02 (float): Nennstreckgrenze des Werkstoffs.
        R_m (float): Nennzugfestigkeit des Werkstoffs.
        festigkeitsklasse_lineedit (QLineEdit): Eingabefeld für die Festigkeitsklasse.
        festigkeitsklasse_result_label (QLabel): Label zur Anzeige der Berechnungsergebnisse.
        show_table_button (QPushButton): Button zum Anzeigen der Werkstoffdatentabelle.
    """
    def __init__(self, parent=None):
        """
        Initialisiert das Widget mit einem optionalen Elternobjekt.

        Args:
            parent (QWidget, optional): Das Elternobjekt des Widgets.
        """
        super().__init__(parent)
        self.mainwindow = parent

        self.festigkeitsklasse = None
        self.R_p02 = None
        self.R_m = None

        # Layout einrichten
        layout = QVBoxLayout()
        
        # füge Festigkeitsklasse zeile hinzu
        festigkeitsklasse_label = QLabel('<span style="color: red;">*</span> ' + "Festigkeitsklasse")
         
        self.festigkeitsklasse_lineedit = QLineEdit()
        self.festigkeitsklasse_lineedit.setObjectName("festigkeitsklasse_lineedit")
        self.festigkeitsklasse_lineedit.setToolTip("a.b (Bsp.: 12.9) <br>R<sub>m</sub>=a*100 <br>R<sub>e</sub>=b*R<sub>m</sub>/10")
        self.festigkeitsklasse_lineedit.editingFinished.connect(self.calculate)
        self.festigkeitsklasse_result_label = QLabel("")

        festigkeitsklasse_layout = QHBoxLayout()
        festigkeitsklasse_layout.addWidget(festigkeitsklasse_label)
        festigkeitsklasse_layout.addWidget(self.festigkeitsklasse_lineedit)
        festigkeitsklasse_layout.addWidget(self.festigkeitsklasse_result_label)
        layout.addLayout(festigkeitsklasse_layout)

        # Button hinzufügen, um Tabelle anzuzeigen
        self.show_table_button = QPushButton("Anhang A.1 Werkstoffdaten anzeigen")
        self.show_table_button.clicked.connect(self.show_table_popup)
        layout.addWidget(self.show_table_button)

        self.setLayout(layout)

    def calculate(self):
        """
        Berechnet die Nennzugfestigkeit und Nennstreckgrenze basierend auf der eingegebenen Festigkeitsklasse.
        Aktualisiert die entsprechenden Labels mit den berechneten Werten.
        Ruft die Berechnung der Dauerfestigkeit auf.
        """
        self.festigkeitsklasse = self.festigkeitsklasse_lineedit.text().replace(',', '.')
        if not self.festigkeitsklasse:
            self.festigkeitsklasse_result_label.setText("")
            return

        try:
            # Split the festigkeitsklasse (e.g., "12.9" into ["12", "9"])
            parts = self.festigkeitsklasse.split('.')
            if len(parts) != 2:
                raise ValueError("Festigkeitsklasse muss im Format 'X.Y' sein (z.B. 12.9)")

            # Convert to floats
            first_part = float(parts[0])  # e.g., 12 from "12.9"
            second_part = float(parts[1])  # e.g., 9 from "12.9"

            # Calculate R_m and R_p02
            self.R_m = first_part * 100  # e.g., 12 * 100 = 1200
            self.R_p02 = second_part * 10 * first_part  # e.g., 9 * 10 * 12 = 1080

            # Update the display
            self.festigkeitsklasse_result_label.setText(
                f"Nennzugfestigkeit R<sub>m</sub>: {self.R_m:.0f}\n"
                f"Nennstreckgrenze R<sub>eL/p0,2</sub>: {self.R_p02:.0f}"
            )

            # Trigger Dauerfestigkeit calculation
            self.mainwindow.dauerfestigkeit_widget.calculate()

        except ValueError as e:
            self.festigkeitsklasse_result_label.setText("ungültige Eingabe")

    def show_table_popup(self):
        """
        Zeigt ein Pop-up-Fenster mit einer Tabelle der Werkstoffdaten an.
        """
        # Erstellt ein pop-up Fenster
        dialog = QDialog(self)
        dialog.setWindowTitle("A.1 Werkstoffdaten")
        dialog.resize(1000, 500)  # Dialoggröße anpassen

        # Erstellen des Layouts für das Dialog-Fenster
        layout = QGridLayout(dialog)

        # Erstellen des Scrollbereichs
        scroll_content = QWidget()
        scroll_layout = QGridLayout(scroll_content)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(scroll_content)

        # Maximale Breite und Höhe der Bilder
        max_width = 2500
        max_height = 1500

        # Liste der Bildpfade
        image_paths = ['stor/0365.jpg', 'stor/0366.jpg', 'stor/0367.jpg', 'stor/0368.jpg']

        for i, image_path in enumerate(image_paths):
            pixmap = QPixmap(image_path)
            # Bild skalieren, wobei das Seitenverhältnis beibehalten wird
            scaled_pixmap = pixmap.scaled(max_width, max_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            label = QLabel()
            label.setPixmap(scaled_pixmap)
            label.setAlignment(Qt.AlignCenter)
            scroll_layout.addWidget(label, i, 0, Qt.AlignCenter)

        # Scrollbereich zum Layout hinzufügen
        layout.addWidget(scroll_area)

        # Setzt das Layout für den Dialog
        dialog.setLayout(layout)

        # Zeigt den Dialog an
        dialog.exec_()
            

                
            

        """
            # Erstellt eine Tabelle
            table = QTableWidget(4, 3)  # 4 rows, 3 columns for this example
            table.setHorizontalHeaderLabels(["Werkstoff Kurzzeichen", "Mittlere Festigkeitswerte / N/mm^2", "Eigs. und Verwendungsbeispiele"])
            
            # Füllt die Tabelle mit zufälligen Werten
            for i in range(4):
                for j in range(3):
                    table.setItem(i, j, QTableWidgetItem(f"Item {i+1},{j+1}"))

            
            """