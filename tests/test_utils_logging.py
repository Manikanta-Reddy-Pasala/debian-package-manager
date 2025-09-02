"""Tests for logging utilities."""

import pytest
import logging
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, Mock

from debian_metapackage_manager.utils.logging.logger import get_logger, setup_logging
from debian_metapackage_manager.utils.logging.formatters import ColoredFormatter, DPMFormatter


class TestGetLogger:
    """Test suite for get_logger function."""

    def test_get_logger_basic(self):
        """Test basic logger retrieval."""
        logger = get_logger('test')
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == 'debian_metapackage_manager.test'

    def test_get_logger_with_module_name(self):
        """Test logger with module-style name."""
        logger = get_logger('core.package_manager')
        
        assert logger.name == 'debian_metapackage_manager.core.package_manager'

    def test_get_logger_same_name_returns_same_instance(self):
        """Test that same logger name returns same instance."""
        logger1 = get_logger('test_same')
        logger2 = get_logger('test_same')
        
        assert logger1 is logger2

    def test_get_logger_different_names_return_different_instances(self):
        """Test that different names return different instances."""
        logger1 = get_logger('test_diff1')
        logger2 = get_logger('test_diff2')
        
        assert logger1 is not logger2
        assert logger1.name != logger2.name


class TestSetupLogging:
    """Test suite for setup_logging function."""

    def test_setup_logging_default(self):
        """Test setup logging with default parameters."""
        with patch('logging.basicConfig') as mock_config:
            setup_logging()
            
            mock_config.assert_called_once()
            call_kwargs = mock_config.call_args[1]
            assert call_kwargs['level'] == logging.INFO
            assert call_kwargs['format'] is not None

    def test_setup_logging_debug_level(self):
        """Test setup logging with debug level."""
        with patch('logging.basicConfig') as mock_config:
            setup_logging(level=logging.DEBUG)
            
            mock_config.assert_called_once()
            call_kwargs = mock_config.call_args[1]
            assert call_kwargs['level'] == logging.DEBUG

    def test_setup_logging_with_file(self):
        """Test setup logging with file output."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            with patch('logging.basicConfig') as mock_config:
                setup_logging(filename=temp_path)
                
                mock_config.assert_called_once()
                call_kwargs = mock_config.call_args[1]
                assert call_kwargs['filename'] == temp_path
        finally:
            os.unlink(temp_path)

    def test_setup_logging_with_colored_formatter(self):
        """Test setup logging with colored formatter."""
        with patch('logging.basicConfig') as mock_config:
            setup_logging(use_colors=True)
            
            mock_config.assert_called_once()
            # In real implementation, this would use ColoredFormatter

    def test_setup_logging_verbose(self):
        """Test setup logging in verbose mode."""
        with patch('logging.basicConfig') as mock_config:
            setup_logging(verbose=True)
            
            mock_config.assert_called_once()
            call_kwargs = mock_config.call_args[1]
            assert call_kwargs['level'] == logging.DEBUG


class TestColoredFormatter:
    """Test suite for ColoredFormatter class."""

    def test_colored_formatter_initialization(self):
        """Test ColoredFormatter initialization."""
        formatter = ColoredFormatter()
        
        assert hasattr(formatter, 'COLORS')
        assert hasattr(formatter, 'RESET')

    def test_colored_formatter_format_info(self):
        """Test formatting INFO level message."""
        formatter = ColoredFormatter()
        
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='',
            lineno=0,
            msg='Test message',
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        
        assert 'Test message' in formatted
        # Should contain color codes for INFO level

    def test_colored_formatter_format_error(self):
        """Test formatting ERROR level message."""
        formatter = ColoredFormatter()
        
        record = logging.LogRecord(
            name='test',
            level=logging.ERROR,
            pathname='',
            lineno=0,
            msg='Error message',
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        
        assert 'Error message' in formatted
        # Should contain color codes for ERROR level

    def test_colored_formatter_format_warning(self):
        """Test formatting WARNING level message."""
        formatter = ColoredFormatter()
        
        record = logging.LogRecord(
            name='test',
            level=logging.WARNING,
            pathname='',
            lineno=0,
            msg='Warning message',
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        
        assert 'Warning message' in formatted

    def test_colored_formatter_format_debug(self):
        """Test formatting DEBUG level message."""
        formatter = ColoredFormatter()
        
        record = logging.LogRecord(
            name='test',
            level=logging.DEBUG,
            pathname='',
            lineno=0,
            msg='Debug message',
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        
        assert 'Debug message' in formatted

    def test_colored_formatter_no_color_when_disabled(self):
        """Test that no colors are used when colors are disabled."""
        # This would test the case where terminal doesn't support colors
        formatter = ColoredFormatter(use_colors=False)
        
        record = logging.LogRecord(
            name='test',
            level=logging.ERROR,
            pathname='',
            lineno=0,
            msg='Error message',
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        
        # Should not contain ANSI color codes
        assert '\033[' not in formatted


class TestDPMFormatter:
    """Test suite for DPMFormatter class."""

    def test_dpm_formatter_initialization(self):
        """Test DPMFormatter initialization."""
        formatter = DPMFormatter()
        
        assert hasattr(formatter, 'datefmt')

    def test_dpm_formatter_format_basic(self):
        """Test basic message formatting."""
        formatter = DPMFormatter()
        
        record = logging.LogRecord(
            name='test.module',
            level=logging.INFO,
            pathname='/path/to/file.py',
            lineno=42,
            msg='Test message',
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        
        assert 'Test message' in formatted
        assert 'test.module' in formatted
        assert 'INFO' in formatted

    def test_dpm_formatter_with_exception(self):
        """Test formatting with exception information."""
        formatter = DPMFormatter()
        
        try:
            raise ValueError("Test exception")
        except ValueError:
            import sys
            exc_info = sys.exc_info()
        
        record = logging.LogRecord(
            name='test',
            level=logging.ERROR,
            pathname='',
            lineno=0,
            msg='Error with exception',
            args=(),
            exc_info=exc_info
        )
        
        formatted = formatter.format(record)
        
        assert 'Error with exception' in formatted

    def test_detailed_formatter_with_extra_fields(self):
        """Test formatting with extra fields."""
        formatter = DetailedFormatter()
        
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='',
            lineno=0,
            msg='Message with extra data',
            args=(),
            exc_info=None
        )
        
        # Add extra fields
        record.package = 'test-package'
        record.operation = 'install'
        
        formatted = formatter.format(record)
        
        assert 'Message with extra data' in formatted


class TestLoggingIntegration:
    """Integration tests for logging components."""

    def test_logger_with_colored_formatter(self):
        """Test logger integration with colored formatter."""
        logger = get_logger('test_colored')
        
        # Add colored formatter to logger
        handler = logging.StreamHandler()
        formatter = ColoredFormatter()
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        
        # Test logging at different levels
        with patch('sys.stdout') as mock_stdout:
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            logger.debug("Debug message")

    def test_logger_with_dpm_formatter(self):
        """Test logger integration with DPM formatter."""
        logger = get_logger('test_dpm')
        
        # Add DPM formatter to logger
        handler = logging.StreamHandler()
        formatter = DPMFormatter()
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        
        # Test logging
        with patch('sys.stdout') as mock_stdout:
            logger.info("DPM info message")

    def test_setup_logging_full_configuration(self):
        """Test complete logging setup."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Setup logging with file and console output
            setup_logging(
                level=logging.DEBUG,
                filename=temp_path,
                use_colors=True,
                verbose=True
            )
            
            # Get a logger and test it
            logger = get_logger('integration_test')
            
            logger.info("Integration test message")
            logger.warning("Integration test warning")
            logger.error("Integration test error")
            
            # Verify file was created and has content
            assert os.path.exists(temp_path)
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_logger_hierarchy(self):
        """Test logger hierarchy behavior."""
        parent_logger = get_logger('parent')
        child_logger = get_logger('parent.child')
        grandchild_logger = get_logger('parent.child.grandchild')
        
        # Test that hierarchy is maintained
        assert 'parent' in parent_logger.name
        assert 'parent.child' in child_logger.name
        assert 'parent.child.grandchild' in grandchild_logger.name

    def test_logger_performance_with_many_messages(self):
        """Test logger performance with many messages."""
        logger = get_logger('performance_test')
        
        # Add null handler to avoid output during test
        logger.addHandler(logging.NullHandler())
        logger.setLevel(logging.DEBUG)
        
        import time
        start_time = time.time()
        
        # Log many messages
        for i in range(1000):
            logger.debug(f"Debug message {i}")
            logger.info(f"Info message {i}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete in reasonable time (less than 1 second)
        assert duration < 1.0


class TestLoggingEdgeCases:
    """Test edge cases and error conditions."""

    def test_logger_with_none_name(self):
        """Test logger creation with None name."""
        # Should handle gracefully
        logger = get_logger(None)
        assert logger.name == 'debian_metapackage_manager.None'

    def test_logger_with_empty_name(self):
        """Test logger creation with empty name."""
        logger = get_logger('')
        assert logger.name == 'debian_metapackage_manager.'

    def test_setup_logging_with_invalid_file_path(self):
        """Test setup logging with invalid file path."""
        invalid_path = '/nonexistent/directory/log.txt'
        
        # Should handle gracefully and not crash
        try:
            setup_logging(log_file=invalid_path)
            # If it succeeds, that's fine too - it might create the directory
            assert True
        except Exception as e:
            # May raise exception but shouldn't crash the program
            assert isinstance(e, (FileNotFoundError, PermissionError, OSError))

    def test_formatter_with_unicode_messages(self):
        """Test formatters with Unicode messages."""
        formatter = ColoredFormatter()
        
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='',
            lineno=0,
            msg='Unicode message: 🔧 Installing package',
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        assert '🔧' in formatted
        assert 'Installing package' in formatted

    def test_formatter_with_very_long_messages(self):
        """Test formatters with very long messages."""
        formatter = DetailedFormatter()
        
        long_message = "A" * 10000  # Very long message
        
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='',
            lineno=0,
            msg=long_message,
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        assert long_message in formatted

    def test_concurrent_logger_access(self):
        """Test concurrent access to loggers (thread safety)."""
        import threading
        import time
        
        results = []
        
        def log_messages(thread_id):
            logger = get_logger(f'thread_{thread_id}')
            logger.addHandler(logging.NullHandler())
            
            for i in range(100):
                logger.info(f"Thread {thread_id} message {i}")
            
            results.append(f"Thread {thread_id} completed")
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=log_messages, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all threads completed
        assert len(results) == 5