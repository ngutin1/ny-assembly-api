from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from typing import List, Optional
from pydantic import BaseModel

app = FastAPI(title="NY Assembly API")
DATABASE = "test_assembly.db"

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Return rows as dicts
    return conn


class Member(BaseModel):
    member_id: int
    name: str
    district: Optional[int] = None
    session_year: Optional[int] = None

class Transcript(BaseModel):
    date: str
    text: str

class TranscriptSegment(BaseModel):
    segment_id: int
    date: str
    sequence_number: int
    member_id: int
    text: str

class Activity(BaseModel):
    activity_id: int
    date: str
    segment_id: int
    member_from: int
    member_to: int
    interaction: str

@app.get("/")
def root():
    return {
        "message": "NY Assembly Transcript API",
        "version": "1.0",
        "endpoints": {
            "members": "/members",
            "transcripts": "/transcripts",
            "segments": "/segments",
            "interactions": "/interactions"
        }
    }

#members
@app.get("/members", response_model=List[Member])
def get_members(
    session_year: Optional[int] = None,
    district: Optional[int] = None
):
    """Get all members, optionally filtered by session year or district"""
    conn = get_db()
    cursor = conn.cursor()
    
    query = "SELECT * FROM members WHERE 1=1"
    params = []
    
    if session_year:
        query += " AND session_year = ?"
        params.append(session_year)
    
    if district:
        query += " AND district = ?"
        params.append(district)
    
    query += " ORDER BY name"
    
    cursor.execute(query, params)
    members = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return members

@app.get("/members/{member_id}", response_model=Member)
def get_member(member_id: int):
    """Get a specific member by ID"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM members WHERE member_id = ?", (member_id,))
    member = cursor.fetchone()
    conn.close()
    
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")
    return dict(member)


# transcripits
@app.get("/transcripts")
def get_all_transcripts():
    """Get list of all available transcript dates"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT date FROM transcripts ORDER BY date DESC")
    dates = [row[0] for row in cursor.fetchall()]
    conn.close()
    return {"dates": dates, "count": len(dates)}

@app.get("/transcripts/{date}")
def get_transcript(date: str):
    """Get full transcript for a specific date"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transcripts WHERE date = ?", (date,))
    transcript = cursor.fetchone()
    conn.close()
    
    if transcript is None:
        raise HTTPException(status_code=404, detail="Transcript not found")
    return dict(transcript)

# segments

@app.get("/segments")
def get_segments(
    date: Optional[str] = None,
    member_id: Optional[int] = None,
    limit: int = Query(100, le=1000),
    offset: int = 0
):
    """Get transcript segments with optional filters"""
    conn = get_db()
    cursor = conn.cursor()
    
    query = """
        SELECT ts.*, m.name as member_name
        FROM transcript_segments ts
        LEFT JOIN members m ON ts.member_id = m.member_id
        WHERE 1=1
    """
    params = []
    
    if date:
        query += " AND ts.date = ?"
        params.append(date)
    
    if member_id:
        query += " AND ts.member_id = ?"
        params.append(member_id)
    
    query += " ORDER BY ts.date, ts.sequence_number LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    segments = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return segments

@app.get("/segments/{segment_id}")
def get_segment(segment_id: int):
    """Get a specific segment by ID"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ts.*, m.name as member_name
        FROM transcript_segments ts
        LEFT JOIN members m ON ts.member_id = m.member_id
        WHERE ts.segment_id = ?
    """, (segment_id,))
    segment = cursor.fetchone()
    conn.close()
    
    if segment is None:
        raise HTTPException(status_code=404, detail="Segment not found")
    return dict(segment)

# interactions 

@app.get("/interactions")
def get_interactions(
    member_id: Optional[int] = None,
    date: Optional[str] = None,
    interaction_type: Optional[str] = None,
    limit: int = Query(100, le=1000),
    offset: int = 0
):
    """Get interactions with optional filters"""
    conn = get_db()
    cursor = conn.cursor()
    
    query = """
        SELECT a.*, 
               m1.name as from_member_name,
               m2.name as to_member_name
        FROM activity a
        LEFT JOIN members m1 ON a.member_from = m1.member_id
        LEFT JOIN members m2 ON a.member_to = m2.member_id
        WHERE 1=1
    """
    params = []
    
    if member_id:
        query += " AND (a.member_from = ? OR a.member_to = ?)"
        params.extend([member_id, member_id])
    
    if date:
        query += " AND a.date = ?"
        params.append(date)
    
    if interaction_type:
        query += " AND a.interaction = ?"
        params.append(interaction_type)
    
    query += " ORDER BY a.date, a.segment_id LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    interactions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return interactions

@app.get("/interactions/{activity_id}")
def get_interaction(activity_id: int):
    """Get a specific interaction by ID"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.*, 
               m1.name as from_member_name,
               m2.name as to_member_name
        FROM activity a
        LEFT JOIN members m1 ON a.member_from = m1.member_id
        LEFT JOIN members m2 ON a.member_to = m2.member_id
        WHERE a.activity_id = ?
    """, (activity_id,))
    interaction = cursor.fetchone()
    conn.close()
    
    if interaction is None:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return dict(interaction)