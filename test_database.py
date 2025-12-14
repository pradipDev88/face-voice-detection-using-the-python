"""
Test Database Connection for phpMyAdmin/MySQL
"""
import mysql.connector
from mysql.connector import Error

def test_connection():
    """Test MySQL connection"""
    print("="*60)
    print("🗄️ Testing MySQL Database Connection")
    print("="*60)
    
    # Default phpMyAdmin settings
    config = {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': '',  # Usually empty for XAMPP/WAMP
    }
    
    print("\n📋 Connection Settings:")
    print(f"   Host: {config['host']}")
    print(f"   Port: {config['port']}")
    print(f"   User: {config['user']}")
    print(f"   Password: {'(empty)' if not config['password'] else '***'}")
    
    # Test 1: Connect to MySQL server
    print("\n🔍 Test 1: Connecting to MySQL server...")
    try:
        connection = mysql.connector.connect(**config)
        if connection.is_connected():
            db_info = connection.get_server_info()
            print(f"✅ Connected to MySQL Server version {db_info}")
            
            # Test 2: Check if database exists
            print("\n🔍 Test 2: Checking for 'mr_beast_db' database...")
            cursor = connection.cursor()
            cursor.execute("SHOW DATABASES")
            databases = [db[0] for db in cursor.fetchall()]
            
            if 'mr_beast_db' in databases:
                print("✅ Database 'mr_beast_db' exists")
                
                # Test 3: Check tables
                print("\n🔍 Test 3: Checking tables...")
                cursor.execute("USE mr_beast_db")
                cursor.execute("SHOW TABLES")
                tables = [table[0] for table in cursor.fetchall()]
                
                if tables:
                    print(f"✅ Found {len(tables)} tables:")
                    for table in tables:
                        print(f"   - {table}")
                else:
                    print("⚠️ Database exists but no tables found")
                    print("   Run: mysql -u root < db/init_db.sql")
            else:
                print("❌ Database 'mr_beast_db' does not exist")
                print("\n📝 To create database:")
                print("   1. Open phpMyAdmin (http://localhost/phpmyadmin)")
                print("   2. Click 'New' to create database")
                print("   3. Name it: mr_beast_db")
                print("   4. Click 'Create'")
                print("   5. Go to 'Import' tab")
                print("   6. Choose file: db/init_db.sql")
                print("   7. Click 'Go'")
            
            cursor.close()
            connection.close()
            
            print("\n" + "="*60)
            print("✅ MySQL Connection Test Complete")
            print("="*60)
            return True
            
    except Error as e:
        print(f"❌ Connection Error: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Make sure XAMPP/WAMP is running")
        print("   2. Start MySQL service")
        print("   3. Check phpMyAdmin is accessible")
        print("   4. Verify username/password in config.yml")
        return False

def create_database_via_python():
    """Create database and tables via Python"""
    print("\n" + "="*60)
    print("🔨 Creating Database via Python")
    print("="*60)
    
    try:
        # Connect without database
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password=''
        )
        
        cursor = connection.cursor()
        
        # Create database
        print("\n📝 Creating database 'mr_beast_db'...")
        cursor.execute("CREATE DATABASE IF NOT EXISTS mr_beast_db")
        print("✅ Database created")
        
        # Use database
        cursor.execute("USE mr_beast_db")
        
        # Create tables
        print("\n📝 Creating tables...")
        
        # Table: user_info
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_info (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            age_range VARCHAR(32),
            gender VARCHAR(16),
            college_or_job VARCHAR(255),
            consent ENUM('Yes', 'No') DEFAULT 'No',
            first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_seen DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            conversation_count INT DEFAULT 0,
            avg_conversation_length FLOAT DEFAULT 0.0,
            engagement_score FLOAT DEFAULT 0.0,
            cluster_id INT DEFAULT NULL,
            INDEX idx_name (name),
            INDEX idx_last_seen (last_seen)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        print("✅ Table 'user_info' created")
        
        # Table: user_images
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_images (
            image_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            file_path VARCHAR(500),
            embedding TEXT,
            captured_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_primary BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (user_id) REFERENCES user_info(id) ON DELETE CASCADE,
            INDEX idx_user_id (user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        print("✅ Table 'user_images' created")
        
        # Table: conversation_log
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversation_log (
            log_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            speaker ENUM('User', 'Robot') NOT NULL,
            message TEXT NOT NULL,
            intent VARCHAR(100),
            confidence FLOAT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user_info(id) ON DELETE SET NULL,
            INDEX idx_user_id (user_id),
            INDEX idx_timestamp (timestamp)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        print("✅ Table 'conversation_log' created")
        
        # Table: user_behavior
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_behavior (
            behavior_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            session_date DATE,
            conversation_length INT DEFAULT 0,
            time_spent_seconds INT DEFAULT 0,
            speaking_speed FLOAT DEFAULT 0.0,
            confirmation_count INT DEFAULT 0,
            emotion_happy_count INT DEFAULT 0,
            emotion_neutral_count INT DEFAULT 0,
            emotion_sad_count INT DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES user_info(id) ON DELETE CASCADE,
            INDEX idx_user_id (user_id),
            INDEX idx_session_date (session_date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        print("✅ Table 'user_behavior' created")
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print("\n✅ Database setup complete!")
        return True
        
    except Error as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    # Test connection
    success = test_connection()
    
    if success:
        print("\n✅ Database is ready to use!")
    else:
        print("\n⚠️ Database not found. Would you like to create it?")
        response = input("Create database now? (y/n): ").strip().lower()
        
        if response == 'y':
            if create_database_via_python():
                print("\n✅ Database created successfully!")
                print("   You can now run: python main.py")
            else:
                print("\n❌ Failed to create database")
                print("   Please create manually via phpMyAdmin")
