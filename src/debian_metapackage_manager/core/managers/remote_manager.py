"""Remote system execution via SSH for package management."""

import subprocess
import json
import os
import threading
import time
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from ...models import OperationResult
from ...models import Package


class ConnectionState:
    """Manages the current connection state (local or remote)."""
    
    def __init__(self):
        """Initialize connection state."""
        self.is_remote = False
        self.current_connection: Optional[SSHConnection] = None
        self.state_file = os.path.expanduser('~/.config/debian-package-manager/connection-state.json')
        self._load_state()
    
    def connect_remote(self, host: str, user: str, key_path: Optional[str] = None, port: int = 22) -> bool:
        """Connect to remote system and set as current target."""
        connection = SSHConnection(host, user, key_path, port)
        
        if not connection.test_connection():
            return False
        
        self.current_connection = connection
        self.is_remote = True
        self._save_state()
        return True
    
    def disconnect(self) -> None:
        """Disconnect from remote system and return to local execution."""
        self.current_connection = None
        self.is_remote = False
        self._save_state()
    
    def get_current_target(self) -> str:
        """Get description of current execution target."""
        if self.is_remote and self.current_connection:
            return f"{self.current_connection.user}@{self.current_connection.host}:{self.current_connection.port}"
        return "local"
    
    def is_connected_remote(self) -> bool:
        """Check if currently connected to remote system."""
        return self.is_remote and self.current_connection is not None
    
    def get_connection(self) -> Optional['SSHConnection']:
        """Get current remote connection if any."""
        return self.current_connection if self.is_remote else None
    
    def _save_state(self) -> None:
        """Save connection state to file."""
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            
            state_data = {
                'is_remote': self.is_remote,
                'connection': None
            }
            
            if self.current_connection:
                state_data['connection'] = {
                    'host': self.current_connection.host,
                    'user': self.current_connection.user,
                    'key_path': self.current_connection.key_path,
                    'port': self.current_connection.port
                }
            
            with open(self.state_file, 'w') as f:
                json.dump(state_data, f, indent=2)
        except IOError:
            pass
    
    def _load_state(self) -> None:
        """Load connection state from file."""
        if not os.path.exists(self.state_file):
            return
        
        try:
            with open(self.state_file, 'r') as f:
                state_data = json.load(f)
            
            self.is_remote = state_data.get('is_remote', False)
            
            if self.is_remote and state_data.get('connection'):
                conn_data = state_data['connection']
                self.current_connection = SSHConnection(
                    host=conn_data['host'],
                    user=conn_data['user'],
                    key_path=conn_data.get('key_path'),
                    port=conn_data.get('port', 22)
                )
                
                # Test if connection is still valid
                if not self.current_connection.test_connection():
                    self.disconnect()
        except (json.JSONDecodeError, IOError, KeyError):
            self.disconnect()


