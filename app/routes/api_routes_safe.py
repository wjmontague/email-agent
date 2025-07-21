from flask import Blueprint, request, jsonify
from app.secure_auth_decorator import require_auth, add_security_headers

api_bp = Blueprint('api', __name__)

@api_bp.route('/urgent_counts')
@add_security_headers()
def get_urgent_counts():
    """Get current urgent counts - safe fallback version"""
    try:
        # Try to import and use state manager safely
        from app.email_state_manager import get_state_manager
        state_manager = get_state_manager()
        
        if state_manager.is_available():
            return jsonify(state_manager.get_current_counts())
        else:
            raise Exception("State manager not available")
    except Exception as e:
        print(f"State manager error: {e}, using fallback")
        # Fallback: calculate counts directly from database
        try:
            from app.models import ClassifiedEmail
            
            # Get actual counts from database
            critical_count = ClassifiedEmail.query.filter_by(
                priority='Critical', is_read=False
            ).filter(
                (ClassifiedEmail.is_archived == False) | (ClassifiedEmail.is_archived == None)
            ).count()
            
            high_count = ClassifiedEmail.query.filter_by(
                priority='High', is_read=False
            ).filter(
                (ClassifiedEmail.is_archived == False) | (ClassifiedEmail.is_archived == None)
            ).count()
            
            unread_count = ClassifiedEmail.query.filter_by(
                is_read=False
            ).filter(
                (ClassifiedEmail.is_archived == False) | (ClassifiedEmail.is_archived == None)
            ).count()
            
            action_count = ClassifiedEmail.query.filter_by(
                requires_action=True, is_read=False
            ).filter(
                (ClassifiedEmail.is_archived == False) | (ClassifiedEmail.is_archived == None)
            ).count()
            
            return jsonify({
                'critical': critical_count,
                'high': high_count,
                'unread': unread_count,
                'requires_action': action_count
            })
        except Exception as db_error:
            print(f"Database error: {db_error}")
            return jsonify({
                'critical': 0,
                'high': 0,
                'unread': 0,
                'requires_action': 0
            })

@api_bp.route('/mark_read/<int:email_id>', methods=['POST'])
@add_security_headers()
def mark_read_safe(email_id):
    """Mark email as read - safe version"""
    try:
        from app.models import ClassifiedEmail, db
        
        classified = ClassifiedEmail.query.filter_by(email_id=email_id).first()
        if classified and not classified.is_read:
            classified.is_read = True
            db.session.commit()
            
            # Try to get updated counts
            try:
                from app.email_state_manager import get_state_manager
                state_manager = get_state_manager()
                if state_manager.is_available():
                    counts = state_manager.get_current_counts()
                else:
                    raise Exception("State manager not available")
            except:
                # Fallback to basic response
                counts = {'status': 'counts_unavailable'}
            
            return jsonify({
                'status': 'success',
                'message': 'Email marked as read',
                'counts': counts
            })
        else:
            return jsonify({
                'status': 'error', 
                'message': 'Email not found or already read'
            })
            
    except Exception as e:
        print(f"Error marking as read: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api_bp.route('/mark_replied/<int:email_id>', methods=['POST'])
@add_security_headers()
def mark_replied_safe(email_id):
    """Mark email as replied - safe version"""
    try:
        from app.models import ClassifiedEmail, db
        
        classified = ClassifiedEmail.query.filter_by(email_id=email_id).first()
        if classified:
            classified.is_read = True
            # Set replied if column exists
            if hasattr(classified, 'is_replied'):
                classified.is_replied = True
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': 'Email marked as replied'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Email not found'
            })
            
    except Exception as e:
        print(f"Error marking as replied: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api_bp.route('/test')
@add_security_headers()
def test_api():
    """Test endpoint to verify API is working"""
    return jsonify({
        'status': 'success',
        'message': 'API is working',
        'timestamp': str(__import__('datetime').datetime.now())
    })
