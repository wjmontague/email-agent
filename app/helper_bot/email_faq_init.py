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

    # Add email system knowledge
    email_faqs = [
        ("how do I classify emails", "The system automatically classifies emails into categories like Critical Alerts, New Leads, Maintenance Requests, Offers & Contracts, and Tenant Communications. You can view classified emails on the dashboard and manually reclassify if needed."),

        ("what are the email categories", "The system uses 5 main categories: Critical Alerts (urgent issues), New Leads (potential clients), Maintenance Requests (property repairs), Offers & Contracts (deals and agreements), and Tenant Communications (routine tenant messages)."),

        ("what are priority levels", "Emails are assigned 4 priority levels: Critical (immediate attention), High (same day response), Medium (respond within 2-3 days), and Low (respond when convenient). Critical and High priority emails are highlighted on the dashboard."),

        ("how do I use the dashboard", "The dashboard shows email counts by category and priority. Click on any number to filter emails. Use the 'Process New Emails' button to check for new messages. The 'Requires Action' section shows emails needing responses."),

        ("how do I reply to emails", "Click on any email to view it, then use the Reply button. You can also use Reply All, Forward, or Compose new emails. The system tracks your responses and updates email status automatically."),

        ("how do I search emails", "Use the search function on the dashboard to find emails by sender, subject, or content. You can also filter by date range, category, or priority level to narrow down results."),

        ("how does email processing work", "The system checks Gmail hourly and automatically classifies new emails. You can manually trigger processing with the 'Process New Emails' button. Historical processing is available for catching up on older emails."),

        ("what does requires action mean", "Emails marked 'Requires Action' are those that typically need a response from you, such as tenant requests, new leads, or urgent maintenance issues. This helps prioritize your email workflow."),

        ("how do I mark emails as read", "Click on any email to open it - this automatically marks it as read. You can also bulk mark emails as read from the email list view using the checkbox selections."),

        ("how do I archive emails", "Use the Archive button when viewing an email to move it to archived status. Archived emails don't appear in your main dashboard counts but remain searchable and accessible."),

        ("what are attachments", "The system automatically downloads and organizes email attachments by sender and date. You can view and download attachments from the email detail view. All attachments are securely stored and organized."),

        ("how do I compose emails", "Use the Compose button on the dashboard or email view. You can add CC/BCC recipients, attach files, and the system will track sent emails. Templates are available for common responses."),

        ("what is email threading", "Related emails are grouped together as conversation threads. You can see the full conversation history when viewing any email in a thread. This helps track ongoing communications with tenants or clients."),

        ("how do I change email status", "Email status updates automatically based on your actions (reading marks as read, replying updates status). You can also manually change status using the action buttons in the email view."),

        ("what are email reports", "The Reports section provides analytics on email volume, response times, category distributions, and tenant communication patterns. Use this to optimize your property management workflow."),

        ("how do I backup emails", "The system maintains backups of all processed emails and attachments. Email data is stored locally and can be exported for additional backup purposes through the admin functions."),

        ("what languages are supported", "The email helper supports English, Spanish, and French. You can change the language using the dropdown in the chat interface. The main email system currently operates in English."),

        ("how do I get help", "You can use this chat assistant anytime, check the user manual, or contact support through the dashboard. Common tasks have step-by-step guides available in the help section."),

        ("what are quick filters", "Quick filters on the dashboard let you instantly view emails by category (Critical Alerts, New Leads, etc.) or priority level. Click any number on the dashboard to apply that filter."),

        ("how do I handle maintenance requests", "Maintenance request emails are automatically categorized and marked by priority. You can reply directly, forward to contractors, or mark as completed. Track all maintenance communications in one place.")
    ]

    cursor.executemany("INSERT INTO email_faq (question, answer) VALUES (?, ?)", email_faqs)
    conn.commit()
    conn.close()

    print(f"✅ Email FAQ database initialized at {db_path}")
    print(f"✅ Added {len(email_faqs)} knowledge entries")

if __name__ == "__main__":
    initialize_email_faq_database()