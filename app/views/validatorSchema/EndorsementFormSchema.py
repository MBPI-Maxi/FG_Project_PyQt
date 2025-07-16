from constants.Enums import StatusEnum, CategoryEnum
from datetime import date
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Type, TypedDict
from sqlalchemy.orm import Session, DeclarativeMeta
from constants.Enums import CategoryEnum, StatusEnum
import re
import math

class FormData(TypedDict):
    """
    Update this code when you are changing EndorsementCreateView.get_form_data() method
    """
    t_refno: str
    t_date_endorsed: date
    t_category: CategoryEnum 
    t_prodcode: str
    t_lotnumberwhole: str
    t_qtykg: float
    t_wtlot: float
    t_status: StatusEnum  
    t_endorsed_by: str
    t_has_excess: bool
    t_bag_num: int
    t_remarks: str

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
    t_bag_num: Optional[int] = Field(
        None,
        ge=0,
        description="Number of bags (optional)"
    )
    # --------- CUSTOM CONFIGURATION ----------
    class Config:
        # Ensures that Pydantic works correctly with Enum values
        use_enum_values = True 
    # ----------------------------------------

    _db_session = None
    _endorsement_model_t1 = None
    _endorsement_model_t2 = None

    @classmethod
    def set_db_session(cls, session: Type[Session]):
        cls._db_session = session
    
    @classmethod
    def set_model_t1(cls, model: Type[DeclarativeMeta]):
        cls._endorsement_model_t1 = model

    @classmethod
    def set_model_t2(cls, model: Type[DeclarativeMeta]):
        cls._endorsement_model_t2 = model
    
    @classmethod
    def validate_with_session(
        cls, 
        data: FormData,  # data of the inputs of pyqt6
        session: Type[Session],
        endorsement_model_t1: Type[DeclarativeMeta] = None,
        endorsement_model_t2: Type[DeclarativeMeta] = None
    ):
        """Helper method to validate with a database session"""
        try:
            if endorsement_model_t1:
                cls.set_model_t1(endorsement_model_t1)
            
            if endorsement_model_t2:
                cls.set_model_t2(endorsement_model_t2)
            
            cls.set_db_session(session)

            return cls(**data)
        finally:
            cls.set_db_session(None)

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
    
    @field_validator("t_bag_num", mode="before")
    @classmethod
    def validate_t_bag_num(cls, value):
        if value == 0:
            return None
        
        try:
            int_value = int(value)
            
            if int_value <= 0:
                raise ValueError("Bag number must be a positive integer")
            
            return int_value
        except ValueError:
            raise ValueError("Bag number must be a positive integer")

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

    # @model_validator(mode="after")
    # def validate_no_overlapping_lots(self):
    #     if self._db_session is None or self._endorsement_model_t1 is None:
    #         return self  # Skip validation if no session

    #     if not hasattr(self, 't_lotnumberwhole') or not self.t_lotnumberwhole:
    #         return self

    #     model = self._endorsement_model_t1

    #     # Get ALL existing lots (regardless of prodcode)
    #     existing_lots = self._db_session.query(
    #         model.t_lotnumberwhole,
    #         model.t_prodcode
    #     ).filter(
    #         model.is_deleted == False,
    #         model.t_lotnumberwhole != self.t_lotnumberwhole  # Exclude self for updates
    #     ).all()

    #     # Parse the new lot range
    #     if "-" in self.t_lotnumberwhole:
    #         new_start, new_end = self.t_lotnumberwhole.split("-")
    #         new_start_num = int(new_start[:4])
    #         new_start_suffix = new_start[4:]
    #         new_end_num = int(new_end[:4])
    #         new_end_suffix = new_end[4:]
    #     else:
    #         new_start_num = new_end_num = int(self.t_lotnumberwhole[:4])
    #         new_start_suffix = new_end_suffix = self.t_lotnumberwhole[4:]

    #     for existing_lot, existing_prodcode in existing_lots:
    #         # Skip if the existing lot is from the same prodcode (optional, if needed)
    #         # if existing_prodcode == self.t_prodcode:
    #         #     continue

    #         # Parse existing lot range
    #         if "-" in existing_lot:
    #             existing_start, existing_end = existing_lot.split("-")
    #             existing_start_num = int(existing_start[:4])
    #             existing_start_suffix = existing_start[4:]
    #             existing_end_num = int(existing_end[:4])
    #             existing_end_suffix = existing_end[4:]
    #         else:
    #             existing_start_num = existing_end_num = int(existing_lot[:4])
    #             existing_start_suffix = existing_end_suffix = existing_lot[4:]

    #         # Check if suffixes match (optional, if lot suffixes must also be unique)
    #         if new_start_suffix != existing_start_suffix:
    #             continue  # Skip if suffixes don't match (optional)

    #         # Check for numeric overlap
    #         if (new_start_num <= existing_end_num) and (new_end_num >= existing_start_num):
    #             raise ValueError(
    #                 f"Lot range {self.t_lotnumberwhole} conflicts with existing lot {existing_lot} "
    #                 f"(Product Code: {existing_prodcode}). Lot numbers must be globally unique."
    #             )

    #     return self
    @model_validator(mode="after")
    def validate_no_overlapping_lots(self):
        if self._db_session is None or self._endorsement_model_t1 is None:
            return self  # Skip validation if no session

        if not hasattr(self, 't_lotnumberwhole') or not self.t_lotnumberwhole:
            return self

        model = self._endorsement_model_t1

        # Skip validation for single lots (they can exist multiple times)
        if "-" not in self.t_lotnumberwhole:
            return self

        # Only check for overlapping ranges if input is a range
        new_start, new_end = self.t_lotnumberwhole.split("-")
        new_start_num = int(new_start[:4])
        new_start_suffix = new_start[4:]
        new_end_num = int(new_end[:4])
        new_end_suffix = new_end[4:]

        # Get all existing RANGED lots (not single lots)
        existing_ranged_lots = self._db_session.query(
            model.t_lotnumberwhole,
            model.t_prodcode
        ).filter(
            model.is_deleted == False,
            model.t_lotnumberwhole != self.t_lotnumberwhole,  # Exclude self for updates
            model.t_lotnumberwhole.contains("-")  # Only check ranged lots
        ).all()

        for existing_lot, existing_prodcode in existing_ranged_lots:
            # Parse existing lot range
            existing_start, existing_end = existing_lot.split("-")
            existing_start_num = int(existing_start[:4])
            existing_start_suffix = existing_start[4:]
            existing_end_num = int(existing_end[:4])
            existing_end_suffix = existing_end[4:]

            # Check if suffixes match (optional)
            if new_start_suffix != existing_start_suffix:
                continue

            # Check for numeric overlap
            if (new_start_num <= existing_end_num) and (new_end_num >= existing_start_num):
                raise ValueError(
                    f"Lot range {self.t_lotnumberwhole} conflicts with existing lot {existing_lot} "
                    f"(Product Code: {existing_prodcode}). Ranged lot numbers must not overlap."
                )

        return self
    ###################################################################