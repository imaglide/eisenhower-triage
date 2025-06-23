# Eisenhower Triage Agent - Streamlit App

A Streamlit application for analyzing and triaging emails using multiple AI strategies with **real LLM calls** and **Supabase integration**.

## Features

- 📧 Upload and parse .eml email files
- 🔍 Display parsed email content (subject, sender, body)
- 🚀 Run multiple triage strategies with **real AI models**:
  - **Email Only**: OpenAI GPT-4 analysis of email content
  - **Contextual**: Context-aware analysis using sender profiles from Supabase
  - **Embedding**: Semantic embedding-based analysis using OpenAI embeddings
  - **Outcomes**: Outcome-focused analysis using historical triage data
- 📊 View detailed results with confidence scores and reasoning
- 📈 Summary dashboard with consensus analysis
- ⚙️ Configuration status monitoring
- 🔄 Automatic fallback to keyword analysis if LLM calls fail

## Prerequisites

### Required Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=400
OPENAI_TEMPERATURE=0.1

# Supabase Configuration
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_anon_key_here

# Optional: Embedding Configuration
EMBEDDING_MODEL=text-embedding-ada-002
```

### API Keys Required

1. **OpenAI API Key**: For GPT-4 analysis and embeddings
   - Get from: https://platform.openai.com/api-keys
   - Required for: All LLM-based triage strategies

2. **Supabase Credentials**: For sender profiles and historical data
   - Get from: https://supabase.com/dashboard
   - Required for: Contextual and outcomes strategies

## Installation

1. Ensure you have the required dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your environment variables (see Prerequisites above)

3. Verify your Supabase database has the required tables:
   - `sender_profiles`
   - `email_embeddings`
   - `triage_results`

## Running the App

1. Start the Streamlit app:
```bash
streamlit run streamlit_app.py
```

2. Open your browser and navigate to the URL shown in the terminal (usually `http://localhost:8501`)

3. Check the configuration status in the sidebar

4. Upload an .eml file using the sidebar

5. Click "Run Triage Analysis" to process the email with real LLM calls

## File Structure

```
├── streamlit_app.py          # Main Streamlit application
├── agent_logic.py           # Real LLM integration with fallbacks
├── backend/
│   ├── triage_core.py       # Real LLM triage functions
│   ├── supabase_client.py   # Supabase database operations
│   └── config.py            # Configuration management
├── utils/
│   ├── __init__.py
│   └── eml_parser.py        # Email parsing utilities
├── test_email.eml           # Sample email for testing
└── STREAMLIT_README.md      # This file
```

## Usage

1. **Upload Email**: Use the sidebar to upload an .eml file
2. **Review Content**: Check the parsed email content (subject, sender, body)
3. **Run Analysis**: Click "Run Triage Analysis" to process the email with real LLM calls
4. **View Results**: Explore results across 4 different strategies in separate tabs
5. **Check Summary**: Review the consensus analysis and overall summary

## Triage Strategies

### Email Only Strategy
- **Real Implementation**: Uses OpenAI GPT-4 for intelligent email classification
- **Analysis**: Comprehensive content analysis with natural language understanding
- **Fallback**: Keyword-based analysis if LLM unavailable

### Contextual Strategy
- **Real Implementation**: Considers sender profiles from Supabase database
- **Analysis**: Relationship-aware classification using historical sender data
- **Fallback**: Basic domain and pattern analysis if Supabase unavailable

### Embedding Strategy
- **Real Implementation**: Uses OpenAI embeddings for semantic similarity
- **Analysis**: Finds similar emails in database for context-aware classification
- **Fallback**: Simulated embedding analysis if embeddings unavailable

### Outcomes Strategy
- **Real Implementation**: Uses historical triage results for outcome prediction
- **Analysis**: Business impact assessment based on past similar emails
- **Fallback**: Keyword-based impact analysis if historical data unavailable

## Priority Quadrants

The app classifies emails into 4 priority quadrants:

- 🔴 **Urgent & Important**: Do first
- 🟡 **Important, Not Urgent**: Schedule
- 🟠 **Urgent, Not Important**: Delegate
- 🟢 **Not Urgent, Not Important**: Eliminate

## Configuration Status

The app shows real-time configuration status in the sidebar:

- ✅ **OpenAI API Key**: Shows if LLM calls are available
- ✅ **Supabase Connection**: Shows if database access is available
- 🤖 **Real LLM Analysis**: Indicates when real AI models are used
- ⚠️ **Fallback Analysis**: Indicates when fallback methods are used

## Testing

Use the provided `test_email.eml` file to test the application. This sample email contains:
- Urgent keywords ("urgent", "deadline", "immediate")
- Important keywords ("critical", "essential", "priority")
- Business impact terms ("revenue", "customer", "contract")
- Action items ("please", "need", "request")

## Error Handling

The app includes robust error handling:

- **LLM Failures**: Automatic fallback to keyword analysis
- **Supabase Errors**: Graceful degradation to basic analysis
- **Network Issues**: Retry logic with exponential backoff
- **Configuration Issues**: Clear warnings and status indicators

## Cost Considerations

- **OpenAI API**: Each analysis uses GPT-4 tokens (~$0.03-0.06 per email)
- **Embeddings**: Additional cost for semantic similarity (~$0.0001 per email)
- **Supabase**: Database operations (usually within free tier limits)

## Customization

You can customize the triage strategies by modifying the functions in `agent_logic.py`:

- Adjust LLM prompts in `backend/triage_core.py`
- Modify sender profile logic in `backend/supabase_client.py`
- Change fallback behavior for different error conditions
- Add new triage strategies

## Dependencies

The app requires the following key dependencies:
- `streamlit`: Web application framework
- `openai`: OpenAI API client
- `supabase`: Supabase database client
- `email`: Python's built-in email parsing
- `tiktoken`: Token counting for OpenAI
- Standard Python libraries (re, time, random, typing)

All dependencies are listed in `requirements.txt`. 