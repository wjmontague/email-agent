from flask import Blueprint, request, jsonify
from app.secure_auth_decorator import require_auth, add_security_headers

api_bp = Blueprint('api', __name__)

@api_bp.route('/urgent_counts')
@add_security_headers()
def get_urgent_counts():
    """Get current urgent counts"""
    try:
        # Use consistent import with main_routes.py
        try:
            from app.database_models import ClassifiedEmail
        except ImportError:
            # Fallback to models if database_models doesn't exist
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
        
    except Exception as e:
        print(f"Database error: {e}")
        return jsonify({
            'critical': 0,
            'high': 0,
            'unread': 0,
            'requires_action': 0
        })

@api_bp.route('/mark_read/<int:email_id>', methods=['POST'])
@add_security_headers()
def mark_read_basic(email_id):
    """Mark email as read"""
    try:
        # Use consistent imports
        try:
            from app.database_models import ClassifiedEmail, db
        except ImportError:
            from app.models import ClassifiedEmail
            from app import db
        
        classified = ClassifiedEmail.query.filter_by(email_id=email_id).first()
        if classified and not classified.is_read:
            classified.is_read = True
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': 'Email marked as read'
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
def mark_replied_basic(email_id):
    """Mark email as replied"""
    try:
        try:
            from app.database_models import ClassifiedEmail, db
        except ImportError:
            from app.models import ClassifiedEmail
            from app import db
        
        classified = ClassifiedEmail.query.filter_by(email_id=email_id).first()
        if classified:
            classified.is_read = True
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

@api_bp.route('/process_emails', methods=['POST'])
@add_security_headers()
def process_emails():
    """Process new emails from Gmail inbox"""
    try:
        print("=== PROCESSING NEW EMAILS API CALLED ===")
        
        # Import processing service
        try:
            from app.services.processing_service import ProcessingService
            processing_service = ProcessingService()
            print("✅ Using ProcessingService")
        except ImportError as e:
            print(f"ProcessingService not available ({e}), using EmailProcessor")
            # Fallback: import email processor directly
            try:
                from app.email_processor import EmailProcessor
                email_processor = EmailProcessor()
                
                # Process emails directly
                result = email_processor.process_new_emails(hours_back=24)
                print(f"✅ EmailProcessor result: {result}")
                return jsonify(result)
                
            except ImportError as e2:
                print(f"EmailProcessor also not available: {e2}")
                return jsonify({
                    'status': 'error',
                    'message': f'Email processing components not available: {e2}',
                    'processed': 0,
                    'new': 0,
                    'errors': 1
                })
        
        # Use processing service
        result = processing_service.process_new_emails(hours_back=24)
        print(f"✅ ProcessingService result: {result}")
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Process emails error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'processed': 0,
            'new': 0,
            'errors': 1
        })

@api_bp.route('/process_emails_historical', methods=['POST'])
@add_security_headers()
def process_emails_historical():
    """Process historical emails (last 2 months)"""
    try:
        print("=== PROCESSING HISTORICAL EMAILS API CALLED ===")
        
        # Import processing service
        try:
            from app.services.processing_service import ProcessingService
            processing_service = ProcessingService()
            print("✅ Using ProcessingService for historical")
        except ImportError as e:
            print(f"ProcessingService not available ({e}), using EmailProcessor")
            # Fallback: import email processor directly
            try:
                from app.email_processor import EmailProcessor
                email_processor = EmailProcessor()
                
                # Start background processing
                import threading
                def background_process():
                    try:
                        result = email_processor.process_new_emails(hours_back=1440)  # 60 days
                        print(f"Historical processing completed: {result}")
                    except Exception as e:
                        print(f"Historical processing error: {e}")
                
                thread = threading.Thread(target=background_process)
                thread.start()
                
                return jsonify({'status': 'processing_started'})
                
            except ImportError as e2:
                print(f"EmailProcessor also not available: {e2}")
                return jsonify({
                    'status': 'error',
                    'message': f'Email processing components not available: {e2}'
                })
        
        # Use processing service
        result = processing_service.process_historical_emails(hours_back=1440)
        print(f"✅ Historical ProcessingService result: {result}")
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Process historical emails error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@api_bp.route('/processing_status', methods=['GET'])
@add_security_headers()
def processing_status():
    """Get current processing status"""
    try:
        # Check if processing is active
        try:
            from app.services.processing_service import ProcessingService
            processing_service = ProcessingService()
            
            # Check if processing is active
            is_processing = hasattr(processing_service, '_processing_active') and processing_service._processing_active
            
            return jsonify({
                'is_processing': is_processing,
                'status': 'active' if is_processing else 'idle'
            })
            
        except ImportError:
            # Fallback: assume not processing
            return jsonify({
                'is_processing': False,
                'status': 'idle'
            })
        
    except Exception as e:
        print(f"Processing status error: {e}")
        return jsonify({
            'is_processing': False,
            'status': 'error',
            'message': str(e)
        })

@api_bp.route('/test')
@add_security_headers()
def test_api():
    """Test endpoint"""
    return jsonify({
        'status': 'success',
        'message': 'API is working!',
        'timestamp': str(__import__('datetime').datetime.now())
    })