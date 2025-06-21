#!/usr/bin/env python3
"""
Test script for triage_core.py module.
"""

import json
import sys
import os
from pathlib import Path

# Add backend to path
project_root = Path(__file__).parent.parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

from triage_core import triage_email_only, triage_with_context, get_quadrant_description
from config import Config


def test_configuration():
    """Test that configuration is properly loaded."""
    print("Testing configuration...")
    
    if not Config.validate():
        print("❌ Configuration validation failed")
        print("Please create a .env file with the following variables:")
        print("  OPENAI_API_KEY=your_openai_api_key")
        print("  SUPABASE_URL=your_supabase_url")
        print("  SUPABASE_KEY=your_supabase_key")
        return False
    
    print("✅ Configuration validation passed")
    Config.print_config()
    return True


def test_email_only_classification():
    """Test email-only classification."""
    print("\nTesting email-only classification...")
    
    test_cases = [
        {
            "subject": "URGENT: Server down - immediate action required",
            "body": "The production server is down and customers are affected. Please respond immediately.",
            "expected_quadrant": "do"
        },
        {
            "subject": "Weekly team meeting agenda",
            "body": "Hi team, here's the agenda for our weekly meeting on Friday. Please review and let me know if you have any items to add.",
            "expected_quadrant": "schedule"
        },
        {
            "subject": "Can you help with this task?",
            "body": "I'm swamped with work and was wondering if you could help me with this simple task. It should only take 10 minutes.",
            "expected_quadrant": "delegate"
        },
        {
            "subject": "Newsletter subscription",
            "body": "Thank you for subscribing to our newsletter! You'll receive updates about our products and services.",
            "expected_quadrant": "delete"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest case {i}: {test_case['subject']}")
        
        try:
            result = triage_email_only(test_case['subject'], test_case['body'])
            
            print(f"  Result: {result['quadrant']} (confidence: {result['confidence']:.2f})")
            print(f"  Reasoning: {result['reasoning']}")
            
            if result['quadrant'] == test_case['expected_quadrant']:
                print(f"  ✅ Expected: {test_case['expected_quadrant']}")
            else:
                print(f"  ⚠️  Expected: {test_case['expected_quadrant']}, Got: {result['quadrant']}")
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")


def test_contextual_classification():
    """Test classification with sender context."""
    print("\nTesting contextual classification...")
    
    test_subject = "Project update request"
    test_body = "Hi, could you please provide an update on the project status? We have a client meeting tomorrow."
    
    # Test with different sender profiles
    sender_profiles = [
        {
            "name": "Boss",
            "tags": ["management", "urgent"],
            "notes": "Direct supervisor, high priority contact",
            "relationship": "supervisor"
        },
        {
            "name": "Colleague",
            "tags": ["peer", "same_level"],
            "notes": "Team member, same department",
            "relationship": "peer"
        },
        {
            "name": "External Vendor",
            "tags": ["external", "vendor"],
            "notes": "Service provider, not urgent",
            "relationship": "vendor"
        }
    ]
    
    for i, profile in enumerate(sender_profiles, 1):
        print(f"\nTest case {i}: Sender = {profile['name']}")
        
        try:
            result = triage_with_context(test_subject, test_body, profile)
            
            print(f"  Result: {result['quadrant']} (confidence: {result['confidence']:.2f})")
            print(f"  Reasoning: {result['reasoning']}")
            
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")


def test_quadrant_descriptions():
    """Test quadrant description function."""
    print("\nTesting quadrant descriptions...")
    
    quadrants = ["do", "schedule", "delegate", "delete"]
    
    for quadrant in quadrants:
        description = get_quadrant_description(quadrant)
        print(f"  {quadrant}: {description}")


def main():
    """Main test function."""
    print("🧪 Testing EisenhowerTriageAgent Core Module")
    print("=" * 50)
    
    # Test configuration first
    if not test_configuration():
        print("\n❌ Configuration test failed. Please fix configuration issues before running other tests.")
        return
    
    # Run tests
    test_quadrant_descriptions()
    test_email_only_classification()
    test_contextual_classification()
    
    print("\n✅ All tests completed!")


if __name__ == "__main__":
    main() 