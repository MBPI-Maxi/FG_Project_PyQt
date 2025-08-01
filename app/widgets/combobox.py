from PyQt6.QtWidgets import QComboBox, QCompleter
from PyQt6.QtCore import Qt, QStringListModel
from typing import override
class ModifiedComboBox(QComboBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setEditable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

        # Prepare empty model for completer
        self._completer_model = QStringListModel()
        self._completer = QCompleter(self._completer_model, self)
        self._completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self._completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.setCompleter(self._completer)
        
        self.apply_style()

    @override
    def wheelEvent(self, e):
        e.ignore()
    
    @override
    def showPopup(self):
        # Always show popup when requested (the filtering is handled by the completer)
        self.view().setCursor(Qt.CursorShape.PointingHandCursor)
        super().showPopup()
    
    @override
    def addItems(self, items: list[str]) -> None:
        """Overrides addItems to keep completer model in sync."""
        super().addItems(items)
        self._completer_model.setStringList(items)

    @override
    def addItem(self, item: str, userData=None) -> None:
        """Overrides addItem to keep completer model in sync."""
        super().addItem(item, userData)
        current_items = [self.itemText(i) for i in range(self.count())]
        self._completer_model.setStringList(current_items)
        
    def apply_style(self):
        self.view().setStyleSheet("""
            background-color: white;
            color: black;
            selection-background-color: #e6f2ff;
            selection-color: black;
            border: 1px solid #ccc;
            font-size: 14px;
        """)
    