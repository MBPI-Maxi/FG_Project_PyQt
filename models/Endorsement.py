from sqlalchemy import (
    Boolean, 
    Column, 
    Enum, 
    DateTime,
    Date, 
    Integer,
    String, 
    Float, 
    func,
    ForeignKey,
    UniqueConstraint
)
from constants.Enums import CategoryEnum, StatusEnum
from models import Base
from sqlalchemy.orm import relationship

class EndorsementModel(Base):
    __tablename__ = "tbl_endorsement_t1"

    t_id = Column(Integer(), primary_key=True, autoincrement=True)
    t_refno = Column(String, nullable=False, unique=True) # should be unique in order to be referenced in the ENDORSEMENTMODELT2
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

    # REVERSE lookup for t2
    endorsement_t2_items = relationship(
        "EndorsementModelT2", 
        back_populates="endorsement_parent", 
        cascade="all, delete-orphan"
    )

class EndorsementModelT2(Base):
    __tablename__ = "tbl_endorsement_t2"

    t_id = Column(Integer(), primary_key=True, autoincrement=True)
    t_refno = Column(String, ForeignKey("tbl_endorsement_t1.t_refno"), nullable=False)
    t_lotnumbersingle = Column(String(10), nullable=False, unique=True)
    t_qty = Column(Float, nullable=False)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    endorsement_parent = relationship("EndorsementModel", back_populates="endorsement_t2_items")

    __table_args__ = (
        UniqueConstraint("t_refno", "t_lotnumbersingle", name="uq_refno_lot"),
    )
