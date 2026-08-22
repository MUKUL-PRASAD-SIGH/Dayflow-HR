"""
Debug script for leave request functionality
"""
import pymysql
from dotenv import load_dotenv
import os
import sys

def connect_db():
    """Create a database connection"""
    try:
        load_dotenv()
        print("\n🔧 Database connection details:")
        print(f"Host: {os.getenv('DB_HOST', 'localhost')}")
        print(f"User: {os.getenv('DB_USER', 'root')}")
        print(f"Database: {os.getenv('DB_NAME', 'hrms')}")
        
        conn = pymysql.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'hrms'),
            cursorclass=pymysql.cursors.DictCursor
        )
        print("✅ Successfully connected to database")
        return conn
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        return None

def check_leave_requests(user_id=None):
    """Check leave requests for a specific user or all users"""
    conn = connect_db()
    if not conn:
        return
        
    try:
        with conn.cursor() as cursor:
            # Check if table exists
            cursor.execute("SHOW TABLES LIKE 'leave_requests'")
            if not cursor.fetchone():
                print("\n❌ Error: 'leave_requests' table does not exist")
                return
                
            # Get table structure
            print("\n📋 LEAVE_REQUESTS TABLE STRUCTURE:")
            cursor.execute("DESCRIBE leave_requests")
            for col in cursor.fetchall():
                print(f"  {col['Field']}: {col['Type']} {'(PK)' if col['Key'] == 'PRI' else ''}")
            
            # Get data
            query = "SELECT * FROM leave_requests"
            params = ()
            if user_id:
                query += " WHERE user_id = %s"
                params = (user_id,)
            query += " ORDER BY created_at DESC LIMIT 10"
            
            print(f"\n🔍 Running query: {query} {params if params else ''}")
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            if not rows:
                print("\nℹ️ No leave requests found" + (f" for user_id: {user_id}" if user_id else ""))
                return
                
            print(f"\n📝 Found {len(rows)} leave requests:")
            for i, row in enumerate(rows, 1):
                print(f"\n📌 Request #{i}:")
                for key, value in row.items():
                    print(f"  {key}: {value} ({type(value).__name__})")
                    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🔍 Leave Request Debug Tool")
    print("=" * 50)
    
    # Check if user_id was provided as command line argument
    user_id = None
    if len(sys.argv) > 1:
        user_id = sys.argv[1]
        print(f"Checking leave requests for user_id: {user_id}")
    
    check_leave_requests(user_id)
