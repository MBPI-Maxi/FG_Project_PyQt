from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

class QCFailedEndorsement(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.main_layout = QVBoxLayout()
        self.qc_failed_endorsement = QLabel("QC Failed Endorsement")
        
        self.main_layout.addWidget(self.qc_failed_endorsement)
        self.setLayout(self.main_layout)