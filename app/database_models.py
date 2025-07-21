# app/database_models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

from app import db
import json

class Email(db.Model):
    """Raw email storage"""
    __tablename__ = 'emails'

    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    thread_id = db.Column(db.String(255), index=True)
    received_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    sender_name = db.Column(db.String(255))
    sender_email = db.Column(db.String(255), nullable=False, index=True)
    recipient_email = db.Column(db.String(255))
    recipient_name = db.Column(db.String(255))
    is_sent = db.Column(db.Boolean, default=False, index=True)
    subject = db.Column(db.Text)
    body_raw = db.Column(db.Text)
    body_cleaned = db.Column(db.Text)
    attachments = db.Column(db.Text)  # JSON string of attachment info
    labels = db.Column(db.Text)  # Gmail labels as JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    classified = db.relationship('ClassifiedEmail', backref='email', uselist=False, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Email {self.message_id}: {self.subject}>'

    def get_attachments(self):
        """Get attachments as list"""
        if self.attachments:
            try:
                return json.loads(self.attachments)
            except:
                return []
        return []

    def set_attachments(self, attachments_list):
        """Set attachments from list"""
        self.attachments = json.dumps(attachments_list) if attachments_list else None

class ClassifiedEmail(db.Model):
    """AI-classified email data"""
    __tablename__ = 'classified_emails'

    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.Integer, db.ForeignKey('emails.id'), nullable=False, unique=True)

    # Classification results
    category = db.Column(db.String(100), nullable=False, index=True)
    sub_category = db.Column(db.String(100), index=True)
    priority = db.Column(db.String(20), nullable=False, default='Medium', index=True)
    confidence_score = db.Column(db.Float)

    # AI-generated content
    summary = db.Column(db.Text)
    extracted_info = db.Column(db.Text)  # JSON string of key-value pairs
    tags = db.Column(db.Text)  # JSON array of tags

    # Property information (if applicable)
    property_address = db.Column(db.String(500), index=True)
    property_type = db.Column(db.String(50))

    # Contact information (if applicable)
    contact_name = db.Column(db.String(255))
    contact_phone = db.Column(db.String(50))
    contact_email = db.Column(db.String(255))

    # Status tracking
    is_read = db.Column(db.Boolean, default=False, index=True)
    is_archived = db.Column(db.Boolean, default=False, index=True)
    is_important = db.Column(db.Boolean, default=False, index=True)
    requires_action = db.Column(db.Boolean, default=False, index=True)
    action_due_date = db.Column(db.DateTime)

    # Metadata
    processed_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<ClassifiedEmail {self.email_id}: {self.category}>'

    def get_extracted_info(self):
        """Get extracted info as dictionary"""
        if self.extracted_info:
            try:
                return json.loads(self.extracted_info)
            except:
                return {}
        return {}

    def set_extracted_info(self, info_dict):
        """Set extracted info from dictionary"""
        self.extracted_info = json.dumps(info_dict) if info_dict else None

    def get_tags(self):
        """Get tags as list"""
        if self.tags:
            try:
                return json.loads(self.tags)
            except:
                return []
        return []

    def set_tags(self, tags_list):
        """Set tags from list"""
        self.tags = json.dumps(tags_list) if tags_list else None

    @property
    def priority_color(self):
        """Get CSS color class for priority"""
        colors = {
            'Critical': 'text-danger',
            'High': 'text-warning',
            'Medium': 'text-info',
            'Low': 'text-secondary'
        }
        return colors.get(self.priority, 'text-secondary')

    @property
    def priority_badge(self):
        """Get Bootstrap badge class for priority"""
        badges = {
            'Critical': 'badge-danger',
            'High': 'badge-warning',
            'Medium': 'badge-info',
            'Low': 'badge-secondary'
        }
        return badges.get(self.priority, 'badge-secondary')

class ProcessingLog(db.Model):
    """Log of email processing runs"""
    __tablename__ = 'processing_logs'

    id = db.Column(db.Integer, primary_key=True)
    started_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    status = db.Column(db.String(50), default='running')  # running, completed, failed
    emails_processed = db.Column(db.Integer, default=0)
    emails_new = db.Column(db.Integer, default=0)
    errors = db.Column(db.Text)  # JSON array of error messages

    def __repr__(self):
        return f'<ProcessingLog {self.started_at}: {self.status}>'

    def get_errors(self):
        """Get errors as list"""
        if self.errors:
            try:
                return json.loads(self.errors)
            except:
                return []
        return []

    def add_error(self, error_msg):
        """Add error message"""
        errors = self.get_errors()
        errors.append(str(error_msg))
        self.errors = json.dumps(errors)

