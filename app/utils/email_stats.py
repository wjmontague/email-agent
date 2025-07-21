import logging
from app.utils.cache import cached
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from app import db
from app.database_models import Email, ClassifiedEmail

logger = logging.getLogger(__name__)

class EmailStatsService:
    """Service class for email statistics and data operations"""

    @cached(ttl=60)  # Cache for 1 minute
    def get_dashboard_stats(self) -> Dict:
        """Get statistics for the main dashboard"""
        try:
            today = datetime.now().date()
            stats = {
                'total_today': Email.query.filter(Email.received_at >= today).count(),
                'unread': ClassifiedEmail.query.filter(ClassifiedEmail.is_read == False).count(),
                'critical': ClassifiedEmail.query.filter(
                    ClassifiedEmail.priority == 'Critical',
                    ClassifiedEmail.is_archived == False
                ).count(),
                'high': ClassifiedEmail.query.filter(
                    ClassifiedEmail.priority == 'High',
                    ClassifiedEmail.is_archived == False
                ).count()
            }
            return stats
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
            return {'total_today': 0, 'unread': 0, 'critical': 0, 'high': 0}

    @cached(ttl=120)  # Cache for 2 minutes
    def get_category_counts(self) -> Dict:
        """Get email counts by category"""
        try:
            categories = ['Critical Alerts', 'New Leads', 'Maintenance Requests',
                         'Offers & Contracts', 'Tenant Communications', 'General']

            category_counts = {}
            for category in categories:
                count = ClassifiedEmail.query.filter(
                    ClassifiedEmail.category == category,
                    ClassifiedEmail.is_archived == False
                ).count()
                category_counts[category] = count

            return category_counts
        except Exception as e:
            logger.error(f"Error getting category counts: {e}")
            return {}

    def check_email_gap(self) -> Dict:
        """Check if historical email processing is needed"""
        try:
            # Get the most recent email in database
            latest_email = Email.query.order_by(Email.received_at.desc()).first()

            if not latest_email:
                return {
                    'show_historical_button': True,
                    'message': 'No emails processed yet. Start with "Process Last 2 Months" to import your email history.'
                }

            # Check how old the latest email is
            now = datetime.now()
            time_diff = now - latest_email.received_at

            if time_diff.days >= 2:
                return {
                    'show_historical_button': True,
                    'message': f'Latest processed email is {time_diff.days} days old. Use "Process Last 2 Months" to catch up.'
                }

            return {
                'show_historical_button': False,
                'message': 'Email processing is current. Use "Process New Emails" for daily updates.'
            }

        except Exception as e:
            logger.error(f"Error checking email gap: {e}")
            return {
                'show_historical_button': True,
                'message': 'Unable to check email status. Historical processing available if needed.'
            }

    def get_category_emails(self, category_name: str) -> Tuple[List, Dict]:
        """Get emails and statistics for a specific category"""
        try:
            emails = db.session.query(ClassifiedEmail, Email).join(Email).filter(
                ClassifiedEmail.category == category_name,
                ClassifiedEmail.is_archived == False
            ).order_by(
                ClassifiedEmail.priority.desc(),
                Email.received_at.desc()
            ).all()

            total_count = len(emails)
            unread_count = sum(1 for classified, email in emails if not classified.is_read)

            priority_counts = {}
            for classified, email in emails:
                priority = classified.priority
                priority_counts[priority] = priority_counts.get(priority, 0) + 1

            category_stats = {
                'total': total_count,
                'unread': unread_count,
                'priority_counts': priority_counts
            }

            return emails, category_stats

        except Exception as e:
            logger.error(f"Error getting category emails: {e}")
            return [], {'total': 0, 'unread': 0, 'priority_counts': {}}

    def search_emails(self, query: str, category: str = '') -> List:
        """Search emails by query and optional category"""
        try:
            # Build search query
            search_query = db.session.query(ClassifiedEmail, Email).join(Email)

            # Text search in subject, body, and summary
            search_query = search_query.filter(
                db.or_(
                    Email.subject.contains(query),
                    Email.body_cleaned.contains(query),
                    ClassifiedEmail.summary.contains(query)
                )
            )

            # Category filter
            if category:
                search_query = search_query.filter(ClassifiedEmail.category == category)

            # Execute search
            results = search_query.order_by(Email.received_at.desc()).limit(50).all()
            return results

        except Exception as e:
            logger.error(f"Error searching emails: {e}")
            return []

    def get_reports_data(self) -> Dict:
        """Get data for reports page with enhanced volume statistics"""
        try:
            # Get email volume by day (last year for all time periods)
            one_year_ago = datetime.now() - timedelta(days=365)
            daily_volumes = db.session.query(
                db.func.date(Email.received_at).label('date'),
                db.func.count(Email.id).label('count')
            ).filter(Email.received_at >= one_year_ago).group_by(
                db.func.date(Email.received_at)
            ).order_by(db.func.date(Email.received_at)).all()

            # Calculate statistics for the default period (last 30 days)
            thirty_days_ago = datetime.now() - timedelta(days=30)
            recent_volumes = [v for v in daily_volumes
                            if datetime.strptime(str(v.date), '%Y-%m-%d') >= thirty_days_ago]

            # Calculate volume statistics
            total_emails = sum(v.count for v in recent_volumes) if recent_volumes else 0
            daily_average = total_emails // len(recent_volumes) if recent_volumes else 0
            peak_day = max(v.count for v in recent_volumes) if recent_volumes else 0
            active_days = len([v for v in recent_volumes if v.count > 0]) if recent_volumes else 0

            # Get category distribution
            category_stats = db.session.query(
                ClassifiedEmail.category,
                db.func.count(ClassifiedEmail.id).label('count')
            ).group_by(ClassifiedEmail.category).all()

            # Get priority distribution
            priority_stats = db.session.query(
                ClassifiedEmail.priority,
                db.func.count(ClassifiedEmail.id).label('count')
            ).group_by(ClassifiedEmail.priority).all()

            # Get email gap info
            email_gap_info = self.check_email_gap()

            return {
                'daily_volumes': daily_volumes,          # Now includes full year of data
                'total_emails': total_emails,            # NEW: Total emails in last 30 days
                'daily_average': daily_average,          # NEW: Daily average for last 30 days
                'peak_day': peak_day,                    # NEW: Peak day volume in last 30 days
                'active_days': active_days,              # NEW: Number of active days in last 30 days
                'is_demo_data': False,                   # NEW: Set to False for real data
                'category_stats': category_stats,
                'priority_stats': priority_stats,
                'email_gap': email_gap_info
            }

        except Exception as e:
            logger.error(f"Error getting reports data: {e}")
            return {
                'daily_volumes': [],
                'total_emails': 0,                       # NEW: Default values
                'daily_average': 0,                      # NEW: Default values
                'peak_day': 0,                           # NEW: Default values
                'active_days': 0,                        # NEW: Default values
                'is_demo_data': False,                   # NEW: Default values
                'category_stats': [],
                'priority_stats': [],
                'email_gap': {'show_historical_button': False, 'message': 'Error loading data'}
    }

    @cached(ttl=300)  # Cache for 5 minutes
    def get_client_list(self) -> List[Dict]:
        """Get list of all clients with conversation summaries"""
        try:
            clients = db.session.query(
                Email.sender_email,
                Email.sender_name,
                db.func.count(Email.id).label('email_count'),
                db.func.max(Email.received_at).label('last_contact'),
                db.func.sum(
                    db.case(
                        (ClassifiedEmail.is_read == False, 1),
                        else_=0
                    )
                ).label('unread_count'),
                db.func.sum(
                    db.case(
                        (db.and_(
                            Email.attachments != None,
                            Email.attachments != ''
                        ), 1),
                        else_=0
                    )
                ).label('attachment_count')
            ).join(ClassifiedEmail).filter(
                Email.is_sent == False
            ).group_by(
                Email.sender_email, Email.sender_name
            ).order_by(db.func.max(Email.received_at).desc()).all()

            client_data = []
            for sender_email, sender_name, email_count, last_contact, unread_count, attachment_count in clients:
                # Get most recent classification
                recent_classified = db.session.query(ClassifiedEmail).join(Email).filter(
                    Email.sender_email == sender_email,
                    Email.is_sent == False
                ).order_by(Email.received_at.desc()).first()

                client_data.append({
                    'email': sender_email,
                    'name': sender_name or sender_email.split('@')[0],
                    'email_count': email_count,
                    'last_contact': last_contact,
                    'unread_count': unread_count or 0,
                    'attachment_count': attachment_count or 0,
                    'primary_category': recent_classified.category if recent_classified else 'General',
                    'status': 'Active Lead' if recent_classified and recent_classified.category == 'New Leads' else 'Client'
                })

            return client_data

        except Exception as e:
            logger.error(f"Error getting client list: {e}")
            return []

    def get_client_conversation(self, client_email: str) -> Optional[Dict]:
        """Get conversation data for a specific client"""
        try:
            # Get all emails with this client
            emails = db.session.query(Email, ClassifiedEmail).join(
                ClassifiedEmail, Email.id == ClassifiedEmail.email_id
            ).filter(
                db.or_(
                    db.and_(Email.sender_email == client_email, Email.is_sent == False),
                    db.and_(Email.recipient_email == client_email, Email.is_sent == True)
                )
            ).order_by(Email.received_at.desc()).all()

            if not emails:
                return None

            # Get client info from most recent inbound email
            client_name = None
            latest_inbound = None

            for email, classified in emails:
                if not email.is_sent:
                    latest_inbound = (email, classified)
                    client_name = email.sender_name or client_email.split('@')[0]
                    break

            if not client_name:
                # If only sent emails, use recipient info
                for email, classified in emails:
                    if email.is_sent and email.recipient_email == client_email:
                        client_name = email.recipient_name or client_email.split('@')[0]
                        break

            if not client_name:
                client_name = client_email.split('@')[0]

            # Calculate stats
            total_emails = len(emails)
            unread_count = sum(1 for _, classified in emails if not classified.is_read)

            # Get date range
            oldest_date = emails[-1][0].received_at if emails else None
            newest_date = emails[0][0].received_at if emails else None

            # Calculate days since last contact
            days_since_contact = 0
            if newest_date:
                days_since_contact = (datetime.now() - newest_date.replace(tzinfo=None)).days

            # Categorize emails by type
            categories = {}
            for email, classified in emails:
                cat = classified.category
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append((email, classified))

            # Get properties mentioned
            properties_mentioned = set()
            for email, classified in emails:
                if classified.property_address:
                    properties_mentioned.add(classified.property_address)

            # Determine primary category and status
            primary_category = 'General'
            if latest_inbound:
                primary_category = latest_inbound[1].category

            client_stats = {
                'total_emails': total_emails,
                'unread_count': unread_count,
                'first_contact': oldest_date,
                'last_contact': newest_date,
                'days_since_contact': days_since_contact,
                'categories': categories,
                'properties_mentioned': list(properties_mentioned),
                'primary_category': primary_category,
                'status': 'Active Lead' if primary_category == 'New Leads' else 'Client'
            }

            return {
                'client_email': client_email,
                'client_name': client_name,
                'emails': emails,
                'client_stats': client_stats
            }

        except Exception as e:
            logger.error(f"Error getting client conversation: {e}")
            return None