class SSHConnection:
    """Manages SSH connection to a remote system."""
    
    def __init__(self, host: str, user: str, key_path: Optional[str] = None, port: int = 22):
        """Initialize SSH connection parameters."""
        self.host = host
        self.user = user
        self.key_path = key_path
        self.port = port
        self.connection_id = f"{user}@{host}:{port}"
        self._last_used = time.time()
        self._is_connected = False
    
    def test_connection(self) -> bool:
        """Test SSH connection to remote system."""
        try:
            cmd = self._build_ssh_command(['echo', 'connection_test'])
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            self._is_connected = result.returncode == 0
            return self._is_connected
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            self._is_connected = False
            return False
    
    def execute_command(self, command: List[str], timeout: int = 300) -> Tuple[int, str, str]:
        """Execute command on remote system."""
        try:
            ssh_cmd = self._build_ssh_command(command)
            result = subprocess.run(
                ssh_cmd, 
                capture_output=True, 
                text=True, 
                timeout=timeout
            )
            self._last_used = time.time()
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return -1, "", f"SSH execution failed: {str(e)}"
    
    def copy_file_to_remote(self, local_path: str, remote_path: str) -> bool:
        """Copy file to remote system using SCP."""
        try:
            scp_cmd = ['scp']
            if self.key_path:
                scp_cmd.extend(['-i', self.key_path])
            if self.port != 22:
                scp_cmd.extend(['-P', str(self.port)])
            
            scp_cmd.extend([local_path, f"{self.user}@{self.host}:{remote_path}"])
            
            result = subprocess.run(scp_cmd, capture_output=True, text=True, timeout=60)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            return False
    
    def _build_ssh_command(self, remote_command: List[str]) -> List[str]:
        """Build SSH command with proper options."""
        ssh_cmd = ['ssh']
        
        # Add SSH options
        ssh_cmd.extend([
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            '-o', 'ConnectTimeout=10'
        ])
        
        if self.key_path:
            ssh_cmd.extend(['-i', self.key_path])
        
        if self.port != 22:
            ssh_cmd.extend(['-p', str(self.port)])
        
        # Add host
        ssh_cmd.append(f"{self.user}@{self.host}")
        
        # Add remote command
        ssh_cmd.extend(remote_command)
        
        return ssh_cmd
    
    def is_alive(self) -> bool:
        """Check if connection is still alive."""
        return self._is_connected and (time.time() - self._last_used) < 300  # 5 minutes



