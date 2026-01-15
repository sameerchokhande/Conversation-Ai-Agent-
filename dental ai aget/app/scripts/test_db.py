from app.db.connection import get_db

def main():
    conn = get_db()
    if conn:
        print("✅ Connection successful!")
        conn.close()
    else:
        print("❌ Connection failed!")

if __name__ == "__main__":
    main()
