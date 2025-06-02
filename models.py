from sqlalchemy import Column, String, Boolean, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class FileScan(Base):
    __tablename__ = "file_scans"
    file_hash = Column(String, primary_key=True, index=True)
    scan_result = Column(Boolean, nullable=False)
    filename = Column(String, nullable=True)
    scan_timestamp = Column(DateTime(timezone=True), server_default=func.now())
