# Implementation Plan

## Overview
This document outlines the implementation strategy for the EisenhowerTriageAgent, divided into two main phases: batch email processing and interactive UI development.

## Part 1: Batch Email Triage

### 1.1 Email Parser (.eml → JSON)
**File**: `backend/email_parser.py`

**Components**:
- Parse .eml files using `email` library
- Extract metadata: sender, recipient, subject, date, attachments
- Convert to structured JSON format
- Handle encoding issues and malformed emails
- Support batch processing with progress tracking

**Key Functions**:
```python
def parse_eml_file(file_path: str) -> dict
def batch_parse_eml_files(directory: str) -> List[dict]
def validate_email_structure(email_data: dict) -> bool
```

### 1.2 Supabase Integration
**File**: `backend/supabase_client.py`

**Components**:
- Check for existing email embeddings in `emails_raw` table
- Query sender profiles and historical context
- Upsert triage results to `triage_results` table
- Handle connection pooling and error recovery

**Database Schema**:
```sql
-- emails_raw table
CREATE TABLE emails_raw (
    id UUID PRIMARY KEY,
    sender_email TEXT,
    subject TEXT,
    content TEXT,
    embedding VECTOR(1536),
    created_at TIMESTAMP
);

-- triage_results table
CREATE TABLE triage_results (
    id UUID PRIMARY KEY,
    email_id UUID REFERENCES emails_raw(id),
    email_only_quadrant TEXT,
    contextual_quadrant TEXT,
    confidence_scores JSONB,
    reasoning TEXT,
    processed_at TIMESTAMP
);
```

### 1.3 Dual Triage Engine
**File**: `backend/triage_engine.py`

**Components**:
- **Email-only classification**: Heuristic rules based on content analysis
- **Contextual classification**: Enhanced with sender profile and history
- Confidence scoring for both approaches
- Explanation generation for classification decisions

**Classification Logic**:
```python
def classify_email_only(email_data: dict) -> dict
def classify_with_context(email_data: dict, sender_context: dict) -> dict
def combine_classifications(email_result: dict, context_result: dict) -> dict
def generate_explanation(quadrant: str, confidence: float, reasoning: str) -> str
```

### 1.4 Batch Processor
**File**: `backend/batch_processor.py`

**Components**:
- Orchestrate the entire batch processing pipeline
- Handle command-line arguments and configuration
- Progress tracking and error handling
- Output generation (JSON, CSV, or database)

**Pipeline Flow**:
1. Scan input directory for .eml files
2. Parse each email to JSON
3. Check Supabase for existing embeddings
4. Run dual triage (email-only + contextual)
5. Upsert results to database
6. Generate summary report

## Part 2: Streamlit UI

### 2.1 Main Application
**File**: `frontend/app.py`

**Components**:
- Streamlit app configuration and layout
- Navigation between different modes
- Session state management
- Error handling and user feedback

**Layout Structure**:
```python
def main():
    st.set_page_config(page_title="Eisenhower Triage", layout="wide")
    
    # Sidebar navigation
    mode = st.sidebar.selectbox("Mode", ["Single Email", "Batch Upload", "Results View"])
    
    if mode == "Single Email":
        single_email_mode()
    elif mode == "Batch Upload":
        batch_upload_mode()
    else:
        results_view_mode()
```

### 2.2 Email Input Components
**File**: `frontend/components/email_input.py`

**Components**:
- Text area for manual email input
- File upload for .eml files
- Email validation and preview
- Input sanitization and formatting

**Key Functions**:
```python
def render_text_input() -> str
def render_file_upload() -> Optional[dict]
def validate_email_content(content: str) -> bool
def format_email_preview(email_data: dict) -> str
```

### 2.3 Triage Display
**File**: `frontend/components/triage_display.py`

**Components**:
- Side-by-side comparison of email-only vs contextual results
- Eisenhower Matrix visualization
- Confidence score displays
- Explanation text with highlighting

**Visualization Features**:
- Interactive quadrant chart
- Color-coded confidence indicators
- Expandable reasoning sections
- Export functionality

### 2.4 Context Viewer
**File**: `frontend/components/context_viewer.py`

**Components**:
- Sender profile display
- Historical email patterns
- Relationship strength indicators
- Contextual factors explanation

**Context Information**:
- Sender's role and importance
- Previous email classifications
- Response patterns and urgency indicators
- Organizational hierarchy context

## Development Phases

### Phase 1: Core Infrastructure (Week 1-2)
- [ ] Set up project structure and dependencies
- [ ] Implement email parser
- [ ] Create Supabase client and schema
- [ ] Basic triage engine (email-only)

### Phase 2: Batch Processing (Week 3-4)
- [ ] Complete dual triage engine
- [ ] Implement batch processor
- [ ] Add error handling and logging
- [ ] Create test suite

### Phase 3: Streamlit UI (Week 5-6)
- [ ] Build main Streamlit app
- [ ] Implement email input components
- [ ] Create triage display
- [ ] Add context viewer

### Phase 4: Integration & Testing (Week 7-8)
- [ ] End-to-end testing
- [ ] Performance optimization
- [ ] Documentation completion
- [ ] Deployment preparation

## Technical Considerations

### Performance
- Use async/await for database operations
- Implement caching for frequently accessed sender profiles
- Batch database operations where possible
- Optimize embedding generation and storage

### Security
- Sanitize all user inputs
- Validate file uploads
- Secure API key management
- Implement rate limiting

### Scalability
- Design for horizontal scaling
- Use connection pooling for database
- Implement queue system for large batch jobs
- Consider microservices architecture for future growth

## Success Metrics

- **Accuracy**: >85% agreement with human classification
- **Performance**: <2 seconds per email for batch processing
- **Reliability**: <1% error rate in production
- **Usability**: Intuitive UI with <5 minute learning curve
