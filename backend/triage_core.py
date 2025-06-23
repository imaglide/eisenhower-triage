"""
Core email triage functionality for EisenhowerTriageAgent.

This module provides functions to classify emails into the four quadrants
of the Eisenhower Matrix using OpenAI's GPT-4 model.
"""

import os
import json
import time
import logging
from typing import Dict, Optional, List
from dotenv import load_dotenv
from openai import OpenAI
import openai

# Try to import tiktoken for token counting, fallback to character-based truncation
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    print("⚠️  tiktoken not available, using character-based truncation fallback")

# Load environment variables
load_dotenv()

# Import configuration
from backend.config import Config

# Configure OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configure logging
logger = logging.getLogger(__name__)

# Eisenhower Matrix quadrants
QUADRANTS = {
    "do": "Do (Urgent & Important) - Handle immediately",
    "schedule": "Schedule (Important but not Urgent) - Plan for later",
    "delegate": "Delegate (Urgent but not Important) - Assign to someone else",
    "delete": "Delete (Neither Urgent nor Important) - Ignore or archive"
}


def count_tokens(text: str) -> int:
    """
    Count the number of tokens in a text string using tiktoken.
    
    Args:
        text: Text to count tokens for
        
    Returns:
        Number of tokens
    """
    if TIKTOKEN_AVAILABLE:
        try:
            # Use cl100k_base encoding (GPT-4 tokenizer)
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except Exception as e:
            logger.warning(f"Error counting tokens with tiktoken: {str(e)}")
            # Fallback to character-based estimation
            return len(text) // 4  # Rough estimate: 4 characters per token
    
    # Fallback when tiktoken is not available
    return len(text) // 4  # Rough estimate: 4 characters per token


def truncate_for_prompt(text: str, max_tokens: int = 3000) -> str:
    """
    Safely truncate text to fit within GPT-4 context limits.
    
    Args:
        text: Text to truncate
        max_tokens: Maximum number of tokens to allow (default: 3000)
        
    Returns:
        Truncated text that fits within token limits
    """
    if TIKTOKEN_AVAILABLE:
        try:
            # Use cl100k_base encoding (GPT-4 tokenizer)
            encoding = tiktoken.get_encoding("cl100k_base")
            tokens = encoding.encode(text)
            
            if len(tokens) <= max_tokens:
                return text
            
            # Truncate to max_tokens and decode back to text
            truncated_tokens = tokens[:max_tokens]
            truncated_text = encoding.decode(truncated_tokens)
            
            logger.info(f"Text truncated from {len(tokens)} to {len(truncated_tokens)} tokens")
            return truncated_text
            
        except Exception as e:
            logger.warning(f"Error truncating with tiktoken: {str(e)}")
            # Fallback to character-based truncation
            return text[:8000]
    
    # Fallback when tiktoken is not available
    # Conservative estimate: 4 characters per token
    max_chars = max_tokens * 4
    if len(text) <= max_chars:
        return text
    
    truncated_text = text[:max_chars]
    logger.info(f"Text truncated from {len(text)} to {len(truncated_text)} characters (fallback mode)")
    return truncated_text


