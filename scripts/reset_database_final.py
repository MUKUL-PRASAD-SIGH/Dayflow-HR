import pymysql
from dotenv import load_dotenv
import os

def reset_database():
    try:
        # Load environment variables
        load_dotenv()
        
        # Database configuration (without database name first)
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', 'mukulinblr#123'),
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor
        }
        
        print("Connecting to MySQL server...")
        connection = pymysql.connect(**db_config)
        
        try:
            with connection.cursor() as cursor:
                # Drop database if exists
                db_name = os.getenv('DB_NAME', 'hr_management')
                print(f"Dropping database '{db_name}' if it exists...")
                cursor.execute(f"DROP DATABASE IF EXISTS `{db_name}`")
                
                # Create new database
                print(f"Creating new database '{db_name}'...")
                cursor.execute(f"CREATE DATABASE `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                cursor.execute(f"USE `{db_name}`")
                
                # Create users table
                print("Creating 'users' table...")
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS `users` (
                    `id` VARCHAR(50) PRIMARY KEY,
                    `gmail` VARCHAR(100) UNIQUE NOT NULL,
                    `password` VARCHAR(100) NOT NULL,
                    `role` ENUM('employee', 'hr') NOT NULL,
                    `name` VARCHAR(100) NOT NULL,
                    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
                # Create otp_verification table
                print("Creating 'otp_verification' table...")
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS `otp_verification` (
                    `email` VARCHAR(100) PRIMARY KEY,
                    `otp` VARCHAR(10) NOT NULL,
                    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    `is_used` TINYINT(1) DEFAULT 0
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
                
                # Insert test users
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
                
                print("\nInserting test users...")
                for user in test_users:
                    cursor.execute("""
                    INSERT INTO users (id, gmail, password, role, name)
                    VALUES (%(id)s, %(gmail)s, %(password)s, %(role)s, %(name)s)
                    """, user)
                    print(f"Added user: {user['id']} - {user['name']} ({user['role']})")
                
                connection.commit()
                print("\n=== Database reset successful! ===")
                print("\nTest users created:")
                print("1. HR User:")
                print("   ID: hr123")
                print("   Password: hr123")
                print("\n2. Employee User:")
                print("   ID: emp123")
                print("   Password: emp123")
                print("\n3. Your Account:")
                print("   ID: a")
                print("   Password: a")
                
        finally:
            connection.close()
            
    except pymysql.Error as e:
        print(f"\nDatabase error: {e}")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    print("=== HR Management System - Database Reset ===\n")
    print("WARNING: This will delete all existing data and create a fresh database.")
    confirm = input("Do you want to continue? (y/n): ")
    if confirm.lower() == 'y':
        reset_database()
        print("\nPlease restart the Streamlit application.")
    else:
        print("Operation cancelled.")
