import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import telegram
from typing import List
from models import AirdropOpportunity

class EmailNotifier:
    def __init__(self, smtp_server: str, smtp_port: int, username: str, password: str):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
    
    def format_opportunity(self, opportunity: AirdropOpportunity) -> str:
        """Format an airdrop opportunity into a readable email message."""
        message = f"""
New Airdrop/Testnet Opportunity!

Project: {opportunity.project_name or 'Unknown'}
Token: {opportunity.token_symbol or 'Unknown'}
Confidence Score: {opportunity.confidence_score:.1f}%

{opportunity.description or ''}

"""
        if opportunity.deadline:
            message += f"Deadline: {opportunity.deadline.strftime('%Y-%m-%d %H:%M UTC')}\n"
        
        if opportunity.participation_steps:
            message += f"\nHow to Participate:\n{opportunity.participation_steps}\n"
        
        message += f"\nSource: {opportunity.tweet_url}"
        
        return message
    
    def send_notification(self, recipient: str, opportunities: List[AirdropOpportunity]) -> bool:
        """Send email notification for new opportunities."""
        if not opportunities:
            return True
            
        try:
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = recipient
            msg['Subject'] = f"New Airdrop Opportunities ({len(opportunities)})"
            
            body = "Here are the latest airdrop and testnet opportunities:\n\n"
            body += "\n" + "="*50 + "\n\n".join(
                self.format_opportunity(opp) for opp in opportunities
            )
            
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
                
            return True
            
        except Exception as e:
            print(f"Failed to send email notification: {str(e)}")
            return False

class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot = telegram.Bot(token=bot_token)
        self.chat_id = chat_id
    
    def format_opportunity(self, opportunity: AirdropOpportunity) -> str:
        """Format an airdrop opportunity into a Telegram message."""
        message = f"""
🚀 *New Airdrop/Testnet Opportunity!*

*Project:* {opportunity.project_name or 'Unknown'}
*Token:* {opportunity.token_symbol or 'Unknown'}
*Confidence:* {opportunity.confidence_score:.1f}%

{opportunity.description or ''}

"""
        if opportunity.deadline:
            message += f"*Deadline:* {opportunity.deadline.strftime('%Y-%m-%d %H:%M UTC')}\n"
        
        if opportunity.participation_steps:
            message += f"\n*How to Participate:*\n{opportunity.participation_steps}\n"
        
        message += f"\n[View Tweet]({opportunity.tweet_url})"
        
        return message
    
    async def send_notification(self, opportunities: List[AirdropOpportunity]) -> bool:
        """Send Telegram notification for new opportunities."""
        if not opportunities:
            return True
            
        try:
            for opp in opportunities:
                message = self.format_opportunity(opp)
                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=message,
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
            return True
            
        except Exception as e:
            print(f"Failed to send Telegram notification: {str(e)}")
            return False

class NotificationManager:
    def __init__(self, email_notifier: EmailNotifier = None, 
                 telegram_notifier: TelegramNotifier = None,
                 min_confidence: float = 80.0):
        self.email_notifier = email_notifier
        self.telegram_notifier = telegram_notifier
        self.min_confidence = min_confidence
    
    def filter_opportunities(self, opportunities: List[AirdropOpportunity]) -> List[AirdropOpportunity]:
        """Filter opportunities based on confidence score."""
        return [opp for opp in opportunities if opp.confidence_score >= self.min_confidence]
    
    async def notify(self, opportunities: List[AirdropOpportunity], email_recipient: str = None) -> bool:
        """Send notifications through all configured channels."""
        filtered_opps = self.filter_opportunities(opportunities)
        if not filtered_opps:
            return True
            
        success = True
        
        if self.email_notifier and email_recipient:
            success &= self.email_notifier.send_notification(email_recipient, filtered_opps)
            
        if self.telegram_notifier:
            success &= await self.telegram_notifier.send_notification(filtered_opps)
            
        return success 