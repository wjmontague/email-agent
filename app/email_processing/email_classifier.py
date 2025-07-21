# app/email_processing/email_classifier.py - FIXED VERSION
import os
import json
import logging
from typing import Dict, List
import openai

logger = logging.getLogger(__name__)

class EmailClassifier:
    """Handles AI-powered email classification and information extraction"""
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
    
    def classify_email(self, email_data: Dict) -> Dict:
        """Use AI to classify and extract information from email with improved critical detection"""
        try:
            # For sent emails, use simpler classification
            if email_data.get('is_sent', False):
                return self._classify_sent_email(email_data)
            
            # For received emails, use full AI classification
            return self._classify_received_email(email_data)
            
        except Exception as e:
            logger.error(f"AI classification error: {e}")
            return self._get_fallback_classification()
    
    def _classify_sent_email(self, email_data: Dict) -> Dict:
        """Simple classification for sent emails"""
        return {
            'category': 'General',
            'sub_category': 'Sent Email',
            'priority': 'Medium',
            'summary': f"Sent email to {email_data.get('recipient_name', 'Unknown')}",
            'extracted_info': {
                'contact_name': email_data.get('recipient_name', ''),
                'contact_email': email_data.get('recipient_email', ''),
            },
            'requires_action': False,
            'confidence_score': 1.0,
            'tags': ['sent', 'outbound']
        }
    
    def _classify_received_email(self, email_data: Dict) -> Dict:
        """Full AI classification for received emails"""
        # Calculate urgency score first
        subject = email_data.get('subject', '')
        body = email_data.get('body_cleaned', '')
        urgency_score = self._calculate_urgency_score(subject, body)
        
        # Check for attachments
        attachments = email_data.get('attachments', [])
        attachment_info = ""
        if attachments:
            attachment_info = f"\nAttachments: {len(attachments)} files - {', '.join([att['filename'] for att in attachments])}"
        
        # Prepare content for AI
        content = f"""
Subject: {subject}
From: {email_data.get('sender_name', '')} <{email_data.get('sender_email', '')}>
Body: {body[:2000]}{attachment_info}
"""
        
        # Enhanced AI prompt with better critical detection
        prompt = self._build_classification_prompt(content)
        
        # Call OpenAI API
        response = self.openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are a professional email classification assistant for real estate professionals. Always respond with valid JSON. Pay special attention to emergency and critical situations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1000
        )
        
        # Parse AI response
        classification = self._parse_ai_response(response.choices[0].message.content)
        
        # Post-process: Override AI if urgency score is very high
        if urgency_score >= 0.8:
            classification = self._apply_urgency_override(classification, urgency_score, body)
        
        # Add attachment info to extracted info
        if attachments:
            extracted_info = classification.get('extracted_info', {})
            extracted_info['attachment_count'] = len(attachments)
            extracted_info['attachment_types'] = [att['mime_type'] for att in attachments]
            classification['extracted_info'] = extracted_info
        
        # Add urgency indicators
        if urgency_score > 0:
            extracted_info = classification.get('extracted_info', {})
            if 'urgency_indicators' not in extracted_info:
                extracted_info['urgency_indicators'] = []
            classification['extracted_info'] = extracted_info
        
        # Validate and set defaults
        classification = self._validate_classification(classification)
        
        logger.info(f"Email classified: {classification['category']} - {classification['priority']} (urgency: {urgency_score})")
        return classification
    
    def _calculate_urgency_score(self, subject: str, body: str) -> float:
        """Calculate urgency score based on critical keywords"""
        critical_keywords = {
            'emergency': 1.0,
            'urgent': 0.9,
            'immediate': 0.9,
            'asap': 0.8,
            'critical': 0.9,
            'fire': 1.0,
            'flood': 1.0,
            'water leak': 0.9,
            'leak': 0.8,
            'broken pipe': 0.9,
            'no heat': 0.8,
            'no electricity': 0.9,
            'break in': 1.0,
            'broken': 0.6,
            'not working': 0.5,
            'health and safety': 0.9,
            'injuries': 0.8,
            'damage': 0.7
        }
        
        combined_text = f"{subject} {body}".lower()
        max_score = 0.0
        
        for keyword, score in critical_keywords.items():
            if keyword in combined_text:
                max_score = max(max_score, score)
                logger.info(f"Found critical keyword '{keyword}' with score {score}")
        
        return max_score
    
    def _build_classification_prompt(self, content: str) -> str:
        """Build the AI classification prompt - FIXED COMPLETE VERSION"""
        return f"""
You are an AI assistant helping a California real estate agent and property manager organize emails.

Classify this email into one of these EXACT categories:

**CATEGORIES:**
1. **Critical Alerts** - Emergency situations requiring immediate attention (fire, flood, break-ins, water leaks, safety issues)
2. **New Leads** - Potential clients, property inquiries, people wanting to buy/sell/rent
3. **Maintenance Requests** - Property maintenance, repairs, broken items, tenant complaints about property issues
4. **Offers & Contracts** - Purchase offers, contracts, legal documents, escrow matters
5. **Tenant Communications** - Communications with current tenants (rent payments, lease issues, move-in/out)
6. **Vendor Communications** - Contractors, suppliers, service providers, invoices, estimates
7. **Legal & Compliance** - Legal matters, attorney communications, compliance issues, violations
8. **Marketing & Listings** - Property marketing, MLS listings, photos, open houses
9. **Financial** - Commission payments, accounting, invoices, financial transactions
10. **General** - Everything else that doesn't fit the above categories

**PRIORITY LEVELS:**
- Critical: Emergency situations, urgent deadlines, critical business matters
- High: New leads, important deadlines, maintenance issues, legal matters
- Medium: Regular business communications, vendor correspondence
- Low: General information, marketing materials, newsletters

**EMAIL TO CLASSIFY:**
{content}

**INSTRUCTIONS:**
- Use EXACT category names from the list above
- Choose the MOST SPECIFIC category that fits
- Water leaks, broken pipes, fires, floods = "Critical Alerts" with "Critical" priority
- Property inquiries from potential clients = "New Leads" with "High" priority  
- Repair requests, broken appliances, maintenance = "Maintenance Requests" with "High" priority
- Current tenant issues (rent, lease questions) = "Tenant Communications" with "Medium" priority
- Contractor estimates, vendor invoices = "Vendor Communications" with "Medium" priority
- Extract contact info, property addresses, phone numbers, action items
- Be concise but informative in summary

Respond with ONLY valid JSON in this format:
{{
    "category": "EXACT category name",
    "sub_category": "More specific classification if applicable",
    "priority": "Critical/High/Medium/Low",
    "summary": "Brief 1-2 sentence summary of the email",
    "extracted_info": {{
        "contact_name": "Name if mentioned",
        "contact_phone": "Phone number if mentioned", 
        "contact_email": "Email if different from sender",
        "property_address": "Address if mentioned",
        "urgency_level": "Description of urgency if applicable",
        "action_required": "What action is needed if any"
    }},
    "requires_action": true/false,
    "confidence_score": 0.0-1.0,
    "tags": ["relevant", "keywords", "extracted"]
}}
"""
    
    def _parse_ai_response(self, ai_response: str) -> Dict:
        """Parse and clean AI response JSON"""
        # Clean and parse JSON
        ai_response = ai_response.strip()
        if ai_response.startswith('```json'):
            ai_response = ai_response[7:-3]
        elif ai_response.startswith('```'):
            ai_response = ai_response[3:-3]
        
        return json.loads(ai_response)
    
    def _apply_urgency_override(self, classification: Dict, urgency_score: float, body: str) -> Dict:
        """Override AI classification if urgency score is very high"""
        logger.info(f"High urgency score {urgency_score} detected, forcing Critical classification")
        
        classification['category'] = 'Critical Alerts'
        classification['priority'] = 'Critical'
        classification['requires_action'] = True
        
        # Update summary to reflect criticality
        if 'water' in body.lower() and 'leak' in body.lower():
            classification['sub_category'] = 'Water Emergency'
        elif 'fire' in body.lower():
            classification['sub_category'] = 'Fire Emergency'
        elif 'break' in body.lower() and 'in' in body.lower():
            classification['sub_category'] = 'Security Emergency'
        else:
            classification['sub_category'] = 'Emergency Situation'
        
        return classification
    
    def _validate_classification(self, classification: Dict) -> Dict:
        """Validate and set defaults for classification"""
        classification.setdefault('category', 'General')
        classification.setdefault('priority', 'Medium')
        classification.setdefault('summary', 'Email requires review')
        classification.setdefault('extracted_info', {})
        classification.setdefault('requires_action', False)
        classification.setdefault('confidence_score', 0.5)
        classification.setdefault('tags', [])
        return classification
    
    def _get_fallback_classification(self) -> Dict:
        """Return fallback classification when AI fails"""
        return {
            'category': 'General',
            'priority': 'Medium',
            'summary': 'Classification failed - manual review needed',
            'extracted_info': {},
            'requires_action': False,
            'confidence_score': 0.0,
            'tags': ['classification_failed']
        }