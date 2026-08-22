"""
Diagnostic script to check the leave_requests table structure and sample data.
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

def check_table_structure():
    """Check the structure of the leave_requests table"""
    conn = None
    cursor = None
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        # Get table structure
        cursor.execute("DESCRIBE leave_requests")
        columns = cursor.fetchall()
        
        print("\n=== LEAVE_REQUESTS TABLE STRUCTURE ===")
        for col in columns:
            print(f"{col['Field']}: {col['Type']} {'(PK)' if col['Key'] == 'PRI' else ''}")
        
        # Get sample data
        cursor.execute("SELECT * FROM leave_requests ORDER BY created_at DESC LIMIT 3")
        sample_data = cursor.fetchall()
        
        print("\n=== SAMPLE DATA (3 most recent) ===")
        for i, row in enumerate(sample_data, 1):
            print(f"\nRecord #{i}:")
            for key, value in row.items():
                print(f"  {key}: {value} ({type(value).__name__})")
        
    except Exception as e:
        print(f"\n❌ Error checking table structure: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🔍 Checking leave_requests table...")
    check_table_structure()
