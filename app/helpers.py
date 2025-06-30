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

# FOR CREATING THE T_REF_NO
def fetch_current_t_refno_in_endorsement(session: Type[Session], endorsement_model: Type[DeclarativeMeta]) -> str:
    order_by_sequence = endorsement_model.t_id.desc()
    endorsement_instance = session.query(endorsement_model).order_by(order_by_sequence).first()
    
    data_split = endorsement_instance.t_refno.split("-")
    current_number = int(data_split[1])

    if endorsement_instance is None:
        return "EF-1"
    
    return f"EF-{current_number + 1}"
    