def safe_openai_chat_completion(messages: List[Dict], model="gpt-4", max_retries=5) -> Optional[Dict]:
    """
    Safely call OpenAI ChatCompletion API with retry logic and error handling.
    
    Args:
        messages: List of message dictionaries for the chat completion
        model: OpenAI model to use (default: gpt-4)
        max_retries: Maximum number of retry attempts (default: 5)
        
    Returns:
        OpenAI response dictionary or None if all retries failed
    """
    
    for attempt in range(max_retries + 1):
        try:
            print(f"OpenAI API call attempt {attempt + 1}/{max_retries + 1}")
            
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.1,  # Low temperature for consistent classification
                max_tokens=400
            )
            
            print(f"✅ OpenAI API call successful on attempt {attempt + 1}")
            return response
            
        except Exception as e:
            # Handle different types of OpenAI errors
            error_str = str(e).lower()
            
            # Rate limit errors
            if "rate limit" in error_str or "too many requests" in error_str:
                wait_time = (2 ** attempt) * 1  # Exponential backoff: 1, 2, 4, 8, 16 seconds
                print(f"⚠️  Rate limit hit on attempt {attempt + 1}. Waiting {wait_time} seconds...")
                logger.warning(f"OpenAI rate limit error on attempt {attempt + 1}: {str(e)}")
                
                if attempt < max_retries:
                    time.sleep(wait_time)
                else:
                    print(f"❌ Rate limit error after {max_retries + 1} attempts. Giving up.")
                    logger.error(f"OpenAI rate limit error after {max_retries + 1} attempts")
                    return None
                    
            # Timeout errors
            elif "timeout" in error_str:
                wait_time = (2 ** attempt) * 0.5  # Shorter backoff for timeouts: 0.5, 1, 2, 4, 8 seconds
                print(f"⚠️  Timeout on attempt {attempt + 1}. Waiting {wait_time} seconds...")
                logger.warning(f"OpenAI timeout error on attempt {attempt + 1}: {str(e)}")
                
                if attempt < max_retries:
                    time.sleep(wait_time)
                else:
                    print(f"❌ Timeout error after {max_retries + 1} attempts. Giving up.")
                    logger.error(f"OpenAI timeout error after {max_retries + 1} attempts")
                    return None
                    
            # Connection errors
            elif "connection" in error_str or "network" in error_str:
                wait_time = (2 ** attempt) * 1  # Exponential backoff for connection errors
                print(f"⚠️  API connection error on attempt {attempt + 1}. Waiting {wait_time} seconds...")
                logger.warning(f"OpenAI connection error on attempt {attempt + 1}: {str(e)}")
                
                if attempt < max_retries:
                    time.sleep(wait_time)
                else:
                    print(f"❌ Connection error after {max_retries + 1} attempts. Giving up.")
                    logger.error(f"OpenAI connection error after {max_retries + 1} attempts")
                    return None
                    
            # Billing/quota errors
            elif "quota" in error_str or "billing" in error_str:
                print(f"❌ Billing/quota error on attempt {attempt + 1}. No retry.")
                logger.error(f"OpenAI billing/quota error: {str(e)}")
                return None
                
            # Other API errors
            else:
                wait_time = (2 ** attempt) * 1
                print(f"⚠️  API error on attempt {attempt + 1}. Waiting {wait_time} seconds...")
                logger.warning(f"OpenAI API error on attempt {attempt + 1}: {str(e)}")
                
                if attempt < max_retries:
                    time.sleep(wait_time)
                else:
                    print(f"❌ API error after {max_retries + 1} attempts. Giving up.")
                    logger.error(f"OpenAI API error after {max_retries + 1} attempts")
                    return None
    
    return None


def format_eisenhower_prompt(subject: str, body: str, sender_profile: Optional[Dict] = None) -> str:
    """
    Format the complete prompt for OpenAI classification.
    
    Args:
        subject: Email subject line
        body: Email body content
        sender_profile: Optional dictionary with sender context
        
    Returns:
        Formatted prompt string for OpenAI
    """
    
    # Base prompt explaining the Eisenhower Matrix
    prompt = f"""You are an expert email triage assistant. Your task is to classify emails using the Eisenhower Matrix, which divides tasks into four quadrants:

{QUADRANTS['do']}
{QUADRANTS['schedule']}
{QUADRANTS['delegate']}
{QUADRANTS['delete']}

Please analyze the following email and classify it into one of these four quadrants.

Email Subject: {subject}
Email Body: {body}"""

    # Add sender context if available
    if sender_profile:
        prompt += f"\n\nSender Context: {json.dumps(sender_profile, indent=2)}"
    
    # Add classification instructions
    prompt += """

Please provide your classification in the following JSON format:
{
    "quadrant": "do|schedule|delegate|delete",
    "confidence": 0.85,
    "reasoning": "Brief explanation of why this classification was chosen"
}

Guidelines:
- "do": Requires immediate attention, high priority, time-sensitive
- "schedule": Important but can wait, plan for dedicated time
- "delegate": Can be handled by someone else, not your core responsibility
- "delete": Low value, can be ignored or archived

Confidence should be between 0.0 and 1.0, where 1.0 is completely certain.
Reasoning should be concise but explain the key factors that led to this classification.

Respond with only the JSON object, no additional text."""

    return prompt


