-- Database schema for EisenhowerTriageAgent with JSONB triage results
-- Run this in your Supabase SQL editor to create the required tables

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Sender profiles table
CREATE TABLE IF NOT EXISTS sender_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    tags JSONB DEFAULT '[]'::jsonb,
    notes TEXT,
    linked_accounts JSONB DEFAULT '[]'::jsonb,
    relationship TEXT,
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Email embeddings table
CREATE TABLE IF NOT EXISTS email_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email_id TEXT UNIQUE NOT NULL,
    embedding VECTOR(1536), -- OpenAI text-embedding-ada-002 dimension
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Triage results table with JSONB fields
CREATE TABLE IF NOT EXISTS triage_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    message_id TEXT UNIQUE NOT NULL,
    triage_email_only JSONB, -- Contains: quadrant, confidence, reasoning
    triage_with_context JSONB, -- Contains: quadrant, confidence, reasoning
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Raw emails table (optional, for storing full email data)
CREATE TABLE IF NOT EXISTS emails_raw (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    message_id TEXT UNIQUE NOT NULL,
    sender_email TEXT,
    recipient_email TEXT,
    subject TEXT,
    body TEXT,
    headers JSONB,
    attachments JSONB DEFAULT '[]'::jsonb,
    received_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_sender_profiles_email ON sender_profiles(email);
CREATE INDEX IF NOT EXISTS idx_email_embeddings_email_id ON email_embeddings(email_id);
CREATE INDEX IF NOT EXISTS idx_triage_results_message_id ON triage_results(message_id);
CREATE INDEX IF NOT EXISTS idx_triage_results_processed_at ON triage_results(processed_at DESC);
CREATE INDEX IF NOT EXISTS idx_emails_raw_message_id ON emails_raw(message_id);
CREATE INDEX IF NOT EXISTS idx_emails_raw_sender_email ON emails_raw(sender_email);
CREATE INDEX IF NOT EXISTS idx_emails_raw_received_at ON emails_raw(received_at DESC);

-- Create JSONB indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_triage_results_email_only_quadrant ON triage_results USING GIN ((triage_email_only->>'quadrant'));
CREATE INDEX IF NOT EXISTS idx_triage_results_context_quadrant ON triage_results USING GIN ((triage_with_context->>'quadrant'));

-- Create indexes for vector similarity search (if using pgvector)
-- Note: This requires the pgvector extension to be enabled
-- CREATE INDEX IF NOT EXISTS idx_email_embeddings_vector ON email_embeddings USING ivfflat (embedding vector_cosine_ops);

-- Create RLS (Row Level Security) policies
-- Enable RLS on all tables
ALTER TABLE sender_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE triage_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE emails_raw ENABLE ROW LEVEL SECURITY;

-- Create policies for authenticated users
-- Note: Adjust these policies based on your security requirements

-- Sender profiles policies
CREATE POLICY "Users can view sender profiles" ON sender_profiles
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Users can insert sender profiles" ON sender_profiles
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Users can update sender profiles" ON sender_profiles
    FOR UPDATE USING (auth.role() = 'authenticated');

-- Email embeddings policies
CREATE POLICY "Users can view email embeddings" ON email_embeddings
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Users can insert email embeddings" ON email_embeddings
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Users can update email embeddings" ON email_embeddings
    FOR UPDATE USING (auth.role() = 'authenticated');

-- Triage results policies
CREATE POLICY "Users can view triage results" ON triage_results
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Users can insert triage results" ON triage_results
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Users can update triage results" ON triage_results
    FOR UPDATE USING (auth.role() = 'authenticated');

-- Emails raw policies
CREATE POLICY "Users can view emails raw" ON emails_raw
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Users can insert emails raw" ON emails_raw
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Users can update emails raw" ON emails_raw
    FOR UPDATE USING (auth.role() = 'authenticated');

-- Create functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for automatic timestamp updates
CREATE TRIGGER update_sender_profiles_updated_at 
    BEFORE UPDATE ON sender_profiles 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_email_embeddings_updated_at 
    BEFORE UPDATE ON email_embeddings 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_triage_results_updated_at 
    BEFORE UPDATE ON triage_results 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_emails_raw_updated_at 
    BEFORE UPDATE ON emails_raw 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert some sample data for testing
INSERT INTO sender_profiles (email, name, tags, notes, relationship, priority) VALUES
    ('boss@company.com', 'John Manager', '["management", "urgent"]', 'Direct supervisor, high priority contact', 'supervisor', 1),
    ('colleague@company.com', 'Jane Colleague', '["peer", "same_level"]', 'Team member, same department', 'peer', 2),
    ('vendor@external.com', 'External Vendor', '["external", "vendor"]', 'Service provider, not urgent', 'vendor', 3)
ON CONFLICT (email) DO NOTHING;

-- Create a view for easy access to triage results with sender information
CREATE OR REPLACE VIEW triage_results_with_sender AS
SELECT 
    tr.*,
    sp.name as sender_name,
    sp.tags as sender_tags,
    sp.relationship as sender_relationship,
    sp.priority as sender_priority
FROM triage_results tr
LEFT JOIN emails_raw er ON tr.message_id = er.message_id
LEFT JOIN sender_profiles sp ON er.sender_email = sp.email;

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO authenticated; 