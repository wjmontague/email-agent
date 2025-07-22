import sqlite3
import os

def initialize_email_faq_database():
    """
    Initialize the email_faq.db SQLite database with email system knowledge
    """
    db_path = os.path.join(os.path.dirname(__file__), "email_faq.db")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create the email_faq table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS email_faq (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Enhanced email system knowledge with rich formatting
    email_faqs = [
        ("how do I classify emails", """The system **automatically classifies** emails into categories:

### 📧 Email Categories:
• **Critical Alerts** 🚨 - Emergency situations requiring immediate attention
• **New Leads** 🎯 - Potential clients and property inquiries  
• **Maintenance Requests** 🔧 - Property maintenance and repair requests
• **Offers & Contracts** 📋 - Purchase offers, contracts, legal documents
• **Tenant Communications** 🏠 - Communications with current tenants

You can view classified emails on the `Dashboard` and manually reclassify if needed using the category dropdown."""),
        
        ("what are the email categories", """The system uses **5 main categories**:

### 📋 Category Details:
1. **Critical Alerts** 🚨 - *Emergencies, urgent issues, immediate attention needed*
2. **New Leads** 🎯 - *Potential clients, property inquiries, showing requests*
3. **Maintenance Requests** 🔧 - *Property repairs, broken items, service requests*
4. **Offers & Contracts** 📋 - *Purchase agreements, legal documents, negotiations*
5. **Tenant Communications** 🏠 - *Routine tenant messages, rent inquiries, lease matters*

💡 **Tip:** Click any category number on the dashboard to filter and view those emails!"""),
        
        ("what are priority levels", """Emails are assigned **4 priority levels**:

### ⚡ Priority Levels:
1. **Critical** 🚨 - *Immediate attention required* (emergencies, urgent offers)
2. **High** ⚠️ - *Same day response needed* (new leads, maintenance issues)
3. **Medium** 📝 - *Respond within 2-3 days* (routine tenant communications)  
4. **Low** ℹ️ - *Respond when convenient* (general inquiries, newsletters)

**Critical** and **High** priority emails are *highlighted* on the dashboard for quick identification."""),
        
        ("how do I use the dashboard", """📊 **Dashboard Overview**

The dashboard shows email counts by **category** and **priority**:

### Quick Actions:
• Click any **category number** to filter emails by type
• Use the `Process New Emails` button to check for new messages  
• The `Requires Action` section shows emails needing responses
• View **today's email count** and **unread totals** at the top

### Priority Indicators:
- **Critical** 🚨 - Red highlighting, immediate attention required
- **High** ⚠️ - Orange highlighting, same-day response needed
- **Medium** 📝 - Blue highlighting, 2-3 day response window
- **Low** ℹ️ - Gray highlighting, respond when convenient

💡 **Pro tip:** Use the email priority filters to quickly find urgent items!"""),
        
        ("how do I reply to emails", """💬 **Replying to Emails**

### Step-by-Step:
1. **Click on any email** to view the full message
2. **Click the `Reply` button** at the bottom of the email
3. **Compose your response** in the message field
4. **Add CC/BCC recipients** if needed (optional)
5. **Attach files** if necessary
6. **Click `Send Email`** to send your reply

### Quick Features:
• **Reply All** - Responds to all recipients
• **Forward** - Send the email to someone else
• **Templates** - Use pre-written responses for common situations
• **Drafts** - Save your work and finish later

⚡ **Quick tip:** You can reply directly from the email view without switching screens!"""),
        
        ("how do I search emails", """🔍 **Email Search Features**

### Search Options:
• **Sender Search** - Find emails from specific people
• **Subject Search** - Search by email subject line
• **Content Search** - Look for keywords in email body
• **Date Range** - Filter by specific time periods
• **Category Filter** - Search within specific categories
• **Priority Filter** - Find emails by urgency level

### How to Search:
1. **Click the `Search` button** in the main navigation
2. **Enter your search terms** in the search box
3. **Use filters** to narrow down results
4. **Click on any result** to view the full email

💡 **Search Tips:**
- Use **quotation marks** for exact phrases
- Try **sender's name** or **email address**
- Search by **property address** for location-specific emails"""),
        
        ("how does email processing work", """🔄 **Email Processing System**

### Automatic Processing:
• **Every 30 minutes** - System checks for new emails automatically
• **AI Classification** - Each email gets categorized and prioritized
• **Smart Learning** - System improves accuracy over time
• **Attachment Handling** - Files are automatically downloaded and organized

### Manual Processing:
1. **Go to Reports page**
2. **Click `Process New Emails`** for immediate check
3. **Use `Process Last 2 Months`** to catch up on older emails
4. **Monitor processing status** on the dashboard

### What Happens:
- Emails are **downloaded** from Gmail
- **AI analyzes** content and assigns categories
- **Priority levels** are determined automatically
- **Attachments** are saved and organized
- **Dashboard** updates with new counts

⚡ **Note:** Historical processing is available for catching up on older emails."""),
        
        ("what does requires action mean", """🎯 **Requires Action Emails**

These are emails that **typically need a response** from you:

### Common Action Items:
• **Tenant requests** - Maintenance, repairs, questions
• **New leads** - Property inquiries, showing requests
• **Urgent maintenance** - Emergency repairs, urgent issues
• **Contract matters** - Offers, negotiations, legal documents
• **Important notifications** - Payment issues, lease matters

### How to Handle:
1. **Check the `Requires Action` section** on your dashboard
2. **Review each email** to understand what's needed
3. **Respond promptly** to maintain good relationships
4. **Use email templates** for faster responses
5. **Mark as completed** when action is taken

💡 **Workflow tip:** This filter helps prioritize your daily email tasks efficiently!"""),
        
        ("how do I mark emails as read", """👀 **Marking Emails as Read**

### Automatic Method:
• **Click on any email** to open it - *automatically marks as read*
• **View email details** - Opens and marks as read instantly
• **Real-time updates** - Dashboard counts update immediately

### Manual Method:
1. **Go to email list view**
2. **Use checkboxes** to select multiple emails
3. **Click `Mark as Read`** button (bulk action)
4. **Confirm selection** to update status

### Read Status Benefits:
- **Dashboard accuracy** - Unread counts stay current
- **Priority focus** - See only new items that need attention
- **Progress tracking** - Know what you've already reviewed

📊 **Dashboard tip:** The unread count helps you track your daily email workload!"""),
        
        ("how do I archive emails", """📁 **Email Archiving**

### Archive Individual Emails:
1. **Open any email** you want to archive
2. **Click the `Archive` button** at the bottom
3. **Email moves to archived status** (removes from main view)
4. **Dashboard counts update** immediately

### Archive Benefits:
• **Clean dashboard** - Removes processed emails from main view
• **Keeps records** - Archived emails remain searchable
• **Better organization** - Focus on current, actionable items
• **Accessible anytime** - Can be found through search function

### When to Archive:
- **Completed requests** - Maintenance issues that are resolved
- **Processed leads** - Inquiries that have been followed up
- **Old communications** - Historical conversations no longer active
- **Reference materials** - Information you might need later

🗂️ **Organization tip:** Regular archiving keeps your workspace clean and focused!"""),
        
        ("what are attachments", """📎 **Email Attachments**

### Automatic Features:
• **Downloads automatically** - All attachments saved securely
• **Organized by sender** - Files sorted by who sent them
• **Date-based folders** - Organized by month and year
• **Safe storage** - All files securely stored and backed up

### File Organization:
```
📁 attachments/
  📁 sender_email.com/
    📁 2025-07/
      📁 message_id/
        📄 document.pdf
        📄 contract.docx
```

### Viewing Attachments:
1. **Open any email** with attachments
2. **Scroll to attachment section** at the bottom
3. **Click attachment name** to download/view
4. **Files open safely** in your browser or download

### Supported Types:
- **Documents** - PDF, Word, Excel files
- **Images** - Photos, screenshots, diagrams  
- **Text files** - Plain text, CSV files
- **Archives** - ZIP files and compressed folders

🔒 **Security:** All attachments are scanned and safely stored with organized access."""),
        
        ("how do I compose emails", """✉️ **Composing New Emails**

### Getting Started:
1. **Click the `Compose Email` button** on the dashboard
2. **Fill in recipient** - Type email address in 'To' field
3. **Add subject line** - Clear, descriptive subject
4. **Write your message** - Use the rich text editor
5. **Add attachments** if needed (drag & drop supported)
6. **Click `Send Email`** to deliver

### Advanced Features:
• **CC/BCC Recipients** - Add additional recipients
• **Email Templates** - Quick responses for common situations
• **Attachment Support** - Up to 50MB per file
• **Draft Saving** - Save work and finish later
• **Scheduled Sending** - Send emails at specific times

### Template Options:
- **Maintenance Response** - For repair requests
- **Follow-up Template** - For new leads
- **Showing Template** - For property viewings
- **General Response** - For routine inquiries

💡 **Efficiency tip:** Use templates to respond faster to common email types!"""),
        
        ("what is email threading", """🧵 **Email Threading**

### How It Works:
• **Related emails grouped together** - All messages in a conversation
• **Full conversation history** - See the complete back-and-forth
• **Chronological order** - Messages sorted by date and time
• **Easy navigation** - Click through conversation easily

### Benefits:
- **Complete context** - Understand the full conversation
- **Track communications** - See all interactions with tenants/clients
- **Avoid confusion** - Never lose track of what was discussed
- **Professional responses** - Reference previous messages accurately

### Thread Features:
1. **Conversation view** - All related messages in one place
2. **Original message** - Always visible for reference
3. **Reply context** - Your responses include conversation history
4. **Search within thread** - Find specific parts of conversations

📧 **Communication tip:** Threading helps you maintain professional, informed conversations with all your contacts!"""),
        
        ("how do I change email status", """🔄 **Email Status Management**

### Automatic Status Updates:
• **Reading emails** - Automatically marks as 'read'
• **Replying** - Updates to 'replied' status
• **Processing actions** - Status changes based on your actions
• **Real-time updates** - Dashboard reflects changes immediately

### Manual Status Changes:
1. **Open any email** you want to update
2. **Use action buttons** at the bottom:
   - `Mark as Read/Unread`
   - `Archive`
   - `Mark as Important`
   - `Requires Action`
3. **Status updates instantly** across the system

### Status Types:
- **Unread** 📬 - New emails needing attention
- **Read** 📖 - Emails you've reviewed
- **Replied** ↩️ - Emails you've responded to
- **Archived** 📁 - Completed/stored emails
- **Important** ⭐ - High-priority flagged emails

📊 **Dashboard impact:** Status changes immediately update your dashboard counts and filters!"""),
        
        ("what are email reports", """📈 **Email Reports & Analytics**

### Available Reports:
• **Volume Tracking** - Daily, weekly, monthly email counts
• **Category Distribution** - Which types of emails are most common
• **Priority Analysis** - Breakdown of urgent vs routine communications
• **Response Metrics** - Track your reply times and efficiency
• **Client Insights** - Per-client email statistics and communication patterns

### Accessing Reports:
1. **Click `Reports`** in the main navigation
2. **View real-time statistics** on the reports dashboard
3. **Filter by date range** for specific time periods
4. **Export data** for external analysis (if needed)

### Key Metrics:
- **Total emails processed** this month
- **Average response time** to important emails
- **Category breakdown** (Critical, High, Medium, Low)
- **Busiest communication days** and times
- **Client interaction frequency** and patterns

### Using Report Data:
💡 **Optimize workflow** - Identify peak email times
📊 **Track performance** - Monitor response efficiency  
🎯 **Focus efforts** - See which categories need most attention
📈 **Business insights** - Understand communication patterns

**Pro tip:** Use reports to optimize your property management workflow and improve client satisfaction!"""),
        
        ("how do I backup emails", """💾 **Email Backup & Data Management**

### Automatic Backups:
• **System maintains backups** - All processed emails and attachments
• **Local storage** - Data stored securely on your server
• **Attachment preservation** - All files backed up with emails
• **Database integrity** - Regular backup verification

### Data Export Options:
1. **Email export** - Download email data in standard formats
2. **Attachment backup** - Access to all downloaded files
3. **Report export** - Analytics data for external use
4. **Database backup** - Complete system backup (admin function)

### Backup Features:
- **Automatic daily backups** of email database
- **Attachment file preservation** with organized structure
- **Email content preservation** including formatting and metadata
- **Search index backup** for quick data recovery

### Data Security:
🔒 **Encrypted storage** - All data secured at rest
📁 **Organized structure** - Easy to navigate backup files
🔄 **Regular verification** - Backup integrity checked automatically
⚡ **Quick recovery** - Fast restoration if needed

**Admin tip:** Contact support for additional backup procedures or data export assistance."""),
        
        ("what languages are supported", """🌐 **Language Support**

### Email Helper Languages:
• **English** 🇺🇸 - Full support (default)
• **Spanish** 🇪🇸 - Complete translation support
• **French** 🇫🇷 - Comprehensive language support

### How to Change Language:
1. **Use the language dropdown** in the chat interface
2. **Select your preferred language** from the menu
3. **Continue asking questions** in your chosen language
4. **AI responds** in the language you selected

### Language Features:
- **Real-time translation** - Instant language switching
- **Context preservation** - Maintains technical accuracy across languages
- **Cultural adaptation** - Responses adapted for regional differences
- **Professional terminology** - Industry-specific terms translated correctly

### Main System Language:
📧 **Email processing** - Currently operates in English
🖥️ **Dashboard interface** - English interface (additional languages planned)
📊 **Reports** - Generated in English
💬 **Templates** - Available in English

💡 **Tip:** The AI assistant can help you understand English interface elements by explaining them in your preferred language!"""),
        
        ("how do I get help", """🆘 **Getting Help & Support**

### Built-in Help:
• **This chat assistant** - Available 24/7 for system questions
• **Quick action buttons** - Pre-built questions for common topics
• **Contextual tips** - Helpful hints appear during conversations
• **User manual** - Comprehensive documentation (if available)

### Support Channels:
1. **AI Assistant** - Ask questions anytime (what you're doing now!)
2. **Documentation** - Check the help section for detailed guides
3. **Contact Support** - Reach out for technical issues
4. **User Community** - Connect with other users (if available)

### Common Help Topics:
🔧 **Technical Issues** - Login problems, processing errors
📧 **Email Setup** - Gmail authorization, classification issues  
📊 **Dashboard Questions** - Navigation, features, filters
💡 **Best Practices** - Workflow optimization, efficiency tips
🎯 **Feature Requests** - Suggestions for improvements

### Self-Help Tips:
- **Try the search function** for specific topics
- **Check recent tips** that appear in this chat
- **Review the dashboard tutorial** (if available)
- **Ask specific questions** for detailed help

**Quick access:** Use the 🤖 **Email Assistant** button anytime you need help with any system feature!"""),
        
        ("what are quick filters", """⚡ **Quick Dashboard Filters**

### How Quick Filters Work:
• **Click any number** on the dashboard to instantly filter emails
• **Category filtering** - View only emails from specific categories
• **Priority filtering** - See only Critical, High, Medium, or Low priority emails
• **Status filtering** - Filter by read/unread, requires action, etc.

### Available Quick Filters:
1. **Today's Emails** 📅 - Only emails received today
2. **Unread** 📬 - All unread emails across categories
3. **Critical** 🚨 - Highest priority emails requiring immediate attention
4. **High Priority** ⚠️ - Important emails needing same-day response

### Category Quick Filters:
- **Critical Alerts** 🚨 - Emergency situations and urgent issues
- **New Leads** 🎯 - Potential clients and property inquiries
- **Maintenance Requests** 🔧 - Property repairs and service requests
- **Offers & Contracts** 📋 - Legal documents and negotiations
- **Tenant Communications** 🏠 - Routine tenant interactions

### Filter Benefits:
💡 **Instant focus** - See only the emails you need right now
🎯 **Priority management** - Handle urgent items first
📊 **Workload organization** - Break down tasks into manageable chunks
⚡ **Efficiency boost** - Find what you need without scrolling

**Workflow tip:** Use quick filters to tackle your emails by priority level - handle **Critical** first, then **High**, and so on!"""),
        
        ("how do I handle maintenance requests", """🔧 **Managing Maintenance Requests**

### Identification:
• **Automatically categorized** - System recognizes maintenance emails
• **Priority assigned** - Based on urgency keywords and content
• **Action flagging** - Most maintenance requests marked as 'Requires Action'
• **Quick access** - Filter by 'Maintenance Requests' category

### Response Workflow:
1. **Review the request** - Understand what needs repair/attention
2. **Assess urgency** - Check if it's Critical (emergency) or High priority
3. **Use reply templates** - Quick responses for common situations
4. **Contact contractors** - Forward request or schedule service
5. **Update tenant** - Confirm receipt and provide timeline
6. **Follow up** - Check completion and tenant satisfaction

### Template Responses:
- **"Request Received"** - Acknowledge the maintenance request
- **"Scheduling Service"** - Inform about contractor scheduling
- **"Emergency Response"** - For urgent/critical maintenance issues
- **"Request Completed"** - Confirm work has been finished

### Priority Handling:
🚨 **Critical** - *Emergencies* (flooding, heating/AC failure, security issues)
⚠️ **High** - *Urgent repairs* (plumbing leaks, electrical issues, broken appliances)
📝 **Medium** - *Standard maintenance* (routine repairs, non-urgent fixes)
ℹ️ **Low** - *Aesthetic issues* (painting touch-ups, minor cosmetic items)

**Efficiency tip:** Keep a list of trusted contractors and their contact info for quick forwarding of maintenance requests!""")
    ]
    
    cursor.executemany("INSERT INTO email_faq (question, answer) VALUES (?, ?)", email_faqs)
    conn.commit()
    conn.close()
    
    print(f"✅ Email FAQ database initialized at {db_path}")
    print(f"✅ Added {len(email_faqs)} enhanced knowledge entries with rich formatting")

if __name__ == "__main__":
    initialize_email_faq_database()