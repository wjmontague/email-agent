# app/email_processing/__init__.py
"""Email processing components for the Email AI Agent"""

# Import shortcuts - makes imports cleaner
from .gmail_client import GmailClient
from .attachment_handler import AttachmentHandler
from .email_parser import EmailParser
from .email_classifier import EmailClassifier
from .email_sender import EmailSender

# Now you can do this:
# from app.email_processing import GmailClient, EmailParser

# Instead of this:
# from app.email_processing.gmail_client import GmailClient
# from app.email_processing.email_parser import EmailParser

__all__ = [
    'GmailClient',
    'AttachmentHandler', 
    'EmailParser',
    'EmailClassifier',
    'EmailSender'
]