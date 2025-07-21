# Email AI Agent for Real Estate

A professional-grade email management system designed specifically for California real estate agents and property managers. This AI-powered application automatically categorizes, prioritizes, and summarizes emails to help busy professionals focus on what matters most.

## Features

### 🤖 AI-Powered Email Classification
- Automatically categorizes emails into 10 relevant categories
- Intelligent priority assignment (Critical, High, Medium, Low)
- Smart summarization of email content
- Extraction of key information (contacts, properties, amounts, dates)

### 📊 Professional Dashboard
- Clean, modern interface optimized for mobile and desktop
- Real-time email statistics and analytics
- Category-based organization with visual priority indicators
- Quick action buttons for common tasks

### 🔍 Advanced Search & Filtering
- Full-text search across subjects, content, and summaries
- Filter by category, priority, and date ranges
- Tag-based organization for easy retrieval

### 💬 Email Thread Management
- Intelligent email threading and conversation grouping
- Complete conversation history with context preservation
- Thread-aware categorization and priority assignment

### ✉️ Email Composition & Reply
- Built-in email composer with rich text editing
- Smart reply suggestions based on email context
- Thread-aware responses that maintain conversation flow
- Draft auto-save functionality

### 📈 Analytics & Reporting
- Daily email volume tracking
- Category and priority distribution charts
- Performance metrics and trends
- Export capabilities for further analysis

### 🔄 Automated Processing
- Batch processing every 30 minutes
- Gmail API integration with OAuth 2.0 security
- Secure local database storage
- Background processing with error handling

## Email Categories

1. **Critical Alerts** - Emergencies requiring immediate attention
2. **New Leads** - Potential clients and property inquiries
3. **Maintenance Requests** - Property repair and maintenance issues

## Installation & Setup

This application comes pre-configured for real estate offices and property management companies. However, it can be easily adapted for any business or personal use by modifying the email categories and AI prompts in the configuration files.

### Prerequisites
- Python 3.10 or higher
- Google Cloud Platform account with Gmail API enabled
- OpenAI API account and key
- Gmail account for email processing

### Setup Steps
1. Clone this repository
2. Install required dependencies: `pip install -r requirements.txt`
3. Configure Google Cloud Gmail API credentials
4. Add your OpenAI API key to the environment variables
5. Customize email categories and prompts (optional)
6. Run the application: `python flask_app.py`

### Customization
To adapt this system for other industries or personal use, simply modify the email categories and AI classification prompts in the `email_classifier.py` file to match your specific needs.

---

**Note:** This application is built to work with the Google Cloud Gmail API and operates as an intelligent layer on top of your existing Gmail account. It requires Google Cloud API credentials and Gmail API access to function. The AI classification and summarization features are powered by OpenAI GPT-4 Turbo, requiring an OpenAI API key. The system reads and analyzes your emails without modifying your original Gmail inbox, providing enhanced organization and insights while maintaining the security and integrity of your email data.