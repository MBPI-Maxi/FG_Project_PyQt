from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

class RequisitionLogbook(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout()
        self.requisition_logbook = QLabel("RequisitionLogbook")
        
        self.main_layout.addWidget(self.requisition_logbook)
        self.setLayout(self.main_layout)