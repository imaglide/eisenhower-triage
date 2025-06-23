#!/usr/bin/env python3
"""
Batch email processing script for EisenhowerTriageAgent.

This script processes .eml files from the ../eml_files/ directory,
extracts email content, runs dual triage classification, generates
embeddings, and stores results in Supabase.
"""

import os
import sys
import json
import uuid
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
from email import message_from_file
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from openai import OpenAI
import openai

# Try to import tiktoken for token counting
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    print("⚠️  tiktoken not available, token counting disabled")

# Processing limit
MAX_EMAILS_TO_PROCESS = 5

# Add backend to path
project_root = Path(__file__).parent.parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

from triage_core import triage_email_only, triage_with_context, triage_with_embeddings, triage_with_outcomes
from supabase_client import (
    embedding_exists, 
    store_embedding, 
    upsert_triage_result,
    get_sender_profile,
    get_email_summary,
    get_triage_result,
    find_similar_emails
)
from config import Config

# OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('batch_processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


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


def extract_email_content(eml_file_path: Path) -> Optional[Dict[str, str]]:
    """
    Parse .eml file and extract email content.
    
    Args:
        eml_file_path: Path to the .eml file
        
    Returns:
        Dictionary with email content or None if parsing fails
    """
    try:
        with open(eml_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            msg = message_from_file(f)
        
        # Extract basic headers
        subject = msg.get('subject', '')
        from_address = msg.get('from', '')
        message_id = msg.get('message-id', '')
        
        # Generate fallback message_id if not present
        if not message_id:
            message_id = f"generated_{uuid.uuid4().hex}"
        
        # Extract body content
        body = extract_body_content(msg)
        
        if not body:
            logger.warning(f"No body content found in {eml_file_path}")
            return None
        
        return {
            'subject': subject,
            'body': body,
            'from': from_address,
            'message_id': message_id
        }
        
    except Exception as e:
        logger.error(f"Error parsing {eml_file_path}: {str(e)}")
        return None


def extract_body_content(msg) -> str:
    """
    Extract text content from email message, preferring text/plain.
    
    Args:
        msg: Email message object
        
    Returns:
        Extracted text content
    """
    body = ""
    
    if msg.is_multipart():
        # Handle multipart messages
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get('Content-Disposition', ''))
            
            # Skip attachments
            if 'attachment' in content_disposition:
                continue
            
            # Prefer text/plain, fallback to text/html
            if content_type == 'text/plain':
                try:
                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    break
                except Exception as e:
                    logger.warning(f"Error decoding text/plain part: {str(e)}")
                    continue
            elif content_type == 'text/html' and not body:
                try:
                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                except Exception as e:
                    logger.warning(f"Error decoding text/html part: {str(e)}")
                    continue
    else:
        # Handle simple text messages
        content_type = msg.get_content_type()
        if content_type in ['text/plain', 'text/html']:
            try:
                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            except Exception as e:
                logger.warning(f"Error decoding simple message: {str(e)}")
    
    return body.strip()


def generate_embedding(text: str) -> Optional[list]:
    """
    Generate text embedding using OpenAI.
    
    Args:
        text: Text to embed (full text, not truncated for triage)
        
    Returns:
        List of float values representing the embedding vector
    """
    try:
        # Truncate text if too long (OpenAI has limits)
        max_tokens = 8000  # Conservative limit for embeddings
        original_length = len(text)
        original_tokens = count_tokens(text)
        
        if original_tokens > max_tokens:
            # Use tiktoken for precise truncation if available
            if TIKTOKEN_AVAILABLE:
                try:
                    encoding = tiktoken.get_encoding("cl100k_base")
                    tokens = encoding.encode(text)
                    truncated_tokens = tokens[:max_tokens]
                    text = encoding.decode(truncated_tokens)
                    print(f"📏 Text truncated from {original_tokens} to {len(truncated_tokens)} tokens for embedding")
                except Exception as e:
                    logger.warning(f"Error truncating with tiktoken: {str(e)}")
                    # Fallback to character-based truncation
                    text = text[:max_tokens * 4]
                    print(f"📏 Text truncated from {original_length} to {len(text)} characters for embedding (fallback)")
            else:
                # Fallback when tiktoken is not available
                text = text[:max_tokens * 4]
                print(f"📏 Text truncated from {original_length} to {len(text)} characters for embedding")
        
        print(f"🔍 Generating embedding for text ({len(text)} characters)...")
        response = client.embeddings.create(
            input=text,
            model="text-embedding-ada-002"
        )
        
        embedding = response.data[0].embedding
        print(f"✅ Embedding generated successfully: {len(embedding)} dimensions")
        return embedding
        
    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}")
        return None


