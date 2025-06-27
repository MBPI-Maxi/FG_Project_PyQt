from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

class ReturnReplacement(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout()
        self.return_replacement_label = QLabel("Return Replacement")
        
        self.main_layout.addWidget(self.return_replacement_label)
        self.setLayout(self.main_layout)