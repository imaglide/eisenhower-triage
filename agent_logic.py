import time
from typing import Dict, Any, List
import random
import os
from dotenv import load_dotenv

# Import the real backend modules
from backend.triage_core import (
    triage_email_only as real_triage_email_only,
    triage_with_context as real_triage_with_context,
    triage_with_embedding as real_triage_with_embedding,
    triage_with_outcomes as real_triage_with_outcomes,
    safe_openai_chat_completion
)
from backend.supabase_client import (
    get_sender_profile,
    find_similar_emails,
    get_recent_triage_results,
    store_embedding,
    embedding_exists
)
from backend.config import Config

# Load environment variables
load_dotenv()

# Validate configuration
if not Config.validate():
    print("⚠️  Configuration validation failed. Some features may not work properly.")

# Standardized mapping from backend quadrant to UI priority
QUADRANT_TO_PRIORITY = {
    "do": "urgent_important",
    "schedule": "important_not_urgent",
    "delegate": "urgent_not_important",
    "delete": "not_urgent_not_important",
    # Allow passthrough for already-standardized values
    "urgent_important": "urgent_important",
    "important_not_urgent": "important_not_urgent",
    "urgent_not_important": "urgent_not_important",
    "not_urgent_not_important": "not_urgent_not_important",
}

PRIORITY_TO_HUMAN = {
    "urgent_important": "Urgent and Important",
    "important_not_urgent": "Important, Not Urgent",
    "urgent_not_important": "Urgent, Not Important",
    "not_urgent_not_important": "Not Urgent, Not Important",
}

def to_human_priority(priority_code: str) -> str:
    return PRIORITY_TO_HUMAN.get(priority_code, priority_code.replace('_', ' ').title())

def run_all_triage(subject: str, sender: str, body: str) -> Dict[str, Dict[str, Any]]:
    """
    Run all triage strategies on the given email content using real LLM calls and Supabase.
    
    Args:
        subject: Email subject
        sender: Email sender
        body: Email body
        
    Returns:
        Dictionary containing results from all triage strategies
    """
    results = {}
    
    # Generate a unique email ID for this analysis
    email_id = f"streamlit_{int(time.time())}_{hash(subject + sender)}"
    
    # Run each triage strategy
    strategies = [
        ('email_only', triage_email_only),
        ('contextual', triage_contextual),
        ('embedding', triage_embedding),
        ('outcomes', triage_outcomes)
    ]
    
    for strategy_name, strategy_func in strategies:
        try:
            result = strategy_func(subject, sender, body, email_id)
            results[strategy_name] = result
        except Exception as e:
            # Log error and provide fallback result
            print(f"Error in {strategy_name} strategy: {e}")
            results[strategy_name] = {
                'priority': 'not_urgent_not_important',
                'confidence': 0.0,
                'reasoning': f'Error occurred during analysis: {str(e)}',
                'metadata': {'error': True, 'error_message': str(e)}
            }
    
    return results


def triage_email_only(subject: str, sender: str, body: str, email_id: str = None) -> Dict[str, Any]:
    """
    Real email-only triage strategy using OpenAI GPT-4.
    
    Args:
        subject: Email subject
        sender: Email sender
        body: Email body
        email_id: Unique identifier for the email
        
    Returns:
        Triage result dictionary
    """
    try:
        # Call the real triage function from backend
        result = real_triage_email_only(subject, body)
        
        # Convert the backend result format to our Streamlit format
        priority_raw = result.get('quadrant', 'not_urgent_not_important')
        priority = QUADRANT_TO_PRIORITY.get(priority_raw, 'not_urgent_not_important')
        return {
            'priority': priority,
            'human_priority': to_human_priority(priority),
            'confidence': result.get('confidence', 0.0),
            'reasoning': result.get('reasoning', 'No reasoning provided'),
            'metadata': {
                'strategy': 'real_llm_email_only',
                'model_used': Config.OPENAI_MODEL,
                'email_id': email_id,
                'tokens_used': result.get('tokens_used', 0)
            }
        }
        
    except Exception as e:
        print(f"Error in real email-only triage: {e}")
        # Fallback to basic keyword analysis
        return fallback_email_only_triage(subject, body)