def process_single_email(email_data: Dict[str, str]) -> bool:
    """
    Process a single email through the complete triage pipeline.
    
    Args:
        email_data: Dictionary with email content
        
    Returns:
        True if processing was successful, False otherwise
    """
    email_id = email_data['message_id']  # Keep message_id in email_data for compatibility
    subject = email_data['subject']
    body = email_data['body']
    from_address = email_data['from']
    
    logger.info(f"Processing email: {email_id}")
    logger.info(f"Subject: {subject}")
    logger.info(f"From: {from_address}")
    
    # Log large emails for monitoring
    body_token_count = count_tokens(body)
    if body_token_count > 12000:
        print(f"⚠️ Large email: {email_id} — {body_token_count} tokens")
        logger.warning(f"Large email detected: {email_id} with {body_token_count} tokens")
    
    try:
        # Check if already processed
        print(f"🔍 Checking if embedding exists for email_id: {email_id}")
        embedding_exists_flag = embedding_exists(email_id)
        
        if embedding_exists_flag:
            print(f"📝 Existing embedding found for email_id: {email_id} - will use for one approach")
        else:
            print(f"📝 No existing embedding found - proceeding with processing")
        
        # Get sender profile
        sender_profile = get_sender_profile(from_address)
        if sender_profile:
            logger.info(f"Found sender profile for {from_address}")
        else:
            logger.info(f"No sender profile found for {from_address}")
            sender_profile = {}
        
        # Always run email-only triage to show results
        logger.info("Running email-only triage...")
        email_only_result = triage_email_only(subject, body)
        logger.info(f"Email-only result: {email_only_result['quadrant']} (confidence: {email_only_result['confidence']:.2f})")
        
        # Display email-only triage results in console
        print(f"📨 Email-only triage: {email_only_result['quadrant']} "
              f"(confidence: {email_only_result['confidence']:.2f})")
        print(f"   🧠 Reasoning: {email_only_result['reasoning'][:200]}...")
        
        # Always run contextual triage to show results
        logger.info("Running contextual triage...")
        contextual_result = triage_with_context(subject, body, sender_profile)
        logger.info(f"Contextual result: {contextual_result['quadrant']} (confidence: {contextual_result['confidence']:.2f})")
        
        # Display contextual triage results in console
        print(f"👤 Contextual triage: {contextual_result['quadrant']} "
              f"(confidence: {contextual_result['confidence']:.2f})")
        print(f"   🧠 Reasoning: {contextual_result['reasoning'][:200]}...")
        
        # Generate or retrieve embedding for similarity search
        embedding = None
        if not embedding_exists_flag:
            # Generate embedding
            print(f"🧠 Generating embedding for email_id: {email_id}")
            combined_text = f"Subject: {subject}\n\nBody: {body}"
            embedding = generate_embedding(combined_text)
            
            if not embedding:
                logger.error(f"Failed to generate embedding for {email_id}")
                return False
            
            # Store embedding
            print(f"💾 Storing embedding in email_embeddings table...")
            if not store_embedding(email_id, embedding):
                logger.error(f"Failed to store embedding for {email_id}")
                return False
        else:
            print(f"💾 Using existing embedding for email_id: {email_id}")
            # For now, we'll use the triage_with_embeddings function which handles embedding retrieval
            # This is a temporary workaround - in a full implementation, we'd retrieve the existing embedding
        
        # Use triage_with_embeddings to get embedding-based classification and similar emails
        result_embedding = triage_with_embeddings(subject, body, email_id)
        logger.info(f"Embedding-based result: {result_embedding['quadrant']} (confidence: {result_embedding['confidence']:.2f})")
        
        # Display embedding-based triage results in console
        print(f"🔍 Embedding-based triage: {result_embedding['quadrant']} "
              f"(confidence: {result_embedding['confidence']:.2f})")
        print(f"   🧠 Reasoning: {result_embedding['reasoning'][:200]}...")
        
        # For outcomes triage, we need to get similar emails and their triage results
        # Since triage_with_embeddings already does this internally, we'll need to do it again
        # or modify the function to return both the result and the similar emails
        # For now, let's use a simplified approach and get similar emails directly
        
        # Generate embedding for similarity search if not already done
        if embedding is None:
            combined_text = f"Subject: {subject}\n\nBody: {body}"
            embedding = generate_embedding(combined_text)
            if not embedding:
                logger.warning("Could not generate embedding for outcomes triage, skipping")
                result_outcomes = {
                    "quadrant": "schedule",
                    "confidence": 0.3,
                    "reasoning": "Skipped due to embedding generation failure"
                }
            else:
                # Find similar emails using vector similarity search
                similar_emails = find_similar_emails(embedding, top_k=5)
                
                # Build similar_contexts using real summaries
                summaries = []
                for e in similar_emails:
                    summary = get_email_summary(e["email_id"])
                    summaries.append(f"- Similar email (score: {e['score']:.2f}):\n{summary.strip()}")
                similar_contexts = "\n\n".join(summaries)
                
                # Collect past triage results from similar emails for outcomes triage
                past_triage_results = []
                for match in similar_emails:
                    result = get_triage_result(match["email_id"])
                    if result and result.get("triage_email_only"):
                        past_triage_results.append({
                            "email_id": match["email_id"],
                            "triage": result["triage_email_only"]
                        })
                
                # Run outcomes triage with past triage results
                result_outcomes = triage_with_outcomes(subject, body, similar_contexts, past_triage_results)
        else:
            # Find similar emails using vector similarity search
            similar_emails = find_similar_emails(embedding, top_k=5)
            
            # Build similar_contexts using real summaries
            summaries = []
            for e in similar_emails:
                summary = get_email_summary(e["email_id"])
                summaries.append(f"- Similar email (score: {e['score']:.2f}):\n{summary.strip()}")
            similar_contexts = "\n\n".join(summaries)
            
            # Collect past triage results from similar emails for outcomes triage
            past_triage_results = []
            for match in similar_emails:
                result = get_triage_result(match["email_id"])
                if result and result.get("triage_email_only"):
                    past_triage_results.append({
                        "email_id": match["email_id"],
                        "triage": result["triage_email_only"]
                    })
            
            # Run outcomes triage with past triage results
            result_outcomes = triage_with_outcomes(subject, body, similar_contexts, past_triage_results)
        
        logger.info(f"Outcomes-based result: {result_outcomes['quadrant']} (confidence: {result_outcomes['confidence']:.2f})")
        
        # Display outcomes triage results in console
        print(f"📊 Outcome-aware triage: {result_outcomes['quadrant']} "
              f"(confidence: {result_outcomes['confidence']:.2f})")
        print(f"   🧠 Reasoning: {result_outcomes['reasoning'][:200]}...")
        
        # Store triage results (always update with latest results)
        logger.info("Storing triage results...")
        if not upsert_triage_result(email_id, email_only_result, contextual_result, result_embedding, result_outcomes):
            logger.error(f"Failed to store triage results for {email_id}")
            return False
        
        logger.info(f"✅ Successfully processed email: {email_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error processing email {email_id}: {str(e)}")
        return False


