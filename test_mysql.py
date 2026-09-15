import sys
from config import load_config
from database import get_db

def main():
    print("=" * 60)
    print("TESTING DATABASE CONNECTION")
    print("=" * 60)
    
    cfg = load_config()
    db = get_db()
    
    print(f"Configured DB_TYPE: {cfg.get('DB_TYPE')}")
    print(f"MySQL Configuration: {cfg.get('MYSQL')}")
    print(f"Active Backend: {db.active_db.upper()}")
    
    if db.mysql_error:
        print(f"MySQL Connection Error: {db.mysql_error}")
    
    m = cfg.get("MYSQL", {})
    success, msg = db.test_mysql_connection(
        host=m.get("host", "localhost"),
        port=m.get("port", 3306),
        user=m.get("user", "root"),
        password=m.get("password", ""),
        database=m.get("database", "smart_class_db")
    )
    print(f"\nDirect MySQL Test Result:")
    print(f"  Success: {success}")
    print(f"  Message: {msg}")
    print("=" * 60)

if __name__ == "__main__":
    main()
