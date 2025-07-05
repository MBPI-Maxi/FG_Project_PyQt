from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

class OutgoingRecord(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.main_layout = QVBoxLayout()
        self.outgoing_form_label = QLabel("Outgoing Form")
        
        self.main_layout.addWidget(self.outgoing_form_label)
        self.setLayout(self.main_layout)