def triage_email_only(subject: str, body: str) -> Dict:
    """
    Classifies the email using only the subject and body.
    
    Args:
        subject: Email subject line
        body: Email body content
        
    Returns:
        Dictionary with classification results:
        {"quadrant": ..., "confidence": ..., "reasoning": ...}
    """
    
    if not client.api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    
    # Validate email content before processing
    if not validate_email_content(subject, body):
        return {
            "quadrant": "delete",
            "confidence": 0.9,
            "reasoning": "Email has insufficient content for meaningful triage - likely spam or empty message"
        }
    
    # Check for meeting notifications
    if is_meeting_notification(subject, body):
        return {
            "quadrant": "delete",
            "confidence": 0.95,
            "reasoning": "Meeting acceptance/rejection notification - no action required"
        }
    
    try:
        # Truncate body to prevent GPT-4 context overflow
        original_body_length = len(body)
        body = truncate_for_prompt(body, max_tokens=3000)
        if len(body) != original_body_length:
            logger.info(f"Body truncated from {original_body_length} to {len(body)} characters for triage")
        
        # Format the prompt without sender context
        prompt = format_eisenhower_prompt(subject, body)
        
        # Use safe OpenAI call with retry logic
        response = safe_openai_chat_completion([
            {"role": "system", "content": "You are an expert email triage assistant specializing in the Eisenhower Matrix."},
            {"role": "user", "content": prompt}
        ])
        
        # Handle API failure
        if response is None:
            print("❌ OpenAI API call failed, returning fallback response")
            return {
                "quadrant": "delegate",
                "confidence": 0.1,
                "reasoning": "Fallback due to OpenAI failure"
            }
        
        # Extract and parse the response
        content = response.choices[0].message.content.strip()
        
        # Try to parse JSON response
        try:
            result = json.loads(content)
            
            # Validate the response structure
            required_keys = ["quadrant", "confidence", "reasoning"]
            if not all(key in result for key in required_keys):
                raise ValueError("Missing required keys in response")
            
            # Validate quadrant
            if result["quadrant"] not in QUADRANTS:
                raise ValueError(f"Invalid quadrant: {result['quadrant']}")
            
            # Validate confidence score
            confidence = float(result["confidence"])
            if not 0.0 <= confidence <= 1.0:
                raise ValueError(f"Confidence must be between 0.0 and 1.0, got: {confidence}")
            
            return result
            
        except json.JSONDecodeError:
            # Fallback: try to extract information from text response
            print("⚠️  Failed to parse OpenAI JSON response, using fallback")
            return {
                "quadrant": "schedule",  # Default to schedule if parsing fails
                "confidence": 0.5,
                "reasoning": f"Failed to parse OpenAI response: {content[:100]}..."
            }
            
    except Exception as e:
        # Return a safe fallback in case of unexpected errors
        print(f"❌ Unexpected error in triage_email_only: {str(e)}")
        logger.error(f"Unexpected error in triage_email_only: {str(e)}")
        return {
            "quadrant": "delegate",
            "confidence": 0.1,
            "reasoning": f"Fallback due to error: {str(e)}"
        }


