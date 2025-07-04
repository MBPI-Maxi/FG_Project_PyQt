from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QLineEdit, QDateEdit, QComboBox, QDoubleSpinBox, QPushButton,
    QCheckBox, QScrollArea, QTableWidget, QTableWidgetItem, QSplitter, QHeaderView, QSizePolicy,
    QStackedWidget, QMenu, QFileDialog
)
from app.helpers import (
    fetch_current_t_refno_in_endorsement,
    generate_endorsement_table_2,
    button_cursor_pointer
) 

from PyQt6.QtCore import QDate, Qt, pyqtSignal
from pydantic import BaseModel, Field, ValidationError, field_validator

from datetime import date
from typing import Union, overload, Callable, List
from sqlalchemy.orm import Session

from constants.Enums import StatusEnum, CategoryEnum
from app.StyledMessage import StyledMessageBox
from constants.mapped_user import mapped_user_to_display

# models
from models import User, EndorsementModel, EndorsementModelT2

# custom widgets
from app.widgets.lineedits import LotNumberLineEdit
import os
import re
import pandas as pd


# --- FORM SCHEMA IS CREATED HERE FOR SERIALIZATION AND VALIDATION ---
class EndorsementFormSchema(BaseModel):
    """
    Schema for validating Endorsement Form input using Pydantic.

    Fields map directly to SQLAlchemy model attributes and ensure
    consistent input structure and data integrity before database operations.
    """
    
    # Map directly to your SQLAlchemy model fields (should match the data)
    t_refno: str = Field(
        ...,  # meaning required field to be fill up
        min_length=1, 
        max_length=255, 
        description="Reference Number"
    )
    t_date_endorsed: date = Field(
        ..., 
        description="Date Endorsed"
    )
    t_category: CategoryEnum = Field(
        default=CategoryEnum.MB, 
        description="Category of Endorsement"
    )
    t_prodcode: str = Field(
        ..., 
        min_length=1, 
        max_length=255, 
        description="Product Code"
    )
    t_lotnumberwhole: str = Field(
        ..., 
        min_length=1, 
        max_length=255, 
        description="Whole Lot Number"
    )
    t_qtykg: float = Field(
        ..., 
        gt=0, 
        description="Quantity in Kilograms"
    ) # gt=0 ensures it's greater than 0
    t_wtlot: float = Field(
        ..., 
        gt=0, 
        description="Weight per Lot"
    ) # gt=0 ensures it's greater than 0
    t_status: StatusEnum = Field(
        default=StatusEnum.PASSED, 
        description="Status of Endorsement"
    )
    t_endorsed_by: str = Field(
        ..., 
        min_length=1, 
        max_length=255, 
        description="Endorsed By"
    )

    class Config:
        # Ensures that Pydantic works correctly with Enum values
        use_enum_values = True 

    ### VALIDATORS ###
    #####################################################################

    @field_validator("t_refno")
    @classmethod
    def validate_refno_format(cls, value):
        if not value.startswith("EF-"):
            raise ValueError("Reference number must start with 'EF-'")
        
        return value
    
    @field_validator("t_prodcode")
    @classmethod
    def validate_prodcode_format(cls, value):
        valid_length_for_prod = 16
        if not len(value) >= valid_length_for_prod:
            raise ValueError("Production code must be GTE 16")
        return value
    
    @field_validator("t_lotnumberwhole")
    @classmethod
    def validate_lot_number(cls, value):
        alphabet_list = list("abcdefghijklmnopqrstuvwxyz")

        single_lot_pattern = r"^\d{4}[A-Z]{2}$"
        range_lot_pattern = r"^\d{4}[A-Z]{2}-\d{4}[A-Z]{2}$"

        if re.match(single_lot_pattern, value):
            return value

        elif re.match(range_lot_pattern, value):
            start, end = value.split("-")
            first_num, first_code = start[:4], start[-2:]
            second_num, second_code = end[:4], end[-2:]

            first_int = int(first_num)
            second_int = int(second_num)

            fl1 = alphabet_list.index(first_code[0].lower())
            fl2 = alphabet_list.index(first_code[1].lower())
            sl1 = alphabet_list.index(second_code[0].lower())
            sl2 = alphabet_list.index(second_code[1].lower())

            first_code_index = fl1 * 26 + fl2
            second_code_index = sl1 * 26 + sl2

            # Validate number order
            if first_int > second_int and not (first_int == 9999 and second_int == 1):
                raise ValueError("Starting lot must be less than or equal to ending lot.")

            # Validate letter code order always
            if second_code_index < first_code_index:
                raise ValueError("Ending letter code is invalid. Please check carefully.")

            # Special case: rollover
            if first_int == 9999:
                if second_int != 1:
                    raise ValueError("After 9999, lot number must reset to 0001.")
                if second_code_index <= first_code_index:
                    raise ValueError("Letter code must increment after 9999 lot reset.")

            return value
        else:
            raise ValueError("Lot number format must be '1234AB' or '1234AB-1235AB'")
    ###################################################################

