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

class StatusEnum(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"