def triage_with_context(subject: str, body: str, sender_profile: Dict) -> Dict:
    """
    Classifies the email using subject, body, and sender profile context.
    
    Args:
        subject: Email subject line
        body: Email body content
        sender_profile: Dictionary with sender context (tags, notes, linked_accounts, etc.)
        
    Returns:
        Dictionary with classification results:
        {"quadrant": ..., "confidence": ..., "reasoning": ...}
    """
    
    if not client.api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    
    # Validate email content before processing
    if not validate_email_content(subject, body):
        return {
            "quadrant": "delete",
            "confidence": 0.9,
            "reasoning": "Email has insufficient content for meaningful triage - likely spam or empty message"
        }
    
    # Check for meeting notifications
    if is_meeting_notification(subject, body):
        return {
            "quadrant": "delete",
            "confidence": 0.95,
            "reasoning": "Meeting acceptance/rejection notification - no action required"
        }
    
    try:
        # Truncate body to prevent GPT-4 context overflow
        original_body_length = len(body)
        body = truncate_for_prompt(body, max_tokens=3000)
        if len(body) != original_body_length:
            logger.info(f"Body truncated from {original_body_length} to {len(body)} characters for triage")
        
        # Format the prompt with sender context
        prompt = format_eisenhower_prompt(subject, body, sender_profile)
        
        # Use safe OpenAI call with retry logic
        response = safe_openai_chat_completion([
            {"role": "system", "content": "You are an expert email triage assistant specializing in the Eisenhower Matrix. Consider the sender's context when making your classification."},
            {"role": "user", "content": prompt}
        ])
        
        # Handle API failure
        if response is None:
            print("❌ OpenAI API call failed, returning fallback response")
            return {
                "quadrant": "delegate",
                "confidence": 0.1,
                "reasoning": "Fallback due to OpenAI failure"
            }
        
        # Extract and parse the response
        content = response.choices[0].message.content.strip()
        
        # Try to parse JSON response
        try:
            result = json.loads(content)
            
            # Validate the response structure
            required_keys = ["quadrant", "confidence", "reasoning"]
            if not all(key in result for key in required_keys):
                raise ValueError("Missing required keys in response")
            
            # Validate quadrant
            if result["quadrant"] not in QUADRANTS:
                raise ValueError(f"Invalid quadrant: {result['quadrant']}")
            
            # Validate confidence score
            confidence = float(result["confidence"])
            if not 0.0 <= confidence <= 1.0:
                raise ValueError(f"Confidence must be between 0.0 and 1.0, got: {confidence}")
            
            return result
            
        except json.JSONDecodeError:
            # Fallback: try to extract information from text response
            print("⚠️  Failed to parse OpenAI JSON response, using fallback")
            return {
                "quadrant": "schedule",  # Default to schedule if parsing fails
                "confidence": 0.5,
                "reasoning": f"Failed to parse OpenAI response: {content[:100]}..."
            }
            
    except Exception as e:
        # Return a safe fallback in case of unexpected errors
        print(f"❌ Unexpected error in triage_with_context: {str(e)}")
        logger.error(f"Unexpected error in triage_with_context: {str(e)}")
        return {
            "quadrant": "delegate",
            "confidence": 0.1,
            "reasoning": f"Fallback due to error: {str(e)}"
        }


def get_quadrant_description(quadrant: str) -> str:
    """
    Get a human-readable description of a quadrant.
    
    Args:
        quadrant: The quadrant key (do, schedule, delegate, delete)
        
    Returns:
        Description string
    """
    return QUADRANTS.get(quadrant, "Unknown quadrant")


def validate_email_content(subject: str, body: str) -> bool:
    """
    Validate that email has sufficient content for meaningful triage.
    
    Args:
        subject: Email subject line
        body: Email body content
        
    Returns:
        True if email has sufficient content, False otherwise
    """
    # Check if body is empty or too short
    if not body or not body.strip():
        logger.warning("Email body is empty or contains only whitespace")
        return False
    
    # Check if body is too short (less than 10 characters)
    if len(body.strip()) < 10:
        logger.warning(f"Email body too short ({len(body.strip())} characters) for meaningful triage")
        return False
    
    # Check if subject is empty
    if not subject or not subject.strip():
        logger.warning("Email subject is empty")
        return False
    
    return True


