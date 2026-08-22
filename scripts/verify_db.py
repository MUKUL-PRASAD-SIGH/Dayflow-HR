import pymysql
from dotenv import load_dotenv
import os

def verify_database():
    try:
        # Load environment variables
        load_dotenv()
        
        # Get database credentials
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'hr_management')
        }
        
        print("Connecting to database with config:", {**db_config, 'password': '***'})
        
        # Connect to MySQL
        con = pymysql.connect(**db_config)
        cursor = con.cursor()
        
        # Check if database exists
        cursor.execute("SHOW DATABASES LIKE %s", (db_config['database'],))
        if not cursor.fetchone():
            print(f"Error: Database '{db_config['database']}' does not exist!")
            return
            
        # Check tables
        print("\nTables in database:")
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        if not tables:
            print("No tables found in the database!")
            return
            
        for table in tables:
            table_name = table[0]
            print(f"\nTable: {table_name}")
            
            # Show table structure
            cursor.execute(f"DESCRIBE {table_name}")
            print("\nStructure:")
            for column in cursor.fetchall():
                print(f"  {column[0]} - {column[1]}")
            
            # Show table data
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            print(f"\nData ({len(rows)} rows):")
            for row in rows:
                print(f"  {row}")
        
    except pymysql.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'con' in locals() and con:
            con.close()

if __name__ == "__main__":
    verify_database()
