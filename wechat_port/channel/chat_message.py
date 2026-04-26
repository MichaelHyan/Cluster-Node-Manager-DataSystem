"""Chat message base class"""

class ChatMessage:
    """Base class for chat messages"""

    def __init__(self, msg: dict):
        """Initialize chat message

        Args:
            msg: Message dictionary
        """
        self.msg = msg
        self.ctype = None  # Context type
        self.content = ""  # Message content
        self._prepare_fn = None  # Function to prepare message (e.g., download media)

    def prepare(self):
        """Prepare message (e.g., download media if needed)"""
        if self._prepare_fn:
            self._prepare_fn()
            self._prepare_fn = None
