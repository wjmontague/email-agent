from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, abort
from app.auth import login_required
from app.database_models import Email, ClassifiedEmail
from app.services.email_service import EmailService
import logging
import os

logger = logging.getLogger(__name__)
email_bp = Blueprint('email', __name__)

@email_bp.route('/compose')
@login_required
def compose():
    """Show compose email form"""
    return render_template('compose_email.html')

@email_bp.route('/reply/<int:email_id>')
@login_required
def reply_form(email_id):
    """Show reply form for an email"""
    try:
        email_service = EmailService()
        reply_data = email_service.prepare_reply_data(email_id)
        return render_template('reply_form.html', **reply_data)
    except Exception as e:
        logger.error(f"Reply form error: {e}")
        return render_template('error.html', error=str(e))

@email_bp.route('/forward/<int:email_id>')
@login_required
def forward(email_id):
    """Show forward form for an email"""
    try:
        email_service = EmailService()
        forward_data = email_service.prepare_forward_data(email_id)
        return render_template('forward_form.html', **forward_data)
    except Exception as e:
        logger.error(f"Forward form error: {e}")
        return render_template('error.html', error=str(e))

@email_bp.route('/send', methods=['POST'])
@login_required
def send_email():
    """Send a new email with CC/BCC support"""
    try:
        email_service = EmailService()
        result = email_service.send_email_from_form(request.form, request.files)
        if result['success']:
            flash(result['message'], 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash(result['message'], 'error')
            return redirect(url_for('email.compose'))
    except Exception as e:
        logger.error(f"Send email error: {e}")
        flash(f'Error sending email: {str(e)}', 'error')
        return redirect(url_for('email.compose'))

@email_bp.route('/send_reply', methods=['POST'])
@login_required
def send_reply():
    """Send email reply with CC/BCC support"""
    try:
        email_service = EmailService()
        result = email_service.send_reply_from_form(request.form, request.files)
        if result['success']:
            flash(result['message'], 'success')
            return redirect(url_for('main.view_email', email_id=result['original_email_id']))
        else:
            flash(result['message'], 'error')
            return redirect(url_for('email.reply_form', email_id=result['original_email_id']))
    except Exception as e:
        logger.error(f"Send reply error: {e}")
        flash(f'Error sending reply: {str(e)}', 'error')
        return redirect(url_for('main.dashboard'))

@email_bp.route('/attachment/<path:filename>')
@login_required
def serve_attachment(filename):
    """Serve attachment files securely"""
    try:
        email_service = EmailService()
        filepath = email_service.validate_and_get_attachment_path(filename)
        return send_file(filepath, as_attachment=True)
    except PermissionError:
        abort(403)
    except FileNotFoundError:
        abort(404)
    except Exception as e:
        logger.error(f"Error serving attachment {filename}: {e}")
        abort(500)
