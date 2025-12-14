"""
Database Connection Module
Handles MySQL database connections
"""
import mysql.connector
from mysql.connector import Error
import yaml
import os

class DatabaseConnection:
    """Manages MySQL database connections"""
    
    def __init__(self, config_path='config.yml'):
        """Initialize database connection"""
        self.connection = None
        self.config = self.load_config(config_path)
        self.connect()
    
    def load_config(self, config_path):
        """Load database configuration from YAML"""
        try:
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
                return config['database']
        except Exception as e:
            print(f"Error loading config: {e}")
            # Default configuration
            return {
                'host': 'localhost',
                'port': 3306,
                'user': 'root',
                'password': '',
                'database': 'mr_beast_db'
            }
    
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = mysql.connector.connect(
                host=self.config['host'],
                port=self.config['port'],
                user=self.config['user'],
                password=self.config['password'],
                database=self.config['database']
            )
            
            if self.connection.is_connected():
                print("✓ Database connected successfully")
                return True
        except Error as e:
            print(f"✗ Database connection error: {e}")
            print("  Make sure MySQL is running and database exists")
            print("  Run: mysql -u root < db/init_db.sql")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("✓ Database disconnected")
    
    def execute_query(self, query, params=None):
        """Execute a query (INSERT, UPDATE, DELETE)"""
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            self.connection.commit()
            return cursor.lastrowid
        except Error as e:
            print(f"Query execution error: {e}")
            return None
        finally:
            cursor.close()
    
    def fetch_one(self, query, params=None):
        """Fetch single result"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            result = cursor.fetchone()
            return result
        except Error as e:
            print(f"Fetch error: {e}")
            return None
        finally:
            cursor.close()
    
    def fetch_all(self, query, params=None):
        """Fetch all results"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            results = cursor.fetchall()
            return results
        except Error as e:
            print(f"Fetch error: {e}")
            return []
        finally:
            cursor.close()
    
    def is_connected(self):
        """Check if database is connected"""
        return self.connection and self.connection.is_connected()

# Singleton instance
_db_instance = None

def get_db():
    """Get database connection instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseConnection()
    return _db_instance
