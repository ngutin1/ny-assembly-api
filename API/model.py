from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Member(Base):
    __tablename__ = 'members'
    
    member_id = Column(Integer, primary_key=True)
    name = Column(String)
    district = Column(Integer)
    session_year = Column(Integer)

class Transcript(Base):
    __tablename__ = 'transcripts'
    
    date = Column(String, primary_key=True)
    text = Column(Text)

class TranscriptSegment(Base):
    __tablename__ = 'transcript_segments'
    
    segment_id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String, ForeignKey('transcripts.date'))
    sequence_number = Column(Integer)
    member_id = Column(Integer, ForeignKey('members.member_id'))
    text = Column(Text)
    
    # Relationships for easier joins
    member = relationship("Member")
    transcript = relationship("Transcript")

class Activity(Base):
    __tablename__ = 'activity'
    
    activity_id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String, ForeignKey('transcripts.date'))
    segment_id = Column(Integer, ForeignKey('transcript_segments.segment_id'))
    member_from = Column(Integer, ForeignKey('members.member_id'))
    member_to = Column(Integer, ForeignKey('members.member_id'))
    interaction = Column(String)
    sentiment = Column(String, default='neutral')
    text_snippet = Column(Text)
    
    # Relationships
    from_member = relationship("Member", foreign_keys=[member_from])
    to_member = relationship("Member", foreign_keys=[member_to])
    segment = relationship("TranscriptSegment")