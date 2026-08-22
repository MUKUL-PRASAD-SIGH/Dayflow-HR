"""
This script ensures the leave_requests table has all required columns.
Run this script to update the database schema if needed.
"""
import pymysql
import os
from dotenv import load_dotenv

def connect_db():
    """Create a database connection"""
    load_dotenv()
    return pymysql.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'hrms'),
        cursorclass=pymysql.cursors.DictCursor
    )

def update_schema():
    """Update the leave_requests table schema if needed"""
    conn = None
    cursor = None
    
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leave_requests (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(50) NOT NULL,
                name VARCHAR(100) NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                reason TEXT NOT NULL,
                status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
                hr_comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        
        # Check for missing columns and add them if needed
        cursor.execute("SHOW COLUMNS FROM leave_requests LIKE 'hr_comment'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE leave_requests ADD COLUMN hr_comment TEXT AFTER status")
            print("✅ Added missing column: hr_comment")
            
        cursor.execute("SHOW COLUMNS FROM leave_requests LIKE 'created_at'")
        if not cursor.fetchone():
            cursor.execute("""
                ALTER TABLE leave_requests 
                ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """)
            print("✅ Added missing column: created_at")
            
        cursor.execute("SHOW COLUMNS FROM leave_requests LIKE 'updated_at'")
        if not cursor.fetchone():
            cursor.execute("""
                ALTER TABLE leave_requests 
                ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            """)
            print("✅ Added missing column: updated_at")
            
        # Add foreign key if it doesn't exist
        cursor.execute("""
            SELECT TABLE_NAME, COLUMN_NAME, CONSTRAINT_NAME, 
                   REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE TABLE_NAME = 'leave_requests' 
            AND CONSTRAINT_NAME != 'PRIMARY'
        """)
        if not cursor.fetchone():
            cursor.execute("""
                ALTER TABLE leave_requests
                ADD CONSTRAINT fk_user_id
                FOREIGN KEY (user_id) REFERENCES users(id)
                ON DELETE CASCADE
            """)
            print("✅ Added foreign key constraint for user_id")
            
        conn.commit()
        print("✅ Database schema is up to date!")
        
    except Exception as e:
        print(f"❌ Error updating schema: {str(e)}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🔍 Checking database schema...")
    update_schema()
