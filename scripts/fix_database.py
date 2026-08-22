import pymysql
from dotenv import load_dotenv
import os

def fix_database():
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
                # Drop existing users table to start fresh
                print("Dropping existing users table...")
                cursor.execute("DROP TABLE IF EXISTS users")
                
                # Recreate users table with proper schema
                print("Creating new users table...")
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id VARCHAR(50) PRIMARY KEY,
                    gmail VARCHAR(100) UNIQUE NOT NULL,
                    password VARCHAR(100) NOT NULL,
                    role ENUM('employee', 'hr') NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
                # Insert test users with proper data
                test_users = [
                    {
                        'id': 'hr123',
                        'gmail': 'hr@example.com',
                        'password': 'hr123',
                        'role': 'hr',
                        'name': 'HR Manager'
                    },
                    {
                        'id': 'emp123',
                        'gmail': 'employee@example.com',
                        'password': 'emp123',
                        'role': 'employee',
                        'name': 'Test Employee'
                    },
                    {
                        'id': 'a',
                        'gmail': 'mukulprasad958@gmail.com',
                        'password': 'a',
                        'role': 'hr',
                        'name': 'Mukul Prasad'
                    }
                ]
                
                print("Inserting test users...")
                for user in test_users:
                    cursor.execute("""
                    INSERT INTO users (id, gmail, password, role, name)
                    VALUES (%(id)s, %(gmail)s, %(password)s, %(role)s, %(name)s)
                    """, user)
                
                connection.commit()
                print("\nDatabase has been reset with clean test users.")
                print("\nTest Users:")
                for user in test_users:
                    print(f"\nID: {user['id']}")
                    print(f"Name: {user['name']}")
                    print(f"Role: {user['role']}")
                    print(f"Email: {user['gmail']}")
                    print(f"Password: {user['password']}")
                
        except Exception as e:
            print(f"Error: {e}")
            connection.rollback()
        finally:
            connection.close()
            
    except pymysql.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("=== Database Reset Tool ===\n")
    print("WARNING: This will delete all existing user data and create new test users.")
    confirm = input("Do you want to continue? (y/n): ")
    if confirm.lower() == 'y':
        fix_database()
        print("\nPlease restart the Streamlit application to apply changes.")
    else:
        print("Operation cancelled.")
