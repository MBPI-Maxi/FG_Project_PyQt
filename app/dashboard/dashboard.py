import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QStackedWidget, QStatusBar,
    QGraphicsDropShadowEffect, QTabWidget
)
from PyQt6.QtGui import QFont, QIcon, QPixmap, QColor
from PyQt6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QEvent, QTimer

from app.views import EndorsementView, RRFView
from typing import Type

import qtawesome as qta
import os

class FGDashboard(QMainWindow):
    def __init__(self, *args, **kwargs):
        # self.management_submenu_visible = False
        super().__init__(*args, **kwargs)
        
        # VIEWS
        self._endorsement_view = EndorsementView()
        self._rrf_view = RRFView()

        self.setWindowTitle("FG Dashboard")
        self.setGeometry(100, 100, 1300, 800)
        # self.icon_maximize = qta.icon("fa5s.expand-arrows-alt", color="#ecf0f1")
        self.setWindowIcon(qta.icon("fa5s.cogs", color="grey"))

        # MAIN WIDGET
        self.main_widget = QWidget()

        # MAIN LAYOUT
        self.main_layout = QHBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # SIDE MENU
        self.side_menu = self.side_menu_widget()
        self.main_layout.addWidget(self.side_menu)

        # MAIN CONTENT AREA
        self.stacked_widget = QStackedWidget()

        # INITIALIZED STACK (index by order)
        self.add_stack_page("Endorsement", "Endorsement", self._endorsement_view)
        self.add_stack_page("RRF", "RRF", self._rrf_view)

        # INITIALIZE STYLES
        self.apply_styles()

        # ADD THE MAIN WIDGET
        self.main_layout.addWidget(self.stacked_widget)
        self.setCentralWidget(self.main_widget)
        
    
    def side_menu_widget(self):
        side_menu = QWidget()
        side_menu.setObjectName("SideMenu")
        layout = QVBoxLayout(side_menu)
        layout.setContentsMargins(10, 20, 10, 20)
        layout.setSpacing(15)
        
        # Profile Section
        profile = QWidget()
        profile_layout = QHBoxLayout(profile)
        user_icon = QLabel()
        user_icon.setPixmap(qta.icon('fa5s.user-circle', color='#ecf0f1').pixmap(40, 40))
        user_label = QLabel("<b>Admin User</b><br><font color='#bdc3c7'>Administrator</font>")
        profile_layout.addWidget(user_icon)
        profile_layout.addWidget(user_label)
        
        # Menu Section
        btn_dashboard = QPushButton("  Endorsement")
        btn_dashboard.setIcon(qta.icon("fa5s.tachometer-alt", color="#ecf0f1"))
        btn_dashboard.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        
        btn_materials = QPushButton("  RRF")
        btn_materials.setIcon(qta.icon("fa5s.boxes", color="#ecf0f1"))
        btn_materials.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        
        btn_users = QPushButton("  Users")
        btn_users.setIcon(qta.icon("fa5s.users", color="#ecf0f1"))
        btn_users.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))
        
        btn_logs = QPushButton("  Logs")
        btn_logs.setIcon(qta.icon("fa5s.file-alt", color="#ecf0f1"))
        btn_logs.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(3))
        
        #   Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setObjectName("Separator")
        
        # Add widgets to layout
        layout.addWidget(profile)
        layout.addWidget(separator)
        layout.addWidget(btn_dashboard)
        layout.addWidget(btn_materials)
        layout.addWidget(btn_users)
        layout.addWidget(btn_logs)
        layout.addStretch()
        
        # Logout button
        btn_logout = QPushButton("  Logout")
        btn_logout.setIcon(qta.icon('fa5s.sign-out-alt', color='#ecf0f1'))
        btn_logout.clicked.connect(self.close)
        layout.addWidget(btn_logout)
        
        return side_menu

    # this is for adding the stack to the initialized stack here in the dashboard
    def add_stack_page(self, title: str, message: str, widget_instance: Type[QWidget]):
        page = self.create_stack_page(title, message, widget_instance)
        self.stacked_widget.addWidget(page)

    # this is for creating the stack page
    def create_stack_page(self, title: str, message: str, widget_instance: Type[QWidget]):
        """Create a unified page with title, message, and embedded widget"""

        main_page = QWidget()
        layout = QVBoxLayout(main_page)
        layout.setContentsMargins(40, 40, 40, 40)

        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title_label.setObjectName("PageTitle")

        message_label = QLabel(message)
        message_label.setFont(QFont("Segoe UI", 14))
        message_label.setWordWrap(True)
        message_label.setObjectName("PageMessage")

        layout.addWidget(title_label)
        layout.addWidget(message_label)
        layout.addWidget(widget_instance)
        layout.addStretch()

        return main_page

    def apply_styles(self):
        qss_path = os.path.join(os.path.dirname(__file__), "styles", "dashboard.css")

        try:
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print("Warning: Style file not found. Default styles will be used.")
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    da = FGDashboard()
    da.show()
    sys.exit(app.exec())
    