def triage_contextual(subject: str, sender: str, body: str, email_id: str = None) -> Dict[str, Any]:
    """
    Real contextual triage strategy using sender profiles from Supabase.
    
    Args:
        subject: Email subject
        sender: Email sender
        body: Email body
        email_id: Unique identifier for the email
        
    Returns:
        Triage result dictionary
    """
    try:
        # Get sender profile from Supabase
        sender_profile = get_sender_profile(sender)
        
        # Call the real contextual triage function
        result = real_triage_with_context(subject, body, sender_profile)
        
        # Convert the backend result format to our Streamlit format
        priority_raw = result.get('quadrant', 'not_urgent_not_important')
        priority = QUADRANT_TO_PRIORITY.get(priority_raw, 'not_urgent_not_important')
        return {
            'priority': priority,
            'human_priority': to_human_priority(priority),
            'confidence': result.get('confidence', 0.0),
            'reasoning': result.get('reasoning', 'No reasoning provided'),
            'metadata': {
                'strategy': 'real_llm_contextual',
                'model_used': Config.OPENAI_MODEL,
                'email_id': email_id,
                'sender_profile_found': bool(sender_profile),
                'sender_profile': sender_profile,
                'tokens_used': result.get('tokens_used', 0)
            }
        }
        
    except Exception as e:
        print(f"Error in real contextual triage: {e}")
        # Fallback to basic contextual analysis
        return fallback_contextual_triage(subject, sender, body)


def triage_embedding(subject: str, sender: str, body: str, email_id: str = None) -> Dict[str, Any]:
    """
    Real embedding-based triage strategy using OpenAI embeddings and Supabase.
    
    Args:
        subject: Email subject
        sender: Email sender
        body: Email body
        email_id: Unique identifier for the email
        
    Returns:
        Triage result dictionary
    """
    try:
        # Check if embedding already exists
        if email_id and embedding_exists(email_id):
            print(f"Using existing embedding for {email_id}")
        
        # Call the real embedding triage function
        result = real_triage_with_embedding(subject, body, email_id or "streamlit_email")
        
        # Convert the backend result format to our Streamlit format
        priority_raw = result.get('quadrant', 'not_urgent_not_important')
        priority = QUADRANT_TO_PRIORITY.get(priority_raw, 'not_urgent_not_important')
        return {
            'priority': priority,
            'human_priority': to_human_priority(priority),
            'confidence': result.get('confidence', 0.0),
            'reasoning': result.get('reasoning', 'No reasoning provided'),
            'metadata': {
                'strategy': 'real_llm_embedding',
                'model_used': Config.OPENAI_MODEL,
                'embedding_model': Config.EMBEDDING_MODEL,
                'email_id': email_id,
                'similar_emails_found': result.get('similar_emails_count', 0),
                'tokens_used': result.get('tokens_used', 0)
            }
        }
        
    except Exception as e:
        print(f"Error in real embedding triage: {e}")
        # Fallback to simulated embedding analysis
        return fallback_embedding_triage(subject, body)


