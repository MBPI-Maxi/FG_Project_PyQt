from enum import Enum

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
    OVERSIZE = "OVER-SIZED"
