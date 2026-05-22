class SessionManager:
    """
    A simple in-memory session manager for MCP.
    Stores the current authenticated user's ID and JWT token.
    """
    def __init__(self):
        self._session = {
            "user_id": None,
            "token": None
        }

    def set_session(self, user_id: int, token: str):
        self._session["user_id"] = user_id
        self._session["token"] = token

    def get_session(self):
        if not self._session["user_id"] or not self._session["token"]:
            return None
        return self._session

    def clear_session(self):
        self._session = {
            "user_id": None,
            "token": None
        }

# Global session instance
SESSION = SessionManager()