def triage_outcomes(subject: str, sender: str, body: str, email_id: str = None) -> Dict[str, Any]:
    """
    Real outcomes-focused triage strategy using historical data from Supabase.
    
    Args:
        subject: Email subject
        sender: Email sender
        body: Email body
        email_id: Unique identifier for the email
        
    Returns:
        Triage result dictionary
    """
    try:
        # Get recent triage results for context
        recent_results = get_recent_triage_results(limit=10)
        
        # Get similar emails for context
        similar_contexts = "No similar contexts found"
        try:
            # This would require getting embeddings first, simplified for now
            similar_contexts = f"Found {len(recent_results)} recent triage results for context"
        except:
            pass
        
        # Call the real outcomes triage function
        result = real_triage_with_outcomes(subject, body, similar_contexts, recent_results)
        
        # Convert the backend result format to our Streamlit format
        priority_raw = result.get('quadrant', 'not_urgent_not_important')
        priority = QUADRANT_TO_PRIORITY.get(priority_raw, 'not_urgent_not_important')
        return {
            'priority': priority,
            'human_priority': to_human_priority(priority),
            'confidence': result.get('confidence', 0.0),
            'reasoning': result.get('reasoning', 'No reasoning provided'),
            'metadata': {
                'strategy': 'real_llm_outcomes',
                'model_used': Config.OPENAI_MODEL,
                'email_id': email_id,
                'recent_results_used': len(recent_results),
                'tokens_used': result.get('tokens_used', 0)
            }
        }
        
    except Exception as e:
        print(f"Error in real outcomes triage: {e}")
        # Fallback to basic outcomes analysis
        return fallback_outcomes_triage(subject, body)


# Fallback functions for when real LLM calls fail
def fallback_email_only_triage(subject: str, body: str) -> Dict[str, Any]:
    """Fallback keyword-based analysis when LLM fails"""
    urgent_keywords = ['urgent', 'asap', 'immediate', 'emergency', 'critical', 'deadline']
    important_keywords = ['important', 'priority', 'key', 'essential', 'vital', 'crucial']
    
    subject_lower = subject.lower()
    body_lower = body.lower()
    
    is_urgent = any(keyword in subject_lower or keyword in body_lower for keyword in urgent_keywords)
    is_important = any(keyword in subject_lower or keyword in body_lower for keyword in important_keywords)
    
    if is_urgent and is_important:
        priority = 'urgent_important'
        confidence = 0.75
    elif is_important and not is_urgent:
        priority = 'important_not_urgent'
        confidence = 0.65
    elif is_urgent and not is_important:
        priority = 'urgent_not_important'
        confidence = 0.60
    else:
        priority = 'not_urgent_not_important'
        confidence = 0.50
    
    priority = QUADRANT_TO_PRIORITY.get(priority, 'not_urgent_not_important')
    return {
        'priority': priority,
        'human_priority': to_human_priority(priority),
        'confidence': confidence,
        'reasoning': f"Fallback keyword analysis. Urgent: {is_urgent}, Important: {is_important}",
        'metadata': {
            'strategy': 'fallback_keyword',
            'urgent_keywords_found': [kw for kw in urgent_keywords if kw in subject_lower or kw in body_lower],
            'important_keywords_found': [kw for kw in important_keywords if kw in subject_lower or kw in body_lower]
        }
    }


def fallback_contextual_triage(subject: str, sender: str, body: str) -> Dict[str, Any]:
    """Fallback contextual analysis when LLM fails"""
    sender_domain = sender.split('@')[-1] if '@' in sender else ''
    important_domains = ['company.com', 'boss.com', 'executive.com', 'management.com']
    is_important_sender = any(domain in sender_domain.lower() for domain in important_domains)
    
    time_patterns = ['today', 'tomorrow', 'this week', 'by end of day', 'deadline']
    has_time_constraint = any(pattern in body.lower() for pattern in time_patterns)
    
    if is_important_sender and has_time_constraint:
        priority = 'urgent_important'
        confidence = 0.80
    elif is_important_sender:
        priority = 'important_not_urgent'
        confidence = 0.70
    elif has_time_constraint:
        priority = 'urgent_not_important'
        confidence = 0.65
    else:
        priority = 'not_urgent_not_important'
        confidence = 0.55
    
    priority = QUADRANT_TO_PRIORITY.get(priority, 'not_urgent_not_important')
    return {
        'priority': priority,
        'human_priority': to_human_priority(priority),
        'confidence': confidence,
        'reasoning': f"Fallback contextual analysis. Important sender: {is_important_sender}, Time constraint: {has_time_constraint}",
        'metadata': {
            'strategy': 'fallback_contextual',
            'sender_domain': sender_domain,
            'is_important_sender': is_important_sender,
            'has_time_constraint': has_time_constraint
        }
    }


