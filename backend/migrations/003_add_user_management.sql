-- Migration: Add user management features

-- Add password_changed flag to admin_users table
ALTER TABLE admin_users
    ADD COLUMN IF NOT EXISTS password_changed BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS email VARCHAR(255),
    ADD COLUMN IF NOT EXISTS temp_password_hash TEXT;

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_admin_users_username ON admin_users(username);
CREATE INDEX IF NOT EXISTS idx_admin_users_email ON admin_users(email);
