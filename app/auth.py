# app/auth.py - Authentication system with email-based password reset
import os
import secrets
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from dotenv import load_dotenv, set_key
import logging
from app.secure_auth_decorator import require_auth, add_security_headers

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

class AuthManager:
    """Handle authentication and password management"""

    def __init__(self):
        self.env_file_path = '/home/MikeAubry02025/email_agent/.env'
        load_dotenv(self.env_file_path)

    def hash_password(self, password: str) -> str:
        """Create a secure hash of the password"""
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_credentials(self, username: str, password: str) -> bool:
        """Verify username and password against .env file"""
        try:
            env_username = os.environ.get('ADMIN_USERNAME')
            env_password_hash = os.environ.get('ADMIN_PASSWORD_HASH')

            if not env_username or not env_password_hash:
                logger.error("Admin credentials not found in .env file")
                return False

            # Check username
            if username != env_username:
                return False

            # Check password hash
            password_hash = self.hash_password(password)
            return password_hash == env_password_hash

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False

    def update_password(self, new_password: str) -> bool:
        """Update password in .env file"""
        try:
            new_hash = self.hash_password(new_password)

            # Update the .env file
            set_key(self.env_file_path, 'ADMIN_PASSWORD_HASH', new_hash)

            # Reload environment variables
            load_dotenv(self.env_file_path, override=True)

            logger.info("Password updated successfully")
            return True

        except Exception as e:
            logger.error(f"Error updating password: {e}")
            return False

    def generate_reset_token(self) -> str:
        """Generate a secure reset token"""
        token = secrets.token_urlsafe(32)

        # Store token in .env with expiration (24 hours)
        expiry = datetime.now() + timedelta(hours=24)
        set_key(self.env_file_path, 'RESET_TOKEN', token)
        set_key(self.env_file_path, 'RESET_TOKEN_EXPIRY', expiry.isoformat())

        # Reload environment
        load_dotenv(self.env_file_path, override=True)

        return token

    def verify_reset_token(self, token: str) -> bool:
        """Verify reset token is valid and not expired"""
        try:
            stored_token = os.environ.get('RESET_TOKEN')
            expiry_str = os.environ.get('RESET_TOKEN_EXPIRY')

            if not stored_token or not expiry_str:
                return False

            if token != stored_token:
                return False

            # Check expiration
            expiry = datetime.fromisoformat(expiry_str)
            if datetime.now() > expiry:
                logger.info("Reset token expired")
                return False

            return True

        except Exception as e:
            logger.error(f"Error verifying reset token: {e}")
            return False

    def send_reset_email(self, reset_token: str) -> bool:
        """Send password reset email using Gmail API"""
        try:
            from app.email_processor import EmailProcessor

            processor = EmailProcessor()
            if not processor.authenticate_gmail():
                logger.error("Gmail authentication failed for password reset")
                return False

            # Create reset link
            reset_url = f"https://mikeaubry02025.pythonanywhere.com/auth/reset-password?token={reset_token}"

            # Email content
            subject = "Email Agent - Password Reset Request"
            message_body = f"""
Hello Michael,

You have requested a password reset for your Email AI Agent dashboard.

Click the link below to reset your password:
{reset_url}

This link will expire in 24 hours.

If you did not request this password reset, please ignore this email.

Best regards,
Email AI Agent System
            """

            # Send email
            success = processor.send_reply(
                to_email="mikeaubry2025@gmail.com",
                subject=subject,
                message_body=message_body
            )

            if success:
                logger.info("Password reset email sent successfully")
            else:
                logger.error("Failed to send password reset email")

            return success

        except Exception as e:
            logger.error(f"Error sending reset email: {e}")
            return False

# Create auth manager instance
auth_manager = AuthManager()

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
@add_security_headers()
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if auth_manager.verify_credentials(username, password):
            session['logged_in'] = True
            session['username'] = username
            session.permanent = True
            logger.info(f"Successful login for user: {username}")
            flash('Login successful!', 'success')

            # 🔧 FIX: Change from 'dashboard' to 'main.dashboard'
            return redirect(url_for('main.dashboard'))  # ← This line

        else:
            logger.warning(f"Failed login attempt for user: {username}")
            flash('Invalid username or password', 'error')

    return render_template('auth/login.html')

@auth_bp.route('/logout')
@add_security_headers()
def logout():
    """Logout route"""
    username = session.get('username', 'Unknown')
    session.clear()
    logger.info(f"User logged out: {username}")
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
@add_security_headers()
def forgot_password():
    """Forgot password page"""
    if request.method == 'POST':
        # Generate reset token
        reset_token = auth_manager.generate_reset_token()

        # Send reset email
        if auth_manager.send_reset_email(reset_token):
            flash('Password reset email sent! Check your email for instructions.', 'success')
            logger.info("Password reset email sent")
        else:
            flash('Error sending reset email. Please try again.', 'error')
            logger.error("Failed to send password reset email")

        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
@add_security_headers()
def reset_password():
    """Reset password with token"""
    token = request.args.get('token') or request.form.get('token')

    if not token:
        flash('Invalid reset link', 'error')
        return redirect(url_for('auth.login'))

    if not auth_manager.verify_reset_token(token):
        flash('Invalid or expired reset link', 'error')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if not new_password or len(new_password) < 8:
            flash('Password must be at least 8 characters long', 'error')
            return render_template('auth/reset_password.html', token=token)

        if new_password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('auth/reset_password.html', token=token)

        # Update password
        if auth_manager.update_password(new_password):
            # Clear reset token
            set_key(auth_manager.env_file_path, 'RESET_TOKEN', '')
            set_key(auth_manager.env_file_path, 'RESET_TOKEN_EXPIRY', '')

            flash('Password updated successfully! You can now log in with your new password.', 'success')
            logger.info("Password reset completed successfully")
            return redirect(url_for('auth.login'))
        else:
            flash('Error updating password. Please try again.', 'error')

    return render_template('auth/reset_password.html', token=token)

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change password while logged in"""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # Verify current password
        username = session.get('username')
        if not auth_manager.verify_credentials(username, current_password):
            flash('Current password is incorrect', 'error')
            return render_template('auth/change_password.html')

        if not new_password or len(new_password) < 8:
            flash('New password must be at least 8 characters long', 'error')
            return render_template('auth/change_password.html')

        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return render_template('auth/change_password.html')

        # Update password
        if auth_manager.update_password(new_password):
            flash('Password changed successfully!', 'success')
            logger.info(f"Password changed for user: {username}")

            # 🔧 FIX: Change from 'dashboard' to 'main.dashboard'
            return redirect(url_for('main.dashboard'))  # ← This line

        else:
            flash('Error changing password. Please try again.', 'error')

    return render_template('auth/change_password.html')