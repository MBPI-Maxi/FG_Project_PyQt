# function for pointing hand cursor
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QPushButton
from sqlalchemy import text
from sqlalchemy.orm import Session, DeclarativeMeta
from typing import Type, Dict, Any

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


# FOR CREATING THE T_REF_NO on the views
def fetch_current_t_refno_in_endorsement(session: Session, endorsement_model: Type[DeclarativeMeta]) -> str:
    table_name = endorsement_model.__tablename__
    column_name = "t_id" # because the id and reference number will only follow the current id

    # Get the sequence name
    result = session.execute(
        text("SELECT pg_get_serial_sequence(:table, :column) AS seq_name"),
        {"table": table_name, "column": column_name}
    )
    seq_name = result.scalar()

    # Get current value of the sequence (non-incrementing)
    result = session.execute(text(f"SELECT last_value FROM {seq_name}"))
    current_value = result.scalar()

    # Optional: You can also +1 if you want the next expected ID
    return f"EF-{current_value + 1}"



def calculate_qty_on_endorsement_table_2():
    pass



# FOR CREATING THE ENDORSEMENT TABLE 2 
def generate_endorsement_table_2(
    endorsement_model: Type[DeclarativeMeta],
    endorsement_model_t2: Type[DeclarativeMeta],
    validated_data 
):
    t2_items = []
    validated_lot_number = validated_data.t_lotnumberwhole

    if "-" in validated_lot_number:
        start_lot = validated_lot_number[:6]
        end_lot = validated_lot_number[-6:]
        
        start_number = int(start_lot[:4])
        end_number = int(end_lot[:4])

        for number in range(start_number, end_number + 1):
            lot_code = f"{number:04d}{start_lot[4:]}"
            t2_items.append(
                endorsement_model_t2(
                    t_refno=validated_data.t_refno,
                    t_lotnumbersingle=lot_code,
                    t_qty=validated_data.t_qtykg # calculate the value here to be inputted
                )
            )
    else:
        # single lot entry
        t2_items.append(
            endorsement_model_t2(
                t_refno=validated_data.t_refno,
                t_lotnumbersingle=validated_data.t_lotnumberwhole,
                t_qty=validated_data.t_qtykg # if single quantity input it as is.
            )
        )

    # attaching to the main model here
    endorsement_model.endorsement_t2_items = t2_items
    