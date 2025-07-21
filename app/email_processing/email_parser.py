# app/email_processing/email_parser.py
import base64
import re
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import html2text
from .attachment_handler import AttachmentHandler

logger = logging.getLogger(__name__)

class EmailParser:
    """Handles parsing of Gmail messages into structured data"""

    def __init__(self, attachment_handler: AttachmentHandler):
        self.attachment_handler = attachment_handler
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = True
        self.html_converter.ignore_images = True

    def parse_gmail_message(self, message: Dict, gmail_client, is_sent: bool = False) -> Optional[Dict]:
        """Parse Gmail message with improved attachment handling"""
        try:
            headers = {h['name']: h['value'] for h in message['payload'].get('headers', [])}

            # Get sender email early for attachment organization
            if is_sent:
                sender_email = self._extract_email_from_string(headers.get('From', '')) or 'mikeaubry2025@gmail.com'
                recipient_email = self._extract_email_from_string(headers.get('To', ''))
            else:
                sender_email = self._extract_email_from_string(headers.get('From', ''))
                recipient_email = self._extract_email_from_string(headers.get('To', ''))

            # Extract body and attachments with sender context
            body_html = ''
            body_text = ''
            attachments = []

            if 'parts' in message['payload']:
                # Pass sender_email for attachment organization
                body_html, body_text, attachments = self._process_message_parts(
                    message['payload']['parts'], message['id'], sender_email, gmail_client
                )
            else:
                # Single part message - check for both text content AND attachments
                payload = message['payload']
                mime_type = payload['mimeType']

                if mime_type == 'text/html':
                    data = payload['body'].get('data', '')
                    if data:
                        body_html = base64.urlsafe_b64decode(data).decode('utf-8')
                elif mime_type == 'text/plain':
                    data = payload['body'].get('data', '')
                    if data:
                        body_text = base64.urlsafe_b64decode(data).decode('utf-8')
                else:
                    # ✅ FIX: Handle single-part attachments (images, PDFs, etc.)
                    filename = payload.get('filename', '')
                    attachment_id = payload['body'].get('attachmentId')

                    if filename or attachment_id:
                        # This is a single-part attachment
                        logger.info(f"Detected single-part attachment: {filename}, MIME: {mime_type}")
                        attachment_info = self.attachment_handler.process_attachment_part(
                            payload, message['id'], sender_email, gmail_client
                        )
                        if attachment_info:
                            attachments.append(attachment_info)
                            logger.info(f"Successfully processed single-part attachment: {filename}")

                        # Set a default body for attachment-only emails
                        body_text = f"[Attachment: {filename}]" if filename else "[Attachment]"
                    else:
                        # Unknown single-part content type
                        logger.warning(f"Unknown single-part MIME type: {mime_type}")
                        body_text = f"[Content type: {mime_type}]"

            # Convert HTML to text if needed
            if body_html and not body_text:
                body_text = self.html_converter.handle(body_html)

            # Parse date and names
            date_str = headers.get('Date', '')
            received_at = self._parse_email_date(date_str)

            if is_sent:
                sender_name = "Michael Aubry"
                recipient_name = self._extract_name_from_email(headers.get('To', ''))
            else:
                sender_name = self._extract_name_from_email(headers.get('From', ''))
                recipient_name = self._extract_name_from_email(headers.get('To', ''))

            return {
                'message_id': message['id'],
                'thread_id': message.get('threadId'),
                'subject': headers.get('Subject', ''),
                'sender_name': sender_name,
                'sender_email': sender_email,
                'recipient_name': recipient_name,
                'recipient_email': recipient_email,
                'received_at': received_at,
                'body_raw': body_html or body_text,
                'body_cleaned': self._clean_email_body(body_text),
                'labels': message.get('labelIds', []),
                'is_sent': is_sent,
                'attachments': attachments
            }

        except Exception as e:
            logger.error(f"Error parsing message: {e}")
            return None

    def _process_message_parts(self, parts: List[Dict], message_id: str,
                             sender_email: str, gmail_client) -> Tuple[str, str, List[Dict]]:
        """Process message parts to extract text and attachments with sender context"""
        body_html = ''
        body_text = ''
        attachments = []

        for part in parts:
            mime_type = part.get('mimeType', '')
            filename = part.get('filename', '')

            # Handle nested parts (multipart messages)
            if 'parts' in part:
                sub_html, sub_text, sub_attachments = self._process_message_parts(
                    part['parts'], message_id, sender_email, gmail_client
                )
                body_html += sub_html
                body_text += sub_text
                attachments.extend(sub_attachments)
                continue

            # Handle text content
            if mime_type == 'text/html':
                data = part['body'].get('data', '')
                if data:
                    body_html += base64.urlsafe_b64decode(data).decode('utf-8')
            elif mime_type == 'text/plain':
                data = part['body'].get('data', '')
                if data:
                    body_text += base64.urlsafe_b64decode(data).decode('utf-8')

            # Handle attachments with sender context
            elif filename or part['body'].get('attachmentId'):
                attachment_info = self.attachment_handler.process_attachment_part(
                    part, message_id, sender_email, gmail_client
                )
                if attachment_info:
                    attachments.append(attachment_info)

        return body_html, body_text, attachments

    def _clean_email_body(self, body: str) -> str:
        """Clean email body for processing"""
        if not body:
            return ''

        # Remove excessive whitespace
        body = re.sub(r'\n\s*\n', '\n\n', body)
        body = re.sub(r' +', ' ', body)

        # Remove common email artifacts
        body = re.sub(r'Sent from my \w+', '', body)
        body = re.sub(r'Get Outlook for \w+', '', body)

        # Truncate very long emails
        if len(body) > 5000:
            body = body[:5000] + '... [truncated]'

        return body.strip()

    def _extract_name_from_email(self, email_string: str) -> str:
        """Extract name from email string like 'John Doe <john@example.com>'"""
        match = re.match(r'^([^<]+)<', email_string.strip())
        if match:
            return match.group(1).strip().strip('"\'')
        return ''

    def _extract_email_from_string(self, email_string: str) -> str:
        """Extract email address from string"""
        match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', email_string)
        return match.group(0) if match else ''

    def _parse_email_date(self, date_str: str) -> datetime:
        """Parse email date string to datetime"""
        try:
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_str)
        except:
            return datetime.now()