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

import sys
import hashlib
import socket
import os

# import models here
from models import User, AuthLog

# registration
from app.auth.registration import Registration

# helpers
from app.helpers import button_cursor_pointer

# super password
from constants.Enums import ITCredentials

class LoginForm(QWidget):
    def __init__(self, engine, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        try:
            self.Session = sessionmaker(engine)
            self.dashboard_window = None
        except SQLAlchemyError as e:
            QMessageBox.critical(
                None, "Database Error",
                f"Could not connect to database: {e}\n\n"
                "Please check your connection details and ensure the server is running."
            )
            sys.exit(1)
        
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("User Login")
        self.setFixedSize(400, 550)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # LOGO
        logo_label = QLabel()
        pixmap = QPixmap(
            self.style()
            .standardIcon(self.style().StandardPixmap.SP_ComputerIcon)
            .pixmap(QSize(80, 80))
        )
        logo_label.setPixmap(pixmap)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Title
        title_label = QLabel("Welcome Back")
        title_label.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Subtitle
        subtitle_label = QLabel("Sign in to continue")
        subtitle_label.setFont(QFont("Segoe UI", 12))
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color:#555;")

        # Input fields
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        # Buttons
        self.login_button = QPushButton("LOGIN")
        self.login_button.setFixedHeight(45)

        self.create_user_button = QPushButton("Create New User")
        self.create_user_button.setObjectName("CreateUserButton")

        # Add widgets to layout
        main_layout.addWidget(logo_label)
        main_layout.addWidget(title_label)
        main_layout.addWidget(subtitle_label)
        main_layout.addSpacing(20)
        main_layout.addWidget(self.username_input)
        main_layout.addWidget(self.password_input)
        main_layout.addSpacing(10)
        main_layout.addWidget(self.login_button)
        main_layout.addStretch(1)
        main_layout.addWidget(self.create_user_button)

        self.setLayout(main_layout)
        self.apply_styles()
        self.connect_signals()
    
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
                log = AuthLog(
                    username=username,
                    event_type="LOGIN",
                    status="FAILED",
                    additional_info=f"Attempted from {workstation_name}"
                )
                session.add(log)
                session.commit()

                return

            # login is successful
            log = AuthLog(
                user_id=user.user_id,
                username=user.username,
                event_type="LOGIN",
                status="SUCCESS",
                additional_info=f"Logged in from {workstation_name}",
            )
            session.add(log)
            session.commit()

            QMessageBox.information(
                self,
                "Login Success",
                f"Welcome, {user.username}!"
            )

            # TODO: Open dashboard or next window here

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
        