from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

class ReceivingReport(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout()
        self.receiving_report = QLabel("Receiving Report")
        
        self.main_layout.addWidget(self.receiving_report)
        self.setLayout(self.main_layout)