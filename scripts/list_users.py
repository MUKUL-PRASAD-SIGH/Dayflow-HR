import pymysql
from dotenv import load_dotenv
import os

def list_users():
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
                # Get all users
                cursor.execute("SELECT * FROM users")
                users = cursor.fetchall()
                
                if not users:
                    print("No users found in the database!")
                    return
                
                print("\n=== Users in Database ===")
                for user in users:
                    print(f"\nID: {user.get('id')}")
                    print(f"Name: {user.get('name')}")
                    print(f"Email: {user.get('gmail')}")
                    print(f"Role: {user.get('role')}")
                    print(f"Password: {user.get('password')}")
                
                # Check login_attempts table if it exists
                try:
                    cursor.execute("SHOW TABLES LIKE 'login_attempts'")
                    if cursor.fetchone():
                        cursor.execute("SELECT * FROM login_attempts")
                        attempts = cursor.fetchall()
                        if attempts:
                            print("\n=== Login Attempts ===")
                            for attempt in attempts:
                                print(f"User ID: {attempt.get('user_id')}, Success: {attempt.get('success')}, Time: {attempt.get('attempt_time')}")
                except:
                    pass
                    
        finally:
            connection.close()
            
    except pymysql.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_users()
