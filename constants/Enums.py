from enum import Enum

class CategoryEnum(Enum):
    MB = "mb"
    DC = "dc"

class StatusEnum(Enum):
    PASSED = "passed"
    FAILED = "failed"