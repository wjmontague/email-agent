from flask import Blueprint, render_template, redirect, url_for, request, flash, session, send_from_directory, Response
from app.database_models import Email, ClassifiedEmail
from app import db
import logging
import os
from app.secure_auth_decorator import require_auth, add_security_headers

logger = logging.getLogger(__name__)
main_bp = Blueprint('main', __name__)

# Try to import optional services (graceful degradation if not available)
try:
    from app.services.drafts_service import DraftsService
    HAS_DRAFTS_SERVICE = True
except ImportError:
    HAS_DRAFTS_SERVICE = False

try:
    from app.utils.email_stats import EmailStatsService
    HAS_EMAIL_STATS = True
except ImportError:
    HAS_EMAIL_STATS = False

# ========== CORE DASHBOARD ROUTES ==========

@main_bp.route('/')
@main_bp.route('/dashboard')
@add_security_headers()
@require_auth()
def dashboard():
    """Main dashboard with comprehensive email data and real-time count management"""
    try:
        # Get basic stats with error handling
        try:
            unread = ClassifiedEmail.query.filter_by(is_read=False).count()
        except:
            unread = 0

        try:
            critical = ClassifiedEmail.query.filter_by(priority='Critical', is_read=False).count()
        except:
            critical = 0

        try:
            high = ClassifiedEmail.query.filter_by(priority='High', is_read=False).count()
        except:
            high = 0

        try:
            from datetime import datetime, date
            today = date.today()
            total_today = Email.query.filter(Email.received_at >= today).count()
        except:
            total_today = 0

        # Prepare stats for template
        stats = {
            'unread': unread,
            'critical': critical,
            'high': high,
            'total': Email.query.count() if Email.query.count() else 0,
            'total_today': total_today
        }

        # Get actual category counts from database
        try:
            critical_alerts = ClassifiedEmail.query.filter_by(category='Critical Alerts').count()
            new_leads = ClassifiedEmail.query.filter_by(category='New Leads').count()
            maintenance = ClassifiedEmail.query.filter_by(category='Maintenance Requests').count()
            offers = ClassifiedEmail.query.filter_by(category='Offers & Contracts').count()
            tenant_comm = ClassifiedEmail.query.filter_by(category='Tenant Communications').count()
            general = ClassifiedEmail.query.filter(
                ~ClassifiedEmail.category.in_(['Critical Alerts', 'New Leads', 'Maintenance Requests', 'Offers & Contracts', 'Tenant Communications'])
            ).count()
        except:
            critical_alerts = critical  # Fallback to priority counts
            new_leads = 0
            maintenance = 0
            offers = 0
            tenant_comm = 0
            general = 0

        # Category counts for dashboard cards
        category_counts = {
            'Critical Alerts': critical_alerts,
            'High Priority': high,
            'New Leads': new_leads,
            'Maintenance Requests': maintenance,
            'Offers & Contracts': offers,
            'Tenant Communications': tenant_comm,
            'General': general
        }

        # Get recent emails for dashboard timeline
        try:
            recent_emails = Email.query.order_by(Email.received_at.desc()).limit(15).all()
        except:
            recent_emails = []

        # Get categorized emails for dashboard sections (if template expects them)
        try:
            categorized_emails = _get_categorized_emails_for_dashboard()
        except:
            categorized_emails = {}

        return render_template('dashboard.html',
                             stats=stats,
                             category_counts=category_counts,
                             categorized_emails=categorized_emails,
                             recent_emails=recent_emails,
                             email_gap={'show_historical_button': False, 'message': 'Dashboard loaded'},
                             username=session.get('username', 'User'))

    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        # Return minimal error page that still works
        return f"""
        <div style="padding: 20px; font-family: Arial;">
            <h1>Dashboard Error</h1>
            <p>Error: {str(e)}</p>
            <p><a href="/api/test">Test API</a> | <a href="/api/urgent_counts">Test Counts</a></p>
            <p><a href="/test">Test Main Routes</a></p>
        </div>
        """

def _get_categorized_emails_for_dashboard():
    """Get recent emails organized by category for dashboard display"""
    try:
        # Get recent emails with classifications
        recent_classified = db.session.query(Email, ClassifiedEmail).join(
            ClassifiedEmail, Email.id == ClassifiedEmail.email_id
        ).order_by(Email.received_at.desc()).limit(20).all()

        # Organize by category
        categorized = {}
        for email, classified in recent_classified:
            category = classified.category or 'General'
            if category not in categorized:
                categorized[category] = []
            categorized[category].append({
                'email': email,
                'classified': classified
            })

        return categorized
    except Exception as e:
        logger.error(f"Error getting categorized emails: {e}")
        return {}

# ========== EMAIL ROUTES ==========

