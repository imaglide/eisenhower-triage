# Backend Module

This module contains the core functionality for the EisenhowerTriageAgent.

## Components

### `triage_core.py`
The main triage engine that classifies emails using OpenAI's GPT-4 model.

**Key Functions:**
- `triage_email_only(subject, body)` - Classify using only email content
- `triage_with_context(subject, body, sender_profile)` - Classify with sender context
- `format_eisenhower_prompt()` - Helper function to format OpenAI prompts
- `get_quadrant_description()` - Get human-readable quadrant descriptions

### `config.py`
Configuration management and environment variable handling.

**Key Features:**
- Environment variable loading from `.env` file
- Configuration validation
- Eisenhower Matrix quadrant definitions
- OpenAI and Supabase configuration

## Usage

### Basic Classification
```python
from backend.triage_core import triage_email_only

result = triage_email_only(
    subject="Urgent: Server down",
    body="The production server is down and customers are affected."
)
print(result)
# Output: {"quadrant": "do", "confidence": 0.95, "reasoning": "..."}
```

### Classification with Context
```python
from backend.triage_core import triage_with_context

sender_profile = {
    "tags": ["IT", "urgent"],
    "notes": "System administrator",
    "relationship": "supervisor"
}

result = triage_with_context(
    subject="Server issue",
    body="Can you help with this server problem?",
    sender_profile=sender_profile
)
```

### Configuration
```python
from backend.config import Config

# Validate configuration
if Config.validate():
    print("Configuration is valid")
    
# Print current config
Config.print_config()
```

## Environment Variables

Create a `.env` file in the project root with:

```env
OPENAI_API_KEY=your_openai_api_key_here
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
```

## Testing

Run the test script to verify functionality:

```bash
python test_triage_core.py
```

## Dependencies

- `openai` - For GPT-4 classification
- `python-dotenv` - For environment variable loading
- `typing` - For type hints

## Error Handling

The module includes robust error handling:
- API failures return safe fallback classifications
- Invalid responses are handled gracefully
- Configuration validation prevents runtime errors 