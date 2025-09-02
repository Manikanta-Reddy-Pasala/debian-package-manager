"""Tests for network utility functions."""

import pytest
import subprocess
from unittest.mock import patch, Mock, MagicMock

from debian_metapackage_manager.utils.network.checker import NetworkChecker


class TestNetworkChecker:
    """Test suite for NetworkChecker class."""

    def test_network_checker_initialization(self):
        """Test NetworkChecker initialization."""
        checker = NetworkChecker()
        
        assert checker.cache_timeout == 30
        assert checker._network_available is None
        assert checker._repository_accessible is None
        assert checker._last_check_time == 0

    def test_network_checker_initialization_custom_timeout(self):
        """Test NetworkChecker initialization with custom timeout."""
        checker = NetworkChecker(cache_timeout=60)
        
        assert checker.cache_timeout == 60

    @patch('subprocess.run')
    def test_is_network_available_success(self, mock_run):
        """Test successful network availability check."""
        mock_run.return_value.returncode = 0
        
        checker = NetworkChecker()
        result = checker.is_network_available()
        
        assert result is True
        assert checker._network_available is True
        
        # Verify correct command was called
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args == ['ping', '-c', '1', '-W', '3', '8.8.8.8']

    @patch('subprocess.run')
    def test_is_network_available_failure(self, mock_run):
        """Test failed network availability check."""
        mock_run.return_value.returncode = 1
        
        checker = NetworkChecker()
        result = checker.is_network_available()
        
        assert result is False
        assert checker._network_available is False

    @patch('subprocess.run')
    def test_is_network_available_timeout(self, mock_run):
        """Test network check with timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired('ping', 5)
        
        checker = NetworkChecker()
        result = checker.is_network_available()
        
        assert result is False
        assert checker._network_available is False

    @patch('subprocess.run')
    def test_is_network_available_exception(self, mock_run):
        """Test network check with exception."""
        mock_run.side_effect = FileNotFoundError("ping command not found")
        
        checker = NetworkChecker()
        result = checker.is_network_available()
        
        assert result is False
        assert checker._network_available is False

    @patch('subprocess.run')
    def test_is_network_available_cached_result(self, mock_run):
        """Test that cached result is returned when not forcing check."""
        mock_run.return_value.returncode = 0
        
        checker = NetworkChecker()
        
        # First call should execute subprocess
        result1 = checker.is_network_available()
        assert result1 is True
        assert mock_run.call_count == 1
        
        # Second call should use cached result
        result2 = checker.is_network_available()
        assert result2 is True
        assert mock_run.call_count == 1  # Should not increase

    @patch('subprocess.run')
    def test_is_network_available_force_check(self, mock_run):
        """Test forcing network check bypasses cache."""
        mock_run.return_value.returncode = 0
        
        checker = NetworkChecker()
        
        # First call
        result1 = checker.is_network_available()
        assert mock_run.call_count == 1
        
        # Force check should bypass cache
        result2 = checker.is_network_available(force_check=True)
        assert mock_run.call_count == 2

    @patch('subprocess.run')
    def test_are_repositories_accessible_success(self, mock_run):
        """Test successful repository accessibility check."""
        mock_run.return_value.returncode = 0
        
        checker = NetworkChecker()
        result = checker.are_repositories_accessible()
        
        assert result is True
        assert checker._repository_accessible is True
        
        # Verify correct command was called
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args == ['apt-get', 'update', '--dry-run']

    @patch('subprocess.run')
    def test_are_repositories_accessible_failure(self, mock_run):
        """Test failed repository accessibility check."""
        mock_run.return_value.returncode = 1
        
        checker = NetworkChecker()
        result = checker.are_repositories_accessible()
        
        assert result is False
        assert checker._repository_accessible is False

    @patch('subprocess.run')
    def test_are_repositories_accessible_timeout(self, mock_run):
        """Test repository check with timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired('apt-get', 10)
        
        checker = NetworkChecker()
        result = checker.are_repositories_accessible()
        
        assert result is False
        assert checker._repository_accessible is False

    @patch('subprocess.run')
    def test_are_repositories_accessible_cached_result(self, mock_run):
        """Test that cached result is returned when not forcing check."""
        mock_run.return_value.returncode = 0
        
        checker = NetworkChecker()
        
        # First call should execute subprocess
        result1 = checker.are_repositories_accessible()
        assert result1 is True
        assert mock_run.call_count == 1
        
        # Second call should use cached result
        result2 = checker.are_repositories_accessible()
        assert result2 is True
        assert mock_run.call_count == 1  # Should not increase

    @patch('subprocess.run')
    def test_are_repositories_accessible_force_check(self, mock_run):
        """Test forcing repository check bypasses cache."""
        mock_run.return_value.returncode = 0
        
        checker = NetworkChecker()
        
        # First call
        result1 = checker.are_repositories_accessible()
        assert mock_run.call_count == 1
        
        # Force check should bypass cache
        result2 = checker.are_repositories_accessible(force_check=True)
        assert mock_run.call_count == 2

    def test_clear_cache(self):
        """Test clearing cache."""
        checker = NetworkChecker()
        
        # Set some cached values
        checker._network_available = True
        checker._repository_accessible = True
        checker._last_check_time = 123456
        
        # Clear cache
        checker.clear_cache()
        
        # Verify cache is cleared
        assert checker._network_available is None
        assert checker._repository_accessible is None
        assert checker._last_check_time == 0

    @patch('subprocess.run')
    def test_get_status_all_successful(self, mock_run):
        """Test get_status with all checks successful."""
        mock_run.return_value.returncode = 0
        
        checker = NetworkChecker()
        status = checker.get_status()
        
        expected = {
            'network_available': True,
            'repositories_accessible': True,
            'cache_valid': True
        }
        
        assert status == expected

    @patch('subprocess.run')
    def test_get_status_mixed_results(self, mock_run):
        """Test get_status with mixed results."""
        # Network available but repositories not accessible
        def side_effect(*args, **kwargs):
            command = args[0]
            if 'ping' in command:
                result = Mock()
                result.returncode = 0
                return result
            elif 'apt-get' in command:
                result = Mock()
                result.returncode = 1
                return result
        
        mock_run.side_effect = side_effect
        
        checker = NetworkChecker()
        status = checker.get_status()
        
        expected = {
            'network_available': True,
            'repositories_accessible': False,
            'cache_valid': True
        }
        
        assert status == expected

    def test_get_status_no_cache(self):
        """Test get_status when no cache exists."""
        checker = NetworkChecker()
        
        # Don't call any check methods, so cache should be invalid
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            status = checker.get_status()
        
        # Should run checks and populate cache
        assert 'network_available' in status
        assert 'repositories_accessible' in status
        assert 'cache_valid' in status
        assert status['cache_valid'] is True


