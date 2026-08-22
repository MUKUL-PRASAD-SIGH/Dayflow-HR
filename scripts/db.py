import sqlite3
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'hr_management.db')

def connect_db():
    """Create and return a SQLite database connection"""
    try:
        connection = sqlite3.connect(DB_PATH)
        connection.row_factory = sqlite3.Row
        return connection
    except sqlite3.Error as e:
        print(f"Error connecting to SQLite: {e}")
        raise
