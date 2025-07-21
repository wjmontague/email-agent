import logging
from typing import Dict
from app.email_processor import EmailProcessor

logger = logging.getLogger(__name__)

class ProcessingService:
    """Service class for email processing operations"""
    
    def __init__(self):
        self.email_processor = EmailProcessor()
    
    def process_new_emails(self, hours_back: int = 24) -> Dict:
        """Process new emails from the last specified hours"""
        try:
            # Process both received and sent emails
            received_result = self.email_processor.process_new_emails(hours_back=hours_back)
            sent_result = self.email_processor.process_sent_emails(hours_back=hours_back)
            
            logger.info(f"Processed {received_result.get('processed', 0)} received emails, {received_result.get('new', 0)} new")
            logger.info(f"Processed {sent_result.get('processed', 0)} sent emails, {sent_result.get('new', 0)} new")
            
            # Log auto-fix results
            fixed_received = received_result.get('fixed', 0)
            fixed_sent = sent_result.get('fixed', 0)
            total_fixed = fixed_received + fixed_sent
            
            if total_fixed > 0:
                logger.info(f"Auto-fixed {total_fixed} emails with missing data")
            
            return {
                'status': 'processing_completed',
                'processed': received_result.get('processed', 0) + sent_result.get('processed', 0),
                'new': received_result.get('new', 0) + sent_result.get('new', 0),
                'fixed': total_fixed,
                'errors': received_result.get('errors', 0) + sent_result.get('errors', 0)
            }
            
        except Exception as e:
            logger.error(f"Email processing error: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'processed': 0,
                'new': 0,
                'errors': 1
            }
    
    def process_historical_emails(self, hours_back: int = 1440) -> Dict:
        """Process historical emails (default: last 60 days)"""
        try:
            # Check if already processing
            if hasattr(self, '_processing_active') and self._processing_active:
                return {'status': 'already_processing'}
            
            # Start background processing
            import threading
            
            def background_process():
                self._processing_active = True
                try:
                    # Process last 60 days for both received and sent
                    received_result = self.email_processor.process_new_emails(hours_back=hours_back)
                    sent_result = self.email_processor.process_sent_emails(hours_back=hours_back)
                    
                    logger.info(f"Historical processing completed: received={received_result}, sent={sent_result}")
                    
                except Exception as e:
                    logger.error(f"Historical email processing error: {e}")
                finally:
                    self._processing_active = False
            
            thread = threading.Thread(target=background_process)
            thread.start()
            
            return {'status': 'processing_started'}
            
        except Exception as e:
            logger.error(f"Error starting historical processing: {e}")
            return {'status': 'error', 'message': str(e)}