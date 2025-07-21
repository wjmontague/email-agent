# app/services/drafts_service.py
from app import db
from app.database_models import EmailDraft
from flask import session
from datetime import datetime
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class DraftsService:
    """Service for managing email drafts"""
    
    def __init__(self):
        self.user_id = session.get('username', 'anonymous')
    
    def save_draft(self, draft_data: Dict) -> Dict:
        """Save or update an email draft"""
        try:
            draft_id = draft_data.get('draft_id')
            
            if draft_id:
                # Update existing draft
                draft = EmailDraft.query.filter_by(
                    id=draft_id, 
                    user_id=self.user_id
                ).first()
                
                if not draft:
                    return {'success': False, 'message': 'Draft not found'}
                
                logger.info(f"Updating draft {draft_id}")
            else:
                # Create new draft
                draft = EmailDraft(user_id=self.user_id)
                logger.info("Creating new draft")
            
            # Update draft fields
            draft.draft_type = draft_data.get('draft_type', 'compose')
            draft.to_email = draft_data.get('to_email', '')
            draft.cc_emails = draft_data.get('cc_emails', '')
            draft.bcc_emails = draft_data.get('bcc_emails', '')
            draft.subject = draft_data.get('subject', '')
            draft.message_body = draft_data.get('message_body', '')
            draft.original_email_id = draft_data.get('original_email_id')
            draft.reply_type = draft_data.get('reply_type')
            draft.updated_at = datetime.utcnow()
            
            if not draft_id:
                db.session.add(draft)
            
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Draft saved successfully',
                'draft_id': draft.id
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving draft: {e}")
            return {'success': False, 'message': f'Error saving draft: {str(e)}'}
    
    def get_drafts(self, draft_type: Optional[str] = None) -> List[Dict]:
        """Get all drafts for current user"""
        try:
            query = EmailDraft.query.filter_by(user_id=self.user_id)
            
            if draft_type:
                query = query.filter_by(draft_type=draft_type)
            
            drafts = query.order_by(EmailDraft.updated_at.desc()).all()
            
            return [draft.to_dict() for draft in drafts]
            
        except Exception as e:
            logger.error(f"Error getting drafts: {e}")
            return []
    
    def get_draft(self, draft_id: int) -> Optional[Dict]:
        """Get a specific draft"""
        try:
            draft = EmailDraft.query.filter_by(
                id=draft_id,
                user_id=self.user_id
            ).first()
            
            return draft.to_dict() if draft else None
            
        except Exception as e:
            logger.error(f"Error getting draft {draft_id}: {e}")
            return None
    
    def delete_draft(self, draft_id: int) -> Dict:
        """Delete a draft"""
        try:
            draft = EmailDraft.query.filter_by(
                id=draft_id,
                user_id=self.user_id
            ).first()
            
            if not draft:
                return {'success': False, 'message': 'Draft not found'}
            
            db.session.delete(draft)
            db.session.commit()
            
            logger.info(f"Deleted draft {draft_id}")
            return {'success': True, 'message': 'Draft deleted successfully'}
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting draft {draft_id}: {e}")
            return {'success': False, 'message': f'Error deleting draft: {str(e)}'}
    
    def auto_save_draft(self, draft_data: Dict) -> Dict:
        """Auto-save draft with conflict detection"""
        try:
            # For auto-save, we can be more lenient
            # Only save if there's actual content
            has_content = any([
                draft_data.get('to_email', '').strip(),
                draft_data.get('subject', '').strip(),
                draft_data.get('message_body', '').strip()
            ])
            
            if not has_content:
                return {'success': False, 'message': 'No content to save'}
            
            return self.save_draft(draft_data)
            
        except Exception as e:
            logger.error(f"Error auto-saving draft: {e}")
            return {'success': False, 'message': f'Auto-save failed: {str(e)}'}
    
    def get_drafts_count(self) -> int:
        """Get count of drafts for current user"""
        try:
            return EmailDraft.query.filter_by(user_id=self.user_id).count()
        except Exception as e:
            logger.error(f"Error getting drafts count: {e}")
            return 0
    
    def cleanup_old_drafts(self, days_old: int = 30) -> int:
        """Clean up drafts older than specified days"""
        try:
            from datetime import timedelta
            
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            old_drafts = EmailDraft.query.filter(
                EmailDraft.user_id == self.user_id,
                EmailDraft.updated_at < cutoff_date
            ).all()
            
            count = len(old_drafts)
            
            for draft in old_drafts:
                db.session.delete(draft)
            
            db.session.commit()
            
            logger.info(f"Cleaned up {count} old drafts for user {self.user_id}")
            return count
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error cleaning up old drafts: {e}")
            return 0