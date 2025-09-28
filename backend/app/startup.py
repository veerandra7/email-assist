"""
Application startup utilities.
"""
import os
import glob
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def clear_gmail_sessions():
    """Clear Gmail session files on application startup."""
    try:
        # Clear global credential files (legacy)
        files_to_remove = ["gmail_credentials.json", "gmail_token.json"]
        cleared_files = []
        
        for file_path in files_to_remove:
            if os.path.exists(file_path):
                os.remove(file_path)
                cleared_files.append(file_path)
        
        # Clear session-specific credential files
        session_cred_files = glob.glob("gmail_credentials_*.json") + glob.glob("gmail_token_*.json")
        for file_path in session_cred_files:
            if os.path.exists(file_path):
                os.remove(file_path)
                cleared_files.append(file_path)
        
        # Clear old user session files (force fresh authentication)
        user_sessions_dir = Path("user_sessions")
        if user_sessions_dir.exists():
            for session_file in user_sessions_dir.glob("*.json"):
                try:
                    session_file.unlink()
                    cleared_files.append(str(session_file))
                except Exception as e:
                    logger.warning(f"Could not remove session file {session_file}: {e}")
        
        if cleared_files:
            logger.info(f"🗑️ Cleared Gmail session files on startup: {', '.join(cleared_files)}")
            logger.info("✅ Fresh Gmail authentication required")
        else:
            logger.info("ℹ️ No Gmail session files found to clear")
            
    except Exception as e:
        logger.warning(f"⚠️ Could not clear Gmail session files: {e}")
