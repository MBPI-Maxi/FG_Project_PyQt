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
)
from constants.Enums import CategoryEnum, StatusEnum
from models import Base
from sqlalchemy.orm import relationship

class EndorsementModel(Base):
    __tablename__ = "tbl_endorsement_t1"

    t_id = Column(
        Integer(), 
        primary_key=True, 
        autoincrement=True,
        comment="Primary key identifier for the endorsement record. Auto-increments."
    )
    t_refno = Column(
        String, 
        nullable=False, 
        unique=True,
        comment="Unique reference number for tracking purposes. Used to link with tbl_endorsement_t2 records."
    ) 
    t_date_endorsed = Column(
        Date, 
        nullable=False,
        comment="Date when the endorsement was created. Format: YYYY-MM-DD."
    )
    t_category = Column(
        Enum(CategoryEnum), 
        nullable=False, 
        default=CategoryEnum.MB.value,
        comment="Product category (e.g., MB, FG, RM). Defaults to MB (Mother Bag)."
    )
    t_prodcode = Column(
        String, 
        nullable=False,
        comment="Product code identifying the specific material or product."
    )
    t_lotnumberwhole = Column(
        String, 
        nullable=False, 
        unique=True,
        comment="Complete lot number (e.g., '1234AB' or '1234AB-5678CD'). Must be unique."
    ) 
    t_qtykg = Column(
        Float, 
        nullable=False,
        comment="Total quantity in kilograms being endorsed. Must be > 0."
    )
    t_wtlot = Column(
        Float, 
        nullable=False,
        comment="Standard weight per individual lot in kilograms. Used for quantity validation."
    )
    t_status = Column(
        Enum(StatusEnum), 
        nullable=False, 
        default=StatusEnum.FAILED.value,
        comment="Current status of endorsement (PASSED, FAILED, HOLD). Defaults to FAILED."
    )
    t_has_excess = Column(
        Boolean, 
        default=False, 
        nullable=False,
        comment="Flag indicating if the quantity exceeds standard lot weights (partial lots)."
    )
    # t_bag_num = Column(Integer, nullable=True)
    t_endorsed_by = Column(
        String, 
        nullable=False,
        comment="Username or identifier of the person creating the endorsement."
    )
    t_remarks = Column(
        String(100), 
        nullable=True,
        comment="Optional comments or notes about the endorsement (max 100 chars)."
    )

    is_deleted = Column(
        Boolean, 
        default=False,
        comment="Soft delete flag. True indicates the record is marked for deletion."
    )
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        comment="Timestamp of when the record was created (auto-set on insert)."
    )
    updated_at = Column(
        DateTime(timezone=True), 
        onupdate=func.now(),
        comment="Timestamp of last record update (auto-updated on modification)."
    )

    # REVERSE lookup for t2
    endorsement_t2_items = relationship(
        "EndorsementModelT2", 
        back_populates="endorsement_parent", 
        cascade="all, delete-orphan"
    )

class EndorsementModelT2(Base):
    __tablename__ = "tbl_endorsement_t2"

    t_id = Column(
        Integer(), 
        primary_key=True, 
        autoincrement=True,
        comment="Primary key identifier for the endorsement line item. Auto-increments."
    )
    t_refno = Column(
        String, 
        ForeignKey("tbl_endorsement_t1.t_refno"), 
        nullable=False,
        comment="Foreign key reference to the parent endorsement in tbl_endorsement_t1."
    )
    t_lotnumbersingle = Column(
        String(10), 
        nullable=False,
        comment="Individual lot number (extracted from t_lotnumberwhole in parent). Max 10 chars."
    )
    t_qty = Column(
        Float, 
        nullable=False,
        comment="Quantity in kilograms for this specific lot. Must match parent's weight rules."
    )
    t_bag_num = Column(
        Integer, 
        nullable=True,
        comment="Optional physical bag number identifier for tracking purposes."
    )
    is_deleted = Column(
        Boolean, 
        default=False,
        comment="Soft delete flag. True indicates the record is marked for deletion."
    )
    t_remarks = Column(
        String(100), 
        nullable=True,
        comment="Optional comments about this specific lot (max 100 characters)."
    )
    is_lot_number_entered = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="Flag indicating if this lot number has been physically recorded in the system."
    )
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        comment="Timestamp when this lot record was created (auto-set on insert)."
    ) 
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        comment="Timestamp of last update to this record (auto-updated on modification)."
    )
    
    # ------------------ RELATIONSHIP -----------------------
    endorsement_parent = relationship(
        "EndorsementModel", 
        back_populates="endorsement_t2_items",
    )
    lot_excess = relationship(
        "EndorsementLotExcessModel",
        back_populates="lot",
        uselist=False,
        cascade="all, delete-orphan",
    )

class EndorsementLotExcessModel(Base):
    __tablename__ = "tbl_endorsement_lot_excess"

    t_id = Column(Integer, primary_key=True, autoincrement=True)
    tbl_endorsement_t2_ref = Column(
        Integer,
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
    """
    The columns here needs to match the views on the pg admin view
    """
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
    t_bag_num = Column(String)
    t_category = Column(String)
    t_has_excess = Column(Boolean)
    t_source_table = Column(String)
    