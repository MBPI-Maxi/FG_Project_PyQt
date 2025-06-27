from config.db import is_connected, engine
from sqlalchemy.orm import sessionmaker
from app.auth.login import LoginForm
from PyQt6.QtWidgets import QApplication

import sys

def print_connection_status():
    """Prints a formatted database connection status message"""
    status = "SUCCESSFULLY CONNECTED" if is_connected else "FAILED TO CONNECT"
    color_code = "\033[92m" if is_connected else "\033[91m"  # Green or Red
    reset_code = "\033[0m"
    
    border = "=" * 60
    print(f"\n{border}")
    print(f"{color_code} DATABASE CONNECTION STATUS: {status}{reset_code}")
    print(f"{border}\n")
    
    if is_connected:
        print(f"• Connection established to: {engine.url}")
        print("• Database engine ready for operations")
    else:
        print("• Please check your database configuration")
        print("• Verify the server is running and accessible")
        print("• Check network connectivity if using remote database")

if __name__ == "__main__":
    print_connection_status()

    if is_connected == True:
        app = QApplication(sys.argv)
        
        # load the login application here
        session_factory = sessionmaker(engine)

        login_view = LoginForm(session_factory=session_factory)
        login_view.show()

        sys.exit(app.exec())
    else:
        sys.exit(1)
