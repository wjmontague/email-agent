#!/usr/bin/env python3
"""
Test Data Populator for Mike's Email Agent
Creates test emails and populates them into Gmail account for testing the sorting agent
"""

import os
import sys
import json
import base64
import random
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Add the parent directory to Python path to import from the main app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from the main email-agent app
from app.email_processing.gmail_client import GmailClient
from app.email_processor import EmailProcessor
from dotenv import load_dotenv

# Load environment variables from the main app
load_dotenv('/home/MikeAubry02025/email_agent/.env')

class EmailTestDataPopulator:
    """Populates Mike's Gmail with realistic test emails"""
    
    def __init__(self):
        self.gmail_client = GmailClient()
        self.target_email = "mikeaubry2025@gmail.com"
        
        # Email templates matching the web generator
        self.email_templates = {
            "tenant_inquiry": {
                "subjects": [
                    "Apartment viewing request for 123 Main St",
                    "Questions about the 2BR unit availability", 
                    "When can I schedule a showing?",
                    "Application status inquiry",
                    "Pet policy question for rental"
                ],
                "bodies": [
                    "Hi Mike,\n\nI saw your listing for the 2-bedroom apartment at 123 Main Street. I'm very interested and would like to schedule a viewing. I'm a working professional with excellent references. When would be a good time this week?\n\nBest regards,\n{name}",
                    "Hello,\n\nI submitted an application for the unit at {address} last week. Could you please update me on the status? I'm very excited about the possibility of renting from you.\n\nThanks,\n{name}",
                    "Hi Mike,\n\nI have a small dog (golden retriever, well-trained). I noticed your listing doesn't mention pets. Are they allowed with a deposit? The unit at {address} would be perfect for us.\n\nLooking forward to hearing from you,\n{name}"
                ]
            },
            "maintenance_request": {
                "subjects": [
                    "URGENT: Water leak in Unit 4B",
                    "AC not working - requesting repair",
                    "Garbage disposal stopped working",
                    "Bathroom light fixture needs replacement",
                    "Heating system making loud noises"
                ],
                "bodies": [
                    "Mike,\n\nI have a water leak under my kitchen sink that started this morning. It's getting worse and I'm concerned about water damage. Can you send someone out today?\n\nTenant: {name}\nUnit: 4B\nPhone: {phone}",
                    "Hello Mike,\n\nThe AC in my unit stopped working yesterday. With the heat wave coming, this is becoming urgent. The unit was working fine last week.\n\nUnit 2A\n{name}\n{phone}",
                    "Hi,\n\nMy garbage disposal isn't working and there's a strange smell coming from it. I've tried the reset button but nothing happened. Could you arrange for a repair?\n\nThanks,\n{name}\nUnit 3C"
                ]
            },
            "rent_payment": {
                "subjects": [
                    "Rent payment confirmation for March",
                    "Payment method change request",
                    "Late fee question",
                    "Rent payment processing issue",
                    "February rent receipt request"
                ],
                "bodies": [
                    "Hi Mike,\n\nI sent my rent payment for March via online transfer yesterday. Can you confirm you received it? The transaction ID is #TX789123.\n\nUnit 1A\n{name}",
                    "Hello,\n\nI'd like to change my rent payment method from check to automatic bank transfer. What information do you need from me?\n\nThanks,\n{name}\nUnit 2B",
                    "Mike,\n\nI see a late fee on my account but I'm sure I paid on time. My payment was submitted on the 1st. Can you please check?\n\n{name}\nUnit 3A"
                ]
            },
            "emergency": {
                "subjects": [
                    "EMERGENCY: Gas leak reported - Unit 1A",
                    "URGENT: Burst pipe flooding basement",
                    "EMERGENCY: Power outage affecting all units",
                    "URGENT: Break-in at 123 Main St",
                    "EMERGENCY: Tenant locked out - needs immediate help"
                ],
                "bodies": [
                    "MIKE - EMERGENCY\n\nTenant reports strong gas smell in Unit 1A. I've called the gas company and they're on their way. Building being evacuated.\n\nEmergency Response Team\nCall me immediately: {phone}",
                    "URGENT\n\nMike, we have a burst pipe in the basement flooding the entire lower level. Water is rising fast. Need emergency plumber NOW.\n\nMaintenance: {name}\n{phone}",
                    "EMERGENCY SITUATION\n\nTotal power outage at 123 Main St. Transformer blew. Electric company says 6-8 hours to restore. Tenants asking about hotel accommodation.\n\n{name}\nEmergency Contact"
                ]
            },
            "vendor_communication": {
                "subjects": [
                    "Plumbing service completion report",
                    "Landscaping schedule for next week",
                    "HVAC maintenance proposal",
                    "Cleaning service invoice",
                    "Electrical work estimate"
                ],
                "bodies": [
                    "Mike,\n\nCompleted the plumbing work at 123 Main St, Unit 2A. Replaced the kitchen faucet and fixed the leak. Invoice attached.\n\nJoe's Plumbing\nTotal: $285",
                    "Hi Mike,\n\nWeather looks good for next week. We'll handle the landscaping at all three properties Tuesday-Thursday.\n\nGreen Thumb Landscaping\n{name}",
                    "Hello Mike,\n\nHere's the estimate for HVAC maintenance on your 4-unit building. Annual service contract would save you 15%.\n\nABC Heating & Cooling\nEstimate: $1,200"
                ]
            },
            "legal_notice": {
                "subjects": [
                    "Legal notice - Tenant eviction process",
                    "City housing inspection notification",
                    "Zoning compliance reminder",
                    "Fire safety inspection required",
                    "ADA compliance update"
                ],
                "bodies": [
                    "Mr. Aubry,\n\nThis is formal notice regarding the eviction proceedings for Unit 3A. Court date is scheduled for March 15th.\n\nLegal Aid Society\nAttorney: {name}",
                    "Dear Property Owner,\n\nCity housing inspection is scheduled for your property at 123 Main St on March 20th at 10 AM.\n\nCity Housing Department\nInspector: {name}",
                    "Mike,\n\nReminder that all rental properties must comply with updated fire safety regulations by April 1st.\n\nFire Marshal Office\n{name}"
                ]
            },
            "lease_questions": {
                "subjects": [
                    "Lease renewal discussion",
                    "Guest policy clarification", 
                    "Early termination options",
                    "Subletting approval request",
                    "Lease modification request"
                ],
                "bodies": [
                    "Hi Mike,\n\nMy lease expires in June and I'd like to renew for another year. Can we discuss the terms and any potential rent changes?\n\n{name}\nUnit 1B",
                    "Hello,\n\nI have family visiting for 2 weeks next month. What's the guest policy for extended stays?\n\nThanks,\n{name}",
                    "Mike,\n\nI received a job offer in another state and may need to break my lease early. What options do I have?\n\n{name}\nUnit 4A"
                ]
            },
            "property_inquiry": {
                "subjects": [
                    "Investment property opportunity",
                    "Property valuation request", 
                    "Management services inquiry",
                    "Bulk property purchase interest",
                    "Property condition assessment"
                ],
                "bodies": [
                    "Mr. Aubry,\n\nI'm interested in purchasing a rental property in your area. Do you have any properties for sale or know of any good investment opportunities?\n\n{name}\nReal Estate Investor",
                    "Hello Mike,\n\nI own a 4-unit building and I'm considering hiring a property management company. What services do you offer and what are your rates?\n\nBest regards,\n{name}",
                    "Hi,\n\nI'm looking to expand my rental portfolio. Are you aware of any off-market properties that might be available?\n\n{name}\nInvestment Group"
                ]
            },
            "complaints": {
                "subjects": [
                    "Noise complaint from upstairs neighbor",
                    "Parking space dispute",
                    "Maintenance response time concern", 
                    "Neighbor's dog barking issue",
                    "Unsatisfactory cleaning service"
                ],
                "bodies": [
                    "Mike,\n\nI need to report that my upstairs neighbor has been extremely loud after 10 PM for the past week. I've tried talking to them but nothing has changed. This is affecting my sleep.\n\nUnit 1A\n{name}",
                    "Hello Mike,\n\nSomeone keeps parking in my assigned space (#5). I've left notes but it continues. Can you please address this?\n\nFrustrated tenant,\n{name}\nUnit 2C",
                    "Mike,\n\nI submitted a maintenance request 5 days ago and haven't heard back. My shower is still not working. This is unacceptable.\n\n{name}\nUnit 3B"
                ]
            },
            "inspection_report": {
                "subjects": [
                    "Monthly property inspection - 123 Main St",
                    "Move-out inspection report - Unit 2B",
                    "Safety inspection findings",
                    "Annual building inspection results", 
                    "Tenant damage assessment"
                ],
                "bodies": [
                    "Mike,\n\nCompleted monthly inspection of 123 Main St. Overall condition good. Minor issues noted:\n- Unit 1A: kitchen faucet dripping\n- Unit 3B: bedroom window needs caulking\n- Common area: light bulb out in hallway\n\nFull report attached.\n\nProperty Inspector: {name}",
                    "Hello Mike,\n\nMove-out inspection completed for Unit 2B. Tenant left property in excellent condition. No deductions from security deposit recommended.\n\nInspector: {name}",
                    "Mike,\n\nSafety inspection revealed two concerns:\n1. Smoke detector battery low in Unit 4A\n2. Emergency exit light not working\n\nBoth need immediate attention.\n\n{name}\nSafety Inspector"
                ]
            }
        }
        
        # Sample data
        self.names = ["Sarah Johnson", "Michael Chen", "Emily Davis", "Robert Wilson", 
                     "Jessica Martinez", "David Thompson", "Lisa Anderson", "James Brown"]
        self.addresses = ["123 Main St", "456 Oak Ave", "789 Pine Dr", "321 Elm St"]
        self.phones = ["(555) 123-4567", "(555) 987-6543", "(555) 456-7890", "(555) 321-9876"]
    
    def authenticate(self):
        """Authenticate with Gmail"""
        try:
            if self.gmail_client.authenticate_gmail():
                print("Gmail authentication successful")
                return True
            else:
                print("Gmail authentication failed")
                return False
        except Exception as e:
            print(f"Authentication error: {e}")
            return False
    
    def generate_test_email(self, category):
        """Generate a single test email for the given category"""
        template = self.email_templates.get(category)
        if not template:
            return None
            
        name = random.choice(self.names)
        address = random.choice(self.addresses)
        phone = random.choice(self.phones)
        
        subject = random.choice(template["subjects"])
        body = random.choice(template["bodies"]).format(
            name=name, address=address, phone=phone
        )
        
        # Generate appropriate sender email
        sender_email = self.get_sender_email(category, name)
        
        return {
            "sender": sender_email,
            "subject": subject,
            "body": body,
            "category": category
        }
    
    def get_sender_email(self, category, name):
        """Generate appropriate sender email based on category"""
        clean_name = name.lower().replace(" ", ".")
        
        if category == "legal_notice":
            return f"{clean_name}@cityhousing.gov"
        elif category == "vendor_communication":
            return f"{clean_name}@servicecompany.com"
        elif category == "emergency":
            return f"{clean_name}@emergency.com"
        else:
            return f"{clean_name}@email.com"
    
    def send_test_email(self, email_data):
        """Send a test email to Mike's Gmail account"""
        try:
            # Create the email message
            message = MIMEMultipart()
            message['To'] = self.target_email
            message['From'] = email_data["sender"]
            message['Subject'] = email_data["subject"]
            
            # Add body
            message.attach(MIMEText(email_data["body"], 'plain'))
            
            # Convert to base64 encoded string
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Send via Gmail API
            send_message = {
                'raw': raw_message
            }
            
            result = self.gmail_client.service.users().messages().send(
                userId='me', 
                body=send_message
            ).execute()
            
            print(f"Sent: {email_data['subject'][:50]}... (Category: {email_data['category']})")
            return result
            
        except Exception as e:
            print(f"Failed to send email: {e}")
            return None
    
    def populate_test_data(self, email_counts_by_category=None):
        """Populate Gmail with test emails"""
        
        # Default distribution if not specified
        if email_counts_by_category is None:
            email_counts_by_category = {
                "tenant_inquiry": 3,
                "maintenance_request": 4, 
                "rent_payment": 2,
                "emergency": 1,
                "vendor_communication": 3,
                "legal_notice": 1
            }
        
        if not self.authenticate():
            return False
        
        print(f"Starting test data population for {self.target_email}")
        
        total_sent = 0
        total_failed = 0
        
        for category, count in email_counts_by_category.items():
            print(f"Generating {count} emails for category: {category}")
            
            for i in range(count):
                email_data = self.generate_test_email(category)
                if email_data:
                    result = self.send_test_email(email_data)
                    if result:
                        total_sent += 1
                    else:
                        total_failed += 1
                else:
                    print(f"Failed to generate email for category: {category}")
                    total_failed += 1
        
        print(f"SUMMARY: Successfully sent: {total_sent} emails, Failed: {total_failed} emails")
        return total_sent > 0
    
    def trigger_email_processing(self):
        """Trigger the email processor to import the new emails"""
        try:
            print("Triggering email processing...")
            processor = EmailProcessor()
            
            if processor.authenticate_gmail():
                # Process new emails
                processor.process_emails()
                print("Email processing completed")
                return True
            else:
                print("Could not authenticate for email processing")
                return False
                
        except Exception as e:
            print(f"Error during email processing: {e}")
            return False

def main():
    """Main function to run the test data population"""
    print("Mike's Email Agent - Test Data Populator")
    
    populator = EmailTestDataPopulator()
    
    # Custom email distribution for testing
    test_distribution = {
        "tenant_inquiry": 5,
        "maintenance_request": 6,
        "rent_payment": 3, 
        "emergency": 2,
        "vendor_communication": 4,
        "legal_notice": 2
    }
    
    # Populate test data
    success = populator.populate_test_data(test_distribution)
    
    if success:
        print("Waiting 30 seconds before triggering email processing...")
        import time
        time.sleep(30)
        
        # Trigger processing of new emails
        populator.trigger_email_processing()
        
        print("Test data population complete!")
        print(f"Check Mike's dashboard at: https://mikeaubry02025.pythonanywhere.com/")
        print(f"Gmail account: {populator.target_email}")
    else:
        print("Test data population failed!")

if __name__ == "__main__":
    main()