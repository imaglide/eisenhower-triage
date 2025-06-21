#!/usr/bin/env python3
"""
Script to inspect the actual structure of all database tables.
"""

import os
import sys
from pathlib import Path

# Add backend to path
project_root = Path(__file__).parent.parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

from supabase_client import supabase


def inspect_table_structure():
    """Inspect the structure of all database tables."""
    
    print("🔍 Inspecting database table structures...")
    print("=" * 60)
    
    tables = ["sender_profiles", "email_embeddings", "triage_results", "emails_raw"]
    
    for table in tables:
        print(f"\n📋 Table: {table}")
        print("-" * 40)
        
        try:
            # Try to get table info by selecting all columns
            response = supabase.table(table).select("*").limit(1).execute()
            
            if response.data:
                # Get column names from the first row
                first_row = response.data[0]
                print(f"✅ Table exists and is accessible")
                print(f"📊 Columns found: {list(first_row.keys())}")
                
                # Show sample data structure
                print(f"📝 Sample data structure:")
                for key, value in first_row.items():
                    if isinstance(value, list):
                        print(f"  - {key}: list[{len(value)}]")
                    elif isinstance(value, dict):
                        print(f"  - {key}: dict")
                    else:
                        print(f"  - {key}: {type(value).__name__}")
            else:
                print(f"✅ Table exists but is empty")
                
        except Exception as e:
            print(f"❌ Error accessing table: {str(e)}")


def inspect_triage_results_structure():
    """Specifically inspect the triage_results table structure."""
    
    print("\n🔍 Inspecting triage_results table structure...")
    print("=" * 60)
    
    try:
        # Try to get the table structure by attempting to insert a minimal record with JSONB fields
        test_data = {
            "message_id": "test_structure_check",
            "triage_email_only": {
                "quadrant": "do",
                "confidence": 0.85,
                "reasoning": "Test reasoning"
            },
            "triage_with_context": {
                "quadrant": "do",
                "confidence": 0.92,
                "reasoning": "Test contextual reasoning"
            }
        }
        
        # Try insert to see what columns are accepted
        response = supabase.table("triage_results").insert(test_data).execute()
        print("✅ Test insert successful - JSONB columns exist")
        
        # Clean up test data
        supabase.table("triage_results").delete().eq("message_id", "test_structure_check").execute()
        print("🧹 Test data cleaned up")
        
    except Exception as e:
        print(f"❌ Error with test insert: {str(e)}")
        # Try to get column info from error message
        if "column" in str(e).lower():
            print("This suggests the table exists but has different column names")
        print("Trying with old schema format...")
        
        try:
            # Fallback to old schema format
            old_test_data = {
                "message_id": "test_structure_check_old",
                "email_only_quadrant": "do",
                "email_only_confidence": 0.85,
                "email_only_reasoning": "Test reasoning"
            }
            
            response = supabase.table("triage_results").insert(old_test_data).execute()
            print("✅ Test insert successful with old schema format")
            
            # Clean up test data
            supabase.table("triage_results").delete().eq("message_id", "test_structure_check_old").execute()
            print("🧹 Test data cleaned up")
            
        except Exception as e2:
            print(f"❌ Error with old schema format too: {str(e2)}")


if __name__ == "__main__":
    inspect_table_structure()
    inspect_triage_results_structure() 