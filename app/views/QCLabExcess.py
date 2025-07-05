from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

class QCLabExcess(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout()
        self.qc_lab_excess = QLabel("QC Lab Excess")
        
        self.main_layout.addWidget(self.qc_lab_excess)
        self.setLayout(self.main_layout)