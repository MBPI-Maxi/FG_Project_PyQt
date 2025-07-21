from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QSizePolicy,
    QVBoxLayout,
    QScrollArea,
    QPushButton,
    QLineEdit,
    QDateEdit,
    QCheckBox,
    QSpinBox
)
from app.helpers import (
    fetch_current_t_refno_in_endorsement,
    populate_endorsement_items,
    load_styles,
    button_cursor_pointer
)

from app.widgets import (
    ModifiedComboBox,
    TableWidget,
    LotNumberLineEdit,
    ModifiedDateEdit,
    ModifiedDoubleSpinBox
)

from PyQt6.QtCore import Qt, QDate
from app.StyledMessage import StyledMessageBox, TerminalCustomStylePrint
from typing import Callable, Type, Union, Dict, Any
from constants.Enums import CategoryEnum, StatusEnum, RemarksEnum
from constants.mapped_user import mapped_user_to_display

from sqlalchemy.orm import Session, DeclarativeMeta
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, ValidationError

import math
import json
import os


class EndorsementCreateView(QWidget):
    def __init__(
        self, 
        session_factory: Callable[..., Session],
        endorsement_t1: Type[DeclarativeMeta],
        endorsement_t2: Type[DeclarativeMeta],
        endorsement_combined_view: Type[DeclarativeMeta],
        endorsement_lot_excess: Type[DeclarativeMeta],
        endorsement_form_schema: Type[BaseModel],
        user_model: Type[DeclarativeMeta],
        parent=None
    ):
        super().__init__(parent)
        self.setWindowTitle("Endorsement Form")
        self.setObjectName("EndorsementForm")
        
        self.Session = session_factory
        self.endorsement_t1 = endorsement_t1
        self.enodrsement_t2 = endorsement_t2
        self.endorsement_combined_view = endorsement_combined_view
        self.endorsement_lot_excess = endorsement_lot_excess
        self.endorsement_form_schema = endorsement_form_schema
        self.user_model = user_model
       
        self.table_widget = self.show_table()
        self.init_ui()
        self.apply_styles()

    def init_ui(self):
        # ------------ HELPER FUNCTION IN CREATING INPUT ROWS ------------
        # NOTE: MAKE THIS INTO A STATICMETHOD FUNCTION INSTEAD. SHOULD BE NO INNER FUNCTION ON A METHOD
        def create_input_row(
            label_text: str,
            widget: Type[QWidget],
            field_name: str,
            error_label_name: str
        ):
            # ------------ Main container for the entire row -------------
            row_container = QWidget()
            row_layout = QHBoxLayout(row_container)
            row_layout.setContentsMargins(0, 5, 0, 5)  # Vertical padding
            row_layout.setSpacing(10)

            # -------------- Label (fixed width) ----------------
            label = QLabel(label_text)
            label.setFixedWidth(150) 
            label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            # ---------- width of the widget field --------------
            widget.setFixedWidth(450)
            
            if isinstance(widget, (QComboBox, ModifiedComboBox)):
                widget.setCursor(Qt.CursorShape.PointingHandCursor)

            # ---------- Error label (auto-expand) --------------
            error_label = QLabel()
            error_label.setStyleSheet("""
                color: red;
                font-size: 12px;
                font-style: italic;
                margin-left: 5px;
            """)
            error_label.setObjectName(f"{field_name}_error_label")
            error_label.setWordWrap(True)
            
            # -------------- Add widgets to layout --------------------
            row_layout.addWidget(label)
            row_layout.addWidget(widget)
            row_layout.addWidget(error_label)
            row_layout.setStretch(2, 1)  # Let error label expand
            
            # -----------------  Store references -------------------------
            self.form_fields[field_name] = widget
            self.form_fields[error_label_name] = error_label
            
            self.main_layout.addWidget(row_container)

        # -------------------  Main container with vertical layout ----------------------------
        form_container = QWidget()
        self.main_layout = QVBoxLayout(form_container)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.main_layout.setSpacing(12)

        # Dictionary to store references to input widgets and error labels
        self.form_fields = {} 

        # ---------------- Create a scroll area for the form inputs only ----------------------
        form_scroll = QScrollArea()
        form_scroll.setWidgetResizable(True)
        form_scroll.setWidget(form_container)
        form_scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    
        # -------------   Create all form rows with scrollable inputs --------------------------
        self.create_t_refno_row(create_input_row)
        self.create_date_endorsed_row(create_input_row)
        self.create_category_row(create_input_row)
        self.create_prod_code_row(create_input_row)
        self.create_lot_number_row(create_input_row)
        self.create_weight_per_lot_row(create_input_row)
        self.create_qtykg_row(create_input_row)
        self.create_bag_input_row(create_input_row)
        self.create_status_row(create_input_row)
        self.create_endorsed_by_input_row(create_input_row)
        self.create_remarks_input_row(create_input_row)

        # --------------  Add save button (outside the scroll area) -------------------------
        self.save_button = QPushButton("Save Endorsement")
        self.save_button.setObjectName("endorsement-save-btn")
        self.save_button.clicked.connect(self.save_endorsement)

        # ------------- Create table widget ------------------
        self.table_widget = self.show_table()

        # ------------- Main layout with form scroll area and table ------------------
        main_layout = QVBoxLayout(self)
        
        # ------------ Add form scroll area ------------------
        main_layout.addWidget(form_scroll)
        
        # ----------- Add save button below the scrollable form ---------------
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.addWidget(self.save_button)
        button_layout.addStretch()

        main_layout.addWidget(button_container)
        
        # ------------ Add table widget with stretch factor ----------------
        main_layout.addWidget(self.table_widget, stretch=1)

        # --------------- Connect real-time validation signals -----------------
        self.t_lotnumberwhole_input.textChanged.connect(self.validate_lot_quantity)
        self.t_qtykg_input.valueChanged.connect(self.validate_lot_quantity)
        self.t_wtlot_input.valueChanged.connect(self.validate_lot_quantity)
        self.has_excess_checkbox.stateChanged.connect(self.validate_lot_quantity)

    def show_table(self):
        table = TableWidget(
            session_factory=self.Session, 
            db_model=self.endorsement_combined_view, 
            view_type="endorsement-create", 
            parent=self,
        )
        table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        return table
        
    def validate_lot_quantity(self):
        """Real-time validation of lot quantity proportion with strict excess checking"""
        try:
            lot_text = self.t_lotnumberwhole_input.text()
            qty = self.t_qtykg_input.value()
            wtlot = self.t_wtlot_input.value()
            has_excess = self.has_excess_checkbox.isChecked()
            
            # ------------- Clear any existing messages if fields are empty -----------------
            if not lot_text or wtlot <= 0:
                self.clear_quantity_error()
                return
                
            if "-" in lot_text:
                try:
                    start, end = lot_text.split("-")
                    start_num = int(start[:4])
                    end_num = int(end[:4])
                    num_lots = (end_num - start_num) + 1
                    expected_full = num_lots * wtlot
                    
                    # ---------- New strict validation -------------
                    if not math.isclose(qty, expected_full, rel_tol=1e-5, abs_tol=1e-5):
                        if not has_excess:
                            self.show_quantity_error(
                                f"💡 Quantity doesn't match exact lots (expected {expected_full}). "
                                "You MUST check 'has excess' for partial lots",
                                require_excess=True
                            )
                            return
                        elif qty > expected_full:
                            self.show_quantity_error(
                                "💡 Excess quantity cannot exceed one full lot",
                                require_excess=True
                            )
                            return
                    else:
                        if has_excess:
                            self.show_quantity_error(
                                "💡 Uncheck 'has excess' since quantity matches exact lots",
                                require_excess=True
                            )
                            return
                            
                except (ValueError, IndexError):
                    self.show_quantity_error("Invalid lot number format")
                    return
            else:
                # ---------------- Single lot validation ------------------
                if not math.isclose(qty, wtlot, rel_tol=1e-5, abs_tol=1e-5):
                    if not has_excess:
                        self.show_quantity_error(
                            f"💡Quantity should match weight per lot ({wtlot}). "
                            "You MUST check 'has excess' for partial quantities",
                            require_excess=True
                        )
                        return
                else:
                    if has_excess:
                        self.show_quantity_error(
                            "💡 Uncheck 'has excess' since quantity matches weight per lot",
                            require_excess=True
                        )
                        return
            
            # ----------------- Clear messages if validation passes -----------------------
            self.clear_quantity_error()
            
        except Exception as e:
            print(f"Validation error: {e}")
            return

    def show_quantity_error(self, message, require_excess=False):
        """Helper to display quantity validation error"""
        error_label = self.form_fields["t_qtykg_error"]
        error_label.setText(message)
        
        # ------------- Style the quantity input ------------------
        self.t_qtykg_input.setStyleSheet("""
            border: 1px solid red;
            background-color: #FFE0E0;
        """)
        
        # ------------------- Style the error label -------------------
        error_label.setStyleSheet("""
            color: red;
            font-size: 12px;
            font-style: italic;
            margin-left: 5px;
        """)
        
        # ---------------- Highlight the excess checkbox if required ------------------
        if require_excess:
            self.has_excess_checkbox.setStyleSheet("""
                QCheckBox {
                    color: red;
                }
                QCheckBox::indicator {
                    border: 1px solid red;
                }
            """)
        else:
            self.has_excess_checkbox.setStyleSheet("")

    def clear_quantity_error(self):
        """Clear all quantity validation styling"""
        self.form_fields["t_qtykg_error"].setText("")
        self.t_qtykg_input.setStyleSheet("")
        self.has_excess_checkbox.setStyleSheet("")
            
    def refresh_table(self):
        """Refresh table data."""
        try:
            # --------------- Store current scroll position -----------------
            scroll_pos = self.table_widget.table.verticalScrollBar().value()
            
            self.table_widget.load_data()
            
            # ------------- Maintain UI state ----------------
            self.table_widget.table.verticalScrollBar().setValue(scroll_pos)
            self.table_widget.table.resizeColumnsToContents()
            
            # ----------------- Set specific column widths if needed -------------------
            self.table_widget.table.setColumnWidth(0, 120)  # Ref No
            self.table_widget.table.setColumnWidth(1, 100)  # Date
            # ... other columns ...
            
            # ----------------- Ensure last column stretches -------------------
            self.table_widget.table.horizontalHeader().setStretchLastSection(True)
        except Exception as e:
            print(f"Error refreshing table: {e}")
        
    def create_input_horizontal_layout(
        self, 
        label_text: str, 
        widget: Union[QWidget, QLineEdit, QDateEdit], 
        field_name: str, 
        error_label_name: str
    ) -> None:
        horizontal_layout = QHBoxLayout()
        
        label = QLabel(label_text)
        
        label.setFixedWidth(200)
        widget.setFixedWidth(250)

        horizontal_layout.addWidget(label)
        horizontal_layout.addWidget(widget)

        error_label = QLabel()
        error_label.setObjectName(f"{field_name}_error_label")
        horizontal_layout.addWidget(error_label)

        self.form_fields[field_name] = widget
        self.form_fields[error_label_name] = error_label
        
        self.main_layout.addLayout(horizontal_layout)
    
    # ---------------- for lot number row ---------------
    def create_lot_number_row(
        self, 
        create_input_row: Callable[[str, Union[QWidget, QLineEdit], str, str], None]
    ) -> None:
        self.t_use_whole_lot_checkbox = QCheckBox("Whole Lot")
        self.t_use_whole_lot_checkbox.setObjectName("endorsement-toggle-lot")
        
        self.t_lotnumberwhole_input = LotNumberLineEdit()
        
        def toggle_lot_number_mask(state) -> None:
            checked_state = 2
            unchecked_state = 0

            self.t_lotnumberwhole_input.clear()

            if state == checked_state:
                self.t_lotnumberwhole_input.setInputMask("0000AA-0000AA; ")
                
            elif state == unchecked_state:
                self.t_lotnumberwhole_input.setInputMask("0000AA; ")
            
            self.t_lotnumberwhole_input.setFocus()
            self.t_lotnumberwhole_input.setCursorPosition(0)

        self.t_use_whole_lot_checkbox.stateChanged.connect(toggle_lot_number_mask)

        # ------------- default -------------------
        self.t_lotnumberwhole_input.setInputMask("0000AA; ")
        self.t_lotnumberwhole_input.setPlaceholderText("e.g.1234AB or 1234AB-5678CD")

        # ----------------- add the layout to make them inline ---------------------
        lot_inline_layout = QHBoxLayout()
        lot_inline_layout.setContentsMargins(0, 0, 0, 0)
        lot_inline_layout.setSpacing(15)
        lot_inline_layout.addWidget(self.t_lotnumberwhole_input)
        lot_inline_layout.addWidget(self.t_use_whole_lot_checkbox)

        # --------------- wrapping the whole lot number in one widget -------------------
        lot_input_widget = QWidget()
        lot_input_widget.setLayout(lot_inline_layout)

        # return lot_input_widget
        create_input_row("Whole Lot Number", lot_input_widget, "t_lotnumberwhole", "t_lotnumberwhole_error")
    
    def create_date_endorsed_row(
        self, 
        create_input_row: Callable[[str, Union[QWidget, QLineEdit], str, str], None]
    ) -> None:
        # ------------------ self.t_date_endorsed_input = QDateEdit(calendarPopup=True) -------------------
        self.t_date_endorsed_input = ModifiedDateEdit(calendarPopup=True)
        self.t_date_endorsed_input.setDate(QDate.currentDate())
        self.t_date_endorsed_input.setObjectName("endorsement-date-endorsed-input")

        create_input_row("Date Endorsed:", self.t_date_endorsed_input, "t_date_endorsed", "t_date_endorsed_error")

    def create_t_refno_row(
        self, 
        create_input_row: Callable[[str, Union[QWidget, QLineEdit], str, str], None]
    ) -> None:
        self.t_refno_input = QLineEdit()
        self.t_refno_input.setObjectName("endorsement-refno-input")
        self.t_refno_input.setDisabled(True)

        # ------------------ Excess checkbox -----------------------
        self.has_excess_checkbox = QCheckBox("Has excess")
        self.has_excess_checkbox.setObjectName("endorsement-has-excess-checkbox")

        refno_container = QWidget()
        refno_layout = QVBoxLayout(refno_container)
        refno_layout.setContentsMargins(0, 0, 0, 0)
        refno_layout.setSpacing(5)

        refno_layout.addWidget(self.has_excess_checkbox)
        refno_layout.addWidget(self.t_refno_input)

        try:
            session = self.Session()
            reference_num = fetch_current_t_refno_in_endorsement(session, self.endorsement_t1)
            
            self.t_refno_input.setText(reference_num)
            create_input_row("Reference Number:", refno_container, "t_refno", "t_refno_error")   
        finally:
            session.close()
    
    def create_category_row(
        self, 
        create_input_row: Callable[[str, Union[QWidget, QLineEdit], str, str], None]
    ) -> None:
        self.t_category_input = ModifiedComboBox()
        
        for category in CategoryEnum:
            self.t_category_input.addItem(category.value, category)
        
        create_input_row("Category:", self.t_category_input, "t_category", "t_category_error")
    
    def create_prod_code_row(
        self, 
        create_input_row: Callable[[str, Union[QWidget, QLineEdit], str, str], None]
    ) -> None:
        self.t_prodcode_input = ModifiedComboBox()
        self.t_prodcode_input.addItems([
            "PlaceholderTest1",
            "PlaceholderTest2",
            "PlaceholderTest3"
        ])

        create_input_row("Product Code:", self.t_prodcode_input, "t_prodcode", "t_prodcode_error")
    
    def create_weight_per_lot_row(
        self, 
        create_input_row: Callable[[str, Union[QWidget, QLineEdit], str, str], None]
    ) -> None:
        self.t_wtlot_input = ModifiedDoubleSpinBox()
        self.t_wtlot_input.setMinimum(0.01) # Pydantic gt=0, so min here can be slightly above 0
        self.t_wtlot_input.setMaximum(999999999.99)
        self.t_wtlot_input.setDecimals(2)

        create_input_row("Weight per Lot:", self.t_wtlot_input, "t_wtlot", "t_wtlot_error")

    def create_qtykg_row(
        self, 
        create_input_row: Callable[[str, Union[QWidget, QLineEdit], str, str], None]
    ) -> None:
        self.t_qtykg_input = ModifiedDoubleSpinBox()
        self.t_qtykg_input.setObjectName("endorsement-t-qtykg-input-spinbox")
        self.t_qtykg_input.setMinimum(0.01) # Pydantic gt=0, so min here can be slightly above 0
        self.t_qtykg_input.setMaximum(999999999.99)
        self.t_qtykg_input.setDecimals(2)

        create_input_row("Quantity (kg):", self.t_qtykg_input, "t_qtykg", "t_qtykg_error")
    
    def create_bag_input_row(
        self,
        create_input_row: Callable[[str, Union[QWidget, QLineEdit], str, str], None]
    ) -> None:
        self.t_bag_num_input = QSpinBox()
        self.t_bag_num_input.setMinimum(0)
        self.t_bag_num_input.setMaximum(500)

        create_input_row("Bag number:", self.t_bag_num_input, "t_bag_num", "t_bag_num_error")

    def create_status_row(
        self, 
        create_input_row: Callable[[str, Union[QWidget, QLineEdit], str, str], None]
    ) -> None:
        self.t_status_input = ModifiedComboBox()
        self.t_status_input.setObjectName("endorsement-create-status-input")

        for status in StatusEnum:
            self.t_status_input.addItem(status.value, status)

        self.t_status_input.setCurrentText(StatusEnum.PASSED.value)

        #  ---------------------- disable the status so that the user cannot change the combox box value ---------------------
        self.t_status_input.setDisabled(True)
        create_input_row("Status:", self.t_status_input, "t_status", "t_status_error")

    def create_endorsed_by_input_row(
        self, 
        create_input_row: Callable[[str, Union[QWidget, QLineEdit], str, str], None]
    ) -> None:
        self.t_endorsed_by_input = ModifiedComboBox()
        session = self.Session()

        try:
            # fetch all the user by username
            users = session.query(self.user_model).all()

            for user  in users:
                displayed_user_text = mapped_user_to_display(user.username)

                self.t_endorsed_by_input.addItem(displayed_user_text)

            create_input_row("Endorsed By:", self.t_endorsed_by_input, "t_endorsed_by", "t_endorsed_by_error")
        finally:
            session.close()
    
    def create_remarks_input_row(
        self,
        create_input_row: Callable[[str, Union[QWidget, QLineEdit], str, str], None]
    ) -> None:
        self.t_remarks_by_input = ModifiedComboBox()
        
        for remark in RemarksEnum:
            self.t_remarks_by_input.addItem(remark.value, remark)

        create_input_row("Remarks:", self.t_remarks_by_input, "t_remarks", "t_remarks_error")

    def get_form_data(self) -> Dict[str, Union[str, int, bool, float, Any]]:
        """Collects data from UI widgets and returns it as a dictionary."""

        return {
            "t_refno": self.t_refno_input.text(),
            "t_date_endorsed": self.t_date_endorsed_input.date().toPyDate(),
            "t_category": self.t_category_input.currentData(), # Retrieves the stored Enum object
            "t_prodcode": self.t_prodcode_input.currentText(),
            "t_lotnumberwhole": self.t_lotnumberwhole_input.text(),
            "t_qtykg": self.t_qtykg_input.value(),
            "t_wtlot": self.t_wtlot_input.value(),
            "t_status": self.t_status_input.currentData(), # Retrieves the stored Enum object
            "t_endorsed_by": self.t_endorsed_by_input.currentText(),
            "t_has_excess": self.has_excess_checkbox.isChecked(),
            "t_bag_num": self.t_bag_num_input.value(),
            "t_remarks": self.t_remarks_by_input.currentText()
        }

    def clear_error_messages(self):
        """Clears all displayed error messages."""
        valid_instance = (
            QLineEdit,
            QComboBox,
            QDateEdit,
            # QDoubleSpinBox,
            ModifiedComboBox,
            ModifiedDateEdit,
            ModifiedDoubleSpinBox,
        )

        # CLEAR THE LOT NUMBER WHOLE STYLE SHEET
        self.t_lotnumberwhole_input.setStyleSheet("")

        for key in self.form_fields:
            if key.endswith("_error"):
                self.form_fields[key].setText("")
                # Optionally reset styling
                field_name = key.replace("_error", "")
                
                if field_name in self.form_fields and isinstance(self.form_fields[field_name], valid_instance):
                    self.form_fields[field_name].setStyleSheet("") # Clear any red borders etc.
                

    def display_errors(self, errors):
        """Displays validation errors next to the corresponding fields."""
        self.clear_error_messages()  # Clear previous errors first

        for error in errors:
            # ---------------- Handle both field-specific and model-level errors --------------------
            if error["loc"]:
                field = error["loc"][0]  # 'loc' is a tuple, first element is the field name
                message = error["msg"]
                
                error_label_key = f"{field}_error"
                
                if error_label_key in self.form_fields:
                    self.form_fields[error_label_key].setText(message)
                    
                    # ------------- Optionally, highlight the input field itself ----------------
                    input_widget = self.form_fields.get(field)
                    
                    if input_widget:
                        input_widget.setStyleSheet("border: 1px solid red;")
                else:
                    print(f"Warning: No error label found for field '{field}'. Error: {message}")
            else:
                # -------------- Model-level error - show it in a general way (e.g., in quantity field) -------------
                message = error["msg"]

                if "Quantity" in message:
                    self.show_quantity_error(message)
                elif "Lot range" in message or "overlaps with existing lot" in message:
                    # Display it next to the lot number field
                    error_label_key = "t_lotnumberwhole_error"

                    if error_label_key in self.form_fields:
                        self.form_fields[error_label_key].setText(message)
                        # self.t_lotnumberwhole_input.setStyleSheet("border: 1px solid red;")
                else:
                    # Fallback - show in status bar or as a message box
                    StyledMessageBox.warning(self, "Validation Error", message)
                    return

    def save_endorsement(self):
        """Collects form data, validates it using Pydantic, and handles the result."""
        self.clear_error_messages() # Clear all errors before re-validation
        
        form_data = self.get_form_data()
        
        try:
            # start the session here
            session = self.Session()

            # -------------------Validate the data using your Pydantic schema ---------------------
            # ---------- SET THE SESSION HERE IN FOR THE SCHEMA ------------
            # EndorsementFormSchema.set_db_session(session)

            # ---------- SET THE FORM SCHEMA VALIDATION HERE --------------
            # validated_data = EndorsementFormSchema(**form_data)
            validated_data = self.endorsement_form_schema.validate_with_session(
                form_data, 
                session,
                endorsement_model_t1=self.endorsement_t1,
                endorsement_model_t2=self.enodrsement_t2
            )

            # --------------------------------------------------------------------------
            # before passing the validated form in the endorsement model check first if the data is already existing on the database
            
            # NOTE: IS_LOT_EXISTING_T2 HANDLES THE PART IF THE LOT NUMBER WAS PREVIOUSLY ENTERED AS A WHOLE LOT NUMBER
            # is_lot_existing_in_t1 = session.query(EndorsementModel).filter(
            #     EndorsementModel.t_lotnumberwhole == validated_data.t_lotnumberwhole
            # ).first()

            is_lot_existing_t2 = session.query(self.enodrsement_t2).filter(
                self.enodrsement_t2.t_lotnumbersingle == validated_data.t_lotnumberwhole
            ).first()

            if is_lot_existing_t2:
                # TODO:
                # PROMPT THE USER THAT AN ITEM IS ALREADY EXISTING ON THE DATABASE
                # CREATE A MESSAGE BOX TELLING THE EXISTING DATA ON THE USER
                # CREATE A FUNCTION HERE THAT OMITS THE WHOLE ENTRY AND JUST UPDATE THE t_qtykg on the endorsement table 1
                # ADD A LOGIC FOR CHECKING THE LOT NUMBER INSIDE THE LOT NUMBER 2 AS WELL
                # CREATE A BAG NUMBER MODEL IN THE DATABASE (DONE)
                # FIX THE CODE LOGIC HERE
                
                # NOTE: HERE INSTEAD OF ITERATING A THE COLUMNS JUST MAKE A COPY OF THE VALIDATED DATA THEN CREATE THE MESSAGE BOX FROM THERE. 
                # JUST USE THE is_lot_existing_t2.endorsement_parent to specify the columns from endorsement_table_1
                details = {}
                for column in self.enodrsement_t2.__table__.columns:
                    key = column.name
                    
                    if key in (("t_refno", "t_lotnumbersingle", "t_qty")):
                        value = getattr(is_lot_existing_t2, key)
                        
                        details[key] = value
                
                # --------- UPDATE THE KEY NAMES HERE FOR USER TO SEE --------
                # NOTE: THAT IF THE COLUMNS BECOME BIG ITERATE THRU IT
                details["Reference No"] = details.pop("t_refno")
                details["Lot Number"] = details.pop("t_lotnumbersingle")
                details["Quantity"] = details.pop("t_qty") 

                # -------- UPDATE THE DATA HERE --------
                details.update({
                    "Weight Per Lot": is_lot_existing_t2.endorsement_parent.t_wtlot,
                    "Date Endorsed": is_lot_existing_t2.endorsement_parent.t_date_endorsed.isoformat(),
                    "Has Excess": is_lot_existing_t2.endorsement_parent.t_has_excess,
                    "Status": is_lot_existing_t2.endorsement_parent.t_status,
                    "Endorsed By": is_lot_existing_t2.endorsement_parent.t_endorsed_by
                })
                
                # ----------------- MODIFY THE DETAILS TO BE A JSON STRING FORMAT --------------
                details_str = json.dumps(details, indent=4, default=str)
                
                # --------------- TERMINAL PRINT -------------------
                TerminalCustomStylePrint.terminal_message_custom_format(
                    details_str
                )

                # --------------- MESSAGE BOX FOR LOT --------------
                lot_already_existing_reply = StyledMessageBox.question(
                    self,
                    "Lot number is already existing",
                    f"The following lot already exists in the database:\n\n{details_str}\n\n"
                    "Are you sure you want to continue?"
                )

                # make this into a method function in this class
                if ans_res == StyledMessageBox.StandardButton.Yes:
                    # TODO: if the prompt is yes. omit the lotnumber input of the user. And update the qty of the existing lot number
                    
                    # fetch the details variable here

                    # UPDATE THE VALUE HERE OF THE QTY IN THE MAIN ENDORSEMENT TABLE 1
                    # increment the value here
                    # is_lot_existing_in_t1.t_qtykg += validated_data.t_qtykg

                    # CREATE A NEW OBJECT ON THE ENDORSEMENT TABLE 2 WITH THAT DATA.
                    # NOTE: THAT THE ENDORSEMENT REFERENCE NUMBER SHOULD BE THE is_lot_existing_t1.ref_no
                    # SHOULD BE A SINGLE ENTRY 
                    # endorsement_t2 = EndorsementModelT2(
                        
                    # )
                    # insert_existing_lot_t2("test")

                    print("User clicked Yes")
                    
                    # remove the return statement here after
                    return
                elif lot_already_existing_reply == StyledMessageBox.StandardButton.No:
                    print("User clicked No")

                    # end the process immedietly here 
                    # NOTE: that if the user presses the x button on the question box it is interpreted as 'No' as well
                    return

            else:
                # if the lot is not existing just proceed as expected. 
                # and just proceed in including it in the database.
                print(False)

                # print(validated_data.model_dump_json(indent=2)) 
                # ------------- if the form is valid store this in the database. ---------------------
                endorsement = self.endorsement_t1(**validated_data.model_dump())
                    
                populate_endorsement_items(
                    endorsement_model=endorsement,
                    endorsement_model_t2=self.enodrsement_t2,
                    endorsement_lot_excess_model=self.endorsement_lot_excess,
                    validated_data=validated_data,
                    category=self.t_category_input.currentText(),
                    has_excess=self.has_excess_checkbox.isChecked()
                )

                session.add(endorsement)

            # --------------------------------------------------------------------------

            # ---------------- commit the changes if all transaction in the try block is valid ----------------
            session.commit()
        except ValueError as e:
            # self.form_fields["t_lotnumberwhole_error"].setText(str(e))
            # print(type(e))
            # print(len(e.errors()))
            # print(e.errors()[0]["msg"])
            error_message_instance = e.errors()[0]["msg"]

            self.form_fields["t_lotnumberwhole_error"].setText(error_message_instance)
            self.t_lotnumberwhole_input.setStyleSheet("border: 1px solid red;")
            session.rollback()
        except ValidationError as e:            
            self.display_errors(e.errors())
            
            StyledMessageBox.warning(
                self,
                "Validation Error",
                "Please correct the errors in the form"
            )
            session.rollback()
        except IntegrityError as e:
            StyledMessageBox.critical(
                self,
                "Error",
                f"Item is already existing on the database. Please add another item: {e}"
            ) 
            session.rollback()

        except Exception as e:
            StyledMessageBox.critical(
                self,
                "Error",
                f"An unexpected error occurred: {e}"
            )
            session.rollback()
        else:
            StyledMessageBox.information(
                self,
                "Success",
                "Endorsement form submitted successfully!"
            )

            # -------------- Optionally clear the form after successful submission -------------
            self.clear_form()
            
            # --------------- ALSO FETCH THE REF_NO AGAIN. To be displayed ----------------------
            reference_number = fetch_current_t_refno_in_endorsement(session, self.endorsement_t1)
            self.t_refno_input.setText(reference_number)
            self.refresh_table()
        finally:
            session.close()

    def clear_form(self):
        """Resets the input fields to their initial state."""
        # -------------- Clear reference number ---------------
        self.t_refno_input.clear()
        
        # --------------- Reset date to current date ----------------
        self.t_date_endorsed_input.setDate(QDate.currentDate())
        
        # --------------- Reset category -----------------
        self.t_category_input.setCurrentIndex(0)
        
        # ------------- Clear product code ----------------
        self.t_prodcode_input.clearEditText()
        
        # ------------ Properly clear lot number field -------------
        self.t_lotnumberwhole_input.clear()  # This will use our overridden clear()
        self.t_use_whole_lot_checkbox.setChecked(False)  # Reset checkbox
        
        # ------------ Reset quantity and weight ---------------
        self.t_qtykg_input.setValue(0.01)
        self.t_wtlot_input.setValue(0.01)
        
        # ------------ Reset status ------------------
        self.t_status_input.setCurrentText(StatusEnum.PASSED.value)
        self.t_status_input.setDisabled(True)
        
        # ---------- Clear endorsed by ----------
        self.t_endorsed_by_input.clearEditText()
        
        # ------------ Clear error messages ---------------
        self.clear_error_messages()

    def apply_styles(self):
        button_cursor_pointer(self.save_button)

        current_dir = os.path.dirname(__file__)
        qss_path = os.path.join(current_dir, "..", "styles", "endorsement.css")
        qss_path = os.path.abspath(qss_path)
        
        load_styles(qss_path, self)