import threading
import time
import logging
from app.services.processing_service import ProcessingService

logger = logging.getLogger(__name__)

class BackgroundService:
    """Service class for background email processing"""
    
    def __init__(self):
        self.processing_service = ProcessingService()
        self.running = False
    
    def start(self):
        """Start background email processing every 30 minutes"""
        if self.running:
            return
        
        self.running = True
        thread = threading.Thread(target=self._process_loop, daemon=True)
        thread.start()
        logger.info("Background email processing started")
    
    def stop(self):
        """Stop background processing"""
        self.running = False
        logger.info("Background email processing stopped")
    
    def _process_loop(self):
        """Main processing loop"""
        while self.running:
            try:
                logger.info("Starting scheduled email processing...")
                
                result = self.processing_service.process_new_emails()
                
                if result['status'] == 'processing_completed':
                    logger.info(f"Scheduled processing completed: {result}")
                else:
                    logger.warning(f"Scheduled processing had issues: {result}")
                
                # Sleep for 30 minutes
                time.sleep(1800)
                
            except Exception as e:
                logger.error(f"Background processing error: {e}")
                time.sleep(300)  # Wait 5 minutes on error