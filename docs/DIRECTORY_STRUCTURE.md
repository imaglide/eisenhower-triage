# Directory Structure Guide

This document explains the refactored directory structure of the EisenhowerTriageAgent project.

## 📁 Root Directory Structure

```
eisenhower-triage/
├── backend/                 # Core backend modules
├── scripts/                 # Executable scripts
├── tests/                   # Test files
├── docs/                    # Documentation
├── data/                    # Data files
├── frontend/                # Frontend components (future)
├── requirements.txt         # Python dependencies
└── README.md               # Main project documentation
```

## 🔧 Backend (`backend/`)

Core functionality and business logic.

```
backend/
├── __init__.py             # Package initialization and exports
├── triage_core.py          # Email classification logic with OpenAI
├── supabase_client.py      # Database operations and Supabase integration
└── config.py               # Configuration management and validation
```

### Key Files:
- **`triage_core.py`**: Main classification engine with robust error handling
- **`supabase_client.py`**: Database operations, embeddings, and sender profiles
- **`config.py`**: Environment variable management and validation
- **`__init__.py`**: Exports main functions for easy importing

## 🚀 Scripts (`scripts/`)

Executable scripts for common tasks.

```
scripts/
├── run_batch_from_eml.py   # Batch email processing
├── run_tests.py            # Run all tests
└── setup.py                # Project setup and validation
```

### Key Scripts:
- **`run_batch_from_eml.py`**: Process .eml files in batch with triage and storage
- **`run_tests.py`**: Convenience script to run all tests
- **`setup.py`**: Validate environment and create configuration templates

## 🧪 Tests (`tests/`)

Test files for all components.

```
tests/
├── test_batch_processing.py  # Batch processing functionality tests
├── test_supabase_client.py   # Database operations tests
└── test_triage_core.py       # Classification logic tests
```

### Test Coverage:
- **Batch Processing**: Email parsing, embedding generation, database storage
- **Supabase Client**: Connection, CRUD operations, error handling
- **Triage Core**: Classification accuracy, error handling, fallbacks

## 📚 Documentation (`docs/`)

Comprehensive project documentation.

```
docs/
├── BATCH_PROCESSING_README.md  # Batch processing guide
├── SUPABASE_SETUP.md           # Database setup instructions
├── database_schema.sql         # Database schema definition
├── implementation_plan.md      # Development roadmap
├── current_status.md           # Project progress tracking
├── parkinglot.md               # Future ideas and improvements
└── DIRECTORY_STRUCTURE.md      # This file
```

### Documentation Types:
- **User Guides**: How to use the system
- **Setup Instructions**: Environment and database configuration
- **Development Docs**: Architecture and implementation details
- **Planning Docs**: Roadmap and future features

## 📊 Data (`data/`)

Data files and sample content.

```
data/
└── sample_emails/           # Sample .eml files for testing
    ├── sample_urgent.eml    # Do quadrant example
    ├── sample_schedule.eml  # Schedule quadrant example
    ├── sample_delegate.eml  # Delegate quadrant example
    ├── sample_delete.eml    # Delete quadrant example
    └── sample_multipart.eml # Multipart email example
```

### Sample Emails:
- **Eisenhower Quadrants**: Examples for each classification category
- **Email Types**: Simple text, multipart, and complex emails
- **Testing**: Used for validation and demonstration

## 🎨 Frontend (`frontend/`)

Future frontend components (currently empty).

```
frontend/
└── (future Streamlit UI components)
```

## 🔄 Migration Summary

### Files Moved:
- `run_batch_from_eml.py` → `scripts/run_batch_from_eml.py`
- `test_*.py` → `tests/test_*.py`
- `*.md` → `docs/*.md` (except README.md)
- `database_schema.sql` → `docs/database_schema.sql`
- `eml_files/` → `data/sample_emails/`

### Path Updates:
- Updated all script references to use new paths
- Updated documentation to reflect new structure
- Updated test files to use new directory paths

## 🛠️ Development Workflow

### Adding New Features:
1. **Backend Logic**: Add to `backend/` modules
2. **Scripts**: Add executable scripts to `scripts/`
3. **Tests**: Add corresponding tests to `tests/`
4. **Documentation**: Update relevant docs in `docs/`

### Running the System:
```bash
# Setup
python scripts/setup.py

# Run tests
python scripts/run_tests.py

# Process emails
python scripts/run_batch_from_eml.py
```

### Importing Modules:
```python
# From scripts or tests
from backend import triage_core, supabase_client, config

# Direct imports
from backend.triage_core import triage_email_only
from backend.supabase_client import get_sender_profile
```

## 📋 Benefits of New Structure

### Organization:
- **Logical Grouping**: Related files are grouped together
- **Clear Separation**: Backend, scripts, tests, and docs are separate
- **Scalability**: Easy to add new components without clutter

### Maintainability:
- **Clear Dependencies**: Easy to understand what depends on what
- **Modular Design**: Components can be developed and tested independently
- **Documentation**: Comprehensive docs for each component

### Usability:
- **Easy Navigation**: Clear directory structure for new developers
- **Convenience Scripts**: Simple commands for common tasks
- **Self-Documenting**: Structure itself explains the project organization

## 🔮 Future Considerations

### Potential Additions:
- **`config/`**: Configuration files and templates
- **`logs/`**: Application logs and debugging output
- **`migrations/`**: Database migration scripts
- **`deploy/`**: Deployment and infrastructure scripts

### Frontend Development:
- **Streamlit App**: Interactive web interface
- **API Endpoints**: REST API for external integrations
- **Web Components**: Reusable UI components

This structure provides a solid foundation for continued development while maintaining clarity and organization as the project grows. 