def is_meeting_notification(subject: str, body: str) -> bool:
    """
    Detect if email is a meeting acceptance/rejection notification.
    
    Args:
        subject: Email subject line
        body: Email body content
        
    Returns:
        True if email is a meeting notification, False otherwise
    """
    # Convert to lowercase for case-insensitive matching
    subject_lower = subject.lower()
    body_lower = body.lower()
    
    # Common meeting notification patterns in subjects
    meeting_subject_patterns = [
        'accepted:', 'declined:', 'tentative:', 'proposed:',
        'accepted -', 'declined -', 'tentative -', 'proposed -',
        'meeting accepted', 'meeting declined', 'meeting tentative',
        'calendar invitation', 'calendar update',
        'outlook meeting', 'teams meeting',
        'zoom meeting', 'webex meeting',
        'meeting response', 'meeting reply',
        'accepted meeting', 'declined meeting',
        'tentative meeting', 'proposed meeting'
    ]
    
    # Common meeting notification patterns in body
    meeting_body_patterns = [
        'accepted this meeting',
        'declined this meeting', 
        'tentatively accepted this meeting',
        'proposed a new time',
        'meeting has been accepted',
        'meeting has been declined',
        'meeting has been tentatively accepted',
        'calendar invitation',
        'outlook meeting',
        'teams meeting',
        'zoom meeting',
        'webex meeting',
        'meeting response',
        'meeting reply'
    ]
    
    # Check subject patterns
    for pattern in meeting_subject_patterns:
        if pattern in subject_lower:
            logger.info(f"Detected meeting notification in subject: '{pattern}'")
            return True
    
    # Check body patterns (only if body is not too long to avoid false positives)
    if len(body_lower) < 500:  # Only check short bodies to avoid false positives
        for pattern in meeting_body_patterns:
            if pattern in body_lower:
                logger.info(f"Detected meeting notification in body: '{pattern}'")
                return True
    
    return False


def triage_with_embeddings(subject: str, body: str, email_id: str) -> Dict:
    """
    Classifies the email using embedding similarity to previously classified emails.
    
    Args:
        subject: Email subject line
        body: Email body content
        email_id: Unique email identifier
        
    Returns:
        Dictionary with classification results:
        {"quadrant": ..., "confidence": ..., "reasoning": ...}
    """
    
    # Validate email content before processing
    if not validate_email_content(subject, body):
        return {
            "quadrant": "delete",
            "confidence": 0.9,
            "reasoning": "Email has insufficient content for meaningful triage - likely spam or empty message"
        }
    
    # Check for meeting notifications
    if is_meeting_notification(subject, body):
        return {
            "quadrant": "delete",
            "confidence": 0.95,
            "reasoning": "Meeting acceptance/rejection notification - no action required"
        }
    
    try:
        # Import here to avoid circular imports
        from supabase_client import find_similar_emails, get_triage_result, embedding_exists, store_embedding
        
        # Generate embedding for the current email
        combined_text = f"Subject: {subject}\n\nBody: {body}"
        
        # Use tiktoken for precise truncation if available
        if TIKTOKEN_AVAILABLE:
            try:
                encoding = tiktoken.get_encoding("cl100k_base")
                tokens = encoding.encode(combined_text)
                max_tokens = 8000  # OpenAI embedding limit
                if len(tokens) > max_tokens:
                    truncated_tokens = tokens[:max_tokens]
                    combined_text = encoding.decode(truncated_tokens)
                    logger.info(f"Text truncated from {len(tokens)} to {len(truncated_tokens)} tokens for embedding")
            except Exception as e:
                logger.warning(f"Error truncating with tiktoken: {str(e)}")
                # Fallback to character-based truncation
                combined_text = combined_text[:32000]  # Conservative limit
        else:
            # Fallback when tiktoken is not available
            combined_text = combined_text[:32000]
        
        # Generate embedding
        response = client.embeddings.create(
            input=combined_text,
            model=Config.EMBEDDING_MODEL
        )
        
        current_embedding = response.data[0].embedding
        
        # Store the embedding if it doesn't exist
        if not embedding_exists(email_id):
            store_embedding(email_id, current_embedding)
        
        # Find similar emails using vector similarity search
        similar_emails = find_similar_emails(current_embedding, top_k=5)
        
        if not similar_emails:
            logger.warning(f"No similar emails found for {email_id}, using fallback")
            return {
                "quadrant": "schedule",
                "confidence": 0.3,
                "reasoning": "No similar emails found in database for embedding-based classification"
            }
        
        # Build similar contexts string
        similar_contexts = []
        for similar_email in similar_emails:
            similar_email_id = similar_email.get('email_id', 'unknown_id')
            similarity_score = similar_email.get('score', 0.5)
            
            # Get triage result for similar email
            triage_result = get_triage_result(similar_email_id)
            if triage_result:
                email_only_data = triage_result.get('triage_email_only', {})
                if isinstance(email_only_data, dict):
                    quadrant = email_only_data.get('quadrant', 'schedule')
                    reasoning = email_only_data.get('reasoning', 'No reasoning available')
                    similar_contexts.append(f"- {similar_email_id} (score: {similarity_score:.2f}): {quadrant} - {reasoning[:100]}...")
        
        if not similar_contexts:
            logger.warning(f"No valid triage results found for similar emails to {email_id}")
            return {
                "quadrant": "schedule",
                "confidence": 0.3,
                "reasoning": "No valid triage results found for similar emails"
            }
        
        # Use GPT-4 to classify based on similar examples
        similar_contexts_text = "\n".join(similar_contexts)
        embedding_result = triage_with_embedding(subject, body, similar_contexts_text)
        
        return embedding_result
        
    except Exception as e:
        logger.error(f"Error in embedding-based triage for {email_id}: {str(e)}")
        return {
            "quadrant": "schedule",
            "confidence": 0.3,
            "reasoning": f"Fallback due to embedding triage error: {str(e)}"
        }


