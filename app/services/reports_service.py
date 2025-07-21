"""
Enhanced Reports Service
Provides real data for reports and analytics
"""

from datetime import datetime, timedelta
from typing import Dict, List
from app.database_models import Email, ClassifiedEmail, db
import logging

logger = logging.getLogger(__name__)

class ReportsService:
    """Enhanced reports service with real data"""
    
    def get_reports_data(self) -> Dict:
        """Get comprehensive reports data"""
        try:
            # Get email volume by day (last year for comprehensive data)
            one_year_ago = datetime.now() - timedelta(days=365)
            daily_volumes = db.session.query(
                db.func.date(Email.received_at).label('date'),
                db.func.count(Email.id).label('count')
            ).filter(
                Email.received_at >= one_year_ago
            ).group_by(
                db.func.date(Email.received_at)
            ).order_by(
                db.func.date(Email.received_at)
            ).all()
            
            # Calculate statistics for last 30 days
            thirty_days_ago = datetime.now() - timedelta(days=30)
            recent_volumes = [v for v in daily_volumes
                            if datetime.strptime(str(v.date), '%Y-%m-%d') >= thirty_days_ago]
            
            total_emails = sum(v.count for v in recent_volumes) if recent_volumes else 0
            daily_average = total_emails // len(recent_volumes) if recent_volumes else 0
            peak_day = max(v.count for v in recent_volumes) if recent_volumes else 0
            active_days = len([v for v in recent_volumes if v.count > 0])
            
            # Get category and priority stats
            category_stats = db.session.query(
                ClassifiedEmail.category,
                db.func.count(ClassifiedEmail.id).label('count')
            ).group_by(ClassifiedEmail.category).all()
            
            priority_stats = db.session.query(
                ClassifiedEmail.priority,
                db.func.count(ClassifiedEmail.id).label('count')
            ).group_by(ClassifiedEmail.priority).all()
            
            return {
                'daily_volumes': daily_volumes,
                'total_emails': total_emails,
                'daily_average': daily_average,
                'peak_day': peak_day,
                'active_days': active_days,
                'is_demo_data': False,  # Always False for real data
                'category_stats': category_stats,
                'priority_stats': priority_stats,
                'email_gap': self.check_email_gap()
            }
            
        except Exception as e:
            logger.error(f"Error getting reports data: {e}")
            return {
                'daily_volumes': [],
                'total_emails': 0,
                'daily_average': 0,
                'peak_day': 0,
                'active_days': 0,
                'is_demo_data': False,
                'category_stats': [],
                'priority_stats': [],
                'email_gap': {'show_historical_button': True, 'message': 'Error loading data'}
            }
    
    def check_email_gap(self) -> Dict:
        """Check if there's a gap in email processing"""
        try:
            latest_email = Email.query.order_by(Email.received_at.desc()).first()
            
            if not latest_email:
                return {
                    'show_historical_button': True,
                    'message': 'No emails found. Use "Process Last 2 Months" to get started.'
                }
            
            hours_since_latest = (datetime.now() - latest_email.received_at).total_seconds() / 3600
            
            if hours_since_latest > 48:
                return {
                    'show_historical_button': True,
                    'message': f'Latest email is {int(hours_since_latest)} hours old. Use "Process Last 2 Months" to catch up.'
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
