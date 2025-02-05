from sqlalchemy import Column, BigInteger, Text, Numeric, Integer, SmallInteger, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Interview(Base):
    __tablename__ = 'interview'
    interview_id = Column(BigInteger, primary_key=True)
    interview_date = Column(TIMESTAMP)
    candidate_id = Column(BigInteger)
    manager_id = Column(BigInteger)
    remarks = Column(Text)
    created_on = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)
