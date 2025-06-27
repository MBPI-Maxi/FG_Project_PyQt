from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QStackedWidget, QStatusBar
)
from app.views import (
    EndorsementView,
    QCFailedToPassed,
    QCLabExcess,
    ReceivingReport,

    DeliveryReceipt,
    ReturnReplacement,
    OutgoingRecord,
    RequisitionLogbook,
    QCFailedEndorsement
)

from PyQt6.QtGui import QFont
from PyQt6.QtCore import QSize, QTimer
from typing import Type
from datetime import datetime


import qtawesome as qta
import os

class FGDashboard(QMainWindow):
    def __init__(self, username, role, login_widget, *args, **kwargs):
        # self.management_submenu_visible = False
        super().__init__(*args, **kwargs)
        
        # initialization
        self.username = username
        self.role = role
        self.login_widget = login_widget

        # VIEWS
        self.form_views = [
            EndorsementView,
            QCFailedEndorsement,
            QCLabExcess,
            ReceivingReport,
            DeliveryReceipt,
            ReturnReplacement,
            OutgoingRecord,
            RequisitionLogbook,
            QCFailedEndorsement
        ]
        

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
        # INCOMING
        self.add_stack_page("Endorsement", "Endorsement", EndorsementView())
        self.add_stack_page("QC Failed to Passed", "QC Failed to Passed", QCFailedToPassed())
        self.add_stack_page("QC Lab Excess", "QC Lab Excess", QCLabExcess())
        self.add_stack_page("Receiving Report", "Receiving Report", ReceivingReport())

        # OUTGOING
        self.add_stack_page("Delivery Receipt", "Delivery Receipt", DeliveryReceipt())
        self.add_stack_page("Return Replacement", "Return Replacement", ReturnReplacement())
        self.add_stack_page("Outgoing Form", "Outgoing Form", OutgoingRecord())
        self.add_stack_page("Requisition Logbook", "Requisition Logbook", RequisitionLogbook())
        self.add_stack_page("QC Failed Endorsement", "QC Failed Endorsement", QCFailedEndorsement())

        # STATUS BAR
        self.setup_status_bar()

        # INITIALIZE STYLES
        self.apply_styles()

        # ADD THE MAIN WIDGET
        self.main_layout.addWidget(self.stacked_widget)
        self.setCentralWidget(self.main_widget)

    def set_username(self, value):
        self.username = value
        self.status_bar.showMessage(f"Ready | Logged in as: {self.username.title()}")
    
    def set_role(self, value):
        self.role = value
    
    def setup_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.db_status_icon_label = QLabel()
        self.db_status_icon_label.setFixedSize(QSize(20, 20))
        self.db_status_icon_label.setObjectName("FGDashboard-db-status-icon-label")
        
        self.db_status_text_label = QLabel()
        self.db_status_text_label.setObjectName("FGDashboard-db-status-text-label")

        self.time_label = QLabel()
        self.time_label.setObjectName("FGDashboard-status-time-label")
        
        # icon for db_status_icon_label
        self.db_status_icon_label.setPixmap(
            qta.icon("fa5s.check-circle", color="green").pixmap(QSize(16, 16))
        )
        self.db_status_text_label.setText("DB Connected ")

        self.status_bar.addPermanentWidget(self.db_status_icon_label)
        self.status_bar.addPermanentWidget(self.db_status_text_label)
        self.status_bar.addPermanentWidget(self.time_label)

        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(
            lambda: self.time_label.setText(f" {datetime.now().strftime('%b %d, %Y  %I:%M:%S %p')} "
        ))
        self.status_timer.setObjectName("FGDashboard-status-qtimer")

        self.status_timer.start(1000)
    
    def side_menu_widget(self):
        side_menu = QWidget()
        side_menu.setObjectName("SideMenu")
        layout = QVBoxLayout(side_menu)
        layout.setContentsMargins(10, 20, 10, 20)
        layout.setSpacing(15)
        
        # --- Profile Section ---
        profile = QWidget()
        profile_layout = QHBoxLayout(profile)
        profile_layout.setContentsMargins(0, 0, 0, 0)
        profile_layout.setSpacing(5)

        user_icon = QLabel()
        user_icon.setPixmap(qta.icon("fa5s.user-circle", color="#ecf0f1").pixmap(40, 40))

        username = self.username if self.username else "Guest"
        role = self.role if self.role else "User"

        user_label = QLabel(f"<strong>{username.title()}</strong><br/><font color='#bdc3c7'>{role.title()}</font>")
        user_label.setObjectName("qlabel-profile-name")
        profile_layout.addWidget(user_icon)
        profile_layout.addWidget(user_label)
        profile_layout.addStretch()

        # --- Separator ---
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setObjectName("Separator")

        layout.addWidget(profile)
        layout.addWidget(separator)

        # === Incoming Section ===
        incoming_label = QLabel("INCOMING")
        incoming_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        incoming_label.setStyleSheet("color: grey;")
        layout.addWidget(incoming_label)    

        btn_endorsement = QPushButton("  Endorsement Form")
        btn_endorsement.setIcon(qta.icon("fa5s.file-signature", color="#ecf0f1"))
        btn_endorsement.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
          
        btn_qc_failed_to_passed = QPushButton("  QC Failed → Passed")
        btn_qc_failed_to_passed.setIcon(qta.icon("fa5s.check-double", color="#ecf0f1"))
        btn_qc_failed_to_passed.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))  # Index 1

        btn_qc_lab_excess = QPushButton("  QC Lab Excess Sheet")
        btn_qc_lab_excess.setIcon(qta.icon("fa5s.vials", color="#ecf0f1"))
        btn_qc_lab_excess.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))  # Index 2

        btn_receiving_report = QPushButton("  Receiving Report")
        btn_receiving_report.setIcon(qta.icon("fa5s.file-invoice", color="#ecf0f1"))
        btn_receiving_report.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(3))  # Index 3

        layout.addWidget(btn_endorsement)
        layout.addWidget(btn_qc_failed_to_passed)
        layout.addWidget(btn_qc_lab_excess)
        layout.addWidget(btn_receiving_report)

        # === Outgoing Section ===
        outgoing_label = QLabel("OUTGOING")
        outgoing_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        outgoing_label.setStyleSheet("color: grey; margin-top: 15px;")
        layout.addWidget(outgoing_label)

        btn_delivery_receipt = QPushButton("  Delivery Receipt")
        btn_delivery_receipt.setIcon(qta.icon("fa5s.truck", color="#ecf0f1"))
        btn_delivery_receipt.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(4))  # Index 5

        btn_rrf = QPushButton("  Return Replacement (RRF)")
        btn_rrf.setIcon(qta.icon("fa5s.exchange-alt", color="#ecf0f1"))
        btn_rrf.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(5))  # Index 5

        btn_outgoing_form = QPushButton("  Outgoing Record Form")
        btn_outgoing_form.setIcon(qta.icon("fa5s.file-export", color="#ecf0f1"))
        btn_outgoing_form.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(6))  # Index 6

        btn_logbook = QPushButton("  Requisition Logbook")
        btn_logbook.setIcon(qta.icon("fa5s.book", color="#ecf0f1"))
        btn_logbook.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(7))  # Index 7

        btn_qc_failed_out = QPushButton("  QC Failed Endorsement")
        btn_qc_failed_out.setIcon(qta.icon("fa5s.times-circle", color="#ecf0f1"))
        btn_qc_failed_out.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(8))  # Index 8

        layout.addWidget(btn_delivery_receipt)
        layout.addWidget(btn_rrf)
        layout.addWidget(btn_outgoing_form)
        layout.addWidget(btn_logbook)
        layout.addWidget(btn_qc_failed_out)

        layout.addStretch()

        # --- Logout Button ---
        btn_logout = QPushButton("  Logout")
        btn_logout.setIcon(qta.icon("fa5s.sign-out-alt", color="#ecf0f1"))
        btn_logout.clicked.connect(self.close_dashboard_main_window)
        
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
    
    def close_dashboard_main_window(self):
        # close the main widget here
        self.close()

        # show the login widget again here
        self.login_widget.show()

    