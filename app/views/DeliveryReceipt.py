from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

class DeliveryReceipt(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.main_layout = QVBoxLayout()
        self.delivery_receipt_label = QLabel("Delivery Receipt")
        
        self.main_layout.addWidget(self.delivery_receipt_label)
        self.setLayout(self.main_layout)