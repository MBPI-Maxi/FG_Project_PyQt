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
    # UniqueConstraint
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
    t_lotnumberwhole = Column(String, nullable=False, unique=True) # this should be unique
    t_qtykg = Column(Float, nullable=False)
    t_wtlot = Column(Float, nullable=False)
    t_status = Column(Enum(StatusEnum), nullable=False, default=StatusEnum.FAILED.value)
    t_has_excess = Column(Boolean, default=False, nullable=False)
    t_bag_num = Column(Integer, nullable=True)
    t_endorsed_by = Column(String, nullable=False)
    t_remarks = Column(String(100), nullable=True)

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
    t_lotnumbersingle = Column(String(10), nullable=False)
    t_qty = Column(Float, nullable=False)
    # t_has_excess = Column(Boolean, default=False) just omit this because I already have a table for the excess items
    is_deleted = Column(Boolean, default=False)
    t_remarks = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # relationship
    endorsement_parent = relationship("EndorsementModel", back_populates="endorsement_t2_items")
    lot_excess = relationship(
        "EndorsementLotExcessModel",
        back_populates="lot",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # __table_args__ = (
    #     UniqueConstraint("t_refno", "t_lotnumbersingle", name="uq_refno_lot"),
    # )


class EndorsementLotExcessModel(Base):
    __tablename__ = "tbl_endorsement_lot_excess"

    t_id = Column(Integer, primary_key=True, autoincrement=True)
    tbl_endorsement_t2_ref = Column(
        Integer,
        # ForeignKey("tbl_endorsement_t2.t_lotnumbersingle"),
        ForeignKey("tbl_endorsement_t2.t_id"),
        nullable=False,
        unique=True  # ensures one-to-one mapping
    )
    t_excess_amount = Column(
        Float,
        nullable=False
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    lot = relationship("EndorsementModelT2", back_populates="lot_excess")

# ------  A SCHEMA FOR THE VIEW EXISTING ON THE DATABASE ------
class EndorsementCombinedView(Base):
    __tablename__ = "endorsement_combined"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True)  # <- synthetic primary key
    t_refno = Column(String)
    t_lot_number = Column(String)
    t_date_endorsed = Column(Date)
    t_total_quantity = Column(Float)
    t_prodcode = Column(String)
    t_status = Column(String)
    t_endorsed_by = Column(String)
    t_category = Column(String)
    t_has_excess = Column(Boolean)
    t_source_table = Column(String)
    