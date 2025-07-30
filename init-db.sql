-- PostgreSQL initialization script
-- This script runs automatically when the container starts for the first time

-- Create application user
CREATE USER appstore_db_user WITH PASSWORD 'ma)4MqtqLF#VTb1WbKQ#';

-- Grant necessary privileges to the application user
-- Grant connection to database
GRANT CONNECT ON DATABASE appstore TO appstore_db_user;

-- Grant usage on public schema
GRANT USAGE ON SCHEMA public TO appstore_db_user;

-- Grant create privileges on public schema (for creating tables)
GRANT CREATE ON SCHEMA public TO appstore_db_user;

-- Grant all privileges on all tables in public schema
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO appstore_db_user;

-- Grant all privileges on all sequences in public schema (for auto-increment/serial)
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO appstore_db_user;

-- Grant privileges on future tables and sequences
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO appstore_db_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO appstore_db_user;