@main_bp.route('/email/<int:email_id>')
@add_security_headers()
@require_auth()
def view_email(email_id):
    """View individual email with count update capability"""
    try:
        email = Email.query.get_or_404(email_id)
        classified_email = ClassifiedEmail.query.filter_by(email_id=email_id).first()

        # Mark as read if not already read
        if classified_email and not classified_email.is_read:
            classified_email.is_read = True
            db.session.commit()
            logger.info(f"Marked email {email_id} as read")

        # Debug: Log what we're trying to render
        logger.info(f"Rendering email {email_id}: {email.subject}")
        logger.info(f"Has classification: {classified_email is not None}")

        # Try multiple template names (in case the template has a different name)
        template_names = [
            'view_email.html',
            'email_detail.html',
            'email_view.html',
            'email.html'
        ]

        for template_name in template_names:
            try:
                return render_template(template_name, email=email, classified=classified_email)
            except Exception as template_error:
                logger.warning(f"Template {template_name} not found: {template_error}")
                continue

        # If no template works, create a simple inline view
        return f"""
        <div style="padding: 20px; font-family: Arial; max-width: 800px; margin: 0 auto;">
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <h1 style="color: #333; margin-bottom: 10px;">📧 {email.subject or 'No Subject'}</h1>
                <div style="color: #666; font-size: 14px; margin-bottom: 15px;">
                    <strong>From:</strong> {email.sender_name or 'Unknown'} &lt;{email.sender_email}&gt;<br>
                    <strong>Date:</strong> {email.received_at.strftime('%B %d, %Y at %I:%M %p')}<br>
                    {f'<strong>Priority:</strong> <span style="color: {"red" if classified_email and classified_email.priority == "Critical" else "orange" if classified_email and classified_email.priority == "High" else "blue"};">{classified_email.priority}</span><br>' if classified_email else ''}
                    {f'<strong>Category:</strong> {classified_email.category}<br>' if classified_email else ''}
                </div>
            </div>

            <div style="background: white; padding: 20px; border-radius: 8px; border: 1px solid #ddd; margin-bottom: 20px;">
                <h3 style="color: #333; margin-bottom: 15px;">Email Content</h3>
                <div style="line-height: 1.6; white-space: pre-wrap;">{email.body_text or email.subject or 'No content available'}</div>
            </div>

            {f'<div style="background: #e3f2fd; padding: 15px; border-radius: 8px; margin-bottom: 20px;"><h4 style="color: #1976d2; margin-bottom: 10px;">Summary</h4><p>{classified_email.summary}</p></div>' if classified_email and classified_email.summary else ''}

            <div style="text-align: center; margin-top: 30px;">
                <a href="/reply/{email.id}" style="background: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-right: 10px;">
                    📝 Reply
                </a>
                <a href="/client/{email.sender_email}" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-right: 10px;">
                    👤 View Client
                </a>
                <a href="javascript:history.back()" style="background: #6c757d; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                    ← Back
                </a>
            </div>
        </div>
        """

    except Exception as e:
        logger.error(f"View email error: {e}")
        import traceback
        traceback.print_exc()

        # Return detailed error instead of redirecting to dashboard
        return f"""
        <div style="padding: 20px; font-family: Arial;">
            <h1>Email View Error</h1>
            <p><strong>Email ID:</strong> {email_id}</p>
            <p><strong>Error:</strong> {str(e)}</p>
            <details style="margin-top: 20px;">
                <summary>Technical Details</summary>
                <pre style="background: #f5f5f5; padding: 10px; border-radius: 4px; overflow: auto;">
{traceback.format_exc()}
                </pre>
            </details>
            <div style="margin-top: 20px;">
                <a href="javascript:history.back()" style="background: #6c757d; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                    ← Back to Conversation
                </a>
            </div>
        </div>
        """

# ========== CATEGORY ROUTES ==========

@main_bp.route('/category/<category_name>')
@add_security_headers()
def category_view(category_name):
    """View emails in specific category"""
    try:
        # Get emails for this category
        emails = db.session.query(ClassifiedEmail, Email).join(Email).filter(
            ClassifiedEmail.category == category_name
        ).order_by(Email.received_at.desc()).all()

        # Calculate category stats
        category_stats = {
            'total': len(emails),
            'unread': sum(1 for classified, email in emails if not classified.is_read),
            'priority_counts': {}
        }

        return render_template('category_view.html',
                             category_name=category_name,
                             emails=emails,
                             category_stats=category_stats)

    except Exception as e:
        logger.error(f"Category view error: {e}")
        return f"""
        <div style="padding: 20px; font-family: Arial;">
            <h1>Category: {category_name}</h1>
            <p>Error loading category: {str(e)}</p>
            <p><a href="/">Back to Dashboard</a></p>
        </div>
        """

# ========== CLIENT ROUTES ==========

