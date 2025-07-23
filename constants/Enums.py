from enum import Enum
from typing import Literal

# IT super password
class ITCredentials(Enum):
    SUPER_PASSWORD = "**itadmin**"

class AuthLogStatus(Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    
    @staticmethod
    def get_event_type(event: str):
        event_type = {
            "registration": "REGISTRATION",
            "login": "LOGIN"
        }

        return event_type.get(event, None)

# for user table
class UserRole(Enum):
    ADMIN = "ADMIN"
    SUPERVISOR = "SUPERVISOR"
    USER = "USER"
    DISABLED = "DISABLED"

class Department(Enum):
    IT = "IT"
    WAREHOUSE = "WAREHOUSE"
    PRODUCTION = "PRODUCTION"
    LAB = "LAB"


# for endorsement table
class CategoryEnum(Enum):
    MB = "MB"
    DC = "DC"

class MBDefaultValue(Enum):
    """
    This is the default value of the kilo per bag for Masterbatch Category
    """
    KG = 25

class StatusEnum(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"

class RemarksEnum(Enum):
    NO_REMARKS = "No Remarks"
    OVERSIZED = "OVERSIZED"

class PageEnum(Enum):
    ITEMS_PER_PAGE = 20
    DEFAULT_CURRENT_PAGE = 1
    DEFAULT_TOTAL_PAGES = 1

class TableHeader():
    LABELS = {
        "endorsement": [
            "Ref No", "Date Endorse", "Category", 
            "Product Code", "Lot Number", 
            "Qty (kg)", "Status", "Bag Number",
            "Endorsed By", "Source Table", "Has Excess",
        ]
    }

    @classmethod
    def get_header(
        cls, 
        form_name_type: Literal[
            "endorsement",
            "deliveryReceipt",
            "outgoingRecord",
            "qcFailedEndorsement",
            "qcFailedToPassed",
            "qcLabExcess",
            "receivingReport",
            "requisitionLogbook",
            "returnReplacement"
        ]
    ):
        if not isinstance(form_name_type, str):
            raise ValueError("form_name_type datatype is incorrect")
        
        if form_name_type not in cls.LABELS:
            raise ValueError("form_name_type value is not valid")

        return cls.LABELS.get(form_name_type)
    
    @classmethod
    def get_header_index(
        cls,
        form_name_type: Literal[
            "endorsement",
            "deliveryReceipt",
            "outgoingRecord",
            "qcFailedEndorsement",
            "qcFailedToPassed",
            "qcLabExcess",
            "receivingReport",
            "requisitionLogbook",
            "returnReplacement"
        ],
        header_name: str
    ) -> int:
        """
        Returns the index position of the string in the list based on the header_name argument

        Note for Developer:
            Use an argument for the header_name that matches the string on the form_name_type labels
        """
        if not isinstance(form_name_type, str):
            raise ValueError("form_name_type datatype is incorrect")
        
        if form_name_type not in cls.LABELS:
            raise ValueError("form_name_type value is not valid")

        index_res = None
        for idx, element in enumerate(cls.LABELS.get(form_name_type)):
            if element == header_name.title():
                index_res = idx
                break

        return index_res 

        
