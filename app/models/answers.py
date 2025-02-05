from sqlalchemy import Column, BigInteger, Text, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Answers(Base):
    __tablename__ = 'answers'
    answer_id = Column(BigInteger, primary_key=True)
    answer = Column(Text)
    question_id = Column(BigInteger)
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)