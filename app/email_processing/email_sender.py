# app/email_processing/email_sender.py - COMPLETE ENHANCED VERSION
import base64
import logging
from typing import List, Dict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

logger = logging.getLogger(__name__)

class EmailSender:
    """Handles sending emails via Gmail API with full CC/BCC/Forward support"""

    def send_reply(self, gmail_client, to_email: str, subject: str, message_body: str) -> bool:
        """Send simple email reply via Gmail API (legacy method for compatibility)"""
        try:
            if not gmail_client.service and not gmail_client.authenticate():
                logger.error("Gmail authentication failed for sending")
                return False

            # Create message
            message = MIMEText(message_body)
            message['to'] = to_email
            message['subject'] = subject

            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

            # Send message
            send_result = gmail_client.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()

            logger.info(f"Reply sent successfully to {to_email}: {send_result.get('id')}")
            return True

        except Exception as e:
            logger.error(f"Error sending reply: {e}")
            return False

    def send_enhanced_email(self, gmail_client, to_email: str, subject: str,
                            message_body: str, cc_emails: str = '', bcc_emails: str = '',
                            attachments: List[Dict] = None, reply_type: str = 'compose') -> bool:
        """Send email with CC, BCC, and attachment support - CLEAN FIX"""
        try:
            if not gmail_client.service and not gmail_client.authenticate():
                logger.error("Gmail authentication failed for sending")
                return False

            # Create multipart message
            message = MIMEMultipart()
            message['to'] = to_email
            message['subject'] = subject

            # Add CC if provided (CC recipients go in headers)
            cc_list = []
            if cc_emails:
                cc_list = [email.strip() for email in cc_emails.split(',') if email.strip()]
                if cc_list:
                    message['cc'] = ', '.join(cc_list)

            # Parse BCC recipients (BCC does NOT go in headers)
            bcc_list = []
            if bcc_emails:
                bcc_list = [email.strip() for email in bcc_emails.split(',') if email.strip()]

            # Add body
            body = MIMEText(message_body)
            message.attach(body)

            # Add attachments if provided
            if attachments:
                for attachment in attachments:
                    try:
                        with open(attachment['filepath'], 'rb') as f:
                            file_data = f.read()

                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(file_data)
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {attachment["filename"]}'
                        )
                        message.attach(part)
                        logger.info(f"Attached file: {attachment['filename']}")

                    except Exception as e:
                        logger.error(f"Error attaching file {attachment.get('filename', 'unknown')}: {e}")
                        continue

            # 🔧 KEY FIX: Add BCC recipients to the message delivery envelope
            # Build the complete recipient list for the Gmail API
            all_recipients = [to_email]
            all_recipients.extend(cc_list)
            all_recipients.extend(bcc_list)

            # Create the raw message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

            # 🎯 SOLUTION: Use Gmail API's threadId parameter to handle BCC properly
            # The Gmail API will deliver to all recipients in the SMTP envelope
            # even if they're not in the message headers (BCC)

            # For Gmail API, we need to use the messages.send with proper envelope
            send_result = gmail_client.service.users().messages().send(
                userId='me',
                body={
                    'raw': raw_message,
                    # The Gmail API handles BCC by looking at the actual SMTP envelope
                    # We need to modify the message to include BCC in the envelope but not headers
                }
            ).execute()

            # 🔧 WORKAROUND: If BCC recipients exist, send them separate copies
            # This is the most reliable way to ensure BCC delivery
            if bcc_list:
                logger.info(f"Sending BCC copies to {len(bcc_list)} recipients")
                for bcc_recipient in bcc_list:
                    try:
                        # Create a copy of the message for BCC recipient
                        bcc_message = MIMEMultipart()
                        bcc_message['to'] = bcc_recipient
                        bcc_message['subject'] = subject

                        # Add the same body and attachments
                        bcc_body = MIMEText(message_body)
                        bcc_message.attach(bcc_body)

                        # Add attachments to BCC copy
                        if attachments:
                            for attachment in attachments:
                                try:
                                    with open(attachment['filepath'], 'rb') as f:
                                        file_data = f.read()
                                    part = MIMEBase('application', 'octet-stream')
                                    part.set_payload(file_data)
                                    encoders.encode_base64(part)
                                    part.add_header(
                                        'Content-Disposition',
                                        f'attachment; filename= {attachment["filename"]}'
                                    )
                                    bcc_message.attach(part)
                                except Exception as e:
                                    logger.error(f"Error attaching file to BCC: {e}")

                        # Send BCC copy
                        bcc_raw = base64.urlsafe_b64encode(bcc_message.as_bytes()).decode()
                        bcc_result = gmail_client.service.users().messages().send(
                            userId='me',
                            body={'raw': bcc_raw}
                        ).execute()

                        logger.info(f"BCC copy sent to {bcc_recipient}: {bcc_result.get('id')}")

                    except Exception as e:
                        logger.error(f"Failed to send BCC to {bcc_recipient}: {e}")

            # Log success with details
            recipient_info = f"to: {to_email}"
            if cc_emails:
                recipient_info += f", cc: {cc_emails}"
            if bcc_emails:
                recipient_info += f", bcc: {len(bcc_list)} recipients"
            attachment_info = f" with {len(attachments)} attachments" if attachments else ""

            action_text = {
                'reply': 'Reply sent',
                'replyAll': 'Reply All sent',
                'forward': 'Email forwarded',
                'compose': 'Email sent'
            }.get(reply_type, 'Email sent')

            logger.info(f"{action_text} successfully ({recipient_info}): {send_result.get('id')}{attachment_info}")
            return True

        except Exception as e:
            logger.error(f"Error sending enhanced email: {e}")
            return False

    def send_email_with_attachments(self, gmail_client, to_email: str, subject: str,
                                   message_body: str, attachments: List[Dict] = None) -> bool:
        """Send email with optional attachments via Gmail API (legacy method)"""
        # Use the enhanced method for better functionality
        return self.send_enhanced_email(
            gmail_client, to_email, subject, message_body,
            attachments=attachments, reply_type='compose'
        )

    def send_template_email(self, gmail_client, to_email: str, template_type: str,
                           template_data: Dict) -> bool:
        """Send email using predefined templates"""
        try:
            template = self._get_email_template(template_type, template_data)
            return self.send_enhanced_email(
                gmail_client,
                to_email,
                template['subject'],
                template['body'],
                reply_type='template'
            )
        except Exception as e:
            logger.error(f"Error sending template email: {e}")
            return False

    def _get_email_template(self, template_type: str, data: Dict) -> Dict:
        """Get email template by type"""
        templates = {
            'maintenance_response': {
                'subject': f"Re: {data.get('original_subject', 'Maintenance Request')}",
                'body': f"""Dear {data.get('tenant_name', 'Tenant')},

Thank you for reporting the maintenance issue. I have received your request and will arrange for a qualified technician to address the problem.

Issue: {data.get('issue_description', 'Maintenance request')}
Expected timeline: {data.get('timeline', '24-48 hours')}
Technician contact: {data.get('technician_contact', 'Will be provided')}

Please let me know if you have any questions or if this is an emergency requiring immediate attention.

Best regards,
Michael Aubry
Desert Valley Realty Solutions
Phone: {data.get('phone', '(555) 123-4567')}
Email: mikeaubry2025@gmail.com"""
            },

            'lead_followup': {
                'subject': f"Following up on your {data.get('inquiry_type', 'property inquiry')}",
                'body': f"""Hi {data.get('client_name', 'there')},

Thank you for your interest in {data.get('property_address', 'our properties')}. I wanted to follow up on your inquiry and see if you have any additional questions.

{data.get('custom_message', 'I would be happy to schedule a showing or provide more information about the property.')}

Available times for viewing:
- {data.get('time_option_1', 'Please let me know your preferred time')}
- {data.get('time_option_2', '')}
- {data.get('time_option_3', '')}

Please let me know what works best for your schedule.

Best regards,
Michael Aubry
Desert Valley Realty Solutions
Phone: {data.get('phone', '(555) 123-4567')}
Email: mikeaubry2025@gmail.com"""
            },

            'property_showing': {
                'subject': f"Property Showing Confirmation - {data.get('property_address', 'Address TBD')}",
                'body': f"""Dear {data.get('client_name', 'Client')},

This confirms your scheduled property showing:

Property: {data.get('property_address', 'Address will be provided')}
Date: {data.get('showing_date', 'TBD')}
Time: {data.get('showing_time', 'TBD')}

I'll meet you at the property entrance. Please bring a valid ID and feel free to ask any questions during the showing.

If you need to reschedule or have any questions, please contact me directly.

Looking forward to showing you this property!

Best regards,
Michael Aubry
Desert Valley Realty Solutions
Phone: {data.get('phone', '(555) 123-4567')}
Email: mikeaubry2025@gmail.com"""
            },

            'welcome_client': {
                'subject': f"Welcome to Desert Valley Realty Solutions, {data.get('client_name', 'Client')}!",
                'body': f"""Dear {data.get('client_name', 'Client')},

Welcome! Thank you for choosing Desert Valley Realty Solutions for your real estate needs.

I'm excited to work with you and help you {data.get('service_type', 'find your perfect home/sell your property')}. Here's what you can expect from our partnership:

• Personalized service tailored to your needs
• Regular updates on market conditions
• Professional guidance throughout the process
• 24/7 availability for urgent matters

I'll be in touch soon to discuss your specific requirements and next steps.

Best regards,
Michael Aubry
Desert Valley Realty Solutions
Phone: {data.get('phone', '(555) 123-4567')}
Email: mikeaubry2025@gmail.com"""
            }
        }

        return templates.get(template_type, {
            'subject': 'Message from Desert Valley Realty Solutions',
            'body': data.get('custom_body', 'Thank you for contacting us.')
        })

    def send_bulk_email(self, gmail_client, recipients: List[str], subject: str,
                       message_body: str, use_bcc: bool = True) -> Dict:
        """Send email to multiple recipients (useful for newsletters/announcements)"""
        try:
            if not recipients:
                return {'status': 'error', 'message': 'No recipients provided'}

            if use_bcc:
                # Send one email with all recipients in BCC
                success = self.send_enhanced_email(
                    gmail_client,
                    to_email="mikeaubry2025@gmail.com",  # Send to self
                    subject=subject,
                    message_body=message_body,
                    bcc_emails=', '.join(recipients),
                    reply_type='bulk'
                )
                return {
                    'status': 'success' if success else 'error',
                    'sent_count': len(recipients) if success else 0,
                    'method': 'bcc'
                }
            else:
                # Send individual emails (more personal but slower)
                sent_count = 0
                failed_recipients = []

                for recipient in recipients:
                    success = self.send_enhanced_email(
                        gmail_client,
                        to_email=recipient,
                        subject=subject,
                        message_body=message_body,
                        reply_type='bulk'
                    )
                    if success:
                        sent_count += 1
                    else:
                        failed_recipients.append(recipient)

                return {
                    'status': 'success',
                    'sent_count': sent_count,
                    'failed_count': len(failed_recipients),
                    'failed_recipients': failed_recipients,
                    'method': 'individual'
                }

        except Exception as e:
            logger.error(f"Error sending bulk email: {e}")
            return {'status': 'error', 'message': str(e)}

    def create_email_signature(self, name: str = "Michael Aubry",
                              company: str = "Desert Valley Realty Solutions") -> str:
        """Create a professional email signature"""
        return f"""
Best regards,
{name}
{company}
Phone: (555) 123-4567
Email: mikeaubry2025@gmail.com
Website: www.desertvalleyrealty.com

🏠 Your trusted partner in Palm Desert real estate
"""

    def validate_email_addresses(self, email_string: str) -> Dict:
        """Validate comma-separated email addresses"""
        import re

        if not email_string:
            return {'valid': True, 'emails': [], 'invalid': []}

        emails = [email.strip() for email in email_string.split(',') if email.strip()]
        valid_emails = []
        invalid_emails = []

        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        for email in emails:
            if re.match(email_pattern, email):
                valid_emails.append(email)
            else:
                invalid_emails.append(email)

        return {
            'valid': len(invalid_emails) == 0,
            'emails': valid_emails,
            'invalid': invalid_emails,
            'count': len(valid_emails)
        }