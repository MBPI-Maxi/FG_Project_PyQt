# FILE: FrmUserManagement.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QFont


class FrmUserManagement(QWidget):
    def __init__(self, username, connection):
        super().__init__()
        self.username = username
        self.conn = connection
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)

        title = QLabel("User Management")
        title.setObjectName("PageTitle")  # Use the same object name for consistent styling

        message = QLabel("This is where the user management table and controls will go.")
        message.setFont(QFont("Segoe UI", 14))

        layout.addWidget(title)
        layout.addWidget(message)
        layout.addStretch()