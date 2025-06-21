# GPT-4 Context Overflow Prevention Implementation

## Overview

This document describes the implementation of safe input truncation to prevent OpenAI GPT-4 context overflows in the EisenhowerTriageAgent project.

## Problem

Large email bodies can exceed GPT-4's context limits, causing API errors and failed triage classifications. The solution implements intelligent truncation that:

1. **Preserves embedding quality** by keeping full text for embeddings
2. **Prevents triage failures** by truncating input before GPT-4 classification
3. **Provides monitoring** for large emails that may need attention

## Implementation Details

### 1. Token Counting with tiktoken

**File**: `backend/triage_core.py`

```python
def count_tokens(text: str) -> int:
    """
    Count the number of tokens in a text string using tiktoken.
    
    Args:
        text: Text to count tokens for
        
    Returns:
        Number of tokens
    """
    if TIKTOKEN_AVAILABLE:
        try:
            # Use cl100k_base encoding (GPT-4 tokenizer)
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except Exception as e:
            logger.warning(f"Error counting tokens with tiktoken: {str(e)}")
            # Fallback to character-based estimation
            return len(text) // 4  # Rough estimate: 4 characters per token
    
    # Fallback when tiktoken is not available
    return len(text) // 4  # Rough estimate: 4 characters per token
```

**Features**:
- Uses GPT-4's actual tokenizer (`cl100k_base`)
- Graceful fallback to character-based estimation
- Error handling for tiktoken failures

### 2. Safe Truncation Function

**File**: `backend/triage_core.py`

```python
def truncate_for_prompt(text: str, max_tokens: int = 3000) -> str:
    """
    Safely truncate text to fit within GPT-4 context limits.
    
    Args:
        text: Text to truncate
        max_tokens: Maximum number of tokens to allow (default: 3000)
        
    Returns:
        Truncated text that fits within token limits
    """
    if TIKTOKEN_AVAILABLE:
        try:
            # Use cl100k_base encoding (GPT-4 tokenizer)
            encoding = tiktoken.get_encoding("cl100k_base")
            tokens = encoding.encode(text)
            
            if len(tokens) <= max_tokens:
                return text
            
            # Truncate to max_tokens and decode back to text
            truncated_tokens = tokens[:max_tokens]
            truncated_text = encoding.decode(truncated_tokens)
            
            logger.info(f"Text truncated from {len(tokens)} to {len(truncated_tokens)} tokens")
            return truncated_text
            
        except Exception as e:
            logger.warning(f"Error truncating with tiktoken: {str(e)}")
            # Fallback to character-based truncation
            return text[:8000]
    
    # Fallback when tiktoken is not available
    # Conservative estimate: 4 characters per token
    max_chars = max_tokens * 4
    if len(text) <= max_chars:
        return text
    
    truncated_text = text[:max_chars]
    logger.info(f"Text truncated from {len(text)} to {len(truncated_text)} characters (fallback mode)")
    return truncated_text
```

**Features**:
- Token-aware truncation using GPT-4's tokenizer
- Preserves complete tokens (no partial word truncation)
- Configurable max_tokens limit (default: 3000)
- Fallback to character-based truncation
- Comprehensive logging

### 3. Triage Function Updates

**Files**: `backend/triage_core.py`

Both `triage_email_only()` and `triage_with_context()` now include:

```python
# Truncate body to prevent GPT-4 context overflow
original_body_length = len(body)
body = truncate_for_prompt(body, max_tokens=3000)
if len(body) != original_body_length:
    logger.info(f"Body truncated from {original_body_length} to {len(body)} characters for triage")
```

**Key Points**:
- Truncation happens **before** prompt construction
- Original body length is preserved for logging
- 3000 token limit provides safety margin for GPT-4
- Full text is still available for embeddings

### 4. Batch Processing Enhancements

**File**: `scripts/run_batch_from_eml.py`

#### Large Email Monitoring

```python
# Log large emails for monitoring
body_token_count = count_tokens(body)
if body_token_count > 12000:
    print(f"⚠️ Large email: {email_id} — {body_token_count} tokens")
    logger.warning(f"Large email detected: {email_id} with {body_token_count} tokens")
```

#### Enhanced Embedding Generation