@main_bp.route('/clients')
@add_security_headers()
def client_list():
    """Client list with conversation summaries"""
    try:
        # Get unique senders with email counts
        unique_senders = db.session.query(
            Email.sender_email,
            Email.sender_name,
            db.func.count(Email.id).label('email_count'),
            db.func.max(Email.received_at).label('last_contact')
        ).group_by(Email.sender_email, Email.sender_name).order_by(
            db.func.max(Email.received_at).desc()
        ).limit(50).all()

        # Format client data
        client_data = []
        for sender in unique_senders:
            # Count unread emails for this sender
            try:
                unread_count = db.session.query(ClassifiedEmail).join(Email).filter(
                    Email.sender_email == sender.sender_email,
                    ClassifiedEmail.is_read == False
                ).count()
            except:
                unread_count = 0

            client_data.append({
                'name': sender.sender_name or 'Unknown',
                'email': sender.sender_email,
                'email_count': sender.email_count,
                'unread_count': unread_count,
                'last_contact': sender.last_contact,
                'status': 'Client',
                'primary_category': 'General',
                'attachment_count': 0  # Could be calculated if needed
            })

        return render_template('client_list.html', clients=client_data)

    except Exception as e:
        logger.error(f"Client list error: {e}")
        return f"""
        <div style="padding: 20px; font-family: Arial;">
            <h1>Client List</h1>
            <p>Error: {str(e)}</p>
            <p><a href="/">Back to Dashboard</a></p>
        </div>
        """

@main_bp.route('/client/<path:client_email>')
@add_security_headers()
def client_conversation(client_email):
    """View conversation with specific client"""
    try:
        # Get all emails with this client (both sent and received)
        emails = db.session.query(Email, ClassifiedEmail).outerjoin(
            ClassifiedEmail, Email.id == ClassifiedEmail.email_id
        ).filter(
            db.or_(
                db.and_(Email.sender_email == client_email, Email.is_sent == False),
                db.and_(Email.recipient_email == client_email, Email.is_sent == True)
            )
        ).order_by(Email.received_at.desc()).all()

        if not emails:
            flash(f'No emails found with {client_email}', 'info')
            return redirect(url_for('main.client_list'))

        # Debug: Check what we got
        logger.info(f"Found {len(emails)} emails for {client_email}")
        for i, (email, classified) in enumerate(emails[:3]):  # Log first 3 emails
            logger.info(f"Email {i}: {email.subject}, classified: {classified is not None}")
            if classified:
                logger.info(f"  - Summary: {classified.summary[:50] if classified.summary else 'None'}...")
                logger.info(f"  - Priority: {classified.priority}")
                logger.info(f"  - Category: {classified.category}")

        # Get client name from most recent email
        client_name = None
        for email, classified in emails:
            if not email.is_sent and email.sender_name:
                client_name = email.sender_name
                break

        if not client_name:
            client_name = client_email.split('@')[0].title()

        # Organize emails by category for the template
        categories = {}
        properties_mentioned = set()

        for email, classified in emails:
            if classified:
                category = classified.category or 'General'
                if category not in categories:
                    categories[category] = []
                categories[category].append((email, classified))

                # Collect property addresses if available
                if hasattr(classified, 'property_address') and classified.property_address:
                    properties_mentioned.add(classified.property_address)
            else:
                # This shouldn't happen based on migration results, but handle it
                if 'General' not in categories:
                    categories['General'] = []
                categories['General'].append((email, None))

        # Calculate dates
        first_contact = emails[-1][0].received_at if emails else None
        last_contact = emails[0][0].received_at if emails else None

        # Calculate days since last contact
        days_since_contact = 0
        if last_contact:
            from datetime import datetime
            days_since_contact = (datetime.now() - last_contact.replace(tzinfo=None)).days

        # Calculate client stats with all required fields
        client_stats = {
            'total_emails': len(emails),
            'unread_count': sum(1 for email, classified in emails if classified and not classified.is_read),
            'status': 'Client',
            'primary_category': 'General',
            'days_since_contact': days_since_contact,
            'categories': categories,
            'first_contact': first_contact,
            'last_contact': last_contact,
            'properties_mentioned': list(properties_mentioned)
        }

        # Debug: Log the data we're sending to template
        logger.info(f"Client stats: {client_stats}")
        logger.info(f"Categories: {list(categories.keys())}")

        conversation_data = {
            'client_email': client_email,
            'client_name': client_name,
            'emails': emails,
            'client_stats': client_stats
        }

        return render_template('client_conversation.html', **conversation_data)

    except Exception as e:
        logger.error(f"Client conversation error: {e}")
        import traceback
        traceback.print_exc()

        # Return a debug version that shows what went wrong
        return f"""
        <div style="padding: 20px; font-family: Arial;">
            <h1>Client Conversation Debug</h1>
            <p><strong>Client:</strong> {client_email}</p>
            <p><strong>Error:</strong> {str(e)}</p>
            <p><strong>Traceback:</strong></p>
            <pre style="background: #f5f5f5; padding: 10px; border-radius: 4px; overflow: auto;">
{traceback.format_exc()}
            </pre>

            <h3>Debug Info:</h3>
            <ul>
                <li>Total emails found: {len(emails) if 'emails' in locals() else 'N/A'}</li>
                <li>Client name: {client_name if 'client_name' in locals() else 'N/A'}</li>
                <li>Categories: {list(categories.keys()) if 'categories' in locals() else 'N/A'}</li>
            </ul>

            <p><a href="/clients">Back to Client List</a></p>
            <p><a href="/">Back to Dashboard</a></p>
        </div>
        """

