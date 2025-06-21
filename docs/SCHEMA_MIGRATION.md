# Schema Migration Guide

## Overview

This document describes the migration from the old flat-column schema to the new JSONB-based schema for the `triage_results` table in the EisenhowerTriageAgent.

## Changes Made

### 1. Embedding Length Fix
- **Before**: 1500-dimensional embeddings
- **After**: 1536-dimensional embeddings (OpenAI text-embedding-ada-002 standard)

### 2. Triage Results Schema Update
- **Before**: Flat columns (`email_only_quadrant`, `email_only_confidence`, etc.)
- **After**: JSONB fields (`triage_email_only`, `triage_with_context`)

## Database Schema Changes

### Old Schema (Flat Columns)
```sql
CREATE TABLE triage_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    message_id TEXT UNIQUE NOT NULL,
    email_only_quadrant TEXT,
    email_only_confidence FLOAT,
    email_only_reasoning TEXT,
    contextual_quadrant TEXT,
    contextual_confidence FLOAT,
    contextual_reasoning TEXT,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### New Schema (JSONB Fields)
```sql
CREATE TABLE triage_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    message_id TEXT UNIQUE NOT NULL,
    triage_email_only JSONB, -- Contains: quadrant, confidence, reasoning
    triage_with_context JSONB, -- Contains: quadrant, confidence, reasoning
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Migration Steps

### 1. Update Database Schema
Run the new schema file in your Supabase SQL editor:
```sql
-- Run docs/database_schema_jsonb.sql
```

### 2. Migrate Existing Data
Run the migration script:
```bash
python scripts/migrate_to_jsonb_schema.py
```

### 3. Update Test Suite
The test suite has been updated to work with the new schema:

#### Embedding Length Fix
```python
# Before
test_embedding = [0.1, 0.2, 0.3, 0.4, 0.5] * 300  # 1500 dimensions

# After
test_embedding = [0.1, 0.2, 0.3, 0.4, 0.5] * 307  # 1536 dimensions (OpenAI text-embedding-ada-002)
```

#### Triage Result Access Patterns
```python
# Before (flat columns)
result.get("email_only_quadrant")
result.get("contextual_quadrant")

# After (JSONB fields)
result.get("triage_email_only", {}).get("quadrant")
result.get("triage_with_context", {}).get("quadrant")
result.get("triage_email_only", {}).get("confidence")
result.get("triage_email_only", {}).get("reasoning")
```

## Updated Files

### Backend Changes
- `backend/supabase_client.py`: Updated `upsert_triage_result()` function to use JSONB fields

### Test Suite Changes
- `tests/test_supabase_client.py`: Fixed embedding length and updated triage result access patterns
- `tests/test_embedding_refactor.py`: Already had correct 1536 dimensions

### Scripts
- `scripts/inspect_table_structure.py`: Updated to test both old and new schema formats
- `scripts/migrate_to_jsonb_schema.py`: New migration script

### Documentation
- `docs/database_schema_jsonb.sql`: New schema file with JSONB fields
- `docs/SCHEMA_MIGRATION.md`: This migration guide

## Benefits of JSONB Schema

1. **Flexibility**: Easy to add new fields without schema changes
2. **Performance**: JSONB indexes for efficient querying
3. **Consistency**: Structured data storage for triage results
4. **Queryability**: Can query nested JSON fields directly

## Testing the Migration

After migration, run the test suite to verify everything works:

```bash
# Test Supabase client
python tests/test_supabase_client.py

# Test embedding functions
python tests/test_embedding_refactor.py

# Test triage core
python tests/test_triage_core.py

# Test batch processing
python tests/test_batch_processing.py
```

## Rollback Plan

If you need to rollback to the old schema:

1. Restore the old schema from `docs/database_schema.sql`
2. Update `backend/supabase_client.py` to use flat columns
3. Update test files to use old access patterns
4. Migrate data back to flat columns if needed

## Troubleshooting

### Common Issues

1. **JSONB columns don't exist**: Make sure you've run the new schema file
2. **Migration fails**: Check that existing data is compatible
3. **Tests fail**: Verify that all test files have been updated

### Support

If you encounter issues during migration:
1. Check the migration script output for specific errors
2. Verify your Supabase connection and permissions
3. Review the test suite output for any remaining issues 