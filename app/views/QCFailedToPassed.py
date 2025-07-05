from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

class QCFailedToPassed(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.main_layout = QVBoxLayout()
        self.qc_label = QLabel("QC Failed to Passed")
        
        self.main_layout.addWidget(self.qc_label)
        self.setLayout(self.main_layout)