# ===== 8. app/services/email_service.py - Email Business Logic =====
import os
import logging
from typing import Dict, List, Optional
from flask import session
from app import db
from app.database_models import Email, ClassifiedEmail
from app.email_processor import EmailProcessor
from app.email_processing.email_sender import EmailSender

logger = logging.getLogger(__name__)

class EmailService:
    """Service class for email-related business logic"""
    
    def __init__(self):
        self.email_processor = EmailProcessor()
        self.email_sender = EmailSender()
    
    def prepare_reply_data(self, email_id: int) -> Dict:
        """Prepare data for reply form"""
        email = Email.query.get_or_404(email_id)
        classified = ClassifiedEmail.query.filter_by(email_id=email_id).first()
        
        reply_data = {
            'to': email.sender_email,
            'subject': f"Re: {email.subject}" if not email.subject.startswith('Re:') else email.subject,
            'original_date': email.received_at.strftime('%B %d, %Y at %I:%M %p'),
            'original_from': f"{email.sender_name} <{email.sender_email}>",
            'original_subject': email.subject,
            'original_body': email.body_cleaned[:500] + '...' if len(email.body_cleaned) > 500 else email.body_cleaned
        }
        
        return {
            'email': email,
            'classified': classified,
            'reply_data': reply_data
        }
    
    def prepare_forward_data(self, email_id: int) -> Dict:
        """Prepare data for forward form"""
        email = Email.query.get_or_404(email_id)
        classified = ClassifiedEmail.query.filter_by(email_id=email_id).first()
        
        forward_data = {
            'to': '',  # Empty for forward
            'subject': f"Fwd: {email.subject}",
            'original_date': email.received_at.strftime('%B %d, %Y at %I:%M %p'),
            'original_from': f"{email.sender_name} <{email.sender_email}>",
            'original_subject': email.subject,
            'original_body': email.body_cleaned
        }
        
        return {
            'email': email,
            'classified': classified,
            'forward_data': forward_data
        }
    
    def send_email_from_form(self, form_data, files) -> Dict:
        """Process and send email from form data"""
        try:
            # Extract form data
            to_email = form_data.get('to')
            cc_emails = form_data.get('cc', '').strip()
            bcc_emails = form_data.get('bcc', '').strip()
            subject = form_data.get('subject')
            message_body = form_data.get('message')
            
            # Validate required fields
            if not to_email or not subject or not message_body:
                return {
                    'success': False,
                    'message': 'Please fill in all required fields (To, Subject, Message)'
                }
            
            # Validate email addresses
            validation_result = self._validate_all_emails(to_email, cc_emails, bcc_emails)
            if not validation_result['valid']:
                return validation_result
            
            # Process attachments
            attachment_files = self._process_attachments(files.getlist('attachments'))
            
            # Send email
            if self.email_processor.authenticate_gmail():
                success = self.email_processor.send_enhanced_email(
                    to_email=to_email,
                    cc_emails=cc_emails,
                    bcc_emails=bcc_emails,
                    subject=subject,
                    message_body=message_body,
                    attachments=attachment_files,
                    reply_type='compose'
                )
                
                # Clean up temporary files
                self._cleanup_temp_files(attachment_files)
                
                if success:
                    return {'success': True, 'message': 'Email sent successfully!'}
                else:
                    return {'success': False, 'message': 'Failed to send email. Please try again.'}
            else:
                return {'success': False, 'message': 'Gmail authentication failed. Please try again.'}
                
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return {'success': False, 'message': f'Error sending email: {str(e)}'}
    
    def send_reply_from_form(self, form_data, files) -> Dict:
        """Process and send reply from form data"""
        try:
            # Extract form data
            to_email = form_data.get('to')
            cc_emails = form_data.get('cc', '').strip()
            bcc_emails = form_data.get('bcc', '').strip()
            subject = form_data.get('subject')
            message_body = form_data.get('message')
            reply_type = form_data.get('reply_type', 'reply')
            original_email_id = form_data.get('original_email_id')
            
            # Validate required fields
            if not to_email or not subject or not message_body:
                return {
                    'success': False,
                    'message': 'Please fill in all required fields (To, Subject, Message)',
                    'original_email_id': original_email_id
                }
            
            # Validate email addresses
            validation_result = self._validate_all_emails(to_email, cc_emails, bcc_emails)
            if not validation_result['valid']:
                validation_result['original_email_id'] = original_email_id
                return validation_result
            
            # Process attachments
            attachment_files = self._process_attachments(files.getlist('attachments'))
            
            # Send reply
            if self.email_processor.authenticate_gmail():
                success = self.email_processor.send_enhanced_email(
                    to_email=to_email,
                    cc_emails=cc_emails,
                    bcc_emails=bcc_emails,
                    subject=subject,
                    message_body=message_body,
                    attachments=attachment_files,
                    reply_type=reply_type
                )
                
                # Clean up temporary files
                self._cleanup_temp_files(attachment_files)
                
                if success:
                    action_text = {
                        'reply': 'Reply sent',
                        'replyAll': 'Reply All sent',
                        'forward': 'Email forwarded'
                    }.get(reply_type, 'Email sent')
                    
                    return {
                        'success': True,
                        'message': f'{action_text} successfully!',
                        'original_email_id': original_email_id
                    }
                else:
                    return {
                        'success': False,
                        'message': 'Failed to send email. Please try again.',
                        'original_email_id': original_email_id
                    }
            else:
                return {
                    'success': False,
                    'message': 'Gmail authentication failed. Please re-authenticate.',
                    'original_email_id': original_email_id
                }
                
        except Exception as e:
            logger.error(f"Error sending reply: {e}")
            return {
                'success': False,
                'message': f'Error sending reply: {str(e)}',
                'original_email_id': form_data.get('original_email_id')
            }
    
    def validate_and_get_attachment_path(self, filename: str) -> str:
        """Validate attachment access and return file path"""
        # Normalize and validate the path
        filename = os.path.normpath(filename).replace('\\', '/')
        
        # Reject directory traversal attempts
        if '..' in filename or filename.startswith('/') or filename.startswith('\\'):
            logger.warning(f"Directory traversal attempt blocked: {filename}")
            raise PermissionError("Access denied")
        
        attachments_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'attachments')
        filepath = os.path.join(attachments_dir, filename)
        
        # Better path validation
        try:
            abs_filepath = os.path.abspath(os.path.realpath(filepath))
            abs_attachments_dir = os.path.abspath(os.path.realpath(attachments_dir))
            
            if not abs_filepath.startswith(abs_attachments_dir):
                logger.warning(f"Path escape attempt blocked: {filename}")
                raise PermissionError("Access denied")
                
        except (OSError, ValueError) as e:
            logger.warning(f"Invalid file path: {filename} - {e}")
            raise PermissionError("Invalid file path")
        
        # Check if file exists
        if not os.path.exists(filepath):
            logger.info(f"File not found: {filename}")
            raise FileNotFoundError("File not found")
        
        # Verify this attachment belongs to a valid email in database
        normalized_filename = filename.replace('\\', '/')
        emails_with_attachment = Email.query.filter(
            Email.attachments.contains(normalized_filename)
        ).first()
        
        if not emails_with_attachment:
            logger.warning(f"Unauthorized attachment access attempt: {filename} by user {session.get('username', 'unknown')}")
            raise PermissionError("Unauthorized access")
        
        # Log successful access
        logger.info(f"Serving attachment: {filename} to user {session.get('username', 'unknown')}")
        
        return filepath
    
    def get_emails_paginated(self, category: str, page: int, per_page: int) -> Dict:
        """Get paginated emails for a category"""
        emails = db.session.query(ClassifiedEmail, Email).join(Email).filter(
            ClassifiedEmail.category == category
        ).order_by(Email.received_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        result = []
        for classified, email in emails.items:
            result.append({
                'id': email.id,
                'subject': email.subject,
                'sender_name': email.sender_name,
                'sender_email': email.sender_email,
                'received_at': email.received_at.isoformat(),
                'priority': classified.priority,
                'summary': classified.summary,
                'is_read': classified.is_read
            })
        
        return {
            'emails': result,
            'total': emails.total,
            'pages': emails.pages,
            'current_page': emails.page
        }
    
    def mark_email_read(self, email_id: int) -> bool:
        """Mark email as read"""
        try:
            classified = ClassifiedEmail.query.filter_by(email_id=email_id).first()
            if classified:
                classified.is_read = True
                db.session.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error marking email as read: {e}")
            return False
    
    def archive_email(self, email_id: int) -> bool:
        """Archive email"""
        try:
            classified = ClassifiedEmail.query.filter_by(email_id=email_id).first()
            if classified:
                classified.is_archived = True
                db.session.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error archiving email: {e}")
            return False
    
    def validate_email_addresses(self, email_string: str) -> Dict:
        """Validate email addresses"""
        return self.email_sender.validate_email_addresses(email_string)
    
    def _validate_all_emails(self, to_email: str, cc_emails: str, bcc_emails: str) -> Dict:
        """Validate all email fields"""
        # Validate TO email
        to_validation = self.email_sender.validate_email_addresses(to_email)
        if not to_validation['valid']:
            return {
                'success': False,
                'message': f'Invalid TO email address: {", ".join(to_validation["invalid"])}'
            }
        
        # Validate CC emails if provided
        if cc_emails:
            cc_validation = self.email_sender.validate_email_addresses(cc_emails)
            if not cc_validation['valid']:
                return {
                    'success': False,
                    'message': f'Invalid CC email address: {", ".join(cc_validation["invalid"])}'
                }
        
        # Validate BCC emails if provided
        if bcc_emails:
            bcc_validation = self.email_sender.validate_email_addresses(bcc_emails)
            if not bcc_validation['valid']:
                return {
                    'success': False,
                    'message': f'Invalid BCC email address: {", ".join(bcc_validation["invalid"])}'
                }
        
        return {'valid': True}
    
    def _process_attachments(self, attachment_files) -> List[Dict]:
        """Process uploaded attachment files"""
        processed_files = []
        
        if not attachment_files:
            return processed_files
        
        upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'temp_uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        for file in attachment_files:
            if file.filename != '':
                # Validate file size (50MB limit)
                file.seek(0, os.SEEK_END)
                file_size = file.tell()
                file.seek(0)
                
                if file_size > 50 * 1024 * 1024:  # 50MB limit
                    logger.warning(f'File {file.filename} is too large (max 50MB)')
                    continue
                
                # Create safe filename
                import time
                timestamp = int(time.time())
                safe_filename = f"{timestamp}_{file.filename}"
                filepath = os.path.join(upload_dir, safe_filename)
                file.save(filepath)
                processed_files.append({
                    'filepath': filepath,
                    'filename': file.filename
                })
        
        return processed_files
    
    def _cleanup_temp_files(self, attachment_files: List[Dict]):
        """Clean up temporary attachment files"""
        for att in attachment_files:
            try:
                os.remove(att['filepath'])
            except Exception as e:
                logger.warning(f"Could not remove temp file {att['filepath']}: {e}")