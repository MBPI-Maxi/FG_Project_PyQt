from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import Qt

class StyledMessageBox(QMessageBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setStyleSheet("""
            QMessageBox {
                background-color: #ffffff;
            }
            QMessageBox QLabel {
                color: #333333;
                font-size: 14px;
            }  
            QMessageBox QPushButton {
                background-color: #0078d7;
                color: white;
                min-width: 80px;
                padding: 10px 10px;
                border-radius: 4px;
                font-size: 12px;
            }             
        """)

    @staticmethod
    def _apply_text_format(msgBox: QMessageBox, use_rich_text: bool):
        if use_rich_text:
            msgBox.setTextFormat(Qt.TextFormat.RichText)
        
    @classmethod
    def information(cls, parent, title, message, setTextFormat=False):
        msg = cls(parent)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle(title)
        
        # ------------- THIS WILL READ THE STRING AS AN HTML FORMAT STRING -----------
        cls._apply_text_format(msg, setTextFormat)
        
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        msg.exec()
        
        return msg

    @classmethod
    def warning(cls, parent, title, message, setTextFormat=False):
        msg = cls(parent)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle(title)

        cls._apply_text_format(msg, setTextFormat)

        msg.setText(message)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        msg.exec()
        
        return msg

    @classmethod
    def critical(cls, parent, title, message, setTextFormat=False):
        msg = cls(parent)
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle(title)

        cls._apply_text_format(msg, setTextFormat)
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)

        msg.exec()
        
        return msg

    @classmethod
    def question(cls, parent, title, message, setTextFormat=False):
        msg = cls(parent)
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setWindowTitle(title)
        cls._apply_text_format(msg, setTextFormat)
        msg.setText(message)
        msg.setStandardButtons(
            QMessageBox.StandardButton.Yes | 
            QMessageBox.StandardButton.No
        )
        
        return msg.exec()

class TerminalCustomStylePrint():
    """Utility for styled terminal messages and exceptions"""

    @classmethod
    def raise_red_flag(cls, message: str, has_QMessageBox=False):
        """Raises an error in the terminal and optionally on the QMessagebox"""
        
        if has_QMessageBox:
            cls.terminal_message_custom_format(message, is_error=True)
            
            raise ValueError(message)
        else:
            cls.terminal_message_custom_format(message)

    @staticmethod
    def terminal_message_custom_format(message: str, is_error=False):
        """Print a green-colored message in terminal"""
        
        if not is_error:
            print(f"\033[92m{message}\033[0m")
        else:
            status = {
                "error": f"\033[93mValueError:\033[0m", # YELLOW
                "msg": f"\033[91m{message}\033[0m" # RED
            }

            print(status["error"], status["msg"])
            