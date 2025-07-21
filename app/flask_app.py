import logging
from app import create_app, db  # Import both create_app AND db
from app.services.background_service import BackgroundService

# Configure logging
logging.basicConfig(level=logging.INFO)

# Create Flask app
app = create_app()

# Export db for use by scheduled tasks and other scripts
# This is what the scheduled task is looking for
__all__ = ['app', 'db']

if __name__ == '__main__':
    # Start background email processing
    try:
        background_service = BackgroundService()
        background_service.start()
    except Exception as e:
        logging.error(f"Failed to start background service: {e}")
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)