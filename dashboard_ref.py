import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QStackedWidget, QStatusBar,
    QGraphicsDropShadowEffect, QTabWidget
)
from PyQt6.QtGui import QFont, QIcon, QPixmap, QColor
from PyQt6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QEvent, QTimer
import qtawesome as fa

class MinimalDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Minimal Dashboard")
        self.setGeometry(100, 100, 1300, 800)
        self.management_submenu_visible = False
        self.icon_maximize = fa.icon('fa5s.expand-arrows-alt', color='#ecf0f1')
        self.icon_restore = fa.icon('fa5s.compress-arrows-alt', color='#ecf0f1')
        self.init_ui()

    def init_ui(self):
        self.setWindowIcon(fa.icon('fa5s.cogs', color='gray'))
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Side Menu
        side_menu = self.create_side_menu()
        main_layout.addWidget(side_menu)
        
        # Main Content Area
        self.stacked_widget = QStackedWidget()
        
        # Create simple pages
        self.stacked_widget.addWidget(self.create_page("Dashboard", "Welcome to the Dashboard"))
        self.stacked_widget.addWidget(self.create_page("Materials", "Material Management"))
        self.stacked_widget.addWidget(self.create_page("Users", "User Management"))
        self.stacked_widget.addWidget(self.create_page("Logs", "System Logs"))
        
        main_layout.addWidget(self.stacked_widget)
        self.setCentralWidget(main_widget)
        self.apply_styles()

        # status bar here


    def create_shadow_effect(self):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 80))
        return shadow

    def create_side_menu(self):
        side_menu = QWidget()
        side_menu.setObjectName("SideMenu")
        layout = QVBoxLayout(side_menu)
        layout.setContentsMargins(10, 20, 10, 20)
        layout.setSpacing(15)
        
        # Profile Section
        profile = QWidget()
        profile_layout = QHBoxLayout(profile)
        user_icon = QLabel()
        user_icon.setPixmap(fa.icon('fa5s.user-circle', color='#ecf0f1').pixmap(40, 40))
        user_label = QLabel("<b>Admin User</b><br><font color='#bdc3c7'>Administrator</font>")
        profile_layout.addWidget(user_icon)
        profile_layout.addWidget(user_label)
        
        # Menu Buttons
        btn_dashboard = QPushButton("  Dashboard")
        btn_dashboard.setIcon(fa.icon('fa5s.tachometer-alt', color='#ecf0f1'))
        btn_dashboard.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        
        btn_materials = QPushButton("  Materials")
        btn_materials.setIcon(fa.icon('fa5s.boxes', color='#ecf0f1'))
        btn_materials.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        
        btn_users = QPushButton("  Users")
        btn_users.setIcon(fa.icon('fa5s.users', color='#ecf0f1'))
        btn_users.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))
        
        btn_logs = QPushButton("  Logs")
        btn_logs.setIcon(fa.icon('fa5s.file-alt', color='#ecf0f1'))
        btn_logs.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(3))
        
        # Separator
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
        btn_logout.setIcon(fa.icon('fa5s.sign-out-alt', color='#ecf0f1'))
        btn_logout.clicked.connect(self.close)
        layout.addWidget(btn_logout)
        
        return side_menu

    def create_page(self, title, message):
        page = QWidget()
        layout = QVBoxLayout(page)
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
        layout.addStretch()
        
        return page

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow, QStackedWidget > QWidget { 
                background-color: #ecf0f1; 
            }
            QWidget#SideMenu { 
                background-color: #2c3e50; 
                color: #ecf0f1;
                max-width: 250px;           
                width: 250px; 
            }
            #SideMenu QLabel { 
                color: #ecf0f1; 
            }
            #SideMenu QPushButton { 
                background-color: transparent; 
                color: #ecf0f1; 
                border: none; 
                padding: 12px; 
                text-align: left; 
                font-family: "Segoe UI"; 
                font-size: 14px; 
                font-weight: bold; 
                border-radius: 5px; 
            }
            #SideMenu QPushButton:hover { 
                background-color: #34495e; 
            }
            QFrame#Separator { 
                background-color: #34495e; 
                height: 1px; 
            }
            QLabel#PageTitle { 
                color: #2c3e50; 
            }
            QLabel#PageMessage {
                color: black;
            }
        """)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    dashboard = MinimalDashboard()
    dashboard.show()
    sys.exit(app.exec())