from FrmDashboard import FrmDashboard, QApplication, create_table_if_not_exists
from PyQt6.QtWidgets import QMessageBox, QWidget
import psycopg2
import sys

DB_CONFIG = {
    "dbname": "dbinventory", "user": "postgres", "password": "mbpi",
    "host": "192.168.1.13", "port": "5432"
}

class DummyLogin(QWidget):
    def show(self): 
        print("Logout successful.")

    def close(self): 
        print("Application exit."); QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    try:
        print("Connecting to the database...")
        connection = psycopg2.connect(**DB_CONFIG)
        print("Connection successful.")
        
        create_table_if_not_exists(connection)
        
        dashboard = FrmDashboard("admin_user", connection, DummyLogin())
        dashboard.show()
        sys.exit(app.exec())

    except psycopg2.Error as e:
        QMessageBox.critical(None, "Database Error", f"A database error occurred: {e}")
        sys.exit(1)
    except Exception as e:
        QMessageBox.critical(None, "Application Error", f"An unexpected error occurred: {e}")
        sys.exit(1)