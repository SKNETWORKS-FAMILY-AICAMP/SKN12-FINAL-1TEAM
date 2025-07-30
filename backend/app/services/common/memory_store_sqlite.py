import sqlite3
import pathlib
import datetime as dt
import json
from typing import Optional, Dict

# [EMOJI] [EMOJI] database/history/memory.sqlite [EMOJI] [EMOJI]
_DB = pathlib.Path(__file__).parent.parent.parent.parent.parent / "database" / "history" / "memory.sqlite"

def _init():
    """[EMOJI] [EMOJI]"""
    # [EMOJI] [EMOJI] [EMOJI]
    _DB.parent.mkdir(parents=True, exist_ok=True)
    
    with sqlite3.connect(str(_DB)) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS memory(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            msg TEXT,
            meta TEXT,
            ts TEXT)""")
        db.commit()

# [EMOJI] [EMOJI]
_initialized = False

def ensure_initialized():
    """[EMOJI] [EMOJI] [EMOJI] [EMOJI]"""
    global _initialized
    if not _initialized:
        _init()
        _initialized = True

async def add_session(session_id: str):
    """[EMOJI] [EMOJI] ([EMOJI] [EMOJI] [EMOJI])"""
    ensure_initialized()

async def add_message(session_id: str, role: str, msg: str,
                      metadata: Optional[Dict] = None):
    """[EMOJI] [EMOJI]"""
    ensure_initialized()
        
    meta_txt = json.dumps(metadata or {})
    
    with sqlite3.connect(str(_DB)) as db:
        db.execute(
            "INSERT INTO memory(session_id, role, msg, meta, ts) "
            "VALUES(?,?,?,?,?)",
            (session_id, role, msg, meta_txt, dt.datetime.utcnow().isoformat())
        )
        db.commit()

def get_messages(session_id: str):
    """[EMOJI] [EMOJI] [EMOJI] [EMOJI]"""
    ensure_initialized()
        
    with sqlite3.connect(str(_DB)) as db:
        cursor = db.execute(
            "SELECT role, msg, meta, ts FROM memory WHERE session_id=? ORDER BY id",
            (session_id,)
        )
        return cursor.fetchall()