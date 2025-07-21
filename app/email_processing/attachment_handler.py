# app/email_processing/attachment_handler.py
import os
import re
import shutil
import logging
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class AttachmentHandler:
    """Handles attachment processing and organized storage"""

    def __init__(self, base_attachments_dir: str):
        self.base_dir = base_attachments_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def create_user_directory(self, sender_email: str, message_id: str) -> str:
        """Create organized directory structure for attachments"""
        # Clean email for use as directory name
        clean_email = re.sub(r'[^\w\-_\.]', '_', sender_email.lower())
        # Create directory structure: attachments/sender_email/YYYY-MM/message_id/
        date_folder = datetime.now().strftime('%Y-%m')
        attachment_dir = os.path.join(
            self.base_dir,
            clean_email,
            date_folder,
            message_id[:12]  # First 12 chars of message ID
        )
        os.makedirs(attachment_dir, exist_ok=True)
        return attachment_dir

    def create_safe_filename(self, filename: str, attachment_id: str) -> str:
        """Create filename that preserves original name but prevents conflicts"""
        # Remove unsafe characters but preserve original name structure
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Split name and extension
        name_parts = safe_name.rsplit('.', 1)
        if len(name_parts) == 2:
            name, ext = name_parts
            # Add attachment ID to prevent conflicts while keeping original name readable
            return f"{name}_{attachment_id[:8]}.{ext}"
        else:
            return f"{safe_name}_{attachment_id[:8]}"

    def save_attachment(self, file_data: bytes, filename: str, sender_email: str,
                       message_id: str, attachment_id: str, mime_type: str, size: int) -> Dict:
        """Save attachment to organized location with comprehensive validation"""
        try:
            # ADDED: Validate file size (50MB limit)
            max_size = 50 * 1024 * 1024  # 50MB
            if size > max_size:
                error_msg = f"Attachment {filename} too large: {size / 1024 / 1024:.1f}MB (max 50MB)"
                logger.warning(error_msg)
                raise ValueError(error_msg)
                
            # ADDED: Validate minimum size (prevent 0-byte files)
            if size <= 0:
                raise ValueError(f"Invalid file size: {size} bytes")
                
            # ADDED: Validate filename
            if not filename or len(filename) > 255:
                raise ValueError(f"Invalid filename: '{filename}'")
                
            # ADDED: Check for suspicious file extensions
            suspicious_extensions = {
                '.exe', '.scr', '.bat', '.cmd', '.com', '.pif', '.vbs', '.js', 
                '.jar', '.app', '.deb', '.rpm', '.dmg', '.pkg', '.msi'
            }
            file_ext = Path(filename).suffix.lower()
            if file_ext in suspicious_extensions:
                logger.warning(f"Suspicious file extension blocked: {filename}")
                raise ValueError(f"File type not allowed: {file_ext}")
                
            # ADDED: Validate MIME type consistency
            expected_extensions = {
                'application/pdf': ['.pdf'],
                'image/jpeg': ['.jpg', '.jpeg'],
                'image/png': ['.png'],
                'text/plain': ['.txt'],
                'application/msword': ['.doc'],
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
            }
            
            if mime_type in expected_extensions:
                if file_ext not in expected_extensions[mime_type]:
                    logger.warning(f"MIME type mismatch: {mime_type} vs {file_ext} for {filename}")
                    # Don't block, but log for monitoring
            
            # Create organized directory structure
            attachment_dir = self.create_user_directory(sender_email, message_id)
            
            # ADDED: Check available disk space
            try:
                total, used, free = shutil.disk_usage(attachment_dir)
                required_space = size * 2  # Require 2x file size free space as buffer
                if free < required_space:
                    error_msg = f"Insufficient disk space: need {required_space / 1024 / 1024:.1f}MB, have {free / 1024 / 1024:.1f}MB"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
            except (OSError, ValueError) as e:
                logger.warning(f"Could not check disk space: {e}")
                # Continue anyway, but log the issue
            
            # Create safe filename with original name preserved
            safe_filename = self.create_safe_filename(filename, attachment_id)
            filepath = os.path.join(attachment_dir, safe_filename)
            
            # ADDED: Check if file already exists (shouldn't happen, but be safe)
            if os.path.exists(filepath):
                logger.warning(f"File already exists, overwriting: {filepath}")
            
            # Save attachment to organized location
            temp_filepath = filepath + '.tmp'
            try:
                with open(temp_filepath, 'wb') as f:
                    f.write(file_data)
                    
                # ADDED: Verify file was written correctly
                actual_size = os.path.getsize(temp_filepath)
                if actual_size != size:
                    os.remove(temp_filepath)
                    raise ValueError(f"File save verification failed: expected {size} bytes, got {actual_size} bytes")
                    
                # ADDED: Verify file integrity by checking if we can read it back
                try:
                    with open(temp_filepath, 'rb') as f:
                        test_read = f.read(1024)  # Read first 1KB to verify accessibility
                    if not test_read and size > 0:
                        raise ValueError("Saved file appears to be corrupted")
                except Exception as e:
                    os.remove(temp_filepath)
                    raise ValueError(f"File integrity check failed: {e}")
                    
                # Move from temp to final location (atomic operation)
                os.rename(temp_filepath, filepath)
                
            except Exception as e:
                # Clean up temp file if it exists
                if os.path.exists(temp_filepath):
                    try:
                        os.remove(temp_filepath)
                    except:
                        pass
                raise
            
            # Create relative path for database storage
            relative_path = os.path.relpath(filepath, self.base_dir)
            
            logger.info(f"Successfully saved attachment: {filename} ({size} bytes) to {relative_path}")
            
            # Return comprehensive attachment info
            return {
                'filename': filename,
                'safe_filename': safe_filename,
                'relative_path': relative_path,
                'full_path': filepath,
                'mime_type': mime_type,
                'size': size,
                'attachment_id': attachment_id,
                'sender_email': sender_email,
                'message_id': message_id,
                'download_url': f"/attachment/{relative_path.replace(os.sep, '/')}"
            }
            
        except Exception as e:
            logger.error(f"Error saving attachment {filename}: {e}")
            raise  # Re-raise to let caller handle

    def process_attachment_part(self, part: Dict, message_id: str, sender_email: str,
                               gmail_client) -> Optional[Dict]:
        """Process an attachment part from email message with robust error handling"""
        filename = "unknown_attachment"
        try:
            filename = part.get('filename', 'unknown_attachment')
            mime_type = part.get('mimeType', 'application/octet-stream')
            attachment_id = part['body'].get('attachmentId')
            size = part['body'].get('size', 0)
            
            # Skip if no attachment ID (inline content)
            if not attachment_id:
                logger.debug(f"Skipping part without attachment ID: {filename}")
                return None
                
            # ADDED: Validate basic parameters
            if not message_id or not sender_email:
                logger.error(f"Missing required parameters for attachment {filename}")
                return None
                
            # ADDED: Skip attachments that are too large (check before downloading)
            max_size = 50 * 1024 * 1024  # 50MB
            if size > max_size:
                logger.warning(f"Skipping large attachment {filename}: {size / 1024 / 1024:.1f}MB > 50MB")
                return {
                    'filename': filename,
                    'error': 'File too large',
                    'size': size,
                    'status': 'skipped'
                }
                
            # ADDED: Skip empty attachments
            if size <= 0:
                logger.warning(f"Skipping empty attachment: {filename}")
                return None
                
            logger.info(f"Processing attachment: {filename} ({size} bytes)")
            
            # Download attachment data with retry logic
            file_data = None
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    file_data = gmail_client.download_attachment(message_id, attachment_id)
                    break
                except Exception as download_error:
                    logger.warning(f"Download attempt {attempt + 1} failed for {filename}: {download_error}")
                    if attempt == max_retries - 1:
                        raise download_error
                    import time
                    time.sleep(1)  # Wait 1 second before retry
                    
            if not file_data:
                raise ValueError("Downloaded file data is empty")
                
            # ADDED: Verify downloaded size matches expected size
            if len(file_data) != size:
                logger.warning(f"Size mismatch for {filename}: expected {size}, got {len(file_data)}")
                # Don't fail completely, but update the size
                size = len(file_data)
            
            # Save attachment with organized storage
            result = self.save_attachment(
                file_data, filename, sender_email, message_id,
                attachment_id, mime_type, size
            )
            
            # ADDED: Mark as successfully processed
            result['status'] = 'success'
            return result
            
        except ValueError as ve:
            # Expected validation errors - log and skip
            logger.warning(f"Validation error for attachment {filename}: {ve}")
            return {
                'filename': filename,
                'error': str(ve),
                'status': 'validation_failed'
            }
            
        except PermissionError as pe:
            # File system permission issues
            logger.error(f"Permission error saving attachment {filename}: {pe}")
            return {
                'filename': filename,
                'error': 'Permission denied',
                'status': 'permission_error'
            }
            
        except OSError as oe:
            # Disk space, file system issues
            logger.error(f"File system error for attachment {filename}: {oe}")
            return {
                'filename': filename,
                'error': 'File system error',
                'status': 'filesystem_error'
            }
            
        except Exception as e:
            # Unexpected errors - log but don't crash email processing
            logger.error(f"Unexpected error processing attachment {filename}: {e}", exc_info=True)
            return {
                'filename': filename,
                'error': 'Processing failed',
                'status': 'error'
            }

    def get_attachment_path(self, relative_path: str) -> str:
        """Get full path from relative path"""
        return os.path.join(self.base_dir, relative_path)

    def attachment_exists(self, relative_path: str) -> bool:
        """Check if attachment file exists"""
        full_path = self.get_attachment_path(relative_path)
        return os.path.exists(full_path)

    def cleanup_old_attachments(self, days_old: int = 90) -> Dict:
        """Clean up old attachment files to manage disk space"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            removed_count = 0
            freed_space = 0
            
            for root, dirs, files in os.walk(self.base_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        file_stat = os.stat(file_path)
                        file_date = datetime.fromtimestamp(file_stat.st_mtime)
                        
                        if file_date < cutoff_date:
                            file_size = file_stat.st_size
                            os.remove(file_path)
                            removed_count += 1
                            freed_space += file_size
                            logger.info(f"Removed old attachment: {file_path}")
                    except Exception as e:
                        logger.warning(f"Could not process file {file_path}: {e}")
                        
            # Remove empty directories
            for root, dirs, files in os.walk(self.base_dir, topdown=False):
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    try:
                        if not os.listdir(dir_path):  # Directory is empty
                            os.rmdir(dir_path)
                            logger.info(f"Removed empty directory: {dir_path}")
                    except Exception as e:
                        logger.warning(f"Could not remove directory {dir_path}: {e}")
                        
            result = {
                'removed_files': removed_count,
                'freed_space_mb': freed_space / 1024 / 1024,
                'status': 'success'
            }
            
            logger.info(f"Cleanup completed: removed {removed_count} files, freed {result['freed_space_mb']:.1f}MB")
            return result
            
        except Exception as e:
            logger.error(f"Error during attachment cleanup: {e}")
            return {
                'removed_files': 0,
                'freed_space_mb': 0,
                'status': 'error',
                'error': str(e)
            }

    def get_storage_stats(self) -> Dict:
        """Get statistics about attachment storage"""
        try:
            total_files = 0
            total_size = 0
            
            for root, dirs, files in os.walk(self.base_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        file_size = os.path.getsize(file_path)
                        total_files += 1
                        total_size += file_size
                    except Exception as e:
                        logger.warning(f"Could not get size for {file_path}: {e}")
                        
            # Get disk usage
            try:
                total_disk, used_disk, free_disk = shutil.disk_usage(self.base_dir)
            except Exception as e:
                logger.warning(f"Could not get disk usage: {e}")
                total_disk = used_disk = free_disk = 0
                
            return {
                'total_files': total_files,
                'total_size_mb': total_size / 1024 / 1024,
                'disk_total_gb': total_disk / 1024 / 1024 / 1024,
                'disk_used_gb': used_disk / 1024 / 1024 / 1024,
                'disk_free_gb': free_disk / 1024 / 1024 / 1024,
                'attachments_dir': self.base_dir
            }
            
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {
                'error': str(e),
                'attachments_dir': self.base_dir
            }