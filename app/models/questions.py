from sqlalchemy import Column, BigInteger, Integer, SmallInteger, Text, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Questions(Base):
    __tablename__ = 'questions'
    question_id = Column(BigInteger, primary_key=True)
    primary_skill_id = Column(Integer)
    sub_tech = Column(Text)
    difficulty_level = Column(SmallInteger)
    question_level = Column(SmallInteger)
    time_to_answer = Column(Integer)
    question_text = Column(Text)
    code_file_name = Column(Text)
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)
    question_image_s3_link = Column(Text)
    question_video_s3_link = Column(Text)