# ========== SEARCH ROUTES ==========

@main_bp.route('/search')
@add_security_headers()
@require_auth()
def search_emails():
    """Email search functionality"""
    try:
        query = request.args.get('q', '')
        category = request.args.get('category', '')

        if not query:
            return render_template('search.html', emails=[], query='', category='')

        # Basic search implementation
        search_query = db.session.query(ClassifiedEmail, Email).join(Email)
        search_query = search_query.filter(
            db.or_(
                Email.subject.contains(query),
                Email.body_cleaned.contains(query) if hasattr(Email, 'body_cleaned') else Email.subject.contains(query)
            )
        )

        if category:
            search_query = search_query.filter(ClassifiedEmail.category == category)

        results = search_query.order_by(Email.received_at.desc()).limit(50).all()

        return render_template('search.html',
                             emails=results,
                             query=query,
                             category=category)

    except Exception as e:
        logger.error(f"Search error: {e}")
        return f"""
        <div style="padding: 20px; font-family: Arial;">
            <h1>Search</h1>
            <p>Error: {str(e)}</p>
            <p><a href="/">Back to Dashboard</a></p>
        </div>
        """

# ========== REPORTS ROUTES ==========

@main_bp.route('/reports')
@add_security_headers()
def reports():
    """Enhanced reports and analytics page with real data"""
    try:
        # Import and use ReportsService
        from app.services.reports_service import ReportsService

        reports_service = ReportsService()
        report_data = reports_service.get_reports_data()

        # Ensure demo mode is off
        report_data['is_demo_data'] = False

        print(f"📊 DEBUG: Sending {len(report_data.get('daily_volumes', []))} volume entries to template")

        return render_template('reports.html', **report_data)

    except Exception as e:
        logger.error(f"Reports error: {e}")
        import traceback
        traceback.print_exc()

        # Fallback
        return render_template('reports.html',
                             daily_volumes=[],
                             total_emails=0,
                             is_demo_data=False,
                             category_stats=[],
                             priority_stats=[],
                             email_gap={'show_historical_button': True, 'message': f'Error: {str(e)}'})

# ========== DRAFTS ROUTES ==========

@main_bp.route('/drafts')
@add_security_headers()
def drafts_list():
    """Show all saved drafts"""
    try:
        if not HAS_DRAFTS_SERVICE:
            flash('Drafts feature not available', 'info')
            return redirect(url_for('main.dashboard'))

        drafts_service = DraftsService()
        drafts = drafts_service.get_drafts()

        # Organize drafts by type
        compose_drafts = [d for d in drafts if d.get('draft_type') == 'compose']
        reply_drafts = [d for d in drafts if d.get('draft_type') in ['reply', 'forward']]

        return render_template('drafts_list.html',
                             compose_drafts=compose_drafts,
                             reply_drafts=reply_drafts,
                             total_drafts=len(drafts))
    except Exception as e:
        logger.error(f"Drafts list error: {e}")
        flash('Error loading drafts', 'error')
        return redirect(url_for('main.dashboard'))

@main_bp.route('/drafts/<int:draft_id>')
@add_security_headers()
def view_draft(draft_id):
    """View/edit a specific draft"""
    try:
        if not HAS_DRAFTS_SERVICE:
            flash('Drafts feature not available', 'info')
            return redirect(url_for('main.dashboard'))

        drafts_service = DraftsService()
        draft = drafts_service.get_draft(draft_id)

        if not draft:
            flash('Draft not found', 'error')
            return redirect(url_for('main.drafts_list'))

        # Redirect to appropriate compose/reply form with draft data
        if draft.get('draft_type') == 'compose':
            return render_template('compose_email.html', draft=draft)
        elif draft.get('draft_type') in ['reply', 'forward']:
            # Get original email for context
            original_email = Email.query.get(draft.get('original_email_id'))
            if original_email:
                return render_template('reply_form.html', draft=draft, email=original_email)

        flash('Invalid draft type', 'error')
        return redirect(url_for('main.drafts_list'))

    except Exception as e:
        logger.error(f"View draft error: {e}")
        flash('Error loading draft', 'error')
        return redirect(url_for('main.drafts_list'))

@main_bp.route('/drafts/<int:draft_id>/delete', methods=['POST'])
@add_security_headers()
def delete_draft(draft_id):
    """Delete a draft"""
    try:
        if not HAS_DRAFTS_SERVICE:
            return redirect(url_for('main.dashboard'))

        drafts_service = DraftsService()
        result = drafts_service.delete_draft(draft_id)

        if result.get('success'):
            flash('Draft deleted successfully', 'success')
        else:
            flash(result.get('message', 'Error deleting draft'), 'error')

        return redirect(url_for('main.drafts_list'))

    except Exception as e:
        logger.error(f"Delete draft error: {e}")
        flash('Error deleting draft', 'error')
        return redirect(url_for('main.drafts_list'))

