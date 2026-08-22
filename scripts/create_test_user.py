from db import connect_db
import pymysql

def create_test_user():
    try:
        con = connect_db()
        cursor = con.cursor()
        
        # Test user details
        user_data = {
            'id': 'test123',
            'gmail': 'test@example.com',
            'password': 'test123',  # In production, always hash passwords!
            'role': 'hr',  # or 'employee'
            'name': 'Test User'
        }
        
        # Insert user
        cursor.execute(
            """
            INSERT INTO users (id, gmail, password, role, name)
            VALUES (%(id)s, %(gmail)s, %(password)s, %(role)s, %(name)s)
            """,
            user_data
        )
        con.commit()
        print("Test user created successfully!")
        print(f"ID: {user_data['id']}")
        print(f"Password: {user_data['password']}")
        
    except pymysql.IntegrityError:
        print("Error: User with this ID or email already exists.")
    except Exception as e:
        print(f"Error creating test user: {e}")
    finally:
        if 'con' in locals() and con:
            con.close()

if __name__ == "__main__":
    create_test_user()
