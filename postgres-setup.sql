DROP DATABASE bh;
CREATE DATABASE bh;
CREATE USER banhammer WITH PASSWORD 'banhammer';
ALTER ROLE banhammer SET client_encoding TO 'utf8';
ALTER ROLE banhammer SET default_transaction_isolation TO 'read committed';
ALTER ROLE banhammer SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE bh TO banhammer;
