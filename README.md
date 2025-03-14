# Airdrop-Testnet-Monitor
An automated system to monitor Twitter for cryptocurrency airdrop and testnet opportunities. The system fetches tweets from trusted accounts and keyword searches, processes them to extract relevant information, and sends notifications through email and/or Telegram.

## Features

- **Tweet Collection**: Monitors specified Twitter accounts and searches for airdrop/testnet-related keywords
- **Smart Filtering**: Removes spam and irrelevant content
- **Information Extraction**: Uses NLP to extract project names, token symbols, deadlines, and participation instructions
- **Confidence Scoring**: Assigns a confidence score to each opportunity based on multiple factors
- **Multi-channel Notifications**: Supports both email and Telegram notifications
- **Persistence**: Stores all data in a SQLite database for historical tracking

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd airdrop-monitor
```

2. Install dependencies:
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

3. Set up environment variables:
```bash
# Twitter API credentials
export TWITTER_API_KEY="your_api_key"
export TWITTER_API_SECRET="your_api_secret"
export TWITTER_ACCESS_TOKEN="your_access_token"
export TWITTER_ACCESS_TOKEN_SECRET="your_access_token_secret"

# Email configuration (optional)
export EMAIL_SMTP_SERVER="smtp.gmail.com"
export EMAIL_SMTP_PORT="587"
export EMAIL_USERNAME="your_email@gmail.com"
export EMAIL_PASSWORD="your_app_specific_password"
export EMAIL_RECIPIENT="recipient@example.com"

# Telegram configuration (optional)
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"

# Monitor settings
export MIN_CONFIDENCE_SCORE="80.0"
export CHECK_INTERVAL_MINUTES="30"
```

4. Run the monitor:
```bash
python main.py
```

## Configuration

### Twitter Accounts

The system comes with a default list of trusted accounts. To add or modify accounts, you can use the SQLite database directly or create a management script.

Default trusted accounts:
- @AirdropAlert
- @CryptoAirdrops
- @TestnetAnnounce

### Keywords

The system searches for tweets containing various airdrop and testnet related keywords. These are defined in `fetch_tweets.py` and can be modified as needed.

### Confidence Scoring

The confidence score (0-100) is calculated based on multiple factors:
- Presence of project name (+20)
- Presence of token symbol (+20)
- Presence of deadline (+15)
- Presence of participation instructions (+15)
- Spam indicators (-5 each)
- Account verification status (future implementation)

Only opportunities with confidence scores above the `MIN_CONFIDENCE_SCORE` threshold will trigger notifications.

## Database Schema

The system uses SQLite with the following main tables:

- `twitter_accounts`: Tracked Twitter accounts
- `processed_tweets`: All processed tweets
- `airdrop_opportunities`: Extracted airdrop/testnet opportunities

## Notifications

### Email
Emails include:
- Project name and token symbol
- Confidence score
- Description and deadline
- Participation instructions
- Source tweet link

### Telegram
Telegram messages include the same information as emails but are formatted for Telegram's Markdown support and include clickable links.

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License

MIT License - see LICENSE file for details 