# --- ENDORSEMENT VIEW LOGIC IS HERE ---
class EndorsementView(QWidget):
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
        # created a table widget (now seperate component)
        self.table_widget = EndorsementTableWidget(
            session_factory=session_factory, 
            parent=self,
            view_type="endorsement-create"
        )
        
        self.init_ui()
        self.apply_styles()
    
    @overload
    def create_input_horizontal_layout(
        self,
        label_text: str,
        widget: QWidget,
        field_name: str,
        error_label_name: str
    ) -> None: 
        ...
    
    @overload
    def create_input_horizontal_layout(
        self,
        label_text: str,
        widget: QLineEdit,
        field_name: str,
        error_label_name: str
    ) -> None:
        ...

    def init_ui(self):
        self.main_layout = QVBoxLayout()
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Dictionary to store references to input widgets and error labels
        self.form_fields = {} 

        # Helper function to create a labeled input field
        def create_input_row(label_text, widget, field_name, error_label_name):
            h_layout = QHBoxLayout()
            h_layout.setContentsMargins(0, 0, 0, 0)
            h_layout.setSpacing(0)

            label = QLabel(label_text)
            label.setFixedWidth(200) # Or whatever consistent width
            
            h_layout.addWidget(label) 
            h_layout.addWidget(widget)
            
            widget.setFixedWidth(400) # <-- consistent width here

            error_label = QLabel()
            error_label.setStyleSheet("""
                color: red;
                font-size: 12px;
                font-style: italic;
                margin-left: 5px;
            """)
            
            error_label.setObjectName(f"{field_name}_error_label")
            h_layout.addWidget(error_label)
            
            self.form_fields[field_name] = widget
            self.form_fields[error_label_name] = error_label
            
            self.main_layout.addLayout(h_layout)
        
        # 1. Reference Number
        self.create_t_refno_row(create_input_row)
    
        # 2. Date Endorsed
        self.create_date_endorsed_row(create_input_row)
        # 3. Category
        self.create_category_row(create_input_row)
        # 4. Product Code
        self.create_prod_code_row(create_input_row)
        # 5. Whole Lot Number
        self.create_lot_number_row(create_input_row)
        # 6. Quantity (kg)
        self.create_qtykg_row(create_input_row)
        # 7. Weight per Lot
        self.create_weight_per_lot_row(create_input_row)
        # 8. Status
        self.create_status_row(create_input_row)
        # 9. Endorsed By
        self.create_endorsed_by_input_row(create_input_row)
        # Spacer to push elements to the top
        self.main_layout.addStretch(1)

        # Save Button
        self.save_button = QPushButton("Save Endorsement")
        self.save_button.setObjectName("endorsement-save-btn")
        self.save_button.clicked.connect(self.save_endorsement)
        
        self.main_layout.addWidget(self.save_button)

        # form table
        splitter = QSplitter(Qt.Orientation.Vertical)
        form_container = QWidget()
        form_container.setLayout(self.main_layout)
        splitter.addWidget(form_container)
        splitter.addWidget(self.table_widget)


        self.main_layout.setSpacing(12)
        container_layout = QVBoxLayout(self)
        container_layout.addWidget(splitter)
        self.setLayout(container_layout)
    
    def refresh_table(self):
        """Refresh table data."""
        # self.table_widget.load_data()
        try:
            # Store current scroll position
            scroll_pos = self.table_widget.table.verticalScrollBar().value()
            
            self.table_widget.load_data()
            
            # Maintain UI state
            self.table_widget.table.verticalScrollBar().setValue(scroll_pos)
            self.table_widget.table.resizeColumnsToContents()
            
            # Set specific column widths if needed
            self.table_widget.table.setColumnWidth(0, 120)  # Ref No
            self.table_widget.table.setColumnWidth(1, 100)  # Date
            # ... other columns ...
            
            # Ensure last column stretches
            self.table_widget.table.horizontalHeader().setStretchLastSection(True)
        
        except Exception as e:
            print(f"Error refreshing table: {e}")
        
    def create_input_horizontal_layout(
        self, 
        label_text: str, 
        widget: Union[QWidget, QLineEdit], 
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
    
    # for lot number row
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

        # default
        self.t_lotnumberwhole_input.setInputMask("0000AA; ")
        self.t_lotnumberwhole_input.setPlaceholderText("e.g.1234AB or 1234AB-5678CD")

        # add the layout to make them inline
        lot_inline_layout = QHBoxLayout()
        lot_inline_layout.setContentsMargins(0, 0, 0, 0)
        lot_inline_layout.setSpacing(15)
        lot_inline_layout.addWidget(self.t_lotnumberwhole_input)
        lot_inline_layout.addWidget(self.t_use_whole_lot_checkbox)

        # wrapping the whole lot number in one widget
        lot_input_widget = QWidget()
        lot_input_widget.setLayout(lot_inline_layout)

        # return lot_input_widget
        create_input_row("Whole Lot Number", lot_input_widget, "t_lotnumberwhole", "t_lotnumberwhole_error")
    
    def create_date_endorsed_row(
        self, 
        create_input_row: Callable[[str, Union[QWidget, QLineEdit], str, str], None]
    ):
        self.t_date_endorsed_input = QDateEdit(calendarPopup=True)
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

        # Excess checkbox
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
        self.t_category_input = QComboBox()
        
        for category in CategoryEnum:
            self.t_category_input.addItem(category.value, category)
        
        create_input_row("Category:", self.t_category_input, "t_category", "t_category_error")
    
    def create_prod_code_row(
        self, 
        create_input_row: Callable[[str, Union[QWidget, QLineEdit], str, str], None]
    ):
        self.t_prodcode_input = QComboBox()
        self.t_prodcode_input.addItems([
            "Placeholder12345",
            "Placeholder12345",
            "Placeholder12345"
        ])

        create_input_row("Product Code:", self.t_prodcode_input, "t_prodcode", "t_prodcode_error")
    
    def create_qtykg_row(
        self, 
        create_input_row: Callable[[str, Union[QWidget, QLineEdit], str, str], None]
    ):
        self.t_qtykg_input = QDoubleSpinBox()
        self.t_qtykg_input.setObjectName("endorsement-t-qtykg-input-spinbox")
        self.t_qtykg_input.setMinimum(0.01) # Pydantic gt=0, so min here can be slightly above 0
        self.t_qtykg_input.setMaximum(999999999.99)
        self.t_qtykg_input.setDecimals(2)

        create_input_row("Quantity (kg):", self.t_qtykg_input, "t_qtykg", "t_qtykg_error")
            
    def create_weight_per_lot_row(
        self, 
        create_input_row: Callable[[str, Union[QWidget, QLineEdit], str, str], None]
    ):
        self.t_wtlot_input = QDoubleSpinBox()
        self.t_wtlot_input.setMinimum(0.01) # Pydantic gt=0, so min here can be slightly above 0
        self.t_wtlot_input.setMaximum(999999999.99)
        self.t_wtlot_input.setDecimals(2)

        create_input_row("Weight per Lot:", self.t_wtlot_input, "t_wtlot", "t_wtlot_error")

    def create_status_row(
        self, 
        create_input_row: Callable[[str, Union[QWidget, QLineEdit], str, str], None]
    ):
        self.t_status_input = QComboBox()

        for status in StatusEnum:
            self.t_status_input.addItem(status.value, status)

        self.t_status_input.setCurrentText(StatusEnum.PASSED.value)
        create_input_row("Status:", self.t_status_input, "t_status", "t_status_error")

    def create_endorsed_by_input_row(
        self, 
        create_input_row: Callable[[str, Union[QWidget, QLineEdit], str, str], None]
    ):
        self.t_endorsed_by_input = QComboBox()
        
        # create the session here now
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
        }

    def clear_error_messages(self):
        """Clears all displayed error messages."""
        for key in self.form_fields:
            if key.endswith("_error"):
                self.form_fields[key].setText("")
                # Optionally reset styling
                field_name = key.replace("_error", "")
                
                if field_name in self.form_fields and isinstance(self.form_fields[field_name], (QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox)):
                    self.form_fields[field_name].setStyleSheet("") # Clear any red borders etc.

    def display_errors(self, errors):
        """Displays validation errors next to the corresponding fields."""
        self.clear_error_messages() # Clear previous errors first

        for error in errors:
            field = error['loc'][0] # 'loc' is a tuple, first element is the field name
            message = error['msg']
            
            error_label_key = f"{field}_error"
            
            if error_label_key in self.form_fields:
                self.form_fields[error_label_key].setText(message)
                
                # Optionally, highlight the input field itself
                input_widget = self.form_fields.get(field)
                
                if input_widget:
                    input_widget.setStyleSheet("border: 1px solid red;")
            else:
                print(f"Warning: No error label found for field '{field}'. Error: {message}")

    def save_endorsement(self):
        """Collects form data, validates it using Pydantic, and handles the result."""
        self.clear_error_messages() # Clear all errors before re-validation
        
        form_data = self.get_form_data()
        
        try:
            # start the session here
            session = self.Session()

            # Validate the data using your Pydantic schema
            validated_data = EndorsementFormSchema(**form_data)

            # If validation passes:
            # At this point, you would typically pass `validated_data.dict()`
            # to your SQLAlchemy model for database insertion/update.
            # For this example, we'll just print it.
            # print("Form data is valid!")
            # print(validated_data.model_dump_json(indent=2)) # Use model_dump_json for Pydantic v2+

            # if the form is valid store this in the database.
            endorsement = EndorsementModel(**validated_data.model_dump())
                
            # if the endorsement is correct store the data to the endorsement table 2 data.
            generate_endorsement_table_2(
                endorsement,
                EndorsementModelT2, 
                validated_data
            )
            
            session.add(endorsement) 
        except ValidationError as e:
            # Handle validation errors
            print("Validation Errors: {}".format(e))
            
            self.display_errors(e.errors())
            
            # QMessageBox.warning(self, "Validation Error", "Please correct the errors in the form.")
            StyledMessageBox.warning(
                self,
                "Validation Error",
                "Please correct the errors in the form"
            )
        except Exception as e:
            StyledMessageBox.critical(
                self,
                "Error",
                f"An unexpected error occurred: {e}"
            )
        else:
            # commit the changes if all transaction in the try block is valid
            session.commit()

            # QMessageBox.information(self, "Success", "Endorsement form submitted successfully!")
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
 
    def clear_form(self):
        """Resets the input fields to their initial state."""
        # Clear reference number
        self.t_refno_input.clear()
        
        # Reset date to current date
        self.t_date_endorsed_input.setDate(QDate.currentDate())
        
        # Reset category
        self.t_category_input.setCurrentIndex(0)
        
        # Clear product code
        self.t_prodcode_input.clearEditText()
        
        # Properly clear lot number field
        self.t_lotnumberwhole_input.clear()  # This will use our overridden clear()
        self.t_use_whole_lot_checkbox.setChecked(False)  # Reset checkbox
        
        # Reset quantity and weight
        self.t_qtykg_input.setValue(0.01)
        self.t_wtlot_input.setValue(0.01)
        
        # Reset status
        self.t_status_input.setCurrentText(StatusEnum.PASSED.value)
        
        # Clear endorsed by
        self.t_endorsed_by_input.clearEditText()
        
        # Clear error messages
        self.clear_error_messages()

    def apply_styles(self):
        qss_style = os.path.join(os.path.dirname(__file__), "styles", "endorsement.css")
        button_cursor_pointer(self.save_button)
        
        try:
            with open(qss_style, "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print("Warning: Style file not found. Default styles will be used.")

class EndorsementTableWidget(QWidget):
    """Reusable table widget for displaying endorsement records across multiple views."""
    # Custom signal
    double_clicked = pyqtSignal(str)

    def __init__(
        self, 
        session_factory: Callable[..., Session],
        view_type: Union[str, None]=None,
        parent=None
    ):
        super().__init__(parent)
        valid_views = [
            "endorsement-list",
            "endorsement-create"
        ]

        if view_type in valid_views:
            self.view_type = view_type
        else:
            self.view_type = None

        self.Session = session_factory
        self.setup_ui()
        self.load_data()
        self.apply_table_styles()

    def apply_table_styles(self):
        """Apply styling to the table widget."""
        qss_path = os.path.join(os.path.dirname(__file__), "styles", "table.css")
        button_cursor_pointer(self.export_btn)
        
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        

        try:
            with open(qss_path, "r") as f:
                self.table.setStyleSheet(f.read())
        except FileNotFoundError:
            print("Warning: Style file not found. Default styles will be used.")

        # Additional Qt properties for better appearance
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        # Stretch last column to fill space
        self.table.horizontalHeader().setStretchLastSection(True)
        
        # Set column widths (adjust as needed)
        self.table.setColumnWidth(0, 100)  # Ref No
        self.table.setColumnWidth(1, 100)  # Date
        self.table.setColumnWidth(2, 100)  # Category
        self.table.setColumnWidth(3, 150)  # Product Code
        self.table.setColumnWidth(4, 150)  # Lot Number
        self.table.setColumnWidth(5, 80)   # Qty (kg)
        self.table.setColumnWidth(6, 80)   # Status

        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a9eea;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                width: 120px;                        
            }

            QPushButton:hover {
                background-color: #317dc4;
                color: white;
            }                         
        """)
        
    def setup_ui(self):
        """Initialize UI components."""
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Create table
        self.table = QTableWidget()
        self.table.setObjectName("endorsementTable")
        self.table.setSizePolicy(
            QSizePolicy.Policy.Expanding, 
            QSizePolicy.Policy.Expanding
        )
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setMinimumHeight(300)
        
        # this is for having a right click button the rows
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        # Configure headers
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Ref No", "Date Endorse", "Category", 
            "Product Code", "Lot Number", 
            "Qty (kg)", "Status", "Endorsed By"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        
        # Create a container widget for proper resizing
        container = QWidget()
        container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        container.setLayout(QVBoxLayout())
        container.layout().setContentsMargins(0, 0, 0, 0)
        container.layout().addWidget(self.table)

        # Add scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        # scroll_area.setWidget(self.table)
        scroll_area.setWidget(container)
        
        self.layout.addWidget(scroll_area)
        # self.layout.addStretch()
         
        # Connect signals
        self.table.doubleClicked.connect(self.on_row_double_click)

        # add the export button here
        
        self.export_btn = QPushButton("Export Excel")
        self.export_btn.setObjectName("endorsement-export-btn")

        btn_container = QHBoxLayout()
        btn_container.addWidget(self.export_btn)
        btn_container.addStretch()
        self.layout.addLayout(btn_container)
        self.export_btn.clicked.connect(self.export_to_excel)

        # self.layout.addWidget(self.export_btn)
        
        if self.view_type and self.view_type == "endorsement-create":
            self.export_btn.hide()

    def export_to_excel(self):
        """Export table data to Excel file."""
        try:
            # Get save file path
            path, _ = QFileDialog.getSaveFileName(
                self,
                "Save as Excel",
                "Endorsement_Summary",
                "Excel Files (*.xlsx)"
            )
            
            if not path:
                return

            # Create DataFrame from table data
            data = []
            for row in range(self.table.rowCount()):
                row_data = []
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    row_data.append(item.text() if item else "")
                data.append(row_data)

            headers = [self.table.horizontalHeaderItem(i).text() 
                      for i in range(self.table.columnCount())]
            
            df = pd.DataFrame(data, columns=headers)
            
            # Export using pandas
            df.to_excel(path, index=False)
            StyledMessageBox.information(
                self, 
                "Success", 
                f"Exported to {path}"
            )
            
        except Exception as e:
            StyledMessageBox.critical(
                self, 
                "Error", 
                f"Export failed: {str(e)}"
            )

    def load_data(self):
        """Load data from database."""
        try:
            session = self.Session()
            endorsements = session.query(EndorsementModel)\
                .order_by(EndorsementModel.t_date_endorsed.desc(), 
                        EndorsementModel.t_refno.desc())\
                .all()
            
            self.table.setRowCount(len(endorsements))
            
            for row, endorsement in enumerate(endorsements):
                self._set_table_item(row, 0, endorsement.t_refno)
                self._set_table_item(row, 1, endorsement.t_date_endorsed.strftime("%Y-%m-%d"))
                self._set_table_item(row, 2, endorsement.t_category.value)
                self._set_table_item(row, 3, endorsement.t_prodcode)
                self._set_table_item(row, 4, endorsement.t_lotnumberwhole)
                self._set_table_item(row, 5, f"{endorsement.t_qtykg:.2f}")
                self._set_table_item(row, 6, endorsement.t_status.value)
                self._set_table_item(row, 7, endorsement.t_endorsed_by)
            
            self.table.verticalHeader().setDefaultSectionSize(24)
            self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
            self.table.resizeColumnsToContents()
        finally:
            session.close()
    
    def _set_table_item(self, row: int, col: int, value: str):
        """Helper method to set table items."""
        item = QTableWidgetItem(str(value))
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, col, item)
    
    def on_row_double_click(self, index):
        """Emit signal when row is double-clicked."""
        ref_no = self.table.item(index.row(), 0).text()
        self.double_clicked.emit(ref_no)
    
    def show_context_menu(self, pos):
        # Get the clicked row
        row = self.table.rowAt(pos.y())
        
        if row < 0:  # Clicked outside a row
            return
        
        # EXTRACT SPECIFIC VALUES FROM THE ROW
        # the number should match the index based on the table layout
        ref_no = self.table.item(row, 0).text() if self.table.item(row, 0) else "N/A"
        product_code = self.table.item(row, 3).text() if self.table.item(row, 3) else "N/A"

        # Create the menu
        menu = QMenu(self)

        # Add actions
        edit_action = menu.addAction("Edit Record")
        delete_action = menu.addAction("Delete Record")
        add_action = menu.addAction("Add New Record")

        # Connect actions to functions
        edit_action.triggered.connect(lambda: print(f"Edit action triggered - Row: {row}, Ref No: {ref_no}, Product Code: {product_code}"))
        delete_action.triggered.connect(lambda: print(f"Delete action triggered - Row: {row}, Ref No: {ref_no}, Product Code: {product_code}"))
        add_action.triggered.connect(lambda: print(f"Add action triggered from Row: {row}, Ref No: {ref_no}"))

        # Show the menu at the cursor position
        menu.exec(self.table.viewport().mapToGlobal(pos))

class EndorsementListView(QWidget):
    """View with filters and table"""
    def __init__(self, session_factory, parent=None):
        super().__init__(parent)
        self.Session = session_factory
        self.setup_ui()
        self.apply_styles()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # --- Top row filter layout ---
        top_filter_layout = QHBoxLayout()
        top_filter_layout.setContentsMargins(0, 0, 0, 0)
        top_filter_layout.setSpacing(6)

        self.category_filter = QComboBox()
        self.status_filter = QComboBox()
        self.prod_code_input = QLineEdit()
        self.ref_no_input = QLineEdit()

        category_label = QLabel("Category:")
        status_label = QLabel("Status:")
        prod_code_label = QLabel("Prod Code:")
        ref_no_label = QLabel("Ref No:")

        for label in [category_label, status_label, prod_code_label, ref_no_label]:
            label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        top_filter_layout.addWidget(category_label)
        top_filter_layout.addWidget(self.category_filter)
        top_filter_layout.addWidget(status_label)
        top_filter_layout.addWidget(self.status_filter)
        top_filter_layout.addWidget(prod_code_label)
        top_filter_layout.addWidget(self.prod_code_input)
        top_filter_layout.addWidget(ref_no_label)
        top_filter_layout.addWidget(self.ref_no_input)
        top_filter_layout.addStretch()  # Push items to the left

        # --- Bottom row filter layout ---
        bottom_filter_layout = QHBoxLayout()
        bottom_filter_layout.setContentsMargins(0, 0, 0, 0)
        bottom_filter_layout.setSpacing(6)

        self.date_from = QDateEdit(calendarPopup=True)
        self.date_to = QDateEdit(calendarPopup=True)
        self.search_button = QPushButton("Search")
        self.search_button.setObjectName("endorsementList-search-btn")

        from_label = QLabel("From:")
        to_label = QLabel("To:")

        for label in [from_label, to_label]:
            label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        bottom_filter_layout.addWidget(from_label)
        bottom_filter_layout.addWidget(self.date_from)
        bottom_filter_layout.addWidget(to_label)
        bottom_filter_layout.addWidget(self.date_to)
        bottom_filter_layout.addStretch()  # Push search button to the right
        bottom_filter_layout.addWidget(self.search_button)

        # --- Table setup ---
        self.table = EndorsementTableWidget(
            session_factory=self.Session,
            view_type="endorsement-list"
        )

        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Add all to main layout
        layout.addLayout(top_filter_layout)
        layout.addLayout(bottom_filter_layout)
        layout.addWidget(self.table)
        layout.setStretch(2, 1)

        self.create_category_menu()
        self.setLayout(layout)

    def apply_styles(self):
        qss_path = os.path.join(os.path.dirname(__file__), "styles", "endorsement_list.css")

        try:
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print("Warning: Style file not found. Default styles will be used.")
    
    def create_category_menu(self):
        for category in CategoryEnum:
            self.category_filter.addItem(category.value, category)

class EndorsementUpdateView(QWidget):
    """View for updating/deleting records"""
    def __init__(self, session_factory, parent=None):
        super().__init__(parent)
        self.Session = session_factory
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Form (could reuse your form with some modifications)
        # self.form = EndorsementFormWidget()
        
        # Buttons
        button_layout = QHBoxLayout()
        self.update_button = QPushButton("Update")
        self.delete_button = QPushButton("Delete")
        self.cancel_button = QPushButton("Cancel")
        
        button_layout.addWidget(self.update_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.cancel_button)
        
        # layout.addWidget(self.form)
        layout.addLayout(button_layout)
        self.setLayout(layout)

class EndorsementMainView(QWidget):
    def __init__(self, session_factory, parent=None):
        super().__init__(parent)
        self.Session = session_factory
        self.setup_ui()
        self.apply_styles()
        
    def setup_ui(self):
        self.layout = QVBoxLayout()
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        self.create_btn = QPushButton("Create New")
        self.list_btn = QPushButton("View List")
        self.create_btn.setObjectName("endorsement-create-btn")
        self.list_btn.setObjectName("endorsement-list-btn")
        
        nav_layout.addWidget(self.create_btn)
        nav_layout.addWidget(self.list_btn)
        nav_layout.addStretch()
        
        # Stacked widget for views
        self.stacked_widget = QStackedWidget()
        
        # Create views
        self.create_view = EndorsementView(self.Session)
        self.list_view = EndorsementListView(self.Session)
        self.update_view = EndorsementUpdateView(self.Session)
        
        # Add to stack
        self.stacked_widget.addWidget(self.create_view)
        self.stacked_widget.addWidget(self.list_view)
        self.stacked_widget.addWidget(self.update_view)
        
        # Connect signals
        self.create_btn.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.create_view))
        self.list_btn.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.list_view))
        
        # When a record is selected in list view for editing
        self.list_view.table.double_clicked.connect(self.show_update_view)
        
        self.layout.addLayout(nav_layout)
        self.layout.addWidget(self.stacked_widget)
        self.setLayout(self.layout)
    
    def apply_styles(self):
        qss_path = os.path.join(os.path.dirname(__file__), "styles", "crud_btn.css")
        
        try:
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print("Warning: Style file not found. Default styles will be used.")

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
