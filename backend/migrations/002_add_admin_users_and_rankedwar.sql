-- Migration: Add admin_users table and ranked war metadata

-- Allow NULL for API key (no longer stored)
ALTER TABLE faction_config
    ALTER COLUMN encrypted_torn_api_key DROP NOT NULL;

-- Admin Users Table
CREATE TABLE IF NOT EXISTS admin_users (
    admin_id SERIAL PRIMARY KEY,
    torn_id INTEGER NOT NULL UNIQUE,
    username VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    faction_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Ranked war metadata on sessions
ALTER TABLE war_sessions
    ADD COLUMN IF NOT EXISTS ranked_war_id BIGINT,
    ADD COLUMN IF NOT EXISTS opposing_faction_name VARCHAR(255),
    ADD COLUMN IF NOT EXISTS war_start_timestamp TIMESTAMP WITH TIME ZONE,
    ADD COLUMN IF NOT EXISTS war_end_timestamp TIMESTAMP WITH TIME ZONE;

-- Member score storage
ALTER TABLE members
    ADD COLUMN IF NOT EXISTS encrypted_score TEXT;

-- Update trigger for admin_users
CREATE TRIGGER update_admin_users_updated_at BEFORE UPDATE ON admin_users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
