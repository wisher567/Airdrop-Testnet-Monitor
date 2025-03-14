import tweepy
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from models import TwitterAccount, ProcessedTweet

class TwitterClient:
    def __init__(self, api_key: str, api_secret: str, access_token: str, access_token_secret: str):
        auth = tweepy.OAuthHandler(api_key, api_secret)
        auth.set_access_token(access_token, access_token_secret)
        self.api = tweepy.API(auth, wait_on_rate_limit=True)
        
    def get_user_tweets(self, username: str, since_id: Optional[str] = None, 
                       max_results: int = 100) -> List[tweepy.Tweet]:
        """Fetch recent tweets from a specific user."""
        try:
            tweets = self.api.user_timeline(screen_name=username,
                                          count=max_results,
                                          since_id=since_id,
                                          tweet_mode="extended")
            return tweets
        except tweepy.TweepError as e:
            print(f"Error fetching tweets for {username}: {str(e)}")
            return []

    def search_tweets(self, query: str, since_id: Optional[str] = None,
                     max_results: int = 100) -> List[tweepy.Tweet]:
        """Search for tweets matching the query."""
        try:
            tweets = self.api.search_tweets(q=query,
                                          count=max_results,
                                          since_id=since_id,
                                          tweet_mode="extended")
            return tweets
        except tweepy.TweepError as e:
            print(f"Error searching tweets for {query}: {str(e)}")
            return []

def preprocess_tweet_text(text: str) -> str:
    """Clean and preprocess tweet text."""
    # Remove URLs
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    
    # Remove mentions while keeping the username text
    text = re.sub(r'@(\w+)', r'\1', text)
    
    # Remove hashtag symbols while keeping the text
    text = re.sub(r'#(\w+)', r'\1', text)
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Convert to lowercase
    text = text.lower()
    
    return text.strip()

def filter_tweets(tweets: List[tweepy.Tweet], db: Session,
                 max_age_days: int = 7) -> List[ProcessedTweet]:
    """Filter tweets based on various criteria."""
    filtered_tweets = []
    cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
    
    for tweet in tweets:
        # Skip if tweet is too old
        if tweet.created_at < cutoff_date:
            continue
            
        # Check if tweet is already processed
        existing = db.query(ProcessedTweet).filter_by(tweet_id=str(tweet.id)).first()
        if existing:
            continue
            
        # Create ProcessedTweet object
        processed_tweet = ProcessedTweet(
            tweet_id=str(tweet.id),
            author_id=str(tweet.user.id),
            text=tweet.full_text,
            processed_text=preprocess_tweet_text(tweet.full_text),
            created_at=tweet.created_at,
            is_retweet=hasattr(tweet, 'retweeted_status'),
            is_reply=tweet.in_reply_to_status_id is not None
        )
        
        filtered_tweets.append(processed_tweet)
    
    return filtered_tweets

# Keywords and hashtags for searching
AIRDROP_KEYWORDS = [
    '#airdrop', '$airdrop', 'free tokens', 'token giveaway',
    'airdrop announcement', 'upcoming airdrop'
]

TESTNET_KEYWORDS = [
    '#testnet', 'testnet launch', 'testnet participation',
    'devnet', 'test network'
]

def get_search_queries() -> List[str]:
    """Combine keywords into search queries."""
    return AIRDROP_KEYWORDS + TESTNET_KEYWORDS

def fetch_new_tweets(client: TwitterClient, db: Session) -> List[ProcessedTweet]:
    """Fetch new tweets from both followed accounts and keyword searches."""
    all_tweets = []
    
    # Get trusted accounts
    trusted_accounts = db.query(TwitterAccount).filter_by(is_trusted=True).all()
    
    # Fetch from trusted accounts
    for account in trusted_accounts:
        tweets = client.get_user_tweets(account.username)
        all_tweets.extend(tweets)
    
    # Search using keywords
    for query in get_search_queries():
        tweets = client.search_tweets(query)
        all_tweets.extend(tweets)
    
    # Filter and process tweets
    return filter_tweets(all_tweets, db) 