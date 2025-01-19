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
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.schema_path = "database/schema.sql"
        
    def init_database(self) -> None:
        """Initialize the database with the schema."""
        try:
            # Read schema
            with open(self.schema_path, 'r') as f:
                schema = f.read()

            # Connect to database
            with sqlite3.connect(self.db_path) as conn:
                # Execute schema - tables will only be created if they don't exist
                conn.executescript(schema)
                
                # Insert default repository if it doesn't exist
                conn.execute("""
                    INSERT OR IGNORE INTO repositories (id, name, url) 
                    VALUES (1, 'Default Repository', 'local')
                """)
                
                # Check if we have any messages
                cursor = conn.execute("SELECT COUNT(*) as count FROM messages")
                message_count = cursor.fetchone()[0]
                
                # Only insert welcome message if there are no messages
                if message_count == 0:
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
    """Initialize the database."""
    initializer = DatabaseInitializer()
    initializer.init_database()

if __name__ == "__main__":
    main()