def triage_with_embedding(subject: str, body: str, similar_contexts: str) -> Dict:
    """
    Use GPT-4 to classify an email based on its content and summaries of similar emails.
    
    Args:
        subject: Email subject line
        body: Email body content
        similar_contexts: String containing summaries of similar past emails
        
    Returns:
        Dictionary with classification results:
        {"quadrant": ..., "confidence": ..., "reasoning": ...}
    """
    
    if not client.api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    
    # Validate email content before processing
    if not validate_email_content(subject, body):
        return {
            "quadrant": "delete",
            "confidence": 0.9,
            "reasoning": "Email has insufficient content for meaningful triage - likely spam or empty message"
        }
    
    # Check for meeting notifications
    if is_meeting_notification(subject, body):
        return {
            "quadrant": "delete",
            "confidence": 0.95,
            "reasoning": "Meeting acceptance/rejection notification - no action required"
        }
    
    try:
        # Truncate body to prevent GPT-4 context overflow
        original_body_length = len(body)
        body = truncate_for_prompt(body, max_tokens=2000)  # Smaller limit to leave room for similar contexts
        if len(body) != original_body_length:
            logger.info(f"Body truncated from {original_body_length} to {len(body)} characters for embedding triage")
        
        # Create the prompt for embedding-based classification
        prompt = f"""You are an expert email triage assistant. Classify this email based on its content and these similar examples from the database:

{QUADRANTS['do']}
{QUADRANTS['schedule']}
{QUADRANTS['delegate']}
{QUADRANTS['delete']}

Similar examples from database:
{similar_contexts}

Email to classify:
Subject: {subject}
Body: {body}

Please provide your classification in the following JSON format:
{{
    "quadrant": "do|schedule|delegate|delete",
    "confidence": 0.85,
    "reasoning": "Brief explanation of why this classification was chosen, considering the similar examples"
}}

Guidelines:
- Consider how similar emails were classified
- "do": Requires immediate attention, high priority, time-sensitive
- "schedule": Important but can wait, plan for dedicated time
- "delegate": Can be handled by someone else, not your core responsibility
- "delete": Low value, can be ignored or archived

Confidence should be between 0.0 and 1.0, where 1.0 is completely certain.
Reasoning should explain how the similar examples influenced your decision.

Respond with only the JSON object, no additional text."""

        # Use safe OpenAI call with retry logic
        response = safe_openai_chat_completion([
            {"role": "system", "content": "You are an expert email triage assistant specializing in the Eisenhower Matrix. Use similar examples to inform your classification."},
            {"role": "user", "content": prompt}
        ])
        
        # Handle API failure
        if response is None:
            print("❌ OpenAI API call failed for embedding triage, returning fallback response")
            return {
                "quadrant": "schedule",
                "confidence": 0.3,
                "reasoning": "Fallback due to OpenAI failure in embedding triage"
            }
        
        # Extract and parse the response
        content = response.choices[0].message.content.strip()
        
        # Try to parse JSON response
        try:
            result = json.loads(content)
            
            # Validate the response structure
            required_keys = ["quadrant", "confidence", "reasoning"]
            if not all(key in result for key in required_keys):
                raise ValueError("Missing required keys in response")
            
            # Validate quadrant
            if result["quadrant"] not in QUADRANTS:
                raise ValueError(f"Invalid quadrant: {result['quadrant']}")
            
            # Validate confidence score
            confidence = float(result["confidence"])
            if not 0.0 <= confidence <= 1.0:
                raise ValueError(f"Confidence must be between 0.0 and 1.0, got: {confidence}")
            
            return result
            
        except json.JSONDecodeError:
            # Fallback: try to extract information from text response
            print("⚠️  Failed to parse OpenAI JSON response for embedding triage, using fallback")
            return {
                "quadrant": "schedule",  # Default to schedule if parsing fails
                "confidence": 0.5,
                "reasoning": f"Failed to parse OpenAI response for embedding triage: {content[:100]}..."
            }
            
    except Exception as e:
        # Return a safe fallback in case of unexpected errors
        print(f"❌ Unexpected error in triage_with_embedding: {str(e)}")
        logger.error(f"Unexpected error in triage_with_embedding: {str(e)}")
        return {
            "quadrant": "schedule",
            "confidence": 0.3,
            "reasoning": f"Fallback due to error in embedding triage: {str(e)}"
        }


