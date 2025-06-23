
from models import Base
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Date,
    Integer,
    String,
    Float,
    func
)

class User(Base):
    __tablename__ = "FG_User"

    id = Column