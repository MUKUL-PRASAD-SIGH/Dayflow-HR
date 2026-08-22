import pymysql
from dotenv import load_dotenv
import os

def fix_database_schema():
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
        print("✓ Connected to database!")
        
        try:
            with connection.cursor() as cursor:
                # Check if users table needs to be altered
                print("\nChecking users table structure...")
                cursor.execute("SHOW COLUMNS FROM users LIKE 'name'")
                if not cursor.fetchone():
                    print("Adding 'name' column to users table...")
                    cursor.execute("""
                    ALTER TABLE users 
                    ADD COLUMN name VARCHAR(100) NOT NULL AFTER id,
                    MODIFY COLUMN id VARCHAR(50) NOT NULL,
                    MODIFY COLUMN gmail VARCHAR(100) NOT NULL,
                    MODIFY COLUMN password VARCHAR(100) NOT NULL,
                    MODIFY COLUMN role ENUM('employee', 'hr') NOT NULL
                    """)
                    print("✓ Added 'name' column to users table")
                
                # Check if leave_requests table exists and has correct structure
                print("\nChecking leave_requests table...")
                cursor.execute("SHOW TABLES LIKE 'leave_requests'")
                if not cursor.fetchone():
                    print("Creating leave_requests table...")
                    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS leave_requests (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id VARCHAR(50) NOT NULL,
                        start_date DATE NOT NULL,
                        end_date DATE NOT NULL,
                        reason TEXT NOT NULL,
                        status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """)
                    print("✓ Created leave_requests table")
                
                # Update existing users with default names if name is empty
                print("\nUpdating existing users with default names...")
                cursor.execute("""
                UPDATE users 
                SET name = CONCAT('User ', id)
                WHERE name IS NULL OR name = ''
                """)
                updated_rows = cursor.rowcount
                if updated_rows > 0:
                    print(f"✓ Updated {updated_rows} users with default names")
                
                # Commit changes
                connection.commit()
                print("\n✓ Database schema updated successfully!")
                
                # Show current users
                print("\nCurrent users:")
                cursor.execute("SELECT id, name, role FROM users")
                for user in cursor.fetchall():
                    print(f"- {user['id']}: {user['name']} ({user['role']})")
                
        except Exception as e:
            print(f"\n❌ Error: {e}")
            connection.rollback()
        finally:
            connection.close()
            
    except pymysql.Error as e:
        print(f"\n❌ Database error: {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    print("=== Database Schema Fixer ===\n")
    print("This script will fix the database schema issues.")
    confirm = input("Do you want to continue? (y/n): ")
    if confirm.lower() == 'y':
        fix_database_schema()
        print("\nPlease restart the application for changes to take effect.")
    else:
        print("Operation cancelled.")
