from PyQt6.QtWidgets import QTableWidget
from PyQt6.QtCore import Qt, QTimer

class ScrollableTableWidget(QTableWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scroll_step = 50  # Pixels to scroll per key press
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)  # Ensure table can receive key events
        
    def keyPressEvent(self, event):
        # Handle horizontal scrolling
        if event.key() == Qt.Key.Key_Right:
            self._scroll_horizontal(forward=True)
            event.accept()
        elif event.key() == Qt.Key.Key_Left:
            self._scroll_horizontal(forward=False)
            event.accept()
        else:
            # Default behavior for other keys (including up/down navigation)
            super().keyPressEvent(event)
    
    def _scroll_horizontal(self, forward=True):
        """Scroll horizontally while maintaining cell selection"""
        scrollbar = self.horizontalScrollBar()
        if not scrollbar.isVisible():
            return
            
        current = scrollbar.value()
        increment = self.scroll_step if forward else -self.scroll_step
        new_value = current + increment
        
        # Constrain within valid range
        new_value = max(scrollbar.minimum(), min(scrollbar.maximum(), new_value))
        scrollbar.setValue(new_value)
        
        # Ensure the current cell remains visible
        QTimer.singleShot(0, self._ensure_cell_visible)
    
    def _ensure_cell_visible(self):
        """Make sure the current cell is visible after scrolling"""
        current_item = self.currentItem()
        if current_item:
            self.scrollToItem(
                current_item, 
                QTableWidget.ScrollHint.EnsureVisible
            )