```python
def generate_embedding(text: str) -> Optional[list]:
    """
    Generate text embedding using OpenAI.
    
    Args:
        text: Text to embed (full text, not truncated for triage)
        
    Returns:
        List of float values representing the embedding vector
    """
    try:
        # Truncate text if too long (OpenAI has limits)
        max_tokens = 8000  # Conservative limit for embeddings
        original_length = len(text)
        original_tokens = count_tokens(text)
        
        if original_tokens > max_tokens:
            # Use tiktoken for precise truncation if available
            if TIKTOKEN_AVAILABLE:
                try:
                    encoding = tiktoken.get_encoding("cl100k_base")
                    tokens = encoding.encode(text)
                    truncated_tokens = tokens[:max_tokens]
                    text = encoding.decode(truncated_tokens)
                    print(f"📏 Text truncated from {original_tokens} to {len(truncated_tokens)} tokens for embedding")
                except Exception as e:
                    logger.warning(f"Error truncating with tiktoken: {str(e)}")
                    # Fallback to character-based truncation
                    text = text[:max_tokens * 4]
                    print(f"📏 Text truncated from {original_length} to {len(text)} characters for embedding (fallback)")
            else:
                # Fallback when tiktoken is not available
                text = text[:max_tokens * 4]
                print(f"📏 Text truncated from {original_length} to {len(text)} characters for embedding")
        
        # ... rest of embedding generation
```

**Key Points**:
- Full text is used for embeddings (not truncated for triage)
- Separate truncation logic for embedding limits
- Token-aware truncation when tiktoken is available
- Comprehensive logging of truncation events

## Dependencies

### Added to requirements.txt

```
tiktoken>=0.5.0
```

### Import Handling

Both files include graceful import handling:

```python
# Try to import tiktoken for token counting, fallback to character-based truncation
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    print("⚠️  tiktoken not available, using character-based truncation fallback")
```

## Testing

### Test File: `tests/test_truncation.py`

Comprehensive tests for:
- Token counting accuracy
- Truncation functionality
- tiktoken availability
- Fallback behavior

### Test Results

```
🧪 Testing Truncation Functionality
==================================================

🧪 Testing tiktoken availability...
✅ tiktoken is available
  Encoding test: 'Hello world' -> 2 tokens -> 'Hello world'
✅ tiktoken availability test completed

🧪 Testing token counting...
  Simple text: 'Hello world' -> 2 tokens
  Longer text: 'This is a longer piece of text...' -> 16 tokens
  Very long text: 12000 characters -> 2001 tokens
✅ Token counting tests completed

🧪 Testing truncation...
  Short text: 50 chars -> 50 chars (truncated: False)
  Long text: 12000 chars -> 299 chars (truncated: True)
  Very long text: 24000 chars
    max_tokens=100: 599 chars
    max_tokens=500: 2999 chars
✅ Truncation tests completed

🎉 All truncation tests completed!
```

## Benefits

1. **Prevents API Errors**: No more GPT-4 context overflow failures
2. **Preserves Quality**: Full text still used for embeddings
3. **Intelligent Truncation**: Token-aware, not character-based
4. **Monitoring**: Large emails are logged for review
5. **Graceful Degradation**: Works with or without tiktoken
6. **Configurable**: Adjustable token limits for different use cases

## Configuration

### Token Limits

- **Triage**: 3000 tokens (safety margin for GPT-4)
- **Embeddings**: 8000 tokens (OpenAI embedding limit)
- **Large Email Alert**: 12000 tokens (monitoring threshold)

### Customization

To adjust limits, modify the `max_tokens` parameter in:

```python
# In triage functions
body = truncate_for_prompt(body, max_tokens=3000)  # Adjust as needed

# In embedding function
max_tokens = 8000  # Adjust as needed

# In batch processing
if body_token_count > 12000:  # Adjust threshold as needed
```

## Monitoring

The system now provides comprehensive logging for:

- Truncation events (with before/after token counts)
- Large email detection
- tiktoken availability status
- Fallback mode usage

Check logs for entries like:
- `"Body truncated from X to Y characters for triage"`
- `"⚠️ Large email: {email_id} — {token_count} tokens"`
- `"Text truncated from X to Y tokens for embedding"` 