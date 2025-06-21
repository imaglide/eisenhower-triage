#!/usr/bin/env python3
"""
Test script for batch processing functionality.
"""

import sys
import os
from pathlib import Path

# Add backend to path
project_root = Path(__file__).parent.parent
backend_path = project_root / "backend"
scripts_path = project_root / "scripts"
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(scripts_path))

from run_batch_from_eml import extract_email_content, extract_body_content, generate_embedding
from email import message_from_string


def test_email_parsing():
    """Test email parsing functionality."""
    print("Testing email parsing...")
    
    # Test simple email
    simple_email = """From: test@example.com
To: recipient@example.com
Subject: Test Subject
Message-ID: <test-123@example.com>
Content-Type: text/plain

This is a test email body.
"""
    
    msg = message_from_string(simple_email)
    body = extract_body_content(msg)
    
    print(f"Simple email body: {body}")
    assert "test email body" in body
    print("✅ Simple email parsing works")
    
    # Test multipart email
    multipart_email = """From: test@example.com
To: recipient@example.com
Subject: Test Multipart
Message-ID: <test-456@example.com>
MIME-Version: 1.0
Content-Type: multipart/alternative; boundary=\"boundary123\"

--boundary123
Content-Type: text/plain; charset=UTF-8

Plain text version
--boundary123
Content-Type: text/html; charset=UTF-8

<html><body>HTML version</body></html>
--boundary123--
"""
    
    msg = message_from_string(multipart_email)
    body = extract_body_content(msg)
    
    print(f"Multipart email body: {body}")
    assert "Plain text version" in body
    print("✅ Multipart email parsing works")
    
    return True


def test_eml_file_parsing():
    """Test parsing of actual .eml files."""
    print("\nTesting .eml file parsing...")
    
    eml_dir = Path("./data/sample_emails/eml_files")
    if not eml_dir.exists():
        print("❌ ./data/sample_emails/eml_files directory not found")
        return False
    
    eml_files = list(eml_dir.glob("*.eml"))
    if not eml_files:
        print("❌ No .eml files found")
        return False
    
    print(f"Found {len(eml_files)} .eml files")
    
    success_count = 0
    fail_count = 0
    for eml_file in eml_files[:3]:  # Test first 3 files
        print(f"\nTesting {eml_file.name}...")
        
        email_data = extract_email_content(eml_file)
        if email_data:
            print(f"  Subject: {email_data['subject']}")
            print(f"  From: {email_data['from']}")
            print(f"  Message-ID: {email_data['message_id']}")
            print(f"  Body length: {len(email_data['body'])} characters")
            print(f"  Body preview: {email_data['body'][:100]}...")
            print("  ✅ File parsed successfully")
            success_count += 1
        else:
            print("  ❌ Failed to parse file")
            fail_count += 1
    
    print(f"\nSummary: {success_count} parsed successfully, {fail_count} failed.")
    if success_count == 0:
        return False
    return True


def test_embedding_generation():
    """Test embedding generation (requires OpenAI API key)."""
    print("\nTesting embedding generation...")
    
    # Check if OpenAI API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OpenAI API key not found, skipping embedding test")
        return True
    
    test_text = "This is a test email for embedding generation."
    embedding = generate_embedding(test_text)
    
    if embedding:
        print(f"✅ Embedding generated successfully")
        print(f"  Embedding length: {len(embedding)}")
        print(f"  First few values: {embedding[:5]}")
    else:
        print("❌ Failed to generate embedding")
        return False
    
    return True


def test_configuration():
    """Test configuration validation."""
    print("\nTesting configuration...")
    
    from config import Config
    
    if Config.validate():
        print("✅ Configuration is valid")
        return True
    else:
        print("❌ Configuration validation failed")
        print("Please check your .env file for required variables:")
        print("  - OPENAI_API_KEY")
        print("  - SUPABASE_URL")
        print("  - SUPABASE_KEY")
        return False


def main():
    """Main test function."""
    print("🧪 Testing Batch Processing Module")
    print("=" * 50)
    
    tests = [
        ("Configuration", test_configuration),
        ("Email Parsing", test_email_parsing),
        ("EML File Parsing", test_eml_file_parsing),
        ("Embedding Generation", test_embedding_generation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                print(f"✅ {test_name} test passed")
                passed += 1
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {str(e)}")
    
    print(f"\n{'='*50}")
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        print("\nYou can now run the batch processing script:")
        print("  python scripts/run_batch_from_eml.py")
    else:
        print(f"⚠️  {total - passed} test(s) failed")
        print("Please fix the issues before running batch processing.")


if __name__ == "__main__":
    main() 