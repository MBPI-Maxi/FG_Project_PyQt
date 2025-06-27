from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

import os

class EndorsementView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.main_layout = QVBoxLayout()
        self.endorsement_label = QLabel("Endorsement Label")
        self.endorsement_label.setObjectName("Endorsement-label")
        
        self.main_layout.addWidget(self.endorsement_label)
        self.setLayout(self.main_layout)

        self.apply_styles()

    def apply_styles(self):
        qss_style = os.path.join(os.path.dirname(__file__), "styles", "endorsement.css")

        try:
            with open(qss_style, "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print("Warning: Style file not found. Default styles will be used.")
    