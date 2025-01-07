#!/usr/bin/env python3.9
import sqlite3
import os
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
        """Create the database and initialize it with the schema."""
        # Ensure database directory exists
        db_dir = os.path.dirname(self.db_path)
        Path(db_dir).mkdir(parents=True, exist_ok=True)
        
        # Connect to database (creates it if it doesn't exist)
        with sqlite3.connect(self.db_path) as conn:
            try:
                # Read schema file
                with open(self.schema_path, 'r') as f:
                    schema = f.read()
                
                # Execute schema
                conn.executescript(schema)
                conn.commit()
                print(f"Database initialized successfully at {self.db_path}")
                
            except sqlite3.Error as e:
                print(f"Error initializing database: {e}")
                raise
            except FileNotFoundError:
                print(f"Schema file not found at {self.schema_path}")
                raise

    def add_test_message(self) -> None:
        """Add a test message to verify the database is working."""
        with sqlite3.connect(self.db_path) as conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO messages (content, timestamp, author)
                    VALUES (?, ?, ?)
                """, ("Test message", "2025-01-07T15:33:47-05:00", "System"))
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
