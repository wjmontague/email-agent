from flask import Blueprint, render_template, request, jsonify
from app.services.email_helper_service import EmailHelperService
from app.secure_auth_decorator import require_auth, add_security_headers
import logging

logger = logging.getLogger(__name__)
helper_bot_bp = Blueprint('helper_bot', __name__)

@helper_bot_bp.route('/email-helper')
@add_security_headers()
@require_auth()
def email_helper():
    """Email learning assistant - full screen chatbot"""
    return render_template('email_helper.html')

@helper_bot_bp.route('/email-helper-chat', methods=['POST'])
@add_security_headers()
@require_auth()
def email_helper_chat():
    """Process chat messages from the email helper bot"""
    try:
        data = request.json
        user_question = data.get('question', '').strip()
        language_code = data.get('language', 'en')

        if not user_question:
            return jsonify({'answer': 'Please provide a question.'}), 400

        # Initialize the email helper service
        helper_service = EmailHelperService()
        answer = helper_service.get_answer(user_question, language_code)

        return jsonify({'answer': answer})

    except Exception as e:
        logger.error(f"Email helper chat error: {e}")
        return jsonify({'answer': f'Sorry, I encountered an error: