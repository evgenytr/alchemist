#!/usr/bin/env python3
"""
PostgreSQL setup script
"""

import os
import sys
from sqlalchemy import create_engine, text
from storage import Base, engine

def setup_database():
    """Create database tables and initial setup"""
    
    try:
        print("Creating PostgreSQL tables...")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        print("Tables created successfully!")
        
        # Create additional indexes for performance
        with engine.connect() as conn:
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_requests_status ON requests(status);",
                "CREATE INDEX IF NOT EXISTS idx_requests_username ON requests(username);", 
                "CREATE INDEX IF NOT EXISTS idx_requests_hostname ON requests(hostname);",
                "CREATE INDEX IF NOT EXISTS idx_requests_created_at ON requests(created_at);",
                "CREATE INDEX IF NOT EXISTS idx_requests_modified_at ON requests(modified_at);",
                "CREATE INDEX IF NOT EXISTS idx_requests_package ON requests(package);"
            ]
            
            for index_sql in indexes:
                try:
                    conn.execute(text(index_sql))
                    print(f"✓ Created index: {index_sql.split()[-1]}")
                except Exception as e:
                    print(f"✗ Failed to create index: {e}")
            
            conn.commit()
        
        print("Database setup completed successfully!")
        
    except Exception as e:
        print(f"Database setup failed: {e}")
        sys.exit(1)

def test_connection():
    """Test database connection"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✓ PostgreSQL connection successful!")
            print(f"  Database version: {version}")
            
            # Test table creation
            result = conn.execute(text("SELECT COUNT(*) FROM requests;"))
            count = result.fetchone()[0]
            print(f"  Requests table: {count} records")
            
    except Exception as e:
        print(f"✗ Connection test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("PostgreSQL Database Setup")
    print("=" * 30)
    
    # Check DATABASE_URL
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("Error: DATABASE_URL environment variable not set")
        print("Example: export DATABASE_URL='postgresql://user:password@localhost:5432/dbname'")
        sys.exit(1)
    
    print(f"Database URL: {db_url.split('@')[0]}@***")
    
    # Test connection first
    if test_connection():
        setup_database()
    else:
        print("Setup aborted due to connection failure")
        sys.exit(1)