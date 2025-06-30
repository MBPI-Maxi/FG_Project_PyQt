# A CUSTOM LINE EDITS
from PyQt6.QtWidgets import QLineEdit
from PyQt6.QtGui import QMouseEvent

class LotNumberLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Removed the NoSpaceValidator since input mask handles formatting
    
    def mousePressEvent(self, event: QMouseEvent):
        super().mousePressEvent(event)
        self.setCursorPosition(0)

    def clear(self):
        """Override clear to properly handle input mask"""
        self.setInputMask("")  # Remove mask temporarily
        super().clear()
        # Restore default mask
        self.setInputMask("0000AA; ")
        self.setPlaceholderText("e.g.1234AB or 1234AB-5678CD")
        self.setCursorPosition(0)