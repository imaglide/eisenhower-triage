"""
Supabase client for EisenhowerTriageAgent.

This module provides functions to interact with Supabase database
for storing and retrieving email triage data, sender profiles, and embeddings.
"""

import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase client
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")

# Create Supabase client with custom options for better error handling
client_options = ClientOptions(
    schema="public",
    headers={
        "X-Client-Info": "eisenhower-triage-agent/0.1.0"
    }
)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY, options=client_options)


def get_sender_profile(email: str) -> Dict[str, Any]:
    """
    Query the 'sender_profiles' table for a row matching the email.
    
    Args:
        email: Email address to search for
        
    Returns:
        Dictionary with profile fields (email, name, role_guess, tone, typical_topics, account, etc.)
        Empty dict if not found
    """
    try:
        # Query the sender_profiles table
        response = supabase.table("sender_profiles").select("*").eq("email", email).execute()
        
        if response.data and len(response.data) > 0:
            profile = response.data[0]
            return profile
        else:
            return {}
            
    except Exception as e:
        print(f"Error querying sender profile for {email}: {str(e)}")
        return {}


def embedding_exists(email_id: str) -> bool:
    """
    Check the 'email_embeddings' table for an existing embedding by email_id.
    
    Args:
        email_id: Unique identifier for the email message
        
    Returns:
        True if embedding exists, False otherwise
    """
    try:
        response = supabase.table("email_embeddings").select("email_id").eq("email_id", email_id).execute()
        
        exists = len(response.data) > 0
        
        if exists:
            print(f"✅ Embedding already exists for email_id: {email_id} - skipping")
        else:
            print(f"📝 No existing embedding found for email_id: {email_id} - will create new")
        
        return exists
        
    except Exception as e:
        print(f"Error checking embedding existence for {email_id}: {str(e)}")
        return False


def store_embedding(email_id: str, embedding: List[float]) -> bool:
    """
    Upsert the embedding into the 'email_embeddings' table using the given email_id.
    
    Args:
        email_id: Unique identifier for the email message
        embedding: List of float values representing the embedding vector
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure embedding is 1536 dimensions
        if len(embedding) != 1536:
            print(f"❌ Embedding must be 1536 dimensions, got {len(embedding)}")
            return False
        # Prepare the data for upsert
        embedding_data = {
            "email_id": email_id,
            "embedding": embedding
            # created_at will be handled by database defaults
        }
        
        # Upsert the embedding
        response = supabase.table("email_embeddings").upsert(embedding_data).execute()
        
        if response.data:
            print(f"✅ Successfully stored/updated embedding for email_id: {email_id}")
            print(f"   Embedding vector length: {len(embedding)} dimensions")
            return True
        else:
            print(f"❌ Failed to store embedding for email_id: {email_id}")
            return False
            
    except Exception as e:
        print(f"Error storing embedding for {email_id}: {str(e)}")
        return False


def upsert_triage_result(message_id: str, email_only: Dict[str, Any], with_context: Dict[str, Any], with_embedding: Dict[str, Any], with_outcomes: Dict[str, Any]) -> bool:
    """
    Insert or update the triage results into the 'triage_results' table.
    Uses JSONB fields: triage_email_only, triage_with_context, triage_with_embedding, and triage_with_outcomes.
    
    Args:
        message_id: Unique identifier for the email message
        email_only: Dictionary with email-only classification results
        with_context: Dictionary with contextual classification results
        with_embedding: Dictionary with embedding-based classification results
        with_outcomes: Dictionary with outcome-aware classification results
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Prepare the triage result data using JSONB fields
        triage_data = {
            "message_id": message_id,
            "triage_email_only": email_only,
            "triage_with_context": with_context,
            "triage_with_embedding": with_embedding,
            "triage_with_outcomes": with_outcomes
        }
        
        # Upsert the triage result
        response = supabase.table("triage_results").upsert(triage_data).execute()
        
        if response.data:
            print(f"Successfully stored triage result for message_id: {message_id}")
            return True
        else:
            print(f"Failed to store triage result for message_id: {message_id}")
            return False
            
    except Exception as e:
        print(f"Error storing triage result for {message_id}: {str(e)}")
        return False


def create_sender_profile(email: str, profile_data: Dict[str, Any]) -> bool:
    """
    Create a new sender profile in the 'sender_profiles' table.
    
    Args:
        email: Email address for the profile
        profile_data: Dictionary with profile information
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Prepare the profile data - only include columns that exist in the actual schema
        profile = {
            "email": email,
            **profile_data
        }
        
        # Insert the profile
        response = supabase.table("sender_profiles").insert(profile).execute()
        
        if response.data:
            print(f"Successfully created sender profile for: {email}")
            return True
        else:
            print(f"Failed to create sender profile for: {email}")
            return False
            
    except Exception as e:
        print(f"Error creating sender profile for {email}: {str(e)}")
        return False


def update_sender_profile(email: str, profile_data: Dict[str, Any]) -> bool:
    """
    Update an existing sender profile in the 'sender_profiles' table.
    
    Args:
        email: Email address for the profile
        profile_data: Dictionary with updated profile information
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Update the profile
        response = supabase.table("sender_profiles").update(profile_data).eq("email", email).execute()
        
        if response.data:
            print(f"Successfully updated sender profile for: {email}")
            return True
        else:
            print(f"Failed to update sender profile for: {email}")
            return False
            
    except Exception as e:
        print(f"Error updating sender profile for {email}: {str(e)}")
        return False


