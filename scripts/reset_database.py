import pymysql
from dotenv import load_dotenv
import os

def reset_database():
    try:
        # Load environment variables
        load_dotenv()
        
        # Get database credentials (without database name first)
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor
        }
        
        print("Connecting to MySQL server...")
        
        # Connect to MySQL server (without database)
        connection = pymysql.connect(**db_config)
        
        try:
            with connection.cursor() as cursor:
                # Create database if not exists
                db_name = os.getenv('DB_NAME', 'hr_management')
                print(f"Creating database '{db_name}' if it doesn't exist...")
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                
                # Use the database
                cursor.execute(f"USE `{db_name}`")
                
                # Create users table
                print("Creating 'users' table...")
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS `users` (
                    `id` VARCHAR(50) NOT NULL,
                    `gmail` VARCHAR(100) NOT NULL,
                    `password` VARCHAR(100) NOT NULL,
                    `role` ENUM('employee', 'hr') NOT NULL,
                    `name` VARCHAR(100) NOT NULL,
                    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (`id`),
                    UNIQUE KEY `gmail` (`gmail`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
                # Create otp_verification table
                print("Creating 'otp_verification' table...")
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS `otp_verification` (
                    `email` VARCHAR(100) NOT NULL,
                    `otp` VARCHAR(10) NOT NULL,
                    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    `is_used` TINYINT(1) DEFAULT 0,
                    PRIMARY KEY (`email`),
                    KEY `created_at` (`created_at`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
                # Create leave_requests table
                print("Creating 'leave_requests' table...")
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS `leave_requests` (
                    `id` INT AUTO_INCREMENT PRIMARY KEY,
                    `user_id` VARCHAR(50) NOT NULL,
                    `start_date` DATE NOT NULL,
                    `end_date` DATE NOT NULL,
                    `reason` TEXT NOT NULL,
                    `status` ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
                    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
                # Create a test HR user
                test_hr = {
                    'id': 'hr123',
                    'gmail': 'hr@example.com',
                    'password': 'hr123',  # In production, always hash passwords!
                    'role': 'hr',
                    'name': 'HR Manager'
                }
                
                # Create a test employee user
                test_employee = {
                    'id': 'emp123',
                    'gmail': 'employee@example.com',
                    'password': 'emp123',  # In production, always hash passwords!
                    'role': 'employee',
                    'name': 'Test Employee'
                }
                
                print("Inserting test users...")
                for user in [test_hr, test_employee]:
                    # Check if user already exists
                    cursor.execute("SELECT id FROM users WHERE id = %s", (user['id'],))
                    if not cursor.fetchone():
                        cursor.execute(
                            """
                            INSERT INTO users (id, gmail, password, role, name)
                            VALUES (%(id)s, %(gmail)s, %(password)s, %(role)s, %(name)s)
                            """,
                            user
                        )
                        print(f"Created {user['role']} user: {user['id']}")
                    else:
                        print(f"User {user['id']} already exists, skipping...")
                
                # Commit changes
                connection.commit()
                print("\nDatabase setup completed successfully!")
                print("\nTest users:")
                print("1. HR User:")
                print(f"   ID: {test_hr['id']}")
                print(f"   Password: {test_hr['password']}")
                print("\n2. Employee User:")
                print(f"   ID: {test_employee['id']}")
                print(f"   Password: {test_employee['password']}")
                print("\nYou can now log in with these credentials.")
                
        finally:
            connection.close()
            
    except pymysql.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("=== Database Setup Script ===\n")
    print("This script will:")
    print("1. Create the database if it doesn't exist")
    print("2. Create all necessary tables")
    print("3. Create test users (HR and Employee)")
    print("\nWARNING: This will reset the database structure!")
    
    confirm = input("\nDo you want to continue? (yes/no): ")
    if confirm.lower() == 'yes':
        reset_database()
    else:
        print("Operation cancelled.")
