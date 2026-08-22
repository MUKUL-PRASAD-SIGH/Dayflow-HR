import pymysql
from dotenv import load_dotenv
import os

def test_mysql_connection():
    try:
        # Load environment variables
        load_dotenv()
        
        # Database configuration
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', 'mukulinblr#123'),
            'port': 3306,  # Default MySQL port
            'connect_timeout': 5  # 5 seconds timeout
        }
        
        print("Testing MySQL connection with these settings:")
        print(f"Host: {db_config['host']}")
        print(f"User: {db_config['user']}")
        print(f"Port: {db_config['port']}")
        
        # Try to connect
        print("\nAttempting to connect to MySQL server...")
        connection = pymysql.connect(**db_config)
        print("✓ Successfully connected to MySQL server!")
        
        # Check if database exists
        with connection.cursor() as cursor:
            cursor.execute("SHOW DATABASES")
            databases = [db[0] for db in cursor.fetchall()]
            print("\nAvailable databases:", ", ".join(databases) if databases else "No databases found")
            
            if 'hr_management' in databases:
                cursor.execute("USE hr_management")
                cursor.execute("SHOW TABLES")
                tables = [table[0] for table in cursor.fetchall()]
                print("\nTables in hr_management:", ", ".join(tables) if tables else "No tables found")
                
                if 'users' in tables:
                    cursor.execute("SELECT COUNT(*) as user_count FROM users")
                    count = cursor.fetchone()[0]
                    print(f"\nFound {count} users in the users table")
        
        connection.close()
        
    except pymysql.Error as e:
        print(f"\n✗ MySQL Error {e.args[0]}: {e.args[1]}")
        print("\nTroubleshooting tips:")
        print("1. Make sure MySQL server is running")
        print("2. Verify your MySQL credentials in the .env file")
        print("3. Check if MySQL is configured to accept connections")
        print("4. Try connecting with MySQL Workbench or MySQL CLI to verify credentials")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    test_mysql_connection()
