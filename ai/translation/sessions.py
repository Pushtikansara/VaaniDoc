"""In-memory session management for VaaniDoc consultations.

Provides temporary session storage for consultation data without persisting
to any database, file, or external service. Sessions are kept in process memory
only.

Key properties:
- Session IDs are random/unpredictable (secrets.token_urlsafe)
- Different patients cannot access each other's sessions
- Data is lost on server restart (documented as expected MVP behavior)
- No database, no external services, no permanent storage
- Designed to be used with FastAPI dependency injection

The session stores:
- source_language: the VaaniDoc language code
- original_text: the confirmed Indian-language patient statement
- english_text: the translation result
- translation_verification: the safety check result
- clinical_data: free-form dict for clinical findings
- urgency: urgency level string

Typical lifecycle:
1. Create session on first patient input
2. Store confirmed text and translation results
3. Clinical staff views data via the session ID
4. On consultation end, session is invalidated/deleted
5. Server restart clears all sessions (expected MVP behavior)
"""

import secrets
import time
from typing import Dict, Optional, Any

# In-memory session store: {session_id: session_data}
# This lives only for the duration of the Python process.
# On server restart, all sessions are lost (expected MVP behavior).
_session_store: Dict[str, dict] = {}

# Session expiration: seconds after which a session is considered expired.
# Set to 3600 (1 hour) for privacy-preserving session lifecycle.
SESSION_EXPIRATION_SECONDS: Optional[int] = 3600



def _generate_session_id() -> str:
    """Generate a random, unpredictable session ID."""
    return secrets.token_urlsafe(32)


def _check_expiration(session_data: dict) -> bool:
    """Check if a session has expired based on its creation time.

    Returns True if the session has expired, False otherwise.
    """
    if SESSION_EXPIRATION_SECONDS is None:
        return False
    age = time.time() - session_data.get("_created_at", 0)
    return age > SESSION_EXPIRATION_SECONDS


def create_session(
    source_language: str,
    original_text: str,
    english_text: str = "",
    translation_verification: dict = None,
    clinical_data: dict = None,
    urgency: str = "routine",
) -> str:
    """Create a new consultation session and return the session ID.

    Stores the initial patient data temporarily in memory.

    Args:
        source_language: VaaniDoc language code (e.g. "gu", "hi")
        original_text: The confirmed Indian-language patient statement
        english_text: The English translation result (may be empty initially)
        translation_verification: The safety verification result dict
        clinical_data: Additional clinical information dict
        urgency: Urgency level (e.g. "routine", "urgent", "emergency")

    Returns:
        session_id: A random-unpredictable session identifier
    """
    cleanup_expired_sessions()
    session_id = _generate_session_id()

    session_data = {
        "session_id": session_id,
        "source_language": source_language,
        "original_text": original_text,
        "english_text": english_text,
        "translation_verification": translation_verification or {},
        "clinical_data": clinical_data or {},
        "urgency": urgency,
        "_created_at": time.time(),
    }

    _session_store[session_id] = session_data
    return session_id


def get_session(session_id: str) -> Optional[dict]:
    """Retrieve a session by ID.

    Returns None if the session does not exist or has expired.

    Security: Ensures different patients cannot access each other's sessions
    by simply returning None for unknown session IDs.
    """
    if session_id not in _session_store:
        return None

    session_data = _session_store[session_id]

    # Check expiration
    if _check_expiration(session_data):
        # Remove expired session
        del _session_store[session_id]
        return None

    return session_data


def update_session(
    session_id: str,
    *,
    original_text: str = None,
    english_text: str = None,
    translation_verification: dict = None,
    clinical_data: dict = None,
    urgency: str = None,
) -> bool:
    """Update specific fields of an existing session.

    Returns True if the session was updated, False if the session was not found
    or has expired.
    """
    session_data = get_session(session_id)
    if session_data is None:
        return False

    if original_text is not None:
        session_data["original_text"] = original_text
    if english_text is not None:
        session_data["english_text"] = english_text
    if translation_verification is not None:
        session_data["translation_verification"] = translation_verification
    if clinical_data is not None:
        session_data["clinical_data"] = clinical_data
    if urgency is not None:
        session_data["urgency"] = urgency

    # Update the timestamp
    session_data["_created_at"] = time.time()
    return True


def delete_session(session_id: str) -> bool:
    """Delete a session by ID.

    Returns True if the session was found and deleted, False if not found.
    """
    if session_id in _session_store:
        del _session_store[session_id]
        return True
    return False


def invalidate_session(session_id: str) -> bool:
    """Alias for delete_session - invalidate a session."""
    return delete_session(session_id)


def list_sessions() -> Dict[str, dict]:
    """List all active sessions (for debugging/admin only).

    Note: This function is not exposed through the API and should not be
    used in production endpoints. It is provided for development/debugging
    purposes only.
    """
    # Remove expired sessions first
    expired_ids = []
    for sid, data in _session_store.items():
        if _check_expiration(data):
            expired_ids.append(sid)
    for sid in expired_ids:
        del _session_store[sid]

    return dict(_session_store)


def cleanup_expired_sessions() -> int:
    """Remove all expired sessions and return the count of removed sessions."""
    expired_ids = []
    for sid, data in _session_store.items():
        if _check_expiration(data):
            expired_ids.append(sid)
    for sid in expired_ids:
        del _session_store[sid]
    return len(expired_ids)