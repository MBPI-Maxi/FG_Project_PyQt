from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QMessageBox,
    QComboBox,
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from models import User, AuthLog
from constants.Enums import Department, UserRole
from sqlalchemy.exc import SQLAlchemyError
from app.helpers import button_cursor_pointer

import hashlib
import socket
import os

class Registration(QWidget):
    def __init__(self, session_factory, parent=None):
        super().__init__(parent)
        self.session_factory = session_factory
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("User Registration")
        self.setFixedSize(400, 500)

        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        title = QLabel("Create New Account")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Confirm Password")
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.role_input = QComboBox()
        self.role_input.addItems([role.name for role in UserRole])

        self.department_input = QComboBox()
        self.department_input.addItems([dept.name for dept in Department])

        self.register_button = QPushButton("Register")
        self.register_button.clicked.connect(self.handle_registration)

        layout.addWidget(title)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.confirm_password_input)
        layout.addWidget(QLabel("Role:"))
        layout.addWidget(self.role_input)
        layout.addWidget(QLabel("Department:"))
        layout.addWidget(self.department_input)
        layout.addSpacing(10)
        layout.addWidget(self.register_button)

        self.setLayout(layout)
        self.apply_styles()

    def apply_styles(self):
        qss_path = os.path.join(os.path.dirname(__file__), "styles", "registration.css")
        
        try:
            button_cursor_pointer(self.register_button)

            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print("Warning: Style file not found. Default styles will be used.")
        
    def hash_password(self, password):
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def get_workstation_name(self):
        return socket.gethostname()

    def handle_registration(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        role = self.role_input.currentText()
        department = self.department_input.currentText()

    

        if not username or not password:
            QMessageBox.warning(
                self, "Input Error", "Username and password cannot be empty."
            )
            return

        if password != confirm_password:
            QMessageBox.warning(
                self, "Input Error", "Please confirm the password if correct."
            )
            return

        hashed_password = self.hash_password(password)
        workstation_name = self.get_workstation_name()

        session = self.session_factory()

        try:
            # Check if user exists
            if session.query(User).filter_by(username=username).first():
                QMessageBox.warning(
                    self, "Registration Failed", "Username already exists."
                )
                return

            us_role = UserRole[role].value
            dept_role = Department[department].value

            new_user = User(
                username=username.lower(), # lowercase name 
                password=hashed_password,
                workstation_name=workstation_name,
                role=UserRole[role].value,
                department=Department[department].value,
            )
            session.add(new_user)
            session.commit()

            # Log registration
            log = AuthLog(
                user_id=new_user.user_id,
                username=new_user.username,
                event_type="REGISTRATION",
                status="SUCCESS",
                additional_info=f"Created from {workstation_name}",
            )
            session.add(log)
            session.commit()

            QMessageBox.information(self, "Success", "User registered successfully.")
            self.close()
        except SQLAlchemyError as e:
            session.rollback()
            QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")
            print(f"Error: {e}")
        finally:
            session.close()
