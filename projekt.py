import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QGridLayout, QGroupBox, QRadioButton
)
from PyQt5.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Schraubenberechnung")
        self.setGeometry(100, 100, 800, 800)  # Window dimensions

        # Store references to inputs for resetting
        self.inputs = []

        # Central widget setup
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Title and subtitle
        title_label = QLabel("Schrauben & Schraubverbindungen")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")

        subtitle_label = QLabel("IGMR RWTH Aachen\nAufbauend auf dem Vorlesungsumdruck")
        subtitle_label.setAlignment(Qt.AlignCenter)

        main_layout.addWidget(title_label)
        main_layout.addWidget(subtitle_label)

        # Diameter and Thread section
        diameter_thread_group = QGroupBox("Durchmesser und Gewinde")
        diameter_thread_layout = QGridLayout()

        labels = [
            "Gewindeart", "Teilung P", "Gangzahl n", "Gewindesteigung Ph",
            "Steigungswinkel α", "Außendurchmesser d", "Flankendurchmesser d2",
            "Kerndurchmesser d3", "Nenndurchmesser ds", "Spannungsquerschnitt As", "Spiel im Gewinde as"
        ]

        # ComboBox for 'Gewindeart'
        thread_type_combo = QComboBox()
        thread_type_combo.addItems(["ISO-Trapezgewinde", "Option 2", "Option 3"])
        diameter_thread_layout.addWidget(QLabel(labels[0]), 0, 0)
        diameter_thread_layout.addWidget(thread_type_combo, 0, 1)
        self.inputs.append(thread_type_combo)  # Store reference to reset later

        # Text fields for other inputs
        for i, label in enumerate(labels[1:], 1):
            diameter_thread_layout.addWidget(QLabel(label), i, 0)
            line_edit = QLineEdit()
            diameter_thread_layout.addWidget(line_edit, i, 1)
            self.inputs.append(line_edit)  # Store reference to reset later

        # Add class selection field
        diameter_thread_layout.addWidget(QLabel("Festigkeitsklasse"), len(labels), 0)
        class_field = QLineEdit()
        diameter_thread_layout.addWidget(class_field, len(labels), 1)
        self.inputs.append(class_field)  # Store reference to reset later

        diameter_thread_group.setLayout(diameter_thread_layout)
        main_layout.addWidget(diameter_thread_group)


        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addWidget(QPushButton("Zurück"))

        # Clear button
        clear_button = QPushButton("Leeren")
        clear_button.clicked.connect(self.clear_inputs)  # Connect to clear_inputs method
        button_layout.addWidget(clear_button)

        button_layout.addWidget(QPushButton("F20"))
        button_layout.addWidget(QPushButton("Beispiel"))
        button_layout.addWidget(QPushButton("Weiter"))

        main_layout.addLayout(button_layout)

    def clear_inputs(self):
        """Clear all input fields and reset selections."""
        for input_widget in self.inputs:
            if isinstance(input_widget, QLineEdit):
                input_widget.clear()  # Clear text fields
            elif isinstance(input_widget, QComboBox):
                input_widget.setCurrentIndex(0)  # Reset ComboBox to first item
            elif isinstance(input_widget, QRadioButton):
                input_widget.setChecked(False)  # Uncheck radio buttons


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
