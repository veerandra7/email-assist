"""
Application startup utilities.
"""
import os
import logging

logger = logging.getLogger(__name__)

def clear_gmail_sessions():
    """Clear Gmail session files on application startup."""
    try:
        files_to_remove = ["gmail_credentials.json", "gmail_token.json"]
        cleared_files = []
        
        for file_path in files_to_remove:
            if os.path.exists(file_path):
                os.remove(file_path)
                cleared_files.append(file_path)
        
        if cleared_files:
            logger.info(f"🗑️ Cleared Gmail session files on startup: {', '.join(cleared_files)}")
            logger.info("✅ Fresh Gmail authentication required")
        else:
            logger.info("ℹ️ No Gmail session files found to clear")
            
    except Exception as e:
        logger.warning(f"⚠️ Could not clear Gmail session files: {e}")
