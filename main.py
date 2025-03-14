import os
import asyncio
import schedule
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import init_db, TwitterAccount, ProcessedTweet, AirdropOpportunity
from fetch_tweets import TwitterClient, fetch_new_tweets
from extract_info import extract_airdrop_info
from notifications import EmailNotifier, TelegramNotifier, NotificationManager

# Configuration
TWITTER_API_KEY = os.getenv('TWITTER_API_KEY')
TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET')
TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
TWITTER_ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')

EMAIL_SMTP_SERVER = os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
EMAIL_SMTP_PORT = int(os.getenv('EMAIL_SMTP_PORT', '587'))
EMAIL_USERNAME = os.getenv('EMAIL_USERNAME')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
EMAIL_RECIPIENT = os.getenv('EMAIL_RECIPIENT')

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

MIN_CONFIDENCE_SCORE = float(os.getenv('MIN_CONFIDENCE_SCORE', '80.0'))
CHECK_INTERVAL_MINUTES = int(os.getenv('CHECK_INTERVAL_MINUTES', '30'))

# Initialize database
engine = init_db()
Session = sessionmaker(bind=engine)

def setup_initial_accounts(session):
    """Set up initial trusted Twitter accounts if none exist."""
    if session.query(TwitterAccount).count() == 0:
        initial_accounts = [
            TwitterAccount(username='AirdropAlert', is_trusted=True),
            TwitterAccount(username='CryptoAirdrops', is_trusted=True),
            TwitterAccount(username='TestnetAnnounce', is_trusted=True)
        ]
        session.add_all(initial_accounts)
        session.commit()

async def process_tweets():
    """Main function to process tweets and send notifications."""
    try:
        # Create new session
        session = Session()
        
        # Initialize clients
        twitter_client = TwitterClient(
            TWITTER_API_KEY,
            TWITTER_API_SECRET,
            TWITTER_ACCESS_TOKEN,
            TWITTER_ACCESS_TOKEN_SECRET
        )
        
        # Set up notifiers
        email_notifier = None
        if all([EMAIL_SMTP_SERVER, EMAIL_USERNAME, EMAIL_PASSWORD]):
            email_notifier = EmailNotifier(
                EMAIL_SMTP_SERVER,
                EMAIL_SMTP_PORT,
                EMAIL_USERNAME,
                EMAIL_PASSWORD
            )
        
        telegram_notifier = None
        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            telegram_notifier = TelegramNotifier(
                TELEGRAM_BOT_TOKEN,
                TELEGRAM_CHAT_ID
            )
        
        notification_manager = NotificationManager(
            email_notifier=email_notifier,
            telegram_notifier=telegram_notifier,
            min_confidence=MIN_CONFIDENCE_SCORE
        )
        
        # Fetch and process new tweets
        new_tweets = fetch_new_tweets(twitter_client, session)
        
        # Extract airdrop information
        opportunities = []
        for tweet in new_tweets:
            opportunity = extract_airdrop_info(tweet)
            if opportunity:
                opportunities.append(opportunity)
                session.add(opportunity)
            session.add(tweet)
        
        # Commit new tweets and opportunities to database
        session.commit()
        
        # Send notifications
        if opportunities:
            await notification_manager.notify(opportunities, EMAIL_RECIPIENT)
        
    except Exception as e:
        print(f"Error in process_tweets: {str(e)}")
    finally:
        session.close()

def run_scheduler():
    """Run the scheduler to periodically check for new tweets."""
    async def schedule_task():
        await process_tweets()
    
    # Schedule the task
    schedule.every(CHECK_INTERVAL_MINUTES).minutes.do(
        lambda: asyncio.run(schedule_task())
    )
    
    # Initialize database and accounts
    session = Session()
    setup_initial_accounts(session)
    session.close()
    
    print(f"Starting airdrop monitor. Checking every {CHECK_INTERVAL_MINUTES} minutes...")
    
    # Run the scheduler
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    run_scheduler() 