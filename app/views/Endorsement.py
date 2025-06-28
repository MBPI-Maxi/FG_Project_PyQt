from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QLineEdit, QDateEdit, QComboBox, QDoubleSpinBox, QPushButton,
    
)
from PyQt6.QtCore import QDate, Qt 
from pydantic import BaseModel, Field, ValidationError, field_validator
from datetime import date
from constants.Enums import StatusEnum, CategoryEnum
from app.StyledMessage import StyledMessageBox

import os


# --- FORM SCHEMA IS CREATED HERE FOR SERIALIZATION AND VALIDATION ---
class EndorsementFormSchema(BaseModel):
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
        default=StatusEnum.FAILED, 
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
        if not value.startswith('REF-'):
            raise ValueError('Reference number must start with "REF-"')

        return value
    
    @field_validator("t_prodcode")
    @classmethod
    def validate_prodcode_format(cls, value):
        valid_length_for_prod = 16
        if not len(value) >= valid_length_for_prod:
            raise ValueError("Production code must be GTE 16")
        return value
    
    ###################################################################

# --- ENDORSEMENT VIEW LOGIC IS HERE ---
class EndorsementView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Endorsement Form")
        self.setObjectName("EndorsementForm")
        self.init_ui()
        self.apply_styles()

    def init_ui(self):
        self.main_layout = QVBoxLayout()
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop) # Align content to the top

        self.form_fields = {} # Dictionary to store references to input widgets and error labels

        # Helper function to create a labeled input field
        def create_input_row(label_text, widget, field_name, error_label_name):
            h_layout = QHBoxLayout()
            label = QLabel(label_text)
            h_layout.addWidget(label)
            h_layout.addWidget(widget)
            
            error_label = QLabel("")
            error_label.setStyleSheet("color: red; font-size: 14px;") # error label font size
            error_label.setObjectName(f"{field_name}_error_label")
            h_layout.addWidget(error_label)
            
            self.form_fields[field_name] = widget
            self.form_fields[error_label_name] = error_label
            
            self.main_layout.addLayout(h_layout)
        
        # 1. Reference Number
        self.t_refno_input = QLineEdit()
        create_input_row("Reference Number:", self.t_refno_input, "t_refno", "t_refno_error")

        # 2. Date Endorsed
        self.t_date_endorsed_input = QDateEdit(calendarPopup=True)
        self.t_date_endorsed_input.setDate(QDate.currentDate())
        create_input_row("Date Endorsed:", self.t_date_endorsed_input, "t_date_endorsed", "t_date_endorsed_error")

        # 3. Category
        self.t_category_input = QComboBox()
        for category in CategoryEnum:
            self.t_category_input.addItem(category.value, category) # Store enum object as user data
        
        # create the input row
        create_input_row("Category:", self.t_category_input, "t_category", "t_category_error")

        # 4. Product Code
        self.t_prodcode_input = QLineEdit()
        create_input_row("Product Code:", self.t_prodcode_input, "t_prodcode", "t_prodcode_error")

        # 5. Whole Lot Number
        self.t_lotnumberwhole_input = QLineEdit()
        create_input_row("Whole Lot Number:", self.t_lotnumberwhole_input, "t_lotnumberwhole", "t_lotnumberwhole_error")

        # 6. Quantity (kg)
        self.t_qtykg_input = QDoubleSpinBox()
        self.t_qtykg_input.setMinimum(0.01) # Pydantic gt=0, so min here can be slightly above 0
        self.t_qtykg_input.setMaximum(999999999.99)
        self.t_qtykg_input.setDecimals(2)
        create_input_row("Quantity (kg):", self.t_qtykg_input, "t_qtykg", "t_qtykg_error")

        # 7. Weight per Lot
        self.t_wtlot_input = QDoubleSpinBox()
        self.t_wtlot_input.setMinimum(0.01) # Pydantic gt=0, so min here can be slightly above 0
        self.t_wtlot_input.setMaximum(999999999.99)
        self.t_wtlot_input.setDecimals(2)
        create_input_row("Weight per Lot:", self.t_wtlot_input, "t_wtlot", "t_wtlot_error")

        # 8. Status
        self.t_status_input = QComboBox()
        
        for status in StatusEnum:
            self.t_status_input.addItem(status.value, status) # Store enum object as user data
        
        create_input_row("Status:", self.t_status_input, "t_status", "t_status_error")
        self.t_status_input.setCurrentText(StatusEnum.FAILED.value) # Set default as per schema

        # 9. Endorsed By
        self.t_endorsed_by_input = QLineEdit()
        create_input_row("Endorsed By:", self.t_endorsed_by_input, "t_endorsed_by", "t_endorsed_by_error")

        # Spacer to push elements to the top
        self.main_layout.addStretch(1)

        # Save Button
        self.save_button = QPushButton("Save Endorsement")
        self.save_button.setObjectName("endorsement-save-btn")
        self.save_button.clicked.connect(self.save_endorsement)
        self.main_layout.addWidget(self.save_button)

        self.main_layout.setSpacing(12)
        self.setLayout(self.main_layout)

    def get_form_data(self):
        """Collects data from UI widgets and returns it as a dictionary."""
        return {
            "t_refno": self.t_refno_input.text(),
            "t_date_endorsed": self.t_date_endorsed_input.date().toPyDate(),
            "t_category": self.t_category_input.currentData(), # Retrieves the stored Enum object
            "t_prodcode": self.t_prodcode_input.text(),
            "t_lotnumberwhole": self.t_lotnumberwhole_input.text(),
            "t_qtykg": self.t_qtykg_input.value(),
            "t_wtlot": self.t_wtlot_input.value(),
            "t_status": self.t_status_input.currentData(), # Retrieves the stored Enum object
            "t_endorsed_by": self.t_endorsed_by_input.text(),
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
            # Validate the data using your Pydantic schema
            validated_data = EndorsementFormSchema(**form_data)

            # If validation passes:
            # At this point, you would typically pass `validated_data.dict()`
            # to your SQLAlchemy model for database insertion/update.
            # For this example, we'll just print it.
            print("Form data is valid!")
            print(validated_data.model_dump_json(indent=2)) # Use model_dump_json for Pydantic v2+

            # QMessageBox.information(self, "Success", "Endorsement form submitted successfully!")
            StyledMessageBox.information(
                self,
                "Success",
                "Endorsement form submitted successfully!"
            )

            # Optionally clear the form after successful submission
            self.clear_form()

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
            # Catch any other unexpected errors during data collection or processing
            StyledMessageBox.critical(
                self,
                "Error",
                f"An unexpected error occurred: {e}"
            )
            print(f"An unexpected error occurred: {e}")

    def clear_form(self):
        """Resets the input fields to their initial state."""
        self.t_refno_input.clear()
        self.t_date_endorsed_input.setDate(QDate.currentDate())
        self.t_category_input.setCurrentIndex(0) # Select first item
        self.t_prodcode_input.clear()
        self.t_lotnumberwhole_input.clear()
        self.t_qtykg_input.setValue(0.01) # Or some default non-zero value
        self.t_wtlot_input.setValue(0.01) # Or some default non-zero value
        self.t_status_input.setCurrentText(StatusEnum.FAILED.value)
        self.t_endorsed_by_input.clear()
        self.clear_error_messages() # Ensure all error messages are cleared

    def apply_styles(self):
        qss_style = os.path.join(os.path.dirname(__file__), "styles", "endorsement.css")

        try:
            with open(qss_style, "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print("Warning: Style file not found. Default styles will be used.")

# --- Main application entry point for testing ---
# if __name__ == "__main__":
#     from PyQt6.QtWidgets import QApplication
#     import sys
#     from enum import Enum # Define Enums if constants/Enums.py is not available for testing

#     # --- TEMPORARY ENUM DEFINITIONS FOR STANDALONE TESTING ---
#     # If constants/Enums.py does not exist or is not in the path for direct execution,
#     # define them here for this script to run independently.
#     # In a real project, these should come from constants/Enums.py
#     try:
#         from constants.Enums import CategoryEnum, StatusEnum
#     except ImportError:
#         print("Warning: constants/Enums.py not found. Using temporary Enum definitions.")
#         class CategoryEnum(str, Enum):
#             MB = "MB"
#             PB = "PB"
#             OTHER = "OTHER"

#         class StatusEnum(str, Enum):
#             FAILED = "FAILED"
#             PASSED = "PASSED"
#             PENDING = "PENDING"
#     # --- END TEMPORARY ENUM DEFINITIONS ---

#     app = QApplication(sys.argv)
#     window = EndorsementView()
#     window.show()
#     sys.exit(app.exec())