from enum import Enum

# IT super password
class ITCredentials(Enum):
    SUPER_PASSWORD = "**itadmin**"

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
