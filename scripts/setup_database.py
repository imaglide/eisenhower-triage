#!/usr/bin/env python3
"""
Database setup script for EisenhowerTriageAgent.

This script helps set up the required database tables in Supabase.
Run this after setting up your Supabase project and environment variables.
"""

import os
import sys
from pathlib import Path

# Add backend to path
project_root = Path(__file__).parent.parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

from supabase_client import test_connection
from config import Config


def setup_database():
    """Set up the database tables and verify connection."""
    
    print("🗄️  Setting up EisenhowerTriageAgent database...")
    print("=" * 60)
    
    # Validate configuration
    if not Config.validate():
        print("❌ Configuration validation failed")
        print("Please check your .env file and ensure SUPABASE_URL and SUPABASE_KEY are set.")
        return False
    
    # Test connection
    print("🔗 Testing Supabase connection...")
    if not test_connection():
        print("❌ Failed to connect to Supabase")
        print("Please check your SUPABASE_URL and SUPABASE_KEY in the .env file.")
        return False
    
    print("✅ Successfully connected to Supabase")
    
    # Instructions for manual setup
    print("\n📋 Database Setup Instructions:")
    print("=" * 60)
    print("1. Go to your Supabase project dashboard")
    print("2. Navigate to the SQL Editor")
    print("3. Copy and paste the contents of docs/database_schema.sql")
    print("4. Run the SQL script to create all tables")
    print("5. Verify the tables were created in the Table Editor")
    
    print("\n📁 Required Tables:")
    print("- sender_profiles")
    print("- email_embeddings") 
    print("- triage_results")
    print("- emails_raw (optional)")
    
    print("\n🔧 After running the schema:")
    print("1. Run: python3 tests/test_embedding_refactor.py")
    print("2. Run: python3 scripts/run_batch_from_eml.py")
    
    return True


def check_table_exists(table_name: str) -> bool:
    """Check if a table exists in the database."""
    try:
        from supabase_client import supabase
        response = supabase.table(table_name).select("count", count="exact").limit(1).execute()
        return True
    except Exception as e:
        print(f"❌ Table {table_name} does not exist or is not accessible: {str(e)}")
        return False


def verify_tables():
    """Verify that all required tables exist."""
    
    print("\n🔍 Verifying database tables...")
    print("=" * 40)
    
    required_tables = [
        "sender_profiles",
        "email_embeddings", 
        "triage_results"
    ]
    
    optional_tables = [
        "emails_raw"
    ]
    
    all_good = True
    
    for table in required_tables:
        if check_table_exists(table):
            print(f"✅ {table}")
        else:
            print(f"❌ {table} - REQUIRED")
            all_good = False
    
    print("\nOptional tables:")
    for table in optional_tables:
        if check_table_exists(table):
            print(f"✅ {table}")
        else:
            print(f"⚠️  {table} - Optional (not created)")
    
    if all_good:
        print("\n🎉 All required tables exist!")
        return True
    else:
        print("\n❌ Some required tables are missing.")
        print("Please run the database schema setup first.")
        return False


if __name__ == "__main__":
    print("EisenhowerTriageAgent Database Setup")
    print("=" * 60)
    
    # Try to set up and verify
    if setup_database():
        print("\n" + "=" * 60)
        verify_tables()
    else:
        print("\n❌ Database setup failed. Please check your configuration.") 