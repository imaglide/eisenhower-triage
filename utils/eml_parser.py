import email
from email import policy
from email.parser import BytesParser
from typing import Tuple, Optional
import re


def parse_eml(file) -> Tuple[str, str, str]:
    """
    Parse an .eml file and extract subject, sender, and body.
    
    Args:
        file: File-like object (e.g., from Streamlit file uploader)
        
    Returns:
        Tuple[str, str, str]: (subject, sender, body)
        
    Raises:
        ValueError: If the file cannot be parsed as a valid email
    """
    try:
        # Parse the email using Python's email parser
        parser = BytesParser(policy=policy.default)
        msg = parser.parse(file)
        
        # Extract subject
        subject = msg.get('subject', '')
        if subject is None:
            subject = '(No Subject)'
        
        # Extract sender
        sender = msg.get('from', '')
        if sender is None:
            sender = '(Unknown Sender)'
        
        # Clean up sender (remove display names, keep email)
        sender = clean_sender(sender)
        
        # Extract body
        body = extract_body(msg)
        
        return subject, sender, body
        
    except Exception as e:
        raise ValueError(f"Failed to parse email file: {str(e)}")


def clean_sender(sender: str) -> str:
    """
    Clean up the sender field to extract just the email address.
    
    Args:
        sender: Raw sender string from email
        
    Returns:
        Cleaned email address
    """
    if not sender:
        return '(Unknown Sender)'
    
    # Common patterns for email addresses
    email_patterns = [
        r'<([^>]+@[^>]+)>',  # <email@domain.com>
        r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',  # email@domain.com
    ]
    
    for pattern in email_patterns:
        match = re.search(pattern, sender)
        if match:
            return match.group(1) if len(match.groups()) > 0 else match.group(0)
    
    # If no email pattern found, return the original string
    return sender.strip()


def extract_body(msg) -> str:
    """
    Extract the text body from an email message, preferring the part with more content.
    
    Args:
        msg: Parsed email message
        
    Returns:
        Email body as string
    """
    text_body = ""
    html_body = ""
    
    if msg.is_multipart():
        # In multipart messages, walk through parts to find text and html
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get('Content-Disposition', ''))
            
            # Skip attachments
            if 'attachment' in content_disposition:
                continue

            if content_type == 'text/plain' and not text_body:
                try:
                    payload = part.get_payload(decode=True)
                    text_body = payload.decode('utf-8', errors='ignore')
                except Exception:
                    continue # Ignore decoding errors
            
            elif content_type == 'text/html' and not html_body:
                try:
                    payload = part.get_payload(decode=True)
                    html_content = payload.decode('utf-8', errors='ignore')
                    html_body = html_to_text(html_content)
                except Exception:
                    continue # Ignore decoding errors

    else:
        # Handle non-multipart messages
        content_type = msg.get_content_type()
        try:
            payload = msg.get_payload(decode=True)
            if content_type == 'text/plain':
                text_body = payload.decode('utf-8', errors='ignore')
            elif content_type == 'text/html':
                html_body = html_to_text(payload.decode('utf-8', errors='ignore'))
            else:
                # Fallback for other content types
                text_body = payload.decode('utf-8', errors='ignore')
        except Exception:
            text_body = str(msg.get_payload())
            
    # Choose the body with more content, as plain text can sometimes be empty
    body = html_body if len(html_body) > len(text_body) else text_body

    # Clean up the final chosen body
    cleaned_body = clean_body(body)
    
    return cleaned_body if cleaned_body else '(No Body)'


def html_to_text(html_content: str) -> str:
    """
    Simple HTML to text conversion.
    
    Args:
        html_content: HTML string
        
    Returns:
        Plain text version
    """
    # Remove HTML tags
    import re
    text = re.sub(r'<[^>]+>', '', html_content)
    
    # Decode HTML entities
    import html
    text = html.unescape(text)
    
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text


def clean_body(body: str) -> str:
    """
    Clean up the email body text.
    
    Args:
        body: Raw email body
        
    Returns:
        Cleaned body text
    """
    if not body:
        return ""
    
    # Remove excessive whitespace
    import re
    body = re.sub(r'\n\s*\n', '\n\n', body)  # Remove excessive line breaks
    body = re.sub(r' +', ' ', body)  # Remove excessive spaces
    
    # Remove common email signatures and quoted text
    lines = body.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Skip common signature indicators
        if any(indicator in line.lower() for indicator in [
            '-- ', 'sent from my', 'get outlook', 'sent from iphone',
            'sent from mobile', 'best regards', 'kind regards', 'sincerely'
        ]):
            break
        
        # Skip quoted text (lines starting with >)
        if line.strip().startswith('>'):
            continue
            
        cleaned_lines.append(line)
    
    body = '\n'.join(cleaned_lines)
    
    return body.strip()


def validate_eml_file(file) -> bool:
    """
    Validate that the uploaded file is a valid .eml file.
    
    Args:
        file: File-like object
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Check file extension
        if not hasattr(file, 'name') or not file.name.lower().endswith('.eml'):
            return False
        
        # Try to parse a small portion to validate
        parser = BytesParser(policy=policy.default)
        msg = parser.parse(file)
        
        # Check for basic email headers
        if not msg.get('from') and not msg.get('to'):
            return False
            
        return True
        
    except Exception:
        return False 