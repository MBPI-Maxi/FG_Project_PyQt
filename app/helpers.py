# function for pointing hand cursor
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QPushButton
from typing import Type

class ButtonCursorError(BaseException):
    pass

def button_cursor_pointer(button_widget: Type[QPushButton]):
    if isinstance(button_widget, QPushButton):
        button_widget.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
    else:
        raise ButtonCursorError("argument is not a QPushButton instance")