# ========== COMPOSE ROUTES ==========

@main_bp.route('/compose')
@add_security_headers()
def compose():
    """Show compose email form"""
    try:
        # Check if email blueprint is available
        return redirect(url_for('email.compose'))
    except:
        # Fallback if email routes not available
        return render_template('compose_email.html')

# ========== PROCESSING ROUTES ==========

@main_bp.route('/processing')
@add_security_headers()
def processing():
    """Email processing management page"""
    try:
        return render_template('processing.html')
    except Exception as e:
        logger.error(f"Processing page error: {e}")
        return f"""
        <div style="padding: 20px; font-family: Arial;">
            <h1>Email Processing</h1>
            <p>Processing management temporarily unavailable</p>
            <p><a href="/">Back to Dashboard</a></p>
        </div>
        """

# ========== GMAIL OAUTH ROUTES ==========

@main_bp.route('/authorize')
@add_security_headers()
def authorize_gmail():
    """Start Gmail OAuth authorization flow"""
    try:
        from google_auth_oauthlib.flow import Flow

        credentials_path = '/home/MikeAubry02025/email_agent/credentials/credentials.json'
        if not os.path.exists(credentials_path):
            flash('Gmail credentials file not found', 'error')
            return redirect(url_for('main.dashboard'))

        flow = Flow.from_client_secrets_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/gmail.readonly',
                   'https://www.googleapis.com/auth/gmail.send'],
            redirect_uri='https://mikeaubry02025.pythonanywhere.com/oauth2callback'
        )

        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )

        session['oauth_state'] = state
        return redirect(authorization_url)

    except Exception as e:
        logger.error(f"Gmail authorization error: {e}")
        flash(f'Gmail authorization failed: {str(e)}', 'error')
        return redirect(url_for('main.dashboard'))

@main_bp.route('/oauth2callback')
@add_security_headers()
def oauth2callback():
    """Handle Gmail OAuth callback"""
    try:
        from google_auth_oauthlib.flow import Flow
        import json

        state = session.get('oauth_state')
        if not state or request.args.get('state') != state:
            flash('Invalid OAuth state. Please try again.', 'error')
            return redirect(url_for('main.dashboard'))

        flow = Flow.from_client_secrets_file(
            '/home/MikeAubry02025/email_agent/credentials/credentials.json',
            scopes=['https://www.googleapis.com/auth/gmail.readonly',
                   'https://www.googleapis.com/auth/gmail.send'],
            redirect_uri='https://mikeaubry02025.pythonanywhere.com/oauth2callback',
            state=state
        )

        flow.fetch_token(authorization_response=request.url)
        credentials = flow.credentials

        # Save token
        token_data = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }

        token_path = '/home/MikeAubry02025/email_agent/credentials/token.json'
        os.makedirs(os.path.dirname(token_path), exist_ok=True)
        with open(token_path, 'w') as token_file:
            json.dump(token_data, token_file)

        flash('✅ Gmail authorization completed successfully!', 'success')
        session.pop('oauth_state', None)
        return redirect(url_for('main.oauth_success'))

    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        flash(f'Gmail authorization failed: {str(e)}', 'error')
        session.pop('oauth_state', None)
        return redirect(url_for('main.dashboard'))

@main_bp.route('/oauth_success')
@add_security_headers()
def oauth_success():
    """OAuth success page"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Gmail Authorization Successful</title>
        <style>
            body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
            .success {{ color: green; font-size: 24px; margin: 20px; }}
            .btn {{ display: inline-block; padding: 10px 20px; margin: 10px;
                    background: #007bff; color: white; text-decoration: none;
                    border-radius: 5px; }}
            .btn:hover {{ background: #0056b3; }}
        </style>
    </head>
    <body>
        <h1>🎉 Gmail Authorization Successful!</h1>
        <div class="success">✅ Your Gmail account is now connected</div>
        <a href="/dashboard" class="btn">📊 Go to Dashboard</a>
    </body>
    </html>
    """

# ========== UTILITY ROUTES ==========

@main_bp.route('/favicon.ico')
@add_security_headers()
def favicon():
    """Serve favicon"""
    try:
        return send_from_directory(
            os.path.join(main_bp.root_path, '..', 'static'),
            'favicon.ico',
            mimetype='image/vnd.microsoft.icon'
        )
    except:
        return Response(status=204)

# ========== REDIRECT ROUTES ==========

@main_bp.route('/reply/<int:email_id>')
@add_security_headers()
@require_auth()
def reply_email(email_id):
    """Redirect to email reply form"""
    try:
        # Check if email blueprint is available
        return redirect(url_for('email.reply_form', email_id=email_id))
    except:
        # Fallback if email routes not available
        flash('Reply feature temporarily unavailable', 'info')
        return redirect(url_for('main.view_email', email_id=email_id))