class EmailCategories(db.Model):
    """Configurable email categories"""
    __tablename__ = 'email_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    keywords = db.Column(db.Text)  # JSON array of keywords
    priority_default = db.Column(db.String(20), default='Medium')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_keywords(self):
        """Get keywords as list"""
        if self.keywords:
            try:
                return json.loads(self.keywords)
            except:
                return []
        return []

    def set_keywords(self, keywords_list):
        """Set keywords from list"""
        self.keywords = json.dumps(keywords_list) if keywords_list else None

class FollowUpReminder(db.Model):
    """Follow-up reminders for emails and clients"""
    __tablename__ = 'follow_up_reminders'

    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.Integer, db.ForeignKey('emails.id'), nullable=False)
    reminder_date = db.Column(db.DateTime, nullable=False, index=True)
    reminder_type = db.Column(db.String(50), default='general')  # general, lead_followup, maintenance_check
    message = db.Column(db.Text)
    is_completed = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

    # Relationship
    email = db.relationship('Email', backref='follow_up_reminders')

    def mark_completed(self):
        """Mark reminder as completed"""
        self.is_completed = True
        self.completed_at = datetime.utcnow()

class Property(db.Model):
    """Property information and tracking"""
    __tablename__ = 'properties'

    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(500), nullable=False, unique=True, index=True)
    property_type = db.Column(db.String(50))  # house, condo, apartment, commercial
    status = db.Column(db.String(50), default='active')  # active, sold, rented, maintenance
    bedrooms = db.Column(db.Integer)
    bathrooms = db.Column(db.Float)
    square_feet = db.Column(db.Integer)
    rent_amount = db.Column(db.Float)
    purchase_price = db.Column(db.Float)

    # Current tenant info
    current_tenant_name = db.Column(db.String(255))
    current_tenant_email = db.Column(db.String(255))
    lease_start = db.Column(db.Date)
    lease_end = db.Column(db.Date)

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    maintenance_requests = db.relationship('MaintenanceRequest', backref='property', lazy='dynamic')

    def __repr__(self):
        return f'<Property {self.address}>'

    @property
    def email_count(self):
        """Count of emails related to this property"""
        return ClassifiedEmail.query.filter(
            ClassifiedEmail.property_address.contains(self.address)
        ).count()

class EmailDraft(db.Model):
    """Email drafts storage"""
    __tablename__ = 'email_drafts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False, index=True)  # Username or user identifier
    draft_type = db.Column(db.String(20), nullable=False, default='compose')  # 'compose', 'reply', 'forward'

    # Email content
    to_email = db.Column(db.Text)
    cc_emails = db.Column(db.Text)
    bcc_emails = db.Column(db.Text)
    subject = db.Column(db.Text)
    message_body = db.Column(db.Text)

    # Reply/Forward specific
    original_email_id = db.Column(db.Integer, db.ForeignKey('emails.id'), nullable=True)
    reply_type = db.Column(db.String(20))  # 'reply', 'replyAll', 'forward'

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    original_email = db.relationship('Email', backref='drafts')

    def __repr__(self):
        return f'<EmailDraft {self.id}: {self.subject[:50]}>'

    def to_dict(self):
        """Convert draft to dictionary"""
        return {
            'id': self.id,
            'draft_type': self.draft_type,
            'to_email': self.to_email,
            'cc_emails': self.cc_emails,
            'bcc_emails': self.bcc_emails,
            'subject': self.subject,
            'message_body': self.message_body,
            'original_email_id': self.original_email_id,
            'reply_type': self.reply_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'preview': self.message_body[:100] + '...' if self.message_body and len(self.message_body) > 100 else self.message_body
        }

class MaintenanceRequest(db.Model):
    """Maintenance requests linked to properties"""
    __tablename__ = 'maintenance_requests'

    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    email_id = db.Column(db.Integer, db.ForeignKey('emails.id'))

    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    priority = db.Column(db.String(20), default='Medium')  # Critical, High, Medium, Low
    status = db.Column(db.String(50), default='Open')  # Open, In Progress, Completed, Cancelled

    # People involved
    tenant_name = db.Column(db.String(255))
    tenant_email = db.Column(db.String(255))
    assigned_vendor = db.Column(db.String(255))
    vendor_contact = db.Column(db.String(255))

    # Dates and costs
    reported_date = db.Column(db.DateTime, default=datetime.utcnow)
    scheduled_date = db.Column(db.DateTime)
    completed_date = db.Column(db.DateTime)
    estimated_cost = db.Column(db.Float)
    actual_cost = db.Column(db.Float)

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<MaintenanceRequest {self.title}: {self.status}>'