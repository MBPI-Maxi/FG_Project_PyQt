from config.db import is_connected, engine
from app.auth.login import LoginForm

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
import sys

if __name__ == "__main__":
    if is_connected == True:
        print("Database is connected.")
        
        app = QApplication(sys.argv)
        
        # load the login application here
        login_view = LoginForm(engine=engine)
        login_view.show()


        # timer sample
        # QTimer.singleShot(60000, login_view.close)


        sys.exit(app.exec())
    else:
        print(f"Failed to connect to the database: {is_connected}")
