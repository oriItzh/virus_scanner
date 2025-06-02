from sqlalchemy import Column, String, Boolean, DateTime, func, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship with FileScan
    scans = relationship("FileScan", back_populates="user")

class FileScan(Base):
    __tablename__ = "file_scans"
    file_hash = Column(String, primary_key=True, index=True)
    scan_result = Column(Boolean, nullable=False)
    filename = Column(String, nullable=True)
    scan_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    
    # Relationship with User
    user = relationship("User", back_populates="scans")
