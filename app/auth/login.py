from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QMessageBox,
    QInputDialog
)
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtCore import Qt, QSize
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from old_files.FrmDashboard import FrmDashboard

import sys
import hashlib
import socket
import os

# import models here
from models import User, AuthLog

# registration
from app.auth.registration import Registration

# helpers
from app.helpers import button_cursor_pointer, record_auth_log

# super password
from constants.Enums import ITCredentials, AuthLogStatus

class LoginForm(QWidget):
    def __init__(self, session_factory, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("User Login")
        self.setFixedSize(400, 550)

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(40, 40, 40, 40)
        self.main_layout.setSpacing(20)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # LOGO
        self.logo_label = QLabel()
        pixmap = QPixmap(
            self.style()
            .standardIcon(self.style().StandardPixmap.SP_ComputerIcon)
            .pixmap(QSize(80, 80))
        )
        self.logo_label.setPixmap(pixmap)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # TITLE
        self.title_label = QLabel("Welcome Back")
        self.title_label.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # SUBTITLE
        self.subtitle_label = QLabel("Sign in to continue")
        self.subtitle_label.setFont(QFont("Segoe UI", 12))
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setStyleSheet("color:#555;")

        # INPUT FIELDS
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        # BUTTONS
        self.login_button = QPushButton("LOGIN")
        self.login_button.setFixedHeight(45)
        self.create_user_button = QPushButton("Create New User")
        self.create_user_button.setObjectName("CreateUserButton")

        # ADD WIDGET TO LAYOUT
        self.main_layout.addWidget(self.logo_label)
        self.main_layout.addWidget(self.title_label)
        self.main_layout.addWidget(self.subtitle_label)
        self.main_layout.addSpacing(20)
        self.main_layout.addWidget(self.username_input)
        self.main_layout.addWidget(self.password_input)
        self.main_layout.addSpacing(10)
        self.main_layout.addWidget(self.login_button)
        self.main_layout.addStretch(1)
        self.main_layout.addWidget(self.create_user_button)

        # sample line edit
        # test_input = QLineEdit()
        # test_input.setInputMask("0000 - 0000 - 0000;_")
        # main_layout.addWidget(test_input)

        self.setLayout(self.main_layout)
        self.apply_styles()
        self.connect_signals()

        try:
            # self.Session = sessionmaker(engine)
            self.Session = session_factory
            self.dashboard_window = None
        except SQLAlchemyError as e:
            QMessageBox.critical(
                None, "Database Error",
                f"Could not connect to database: {e}\n\n"
                "Please check your connection details and ensure the server is running."
            )

            sys.exit(1)
    
    def apply_styles(self):
        button_cursor_pointer(self.login_button)
        button_cursor_pointer(self.create_user_button)
        qss_path = os.path.join(os.path.dirname(__file__), "styles", "login.css")
        
        try:
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print("Warning: Style file not found. Default styles will be used.")

    def connect_signals(self):
        self.login_button.clicked.connect(self.handle_login)
        self.create_user_button.clicked.connect(self.open_registration_form)
        self.username_input.returnPressed.connect(self.handle_login)
        self.password_input.returnPressed.connect(self.handle_login)
    
    def hash_password(self, password):
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    def get_workstation_name(self):
        return socket.gethostname()

    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        

        if username is None or password is None:
            QMessageBox.warning(
                self,
                "Input Error",
                "Username and password cannot be empty."
            )
        
        # hashed the password here
        hashed_password = self.hash_password(password)
        
        workstation_name = self.get_workstation_name()

        # start the session here
        session = self.Session()

        try:
            user = session.query(User).filter_by(
                username=username,
                password=hashed_password
            ).first()

            if not user:
                QMessageBox.warning(
                    self,
                    "Login failed",
                    "Invalid username or password"
                )

                # log failed attempt
                record_auth_log(
                    session=session,
                    data_required={
                        "username": username,
                        "event_type": AuthLogStatus.get_event_type("login"),
                        "status": AuthLogStatus.FAILED.value,
                        "additional_info": f"Attempted from {workstation_name}"
                    },
                    auth_log_model=AuthLog,
                    commit=True
                )
                
                return

            # login is successful
            record_auth_log(
                session=session,
                data_required={
                    "user_id": user.user_id,
                    "username": user.username,
                    "event_type": AuthLogStatus.get_event_type("login"),
                    "status": AuthLogStatus.SUCCESS.value,
                    "additional_info": f"Logged in from {workstation_name}"
                },
                auth_log_model=AuthLog,
                commit=True
            )

            QMessageBox.information(
                self,
                "Login Success",
                f"Welcome, {user.username}!"
            )

            # TODO: Open dashboard or next window here
            
            # close the login interface after the 
            self.close()

            # open the main dashboard for the user
            # self.dashboard = FrmDashboard(username=username, login_window=self)
            # self.dashboard.show()
            
        except SQLAlchemyError as e:
            QMessageBox.critical(
                self, 
                "Database Error", 
                f"An error occurred during login: {e}"
            )
    
    def open_registration_form(self):
        super_password, ok = QInputDialog.getText(
            self,
            "Admin Authentication",
            "Enter super password to create new user:",
            QLineEdit.EchoMode.Password
        )
        
        if ok:
            if super_password == ITCredentials.SUPER_PASSWORD.value:
                self.registration = Registration(session_factory=self.Session)
                self.registration.show()
            else:
                QMessageBox.warning(
                    self, 
                    "Access Denied", 
                    "Incorrect super password."
                )
        