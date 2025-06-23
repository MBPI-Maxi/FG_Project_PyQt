# FILE: FrmLogin.py

import sys
import hashlib
import socket
import psycopg2
from psycopg2 import sql, errors
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QMessageBox, QInputDialog
)
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtCore import Qt, QSize
from FrmDashboard import FrmDashboard

DB_CONFIG = {'dbname': 'dbinventory', 'user': 'postgres', 'password': 'mbpi', 'host': '192.168.1.13', 'port': '5432'}
ADMIN_PASSWORD = "Itadmin"


def setup_database():
    conn = None
    try:
        conn = psycopg2.connect(dbname='postgres', user=DB_CONFIG['user'], password=DB_CONFIG['password'],
                                host=DB_CONFIG['host'], port=DB_CONFIG['port'])
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_CONFIG['dbname'],))
        if cursor.fetchone() is None:
            print(f"Database '{DB_CONFIG['dbname']}' not found. Creating it...")
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB_CONFIG['dbname'])))
            print("Database created successfully.")
        cursor.close()
        conn.close()
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS tbl_user_pass (t_wsid VARCHAR(35), t_wsname VARCHAR(50), t_username VARCHAR(50) PRIMARY KEY, t_userpass VARCHAR(64) NOT NULL);""")
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS tbl_user_log01 (log_id SERIAL PRIMARY KEY, t_wsid VARCHAR(35), t_username VARCHAR(50), login_timestamp TIMESTAMPTZ DEFAULT NOW());""")
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS tbl_user_log02 (log_id SERIAL PRIMARY KEY, t_wsname VARCHAR(50), t_username VARCHAR(50), t_datetime TIMESTAMPTZ DEFAULT NOW(), t_status VARCHAR(10));""")
        conn.commit()
        print("All tables checked/created successfully.")
        return conn
    except psycopg2.OperationalError as e:
        QMessageBox.critical(None, "Database Error",
                             f"Could not connect to PostgreSQL: {e}\n\nPlease check your connection details, firewall, and ensure the server is running.")
        return None
    except Exception as e:
        QMessageBox.critical(None, "Setup Error", f"An unexpected error occurred: {e}")
        return None


class LoginForm(QWidget):
    def __init__(self, db_connection):
        super().__init__()
        self.conn = db_connection
        self.dashboard_window = None
        self.init_ui()

    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        if not username or not password:
            QMessageBox.warning(self, "Input Error", "Username and password cannot be empty.")
            return

        hashed_password = self.hash_password(password)
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT t_username FROM tbl_user_pass WHERE t_username = %s AND t_userpass = %s;",
                               (username, hashed_password))
                result = cursor.fetchone()

            if result:
                self.log_event(username, 'SUCCESS')
                print(f"Login successful for user: {result[0]}. Opening dashboard...")

                self.dashboard_window = FrmDashboard(
                    username=result[0],
                    connection=self.conn,
                    login_window=self
                )

                self.dashboard_window.showMaximized()
                self.hide()
            else:
                self.log_event(username, 'FAIL')
                QMessageBox.warning(self, "Login Failed", "Invalid username or password.")
                self.password_input.clear()
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred during login: {e}")
            self.conn.rollback()

    # Condensed helper methods for brevity
    def init_ui(self):
        self.setWindowTitle("User Login"); self.setFixedSize(400,
                                                             550); main_layout = QVBoxLayout(); main_layout.setContentsMargins(
            40, 40, 40, 40); main_layout.setSpacing(20); main_layout.setAlignment(
            Qt.AlignmentFlag.AlignCenter); logo_label = QLabel(); pixmap = QPixmap(
            self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon).pixmap(
                QSize(80, 80))); logo_label.setPixmap(pixmap); logo_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter); title_label = QLabel("Welcome Back"); title_label.setFont(
            QFont("Segoe UI", 22, QFont.Weight.Bold)); title_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter); subtitle_label = QLabel("Sign in to continue"); subtitle_label.setFont(
            QFont("Segoe UI", 12)); subtitle_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter); subtitle_label.setStyleSheet(
            "color:#555;"); self.username_input = QLineEdit(); self.username_input.setPlaceholderText(
            "Username"); self.password_input = QLineEdit(); self.password_input.setPlaceholderText(
            "Password"); self.password_input.setEchoMode(QLineEdit.EchoMode.Password); self.login_button = QPushButton(
            "LOGIN"); self.login_button.setFixedHeight(45); self.create_user_button = QPushButton(
            "Create New User"); self.create_user_button.setObjectName("CreateUserButton"); main_layout.addWidget(
            logo_label); main_layout.addWidget(title_label); main_layout.addWidget(
            subtitle_label); main_layout.addSpacing(20); main_layout.addWidget(
            self.username_input); main_layout.addWidget(self.password_input); main_layout.addSpacing(
            10); main_layout.addWidget(self.login_button); main_layout.addStretch(1); main_layout.addWidget(
            self.create_user_button); self.setLayout(main_layout); self.apply_styles(); self.connect_signals()

    def apply_styles(self):
        self.setStyleSheet(
            """QWidget{background-color:#ffffff;color:#000000;font-family:Segoe UI}QLineEdit{border:1px solid #cccccc;border-radius:8px;padding:12px;font-size:14px;background-color:#f7f7f7}QLineEdit:focus{border:1px solid #0078d7}QPushButton{background-color:#0078d7;color:white;font-size:14px;font-weight:bold;border:none;border-radius:8px;padding:12px}QPushButton:hover{background-color:#005a9e}QPushButton#CreateUserButton{background-color:transparent;color:#0078d7;font-weight:normal;text-align:center}QPushButton#CreateUserButton:hover{text-decoration:underline}""")

    def connect_signals(self):
        self.login_button.clicked.connect(self.handle_login); self.create_user_button.clicked.connect(
            self.show_create_user_dialog); self.username_input.returnPressed.connect(
            self.handle_login); self.password_input.returnPressed.connect(self.handle_login)

    def hash_password(self, password):
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    def get_workstation_info(self):
        hostname = socket.gethostname(); return {'wsid': hostname, 'wsname': hostname}

    def log_event(self, username, status):
        if not self.conn: return
        try:
            with self.conn.cursor() as cursor:
                if status == 'SUCCESS': cursor.execute(
                    "INSERT INTO tbl_user_log01 (t_wsid, t_username) VALUES (%s, %s);",
                    (self.get_workstation_info()['wsid'], username))
                cursor.execute("INSERT INTO tbl_user_log02 (t_wsname, t_username, t_status) VALUES (%s, %s, %s);",
                               (self.get_workstation_info()['wsname'], username, status))
            self.conn.commit()
        except psycopg2.Error as e:
            print(f"Error logging event: {e}"); self.conn.rollback()

    def show_create_user_dialog(self):
        admin_pass, ok = QInputDialog.getText(self, "Admin Access Required", "Enter IT Admin Password:",
                                              QLineEdit.EchoMode.Password);_ = (
            self.prompt_for_new_user_details() if ok and admin_pass == ADMIN_PASSWORD else (
                QMessageBox.critical(self, "Access Denied", "Incorrect admin password.") if ok else None))

    def prompt_for_new_user_details(self):
        username, ok1 = QInputDialog.getText(self, "Create User", "Enter new username:"); password, ok2 = (
            QInputDialog.getText(self, "Create User", "Enter password:",
                                 QLineEdit.EchoMode.Password) if ok1 and username.strip() else (
            None, False)); confirm_pass, ok3 = (QInputDialog.getText(self, "Create User", "Confirm password:",
                                                                     QLineEdit.EchoMode.Password) if ok2 and password else (
        None, False)); _ = (
            self.create_user_in_db(username.strip(), password) if ok3 and password == confirm_pass else (
                QMessageBox.warning(self, "Error",
                                    "Passwords do not match.") if ok3 and password != confirm_pass else None))

    def create_user_in_db(self, username, password):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO tbl_user_pass (t_wsid, t_wsname, t_username, t_userpass) VALUES (%s, %s, %s, %s);", (
                    self.get_workstation_info()['wsid'], self.get_workstation_info()['wsname'], username,
                    self.hash_password(password)))
            self.conn.commit();
            QMessageBox.information(self, "Success", f"User '{username}' created successfully.")
        except errors.UniqueViolation:
            QMessageBox.warning(self, "Creation Failed", f"Username '{username}' already exists."); self.conn.rollback()
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to create user: {e}"); self.conn.rollback()


if __name__ == '__main__':
    db_connection = setup_database()
    if not db_connection: sys.exit(1)
    app = QApplication(sys.argv)
    login_window = LoginForm(db_connection)
    login_window.show()
    exit_code = app.exec()
    if db_connection: db_connection.close(); print("Database connection closed.")
    sys.exit(exit_code)