class TestNetworkCheckerIntegration:
    """Integration tests for NetworkChecker."""

    @patch('subprocess.run')
    def test_network_checker_realistic_scenario_online(self, mock_run):
        """Test realistic scenario when online."""
        mock_run.return_value.returncode = 0
        
        checker = NetworkChecker()
        
        # Check network
        assert checker.is_network_available() is True
        
        # Check repositories
        assert checker.are_repositories_accessible() is True
        
        # Get overall status
        status = checker.get_status()
        assert status['network_available'] is True
        assert status['repositories_accessible'] is True

    @patch('subprocess.run')
    def test_network_checker_realistic_scenario_offline(self, mock_run):
        """Test realistic scenario when offline."""
        mock_run.return_value.returncode = 1
        
        checker = NetworkChecker()
        
        # Check network
        assert checker.is_network_available() is False
        
        # Check repositories (should also fail)
        assert checker.are_repositories_accessible() is False
        
        # Get overall status
        status = checker.get_status()
        assert status['network_available'] is False
        assert status['repositories_accessible'] is False

    @patch('subprocess.run')
    def test_network_checker_network_ok_repos_fail(self, mock_run):
        """Test scenario where network is OK but repositories fail."""
        def side_effect(*args, **kwargs):
            command = args[0]
            result = Mock()
            if 'ping' in command:
                result.returncode = 0  # Network OK
            elif 'apt-get' in command:
                result.returncode = 1  # Repositories fail
            return result
        
        mock_run.side_effect = side_effect
        
        checker = NetworkChecker()
        
        assert checker.is_network_available() is True
        assert checker.are_repositories_accessible() is False

    @patch('subprocess.run')
    def test_network_checker_command_parameters(self, mock_run):
        """Test that correct command parameters are used."""
        mock_run.return_value.returncode = 0
        
        checker = NetworkChecker()
        
        # Test network check command
        checker.is_network_available()
        
        # Verify ping command parameters
        network_call = mock_run.call_args_list[0]
        assert network_call[0][0] == ['ping', '-c', '1', '-W', '3', '8.8.8.8']
        assert network_call[1]['capture_output'] is True
        assert network_call[1]['timeout'] == 5
        
        # Test repository check command
        checker.are_repositories_accessible()
        
        # Verify apt-get command parameters
        repo_call = mock_run.call_args_list[1]
        assert repo_call[0][0] == ['apt-get', 'update', '--dry-run']
        assert repo_call[1]['capture_output'] is True
        assert repo_call[1]['text'] is True
        assert repo_call[1]['timeout'] == 10


