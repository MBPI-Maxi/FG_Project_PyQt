# function for pointing hand cursor
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QPushButton, QLineEdit
from typing import Type, Dict, Any
from sqlalchemy.orm import Session, DeclarativeMeta

class ButtonCursorError(BaseException):
    pass

# FOR CREATING CURSOR POINTER ON BUTTON
def button_cursor_pointer(button_widget: Type[QPushButton]):
    if isinstance(button_widget, QPushButton):
        button_widget.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
    else:
        raise ButtonCursorError("argument is not a QPushButton instance")

# FOR LOGGING AUTH LOGS
def record_auth_log(
    session: Type[Session],
    data_required: Dict[str, Any],
    auth_log_model: Type[DeclarativeMeta],
    commit=False
) -> None:
    
    log = auth_log_model(**data_required)
    
    session.add(log)

    if commit:
        session.commit()

# FOR ADDING NEW USER
def add_new_user(
    session: Type[Session],
    data_required: Dict[str, Any],
    user_model: Type[DeclarativeMeta],
) -> type[DeclarativeMeta]:
    
    new_user = user_model(**data_required)

    session.add(new_user)
    session.flush() # this makes the user ID available to use (ie new_user.user_id) but doesn't commit

    return new_user


# FOR CREATING A LABELED INPUT WITH ERROR LABEL INLINE
def modified_input_row(
    label_text: str,
    widget: Type[QLineEdit],
    field_name: str,
    error_label_name: str
): 
    pass
    