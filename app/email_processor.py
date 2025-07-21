
import gc
import psutil
# app/email_processor.py - FIXED VERSION with improved critical classification

# app/email_processor.py - Main orchestrator (simplified)
import os
import logging
from typing import Dict, List
from datetime import datetime
import json

from .email_processing.gmail_client import GmailClient
from .email_processing.attachment_handler import AttachmentHandler
from .email_processing.email_parser import EmailParser
from .email_processing.email_classifier import EmailClassifier
from .email_processing.email_sender import EmailSender
from .property_management.property_manager import PropertyManager
from .database_models import db, Email, ClassifiedEmail, ProcessingLog

logger = logging.getLogger(__name__)

class EmailProcessor:
    """Main email processing orchestrator"""

    def __init__(self):
        """Initialize the email processor with all components"""
        # Initialize components
        self.gmail_client = GmailClient()

        attachments_base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'attachments')
        self.attachment_handler = AttachmentHandler(attachments_base_dir)

        self.email_parser = EmailParser(self.attachment_handler)
        self.email_classifier = EmailClassifier()
        self.email_sender = EmailSender()
        self.property_manager = PropertyManager()

    def authenticate_gmail(self) -> bool:
        """Authenticate Gmail client"""
        return self.gmail_client.authenticate()

    def send_enhanced_email(self, to_email: str, cc_emails: str = '', bcc_emails: str = '',
                       subject: str = '', message_body: str = '',
                       attachments: List[Dict] = None, reply_type: str = 'compose') -> bool:
        """Send enhanced email with CC, BCC support"""
        return self.email_sender.send_enhanced_email(
            self.gmail_client, to_email, subject, message_body,
            cc_emails, bcc_emails, attachments, reply_type
        )

    def process_new_emails(self, hours_back: int = 24) -> Dict:
        """Main processing function - fetch and classify new emails (received only)"""
        log = ProcessingLog()
        db.session.add(log)
        db.session.commit()

        try:
            logger.info("Starting email processing...")

            # Fetch recent emails (received only)
            gmail_messages = self.gmail_client.get_recent_emails(hours_back=hours_back)
            log.emails_processed = len(gmail_messages)

            new_count = 0
            errors = []

            for gmail_message in gmail_messages:
                try:
                    # Parse email
                    email_data = self.email_parser.parse_gmail_message(
                        gmail_message, self.gmail_client, is_sent=False
                    )

                    if not email_data:
                        continue

                    # Classify email
                    classification = self.email_classifier.classify_email(email_data)

                    # Save to database
                    if self._save_email_to_database(email_data, classification):
                        new_count += 1

                except Exception as e:
                    error_msg = f"Error processing email: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            # Update log
            log.completed_at = datetime.now()
            log.status = 'completed'
            log.emails_new = new_count
            if errors:
                import json
                log.errors = json.dumps(errors)

            db.session.commit()

            result = {
                'status': 'success',
                'processed': len(gmail_messages),
                'new': new_count,
                'errors': len(errors)
            }

            logger.info(f"Processing completed: {result}")
            return result

        except Exception as e:
            log.completed_at = datetime.now()
            log.status = 'failed'
            log.add_error(str(e))
            db.session.commit()

            logger.error(f"Processing failed: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'processed': 0,
                'new': 0,
                'errors': 1
            }

    def process_sent_emails(self, hours_back: int = 24) -> Dict:
        """Process sent emails specifically"""
        try:
            logger.info("Starting sent email processing...")

            # Fetch sent emails
            gmail_messages = self.gmail_client.get_sent_emails(hours_back=hours_back)

            new_count = 0
            errors = []

            for gmail_message in gmail_messages:
                try:
                    # Parse email
                    email_data = self.email_parser.parse_gmail_message(
                        gmail_message, self.gmail_client, is_sent=True
                    )

                    if not email_data:
                        continue

                    # Classify email (simplified for sent)
                    classification = self.email_classifier.classify_email(email_data)

                    # Save to database
                    if self._save_email_to_database(email_data, classification):
                        new_count += 1

                except Exception as e:
                    error_msg = f"Error processing sent email: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            result = {
                'status': 'success',
                'processed': len(gmail_messages),
                'new': new_count,
                'errors': len(errors)
            }

            logger.info(f"Sent email processing completed: {result}")
            return result

        except Exception as e:
            logger.error(f"Sent email processing failed: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'processed': 0,
                'new': 0,
                'errors': 1
            }

    def send_reply(self, to_email: str, subject: str, message_body: str) -> bool:
        """Send email reply"""
        return self.email_sender.send_reply(
            self.gmail_client, to_email, subject, message_body
        )

    def send_email_with_attachments(self, to_email: str, subject: str,
                                   message_body: str, attachments: List[Dict] = None) -> bool:
        """Send email with optional attachments"""
        return self.email_sender.send_email_with_attachments(
            self.gmail_client, to_email, subject, message_body, attachments
        )

    def _save_email_to_database(self, email_data: Dict, classification: Dict) -> bool:
        """Save email and classification to database"""
        try:
            # Check if email already exists
            existing = Email.query.filter_by(message_id=email_data['message_id']).first()
            if existing:
                logger.info(f"Email {email_data['message_id']} already exists")
                return False

            # Create new email record
            email_record = Email(
                message_id=email_data['message_id'],
                thread_id=email_data.get('thread_id'),
                received_at=email_data['received_at'],
                sender_name=email_data.get('sender_name'),
                sender_email=email_data['sender_email'],
                recipient_name=email_data.get('recipient_name'),
                recipient_email=email_data.get('recipient_email'),
                is_sent=email_data.get('is_sent', False),
                subject=email_data.get('subject'),
                body_raw=email_data.get('body_raw'),
                body_cleaned=email_data.get('body_cleaned'),
                labels=json.dumps(email_data.get('labels', []))
            )

            # Save attachments info
            attachments = email_data.get('attachments', [])
            if attachments:
                email_record.set_attachments(attachments)
                logger.info(f"Saved {len(attachments)} attachments for email {email_data['message_id']}")

            db.session.add(email_record)
            db.session.flush()

            # Create classification record
            extracted_info = classification.get('extracted_info', {})
            if attachments:
                extracted_info['attachment_count'] = len(attachments)
                extracted_info['attachment_types'] = [att['mime_type'] for att in attachments]

            classified = ClassifiedEmail(
                email_id=email_record.id,
                category=classification['category'],
                sub_category=classification.get('sub_category'),
                priority=classification['priority'],
                confidence_score=classification.get('confidence_score'),
                summary=classification.get('summary'),
                extracted_info=json.dumps(extracted_info),
                tags=json.dumps(classification.get('tags', [])),
                property_address=extracted_info.get('property_address'),
                property_type=extracted_info.get('property_type'),
                contact_name=extracted_info.get('contact_name'),
                contact_phone=extracted_info.get('contact_phone'),
                contact_email=extracted_info.get('contact_email'),
                requires_action=classification.get('requires_action', False)
            )

            db.session.add(classified)

            # Link to property if property information is available
            self.property_manager.link_email_to_property(email_record.id, classification)

            db.session.commit()

            email_type = "sent" if email_data.get('is_sent') else "received"
            attachment_info = f" with {len(attachments)} attachments" if attachments else ""
            logger.info(f"Saved {email_type} email: {email_record.subject} -> {classification['category']} ({classification['priority']}){attachment_info}")
            return True

        except Exception as e:
            logger.error(f"Database save error: {e}")
            db.session.rollback()
            return False
def cleanup_memory():
    """Force memory cleanup"""
    try:
        collected = gc.collect()
        logger.debug(f"Memory cleanup: {collected} objects collected")
        return True
    except Exception as e:
        logger.warning(f"Memory cleanup failed: {e}")
        return False
