from config.db import is_connected, engine
from sqlalchemy.orm import sessionmaker
from app.auth.login import LoginForm
from PyQt6.QtWidgets import QApplication
from config.pyqtConfig import print_connection_status, enforce_light_theme
import sys

if __name__ == "__main__":
    print_connection_status(is_connected, engine)
    
    if is_connected == True:
        app = QApplication(sys.argv)
        enforce_light_theme(app)

        # load the login application here
        session_factory = sessionmaker(engine)

        login_view = LoginForm(session_factory=session_factory)
        login_view.show()

        sys.exit(app.exec())
    else:
        sys.exit(1)
