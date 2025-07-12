from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QLineEdit, QDateEdit, QComboBox, QDoubleSpinBox, QPushButton,
    QCheckBox, QSizePolicy, QScrollArea,
    QStackedWidget, QSpinBox
)

from app.helpers import (
    fetch_current_t_refno_in_endorsement,
    populate_endorsement_items,
    button_cursor_pointer,
    load_styles
) 

from PyQt6.QtCore import QDate, Qt
from pydantic import ValidationError

from typing import Union, Callable, Type
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.StyledMessage import StyledMessageBox
from constants.Enums import StatusEnum, CategoryEnum, RemarksEnum
from constants.mapped_user import mapped_user_to_display

# MODELS
from models import (
    User,
    EndorsementModel,
    EndorsementModelT2,
    EndorsementLotExcessModel,
    EndorsementCombinedView
)

# CUSTOM WIDGET
from app.widgets import (
    LotNumberLineEdit,
    TableWidget,
    ModifiedComboBox,
    ModifiedDateEdit,
    ModifiedDoubleSpinBox
)

# ENDORSEMENT SCHEMA
from app.views.validatorSchema import EndorsementFormSchema

import os
import math

# --- ENDORSEMENT VIEW LOGIC IS HERE ---
class EndorsementCreateView(QWidget):
    """
    A form widget for creating and submitting product endorsements.

    This view provides a user interface for entering endorsement information including:
    - Reference number (auto-generated)
    - Date endorsed
    - Product category and code
    - Lot numbers (with support for whole/partial lot formats)
    - Quantity and weight measurements
    - Status selection
    - Endorsement approver selection

    The form includes validation, error display, and database persistence capabilities.

    Args:
        session_factory (Callable[..., Session]): A factory function that creates SQLAlchemy sessions
        parent (QWidget, optional): The parent widget. Defaults to None.

    Attributes:
        Session (Callable[..., Session]): Factory for creating database sessions
        form_fields (dict): Stores references to input widgets and their error labels
        main_layout (QVBoxLayout): The main layout container for the form

    Methods:
        init_ui(): Initializes the user interface components
        apply_styles(): Applies CSS styling to the widget
        create_input_horizontal_layout(): Creates a standardized input row with label, widget, and error display
        Various create_*_row() methods: Create specific form input rows
        get_form_data(): Collects and returns form data as a dictionary
        clear_error_messages(): Clears all validation error displays
        display_errors(): Shows validation errors next to the relevant fields
        save_endorsement(): Validates and saves the endorsement data
        clear_form(): Resets all form fields to their default state
    """
    
    def __init__(self, session_factory: Callable[..., Session], parent=None):
        """
        Initialize the endorsement form view.
        
        Args:
            session_factory: Factory function for creating SQLAlchemy sessions
            parent: Optional parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Endorsement Form")
        self.setObjectName("EndorsementForm")
        
        self.Session = session_factory
        self.table_widget = self.show_table()
       
        self.init_ui()
        self.apply_styles()

    def init_ui(self):
        # helper function in creating input rows
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
            label.setFixedWidth(150)  # Adjust as needed
            label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            # ---------- width of the widget field --------------
            widget.setFixedWidth(450)  # Set your desired field width
            
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
            db_model=EndorsementCombinedView, 
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
    ):
        # ------------------ self.t_date_endorsed_input = QDateEdit(calendarPopup=True) -------------------
        self.t_date_endorsed_input = ModifiedDateEdit(calendarPopup=True)
        self.t_date_endorsed_input.setDate(QDate.currentDate())
        self.t_date_endorsed_input.setObjectName("endorsement-date-endorsed-input")

        create_input_row("Date Endorsed:", self.t_date_endorsed_input, "t_date_endorsed", "t_date_endorsed_error")

    def create_t_refno_row(
        self, 
        create_input_row: Callable[[str, Union[QWidget, QLineEdit], str, str], None]
    ):
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
            reference_num = fetch_current_t_refno_in_endorsement(session, EndorsementModel)
            
            self.t_refno_input.setText(reference_num)
            create_input_row("Reference Number:", refno_container, "t_refno", "t_refno_error")   
        finally:
            session.close()
    
    def create_category_row(
        self, 
        create_input_row: Callable[[str, Union[QWidget, QLineEdit], str, str], None]
    ):
        self.t_category_input = ModifiedComboBox()
        
        for category in CategoryEnum:
            self.t_category_input.addItem(category.value, category)
        
        create_input_row("Category:", self.t_category_input, "t_category", "t_category_error")
    
    def create_prod_code_row(
        self, 
        create_input_row: Callable[[str, Union[QWidget, QLineEdit], str, str], None]
    ):
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
    ):
        self.t_wtlot_input = ModifiedDoubleSpinBox()
        self.t_wtlot_input.setMinimum(0.01) # Pydantic gt=0, so min here can be slightly above 0
        self.t_wtlot_input.setMaximum(999999999.99)
        self.t_wtlot_input.setDecimals(2)

        create_input_row("Weight per Lot:", self.t_wtlot_input, "t_wtlot", "t_wtlot_error")

    def create_qtykg_row(
        self, 
        create_input_row: Callable[[str, Union[QWidget, QLineEdit], str, str], None]
    ):
        self.t_qtykg_input = ModifiedDoubleSpinBox()
        self.t_qtykg_input.setObjectName("endorsement-t-qtykg-input-spinbox")
        self.t_qtykg_input.setMinimum(0.01) # Pydantic gt=0, so min here can be slightly above 0
        self.t_qtykg_input.setMaximum(999999999.99)
        self.t_qtykg_input.setDecimals(2)

        create_input_row("Quantity (kg):", self.t_qtykg_input, "t_qtykg", "t_qtykg_error")
    
    def create_bag_input_row(
        self,
        create_input_row: Callable[[str, Union[QWidget, QLineEdit], str, str], None]
    ):
        self.t_bag_num_input = QSpinBox()
        self.t_bag_num_input.setMinimum(0)
        self.t_bag_num_input.setMaximum(500)

        create_input_row("Bag number:", self.t_bag_num_input, "t_bag_num", "t_bag_num_error")

    def create_status_row(
        self, 
        create_input_row: Callable[[str, Union[QWidget, QLineEdit], str, str], None]
    ):
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
    ):
        self.t_endorsed_by_input = ModifiedComboBox()
        
        session = self.Session()

        try:
            # fetch all the user by username
            users = session.query(User).all()

            for user  in users:
                displayed_user_text = mapped_user_to_display(user.username)

                self.t_endorsed_by_input.addItem(displayed_user_text)

            create_input_row("Endorsed By:", self.t_endorsed_by_input, "t_endorsed_by", "t_endorsed_by_error")
        finally:
            session.close()
    
    def create_remarks_input_row(
        self,
        create_input_row: Callable[[str, Union[QWidget, QLineEdit], str, str], None]
    ):
        self.t_remarks_by_input = ModifiedComboBox()
        
        for remark in RemarksEnum:
            self.t_remarks_by_input.addItem(remark.value, remark)

        create_input_row("Remarks:", self.t_remarks_by_input, "t_remarks", "t_remarks_error")

    def get_form_data(self):
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
            "t_bag_num": self.t_bag_num_input.value()
        }

    def clear_error_messages(self):
        """Clears all displayed error messages."""
        valid_instance = (
            QLineEdit,
            QComboBox,
            QDateEdit,
            QDoubleSpinBox,
            ModifiedComboBox,
            ModifiedDateEdit,
            ModifiedDoubleSpinBox,
        )

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
                else:
                    # Fallback - show in status bar or as a message box
                    StyledMessageBox.warning(self, "Validation Error", message)

    def save_endorsement(self):
        """Collects form data, validates it using Pydantic, and handles the result."""
        self.clear_error_messages() # Clear all errors before re-validation
        
        form_data = self.get_form_data()
        
        try:
            # start the session here
            session = self.Session()

            # -------------------Validate the data using your Pydantic schema ---------------------
            validated_data = EndorsementFormSchema(**form_data)
            
            # --------------------------------------------------------------------------
            # before passing the validated form in the endorsement model check first if the data is already existing on the database
            
            is_lot_existing = session.query(EndorsementModel).filter(
                EndorsementModel.t_lotnumberwhole == validated_data.t_lotnumberwhole
            ).first()

            if is_lot_existing:
                print(True)
                # prompt the user that an item is already existing on the database.
                # enforce the user to just only change weight per lot 

                # TODO: 
                # CREATE A MESSAGE BOX TELLING THE EXISTING DATA ON THE USER
                # CREATE A FUNCTION HERE THAT OMITS THE WHOLE ENTRY AND JUST UPDATE THE t_qtykg on the endorsement table 1
                # CREATE A BAG NUMBER MODEL IN THE DATABASE
                
            else:
                print(False)


        
            # --------------------------------------------------------------------------

            # print(validated_data.model_dump_json(indent=2)) 
            # ------------- if the form is valid store this in the database. ---------------------
            endorsement = EndorsementModel(**validated_data.model_dump())
                
            populate_endorsement_items(
                endorsement_model=endorsement,
                endorsement_model_t2=EndorsementModelT2,
                endorsement_lot_excess_model=EndorsementLotExcessModel,
                validated_data=validated_data,
                category=self.t_category_input.currentText(),
                has_excess=self.has_excess_checkbox.isChecked()
            )

            session.add(endorsement)
            
            # ---------------- commit the changes if all transaction in the try block is valid ----------------
            session.commit()
        except ValidationError as e:            
            self.display_errors(e.errors())
            
            StyledMessageBox.warning(
                self,
                "Validation Error",
                "Please correct the errors in the form"
            )
        except IntegrityError as e:
            StyledMessageBox.critical(
                self,
                "Error",
                f"Item is already existing on the database. Please add another item: {e}"
            ) 

        except Exception as e:
            StyledMessageBox.critical(
                self,
                "Error",
                f"An unexpected error occurred: {e}"
            )
        else:
            StyledMessageBox.information(
                self,
                "Success",
                "Endorsement form submitted successfully!"
            )

            # Optionally clear the form after successful submission
            self.clear_form()
            
            # ALSO FETCH THE REF_NO AGAIN. TO be displayed
            reference_number = fetch_current_t_refno_in_endorsement(session, EndorsementModel)
            self.t_refno_input.setText(reference_number)
            self.refresh_table()
        finally:
            session.close()

    def show_lot_exists_warning(self):
        pass

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
        qss_style = os.path.join(os.path.dirname(__file__), "styles", "endorsement.css")
        button_cursor_pointer(self.save_button)
        
        load_styles(qss_style, self)
class EndorsementListView(QWidget):
    """View with filters and table"""
    def __init__(self, session_factory: Callable[..., Session], parent=None):
        super().__init__(parent)
        self.Session = session_factory
        self.setup_ui()
        self.apply_styles()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        top_filter_layout, bottom_filter_layout = self.create_filter_layout()
        self.table = self.show_table()

        # ------------- Add all to main layout ----------------
        layout.addLayout(top_filter_layout)
        layout.addLayout(bottom_filter_layout)
        layout.addWidget(self.table)
        layout.setStretch(2, 1)

        self.create_category_menu()
        self.setLayout(layout)

        # connect the button to filter function
        self.search_button.clicked.connect(self.filter_function)
        self.list_reset_btn.clicked.connect(self.list_reset_callback)
        
        # Connect returnPressed signals for quick filtering
        self.ref_no_input.returnPressed.connect(self.filter_function)
        self.prod_code_input.returnPressed.connect(self.filter_function)

    def apply_styles(self):
        qss_path = os.path.join(os.path.dirname(__file__), "styles", "endorsement_list.css")

        load_styles(qss_path, self)
    
    def show_table(self):
        table = TableWidget(
            session_factory=self.Session,
            db_model=EndorsementCombinedView,
            view_type="endorsement-list"
        )
        table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        return table

    def create_category_menu(self):
        for category in CategoryEnum:
            self.category_filter.addItem(category.value, category)
        
        # add a ALL filter in the category enum
        self.category_filter.addItem("ALL")
        self.category_filter.setCurrentText("ALL")

    def create_filter_layout(self):
        def create_filter_group(label, widget):
            group = QWidget()
            layout = QVBoxLayout(group)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(2)
            layout.addWidget(label)
            layout.addWidget(widget)
            
            return group
        # ------------- FILTERS ----------------
        self.category_filter = ModifiedComboBox()
        self.status_filter = ModifiedComboBox()
        self.prod_code_input = QLineEdit()
        self.ref_no_input = QLineEdit()

        self.prod_code_input.setPlaceholderText("Filter by production code")
        self.ref_no_input.setPlaceholderText("Filter by reference number")

        # ------------ RESET BTN ----------------
        self.list_reset_btn = QPushButton("Reset")
        self.list_reset_btn.setObjectName("endorsementList-reset-btn")

        # --------------- LABELS FOR THE FILTERS ---------------------
        category_label = QLabel("Category:")
        status_label = QLabel("Status:")
        prod_code_label = QLabel("Prod Code:")
        ref_no_label = QLabel("Ref No:")
        from_label = QLabel("From:")
        to_label = QLabel("To:")

        # --------------- DATES ---------------------
        self.date_from = ModifiedDateEdit(calendarPopup=True)
        self.date_to = ModifiedDateEdit(calendarPopup=True)
        self.date_to.setDate(QDate.currentDate())

        # --------------- QPushButton -------------------
        self.search_button = QPushButton("Search")
        self.search_button.setObjectName("endorsementList-search-btn")

        # --- Top row filter layout ---
        top_filter_layout = QHBoxLayout()
        top_filter_layout.setContentsMargins(0, 0, 0, 0)
        top_filter_layout.setSpacing(6)

        # --- Bottom row filter layout ---
        bottom_filter_layout = QHBoxLayout()
        bottom_filter_layout.setContentsMargins(0, 0, 0, 0)
        bottom_filter_layout.setSpacing(6)
        
        # --------------- SIZE POLICY --------------------
        category_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        status_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        prod_code_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        ref_no_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        from_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        to_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        # --- Top row add widget ---
        top_filter_layout.addWidget(create_filter_group(category_label, self.category_filter), stretch=1)
        top_filter_layout.addWidget(create_filter_group(status_label, self.status_filter), stretch=1)
        top_filter_layout.addWidget(create_filter_group(prod_code_label, self.prod_code_input), stretch=1)
        top_filter_layout.addWidget(create_filter_group(ref_no_label, self.ref_no_input), stretch=1)

        # --- Bottom row filter layout ---
        bottom_filter_layout.addWidget(from_label)
        bottom_filter_layout.addWidget(self.date_from)
        bottom_filter_layout.addWidget(to_label)
        bottom_filter_layout.addWidget(self.date_to)
        bottom_filter_layout.addStretch() # push the search button to the right
        bottom_filter_layout.addWidget(self.list_reset_btn)
        bottom_filter_layout.addWidget(self.search_button)

        return (
            top_filter_layout, 
            bottom_filter_layout
        )
    
    def filter_function(self):
        session = self.Session()

        try:
            ref_no_filter = self.ref_no_input.text().strip()
            prod_code_filter = self.prod_code_input.text().strip()

            query = session.query(EndorsementCombinedView)

            if ref_no_filter:
                query = query.filter(EndorsementCombinedView.t_refno.ilike(f"%{ref_no_filter}%"))
            
            if prod_code_filter:
                query = query.filter(EndorsementCombinedView.t_prodcode.ilike(f"%{prod_code_filter}%"))

            if self.date_from.date() <= self.date_to.date():
                query = query.filter(
                    EndorsementCombinedView.t_date_endorsed >= self.date_from.date().toPyDate(),
                    EndorsementCombinedView.t_date_endorsed <= self.date_to.date().toPyDate()
                )
            
            if self.category_filter.currentText() != "ALL":
                selected_category = self.category_filter.currentData()

                if selected_category:  # Ensure we have valid category data
                    query = query.filter(EndorsementCombinedView.t_category == selected_category.value)
            
            results = query.order_by(EndorsementCombinedView.t_date_endorsed.desc()).all()

            self.table.update_table_with_results(results, apply_pagination=True)
        finally:
            session.close()

    def list_reset_callback(self):
        filter_objects = (
            self.prod_code_input,
            self.ref_no_input
        )
        
        for input_widget in filter_objects:
            if isinstance(input_widget, QLineEdit):
                input_widget.clear()
             
        self.table.load_data()

class EndorsementMainView(QWidget):
    def __init__(self, session_factory: Callable[..., Session], parent=None):
        super().__init__(parent)
        self.Session = session_factory
        self.setup_ui()
        self.apply_styles()
        
    def setup_ui(self):
        self.layout = QVBoxLayout()

        # ----------------- Navigation buttons ---------------------
        nav_layout = QHBoxLayout()
        self.create_btn = QPushButton("Create New")
        self.list_btn = QPushButton("View List")
        self.how_to_use_btn = QPushButton("How To Use")
        
        self.create_btn.setObjectName("endorsement-create-btn")
        self.list_btn.setObjectName("endorsement-list-btn")
        self.how_to_use_btn.setObjectName("endorsement-how-to-use-btn")
        
        nav_layout.addWidget(self.create_btn)
        nav_layout.addWidget(self.list_btn)
        nav_layout.addWidget(self.how_to_use_btn)
        nav_layout.addStretch()
        
        # ---------------- Stacked widget for views ---------------------
        self.stacked_widget = QStackedWidget()
        
        # --------------- Create views -----------------------
        self.create_view = EndorsementCreateView(self.Session)
        self.list_view = EndorsementListView(self.Session)
        self.how_to_use_view = HowToUseView()
        
        # ---------------- Add to stack --------------------
        self.stacked_widget.addWidget(self.create_view)
        self.stacked_widget.addWidget(self.list_view)
        self.stacked_widget.addWidget(self.how_to_use_view)

        # --------------------- Connect signals -----------------------
        self.create_btn.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.create_view))
        self.list_btn.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.list_view))
        self.how_to_use_btn.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.how_to_use_view))
        
        # ----------------------- When a record is selected in list view for editing -------------------------------
        # self.list_view.table.double_clicked.connect(self.show_update_view)
        
        self.layout.addLayout(nav_layout)
        self.layout.addWidget(self.stacked_widget)
        self.setLayout(self.layout)
    
    def apply_styles(self):
        qss_path = os.path.join(os.path.dirname(__file__), "styles", "crud_btn.css")
        
        load_styles(qss_path, self)

    def show_update_view(self, ref_no):
        """Load data for editing and switch to update view"""
        try:
            session = self.Session()
            record = session.query(EndorsementModel).filter_by(t_refno=ref_no).first()

            if record:
                # Populate the update form with record data
                self.update_view.form.load_data(record)
                self.stacked_widget.setCurrentWidget(self.update_view)
        finally:
            session.close()


# HOW TO USE VIEW
class HowToUseView(QWidget):
    """Interactive guide for using the endorsement system"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):
        # Main layout with scroll area
        main_layout = QVBoxLayout(self)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        # Content container
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel("Endorsement System Guide")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        # Sections
        self.add_section(
            layout,
            "Creating New Endorsements",
            "1. Fill all required fields\n"
            "2. Use proper lot number format (e.g., 1234AB or 1234AB-5678CD)\n"
            "3. Check 'Has excess' for partial quantities\n"
            "4. Click 'Save Endorsement' to submit"
        )

        self.add_section(
            layout,
            "Viewing Existing Records",
            "• Use filters to find specific endorsements\n"
            "• Double-click any record to view details\n"
            "• Sort columns by clicking headers"
        )

        self.add_section(
            layout,
            "Common Validation Rules",
            "• Quantity must match whole lot multiples unless 'Has excess' is checked\n"
            "• Lot numbers must follow the pattern: 4 digits + 2 letters\n"
            "• Reference numbers are auto-generated"
        )

        self.add_video_section(layout)
        self.add_contact_section(layout)

        scroll_area.setWidget(content)
        main_layout.addWidget(scroll_area)

    def add_section(self, layout, title, content):
        """Adds a titled content section"""
        section_title = QLabel(title)
        section_title.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 10px;")
        
        content_label = QLabel(content)
        content_label.setWordWrap(True)
        content_label.setStyleSheet("margin-left: 10px;")
        
        layout.addWidget(section_title)
        layout.addWidget(content_label)

    def add_video_section(self, layout):
        """Adds video tutorial placeholder"""
        section = QWidget()
        section_layout = QVBoxLayout(section)
        
        title = QLabel("Video Tutorials")
        title.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 10px;")
        
        video_links = [
            ("Basic Endorsement", "https://example.com/video1"),
            ("Troubleshooting", "https://example.com/video2"),
            ("Advanced Features", "https://example.com/video3")
        ]
        
        for text, url in video_links:
            btn = QPushButton(f"▶ {text}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("text-align: left; color: #0066cc;")
            btn.clicked.connect(lambda _, u=url: self.open_url(u))
            section_layout.addWidget(btn)
        
        layout.addWidget(title)
        layout.addWidget(section)

    def add_contact_section(self, layout):
        """Adds support contact information"""
        section = QWidget()
        section_layout = QVBoxLayout(section)
        
        title = QLabel("Need Help?")
        title.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 10px;")
        
        contacts = [
            ("IT Support:", "support@masterbatch.com", "mailto:support@example.com"),
            ("QC Department:", "qc@masterbatch.com", "mailto:qc@example.com"),
            ("Urgent Issues:", "Ext. 1234", "")
        ]
        
        for label, text, link in contacts:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(10, 0, 0, 0)
            
            lbl = QLabel(label)
            lbl.setFixedWidth(100)
            
            if link:
                btn = QPushButton(text)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setStyleSheet("text-align: left; color: #0066cc; border: none;")
                btn.clicked.connect(lambda _, u=link: self.open_url(u))
                row_layout.addWidget(lbl)
                row_layout.addWidget(btn)
            else:
                txt = QLabel(text)
                row_layout.addWidget(lbl)
                row_layout.addWidget(txt)
            
            section_layout.addWidget(row)
        
        layout.addWidget(title)
        layout.addWidget(section)

    def open_url(self, url):
        """Handles opening external links"""
        import webbrowser
        webbrowser.open(url)

    def apply_styles(self):
        qss_path = os.path.join(os.path.dirname(__file__), "styles", "how_to_use_view.css")
        load_styles(qss_path, self)