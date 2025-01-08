#!/usr/bin/env python3

import sqlite3
import os
from datetime import datetime
from pathlib import Path

def init_database():
    """Initialize the database with the new schema and add test data."""
    db_path = "database/messages.db"
    
    # Create database directory if it doesn't exist
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Remove existing database if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # Create new database
    conn = sqlite3.connect(db_path)
    
    try:
        # Read and execute schema
        with open("database/schema_v2.sql") as f:
            conn.executescript(f.read())
        
        # Add test repositories
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO repositories (name, url, last_synced)
            VALUES (?, ?, ?)
        """, ("Test Repo 1", "https://github.com/test/repo1", datetime.utcnow().isoformat()))
        repo1_id = cursor.lastrowid
        
        cursor.execute("""
            INSERT INTO repositories (name, url, last_synced)
            VALUES (?, ?, ?)
        """, ("Test Repo 2", "https://github.com/test/repo2", datetime.utcnow().isoformat()))
        repo2_id = cursor.lastrowid
        
        # Add test messages
        test_messages = [
            (repo1_id, "Test message 1 from repo 1", datetime.utcnow().isoformat(), "TestUser1"),
            (repo1_id, "Test message 2 from repo 1", datetime.utcnow().isoformat(), "TestUser2"),
            (repo2_id, "Test message 1 from repo 2", datetime.utcnow().isoformat(), "TestUser1"),
            (repo2_id, "Test message 2 from repo 2", datetime.utcnow().isoformat(), "TestUser2"),
        ]
        
        cursor.executemany("""
            INSERT INTO messages (repository_id, content, timestamp, author)
            VALUES (?, ?, ?, ?)
        """, test_messages)
        
        conn.commit()
        print("Database initialized successfully at", db_path)
        print("Added test repositories and messages")
        
    except Exception as e:
        print("Error initializing database:", str(e))
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    init_database()
