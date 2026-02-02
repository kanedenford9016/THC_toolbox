-- Torn Faction War Calculator Database Schema
-- PostgreSQL Database with SSL support for Vercel Postgres

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Faction Configuration Table
CREATE TABLE faction_config (
    id SERIAL PRIMARY KEY,
    faction_id INTEGER NOT NULL UNIQUE,
    faction_name VARCHAR(255) NOT NULL,
    encrypted_torn_api_key TEXT,
    last_api_refresh_timestamp TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Admin Users Table (Torn username + password hash)
CREATE TABLE admin_users (
    admin_id SERIAL PRIMARY KEY,
    torn_id INTEGER NOT NULL UNIQUE,
    username VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    faction_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- War Sessions Table
CREATE TABLE war_sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    war_name VARCHAR(255) NOT NULL,
    ranked_war_id BIGINT,
    opposing_faction_name VARCHAR(255),
    war_start_timestamp TIMESTAMP WITH TIME ZONE,
    war_end_timestamp TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) NOT NULL CHECK (status IN ('active', 'completed')),
    total_earnings DECIMAL(15, 2) NOT NULL DEFAULT 0,
    price_per_hit DECIMAL(15, 2) NOT NULL DEFAULT 0,
    encrypted_total_paid TEXT,
    encrypted_remaining_balance TEXT,
    created_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_timestamp TIMESTAMP WITH TIME ZONE,
    created_by_torn_id INTEGER,
    CONSTRAINT unique_active_session EXCLUDE (status WITH =) WHERE (status = 'active')
);

-- Members Table
CREATE TABLE members (
    member_id SERIAL PRIMARY KEY,
    torn_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    war_session_id UUID REFERENCES war_sessions(session_id) ON DELETE CASCADE,
    encrypted_hit_count TEXT,
    encrypted_score TEXT,
    encrypted_bonus_amount TEXT,
    bonus_reason TEXT,
    member_status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (member_status IN ('active', 'left_faction')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(torn_id, war_session_id)
);

-- Other Payments Table
CREATE TABLE other_payments (
    payment_id SERIAL PRIMARY KEY,
    war_session_id UUID REFERENCES war_sessions(session_id) ON DELETE CASCADE,
    encrypted_amount TEXT NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by_torn_id INTEGER
);

-- Audit Logs Table
CREATE TABLE audit_logs (
    log_id SERIAL PRIMARY KEY,
    action_type VARCHAR(100) NOT NULL,
    encrypted_old_value TEXT,
    encrypted_new_value TEXT,
    encrypted_details TEXT,
    user_torn_id INTEGER,
    war_session_id UUID REFERENCES war_sessions(session_id) ON DELETE SET NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    retention_date DATE NOT NULL
);

-- Audit Logs Archived Table (Read-only)
CREATE TABLE audit_logs_archived (
    log_id INTEGER PRIMARY KEY,
    action_type VARCHAR(100) NOT NULL,
    encrypted_old_value TEXT,
    encrypted_new_value TEXT,
    encrypted_details TEXT,
    user_torn_id INTEGER,
    war_session_id UUID,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    retention_date DATE NOT NULL,
    archived_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_members_war_session ON members(war_session_id);
CREATE INDEX idx_members_torn_id ON members(torn_id);
CREATE INDEX idx_other_payments_war_session ON other_payments(war_session_id);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_audit_logs_retention ON audit_logs(retention_date);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_torn_id);
CREATE INDEX idx_war_sessions_status ON war_sessions(status);
CREATE INDEX idx_audit_logs_archived_timestamp ON audit_logs_archived(timestamp);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_faction_config_updated_at BEFORE UPDATE ON faction_config
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_members_updated_at BEFORE UPDATE ON members
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_other_payments_updated_at BEFORE UPDATE ON other_payments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_admin_users_updated_at BEFORE UPDATE ON admin_users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant read-only access to audit_logs_archived
REVOKE ALL ON audit_logs_archived FROM PUBLIC;
GRANT SELECT ON audit_logs_archived TO PUBLIC;
