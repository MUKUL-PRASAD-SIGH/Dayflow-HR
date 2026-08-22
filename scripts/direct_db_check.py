import pymysql
from dotenv import load_dotenv
import os

def check_database():
    try:
        # Load environment variables
        load_dotenv()
        
        # Database configuration
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', 'mukulinblr#123'),
            'database': os.getenv('DB_NAME', 'hr_management'),
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor
        }
        
        print("Connecting to database...")
        connection = pymysql.connect(**db_config)
        print("✓ Connected to database successfully!")
        
        try:
            with connection.cursor() as cursor:
                # Show databases
                print("\n=== Databases ===")
                cursor.execute("SHOW DATABASES")
                for db in cursor.fetchall():
                    print(f"- {db['Database']}")
                
                # Show tables in hr_management
                print("\n=== Tables in hr_management ===")
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                if not tables:
                    print("No tables found!")
                else:
                    for table in tables:
                        print(f"- {list(table.values())[0]}")
                
                # Check users table
                print("\n=== Users Table Structure ===")
                try:
                    cursor.execute("DESCRIBE users")
                    print("\nColumns in users table:")
                    for col in cursor.fetchall():
                        print(f"- {col['Field']} ({col['Type']})")
                except pymysql.Error as e:
                    print(f"Error describing users table: {e}")
                
                # Check users
                print("\n=== Users ===")
                try:
                    cursor.execute("SELECT * FROM users")
                    users = cursor.fetchall()
                    if not users:
                        print("No users found!")
                    else:
                        print("\nUser accounts:")
                        for user in users:
                            print(f"\nID: {user.get('id')}")
                            print(f"Name: {user.get('name')}")
                            print(f"Email: {user.get('gmail')}")
                            print(f"Role: {user.get('role')}")
                            print(f"Password: {user.get('password')}")
                except pymysql.Error as e:
                    print(f"Error fetching users: {e}")
                
                # Test logins
                print("\n=== Testing Logins ===")
                test_accounts = [
                    ('hr123', 'hr123'),
                    ('emp123', 'emp123'),
                    ('a', 'a')
                ]
                
                for user_id, password in test_accounts:
                    print(f"\nTesting login for {user_id}:")
                    try:
                        cursor.execute("SELECT * FROM users WHERE id = %s AND password = %s", (user_id, password))
                        user = cursor.fetchone()
                        if user:
                            print(f"✓ Login successful!")
                            print(f"   Name: {user.get('name')}")
                            print(f"   Role: {user.get('role')}")
                        else:
                            print("✗ Login failed!")
                            
                            # Check if user exists with different password
                            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                            if cursor.fetchone():
                                print("   (User exists but password doesn't match!)")
                            else:
                                print("   (User not found!)")
                                
                    except pymysql.Error as e:
                        print(f"Error during login test: {e}")
        
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
    print("=== Database Connection Checker ===\n")
    check_database()
    input("\nPress Enter to exit...")
