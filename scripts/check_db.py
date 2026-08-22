from db import connect_db

def check_database():
    try:
        # Test database connection
        con = connect_db()
        cursor = con.cursor()
        
        # Check if users table exists and show its structure
        cursor.execute("SHOW TABLES LIKE 'users'")
        if not cursor.fetchone():
            print("Error: 'users' table does not exist!")
            return
            
        # Show table structure
        print("\nUsers table structure:")
        cursor.execute("DESCRIBE users")
        for column in cursor.fetchall():
            print(column)
            
        # Show existing users
        print("\nExisting users:")
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        if not users:
            print("No users found in the database!")
        else:
            for user in users:
                print(user)
                
    except Exception as e:
        print(f"Error checking database: {e}")
    finally:
        if 'con' in locals() and con:
            con.close()

if __name__ == "__main__":
    check_database()