class RemotePackageManager:
    """Manages package operations on remote systems."""
    
    def __init__(self):
        """Initialize remote package manager."""
        self.connection_state = ConnectionState()
    
    def execute_command(self, operation: str, package_name: str = '', **kwargs) -> OperationResult:
        """Execute package operation on current target (local or remote)."""
        # If not connected to remote, this shouldn't be called
        if not self.connection_state.is_connected_remote():
            return OperationResult(
                success=False,
                packages_affected=[],
                warnings=[],
                errors=["No remote connection active"]
            )
        
        connection = self.connection_state.get_connection()
        
        # Test connection first
        if not connection.test_connection():
            return OperationResult(
                success=False,
                packages_affected=[],
                warnings=[],
                errors=[f"Cannot connect to {connection.connection_id}"]
            )
        
        # Build remote command
        if operation == 'install':
            remote_cmd = self._build_install_command(package_name, **kwargs)
        elif operation == 'remove':
            remote_cmd = self._build_remove_command(package_name, **kwargs)
        elif operation == 'info':
            remote_cmd = self._build_info_command(package_name)
        elif operation == 'list':
            remote_cmd = self._build_list_command(**kwargs)
        elif operation == 'health':
            remote_cmd = self._build_health_command()
        elif operation == 'fix':
            remote_cmd = self._build_fix_command(**kwargs)
        elif operation == 'mode':
            remote_cmd = self._build_mode_command(**kwargs)
        elif operation == 'cleanup':
            remote_cmd = self._build_cleanup_command(**kwargs)
        else:
            return OperationResult(
                success=False,
                packages_affected=[],
                warnings=[],
                errors=[f"Unknown operation: {operation}"]
            )
        
        # Execute command
        return_code, stdout, stderr = connection.execute_command(remote_cmd)
        
        # Parse results
        return self._parse_command_result(operation, return_code, stdout, stderr)
    
    def connect(self, host: str, user: str, key_path: Optional[str] = None, port: int = 22) -> bool:
        """Connect to remote system."""
        return self.connection_state.connect_remote(host, user, key_path, port)
    
    def disconnect(self) -> None:
        """Disconnect from remote system."""
        self.connection_state.disconnect()
    
    def is_remote_connected(self) -> bool:
        """Check if connected to remote system."""
        return self.connection_state.is_connected_remote()
    
    def get_current_target(self) -> str:
        """Get current execution target description."""
        return self.connection_state.get_current_target()
    
    def sync_config_to_remote(self, local_config_path: str) -> bool:
        """Sync local configuration to current remote system."""
        if not self.connection_state.is_connected_remote():
            return False
        
        connection = self.connection_state.get_connection()
        remote_config_path = '/tmp/dpm-config.json'
        
        # Copy config file
        if not connection.copy_file_to_remote(local_config_path, remote_config_path):
            return False
        
        # Install config on remote system
        install_cmd = [
            'sudo', 'mkdir', '-p', '/etc/debian-package-manager', '&&',
            'sudo', 'cp', remote_config_path, '/etc/debian-package-manager/config.json', '&&',
            'rm', remote_config_path
        ]
        
        return_code, _, _ = connection.execute_command(install_cmd)
        return return_code == 0
    
    def _build_install_command(self, package_name: str, **kwargs) -> List[str]:
        """Build remote install command."""
        cmd = ['dpm', 'install', package_name]
        
        if kwargs.get('version'):
            cmd.extend(['--version', kwargs['version']])
        if kwargs.get('force'):
            cmd.append('--force')
        
        return cmd
    
    def _build_remove_command(self, package_name: str, **kwargs) -> List[str]:
        """Build remote remove command."""
        cmd = ['dpm', 'remove', package_name]
        
        if kwargs.get('force'):
            cmd.append('--force')
        if kwargs.get('purge'):
            cmd.append('--purge')
        
        return cmd
    
    def _build_info_command(self, package_name: str) -> List[str]:
        """Build remote info command."""
        return ['dpm', 'info', package_name, '--dependencies']
    
    def _build_list_command(self, **kwargs) -> List[str]:
        """Build remote list command."""
        cmd = ['dpm', 'list']
        
        if kwargs.get('all'):
            cmd.append('--all')
        if kwargs.get('broken'):
            cmd.append('--broken')
        if kwargs.get('metapackages'):
            cmd.append('--metapackages')
        if kwargs.get('simple'):
            cmd.append('--simple')
        
        return cmd
    
    def _build_health_command(self) -> List[str]:
        """Build remote health command."""
        return ['dpm', 'health', '--verbose']
    
    def _build_fix_command(self, **kwargs) -> List[str]:
        """Build remote fix command."""
        cmd = ['dpm', 'fix']
        if kwargs.get('force'):
            cmd.append('--force')
        return cmd
    
    def _build_mode_command(self, **kwargs) -> List[str]:
        """Build remote mode command."""
        cmd = ['dpm', 'mode']
        if kwargs.get('status'):
            cmd.append('--status')
        if kwargs.get('offline'):
            cmd.append('--offline')
        if kwargs.get('online'):
            cmd.append('--online')
        if kwargs.get('auto'):
            cmd.append('--auto')
        return cmd
    
    def _build_cleanup_command(self, **kwargs) -> List[str]:
        """Build remote cleanup command."""
        cmd = ['dpm', 'cleanup']
        if kwargs.get('all'):
            cmd.append('--all')
        if kwargs.get('apt_cache'):
            cmd.append('--apt-cache')
        if kwargs.get('offline_repos'):
            cmd.append('--offline-repos')
        if kwargs.get('artifactory'):
            cmd.append('--artifactory')
        if kwargs.get('aggressive'):
            cmd.append('--aggressive')
        return cmd
    
    def _parse_command_result(self, operation: str, return_code: int, stdout: str, stderr: str) -> OperationResult:
        """Parse command result into OperationResult."""
        success = return_code == 0
        errors = []
        warnings = []
        packages_affected = []
        
        if not success:
            errors.append(f"Command failed with exit code {return_code}")
            if stderr:
                errors.append(stderr.strip())
        
        # Parse stdout for package information
        if stdout:
            lines = stdout.strip().split('\n')
            for line in lines:
                if 'warning' in line.lower():
                    warnings.append(line.strip())
                elif operation in ['install', 'remove'] and ('✓' in line or '✗' in line):
                    # Extract package name from status line
                    parts = line.split()
                    if len(parts) >= 2:
                        package_name = parts[1]
                        packages_affected.append(Package(
                            name=package_name,
                            version="unknown",
                            status="unknown",
                            is_custom=False,
                            is_metapackage=False
                        ))
        
        return OperationResult(
            success=success,
            packages_affected=packages_affected,
            warnings=warnings,
            errors=errors,
            details={'stdout': stdout, 'stderr': stderr}
        )