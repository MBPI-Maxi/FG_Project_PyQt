from PyQt6.QtWidgets import QSpinBox
from PyQt6.QtCore import Qt
from typing import override

class ModifiedSpinBox(QSpinBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    @override
    def wheelEvent(self, e):
        e.ignore()
        