def main():
    """Main function to process batch of .eml files."""
    print("🚀 Starting batch email processing...")
    print("=" * 50)
    
    # Validate configuration
    if not Config.validate():
        logger.error("Configuration validation failed")
        print("❌ Configuration validation failed. Please check your .env file.")
        return
    
    # Check for eml_files directory
    eml_dir = Path("./data/sample_emails/eml_files")
    if not eml_dir.exists():
        logger.error(f"Directory {eml_dir} does not exist")
        print(f"❌ Directory {eml_dir} does not exist")
        print("Please create the directory and add some .eml files for testing.")
        return
    
    # Find .eml files and limit processing
    print(f"🔍 Processing up to {MAX_EMAILS_TO_PROCESS} .eml files for triage...")
    eml_files = sorted(eml_dir.glob("*.eml"))[:MAX_EMAILS_TO_PROCESS]
    
    if not eml_files:
        logger.warning(f"No .eml files found in {eml_dir}")
        print(f"⚠️  No .eml files found in {eml_dir}")
        print("Please add some .eml files for testing.")
        return
    
    logger.info(f"Found {len(eml_files)} .eml files to process")
    print(f"📧 Found {len(eml_files)} .eml files to process")
    
    # Process each file
    successful = 0
    failed = 0
    
    for i, eml_file in enumerate(eml_files, 1):
        print(f"\n{'='*20} Processing File {i}/{len(eml_files)} {'='*20}")
        print(f"File: {eml_file.name}")
        
        # Extract email content
        email_data = extract_email_content(eml_file)
        if not email_data:
            logger.error(f"Failed to extract content from {eml_file}")
            print(f"❌ Failed to extract content from {eml_file.name}")
            failed += 1
            continue
        
        # Process the email
        if process_single_email(email_data):
            successful += 1
            print(f"✅ Successfully processed {eml_file.name}")
        else:
            failed += 1
            print(f"❌ Failed to process {eml_file.name}")
    
    # Summary
    print(f"\n{'='*50}")
    print("📊 Processing Summary:")
    print(f"  Total files: {len(eml_files)}")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print(f"  Success rate: {successful/len(eml_files)*100:.1f}%")
    
    if successful > 0:
        print("\n🎉 Batch processing completed!")
        print("Check the database for stored results and embeddings.")
    else:
        print("\n⚠️  No files were processed successfully.")
        print("Check the logs for detailed error information.")


if __name__ == "__main__":
    main() 