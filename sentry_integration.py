#!/usr/bin/env python3
"""
Sentry error monitoring integration for ImageFox.

This module handles Sentry SDK initialization and configuration
for comprehensive error tracking across all ImageFox components.
"""

import os
import logging
from typing import Optional, Dict, Any
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

logger = logging.getLogger(__name__)


class SentryIntegration:
    """Sentry error monitoring integration manager."""
    
    def __init__(self, dsn: Optional[str] = None):
        """
        Initialize Sentry integration.
        
        Args:
            dsn: Sentry DSN. If not provided, reads from environment.
        """
        self.dsn = dsn or os.getenv('SENTRY_DSN')
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self.release = os.getenv('RELEASE_VERSION', 'unknown')
        self.initialized = False
        
        if self.dsn:
            self.initialize()
        else:
            logger.warning("Sentry DSN not found - error monitoring disabled")
    
    def initialize(self) -> bool:
        """
        Initialize Sentry SDK with configuration.
        
        Returns:
            True if initialization successful, False otherwise.
        """
        if self.initialized:
            logger.info("Sentry already initialized")
            return True
        
        try:
            # Configure logging integration
            logging_integration = LoggingIntegration(
                level=logging.INFO,
                event_level=logging.ERROR
            )
            
            # Initialize Sentry
            sentry_sdk.init(
                dsn=self.dsn,
                environment=self.environment,
                release=self.release,
                integrations=[logging_integration],
                traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
                send_default_pii=False,  # Don't send personally identifiable information
                attach_stacktrace=True,
                max_breadcrumbs=50,
                before_send=self._before_send_filter
            )
            
            self.initialized = True
            logger.info(f"Sentry initialized for environment: {self.environment}")
            
            # Set initial context
            self.set_context("app", {
                "name": "ImageFox",
                "version": self.release,
                "environment": self.environment
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Sentry: {e}")
            return False
    
    def _before_send_filter(self, event: Dict, hint: Dict) -> Optional[Dict]:
        """
        Filter events before sending to Sentry.
        
        Args:
            event: The event to be sent
            hint: Additional information about the event
        
        Returns:
            Modified event or None to drop the event
        """
        # Filter out sensitive information
        if 'extra' in event:
            sensitive_keys = ['api_key', 'password', 'token', 'secret']
            for key in list(event['extra'].keys()):
                if any(sensitive in key.lower() for sensitive in sensitive_keys):
                    event['extra'][key] = '[REDACTED]'
        
        # Add module context
        if 'exception' in event:
            for exception in event['exception']['values']:
                if 'stacktrace' in exception:
                    for frame in exception['stacktrace']['frames']:
                        if 'filename' in frame:
                            module = frame['filename'].replace('.py', '')
                            self.add_tag('module', module)
        
        return event
    
    def capture_exception(self, exception: Exception, **kwargs) -> Optional[str]:
        """
        Capture an exception and send to Sentry.
        
        Args:
            exception: The exception to capture
            **kwargs: Additional context data
        
        Returns:
            Event ID if sent successfully, None otherwise
        """
        if not self.initialized:
            logger.error(f"Sentry not initialized, exception not captured: {exception}")
            return None
        
        try:
            # Add context if provided
            if 'context' in kwargs:
                for key, value in kwargs['context'].items():
                    self.set_context(key, value)
            
            # Add tags if provided
            if 'tags' in kwargs:
                for key, value in kwargs['tags'].items():
                    self.add_tag(key, value)
            
            # Capture the exception
            event_id = sentry_sdk.capture_exception(exception)
            logger.info(f"Exception captured with ID: {event_id}")
            return event_id
            
        except Exception as e:
            logger.error(f"Failed to capture exception: {e}")
            return None
    
    def capture_message(self, message: str, level: str = 'info', **kwargs) -> Optional[str]:
        """
        Capture a message and send to Sentry.
        
        Args:
            message: The message to capture
            level: Severity level (debug, info, warning, error, critical)
            **kwargs: Additional context data
        
        Returns:
            Event ID if sent successfully, None otherwise
        """
        if not self.initialized:
            logger.warning(f"Sentry not initialized, message not captured: {message}")
            return None
        
        try:
            event_id = sentry_sdk.capture_message(message, level=level)
            logger.info(f"Message captured with ID: {event_id}")
            return event_id
            
        except Exception as e:
            logger.error(f"Failed to capture message: {e}")
            return None
    
    def set_user(self, user_data: Dict[str, Any]):
        """
        Set user context for Sentry events.
        
        Args:
            user_data: Dictionary with user information
        """
        if self.initialized:
            sentry_sdk.set_user(user_data)
    
    def set_context(self, key: str, value: Dict[str, Any]):
        """
        Set custom context for Sentry events.
        
        Args:
            key: Context key
            value: Context data
        """
        if self.initialized:
            sentry_sdk.set_context(key, value)
    
    def add_tag(self, key: str, value: str):
        """
        Add a tag to Sentry events.
        
        Args:
            key: Tag key
            value: Tag value
        """
        if self.initialized:
            sentry_sdk.set_tag(key, value)
    
    def add_breadcrumb(self, message: str, category: str = 'default', level: str = 'info', data: Optional[Dict] = None):
        """
        Add a breadcrumb for debugging.
        
        Args:
            message: Breadcrumb message
            category: Breadcrumb category
            level: Breadcrumb level
            data: Additional data
        """
        if self.initialized:
            sentry_sdk.add_breadcrumb(
                message=message,
                category=category,
                level=level,
                data=data or {}
            )
    
    def start_transaction(self, name: str, op: str = 'task') -> Any:
        """
        Start a performance monitoring transaction.
        
        Args:
            name: Transaction name
            op: Operation type
        
        Returns:
            Transaction object
        """
        if self.initialized:
            return sentry_sdk.start_transaction(name=name, op=op)
        return None
    
    def flush(self, timeout: int = 2):
        """
        Flush pending events to Sentry.
        
        Args:
            timeout: Maximum time to wait for flush
        """
        if self.initialized:
            sentry_sdk.flush(timeout=timeout)
    
    def test_error(self):
        """Send a test error to verify Sentry integration."""
        if not self.initialized:
            logger.warning("Sentry not initialized, cannot send test error")
            return
        
        try:
            # Create a test exception
            raise Exception("This is a test error from ImageFox")
        except Exception as e:
            event_id = self.capture_exception(
                e,
                tags={'test': 'true', 'module': 'sentry_integration'},
                context={'test_info': {'purpose': 'verify_integration'}}
            )
            if event_id:
                logger.info(f"Test error sent successfully with ID: {event_id}")
            else:
                logger.error("Failed to send test error")


# Global instance for easy access
_sentry_instance = None


def get_sentry() -> SentryIntegration:
    """
    Get the global Sentry integration instance.
    
    Returns:
        SentryIntegration instance
    """
    global _sentry_instance
    if _sentry_instance is None:
        _sentry_instance = SentryIntegration()
    return _sentry_instance


def initialize_sentry(dsn: Optional[str] = None) -> SentryIntegration:
    """
    Initialize and return Sentry integration.
    
    Args:
        dsn: Optional Sentry DSN
    
    Returns:
        Initialized SentryIntegration instance
    """
    global _sentry_instance
    _sentry_instance = SentryIntegration(dsn)
    return _sentry_instance


def main():
    """Test Sentry integration."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize Sentry
    sentry = initialize_sentry()
    
    if sentry.initialized:
        print("Sentry initialized successfully")
        
        # Send test error
        print("Sending test error to Sentry...")
        sentry.test_error()
        
        # Flush events
        sentry.flush()
        print("Test complete - check Sentry dashboard for the test error")
    else:
        print("Sentry not initialized - check SENTRY_DSN environment variable")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())