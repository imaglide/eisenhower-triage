# EisenhowerTriageAgent

An intelligent email classification system that uses the Eisenhower Matrix to automatically triage emails into four quadrants: Do, Schedule, Delegate, and Delete. Built with OpenAI GPT-4 for classification and Supabase for data storage.

## 🏗️ Project Structure

```
eisenhower-triage/
├── backend/                 # Core backend modules
│   ├── triage_core.py      # Email classification logic
│   ├── supabase_client.py  # Database operations
│   ├── config.py           # Configuration management
│   └── __init__.py         # Package initialization
├── scripts/                 # Executable scripts
│   └── run_batch_from_eml.py  # Batch email processing
├── tests/                   # Test files
│   ├── test_batch_processing.py
│   ├── test_supabase_client.py
│   └── test_triage_core.py
├── docs/                    # Documentation
│   ├── BATCH_PROCESSING_README.md
│   ├── SUPABASE_SETUP.md
│   ├── database_schema.sql
│   ├── implementation_plan.md
│   ├── current_status.md
│   └── parkinglot.md
├── data/                    # Data files
│   └── sample_emails/       # Sample .eml files for testing
├── frontend/                # Frontend components (future)
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Clone the repository
git clone <repository-url>
cd eisenhower-triage

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your API keys
```

### 2. Configure API Keys

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
```

### 3. Setup Database

Follow the [Supabase Setup Guide](docs/SUPABASE_SETUP.md) to create your database schema.

### 4. Test the System

```bash
# Run all tests
python tests/test_batch_processing.py
python tests/test_supabase_client.py
python tests/test_triage_core.py
```

### 5. Process Sample Emails

```bash
# Process up to 5 sample emails
python scripts/run_batch_from_eml.py
```

## 📚 Documentation

- **[Batch Processing Guide](docs/BATCH_PROCESSING_README.md)** - How to process .eml files in batch
- **[Supabase Setup](docs/SUPABASE_SETUP.md)** - Database configuration and setup
- **[Implementation Plan](docs/implementation_plan.md)** - Development roadmap and phases
- **[Current Status](docs/current_status.md)** - Project progress and completed features
- **[Parking Lot](docs/parkinglot.md)** - Future ideas and improvements

## 🔧 Core Features

### Email Classification
- **Dual Triage**: Email-only and contextual classification
- **Eisenhower Matrix**: Four-quadrant classification system
- **Confidence Scoring**: AI confidence levels for each classification
- **Reasoning**: Detailed explanations for classification decisions

### Robust Error Handling
- **API Retry Logic**: Exponential backoff for OpenAI API calls
- **Rate Limiting**: Protection against API rate limits
- **Graceful Fallbacks**: Safe defaults when services are unavailable
- **Comprehensive Logging**: Detailed error tracking and debugging

### Data Management
- **Supabase Integration**: PostgreSQL database with real-time capabilities
- **Embedding Storage**: OpenAI embeddings for similarity search
- **Sender Profiles**: Context-aware classification based on sender history
- **Duplicate Detection**: Prevents reprocessing of already analyzed emails

## 🛠️ Development

### Running Tests
```bash
# Test batch processing
python tests/test_batch_processing.py

# Test database operations
python tests/test_supabase_client.py

# Test classification logic
python tests/test_triage_core.py
```

### Adding New Features
1. Create feature branch
2. Add tests in `tests/` directory
3. Update documentation in `docs/` directory
4. Submit pull request

## 📊 Eisenhower Matrix

The system classifies emails into four quadrants:

| Quadrant | Description | Action |
|----------|-------------|---------|
| **Do** | Urgent & Important | Handle immediately |
| **Schedule** | Important but not Urgent | Plan for dedicated time |
| **Delegate** | Urgent but not Important | Assign to someone else |
| **Delete** | Neither Urgent nor Important | Ignore or archive |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Update documentation
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For questions or issues:
1. Check the documentation in `docs/`
2. Review existing issues
3. Create a new issue with detailed information