def get_triage_result(message_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve triage results for a specific message_id.
    
    Args:
        message_id: Unique identifier for the email message
        
    Returns:
        Dictionary with triage results or None if not found
    """
    try:
        response = supabase.table("triage_results").select("*").eq("message_id", message_id).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        else:
            return None
            
    except Exception as e:
        print(f"Error retrieving triage result for {message_id}: {str(e)}")
        return None


def get_recent_triage_results(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get recent triage results ordered by created_at.
    
    Args:
        limit: Maximum number of results to return
        
    Returns:
        List of triage result dictionaries
    """
    try:
        response = supabase.table("triage_results").select("*").order("created_at", desc=True).limit(limit).execute()
        
        return response.data or []
        
    except Exception as e:
        print(f"Error retrieving recent triage results: {str(e)}")
        return []


def test_connection() -> bool:
    """
    Test the Supabase connection by performing a simple query.
    
    Returns:
        True if connection is successful, False otherwise
    """
    try:
        # Try to query the sender_profiles table (should exist)
        response = supabase.table("sender_profiles").select("count", count="exact").limit(1).execute()
        print("✅ Supabase connection successful")
        return True
        
    except Exception as e:
        print(f"❌ Supabase connection failed: {str(e)}")
        return False


def find_similar_emails(embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Calls match_embeddings RPC function in Supabase to find top-K similar emails.
    
    Args:
        embedding: Query embedding vector (1536 dimensions)
        top_k: Number of similar emails to return
        
    Returns:
        List of dictionaries with email_id and similarity score
    """
    try:
        response = supabase.rpc("match_embeddings", {
            "query_embedding": embedding,
            "match_count": top_k,
            "match_threshold": 0.5
        }).execute()
        
        if response.data:
            return response.data
        else:
            return []
            
    except Exception as e:
        print(f"Error in vector similarity search: {str(e)}")
        # Simple fallback: return empty list if RPC function doesn't exist
        return []


def get_triage_result_for_embedding(email_id: str) -> Optional[Dict[str, Any]]:
    """
    Get triage result with proper field access for embedding-based classification.
    
    Args:
        email_id: Unique identifier for the email message
        
    Returns:
        Dictionary with triage results or None if not found
    """
    try:
        result = get_triage_result(email_id)
        if result:
            # Extract email-only quadrant from JSONB field
            email_only_data = result.get('triage_email_only', {})
            if isinstance(email_only_data, dict):
                return {
                    'email_only_quadrant': email_only_data.get('quadrant', 'schedule'),
                    'email_only_confidence': email_only_data.get('confidence', 0.5),
                    'email_only_reasoning': email_only_data.get('reasoning', ''),
                    'contextual_quadrant': result.get('triage_with_context', {}).get('quadrant', 'schedule'),
                    'contextual_confidence': result.get('triage_with_context', {}).get('confidence', 0.5),
                    'contextual_reasoning': result.get('triage_with_context', {}).get('reasoning', '')
                }
        return None
        
    except Exception as e:
        print(f"Error getting triage result for embedding: {str(e)}")
        return None


def get_email_summary(email_id: str) -> str:
    """
    Fetches subject + truncated body or reasoning from emails_raw or triage_results.
    Fallbacks gracefully if missing.
    """
    # Try triage_results first for prior reasoning
    try:
        result = supabase.table("triage_results").select("triage_email_only").eq("message_id", email_id).execute()
        if result.data and result.data[0].get("triage_email_only"):
            return result.data[0]["triage_email_only"].get("reasoning", "")
    except Exception:
        pass

    # Else fallback to raw subject + body
    try:
        raw = supabase.table("emails_raw").select("subject, body").eq("id", email_id).execute()
        if raw.data:
            subject = raw.data[0].get("subject", "")
            body = raw.data[0].get("body", "")[:1000]  # truncate
            return f"{subject}\n{body}"
    except Exception:
        pass

    return ""


# Example usage and testing
if __name__ == "__main__":
    print("Testing Supabase client...")
    
    # Test connection
    if not test_connection():
        print("Connection test failed. Please check your Supabase configuration.")
        exit(1)
    
    # Test sender profile functions
    test_email = "test@example.com"
    
    # Create a test profile
    test_profile = {
        "name": "Test User",
        "role_guess": "colleague",
        "tone": "professional",
        "typical_topics": ["work", "IT"],
        "account": "test@example.com"
    }
    
    print(f"\nCreating test profile for {test_email}...")
    create_sender_profile(test_email, test_profile)
    
    # Retrieve the profile
    print(f"\nRetrieving profile for {test_email}...")
    profile = get_sender_profile(test_email)
    print(f"Retrieved profile: {json.dumps(profile, indent=2)}")
    
    # Test embedding functions
    test_email_id = "test_message_123"
    test_embedding = [0.1, 0.2, 0.3, 0.4, 0.5] * 307 + [0.1]  # 1536-dimensional vector (OpenAI text-embedding-ada-002)
    
    print(f"\nTesting embedding functions for {test_email_id}...")
    print(f"Embedding exists: {embedding_exists(test_email_id)}")
    
    # Store embedding
    store_embedding(test_email_id, test_embedding)
    print(f"Embedding exists after storage: {embedding_exists(test_email_id)}")
    
    # Test triage results
    test_email_result = {
        "quadrant": "do",
        "confidence": 0.85,
        "reasoning": "Urgent server issue requires immediate attention"
    }
    
    test_context_result = {
        "quadrant": "do",
        "confidence": 0.92,
        "reasoning": "Urgent server issue from IT admin requires immediate attention"
    }
    
    print(f"\nStoring triage results for {test_email_id}...")
    upsert_triage_result(test_email_id, test_email_result, test_context_result, {}, {})
    
    # Retrieve triage result
    result = get_triage_result(test_email_id)
    print(f"Retrieved triage result: {json.dumps(result, indent=2)}")
    
    print("\n✅ All tests completed!") 