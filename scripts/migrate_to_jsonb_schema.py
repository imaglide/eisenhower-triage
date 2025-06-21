#!/usr/bin/env python3
"""
Migration script to convert triage_results table from flat columns to JSONB fields.
Run this script after updating your database schema to use JSONB fields.
"""

import os
import sys
import json
from pathlib import Path

# Add backend to path
project_root = Path(__file__).parent.parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

from supabase_client import supabase


def migrate_triage_results_to_jsonb():
    """Migrate existing triage_results from flat columns to JSONB fields."""
    
    print("🔄 Migrating triage_results to JSONB schema...")
    print("=" * 60)
    
    try:
        # First, check if the new JSONB columns exist
        print("🔍 Checking if JSONB columns exist...")
        test_data = {
            "message_id": "migration_test",
            "triage_email_only": {
                "quadrant": "do",
                "confidence": 0.85,
                "reasoning": "Migration test"
            },
            "triage_with_context": {
                "quadrant": "do",
                "confidence": 0.92,
                "reasoning": "Migration test"
            }
        }
        
        # Try to insert test data
        response = supabase.table("triage_results").insert(test_data).execute()
        if response.data:
            print("✅ JSONB columns exist - proceeding with migration")
            # Clean up test data
            supabase.table("triage_results").delete().eq("message_id", "migration_test").execute()
        else:
            print("❌ JSONB columns don't exist - please run the new schema first")
            return False
            
    except Exception as e:
        print(f"❌ Error checking JSONB columns: {str(e)}")
        print("Please ensure you've run the new database schema (database_schema_jsonb.sql)")
        return False
    
    try:
        # Get all existing triage results with old schema
        print("📊 Fetching existing triage results...")
        response = supabase.table("triage_results").select("*").execute()
        
        if not response.data:
            print("✅ No existing data to migrate")
            return True
        
        existing_results = response.data
        print(f"📝 Found {len(existing_results)} existing triage results to migrate")
        
        migrated_count = 0
        failed_count = 0
        
        for result in existing_results:
            try:
                message_id = result.get("message_id")
                if not message_id:
                    print(f"⚠️  Skipping result without message_id: {result}")
                    continue
                
                # Convert old flat columns to JSONB structure
                email_only_data = {}
                context_data = {}
                
                # Map old columns to new JSONB structure
                if "email_only_quadrant" in result:
                    email_only_data["quadrant"] = result["email_only_quadrant"]
                if "email_only_confidence" in result:
                    email_only_data["confidence"] = result["email_only_confidence"]
                if "email_only_reasoning" in result:
                    email_only_data["reasoning"] = result["email_only_reasoning"]
                
                if "contextual_quadrant" in result:
                    context_data["quadrant"] = result["contextual_quadrant"]
                if "contextual_confidence" in result:
                    context_data["confidence"] = result["contextual_confidence"]
                if "contextual_reasoning" in result:
                    context_data["reasoning"] = result["contextual_reasoning"]
                
                # Prepare new JSONB data
                new_data = {
                    "message_id": message_id,
                    "triage_email_only": email_only_data if email_only_data else None,
                    "triage_with_context": context_data if context_data else None
                }
                
                # Update the record with new JSONB structure
                update_response = supabase.table("triage_results").update(new_data).eq("message_id", message_id).execute()
                
                if update_response.data:
                    migrated_count += 1
                    print(f"✅ Migrated: {message_id}")
                else:
                    failed_count += 1
                    print(f"❌ Failed to migrate: {message_id}")
                    
            except Exception as e:
                failed_count += 1
                print(f"❌ Error migrating result {result.get('message_id', 'unknown')}: {str(e)}")
        
        print(f"\n📊 Migration Summary:")
        print(f"   Total records: {len(existing_results)}")
        print(f"   Successfully migrated: {migrated_count}")
        print(f"   Failed: {failed_count}")
        
        if failed_count == 0:
            print("🎉 Migration completed successfully!")
            return True
        else:
            print(f"⚠️  Migration completed with {failed_count} failures")
            return False
            
    except Exception as e:
        print(f"❌ Error during migration: {str(e)}")
        return False


def verify_migration():
    """Verify that the migration was successful."""
    
    print("\n🔍 Verifying migration...")
    print("=" * 40)
    
    try:
        # Get a sample of migrated results
        response = supabase.table("triage_results").select("*").limit(5).execute()
        
        if not response.data:
            print("⚠️  No data found to verify")
            return True
        
        print("📝 Sample migrated results:")
        for i, result in enumerate(response.data, 1):
            print(f"\n  Record {i}:")
            print(f"    Message ID: {result.get('message_id')}")
            print(f"    Email Only: {result.get('triage_email_only')}")
            print(f"    With Context: {result.get('triage_with_context')}")
        
        print("\n✅ Migration verification completed")
        return True
        
    except Exception as e:
        print(f"❌ Error during verification: {str(e)}")
        return False


def main():
    """Main migration function."""
    print("🚀 EisenhowerTriageAgent Schema Migration")
    print("=" * 60)
    print("This script migrates triage_results from flat columns to JSONB fields.")
    print("Make sure you've run the new database schema first!")
    print()
    
    # Run migration
    if migrate_triage_results_to_jsonb():
        # Verify migration
        verify_migration()
        print("\n🎉 Migration process completed!")
    else:
        print("\n❌ Migration failed. Please check the errors above.")


if __name__ == "__main__":
    main() 