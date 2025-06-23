from sqlalchemy import (
    Boolean, 
    Column, 
    Enum, 
    DateTime,
    Date, 
    Integer,
    String, 
    Float, 
    func
)
from constants.Enums import CategoryEnum, StatusEnum
from models import Base
# from sqlalchemy.orm import relationship, validates

class EndorsementModel(Base):
    __tablename__ = "tbl_endorsement_t1"

    t_id = Column(Integer(), primary_key=True, autoincrement=True)
    t_refno = Column(String, nullable=False)
    t_date_endorsed = Column(Date, nullable=False)
    t_category = Column(Enum(CategoryEnum), nullable=False, default=CategoryEnum.MB.value)
    t_prodcode = Column(String, nullable=False)
    t_lotnumberwhole = Column(String, nullable=False)
    t_qtykg = Column(Float, nullable=False)
    t_wtlot = Column(Float, nullable=False)
    t_status = Column(Enum(StatusEnum), nullable=False, default=StatusEnum.FAILED.value)
    t_endorsed_by = Column(String, nullable=False)

    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
