# app/email_processing/gmail_client.py
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

class GmailClient:
    """Handles Gmail API authentication and email fetching"""

    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send'
    ]

    def __init__(self):
        self.service = None

    # Replace the authenticate method in your app/email_processing/gmail_client.py

    def authenticate(self) -> bool:
        """Authenticate with Gmail API - Web-friendly version"""
        try:
            creds = None
            token_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                                    'credentials', 'token.json')
            creds_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                                    'credentials', 'credentials.json')

            # Load existing credentials
            if os.path.exists(token_path):
                creds = Credentials.from_authorized_user_file(token_path, self.SCOPES)

            # If no valid credentials, return False (user needs to use web auth)
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    try:
                        # Try to refresh the token
                        creds.refresh(Request())

                        # Save refreshed credentials
                        with open(token_path, 'w') as token:
                            token.write(creds.to_json())

                        logger.info("Gmail token refreshed successfully")

                    except Exception as refresh_error:
                        logger.error(f"Token refresh failed: {refresh_error}")
                        return False
                else:
                    # No valid credentials - user needs to authorize via web
                    logger.info("No valid Gmail credentials - web authorization required")
                    return False

            # Build service with valid credentials
            self.service = build('gmail', 'v1', credentials=creds)
            logger.info("Gmail authentication successful")
            return True

        except Exception as e:
            logger.error(f"Gmail authentication error: {e}")
            return False

    def get_recent_emails(self, hours_back: int = 24, max_results: int = 100, include_sent: bool = False) -> List[Dict]:
        """Fetch recent emails from Gmail"""
        try:
            if not self.service and not self.authenticate():
                raise Exception("Gmail authentication failed")

            # Calculate date range
            after_date = datetime.now() - timedelta(hours=hours_back)

            # Build query
            if include_sent:
                query = f'after:{after_date.strftime("%Y/%m/%d")}'
            else:
                query = f'after:{after_date.strftime("%Y/%m/%d")} -in:sent'

            # Get message list
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])
            email_messages = []

            for message in messages:
                try:
                    # Get full message
                    msg = self.service.users().messages().get(
                        userId='me',
                        id=message['id'],
                        format='full'
                    ).execute()
                    email_messages.append(msg)

                except Exception as e:
                    logger.error(f"Error fetching message {message['id']}: {e}")
                    continue

            logger.info(f"Retrieved {len(email_messages)} emails")
            return email_messages

        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            return []

    def get_sent_emails(self, hours_back: int = 24, max_results: int = 100) -> List[Dict]:
        """Fetch sent emails from Gmail"""
        try:
            if not self.service and not self.authenticate():
                raise Exception("Gmail authentication failed")

            # Calculate date range
            after_date = datetime.now() - timedelta(hours=hours_back)
            query = f'after:{after_date.strftime("%Y/%m/%d")} in:sent'

            # Get message list
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])
            email_messages = []

            for message in messages:
                try:
                    msg = self.service.users().messages().get(
                        userId='me',
                        id=message['id'],
                        format='full'
                    ).execute()
                    email_messages.append(msg)

                except Exception as e:
                    logger.error(f"Error fetching sent message {message['id']}: {e}")
                    continue

            logger.info(f"Retrieved {len(email_messages)} sent emails")
            return email_messages

        except Exception as e:
            logger.error(f"Error fetching sent emails: {e}")
            return []

    def download_attachment(self, message_id: str, attachment_id: str) -> bytes:
        """Download attachment data from Gmail"""
        try:
            attachment_data = self.service.users().messages().attachments().get(
                userId='me',
                messageId=message_id,
                id=attachment_id
            ).execute()

            import base64
            return base64.urlsafe_b64decode(attachment_data['data'])

        except Exception as e:
            logger.error(f"Error downloading attachment {attachment_id}: {e}")
            raise