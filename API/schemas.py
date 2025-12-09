# schemas.py
from pydantic import BaseModel
from typing import List, Any, Optional, Generic, TypeVar

T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    success: bool
    message: str = ""
    responseType: str
    total: int
    offsetStart: int
    offsetEnd: int
    limit: int
    result: dict

    class Config:
        from_attributes = True


class ResultItems(BaseModel, Generic[T]):
    items: List[T]

    class Config:
        from_attributes = True

class MemberSchema(BaseModel):
    member_id: int
    name: str
    district: Optional[int] = None
    session_year: Optional[int] = None
    
    class Config:
        from_attributes = True

class TranscriptSchema(BaseModel):
    date: str
    text: str
    
    class Config:
        from_attributes = True

class TranscriptSegmentSchema(BaseModel):
    segment_id: int
    date: str
    sequence_number: int
    member_id: Optional[int] = None
    text: str
    member_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class ActivitySchema(BaseModel):
    activity_id: int
    date: str
    segment_id: int
    member_from: Optional[int] = None
    member_to: Optional[int] = None
    interaction: str
    from_member_name: Optional[str] = None
    to_member_name: Optional[str] = None
    
    class Config:
        from_attributes = True