class TestNetworkCheckerEdgeCases:
    """Test edge cases and error conditions."""

    @patch('subprocess.run')
    def test_network_checker_multiple_exceptions(self, mock_run):
        """Test handling multiple different exceptions."""
        exceptions = [
            subprocess.TimeoutExpired('ping', 5),
            FileNotFoundError("Command not found"),
            PermissionError("Permission denied"),
            OSError("System error")
        ]
        
        checker = NetworkChecker()
        
        for exception in exceptions:
            mock_run.side_effect = exception
            result = checker.is_network_available(force_check=True)
            assert result is False

    @patch('subprocess.run')
    def test_network_checker_zero_timeout(self, mock_run):
        """Test with very short timeout."""
        checker = NetworkChecker(cache_timeout=0)
        
        mock_run.return_value.returncode = 0
        
        # Even with zero timeout, should work
        result = checker.is_network_available()
        assert result is True

    @patch('subprocess.run')
    def test_network_checker_very_long_timeout(self, mock_run):
        """Test with very long cache timeout."""
        checker = NetworkChecker(cache_timeout=3600)  # 1 hour
        
        mock_run.return_value.returncode = 0
        
        result = checker.is_network_available()
        assert result is True
        assert checker.cache_timeout == 3600

    def test_network_checker_state_persistence(self):
        """Test that checker state is properly maintained."""
        checker = NetworkChecker()
        
        # Manually set state
        checker._network_available = True
        checker._repository_accessible = False
        
        # Verify state is maintained
        assert checker._network_available is True
        assert checker._repository_accessible is False
        
        # Clear cache should reset state
        checker.clear_cache()
        assert checker._network_available is None
        assert checker._repository_accessible is None

    @patch('subprocess.run')
    def test_network_checker_concurrent_access_simulation(self, mock_run):
        """Simulate concurrent access patterns."""
        mock_run.return_value.returncode = 0
        
        checker = NetworkChecker()
        
        # Simulate multiple rapid calls (as might happen in concurrent scenarios)
        results = []
        for _ in range(10):
            results.append(checker.is_network_available())
        
        # All should return same result
        assert all(result is True for result in results)
        
        # Should only call subprocess once due to caching
        assert mock_run.call_count == 1