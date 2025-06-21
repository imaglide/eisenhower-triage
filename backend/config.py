"""
Configuration settings for EisenhowerTriageAgent.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for the application."""
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4")
    OPENAI_MAX_TOKENS: int = int(os.getenv("OPENAI_MAX_TOKENS", "400"))
    OPENAI_TEMPERATURE: float = float(os.getenv("OPENAI_TEMPERATURE", "0.1"))
    
    # Supabase Configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    # Application Configuration
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Optional: Embedding Configuration
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")
    
    @classmethod
    def validate(cls) -> bool:
        """
        Validate that required configuration is present.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        required_vars = [
            ("OPENAI_API_KEY", cls.OPENAI_API_KEY),
            ("SUPABASE_URL", cls.SUPABASE_URL),
            ("SUPABASE_KEY", cls.SUPABASE_KEY),
        ]
        
        missing_vars = []
        for var_name, var_value in required_vars:
            if not var_value:
                missing_vars.append(var_name)
        
        if missing_vars:
            print(f"Missing required environment variables: {', '.join(missing_vars)}")
            print("Please set these variables in your .env file or environment.")
            return False
        
        return True
    
    @classmethod
    def print_config(cls) -> None:
        """Print current configuration (without sensitive values)."""
        print("Configuration:")
        print(f"  OpenAI Model: {cls.OPENAI_MODEL}")
        print(f"  OpenAI Max Tokens: {cls.OPENAI_MAX_TOKENS}")
        print(f"  OpenAI Temperature: {cls.OPENAI_TEMPERATURE}")
        print(f"  Supabase URL: {cls.SUPABASE_URL}")
        print(f"  Debug Mode: {cls.DEBUG}")
        print(f"  Log Level: {cls.LOG_LEVEL}")
        print(f"  Embedding Model: {cls.EMBEDDING_MODEL}")


# Eisenhower Matrix quadrants configuration
EISENHOWER_QUADRANTS = {
    "do": {
        "name": "Do",
        "description": "Urgent & Important - Handle immediately",
        "color": "#FF6B6B",  # Red
        "priority": 1
    },
    "schedule": {
        "name": "Schedule", 
        "description": "Important but not Urgent - Plan for later",
        "color": "#4ECDC4",  # Teal
        "priority": 2
    },
    "delegate": {
        "name": "Delegate",
        "description": "Urgent but not Important - Assign to someone else", 
        "color": "#45B7D1",  # Blue
        "priority": 3
    },
    "delete": {
        "name": "Delete",
        "description": "Neither Urgent nor Important - Ignore or archive",
        "color": "#96CEB4",  # Green
        "priority": 4
    }
}


def get_quadrant_config(quadrant: str) -> dict:
    """
    Get configuration for a specific quadrant.
    
    Args:
        quadrant: Quadrant key (do, schedule, delegate, delete)
        
    Returns:
        Quadrant configuration dictionary
    """
    return EISENHOWER_QUADRANTS.get(quadrant, {})


def get_all_quadrants() -> dict:
    """
    Get all quadrant configurations.
    
    Returns:
        Dictionary of all quadrant configurations
    """
    return EISENHOWER_QUADRANTS.copy() 