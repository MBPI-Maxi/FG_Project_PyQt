from config.db import is_connected, engine
from sqlalchemy.orm import sessionmaker
from app.auth.login import LoginForm
from PyQt6.QtWidgets import QApplication

import sys

if __name__ == "__main__":
    if is_connected == True:
        print("Database is connected.")
        
        app = QApplication(sys.argv)
        
        # load the login application here
        session_factory = sessionmaker(engine)

        login_view = LoginForm(session_factory=session_factory)
        login_view.show()

        # timer sample
        # from PyQt6.QtCore import QTimer
        # QTimer.singleShot(60000, login_view.close)

        sys.exit(app.exec())
    else:
        print(f"Failed to connect to the database: {is_connected}")
