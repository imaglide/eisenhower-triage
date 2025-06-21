"""
EisenhowerTriageAgent Backend Package

This package contains the core functionality for email triage using the Eisenhower Matrix.
"""

from .triage_core import (
    triage_email_only,
    triage_with_context,
    get_quadrant_description,
    format_eisenhower_prompt
)

from .config import (
    Config,
    get_quadrant_config,
    get_all_quadrants,
    EISENHOWER_QUADRANTS
)

from .supabase_client import (
    get_sender_profile,
    create_sender_profile,
    update_sender_profile,
    embedding_exists,
    store_embedding,
    upsert_triage_result,
    get_triage_result,
    get_recent_triage_results,
    test_connection
)

__version__ = "0.1.0"
__author__ = "EisenhowerTriageAgent Team"

__all__ = [
    # Core triage functions
    "triage_email_only",
    "triage_with_context", 
    "get_quadrant_description",
    "format_eisenhower_prompt",
    
    # Configuration
    "Config",
    "get_quadrant_config",
    "get_all_quadrants",
    "EISENHOWER_QUADRANTS",
    
    # Supabase client functions
    "get_sender_profile",
    "create_sender_profile",
    "update_sender_profile",
    "embedding_exists",
    "store_embedding",
    "upsert_triage_result",
    "get_triage_result",
    "get_recent_triage_results",
    "test_connection"
] 