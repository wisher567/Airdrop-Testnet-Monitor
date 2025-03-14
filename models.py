from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class TwitterAccount(Base):
    __tablename__ = 'twitter_accounts'
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    is_trusted = Column(Boolean, default=False)
    is_blacklisted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class ProcessedTweet(Base):
    __tablename__ = 'processed_tweets'
    
    id = Column(Integer, primary_key=True)
    tweet_id = Column(String, unique=True, nullable=False)
    author_id = Column(String, nullable=False)
    text = Column(String)
    processed_text = Column(String)
    created_at = Column(DateTime)
    processed_at = Column(DateTime, default=datetime.utcnow)
    is_retweet = Column(Boolean, default=False)
    is_reply = Column(Boolean, default=False)

class AirdropOpportunity(Base):
    __tablename__ = 'airdrop_opportunities'
    
    id = Column(Integer, primary_key=True)
    tweet_id = Column(String, ForeignKey('processed_tweets.tweet_id'))
    project_name = Column(String)
    token_symbol = Column(String)
    description = Column(String)
    deadline = Column(DateTime)
    participation_steps = Column(String)
    tweet_url = Column(String)
    confidence_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    notified = Column(Boolean, default=False)
    
    tweet = relationship("ProcessedTweet")

# Create engine and tables
def init_db(db_url='sqlite:///airdrops.db'):
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    return engine 