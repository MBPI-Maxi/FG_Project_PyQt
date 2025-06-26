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
from constants.Enums import Department, UserRole, AuthLogStatus
from sqlalchemy.exc import SQLAlchemyError
from app.helpers import button_cursor_pointer, record_auth_log, add_new_user

import hashlib
import socket
import os

class Registration(QWidget):
    def __init__(self, session_factory, parent=None):
        super().__init__(parent)
        self.session_factory = session_factory
        # self.init_ui()

        self.setWindowTitle("User Registration")
        self.setFixedSize(400, 500)

        # MAIN LAYOUT
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(30, 30, 30, 30)
        self.main_layout.setSpacing(15)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # TITLE
        self.title = QLabel("Create New Account")
        self.title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.role_label = QLabel("Role:")
        self.department_label = QLabel("Department:")

        # INPUT FIELDS
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Confirm Password")
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)

        # COMBO BOX
        self.role_input = QComboBox()
        self.role_input.addItems([role.name for role in UserRole])

        self.department_input = QComboBox()
        self.department_input.addItems([dept.name for dept in Department])

        # BUTTONS
        self.register_button = QPushButton("Register")
        self.register_button.clicked.connect(self.handle_registration)

        self.main_layout.addWidget(self.title)
        self.main_layout.addWidget(self.username_input)
        self.main_layout.addWidget(self.password_input)
        self.main_layout.addWidget(self.confirm_password_input)
        # self.main_layout.addWidget(QLabel("Role:"))
        self.main_layout.addWidget(self.role_label)
        self.main_layout.addWidget(self.role_input)
        # self.main_layout.addWidget(QLabel("Department:"))
        self.main_layout.addWidget(self.department_label)
        self.main_layout.addWidget(self.department_input)
        self.main_layout.addSpacing(10)
        self.main_layout.addWidget(self.register_button)

        self.setLayout(self.main_layout)
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

        # initialize the session here that was imported in the Login widget
        session = self.session_factory()

        try:
            # Check if user exists
            if session.query(User).filter_by(username=username).first():
                QMessageBox.warning(
                    self, "Registration Failed", "Username already exists."
                )
                return
 
            # record new user in the User model
            user_details = {
                "username": username.lower(),
                "password": hashed_password,
                "workstation_name": workstation_name,
                "role": UserRole[role].value,
                "department": Department[department].value
            }

            new_user = add_new_user(
                session=session,
                data_required=user_details,
                user_model=User
            )

            record_auth_log(
                session=session,
                data_required={
                    "user_id": new_user.user_id,
                    "username": new_user.username,
                    "event_type": AuthLogStatus.get_event_type("registration"),
                    "status": AuthLogStatus.SUCCESS.value
                },
                auth_log_model=AuthLog
            )

            # commit everything if there is no failed transaction on both helper function 
            session.commit()

            QMessageBox.information(self, "Success", "User registered successfully.")
            self.close()

        except SQLAlchemyError as e:
            session.rollback()
            QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")
            print(f"SQLAlchemyError: {e}")
        except TypeError as e:
            session.rollback()
            QMessageBox.critical(self, "Program Error", f"An error occurred: {e}")
            print(f"TypeError: {e}")
        finally:
            session.close()
