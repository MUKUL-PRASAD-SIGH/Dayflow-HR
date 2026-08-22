import pymysql
from dotenv import load_dotenv
import os
import sys

def debug_login():
    try:
        # Load environment variables
        print("Loading environment variables...")
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        load_dotenv(env_path)
        
        # Print environment variables (for debugging)
        print("\nEnvironment variables:")
        print(f"DB_HOST: {os.getenv('DB_HOST')}")
        print(f"DB_USER: {os.getenv('DB_USER')}")
        print(f"DB_PASSWORD: {'*' * len(os.getenv('DB_PASSWORD', '')) if os.getenv('DB_PASSWORD') else 'Not set'}")
        print(f"DB_NAME: {os.getenv('DB_NAME')}")
        
        # Database configuration
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', 'mukulinblr#123'),
            'database': os.getenv('DB_NAME', 'hr_management'),
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor
        }
        
        print("\nAttempting to connect to database...")
        connection = pymysql.connect(**db_config)
        print("✓ Successfully connected to database!")
        
        try:
            with connection.cursor() as cursor:
                # Check if users table exists
                cursor.execute("SHOW TABLES LIKE 'users'")
                if not cursor.fetchone():
                    print("\n❌ Error: 'users' table does not exist!")
                    return
                
                # List all tables
                print("\nTables in the database:")
                cursor.execute("SHOW TABLES")
                for table in cursor.fetchall():
                    print(f"- {list(table.values())[0]}")
                
                # Check users table structure
                print("\nUsers table structure:")
                cursor.execute("DESCRIBE users")
                for column in cursor.fetchall():
                    print(f"{column['Field']}: {column['Type']} {'' if column['Null'] == 'YES' else 'NOT NULL'}")
                
                # List all users
                print("\nUsers in the database:")
                cursor.execute("SELECT * FROM users")
                users = cursor.fetchall()
                
                if not users:
                    print("No users found in the database!")
                else:
                    for user in users:
                        print(f"\nID: {user.get('id')}")
                        print(f"Name: {user.get('name')}")
                        print(f"Email: {user.get('gmail')}")
                        print(f"Role: {user.get('role')}")
                        print(f"Password: {user.get('password')}")
                
                # Test login with hardcoded credentials
                test_credentials = [
                    ('hr123', 'hr123'),
                    ('emp123', 'emp123'),
                    ('a', 'a')
                ]
                
                print("\nTesting login with credentials:")
                for user_id, password in test_credentials:
                    print(f"\nTesting login for {user_id}:")
                    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                    user = cursor.fetchone()
                    
                    if user:
                        print(f"✓ User found: {user.get('id')} - {user.get('name')}")
                        if user.get('password') == password:
                            print("✓ Password matches!")
                        else:
                            print(f"❌ Password mismatch! Stored: {user.get('password')}, Provided: {password}")
                    else:
                        print(f"❌ User not found: {user_id}")
        
        finally:
            connection.close()
            
    except pymysql.Error as e:
        print(f"\n❌ Database error: {e}")
        print(f"Error code: {e.args[0]}")
        print(f"Error message: {e.args[1]}")
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=== Login Debugger ===\n")
    debug_login()
    input("\nPress Enter to exit...")