def triage_with_outcomes(subject: str, body: str, similar_contexts: str, past_triage_results: List[Dict]) -> Dict:
    """
    Classify the email using GPT-4, incorporating known outcomes of similar past emails.
    
    Args:
        subject: Email subject line
        body: Email body content
        similar_contexts: String containing summaries of similar past emails
        past_triage_results: List of dictionaries with past triage results
        
    Returns:
        Dictionary with classification results:
        {"quadrant": ..., "confidence": ..., "reasoning": ...}
    """
    
    if not client.api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    
    # Validate email content before processing
    if not validate_email_content(subject, body):
        return {
            "quadrant": "delete",
            "confidence": 0.9,
            "reasoning": "Email has insufficient content for meaningful triage - likely spam or empty message"
        }
    
    # Check for meeting notifications
    if is_meeting_notification(subject, body):
        return {
            "quadrant": "delete",
            "confidence": 0.95,
            "reasoning": "Meeting acceptance/rejection notification - no action required"
        }
    
    try:
        # Truncate body to prevent GPT-4 context overflow
        original_body_length = len(body)
        body = truncate_for_prompt(body, max_tokens=2000)  # Smaller limit to leave room for outcomes
        if len(body) != original_body_length:
            logger.info(f"Body truncated from {original_body_length} to {len(body)} characters for outcomes triage")
        
        # Build outcome summary from past triage results
        outcome_summary = "\n".join([
            f"- {res.get('message_id', 'unknown_id')}: labeled as {res.get('triage_email_only', {}).get('quadrant', 'unknown')} (conf: {res.get('triage_email_only', {}).get('confidence', 0.0)})"
            for res in past_triage_results
        ])
        
        # Handle empty outcome summary
        if not outcome_summary:
            outcome_summary = "No past triage results available for reference."
        
        # Create the prompt for outcome-aware classification
        prompt = f"""You are an expert email triage assistant. Classify this email based on its content, similar examples, and the outcomes of past similar emails:

{QUADRANTS['do']}
{QUADRANTS['schedule']}
{QUADRANTS['delegate']}
{QUADRANTS['delete']}

Similar examples from database:
{similar_contexts}

Past triage outcomes:
{outcome_summary}

Email to classify:
Subject: {subject}
Body: {body}

Please provide your classification in the following JSON format:
{{
    "quadrant": "do|schedule|delegate|delete",
    "confidence": 0.85,
    "reasoning": "Brief explanation of why this classification was chosen, considering the similar examples and past outcomes"
}}

Guidelines:
- Consider how similar emails were classified and their outcomes
- "do": Requires immediate attention, high priority, time-sensitive
- "schedule": Important but can wait, plan for dedicated time
- "delegate": Can be handled by someone else, not your core responsibility
- "delete": Low value, can be ignored or archived

Confidence should be between 0.0 and 1.0, where 1.0 is completely certain.
Reasoning should explain how the similar examples and past outcomes influenced your decision.

Respond with only the JSON object, no additional text."""

        # Use safe OpenAI call with retry logic
        response = safe_openai_chat_completion([
            {"role": "system", "content": "You are an expert email triage assistant specializing in the Eisenhower Matrix. Use similar examples and past outcomes to inform your classification."},
            {"role": "user", "content": prompt}
        ])
        
        # Handle API failure
        if response is None:
            print("❌ OpenAI API call failed for outcomes triage, returning fallback response")
            return {
                "quadrant": "schedule",
                "confidence": 0.3,
                "reasoning": "Fallback due to OpenAI failure in outcomes triage"
            }
        
        # Extract and parse the response
        content = response.choices[0].message.content.strip()
        
        # Try to parse JSON response
        try:
            result = json.loads(content)
            
            # Validate the response structure
            required_keys = ["quadrant", "confidence", "reasoning"]
            if not all(key in result for key in required_keys):
                raise ValueError("Missing required keys in response")
            
            # Validate quadrant
            if result["quadrant"] not in QUADRANTS:
                raise ValueError(f"Invalid quadrant: {result['quadrant']}")
            
            # Validate confidence score
            confidence = float(result["confidence"])
            if not 0.0 <= confidence <= 1.0:
                raise ValueError(f"Confidence must be between 0.0 and 1.0, got: {confidence}")
            
            return result
            
        except json.JSONDecodeError:
            # Fallback: try to extract information from text response
            print("⚠️  Failed to parse OpenAI JSON response for outcomes triage, using fallback")
            return {
                "quadrant": "schedule",  # Default to schedule if parsing fails
                "confidence": 0.5,
                "reasoning": f"Failed to parse OpenAI response for outcomes triage: {content[:100]}..."
            }
            
    except Exception as e:
        # Return a safe fallback in case of unexpected errors
        print(f"❌ Unexpected error in triage_with_outcomes: {str(e)}")
        logger.error(f"Unexpected error in triage_with_outcomes: {str(e)}")
        return {
            "quadrant": "schedule",
            "confidence": 0.3,
            "reasoning": f"Fallback due to error in outcomes triage: {str(e)}"
        }


# Example usage and testing
if __name__ == "__main__":
    # Test the functions
    test_subject = "Urgent: Server down - immediate action required"
    test_body = "The production server is down and customers are affected. Please respond immediately."
    
    print("Testing email-only classification:")
    result1 = triage_email_only(test_subject, test_body)
    print(json.dumps(result1, indent=2))
    
    print("\nTesting classification with context:")
    test_profile = {
        "tags": ["IT", "urgent"],
        "notes": "System administrator, handles critical infrastructure",
        "linked_accounts": ["admin@company.com"]
    }
    result2 = triage_with_context(test_subject, test_body, test_profile)
    print(json.dumps(result2, indent=2)) 