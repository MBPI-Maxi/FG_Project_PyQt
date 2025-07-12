from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import date
from constants.Enums import StatusEnum, CategoryEnum
import re
import math

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
    t_has_excess: bool = Field(
        False,
        description="User's input for 'has excess' checkbox"
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
    
    #     return self
    @model_validator(mode="after")
    def validate_lot_quantity_proportion(self):
        if "-" in self.t_lotnumberwhole:
            # For range lot numbers
            start, end = self.t_lotnumberwhole.split("-")
            start_num = int(start[:4])
            end_num = int(end[:4])
            
            # Calculate number of lots
            num_lots = (end_num - start_num) + 1
            
            # Calculate expected quantity
            expected_full_quantity = num_lots * self.t_wtlot
            
            if self.t_has_excess:
                # With excess, quantity must be >= expected_full_quantity - wtlot (since last can be partial)
                if self.t_qtykg < (expected_full_quantity - self.t_wtlot):
                    raise ValueError(
                        f"Quantity ({self.t_qtykg}) is too small for lot range {self.t_lotnumberwhole}. "
                        f"Minimum expected with excess: {expected_full_quantity - self.t_wtlot}"
                    )
                
                # Also check if quantity is more than full lots (must have excess)
                if self.t_qtykg > expected_full_quantity:
                    if not math.isclose(self.t_qtykg % self.t_wtlot, 0, abs_tol=1e-5):
                        raise ValueError(
                            f"Quantity ({self.t_qtykg}) exceeds full lots ({expected_full_quantity}) but "
                            "the excess isn't a proper partial lot."
                        )
            else:
                # Without excess, quantity must exactly match (with floating point tolerance)
                if not math.isclose(self.t_qtykg, expected_full_quantity, rel_tol=1e-5, abs_tol=1e-5):
                    raise ValueError(
                        f"Quantity ({self.t_qtykg}) doesn't match lot range {self.t_lotnumberwhole}. "
                        f"Expected exactly: {expected_full_quantity} (or check 'has excess')"
                    )
        else:
            # For single lot numbers
            if not self.t_has_excess and not math.isclose(self.t_qtykg, self.t_wtlot, rel_tol=1e-5, abs_tol=1e-5):
                raise ValueError(
                    f"Quantity ({self.t_qtykg}) doesn't match single lot weight ({self.t_wtlot}). "
                    "Either enable 'has excess' or set quantity equal to weight per lot."
                )
        
        # Check if has_excess should be checked based on quantity
        if "-" in self.t_lotnumberwhole and not self.t_has_excess:
            start, end = self.t_lotnumberwhole.split("-")
            start_num = int(start[:4])
            end_num = int(end[:4])
            num_lots = (end_num - start_num) + 1
            expected_full_quantity = num_lots * self.t_wtlot
            
            if not math.isclose(self.t_qtykg, expected_full_quantity, rel_tol=1e-5, abs_tol=1e-5):
                raise ValueError(
                    f"Quantity ({self.t_qtykg}) suggests there should be excess (expected {expected_full_quantity}). "
                    "Please check the 'has excess' checkbox."
                )
        
        return self
    ###################################################################