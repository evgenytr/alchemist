#!/usr/bin/env python3
"""
Migration script to move data from MariaDB to PostgreSQL
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import uuid
from datetime import datetime

# Old MariaDB configuration
MARIADB_URL = os.getenv('MARIADB_URL', 'mysql+pymysql://user:password@localhost:3306/old_db')

# New PostgreSQL configuration  
POSTGRES_URL = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/new_db')

def migrate_data():
    """Migrate data from MariaDB to PostgreSQL"""
    
    # Create engines
    mariadb_engine = create_engine(MARIADB_URL)
    postgres_engine = create_engine(POSTGRES_URL)
    
    # Create sessions
    MariaDBSession = sessionmaker(bind=mariadb_engine)
    PostgresSession = sessionmaker(bind=postgres_engine)
    
    mariadb_session = MariaDBSession()
    postgres_session = PostgresSession()
    
    try:
        # Create PostgreSQL tables first
        from storage import Base
        Base.metadata.create_all(bind=postgres_engine)
        
        # Fetch data from MariaDB
        print("Fetching data from MariaDB...")
        mariadb_requests = mariadb_session.execute(
            text("SELECT id, created_at, modified_at, package, status, username, hostname, ip FROM requests")
        ).fetchall()
        
        print(f"Found {len(mariadb_requests)} records to migrate")
        
        # Insert data into PostgreSQL
        for row in mariadb_requests:
            # Convert string UUID to proper UUID if needed
            id_value = row.id
            if isinstance(id_value, str):
                try:
                    id_value = uuid.UUID(id_value)
                except ValueError:
                    # Generate new UUID if invalid
                    id_value = uuid.uuid4()
                    print(f"Generated new UUID for invalid ID: {row.id}")
            
            # Insert into PostgreSQL
            postgres_session.execute(
                text("""
                    INSERT INTO requests (id, created_at, modified_at, package, status, username, hostname, ip)
                    VALUES (:id, :created_at, :modified_at, :package, :status, :username, :hostname, :ip)
                    ON CONFLICT (id) DO NOTHING
                """),
                {
                    'id': id_value,
                    'created_at': row.created_at,
                    'modified_at': row.modified_at,
                    'package': row.package,
                    'status': row.status,
                    'username': row.username,
                    'hostname': row.hostname,
                    'ip': row.ip
                }
            )
        
        postgres_session.commit()
        print("Migration completed successfully!")
        
        # Verify migration
        count = postgres_session.execute(text("SELECT COUNT(*) FROM requests")).scalar()
        print(f"PostgreSQL now contains {count} records")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        postgres_session.rollback()
        raise
    finally:
        mariadb_session.close()
        postgres_session.close()

def create_indexes():
    """Create additional indexes for better performance"""
    postgres_engine = create_engine(POSTGRES_URL)
    
    with postgres_engine.connect() as conn:
        # Create indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_requests_status ON requests(status);",
            "CREATE INDEX IF NOT EXISTS idx_requests_username ON requests(username);",
            "CREATE INDEX IF NOT EXISTS idx_requests_hostname ON requests(hostname);",
            "CREATE INDEX IF NOT EXISTS idx_requests_created_at ON requests(created_at);",
            "CREATE INDEX IF NOT EXISTS idx_requests_modified_at ON requests(modified_at);"
        ]
        
        for index_sql in indexes:
            try:
                conn.execute(text(index_sql))
                print(f"Created index: {index_sql}")
            except Exception as e:
                print(f"Failed to create index: {e}")
        
        conn.commit()

if __name__ == "__main__":
    print("Starting migration from MariaDB to PostgreSQL...")
    
    # Check if environment variables are set
    if not os.getenv('MARIADB_URL'):
        print("Warning: MARIADB_URL not set, using default")
    
    if not os.getenv('DATABASE_URL'):
        print("Warning: DATABASE_URL not set, using default")
    
    try:
        migrate_data()
        create_indexes()
        print("Migration completed successfully!")
    except Exception as e:
        print(f"Migration failed: {e}")
        sys.exit(1)