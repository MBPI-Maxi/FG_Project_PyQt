from PyQt6.QtWidgets import QDoubleSpinBox
from PyQt6.QtCore import Qt
from typing import override

class ModifiedDoubleSpinBox(QDoubleSpinBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    @override
    def wheelEvent(self, e):
        e.ignore()