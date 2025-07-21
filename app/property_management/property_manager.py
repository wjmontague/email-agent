# app/property_management/property_manager.py
import logging
from typing import Dict, List
from datetime import datetime
from ..database_models import db, Email, ClassifiedEmail, Property, MaintenanceRequest, FollowUpReminder

logger = logging.getLogger(__name__)

class PropertyManager:
    """Handles property-related email processing and management"""

    def link_email_to_property(self, email_id: int, classification: Dict) -> bool:
        """Link an email to a property and create maintenance request if needed"""
        try:
            property_address = classification.get('extracted_info', {}).get('property_address')
            if not property_address:
                return False

            # Find or create property
            property_obj = self._find_or_create_property(property_address, classification)

            # Update classification with property link
            self._update_classification_with_property(email_id, property_obj.address)

            # Create maintenance request if it's a maintenance email
            if classification.get('category') == 'Maintenance Requests':
                self._create_maintenance_request(email_id, property_obj.id, classification)

            db.session.commit()
            logger.info(f"Linked email {email_id} to property {property_obj.address}")
            return True

        except Exception as e:
            logger.error(f"Error linking email to property: {e}")
            db.session.rollback()
            return False

    def _find_or_create_property(self, property_address: str, classification: Dict) -> Property:
        """Find existing property or create new one"""
        # Try to find existing property
        property_obj = Property.query.filter(
            Property.address.contains(property_address)
        ).first()

        if not property_obj:
            # Create new property entry
            property_obj = Property(
                address=property_address,
                property_type=classification.get('extracted_info', {}).get('property_type'),
                status='active'
            )
            db.session.add(property_obj)
            db.session.flush()
            logger.info(f"Created new property: {property_address}")

        return property_obj

    def _update_classification_with_property(self, email_id: int, property_address: str):
        """Update email classification with property information"""
        classified_email = ClassifiedEmail.query.filter_by(email_id=email_id).first()
        if classified_email:
            classified_email.property_address = property_address

    def _create_maintenance_request(self, email_id: int, property_id: int, classification: Dict):
        """Create maintenance request for maintenance emails"""
        email = Email.query.get(email_id)
        if not email:
            return

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
        logger.info(f"Created maintenance request for email {email_id}")

    def create_follow_up_reminder(self, email_id: int, days_ahead: int = 3,
                                 reminder_type: str = 'general') -> bool:
        """Create a follow-up reminder for an email"""
        try:
            from datetime import timedelta
            reminder_date = datetime.now() + timedelta(days=days_ahead)

            # Get email for context
            email = Email.query.get(email_id)
            if not email:
                return False

            classified = ClassifiedEmail.query.filter_by(email_id=email_id).first()

            # Customize message based on category and type
            message = self._generate_reminder_message(email, classified, reminder_type)

            # Create reminder
            reminder = FollowUpReminder(
                email_id=email_id,
                reminder_date=reminder_date,
                reminder_type=reminder_type,
                message=message
            )

            db.session.add(reminder)
            db.session.commit()

            logger.info(f"Created follow-up reminder for email {email_id} on {reminder_date}")
            return True

        except Exception as e:
            logger.error(f"Error creating follow-up reminder: {e}")
            db.session.rollback()
            return False

    def _generate_reminder_message(self, email: Email, classified: ClassifiedEmail,
                                  reminder_type: str) -> str:
        """Generate appropriate reminder message based on email category"""
        if classified and classified.category == 'New Leads':
            return f"Follow up on lead from {email.sender_name} regarding: {email.subject}"
        elif classified and classified.category == 'Maintenance Requests':
            return f"Check maintenance status with {email.sender_name}: {email.subject}"
        else:
            return f"Follow up on email from {email.sender_name}: {email.subject}"

    def get_due_reminders(self) -> List[Dict]:
        """Get all reminders that are due"""
        try:
            due_reminders = FollowUpReminder.query.filter(
                FollowUpReminder.reminder_date <= datetime.now(),
                FollowUpReminder.is_completed == False
            ).join(Email).all()

            reminders_list = []
            for reminder in due_reminders:
                reminders_list.append({
                    'id': reminder.id,
                    'email_id': reminder.email_id,
                    'message': reminder.message,
                    'reminder_type': reminder.reminder_type,
                    'due_date': reminder.reminder_date,
                    'email_subject': reminder.email.subject,
                    'email_sender': reminder.email.sender_name,
                    'days_overdue': (datetime.now() - reminder.reminder_date).days
                })

            return reminders_list

        except Exception as e:
            logger.error(f"Error getting due reminders: {e}")
            return []

    def get_property_dashboard(self) -> Dict:
        """Get property management dashboard data"""
        try:
            properties = Property.query.all()

            dashboard_data = {
                'total_properties': len(properties),
                'active_leases': Property.query.filter(
                    Property.lease_end >= datetime.now().date()
                ).count(),
                'maintenance_open': MaintenanceRequest.query.filter(
                    MaintenanceRequest.status == 'Open'
                ).count(),
                'maintenance_critical': MaintenanceRequest.query.filter(
                    MaintenanceRequest.status == 'Open',
                    MaintenanceRequest.priority == 'Critical'
                ).count(),
                'properties': []
            }

            for prop in properties:
                prop_data = {
                    'id': prop.id,
                    'address': prop.address,
                    'type': prop.property_type,
                    'status': prop.status,
                    'tenant': prop.current_tenant_name,
                    'lease_expires': prop.lease_end.isoformat() if prop.lease_end else None,
                    'open_maintenance': prop.maintenance_requests.filter_by(status='Open').count(),
                    'email_count': prop.email_count
                }
                dashboard_data['properties'].append(prop_data)

            return dashboard_data

        except Exception as e:
            logger.error(f"Error getting property dashboard: {e}")
            return {'error': str(e)}

    def update_maintenance_request(self, request_id: int, status: str = None,
                                  assigned_vendor: str = None, notes: str = None) -> bool:
        """Update maintenance request status and details"""
        try:
            maintenance_request = MaintenanceRequest.query.get(request_id)
            if not maintenance_request:
                return False

            if status:
                maintenance_request.status = status
                if status == 'Completed':
                    maintenance_request.completed_date = datetime.now()

            if assigned_vendor:
                maintenance_request.assigned_vendor = assigned_vendor

            if notes:
                # Add notes to description
                maintenance_request.description += f"\n\nUpdate: {notes}"

            maintenance_request.updated_at = datetime.now()
            db.session.commit()

            logger.info(f"Updated maintenance request {request_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating maintenance request: {e}")
            db.session.rollback()
            return False

    def get_property_maintenance_history(self, property_id: int) -> List[Dict]:
        """Get maintenance history for a property"""
        try:
            requests = MaintenanceRequest.query.filter_by(
                property_id=property_id
            ).order_by(MaintenanceRequest.reported_date.desc()).all()

            history = []
            for request in requests:
                history.append({
                    'id': request.id,
                    'title': request.title,
                    'description': request.description,
                    'status': request.status,
                    'priority': request.priority,
                    'reported_date': request.reported_date.isoformat() if request.reported_date else None,
                    'completed_date': request.completed_date.isoformat() if request.completed_date else None,
                    'tenant_name': request.tenant_name,
                    'assigned_vendor': request.assigned_vendor
                })
            return history
        except Exception as e:
            logger.error(f"Error getting maintenance history: {e}")
            return []