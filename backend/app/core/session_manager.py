"""
Session management for handling multiple user sessions.
"""
import os
import json
import logging
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class SessionManager:
    """Manages user sessions for multi-user authentication."""
    
    def __init__(self):
        """Initialize session manager."""
        self.sessions_dir = Path("user_sessions")
        self.sessions_dir.mkdir(exist_ok=True)
        self.session_timeout = timedelta(hours=24)  # Sessions expire after 24 hours
    
    def create_session(self) -> str:
        """Create a new session and return session ID."""
        session_id = secrets.token_urlsafe(32)
        return self.create_session_with_id(session_id)
    
    def create_session_with_id(self, session_id: str) -> str:
        """Create a session with a specific ID."""
        session_data = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + self.session_timeout).isoformat(),
            "is_active": True,
            "user_email": None  # Will be set during authentication
        }
        
        session_file = self.sessions_dir / f"{session_id}.json"
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        logger.info(f"🆕 Created new session: {session_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data by session ID."""
        session_file = self.sessions_dir / f"{session_id}.json"
        
        if not session_file.exists():
            return None
        
        try:
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            
            # Check if session is expired
            expires_at = datetime.fromisoformat(session_data['expires_at'])
            if datetime.now() > expires_at:
                self.delete_session(session_id)
                return None
            
            return session_data
            
        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {e}")
            return None
    
    def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session data."""
        session_data = self.get_session(session_id)
        if not session_data:
            return False
        
        session_data.update(updates)
        session_file = self.sessions_dir / f"{session_id}.json"
        
        try:
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to update session {session_id}: {e}")
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session and its associated data."""
        try:
            # Remove session file
            session_file = self.sessions_dir / f"{session_id}.json"
            if session_file.exists():
                session_file.unlink()
            
            # Remove associated credential files
            self._clear_session_credentials(session_id)
            
            logger.info(f"🗑️ Deleted session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False
    
    def _clear_session_credentials(self, session_id: str):
        """Clear Gmail credentials for a specific session."""
        try:
            credentials_file = f"gmail_credentials_{session_id}.json"
            token_file = f"gmail_token_{session_id}.json"
            
            for file_path in [credentials_file, token_file]:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.debug(f"Removed credential file: {file_path}")
        except Exception as e:
            logger.warning(f"Could not clear credentials for session {session_id}: {e}")
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions."""
        try:
            for session_file in self.sessions_dir.glob("*.json"):
                session_id = session_file.stem
                session_data = self.get_session(session_id)
                if not session_data:  # Will be None if expired
                    logger.info(f"🧹 Cleaned up expired session: {session_id}")
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
    
    def is_valid_session(self, session_id: str) -> bool:
        """Check if session ID is valid and not expired."""
        return self.get_session(session_id) is not None


# Global session manager instance
session_manager = SessionManager() 