#!/usr/bin/env python3
"""
Test script for supabase_client.py module.
"""

import json
import sys
import os
from pathlib import Path
import time

# Add backend to path
project_root = Path(__file__).parent.parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

from supabase_client import (
    test_connection,
    get_sender_profile,
    create_sender_profile,
    update_sender_profile,
    embedding_exists,
    store_embedding,
    upsert_triage_result,
    get_triage_result,
    get_recent_triage_results
)


def test_supabase_connection():
    """Test Supabase connection."""
    print("Testing Supabase connection...")
    
    if test_connection():
        print("✅ Supabase connection successful")
        return True
    else:
        print("❌ Supabase connection failed")
        print("Please check your Supabase configuration in .env file:")
        print("  SUPABASE_URL=your_supabase_project_url")
        print("  SUPABASE_KEY=your_supabase_anon_key")
        return False


def test_sender_profiles():
    """Test sender profile functions."""
    print("\nTesting sender profile functions...")
    
    # Use a unique email address with timestamp to avoid conflicts
    timestamp = int(time.time())
    test_email = f"test.user.{timestamp}@example.com"
    
    # Test creating a profile
    print(f"Creating profile for {test_email}...")
    profile_data = {
        "name": "Test User",
        "tags": ["test", "developer", "urgent"],
        "notes": "This is a test profile for testing purposes",
        "relationship": "colleague",
        "priority": 2
    }
    
    success = create_sender_profile(test_email, profile_data)
    if success:
        print("✅ Profile created successfully")
    else:
        print("❌ Failed to create profile")
        return False
    
    # Test retrieving the profile
    print(f"Retrieving profile for {test_email}...")
    profile = get_sender_profile(test_email)
    
    if profile:
        print("✅ Profile retrieved successfully")
        print(f"Profile data: {json.dumps(profile, indent=2)}")
        
        # Verify the data
        if profile.get("name") == "Test User" and profile.get("email") == test_email:
            print("✅ Profile data matches expected values")
        else:
            print("❌ Profile data doesn't match expected values")
            return False
    else:
        print("❌ Failed to retrieve profile")
        return False
    
    # Test updating the profile
    print(f"Updating profile for {test_email}...")
    update_data = {
        "notes": "Updated notes for testing",
        "priority": 1
    }
    
    success = update_sender_profile(test_email, update_data)
    if success:
        print("✅ Profile updated successfully")
        
        # Verify the update
        updated_profile = get_sender_profile(test_email)
        if updated_profile.get("notes") == "Updated notes for testing":
            print("✅ Profile update verified")
        else:
            print("❌ Profile update not reflected")
            return False
    else:
        print("❌ Failed to update profile")
        return False
    
    return True


def test_embedding_functions():
    """Test embedding functions."""
    print("\nTesting embedding functions...")
    
    test_message_id = "test_message_12345"
    
    # Test checking if embedding exists (should be False initially)
    print(f"Checking if embedding exists for {test_message_id}...")
    exists = embedding_exists(test_message_id)
    print(f"Embedding exists: {exists}")
    
    if exists:
        print("⚠️  Embedding already exists, this might be from a previous test")
    else:
        print("✅ No existing embedding found (expected)")
    
    # Test storing an embedding
    print(f"Storing embedding for {test_message_id}...")
    test_embedding = [0.1, 0.2, 0.3, 0.4, 0.5] * 307 + [0.1]  # 1536-dimensional vector (OpenAI text-embedding-ada-002 output)
    
    success = store_embedding(test_message_id, test_embedding)
    if success:
        print("✅ Embedding stored successfully")
    else:
        print("❌ Failed to store embedding")
        return False
    
    # Test checking if embedding exists after storage
    print(f"Checking if embedding exists after storage...")
    exists = embedding_exists(test_message_id)
    print(f"Embedding exists: {exists}")
    
    if exists:
        print("✅ Embedding found after storage")
    else:
        print("❌ Embedding not found after storage")
        return False
    
    return True


def test_triage_results():
    """Test triage result functions."""
    print("\nTesting triage result functions...")

    test_message_id = "test_triage_message_67890"

    # Test storing triage results
    print(f"Storing triage results for {test_message_id}...")

    email_only_result = {
        "quadrant": "do",
        "confidence": 0.85,
        "reasoning": "Urgent server issue requires immediate attention"
    }

    contextual_result = {
        "quadrant": "do",
        "confidence": 0.92,
        "reasoning": "Urgent server issue from IT admin requires immediate attention"
    }

    embedding_result = {
        "quadrant": "do",
        "confidence": 0.88,
        "reasoning": "Similar to previous urgent server issues"
    }

    success = upsert_triage_result(test_message_id, email_only_result, contextual_result, embedding_result)
    assert success, "Failed to store triage results"

    # Test retrieving triage results
    print(f"Retrieving triage results for {test_message_id}...")
    retrieved_result = get_triage_result(test_message_id)
    assert retrieved_result is not None, "Failed to retrieve triage results"
    assert "triage_email_only" in retrieved_result, "Missing email_only result"
    assert "triage_with_context" in retrieved_result, "Missing contextual result"
    assert "triage_with_embedding" in retrieved_result, "Missing embedding result"

    print("✅ Triage result functions working correctly")
    return True


def test_error_handling():
    """Test error handling with invalid data."""
    print("\nTesting error handling...")
    
    # Test with invalid message_id
    print("Testing with invalid message_id...")
    result = get_triage_result("")
    if result is None:
        print("✅ Properly handled invalid message_id")
    else:
        print("❌ Should have returned None for invalid message_id")
    
    # Test with invalid email
    print("Testing with invalid email...")
    profile = get_sender_profile("")
    if profile == {}:
        print("✅ Properly handled invalid email")
    else:
        print("❌ Should have returned empty dict for invalid email")
    
    # Test embedding existence with invalid message_id
    print("Testing embedding existence with invalid message_id...")
    exists = embedding_exists("")
    if not exists:
        print("✅ Properly handled invalid message_id for embedding check")
    else:
        print("❌ Should have returned False for invalid message_id")
    
    return True


def main():
    """Main test function."""
    print("🧪 Testing Supabase Client Module")
    print("=" * 50)
    
    # Test connection first
    if not test_supabase_connection():
        print("\n❌ Connection test failed. Please fix Supabase configuration before running other tests.")
        return
    
    # Run all tests
    tests = [
        ("Sender Profiles", test_sender_profiles),
        ("Embedding Functions", test_embedding_functions),
        ("Triage Results", test_triage_results),
        ("Error Handling", test_error_handling)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                print(f"✅ {test_name} tests passed")
                passed += 1
            else:
                print(f"❌ {test_name} tests failed")
        except Exception as e:
            print(f"❌ {test_name} tests failed with exception: {str(e)}")
    
    print(f"\n{'='*50}")
    print(f"Test Results: {passed}/{total} test suites passed")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print(f"⚠️  {total - passed} test suite(s) failed")


if __name__ == "__main__":
    main() 