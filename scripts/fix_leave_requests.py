import pymysql
from db import connect_db

def check_leave_requests_schema():
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            # Check if the table exists
            cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'leave_requests';
            """)
            columns = cursor.fetchall()
            
            if not columns:
                print("Table 'leave_requests' does not exist.")
                return False
                
            print("Current leave_requests table structure:")
            for col in columns:
                print(f"- {col['COLUMN_NAME']} ({col['DATA_TYPE']}) {'NULL' if col['IS_NULLABLE'] == 'YES' else 'NOT NULL'} "
                      f"DEFAULT {col['COLUMN_DEFAULT'] if col['COLUMN_DEFAULT'] is not None else 'NULL'}")
            
            return True
            
    except Exception as e:
        print(f"Error checking schema: {e}")
        return False
    finally:
        if conn:
            conn.close()

def update_leave_requests_schema():
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            # Check if the name column exists
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'leave_requests' 
                AND COLUMN_NAME = 'name';
            """)
            result = cursor.fetchone()
            
            if result['count'] == 0:
                print("Adding 'name' column to leave_requests table...")
                cursor.execute("""
                    ALTER TABLE leave_requests
                    ADD COLUMN name VARCHAR(100) AFTER user_id;
                """)
                
                # Update existing records with user names
                print("Updating existing records with user names...")
                cursor.execute("""
                    UPDATE leave_requests lr
                    JOIN users u ON lr.user_id = u.id
                    SET lr.name = u.name;
                """)
                
                conn.commit()
                print("Successfully updated leave_requests table schema.")
            else:
                print("'name' column already exists in leave_requests table.")
            
    except Exception as e:
        print(f"Error updating schema: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("Checking current schema...")
    if check_leave_requests_schema():
        print("\nUpdating schema if needed...")
        update_leave_requests_schema()
    else:
        print("Could not check schema. Table may not exist.")
        print("Please ensure the leave_requests table exists with the correct structure.")
