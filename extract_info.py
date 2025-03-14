import spacy
import re
from datetime import datetime
from dateutil import parser
from typing import Dict, Optional, Tuple
from models import ProcessedTweet, AirdropOpportunity

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

def extract_token_symbol(text: str) -> Optional[str]:
    """Extract potential token symbols from text."""
    # Look for $SYMBOL pattern
    dollar_match = re.search(r'\$([A-Z]{2,10})', text)
    if dollar_match:
        return dollar_match.group(1)
    
    # Look for "TOKEN" or "Token" followed by "token"/"coin"
    token_match = re.search(r'([A-Z][A-Z0-9]{2,9})\s+(?:token|coin)', text, re.IGNORECASE)
    if token_match:
        return token_match.group(1)
    
    return None

def extract_deadline(text: str) -> Optional[datetime]:
    """Extract deadline date from text."""
    # Common deadline patterns
    patterns = [
        r'deadline:?\s*(.+?)(?:\.|$)',
        r'ends?(?:\son)?:?\s*(.+?)(?:\.|$)',
        r'until:?\s*(.+?)(?:\.|$)',
        r'closes?(?:\son)?:?\s*(.+?)(?:\.|$)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return parser.parse(match.group(1), fuzzy=True)
            except (ValueError, parser.ParserError):
                continue
    
    return None

def extract_participation_steps(text: str) -> Optional[str]:
    """Extract participation instructions from text."""
    # Common patterns for participation instructions
    patterns = [
        r'(?:how to participate|steps?|to participate):\s*(.+?)(?:\n|$)',
        r'(?:1\.|\*)(.+?)(?:\n|$)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return None

def extract_project_info(doc) -> Tuple[Optional[str], Optional[str]]:
    """Extract project name and description using spaCy NER."""
    project_name = None
    description = None
    
    # Look for organization entities
    orgs = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
    if orgs:
        project_name = orgs[0]  # Take the first organization mentioned
    
    # Get the sentence containing the project name as description
    if project_name:
        for sent in doc.sents:
            if project_name in sent.text:
                description = sent.text.strip()
                break
    
    return project_name, description

def calculate_confidence_score(tweet: ProcessedTweet, extracted_info: Dict) -> float:
    """Calculate confidence score for the airdrop opportunity."""
    score = 0.0
    
    # Check if essential information is present
    if extracted_info.get('project_name'):
        score += 20
    if extracted_info.get('token_symbol'):
        score += 20
    if extracted_info.get('deadline'):
        score += 15
    if extracted_info.get('participation_steps'):
        score += 15
    
    # Check for spam indicators
    spam_keywords = ['fake', 'scam', 'hurry', '100x', 'guaranteed']
    spam_count = sum(1 for keyword in spam_keywords if keyword in tweet.processed_text.lower())
    score -= spam_count * 5
    
    # Bonus points for verified accounts (would need to be implemented with actual Twitter API)
    # if tweet.author_verified:
    #     score += 10
    
    # Normalize score to 0-100 range
    score = max(0, min(100, score))
    
    return score

def extract_airdrop_info(tweet: ProcessedTweet) -> Optional[AirdropOpportunity]:
    """Extract all relevant information from a tweet and create an AirdropOpportunity."""
    # Process with spaCy
    doc = nlp(tweet.processed_text)
    
    # Extract information
    project_name, description = extract_project_info(doc)
    token_symbol = extract_token_symbol(tweet.processed_text)
    deadline = extract_deadline(tweet.processed_text)
    participation_steps = extract_participation_steps(tweet.processed_text)
    
    # If we don't have enough information, return None
    if not (project_name or token_symbol):
        return None
    
    # Create extracted info dictionary for confidence calculation
    extracted_info = {
        'project_name': project_name,
        'token_symbol': token_symbol,
        'deadline': deadline,
        'participation_steps': participation_steps
    }
    
    # Calculate confidence score
    confidence_score = calculate_confidence_score(tweet, extracted_info)
    
    # Create AirdropOpportunity object
    return AirdropOpportunity(
        tweet_id=tweet.tweet_id,
        project_name=project_name,
        token_symbol=token_symbol,
        description=description,
        deadline=deadline,
        participation_steps=participation_steps,
        tweet_url=f"https://twitter.com/i/web/status/{tweet.tweet_id}",
        confidence_score=confidence_score
    ) 