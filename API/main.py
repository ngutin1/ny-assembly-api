from fastapi import FastAPI, HTTPException, Query, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from database import * 
from model import *
from auth import verify_api_key

# Initialize rate limiter 
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="NY Assembly API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
@limiter.limit("100/minute")
def root(request: Request):
    return {
        "success": True,
        "message": "NY Assembly Transcript API",
        "version": "1.0",
        "authentication": "Required. Include ?key=YOUR_KEY in URL",
        "endpoints": {
            "members": "/members?key=YOUR_KEY",
            "transcripts": "/transcripts?key=YOUR_KEY",
            "segments": "/segments?key=YOUR_KEY",
            "interactions": "/interactions?key=YOUR_KEY"
        }
    }

# MEMBERS
@app.get("/members")
@limiter.limit("60/minute")
def get_members(
    request: Request,
    key: str = Depends(verify_api_key),  
    session_year: Optional[int] = None,
    district: Optional[int] = None,
    limit: int = Query(400, le=1000),
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get all members, optionally filtered by session year or district"""
    query = db.query(Member)
    
    if session_year:
        query = query.filter(Member.session_year == session_year)
    
    if district:
        query = query.filter(Member.district == district)
    
    total = query.count()
    members = query.order_by(Member.name).limit(limit).offset(offset).all()
    
    items = []
    for m in members:
        items.append({
            "sessionMemberId": m.member_id,
            "shortName": m.name,
            "sessionYear": m.session_year,
            "districtCode": m.district,
            "alternate": False,
            "memberId": m.member_id
        })
    
    return {
        "success": True,
        "message": "",
        "responseType": "member-session list",
        "total": total,
        "offsetStart": offset + 1 if total > 0 else 0,
        "offsetEnd": min(offset + len(items), total),
        "limit": limit,
        "result": {
            "items": items
        }
    }

@app.get("/members/{member_id}")
@limiter.limit("60/minute")
def get_member(
    request: Request,
    member_id: int,
    key: str = Depends(verify_api_key),  
    db: Session = Depends(get_db)
):
    """Get a specific member by ID"""
    member = db.query(Member).filter(Member.member_id == member_id).first()
    
    if member is None:
        return {
            "success": False,
            "message": "Member not found",
            "responseType": "member",
            "total": 0,
            "offsetStart": 0,
            "offsetEnd": 0,
            "limit": 1,
            "result": {}
        }
    
    return {
        "success": True,
        "message": "",
        "responseType": "member",
        "total": 1,
        "offsetStart": 1,
        "offsetEnd": 1,
        "limit": 1,
        "result": {
            "sessionMemberId": member.member_id,
            "shortName": member.name,
            "sessionYear": member.session_year,
            "districtCode": member.district,
            "alternate": False,
            "memberId": member.member_id
        }
    }

# TRANSCRIPTS
@app.get("/transcripts")
@limiter.limit("60/minute")
def get_all_transcripts(
    request: Request,
    key: str = Depends(verify_api_key),  
    limit: int = Query(400, le=1000),
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get list of all available transcript dates"""
    total = db.query(Transcript).count()
    dates_query = db.query(Transcript.date).order_by(Transcript.date.desc())
    dates = dates_query.limit(limit).offset(offset).all()
    
    items = [{"date": d[0]} for d in dates]
    
    return {
        "success": True,
        "message": "",
        "responseType": "transcript list",
        "total": total,
        "offsetStart": offset + 1 if total > 0 else 0,
        "offsetEnd": min(offset + len(items), total),
        "limit": limit,
        "result": {
            "items": items
        }
    }

@app.get("/transcripts/{date}")
@limiter.limit("30/minute")
def get_transcript(
    request: Request,
    date: str,
    key: str = Depends(verify_api_key),  
    db: Session = Depends(get_db)
):
    """Get full transcript for a specific date"""
    transcript = db.query(Transcript).filter(Transcript.date == date).first()
    
    if transcript is None:
        return {
            "success": False,
            "message": "Transcript not found",
            "responseType": "transcript",
            "total": 0,
            "offsetStart": 0,
            "offsetEnd": 0,
            "limit": 1,
            "result": {}
        }
    
    return {
        "success": True,
        "message": "",
        "responseType": "transcript",
        "total": 1,
        "offsetStart": 1,
        "offsetEnd": 1,
        "limit": 1,
        "result": {
            "date": transcript.date,
            "text": transcript.text
        }
    }

# SEGMENTS
@app.get("/segments")
@limiter.limit("60/minute")
def get_segments(
    request: Request,
    key: str = Depends(verify_api_key),  
    date: Optional[str] = None,
    member_id: Optional[int] = None,
    limit: int = Query(100, le=1000),
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get transcript segments with optional filters"""
    query = db.query(TranscriptSegment, Member.name.label('member_name'))\
        .outerjoin(Member, TranscriptSegment.member_id == Member.member_id)
    
    if date:
        query = query.filter(TranscriptSegment.date == date)
    
    if member_id:
        query = query.filter(TranscriptSegment.member_id == member_id)
    
    total = query.count()
    query = query.order_by(TranscriptSegment.date, TranscriptSegment.sequence_number)
    results = query.limit(limit).offset(offset).all()
    
    items = []
    for segment, member_name in results:
        items.append({
            "segmentId": segment.segment_id,
            "date": segment.date,
            "sequenceNumber": segment.sequence_number,
            "memberId": segment.member_id,
            "text": segment.text,
            "memberName": member_name
        })
    
    return {
        "success": True,
        "message": "",
        "responseType": "segment list",
        "total": total,
        "offsetStart": offset + 1 if total > 0 else 0,
        "offsetEnd": min(offset + len(items), total),
        "limit": limit,
        "result": {
            "items": items
        }
    }

@app.get("/segments/{segment_id}")
@limiter.limit("60/minute")
def get_segment(
    request: Request,
    segment_id: int,
    key: str = Depends(verify_api_key),  
    db: Session = Depends(get_db)
):
    """Get a specific segment by ID"""
    result = db.query(TranscriptSegment, Member.name.label('member_name'))\
        .outerjoin(Member, TranscriptSegment.member_id == Member.member_id)\
        .filter(TranscriptSegment.segment_id == segment_id).first()
    
    if result is None:
        return {
            "success": False,
            "message": "Segment not found",
            "responseType": "segment",
            "total": 0,
            "offsetStart": 0,
            "offsetEnd": 0,
            "limit": 1,
            "result": {}
        }
    
    segment, member_name = result
    
    return {
        "success": True,
        "message": "",
        "responseType": "segment",
        "total": 1,
        "offsetStart": 1,
        "offsetEnd": 1,
        "limit": 1,
        "result": {
            "segmentId": segment.segment_id,
            "date": segment.date,
            "sequenceNumber": segment.sequence_number,
            "memberId": segment.member_id,
            "text": segment.text,
            "memberName": member_name
        }
    }

# INTERACTIONS
@app.get("/interactions")
@limiter.limit("60/minute")
def get_interactions(
    request: Request,
    key: str = Depends(verify_api_key),  
    member_id: Optional[int] = None,
    date: Optional[str] = None,
    interaction_type: Optional[str] = None,
    limit: int = Query(100, le=1000),
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get interactions with optional filters"""
    query = db.query(Activity, Member.name.label('from_member_name'))\
        .outerjoin(Member, Activity.member_from == Member.member_id)
    
    if member_id:
        query = query.filter(
            or_(Activity.member_from == member_id, Activity.member_to == member_id)
        )
    
    if date:
        query = query.filter(Activity.date == date)
    
    if interaction_type:
        query = query.filter(Activity.interaction == interaction_type)
    
    total = query.count()
    query = query.order_by(Activity.date, Activity.segment_id)
    results = query.limit(limit).offset(offset).all()
    
    items = []
    for activity, from_name in results:
        to_member = db.query(Member).filter(Member.member_id == activity.member_to).first()
        to_name = to_member.name if to_member else None
        
        items.append({
            "activityId": activity.activity_id,
            "date": activity.date,
            "segmentId": activity.segment_id,
            "memberFrom": activity.member_from,
            "memberTo": activity.member_to,
            "interactionType": activity.interaction,
            "fromMemberName": from_name,
            "toMemberName": to_name,
            "sentiment": activity.sentiment
        })
    
    return {
        "success": True,
        "message": "",
        "responseType": "interaction list",
        "total": total,
        "offsetStart": offset + 1 if total > 0 else 0,
        "offsetEnd": min(offset + len(items), total),
        "limit": limit,
        "result": {
            "items": items
        }
    }

@app.get("/interactions/{activity_id}")
@limiter.limit("60/minute")
def get_interaction(
    request: Request,
    activity_id: int,
    key: str = Depends(verify_api_key),  
    db: Session = Depends(get_db)
):
    """Get a specific interaction by ID"""
    result = db.query(Activity, Member.name.label('from_member_name'))\
        .outerjoin(Member, Activity.member_from == Member.member_id)\
        .filter(Activity.activity_id == activity_id).first()
    
    if result is None:
        return {
            "success": False,
            "message": "Interaction not found",
            "responseType": "interaction",
            "total": 0,
            "offsetStart": 0,
            "offsetEnd": 0,
            "limit": 1,
            "result": {}
        }
    
    activity, from_name = result
    to_member = db.query(Member).filter(Member.member_id == activity.member_to).first()
    to_name = to_member.name if to_member else None
    
    return {
        "success": True,
        "message": "",
        "responseType": "interaction",
        "total": 1,
        "offsetStart": 1,
        "offsetEnd": 1,
        "limit": 1,
        "result": {
            "activityId": activity.activity_id,
            "date": activity.date,
            "segmentId": activity.segment_id,
            "memberFrom": activity.member_from,
            "memberTo": activity.member_to,
            "interactionType": activity.interaction,
            "fromMemberName": from_name,
            "toMemberName": to_name,
            "sentiment": activity.sentiment
        }
    }