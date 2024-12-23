"""Logging filters for the application."""
import logging


class IgnoreSocketIOFilter(logging.Filter):
    """Filter to ignore Socket.IO polling logs."""
    
    def filter(self, record):
        """Filter Socket.IO polling logs.
        
        Args:
            record: Log record to filter
            
        Returns:
            bool: True if log should be shown, False if it should be filtered out
        """
        if not hasattr(record, 'request_line'):
            return True
            
        # Filter out Socket.IO polling requests
        if 'socket.io' in record.request_line and 'transport=polling' in record.request_line:
            return False
            
        return True
