#!/usr/bin/env python3
"""
Test script for truncation functionality to prevent GPT-4 context overflows.
"""

import sys
import os
from pathlib import Path

# Add backend to path
project_root = Path(__file__).parent.parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

from triage_core import count_tokens, truncate_for_prompt


def test_token_counting():
    """Test token counting functionality."""
    print("🧪 Testing token counting...")
    
    # Test simple text
    simple_text = "Hello world"
    token_count = count_tokens(simple_text)
    print(f"  Simple text: '{simple_text}' -> {token_count} tokens")
    
    # Test longer text
    longer_text = "This is a longer piece of text that should have more tokens when counted properly."
    token_count = count_tokens(longer_text)
    print(f"  Longer text: '{longer_text}' -> {token_count} tokens")
    
    # Test very long text
    very_long_text = "Hello world " * 1000
    token_count = count_tokens(very_long_text)
    print(f"  Very long text: {len(very_long_text)} characters -> {token_count} tokens")
    
    print("✅ Token counting tests completed")


def test_truncation():
    """Test truncation functionality."""
    print("\n🧪 Testing truncation...")
    
    # Test short text (should not be truncated)
    short_text = "This is a short text that should not be truncated."
    truncated = truncate_for_prompt(short_text, max_tokens=100)
    print(f"  Short text: {len(short_text)} chars -> {len(truncated)} chars (truncated: {len(short_text) != len(truncated)})")
    
    # Test long text (should be truncated)
    long_text = "Hello world " * 1000
    truncated = truncate_for_prompt(long_text, max_tokens=50)
    print(f"  Long text: {len(long_text)} chars -> {len(truncated)} chars (truncated: {len(long_text) != len(truncated)})")
    
    # Test very long text with different max_tokens
    very_long_text = "Hello world " * 2000
    truncated_100 = truncate_for_prompt(very_long_text, max_tokens=100)
    truncated_500 = truncate_for_prompt(very_long_text, max_tokens=500)
    print(f"  Very long text: {len(very_long_text)} chars")
    print(f"    max_tokens=100: {len(truncated_100)} chars")
    print(f"    max_tokens=500: {len(truncated_500)} chars")
    
    print("✅ Truncation tests completed")


def test_tiktoken_availability():
    """Test tiktoken availability."""
    print("\n🧪 Testing tiktoken availability...")
    
    try:
        import tiktoken
        print("✅ tiktoken is available")
        
        # Test encoding
        encoding = tiktoken.get_encoding("cl100k_base")
        test_text = "Hello world"
        tokens = encoding.encode(test_text)
        decoded = encoding.decode(tokens)
        print(f"  Encoding test: '{test_text}' -> {len(tokens)} tokens -> '{decoded}'")
        
    except ImportError:
        print("⚠️  tiktoken is not available, using fallback")
    except Exception as e:
        print(f"❌ Error with tiktoken: {str(e)}")
    
    print("✅ tiktoken availability test completed")


def main():
    """Main test function."""
    print("🧪 Testing Truncation Functionality")
    print("=" * 50)
    
    test_tiktoken_availability()
    test_token_counting()
    test_truncation()
    
    print("\n🎉 All truncation tests completed!")


if __name__ == "__main__":
    main() 