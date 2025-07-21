# app/init_db.py
from flask import Flask
from database_models import db, EmailCategories
import os

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(os.path.dirname(__file__), "email_agent.db")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    return app

def initialize_database():
    """Create tables and populate with default data"""
    app = create_app()

    with app.app_context():
        # Create all tables
        db.create_all()

        # Default email categories
        default_categories = [
            {
                'name': 'Critical Alerts',
                'description': 'Emergency situations requiring immediate attention',
                'keywords': ['urgent', 'emergency', 'asap', 'immediate', 'critical', 'fire', 'flood', 'break in', 'broken pipe'],
                'priority_default': 'Critical'
            },
            {
                'name': 'New Leads',
                'description': 'Potential clients and property inquiries',
                'keywords': ['interested in', 'looking for', 'want to buy', 'want to sell', 'property inquiry', 'showing request'],
                'priority_default': 'High'
            },
            {
                'name': 'Maintenance Requests',
                'description': 'Property maintenance and repair requests',
                'keywords': ['repair', 'broken', 'not working', 'maintenance', 'fix', 'leak', 'heating', 'air conditioning'],
                'priority_default': 'High'
            },
            {
                'name': 'Offers & Contracts',
                'description': 'Purchase offers, contracts, and legal documents',
                'keywords': ['offer', 'contract', 'purchase agreement', 'counteroffer', 'acceptance', 'escrow'],
                'priority_default': 'Critical'
            },
            {
                'name': 'Tenant Communications',
                'description': 'Communications with current tenants',
                'keywords': ['tenant', 'rent', 'lease', 'rental', 'renter', 'move in', 'move out', 'deposit'],
                'priority_default': 'Medium'
            },
            {
                'name': 'Vendor Communications',
                'description': 'Communications with contractors and service providers',
                'keywords': ['contractor', 'vendor', 'supplier', 'invoice', 'estimate', 'quote', 'service'],
                'priority_default': 'Medium'
            },
            {
                'name': 'Legal & Compliance',
                'description': 'Legal matters and regulatory compliance',
                'keywords': ['legal', 'attorney', 'lawyer', 'court', 'lawsuit', 'compliance', 'violation', 'notice'],
                'priority_default': 'High'
            },
            {
                'name': 'Marketing & Listings',
                'description': 'Property marketing and listing management',
                'keywords': ['listing', 'mls', 'marketing', 'photos', 'virtual tour', 'open house', 'showing'],
                'priority_default': 'Medium'
            },
            {
                'name': 'Financial',
                'description': 'Financial transactions and accounting',
                'keywords': ['commission', 'payment', 'invoice', 'receipt', 'transaction', 'closing', 'settlement'],
                'priority_default': 'Medium'
            },
            {
                'name': 'General',
                'description': 'General correspondence and uncategorized emails',
                'keywords': [],
                'priority_default': 'Low'
            }
        ]

        # Add categories if they don't exist
        for category_data in default_categories:
            existing = EmailCategories.query.filter_by(name=category_data['name']).first()
            if not existing:
                category = EmailCategories(
                    name=category_data['name'],
                    description=category_data['description'],
                    priority_default=category_data['priority_default']
                )
                category.set_keywords(category_data['keywords'])
                db.session.add(category)

        db.session.commit()
        print("Database initialized successfully!")

if __name__ == '__main__':
    initialize_database()
