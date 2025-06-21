# Batch Processing Guide

This guide explains how to use the batch email processing functionality for the EisenhowerTriageAgent.

## Overview

The batch processing script (`scripts/run_batch_from_eml.py`) processes .eml files from the `data/sample_emails/` directory, running them through the complete triage pipeline:

1. **Parse .eml files** - Extract subject, body, sender, and message ID
2. **Check for duplicates** - Skip if already processed
3. **Get sender context** - Retrieve sender profile from database
4. **Run dual triage** - Email-only and contextual classification
5. **Generate embeddings** - Create OpenAI embeddings for the email
6. **Store results** - Save everything to Supabase database

## Prerequisites

1. **Environment setup** - `.env` file with API keys
2. **Supabase setup** - Database schema and tables created
3. **Sample .eml files** - Test files in `data/sample_emails/` directory

## Quick Start

### 1. Set up environment variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
```

### 2. Test the setup

Run the test script to verify everything is working:

```bash
python tests/test_batch_processing.py
```

### 3. Run batch processing

Process up to 5 .eml files:

```bash
python scripts/run_batch_from_eml.py
```

## Sample .eml Files

The script comes with 5 sample .eml files for testing:

### 1. `sample_urgent.eml` - Do Quadrant
- **From**: boss@company.com
- **Subject**: URGENT: Server down - immediate action required
- **Expected classification**: Do (urgent & important)

### 2. `sample_schedule.eml` - Schedule Quadrant
- **From**: colleague@company.com
- **Subject**: Weekly team meeting agenda
- **Expected classification**: Schedule (important but not urgent)

### 3. `sample_delegate.eml` - Delegate Quadrant
- **From**: coworker@company.com
- **Subject**: Can you help with this task?
- **Expected classification**: Delegate (urgent but not important)

### 4. `sample_delete.eml` - Delete Quadrant
- **From**: noreply@newsletter.com
- **Subject**: Newsletter subscription confirmed
- **Expected classification**: Delete (neither urgent nor important)

### 5. `sample_multipart.eml` - Mixed Content
- **From**: vendor@external.com
- **Subject**: Project update request
- **Content**: Both text/plain and text/html parts

## Processing Pipeline

### Email Parsing
The script extracts:
- **Subject**: Email subject line
- **Body**: Text content (prefers text/plain, falls back to text/html)
- **From**: Sender email address
- **Message-ID**: From headers or generated UUID

### Duplicate Detection
- Checks `embedding_exists(message_id)` before processing
- Skips files that have already been processed
- Prevents duplicate work and API costs

### Sender Context
- Retrieves sender profile using `get_sender_profile(from)`
- Uses profile data for contextual classification
- Falls back to empty profile if not found

### Dual Classification
1. **Email-only triage**: Uses only subject and body content
2. **Contextual triage**: Incorporates sender profile information
3. Both return quadrant, confidence, and reasoning

### Embedding Generation
- Combines subject and body for embedding
- Uses OpenAI text-embedding-ada-002 model
- Truncates text if too long (8000 token limit)
- Stores 1536-dimensional vector in database

### Database Storage
- **Embeddings**: Stored in `email_embeddings` table
- **Triage results**: Stored in `triage_results` table
- **Timestamps**: Automatic creation and update times

## Output and Logging

### Console Output
```
🚀 Starting batch email processing...
==================================================
📧 Found 5 .eml files to process

==================== Processing File 1/5 ====================
File: sample_urgent.eml
Processing email: urgent-server-123@company.com
Subject: URGENT: Server down - immediate action required
From: boss@company.com
Found sender profile for boss@company.com
Running email-only triage...
Email-only result: do (confidence: 0.95)
Running contextual triage...
Contextual result: do (confidence: 0.98)
Generating embedding...
Storing embedding...
Storing triage results...
✅ Successfully processed email: urgent-server-123@company.com
✅ Successfully processed sample_urgent.eml
```

### Log File
Detailed logs are saved to `batch_processing.log`:
```
2024-12-15 10:30:00,123 - INFO - Processing email: urgent-server-123@company.com
2024-12-15 10:30:00,124 - INFO - Subject: URGENT: Server down - immediate action required
2024-12-15 10:30:00,125 - INFO - From: boss@company.com
2024-12-15 10:30:00,126 - INFO - Found sender profile for boss@company.com
2024-12-15 10:30:00,127 - INFO - Running email-only triage...
2024-12-15 10:30:00,128 - INFO - Email-only result: do (confidence: 0.95)
```

### Summary Report
```
==================================================
📊 Processing Summary:
  Total files: 5
  Successful: 5
  Failed: 0
  Success rate: 100.0%

🎉 Batch processing completed!
Check the database for stored results and embeddings.
```

## Error Handling

### Graceful Failures
- **File parsing errors**: Logged and skipped, continues with next file
- **API failures**: Logged and skipped, continues with next file
- **Database errors**: Logged and skipped, continues with next file
- **Embedding generation failures**: Logged and skipped, continues with next file

### Common Issues
1. **Missing .env file**: Configuration validation fails
2. **Invalid API keys**: OpenAI or Supabase connection fails
3. **Missing .eml files**: No files found in directory
4. **Malformed .eml files**: Parsing errors logged
5. **Network issues**: API timeouts logged

## Database Results

After processing, check your Supabase database:

### Triage Results
```sql
SELECT * FROM triage_results ORDER BY processed_at DESC LIMIT 5;
```

### Embeddings
```sql
SELECT message_id, created_at FROM email_embeddings ORDER BY created_at DESC LIMIT 5;
```

### Sender Profiles
```sql
SELECT email, name, tags, relationship FROM sender_profiles;
```

## Customization

### Processing More Files
Edit the script to process more than 5 files:
```python
# Change this line in main()
eml_files = eml_files[:10]  # Process up to 10 files
```

### Different Directory
Change the source directory:
```python
# Change this line in main()
eml_dir = Path("./my_emails")  # Use different directory
```

### Custom Logging
Modify logging configuration:
```python
logging.basicConfig(
    level=logging.DEBUG,  # More verbose logging
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## Performance Considerations

### API Limits
- **OpenAI**: Rate limits apply to both classification and embedding
- **Supabase**: Connection pooling handles database operations
- **Processing time**: ~2-5 seconds per email (depending on API response times)

### Cost Optimization
- **Duplicate detection**: Prevents reprocessing
- **Text truncation**: Limits embedding token usage
- **Batch size**: Process in small batches to manage costs

### Scaling
For large-scale processing:
1. Implement queue system
2. Add progress persistence
3. Use async processing
4. Add retry logic for API failures

## Troubleshooting

### Configuration Issues
```bash
# Test configuration
python tests/test_batch_processing.py
```

### Database Issues
```bash
# Test Supabase connection
python tests/test_supabase_client.py
```

### Email Parsing Issues
```bash
# Test individual file parsing
python -c "
from scripts.run_batch_from_eml import extract_email_content
from pathlib import Path
data = extract_email_content(Path('../data/sample_emails/sample_urgent.eml'))
print(data)
"
```

## Next Steps

After successful batch processing:

1. **Review results** in Supabase dashboard
2. **Analyze classifications** for accuracy
3. **Update sender profiles** based on results
4. **Integrate with Streamlit UI** for real-time processing
5. **Scale up** for production use 