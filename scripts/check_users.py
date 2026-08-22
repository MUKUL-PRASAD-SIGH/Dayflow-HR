import pymysql
from dotenv import load_dotenv
import os

def check_users():
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
        
        try:
            with connection.cursor() as cursor:
                # Check if users table exists
                cursor.execute("SHOW TABLES LIKE 'users'")
                if not cursor.fetchone():
                    print("Error: 'users' table does not exist!")
                    return
                
                # Print all users
                print("\nUsers in database:")
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
                        
        finally:
            connection.close()
            
    except pymysql.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_users()
