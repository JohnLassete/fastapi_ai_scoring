from app.config.db import Base
from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime
from sqlalchemy.sql import func

class Interview(Base):
    __tablename__ = "interview"

    interview_id = Column(BigInteger, primary_key=True, index=True)
    interview_date = Column(DateTime, nullable=False)
    candidate_id = Column(BigInteger, nullable=False)
    manager_id = Column(BigInteger, nullable=False)
    remarks = Column(Text)
    created_on = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

