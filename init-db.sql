-- PostgreSQL initialization script
-- This script runs automatically when the container starts for the first time

-- Create application user
CREATE USER appstore_user WITH PASSWORD 'AppPass456$%^UserSecure';

-- Grant necessary privileges to the application user
-- Grant connection to database
GRANT CONNECT ON DATABASE appstore TO appstore_user;

-- Grant usage on public schema
GRANT USAGE ON SCHEMA public TO appstore_user;

-- Grant create privileges on public schema (for creating tables)
GRANT CREATE ON SCHEMA public TO appstore_user;

-- Grant all privileges on all tables in public schema
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO appstore_user;

-- Grant all privileges on all sequences in public schema (for auto-increment/serial)
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO appstore_user;

-- Grant privileges on future tables and sequences
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO appstore_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO appstore_user;

-- Optional: Create a read-only user for reporting/monitoring
-- CREATE USER appstore_readonly WITH PASSWORD 'ReadOnlyPass123!';
-- GRANT CONNECT ON DATABASE appstore TO appstore_readonly;
-- GRANT USAGE ON SCHEMA public TO appstore_readonly;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO appstore_readonly;
-- ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO appstore_readonly;