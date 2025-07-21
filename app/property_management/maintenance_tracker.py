# app/property_management/maintenance_tracker.py
import logging
from typing import Dict, List, Optional
from datetime import datetime
from ..database_models import db, MaintenanceRequest, Property, Email

logger = logging.getLogger(__name__)

class MaintenanceTracker:
    """Handles maintenance request tracking and management"""

    def create_maintenance_request(self, email_id: int, property_id: int,
                                 classification: Dict) -> Optional[MaintenanceRequest]:
        """Create a new maintenance request from an email"""
        try:
            email = Email.query.get(email_id)
            if not email:
                logger.error(f"Email {email_id} not found")
                return None

            maintenance_request = MaintenanceRequest(
                property_id=property_id,
                email_id=email_id,
                title=email.subject,
                description=email.body_cleaned[:500],
                priority=classification.get('priority', 'Medium'),
                tenant_name=email.sender_name,
                tenant_email=email.sender_email,
                status='Open'
            )

            db.session.add(maintenance_request)
            db.session.commit()

            logger.info(f"Created maintenance request {maintenance_request.id} for email {email_id}")
            return maintenance_request

        except Exception as e:
            logger.error(f"Error creating maintenance request: {e}")
            db.session.rollback()
            return None

    def update_maintenance_status(self, request_id: int, status: str,
                                notes: str = None) -> bool:
        """Update maintenance request status"""
        try:
            request = MaintenanceRequest.query.get(request_id)
            if not request:
                return False

            request.status = status
            request.updated_at = datetime.now()

            if status == 'Completed':
                request.completed_date = datetime.now()

            if notes:
                request.description += f"\n\nUpdate ({datetime.now().strftime('%Y-%m-%d')}): {notes}"

            db.session.commit()
            logger.info(f"Updated maintenance request {request_id} status to {status}")
            return True

        except Exception as e:
            logger.error(f"Error updating maintenance request: {e}")
            db.session.rollback()
            return False

    def assign_vendor(self, request_id: int, vendor_name: str,
                     vendor_contact: str = None) -> bool:
        """Assign vendor to maintenance request"""
        try:
            request = MaintenanceRequest.query.get(request_id)
            if not request:
                return False

            request.assigned_vendor = vendor_name
            if vendor_contact:
                request.vendor_contact = vendor_contact
            request.status = 'In Progress'
            request.updated_at = datetime.now()

            db.session.commit()
            logger.info(f"Assigned vendor {vendor_name} to maintenance request {request_id}")
            return True

        except Exception as e:
            logger.error(f"Error assigning vendor: {e}")
            db.session.rollback()
            return False

    def get_open_requests(self) -> List[MaintenanceRequest]:
        """Get all open maintenance requests"""
        return MaintenanceRequest.query.filter_by(status='Open').all()

    def get_critical_requests(self) -> List[MaintenanceRequest]:
        """Get all critical maintenance requests"""
        return MaintenanceRequest.query.filter_by(
            priority='Critical',
            status='Open'
        ).all()

    def get_requests_by_property(self, property_id: int) -> List[MaintenanceRequest]:
        """Get maintenance requests for a specific property"""
        return MaintenanceRequest.query.filter_by(
            property_id=property_id
        ).order_by(MaintenanceRequest.reported_date.desc()).all()

    def get_maintenance_stats(self) -> Dict:
        """Get maintenance statistics"""
        try:
            total_requests = MaintenanceRequest.query.count()
            open_requests = MaintenanceRequest.query.filter_by(status='Open').count()
            critical_requests = MaintenanceRequest.query.filter_by(
                status='Open',
                priority='Critical'
            ).count()
            completed_requests = MaintenanceRequest.query.filter_by(
                status='Completed'
            ).count()

            return {
                'total': total_requests,
                'open': open_requests,
                'critical': critical_requests,
                'completed': completed_requests,
                'completion_rate': (completed_requests / total_requests * 100) if total_requests > 0 else 0
            }

        except Exception as e:
            logger.error(f"Error getting maintenance stats: {e}")
            return {
                'total': 0,
                'open': 0,
                'critical': 0,
                'completed': 0,
                'completion_rate': 0
            }