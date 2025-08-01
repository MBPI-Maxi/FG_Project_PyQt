from PyQt6.QtWidgets import QCheckBox
from PyQt6.QtCore import Qt

class ModifiedCheckbox(QCheckBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
