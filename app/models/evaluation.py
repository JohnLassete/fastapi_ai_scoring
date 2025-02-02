from sqlalchemy import Column, Integer, String, BigInteger, Numeric, Text, TIMESTAMP
from app.config.db import Base

class Evaluation(Base):
    __tablename__ = "evaluation"

    evaluation_id = Column(BigInteger, primary_key=True, index=True)
    interview_id = Column(BigInteger, index=True)
    question_id = Column(BigInteger, index=True)
    asrfilename = Column(Text)
    semantic_similarity_score = Column(Numeric(3))
    broad_topic_sim_score = Column(Numeric(3))
    grammar_score = Column(Numeric(3))
    disfluency_score = Column(Numeric(3))
    videofilename = Column(Text)
    videofile_s3key = Column(Text)
    asrfile_s3key = Column(Text)
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)