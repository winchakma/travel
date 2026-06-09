import os
import logging
from typing import List
from app.models.user import User

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Notifications")

class NotificationService:
    @staticmethod
    async def broadcast_to_all(title: str, message: str):
        """Sends a notification to all members."""
        users = await User.find_all().to_list()
        emails = [u.email for u in users if u.email]
        phones = [u.phoneNumber for u in users if u.phoneNumber]
        
        logger.info(f"SYNCING BROADCAST: {title}")
        
        # 1. Send Emails
        await NotificationService.send_bulk_email(emails, title, message)
        
        # 2. Send SMS
        await NotificationService.send_bulk_sms(phones, f"{title}: {message}")

    @staticmethod
    async def notify_new_class(class_name: str, time: str, trainer: str):
        """Notifies all members about a newly added class."""
        title = "NEW ELITE SESSION ADDED"
        frontend_url = os.getenv("FRONTEND_URL", "https://mygym-p9rd.vercel.app")
        message = f"Gear up! {class_name} with {trainer} has been scheduled for {time}. Book your spot now in the Member HUD!<br><br><a href='{frontend_url}/community.html' style='display: inline-block; padding: 10px 20px; background-color: #f5e642; color: #000; text-decoration: none; font-weight: bold; border-radius: 5px;'>Go to Member HUD</a>"
        
        await NotificationService.broadcast_to_all(title, message)

    @staticmethod
    async def notify_gym_closure(reason: str = "Maintenance"):
        """Notifies all members that the gym is closed."""
        title = "GYM STATUS: CLOSED"
        frontend_url = os.getenv("FRONTEND_URL", "https://mygym-p9rd.vercel.app")
        message = f"Attention Elite Members: The gym will be closed today for {reason}. We apologize for the inconvenience and will resume synchronization tomorrow.<br><br><a href='{frontend_url}' style='display: inline-block; padding: 10px 20px; background-color: #333; color: #fff; text-decoration: none; border-radius: 5px;'>Check Website for Updates</a>"
        
        await NotificationService.broadcast_to_all(title, message)

    @staticmethod
    async def send_bulk_email(emails: List[str], subject: str, content: str):
        """Sends real emails using the Brevo HTTP API."""
        brevo_key = os.getenv("BREVO_API_KEY", "").strip()
        if not brevo_key:
            logger.warning("BREVO_API_KEY credentials missing. Simulation mode active.")
            for email in emails:
                logger.info(f"[SIMULATED EMAIL] To: {email} | Subject: {subject}")
            return

        import asyncio

        def sync_send_brevo(recipients: List[str], mail_subject: str, mail_content: str, api_key: str):
            import requests
            url = "https://api.brevo.com/v3/smtp/email"
            headers = {
                "accept": "application/json",
                "api-key": api_key,
                "content-type": "application/json"
            }
            
            for recipient in recipients:
                recipient_clean = recipient.strip().lower()
                if not recipient_clean:
                    continue
                try:
                    payload = {
                        "sender": {"name": "East Blue Gym", "email": "winchakma123@gmail.com"},
                        "to": [{"email": recipient_clean}],
                        "subject": mail_subject,
                        "htmlContent": f"<html><body><p>{mail_content}</p></body></html>"
                    }
                    response = requests.post(url, json=payload, headers=headers, timeout=10)
                    if response.ok:
                        logger.info(f"[BREVO EMAIL SUCCESS] Delivered to: {recipient_clean}")
                    else:
                        logger.error(f"[BREVO EMAIL ERROR] Failed delivering to {recipient_clean}: {response.text}")
                except Exception as e:
                    logger.error(f"[BREVO EMAIL ERROR] Exception delivering to {recipient_clean}: {e}")

        # Offload blocking HTTP calls to a background thread to prevent Render HTTP request timeout
        logger.info(f"[BREVO BACKGROUND INITIATED] Queued {len(emails)} emails: {subject}")
        asyncio.create_task(asyncio.to_thread(sync_send_brevo, emails, subject, content, brevo_key))

    @staticmethod
    async def send_bulk_sms(phones: List[str], message: str):
        """Placeholder for SMS. In production, use Twilio or Email-to-SMS gateways."""
        for phone in phones:
            logger.info(f"[SMS QUEUED] To: {phone} | Message: {message}")
        # Note: Professional SMS requires a service like Twilio.