@main_bp.route('/send_test_emails', methods=['POST'])
@add_security_headers()
def send_test_emails():
    """Send actual test emails to Gmail inbox for classification testing"""
    try:
        from datetime import datetime
        from flask import redirect, url_for, flash
        import time

        # Import your email processor
        try:
            from app.email_processor import EmailProcessor
            email_processor = EmailProcessor()
        except ImportError:
            flash("Email processor not available", "error")
            return redirect(url_for('main.populate'))

        # Check Gmail authentication
        if not email_processor.authenticate_gmail():
            flash("Gmail authentication failed. Please authorize Gmail access first.", "error")
            return redirect(url_for('main.authorize_gmail'))

        # Get your Gmail address (recipient)
        try:
            gmail_service = email_processor.gmail_service
            profile = gmail_service.users().getProfile(userId='me').execute()
            your_email = profile.get('emailAddress')
            print(f"Sending test emails to: {your_email}")
        except Exception as e:
            flash(f"Could not get Gmail profile: {e}", "error")
            return redirect(url_for('main.populate'))

        # Test email templates for different categories
        test_emails = [
            {
                'from_name': 'John Smith',
                'from_email': 'john.smith.leads@example.com',
                'subject': 'Interested in Your Property Listing - 123 Main St',
                'body': '''Hi there,

I saw your listing for 123 Main Street and I'm very interested. Could we schedule a viewing this week? I'm pre-approved for financing and ready to move quickly.

My budget is around $450,000 and I love the neighborhood. Please let me know your availability.

Best regards,
John Smith
Phone: (555) 123-4567'''
            },
            {
                'from_name': 'Sarah Johnson',
                'from_email': 'sarah.johnson.client@example.com',
                'subject': 'Maintenance Request - Leaky Faucet at 456 Oak Ave',
                'body': '''Hello,

I'm having an issue with the kitchen faucet at 456 Oak Avenue. It's been dripping constantly for the past few days and seems to be getting worse.

Could you please arrange for a plumber to come take a look? I'm available most weekdays after 3 PM or weekends.

Thank you,
Sarah Johnson
Tenant at 456 Oak Ave
Phone: (555) 987-6543'''
            },
            {
                'from_name': 'Mike Wilson',
                'from_email': 'mike.wilson.offer@example.com',
                'subject': 'URGENT: Counter Offer for 789 Pine Street',
                'body': '''Dear Agent,

I'm submitting a counter offer for the property at 789 Pine Street:

Original asking price: $525,000
My offer: $510,000
Closing date: 30 days
Inspection contingency: 7 days

This is a cash offer with proof of funds attached. Please respond by end of business today as I have other properties under consideration.

Mike Wilson
Real Estate Investor
Phone: (555) 246-8135'''
            },
            {
                'from_name': 'Emergency Alert System',
                'from_email': 'alerts@propertysystem.com',
                'subject': 'CRITICAL: Water Damage Reported at 321 Elm Street',
                'body': '''CRITICAL ALERT - IMMEDIATE ACTION REQUIRED

Property: 321 Elm Street
Issue: Water damage reported in basement
Reported by: Tenant (Jane Doe)
Time: ''' + datetime.now().strftime('%Y-%m-%d %H:%M') + '''

Description: Tenant reports significant water in basement, possibly from burst pipe. Damage to personal belongings already occurring.

IMMEDIATE ACTIONS NEEDED:
1. Contact emergency plumber immediately
2. Arrange temporary housing for tenant if needed
3. Contact insurance company
4. Document damage with photos

Tenant contact: (555) 555-5555

This is an automated alert. Please respond immediately.'''
            },
            {
                'from_name': 'Property Management Co',
                'from_email': 'billing@propertymanagement.com',
                'subject': 'Monthly Rental Statement - Multiple Properties',
                'body': '''Monthly Rental Income Statement

Period: ''' + datetime.now().strftime('%B %Y') + '''

INCOME RECEIVED:
- 123 Main St: $2,200 (On time)
- 456 Oak Ave: $1,800 (On time)
- 789 Pine St: $2,500 (3 days late)
- 321 Elm St: $1,900 (On time)

TOTAL COLLECTED: $8,400
OUTSTANDING: $0

MAINTENANCE EXPENSES:
- 456 Oak Ave plumbing: $150
- 123 Main St landscaping: $75

NET INCOME: $8,175

Full report attached. Please review and contact us with any questions.

Property Management Team'''
            }
        ]

        sent_count = 0
        errors = []

        for i, email_template in enumerate(test_emails):
            try:
                # Add timestamp to make each email unique
                timestamp = datetime.now().strftime('%H:%M:%S')
                subject = f"[TEST {i+1}] {email_template['subject']} - {timestamp}"

                # Create the email content
                message_body = f"""FROM: {email_template['from_name']} <{email_template['from_email']}>
TO: {your_email}
SUBJECT: {email_template['subject']}

{email_template['body']}

---
[This is a test email generated for AI classification testing at {datetime.now()}]"""

                # Send the email using your email processor
                success = email_processor.send_enhanced_email(
                    to_email=your_email,
                    subject=subject,
                    message_body=message_body,
                    reply_type='compose'
                )

                if success:
                    sent_count += 1
                    print(f"✅ Sent test email {i+1}: {subject}")
                    # Small delay between emails
                    time.sleep(2)
                else:
                    errors.append(f"Failed to send email {i+1}")

            except Exception as e:
                error_msg = f"Error sending email {i+1}: {str(e)}"
                errors.append(error_msg)
                print(f"❌ {error_msg}")

        # Report results
        if sent_count > 0:
            success_msg = f"Successfully sent {sent_count} test emails to your Gmail inbox!"
            if errors:
                success_msg += f" ({len(errors)} errors occurred)"
            flash(success_msg, "success")
        else:
            flash(f"Failed to send test emails. Errors: {'; '.join(errors[:2])}", "error")

        return redirect(url_for('main.dashboard'))

    except Exception as e:
        flash(f"Error sending test emails: {str(e)}", "error")
        return redirect(url_for('main.populate'))


