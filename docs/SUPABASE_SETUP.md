# Supabase Setup Guide

This guide will help you set up Supabase for the EisenhowerTriageAgent project.

## Prerequisites

1. A Supabase account (free tier available at [supabase.com](https://supabase.com))
2. Python environment with the required dependencies installed

## Step 1: Create a Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign in
2. Click "New Project"
3. Choose your organization
4. Enter a project name (e.g., "eisenhower-triage")
5. Enter a database password (save this securely)
6. Choose a region close to you
7. Click "Create new project"

## Step 2: Get Your Project Credentials

1. In your Supabase dashboard, go to **Settings** → **API**
2. Copy the following values:
   - **Project URL** (looks like: `https://your-project-id.supabase.co`)
   - **anon public** key (starts with `eyJ...`)

## Step 3: Set Up Environment Variables

Create a `.env` file in your project root with:

```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-public-key-here
OPENAI_API_KEY=your-openai-api-key-here
```

## Step 4: Create Database Schema

1. In your Supabase dashboard, go to **SQL Editor**
2. Copy the contents of `database_schema.sql`
3. Paste it into the SQL editor
4. Click "Run" to execute the schema

This will create:
- `sender_profiles` table for storing sender information
- `email_embeddings` table for storing email embeddings
- `triage_results` table for storing classification results
- `emails_raw` table for storing full email data
- Appropriate indexes and security policies

## Step 5: Test the Connection

Run the Supabase client test:

```bash
python test_supabase_client.py
```

This will test:
- Connection to Supabase
- Sender profile operations
- Embedding storage and retrieval
- Triage result storage and retrieval
- Error handling

## Step 6: Verify Tables

In your Supabase dashboard, go to **Table Editor** to verify the tables were created:

- `sender_profiles`
- `email_embeddings`
- `triage_results`
- `emails_raw`

## Database Schema Overview

### sender_profiles
Stores information about email senders:
- `email`: Primary identifier
- `name`: Sender's name
- `tags`: JSON array of tags (e.g., ["urgent", "IT"])
- `notes`: Free text notes
- `linked_accounts`: JSON array of related email addresses
- `relationship`: Relationship type (supervisor, peer, vendor, etc.)
- `priority`: Numeric priority (1=highest, 4=lowest)

### email_embeddings
Stores vector embeddings for emails:
- `message_id`: Unique email identifier
- `embedding`: 1536-dimensional vector (OpenAI text-embedding-ada-002)

### triage_results
Stores classification results:
- `message_id`: Links to the email
- `email_only_quadrant`: Classification without context
- `email_only_confidence`: Confidence score for email-only
- `email_only_reasoning`: Reasoning for email-only classification
- `contextual_quadrant`: Classification with sender context
- `contextual_confidence`: Confidence score for contextual
- `contextual_reasoning`: Reasoning for contextual classification

### emails_raw
Stores full email data:
- `message_id`: Unique identifier
- `sender_email`: Sender's email address
- `recipient_email`: Recipient's email address
- `subject`: Email subject
- `body`: Email body content
- `headers`: JSON object with email headers
- `attachments`: JSON array of attachment information

## Security Features

The schema includes:
- **Row Level Security (RLS)**: All tables have RLS enabled
- **Authentication policies**: Only authenticated users can access data
- **Automatic timestamps**: Created/updated timestamps are managed automatically
- **Data validation**: JSON fields are properly validated

## Troubleshooting

### Connection Issues
- Verify your `SUPABASE_URL` and `SUPABASE_KEY` are correct
- Check that your project is active in the Supabase dashboard
- Ensure your IP is not blocked by Supabase

### Schema Issues
- If tables don't exist, run the `database_schema.sql` script again
- Check the SQL editor for any error messages
- Verify you have the necessary permissions

### Permission Issues
- Ensure you're using the correct API key (anon public, not service role)
- Check that RLS policies are properly configured
- Verify your user is authenticated if using auth features

## Next Steps

Once Supabase is set up:

1. **Test the integration**: Run `python test_supabase_client.py`
2. **Test the triage system**: Run `python test_triage_core.py`
3. **Start building**: Use the functions in your application

## Advanced Configuration

### Vector Similarity Search
To enable vector similarity search with pgvector:

1. Enable the pgvector extension in Supabase
2. Uncomment the vector index line in `database_schema.sql`
3. Run the updated schema

### Custom Policies
Modify the RLS policies in `database_schema.sql` to match your security requirements.

### Backup and Recovery
Set up automated backups in your Supabase project settings. 