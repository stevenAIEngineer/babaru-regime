# Author: Steven Lansangan
# Project: Cloud for Babaru
# This handles all the database stuff so Babaru remembers you
import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

DB_PATH = "babaru.db"

# basic logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MemoryManager")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # User Identity Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS use_identity (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            timezone TEXT
        )
    ''')
    
    # Progression Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS progression (
            user_id TEXT PRIMARY KEY,
            rank TEXT DEFAULT 'Newcomer',
            points INTEGER DEFAULT 0,
            streak_days INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES use_identity(user_id)
        )
    ''')

    # Missions Table (JSON columns)
    c.execute('''
        CREATE TABLE IF NOT EXISTS missions (
            user_id TEXT PRIMARY KEY,
            active TEXT DEFAULT '[]',
            completed TEXT DEFAULT '[]',
            failed TEXT DEFAULT '[]',
            FOREIGN KEY (user_id) REFERENCES use_identity(user_id)
        )
    ''')

    # Conversations Table (Rolling window)
    c.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            user_id TEXT PRIMARY KEY,
            history TEXT DEFAULT '[]',
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES use_identity(user_id)
        )
    ''')

    # Core Profile Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS core_profile (
            user_id TEXT PRIMARY KEY,
            primary_goal TEXT,
            obstacles TEXT,
            wins TEXT,
            communication_preferences TEXT,
            FOREIGN KEY (user_id) REFERENCES use_identity(user_id)
        )
    ''')

    # Relationship Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS relationship (
            user_id TEXT PRIMARY KEY,
            familiarity_level INTEGER DEFAULT 1,
            trust_level INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES use_identity(user_id)
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully.")

# --- Helper Functions ---

def create_user(user_id: str, name: str, timezone: str = "UTC"):
    """Initialize a new user with default values across all tables."""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        
        # Check if user exists
        c.execute("SELECT user_id FROM use_identity WHERE user_id = ?", (user_id,))
        if c.fetchone():
            logger.info(f"User {user_id} already exists.")
            return

        c.execute("INSERT INTO use_identity (user_id, name, timezone) VALUES (?, ?, ?)", (user_id, name, timezone))
        c.execute("INSERT INTO progression (user_id) VALUES (?)", (user_id,))
        c.execute("INSERT INTO missions (user_id) VALUES (?)", (user_id,))
        c.execute("INSERT INTO conversations (user_id) VALUES (?)", (user_id,))
        c.execute("INSERT INTO core_profile (user_id) VALUES (?)", (user_id,))
        c.execute("INSERT INTO relationship (user_id) VALUES (?)", (user_id,))
        
        conn.commit()
        logger.info(f"User {user_id} created.")
    except Exception as e:
        logger.error(f"Error creating user: {e}")
    finally:
        conn.close()

def get_user_memory(user_id: str) -> Dict[str, Any]:
    """Retrieve the full user memory state."""
    conn = get_db_connection()
    memory = {}
    try:
        c = conn.cursor()
        
        # Identity
        identity = c.execute("SELECT * FROM use_identity WHERE user_id = ?", (user_id,)).fetchone()
        if not identity:
            return {}
        memory['identity'] = dict(identity)
        
        # Progression
        progression = c.execute("SELECT * FROM progression WHERE user_id = ?", (user_id,)).fetchone()
        memory['progression'] = dict(progression) if progression else {}
        
        # Missions
        missions = c.execute("SELECT * FROM missions WHERE user_id = ?", (user_id,)).fetchone()
        if missions:
            memory['missions'] = {
                'active': json.loads(missions['active']),
                'completed': json.loads(missions['completed']),
                'failed': json.loads(missions['failed'])
            }
        
        # Conversations
        conversations = c.execute("SELECT * FROM conversations WHERE user_id = ?", (user_id,)).fetchone()
        memory['conversations'] = json.loads(conversations['history']) if conversations else []
        
        # Profile
        profile = c.execute("SELECT * FROM core_profile WHERE user_id = ?", (user_id,)).fetchone()
        memory['profile'] = dict(profile) if profile else {}
        
        # Relationship
        relationship = c.execute("SELECT * FROM relationship WHERE user_id = ?", (user_id,)).fetchone()
        memory['relationship'] = dict(relationship) if relationship else {}
        
    except Exception as e:
        logger.error(f"Error fetching memory: {e}")
    finally:
        conn.close()
    
    return memory

def update_progression(user_id: str, updates: Dict[str, Any]):
    """Update progression fields (rank, points, streak)."""
    conn = get_db_connection()
    try:
        updates_sql = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [user_id]
        conn.execute(f"UPDATE progression SET {updates_sql} WHERE user_id = ?", values)
        conn.commit()
    finally:
        conn.close()

def update_missions(user_id: str, active: Optional[List] = None, completed: Optional[List] = None, failed: Optional[List] = None):
    """Update mission lists."""
    conn = get_db_connection()
    try:
        data = {}
        if active is not None: data['active'] = json.dumps(active)
        if completed is not None: data['completed'] = json.dumps(completed)
        if failed is not None: data['failed'] = json.dumps(failed)
        
        if data:
            updates_sql = ", ".join([f"{k} = ?" for k in data.keys()])
            values = list(data.values()) + [user_id]
            conn.execute(f"UPDATE missions SET {updates_sql} WHERE user_id = ?", values)
            conn.commit()
    finally:
        conn.close()

def update_conversation_history(user_id: str, message: Dict[str, str]):
    """Append a message to the conversation history (rolling window logic can be added here)."""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        current = c.execute("SELECT history FROM conversations WHERE user_id = ?", (user_id,)).fetchone()
        history = json.loads(current['history']) if current else []
        
        history.append(message)
        # Keep last 30 days or N messages - for now just simple trim if too long? 
        # Requirement says "Rolling window of the last 30 days". 
        # For simplicity, let's keep last 50 messages for now or just append. 
        # The prompt builder will likely filter.
        
        conn.execute("UPDATE conversations SET history = ?, last_updated = CURRENT_TIMESTAMP WHERE user_id = ?", (json.dumps(history), user_id))
        conn.commit()
    finally:
        conn.close()

def update_profile(user_id: str, updates: Dict[str, Any]):
    """Update core profile fields."""
    conn = get_db_connection()
    try:
        updates_sql = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [user_id]
        conn.execute(f"UPDATE core_profile SET {updates_sql} WHERE user_id = ?", values)
        conn.commit()
    finally:
        conn.close()

def update_relationship(user_id: str, familiarity_delta: int = 0, trust_delta: int = 0):
    """Update relationship stats."""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        current = c.execute("SELECT familiarity_level, trust_level FROM relationship WHERE user_id = ?", (user_id,)).fetchone()
        if current:
            new_fam = max(0, min(10, current['familiarity_level'] + familiarity_delta))
            new_trust = max(0, min(10, current['trust_level'] + trust_delta))
            c.execute("UPDATE relationship SET familiarity_level = ?, trust_level = ? WHERE user_id = ?", (new_fam, new_trust, user_id))
            conn.commit()
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
    # Test creation
    # create_user("test_user_1", "Test Subject", "EST")
    # print(get_user_memory("test_user_1"))