@main_bp.route('/populate')
@add_security_headers()
def populate():
    """Show Gmail test email populator interface"""
    return render_template('test_data_populator.html')

@main_bp.route('/run_test_populator', methods=['POST'])
@add_security_headers()
def run_test_populator():
    """Send realistic test emails to Gmail inbox for import and classification"""
    try:
        from datetime import datetime
        from flask import redirect, url_for, flash
        import time

        # YOUR GMAIL ADDRESS - REPLACE THIS WITH YOUR ACTUAL EMAIL
        your_email = "mikeaubry2025@gmail.com"

        # Import your email processor
        try:
            from app.email_processor import EmailProcessor
            email_processor = EmailProcessor()
        except ImportError:
            flash("Email processor not available. Please check your email processing setup.", "error")
            return redirect(url_for('main.populate'))

        # Check Gmail authentication
        if not email_processor.authenticate_gmail():
            flash("Gmail authentication failed. Please authorize Gmail access first.", "error")
            return redirect(url_for('main.authorize_gmail'))

        print(f"Sending test emails to: {your_email}")

        # Realistic test email templates for property management scenarios
        test_emails = [
            {
                'subject': 'Interested in 123 Oak Street Property',
                'body': '''Hello,

I hope this email finds you well. I came across your listing for 123 Oak Street and I'm very interested in scheduling a viewing.

A bit about me: I'm a software engineer relocating to the area for work. I'm pre-approved for a mortgage up to $475,000 and looking to close within 45 days if possible.

The property seems perfect for my needs - I especially love the updated kitchen and the proximity to downtown. Could we arrange a viewing this weekend? I'm flexible with timing.

I'm also curious about:
- Property taxes for this year
- Any recent renovations or repairs
- Neighborhood parking situation

Thank you for your time, and I look forward to hearing from you soon.

Best regards,
Jennifer Martinez
Phone: (555) 123-4567
Email: jennifer.martinez.leads@example.com'''
            },
            {
                'subject': 'Urgent: Heating System Issue at 456 Pine Avenue',
                'body': '''Hi,

I hope you can help me with an urgent issue. The heating system at 456 Pine Avenue (Unit 2B) stopped working yesterday evening.

Details of the problem:
- Thermostat shows "Error Code E3"
- No heat coming from any vents
- System makes clicking noises when trying to start
- Outside temperature dropped to 32°F last night

I tried the basic troubleshooting steps you provided (checking circuit breakers, replacing thermostat batteries), but nothing worked.

Could you please send a technician as soon as possible? I work from home and really need the heat restored. I'm available anytime today and tomorrow.

Thanks for your quick attention to this matter.

David Chen
Tenant - 456 Pine Avenue, Unit 2B
Phone: (555) 987-6543
Lease signed: March 2023'''
            },
            {
                'subject': 'Cash Offer - 789 Maple Drive ($485,000)',
                'body': '''Dear Property Manager,

I am writing to submit a formal cash offer for 789 Maple Drive.

OFFER DETAILS:
Purchase Price: $485,000 (cash)
Closing Timeline: 21 days
Inspection Period: 7 days
Earnest Money: $25,000 (ready to wire)

BUYER QUALIFICATIONS:
- Proof of funds available immediately
- No financing contingencies
- Local real estate investor with 12+ properties
- Excellent references available

This property fits perfectly into my rental portfolio. I've done extensive research on comparable sales and believe this is a fair market offer given current conditions.

I can provide proof of funds within 2 hours of acceptance. Please let me know if you need any additional documentation or have questions about the offer terms.

Time is important to me - I have other properties under consideration, so I'd appreciate a response by Thursday 5 PM.

Thank you for your consideration.

Best regards,
Rebecca Thompson
Thompson Property Investments, LLC
Phone: (555) 246-8135
investor.rebecca@example.com'''
            },
            {
                'subject': 'CRITICAL ALERT: Water Leak Detected - 321 Elm Street',
                'body': '''*** CRITICAL PROPERTY ALERT ***

PROPERTY: 321 Elm Street, Unit 1A
ALERT TYPE: Water Leak Detection
SEVERITY: HIGH PRIORITY
TIMESTAMP: ''' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '''

DETAILS:
- Water sensor activated in basement utility room
- Continuous water flow detected for 47 minutes
- Estimated leak rate: 5+ gallons per hour
- Temperature: Normal (no freeze concern)

TENANT STATUS:
- Tenant notified automatically
- Tenant confirms visible water accumulation
- Personal belongings at risk

IMMEDIATE ACTION REQUIRED:
1. Contact emergency plumber immediately
2. Shut off main water supply if possible
3. Arrange water extraction service
4. Document damage for insurance
5. Check neighboring units for damage

EMERGENCY CONTACTS:
- Tenant: Sarah Williams (555) 555-5555
- Emergency Plumber: AquaFix Services (555) 911-PIPE
- Insurance: PropertyGuard Insurance (555) 123-CLAIM

This is an automated alert from your property monitoring system.
DO NOT REPLY to this email. Contact the monitoring center at (555) 911-PROP for assistance.

*** END ALERT ***'''
            },
            {
                'subject': 'Monthly Maintenance Report - Multiple Properties',
                'body': '''Monthly Property Maintenance Summary
Report Period: ''' + datetime.now().strftime('%B %Y') + '''

COMPLETED WORK ORDERS:

123 Oak Street:
- Replaced kitchen faucet aerator ($15 parts, 1hr labor)
- Fixed squeaky front door hinges ($8 WD-40)
- Cleaned gutters and downspouts (2hrs labor)
Status: All issues resolved

456 Pine Avenue:
- Repaired bathroom tile grout (Unit 2B) ($45 materials, 3hrs)
- Replaced air filter in HVAC system ($25)
- Fixed loose handrail on stairs ($12 screws, 1hr)
Status: All issues resolved

MONTHLY TOTALS:
Materials/Parts: $340
Labor Hours: 12 hours
Emergency Calls: 0
Tenant Satisfaction: 4.8/5 (based on follow-up calls)

UPCOMING MAINTENANCE:
- Quarterly pest control scheduled for all properties
- Spring landscaping planning needed
- Two properties due for exterior power washing

Please let me know if you have questions about any of these items.

Mike Rodriguez
Property Maintenance Coordinator
Phone: (555) 444-WORK
mike.maintenance@email.com'''
            },
            {
                'subject': 'Notice: Moving Out - 30 Day Notice for 123 Oak Street',
                'body': '''Dear Property Management,

I am writing to provide formal notice that I will be vacating my apartment at 123 Oak Street, Unit 3A, effective ''' + (datetime.now().replace(day=28) if datetime.now().day < 28 else datetime.now().replace(month=datetime.now().month+1, day=28)).strftime('%B %d, %Y') + '''.

This letter serves as my 30-day notice as required by the lease agreement.

MOVE-OUT DETAILS:
Current Address: 123 Oak Street, Unit 3A
Move-out Date: ''' + (datetime.now().replace(day=28) if datetime.now().day < 28 else datetime.now().replace(month=datetime.now().month+1, day=28)).strftime('%B %d, %Y') + '''
Security Deposit: $1,200 (paid March 2023)

REASON FOR MOVING:
I've been offered a great job opportunity in another state that I cannot pass up. I've really enjoyed living here and appreciate your responsiveness to maintenance requests.

Please confirm receipt of this notice and let me know the next steps for the move-out process. I want to ensure everything goes smoothly and that I receive my security deposit back promptly.

Thank you for being great landlords.

Best regards,
Lisa Park
Current Tenant - 123 Oak Street, Unit 3A
Phone: (555) 789-0123
lease.lisa.park@email.com'''
            }
        ]

        sent_count = 0
        errors = []

        for i, email_template in enumerate(test_emails):
            try:
                subject = email_template['subject']
                body = email_template['body']

                # Send the email using your email processor
                success = email_processor.send_enhanced_email(
                    to_email=your_email,
                    subject=subject,
                    message_body=body,
                    reply_type='compose'
                )

                if success:
                    sent_count += 1
                    print(f"✅ Sent test email {i+1}: {subject}")
                    # Small delay between emails to avoid rate limiting
                    time.sleep(3)
                else:
                    errors.append(f"Failed to send email {i+1}: {subject}")

            except Exception as e:
                error_msg = f"Error sending email {i+1}: {str(e)}"
                errors.append(error_msg)
                print(f"❌ {error_msg}")

        # Report results
        if sent_count > 0:
            success_msg = f"Successfully sent {sent_count} test emails to {your_email}! Check your Gmail inbox in a few minutes, then run 'Process New Emails' to import and classify them."
            if errors:
                success_msg += f" ({len(errors)} emails failed to send)"
            flash(success_msg, "success")
        else:
            flash(f"Failed to send test emails. Errors: {'; '.join(errors[:2])}", "error")

        return redirect(url_for('main.dashboard'))

    except Exception as e:
        flash(f"Error sending test emails: {str(e)}", "error")
        return redirect(url_for('main.populate'))