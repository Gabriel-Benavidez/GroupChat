#!/usr/bin/env python3.9
import sqlite3
import os
from datetime import datetime, timezone
from pathlib import Path

class DatabaseInitializer:
    """Initialize the SQLite database with the required schema."""
    
    def __init__(self, db_path: str = "database/messages.db"):
        """
        Initialize the database connection.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.schema_path = "database/schema.sql"
        
    def init_database(self) -> None:
        """Initialize the database with the schema."""
        try:
            # Read schema
            with open(self.schema_path, 'r') as f:
                schema = f.read()

            # Connect to database
            with sqlite3.connect(self.db_path) as conn:
                # Drop existing tables if they exist
                conn.executescript("""
                    DROP TABLE IF EXISTS messages;
                    DROP TABLE IF EXISTS repositories;
                """)
                
                # Create fresh tables
                conn.executescript(schema)
                
                # Insert default repository
                conn.execute("""
                    INSERT INTO repositories (name, url) 
                    VALUES (?, ?)
                """, ('Default Repository', 'local'))
                
                # Insert test message
                timestamp = datetime.now(timezone.utc).isoformat()
                conn.execute("""
                    INSERT INTO messages (repository_id, content, timestamp, author, git_commit_hash)
                    VALUES (?, ?, ?, ?, ?)
                """, (1, 'Welcome to GroupChat!', timestamp, 'System', None))
                
                conn.commit()
                print("Database initialized successfully!")
                
        except Exception as e:
            print(f"Error initializing database: {str(e)}")
            raise

    def add_test_message(self) -> None:
        """Add a test message to verify the database is working."""
        with sqlite3.connect(self.db_path) as conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO messages (repository_id, content, timestamp, author, git_commit_hash)
                    VALUES (?, ?, ?, ?, ?)
                """, (1, "Test message", "2025-01-07T15:33:47-05:00", "System", None))
                conn.commit()
                print("Test message added successfully")
            except sqlite3.Error as e:
                print(f"Error adding test message: {e}")
                raise

def main():
    """Initialize the database and add a test message."""
    initializer = DatabaseInitializer()
    initializer.init_database()
    initializer.add_test_message()

if __name__ == "__main__":
    main()