def fallback_embedding_triage(subject: str, body: str) -> Dict[str, Any]:
    """Fallback embedding analysis when LLM fails"""
    # Simulate embedding-based analysis
    urgent_similarity = random.uniform(0.1, 0.9)
    important_similarity = random.uniform(0.1, 0.9)
    
    is_urgent = urgent_similarity > 0.6
    is_important = important_similarity > 0.5
    
    if is_urgent and is_important:
        priority = 'urgent_important'
        confidence = 0.78
    elif is_important and not is_urgent:
        priority = 'important_not_urgent'
        confidence = 0.72
    elif is_urgent and not is_important:
        priority = 'urgent_not_important'
        confidence = 0.68
    else:
        priority = 'not_urgent_not_important'
        confidence = 0.62
    
    priority = QUADRANT_TO_PRIORITY.get(priority, 'not_urgent_not_important')
    return {
        'priority': priority,
        'human_priority': to_human_priority(priority),
        'confidence': confidence,
        'reasoning': f"Fallback embedding analysis. Urgent similarity: {urgent_similarity:.2f}, Important similarity: {important_similarity:.2f}",
        'metadata': {
            'strategy': 'fallback_embedding',
            'urgent_similarity': urgent_similarity,
            'important_similarity': important_similarity
        }
    }


def fallback_outcomes_triage(subject: str, body: str) -> Dict[str, Any]:
    """Fallback outcomes analysis when LLM fails"""
    outcome_keywords = {
        'high_impact': ['revenue', 'profit', 'loss', 'customer', 'contract', 'deal'],
        'medium_impact': ['project', 'meeting', 'report', 'review', 'update'],
        'low_impact': ['newsletter', 'announcement', 'update', 'information']
    }
    
    full_text = f"{subject} {body}".lower()
    
    impact_scores = {}
    for impact_level, keywords in outcome_keywords.items():
        score = sum(1 for keyword in keywords if keyword in full_text)
        impact_scores[impact_level] = score
    
    max_impact = max(impact_scores.items(), key=lambda x: x[1])
    impact_level = max_impact[0]
    
    if impact_level == 'high_impact':
        priority = 'urgent_important'
        confidence = 0.82
    elif impact_level == 'medium_impact':
        priority = 'important_not_urgent'
        confidence = 0.68
    else:
        priority = 'not_urgent_not_important'
        confidence = 0.58
    
    priority = QUADRANT_TO_PRIORITY.get(priority, 'not_urgent_not_important')
    return {
        'priority': priority,
        'human_priority': to_human_priority(priority),
        'confidence': confidence,
        'reasoning': f"Fallback outcomes analysis. Impact level: {impact_level}",
        'metadata': {
            'strategy': 'fallback_outcomes',
            'impact_level': impact_level,
            'impact_scores': impact_scores
        }
    }


def get_triage_summary(results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate a summary of all triage results.
    
    Args:
        results: Results from all triage strategies
        
    Returns:
        Summary dictionary
    """
    if not results:
        return {}
    
    # Count priorities
    priority_counts = {}
    total_confidence = 0
    valid_results = 0
    
    for strategy, result in results.items():
        if result and 'priority' in result:
            priority = result['priority']
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
            
            if 'confidence' in result:
                total_confidence += result['confidence']
                valid_results += 1
    
    # Determine consensus priority
    consensus_priority = max(priority_counts.items(), key=lambda x: x[1])[0] if priority_counts else None
    
    # Calculate average confidence
    avg_confidence = total_confidence / valid_results if valid_results > 0 else 0
    
    return {
        'consensus_priority': consensus_priority,
        'priority_distribution': priority_counts,
        'average_confidence': avg_confidence,
        'total_strategies': len(results),
        'successful_strategies': valid_results
    } 