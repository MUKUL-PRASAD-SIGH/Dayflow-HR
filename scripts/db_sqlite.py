import sqlite3
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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

def init_database():
    """Initialize the database with tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        gmail TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT CHECK(role IN ('employee', 'hr')) NOT NULL,
        name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create leave_requests table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS leave_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        name TEXT,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        reason TEXT NOT NULL,
        status TEXT CHECK(status IN ('pending', 'approved', 'rejected')) DEFAULT 'pending',
        hr_comment TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)
    
    # Create test users
    test_users = [
        ('hr123', 'hr@example.com', 'hr123', 'hr', 'HR Manager'),
        ('emp123', 'employee@example.com', 'emp123', 'employee', 'Test Employee')
    ]
    
    for user in test_users:
        try:
            cursor.execute("""
            INSERT OR IGNORE INTO users (id, gmail, password, role, name)
            VALUES (?, ?, ?, ?, ?)
            """, user)
            print(f"Created user: {user[0]}")
        except Exception as e:
            print(f"User {user[0]} already exists or error: {e}")
    
    conn.commit()
    conn.close()
    print("\nDatabase initialized successfully!")
    print("\nTest users:")
    print("1. HR User - ID: hr123, Password: hr123")
    print("2. Employee User - ID: emp123, Password: emp123")

if __name__ == "__main__":
    init_database()
