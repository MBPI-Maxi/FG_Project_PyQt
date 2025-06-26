from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

class RRFView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.main_layout = QVBoxLayout()
        self.rrf_label = QLabel("RRF Label")
        
        self.main_layout.addWidget(self.rrf_label)
        self.setLayout(self.main_layout)