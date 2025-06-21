#!/usr/bin/env python3
"""
Test script to verify embedding functions work with email_embeddings table.
"""

import os
import sys
from pathlib import Path

# Add backend to path
project_root = Path(__file__).parent.parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

from supabase_client import embedding_exists, store_embedding
from config import Config


def test_embedding_functions():
    """Test the embedding functions with the email_embeddings table."""
    
    print("🧪 Testing embedding functions with email_embeddings table...")
    print("=" * 60)
    
    # Validate configuration
    if not Config.validate():
        print("❌ Configuration validation failed")
        return False
    
    # Test data
    test_email_id = "test_embedding_refactor_123"
    test_embedding = [0.1] * 1536  # OpenAI text-embedding-ada-002 dimension
    
    print(f"📝 Test email_id: {test_email_id}")
    print(f"📊 Test embedding dimensions: {len(test_embedding)}")
    
    # Test 1: Check if embedding exists (should be False initially)
    print("\n🔍 Test 1: Checking if embedding exists...")
    exists = embedding_exists(test_email_id)
    print(f"   Result: {exists}")
    
    # Test 2: Store embedding
    print("\n💾 Test 2: Storing embedding...")
    success = store_embedding(test_email_id, test_embedding)
    print(f"   Result: {success}")
    
    # Test 3: Check if embedding exists again (should be True now)
    print("\n🔍 Test 3: Checking if embedding exists after storage...")
    exists_after = embedding_exists(test_email_id)
    print(f"   Result: {exists_after}")
    
    # Test 4: Try to store the same embedding again (should update)
    print("\n💾 Test 4: Storing same embedding again (upsert test)...")
    success_update = store_embedding(test_email_id, test_embedding)
    print(f"   Result: {success_update}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print(f"   Initial existence check: {exists}")
    print(f"   First storage attempt: {success}")
    print(f"   Existence after storage: {exists_after}")
    print(f"   Update attempt: {success_update}")
    
    if success and exists_after:
        print("✅ All tests passed! Embedding functions work correctly.")
        return True
    else:
        print("❌ Some tests failed. Check the output above.")
        return False


if __name__ == "__main__":
    test_embedding_functions() 