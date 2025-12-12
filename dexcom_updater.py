"""
Dexcom Plugin Update Manager
Handles version checking, updates, backups, and rollbacks.
"""

import json
import shutil
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class ConfigManager:
    """Manages plugin configuration stored in config.json"""
    
    def __init__(self, config_file: Path):
        self.config_file = config_file
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
    
    def load(self) -> Dict:
        """Load configuration from file, or create default if not exists."""
        if not self.config_file.exists():
            return self._create_default_config()
        
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            self._log(f"Error loading config: {e}. Creating new config.")
            return self._create_default_config()
    
    def save(self, config: Dict) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except IOError as e:
            self._log(f"Error saving config: {e}")
    
    def _create_default_config(self, version: str = "1.0.0") -> Dict:
        """Create default configuration."""
        config = {
            "version": version,
            "last_check": 0,
            "first_run_after_update": False,
            "backup_version": None,
            "dependencies": {
                "pip": ["pydexcom", "sparklines"],
                "homebrew": []
            }
        }
        self.save(config)
        return config
    
    def _log(self, message: str) -> None:
        """Write message to update log."""
        log_file = self.config_file.parent / "update.log"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(log_file, 'a') as f:
                f.write(f"[{timestamp}] {message}\n")
        except IOError:
            pass


class UpdateChecker:
    """Checks for plugin updates from GitHub releases."""
    
    def __init__(self, current_version: str, api_url: str):
        self.current_version = current_version
        self.api_url = api_url
    
    def check_for_updates(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Check if a new version is available.
        
        Returns:
            Tuple of (update_available, new_version, download_url)
            
        Note: GitHub API rate limit is 60 requests/hour for unauthenticated requests.
        Weekly checks ensure we stay well within this limit.
        """
        try:
            req = urllib.request.Request(self.api_url)
            req.add_header('Accept', 'application/vnd.github.v3+json')
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                
            latest_version = data.get('tag_name', '').lstrip('v')
            download_url = None
            
            # Find the plugin file in release assets
            for asset in data.get('assets', []):
                if asset['name'] == 'dexcom.5m.py':
                    download_url = asset['browser_download_url']
                    break
            
            # If no asset found, construct raw GitHub URL
            if not download_url and latest_version:
                repo = self.api_url.split('/repos/')[1].split('/releases')[0]
                download_url = f"https://raw.githubusercontent.com/{repo}/v{latest_version}/dexcom.5m.py"
            
            if latest_version and self._is_newer_version(latest_version):
                return True, latest_version, download_url
            
            return False, None, None
            
        except (urllib.error.URLError, json.JSONDecodeError, KeyError) as e:
            # Silently fail - don't interrupt glucose reading
            return False, None, None
    
    def _is_newer_version(self, remote_version: str) -> bool:
        """Compare version strings (semantic versioning)."""
        try:
            current_parts = [int(x) for x in self.current_version.split('.')]
            remote_parts = [int(x) for x in remote_version.split('.')]
            
            # Pad to same length
            while len(current_parts) < len(remote_parts):
                current_parts.append(0)
            while len(remote_parts) < len(current_parts):
                remote_parts.append(0)
            
            return remote_parts > current_parts
        except (ValueError, AttributeError):
            return False


class DependencyManager:
    """Manages package dependencies (pip and Homebrew)."""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
    
    def get_current_dependencies(self) -> Dict[str, List[str]]:
        """Get currently tracked dependencies."""
        config = self.config_manager.load()
        return config.get('dependencies', {'pip': [], 'homebrew': []})
    
    def update_dependencies(self, new_deps: Dict[str, List[str]]) -> None:
        """Update tracked dependencies."""
        config = self.config_manager.load()
        config['dependencies'] = new_deps
        self.config_manager.save(config)
    
    def get_dependency_changes(self, new_deps: Dict[str, List[str]]) -> Dict[str, Dict[str, List[str]]]:
        """
        Compare current and new dependencies to find what changed.
        
        Returns:
            Dict with 'added' and 'removed' keys, each containing pip/homebrew lists
        """
        current = self.get_current_dependencies()
        changes = {
            'added': {'pip': [], 'homebrew': []},
            'removed': {'pip': [], 'homebrew': []}
        }
        
        for pkg_type in ['pip', 'homebrew']:
            current_pkgs = set(current.get(pkg_type, []))
            new_pkgs = set(new_deps.get(pkg_type, []))
            
            changes['added'][pkg_type] = list(new_pkgs - current_pkgs)
            changes['removed'][pkg_type] = list(current_pkgs - new_pkgs)
        
        return changes
    
    def format_removal_commands(self, packages_to_remove: Dict[str, List[str]]) -> List[str]:
        """Generate commands for removing packages."""
        commands = []
        
        if packages_to_remove.get('pip'):
            for pkg in packages_to_remove['pip']:
                commands.append(f"python3 -m pip uninstall -y {pkg}")
        
        if packages_to_remove.get('homebrew'):
            for pkg in packages_to_remove['homebrew']:
                commands.append(f"brew uninstall {pkg}")
        
        return commands


class UpdateInstaller:
    """Handles plugin update installation and rollback."""
    
    def __init__(self, config_manager: ConfigManager, dep_manager: DependencyManager,
                 plugin_file: Path, backup_dir: Path):
        self.config_manager = config_manager
        self.dep_manager = dep_manager
        self.plugin_file = plugin_file
        self.backup_dir = backup_dir
        self.config_file = config_manager.config_file
    
    def create_backup(self) -> bool:
        """Create backup of current plugin, delete old backup first."""
        try:
            # Delete old backup if exists
            if self.backup_dir.exists():
                shutil.rmtree(self.backup_dir)
            
            # Create new backup
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            if self.plugin_file.exists():
                shutil.copy2(self.plugin_file, self.backup_dir / "dexcom.5m.py")
            
            if self.config_file.exists():
                shutil.copy2(self.config_file, self.backup_dir / "config.json")
            
            # Update config with backup info
            config = self.config_manager.load()
            config['backup_version'] = config.get('version', '1.0.0')
            self.config_manager.save(config)
            
            return True
        except (IOError, OSError) as e:
            self._log(f"Backup failed: {e}")
            return False
    
    def install_update(self, download_url: str, new_version: str) -> bool:
        """Download and install new plugin version."""
        try:
            # Download new version
            req = urllib.request.Request(download_url)
            with urllib.request.urlopen(req, timeout=30) as response:
                new_plugin_content = response.read()
            
            # Validate downloaded content
            if len(new_plugin_content) < 100:  # Basic sanity check
                self._log("Downloaded file is suspiciously small")
                return False
            
            # Install new version
            with open(self.plugin_file, 'wb') as f:
                f.write(new_plugin_content)
            
            # Make executable
            self.plugin_file.chmod(0o755)
            
            # Update config
            config = self.config_manager.load()
            config['version'] = new_version
            config['first_run_after_update'] = True
            self.config_manager.save(config)
            
            self._log(f"Successfully updated to version {new_version}")
            return True
            
        except (urllib.error.URLError, IOError, OSError) as e:
            self._log(f"Update installation failed: {e}")
            return False
    
    def rollback(self) -> bool:
        """Restore previous version from backup."""
        try:
            backup_plugin = self.backup_dir / "dexcom.5m.py"
            backup_config = self.backup_dir / "config.json"
            
            if not backup_plugin.exists():
                self._log("No backup found for rollback")
                return False
            
            # Restore plugin
            shutil.copy2(backup_plugin, self.plugin_file)
            
            # Restore config if exists
            if backup_config.exists():
                shutil.copy2(backup_config, self.config_file)
            
            self._log("Rollback successful")
            return True
            
        except (IOError, OSError) as e:
            self._log(f"Rollback failed: {e}")
            return False
    
    def _log(self, message: str) -> None:
        """Write message to update log."""
        log_file = self.config_file.parent / "update.log"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(log_file, 'a') as f:
                f.write(f"[{timestamp}] {message}\n")
        except IOError:
            pass
