"""
Script to check the database structure and contents of the leave_requests table.
"""
import pymysql
from dotenv import load_dotenv
import os

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

def check_database():
    """Check the database structure and contents"""
    conn = None
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            # Check if table exists
            cursor.execute("SHOW TABLES LIKE 'leave_requests'")
            if not cursor.fetchone():
                print("❌ Error: 'leave_requests' table does not exist")
                return
            
            # Get table structure
            print("\n=== LEAVE_REQUESTS TABLE STRUCTURE ===")
            cursor.execute("DESCRIBE leave_requests")
            for col in cursor.fetchall():
                print(f"{col['Field']}: {col['Type']} {'(PK)' if col['Key'] == 'PRI' else ''}")
            
            # Get sample data
            print("\n=== SAMPLE DATA (5 most recent) ===")
            cursor.execute("""
                SELECT * FROM leave_requests 
                ORDER BY created_at DESC 
                LIMIT 5
            """)
            
            rows = cursor.fetchall()
            if not rows:
                print("No leave requests found in the database.")
                return
                
            for i, row in enumerate(rows, 1):
                print(f"\nRecord #{i}:")
                for key, value in row.items():
                    print(f"  {key}: {value} ({type(value).__name__})")
                    
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🔍 Checking database...")
    check_database()
