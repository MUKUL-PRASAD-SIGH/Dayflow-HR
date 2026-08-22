"""
Script to check and create necessary database tables
"""
import pymysql
from dotenv import load_dotenv
import os

def get_db_connection():
    """Create a database connection"""
    load_dotenv()
    try:
        conn = pymysql.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'hrms')
        )
        print("✅ Successfully connected to database")
        return conn
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return None

def check_and_create_tables():
    """Check and create necessary tables"""
    conn = get_db_connection()
    if not conn:
        return

    try:
        with conn.cursor() as cursor:
            # Create leave_requests table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS leave_requests (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id VARCHAR(50) NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    reason TEXT NOT NULL,
                    status ENUM('pending', 'approved', 'rejected', 'cancelled') DEFAULT 'pending',
                    hr_comment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            print("✅ leave_requests table is ready")
            
            # Create users table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id VARCHAR(50) PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    gmail VARCHAR(100) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    role ENUM('employee', 'hr') NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ users table is ready")
            
            conn.commit()
            print("\n✅ Database setup completed successfully!")
            
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
    finally:
        if conn and conn.open:
            conn.close()

if __name__ == "__main__":
    print("🔍 Checking and setting up database tables...")
    check_and_create_tables()
