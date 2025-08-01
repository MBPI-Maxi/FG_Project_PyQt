

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    func,
    Enum,
    ForeignKey
)
from sqlalchemy.orm import relationship
from models import Base
from constants.Enums import Department, UserRole

class User(Base):
    __tablename__ = "users"

    user_id = Column(
        Integer, 
        primary_key=True, 
        autoincrement=True,
        comment="Unique identifier for the user. Automatically increments."
    )
    username = Column(
        String(50), 
        nullable=False,
        comment="Unique username for authentication. Required field."
    )
    password = Column(
        String, 
        nullable=False,
        comment="Hashed password for user authentication. Stored using secure hashing."
    )
    workstation_name = Column(
        String(40), 
        nullable=True,
        comment="Optional identifier for the user's primary workstation or device."
    )
    role = Column(
        Enum(UserRole), 
        nullable=False, 
        default=UserRole.USER,
        comment="User's permission level (e.g., ADMIN, USER). Defaults to USER."
    )
    department = Column(
        Enum(Department), 
        nullable=False,
        comment="Organizational department the user belongs to (e.g., IT, HR, PRODUCTION)."
    )


    # reverse relationship to the auth_logs
    ### NOTE: SAMPLE ###
    #############################################################
    # user = session.query(User).first()                        #
    # for log in user.auth_logs:                                #
    #     print(log.timestamp, log.status)                      #
    #############################################################
    
    auth_logs = relationship("AuthLog", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(username={self.username}, role={self.role.name}, dept={self.department.name})>"

class AuthLog(Base):
    __tablename__ = "auth_logs"
    
    log_id = Column(
        Integer, 
        primary_key=True,
        comment="Primary key identifier for the log entry."
    )
    user_id = Column(
        Integer, 
        ForeignKey("users.user_id", ondelete="CASCADE"), 
        nullable=True,
        comment="References the user who triggered the event. Nullable if user is deleted."
    )
    username = Column(
        String(50),
        comment="Stores the username at the time of the event (for auditing even if user is deleted)."
    ) 
    event_type = Column(
        String(50),
        comment="Type of event (e.g., LOGIN, AUTH_ATTEMPT, LOGOUT, PASSWORD_RESET)."
    ) 
    status = Column(
        String(10),
        comment="Outcome of the event: SUCCESS or FAIL."
    )   
    additional_info = Column(
        String(255), 
        nullable=True,
        comment="Additional context (e.g., IP address, failure reason, device info)."
    )
    timestamp = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        comment="Timestamp of when the event was logged (automatically set to current time)."
    )

    # reverse relationship to the User
    ### NOTE: SAMPLE ###
    #############################################################
    # log = session.query(AuthLog).first()                      #
    # print(log.user.username)                                  #
    #############################################################

    user = relationship("User", back_populates="auth_logs")

    def __repr__(self):
        return f"<AuthLog(user={self.username}, type={self.event_type}, status={self.status}, time={self.timestamp})>"