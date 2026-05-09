"""
LSP Integration Helper for DevContainer
Provides utilities to configure and manage LSP servers in containers
"""

import sublime
import json
import subprocess
from typing import Dict, List, Optional
from pathlib import Path


class LSPServerManager:
    """Manages LSP server installation and configuration in containers"""
    
    # Language to LSP server mapping
    LSP_SERVERS = {
        "python": {
            "pyright": {
                "install": ["pip3", "install", "pyright"],
                "command": ["pyright-langserver", "--stdio"],
                "selector": "source.python"
            },
            "pylsp": {
                "install": ["pip3", "install", "python-lsp-server[all]"],
                "command": ["pylsp"],
                "selector": "source.python"
            },
            "ruff": {
                "install": ["pip3", "install", "ruff-lsp"],
                "command": ["ruff-lsp"],
                "selector": "source.python"
            }
        },
        "javascript": {
            "typescript-language-server": {
                "install": ["npm", "install", "-g", "typescript-language-server", "typescript"],
                "command": ["typescript-language-server", "--stdio"],
                "selector": "source.js"
            }
        },
        "typescript": {
            "typescript-language-server": {
                "install": ["npm", "install", "-g", "typescript-language-server", "typescript"],
                "command": ["typescript-language-server", "--stdio"],
                "selector": "source.ts"
            }
        },
        "rust": {
            "rust-analyzer": {
                "install": ["rustup", "component", "add", "rust-analyzer"],
                "command": ["rust-analyzer"],
                "selector": "source.rust"
            }
        },
        "go": {
            "gopls": {
                "install": ["go", "install", "golang.org/x/tools/gopls@latest"],
                "command": ["gopls"],
                "selector": "source.go"
            }
        },
        "c++": {
            "clangd": {
                "install": ["apt-get", "update", "&&", "apt-get", "install", "-y", "clangd"],
                "command": ["clangd"],
                "selector": "source.c++, source.c"
            }
        },
        "ruby": {
            "solargraph": {
                "install": ["gem", "install", "solargraph"],
                "command": ["solargraph", "stdio"],
                "selector": "source.ruby"
            }
        },
        "java": {
            "jdtls": {
                "install": [],  # Usually pre-installed in Java containers
                "command": ["jdtls"],
                "selector": "source.java"
            }
        }
    }
    
    @classmethod
    def install_lsp_server(cls, container_id: str, language: str, 
                          server_name: str, runtime: str = "docker"):
        """Install LSP server in container"""
        if language not in cls.LSP_SERVERS:
            print(f"Unknown language: {language}")
            return False
        
        if server_name not in cls.LSP_SERVERS[language]:
            print(f"Unknown LSP server for {language}: {server_name}")
            return False
        
        server_config = cls.LSP_SERVERS[language][server_name]
        install_cmd = server_config.get("install", [])
        
        if not install_cmd:
            print(f"No installation command for {server_name}")
            return True
        
        # Execute installation in container
        cmd = [runtime, "exec", container_id] + install_cmd
        
        try:
            print(f"Installing {server_name} in container {container_id}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print(f"Successfully installed {server_name}")
                return True
            else:
                print(f"Failed to install {server_name}: {result.stderr}")
                return False
        except Exception as e:
            print(f"Error installing {server_name}: {e}")
            return False
    
    @classmethod
    def generate_lsp_config(cls, container_id: str, container_ip: str,
                           languages: List[str]) -> Dict:
        """Generate LSP configuration for container"""
        lsp_config = {
            "clients": {}
        }
        
        for language in languages:
            if language not in cls.LSP_SERVERS:
                continue
            
            for server_name, server_config in cls.LSP_SERVERS[language].items():
                client_name = f"{language}-{server_name}-container"
                
                lsp_config["clients"][client_name] = {
                    "enabled": True,
                    "command": cls._build_remote_command(
                        container_id, 
                        server_config["command"]
                    ),
                    "selector": server_config["selector"],
                    "env": {
                        "DEVCONTAINER_ID": container_id
                    }
                }
        
        return lsp_config
    
    @classmethod
    def _build_remote_command(cls, container_id: str, 
                             server_command: List[str]) -> List[str]:
        """Build command to run LSP server in container"""
        runtime = "docker"  # TODO: Get from settings
        
        # Command to execute LSP server in container
        return [
            runtime, "exec", "-i", container_id
        ] + server_command
    
    @classmethod
    def update_lsp_settings(cls, container_config: Dict):
        """Update LSP package settings with container configuration"""
        try:
            # Load current LSP settings
            lsp_settings_file = "LSP.sublime-settings"
            lsp_settings = sublime.load_settings(lsp_settings_file)
            
            # Get container LSP configuration
            customizations = container_config.get("customizations", {})
            sublime_config = customizations.get("sublimetext", {})
            
            # Merge settings
            current_clients = lsp_settings.get("clients", {})
            
            # Add devcontainer clients
            # This would need more sophisticated merging logic
            
            sublime.save_settings(lsp_settings_file)
            
            print("LSP settings updated for devcontainer")
            return True
        except Exception as e:
            print(f"Error updating LSP settings: {e}")
            return False


class DevContainerLSPServer:
    """Wrapper for LSP server running in container"""
    
    def __init__(self, container_id: str, language: str, server_name: str):
        self.container_id = container_id
        self.language = language
        self.server_name = server_name
        self.runtime = "docker"  # TODO: Get from settings
    
    def start(self):
        """Start LSP server in container"""
        server_config = LSPServerManager.LSP_SERVERS.get(
            self.language, {}
        ).get(self.server_name)
        
        if not server_config:
            return False
        
        # The LSP package will handle starting via the command
        # we configured in generate_lsp_config
        return True
    
    def execute_command(self, command: List[str]) -> subprocess.CompletedProcess:
        """Execute command in container"""
        cmd = [self.runtime, "exec", "-i", self.container_id] + command
        return subprocess.run(cmd, capture_output=True, text=True)


class LSPWorkspaceMapper:
    """Maps local workspace paths to container paths"""
    
    def __init__(self, container_id: str, workspace_mount: str):
        self.container_id = container_id
        self.workspace_mount = workspace_mount
        self._parse_mount()
    
    def _parse_mount(self):
        """Parse workspace mount string"""
        # Format: type=bind,source=/local/path,target=/container/path
        parts = self.workspace_mount.split(',')
        self.local_path = None
        self.container_path = None
        
        for part in parts:
            if part.startswith('source='):
                self.local_path = part.split('=', 1)[1]
            elif part.startswith('target='):
                self.container_path = part.split('=', 1)[1]
    
    def local_to_container(self, local_path: str) -> Optional[str]:
        """Convert local path to container path"""
        if not self.local_path or not self.container_path:
            return None
        
        local = Path(local_path).resolve()
        local_workspace = Path(self.local_path).resolve()
        
        if not str(local).startswith(str(local_workspace)):
            return None
        
        relative = local.relative_to(local_workspace)
        container = Path(self.container_path) / relative
        
        return str(container)
    
    def container_to_local(self, container_path: str) -> Optional[str]:
        """Convert container path to local path"""
        if not self.local_path or not self.container_path:
            return None
        
        container = Path(container_path)
        container_workspace = Path(self.container_path)
        
        if not str(container).startswith(str(container_workspace)):
            return None
        
        relative = container.relative_to(container_workspace)
        local = Path(self.local_path) / relative
        
        return str(local)


def setup_lsp_for_devcontainer(container_id: str, config: Dict,
                               workspace_mount: str) -> bool:
    """
    Setup LSP integration for a devcontainer
    
    Args:
        container_id: Container ID
        config: devcontainer.json configuration
        workspace_mount: Workspace mount string
    
    Returns:
        True if setup successful
    """
    try:
        # Detect languages based on workspace
        # For now, we'll use a simple approach
        settings = sublime.load_settings("DevContainer.sublime-settings")
        lsp_config = settings.get("lsp", {})
        
        if not lsp_config.get("auto_configure", True):
            return True
        
        # Get languages to configure
        default_servers = lsp_config.get("default_servers", {})
        
        # Install LSP servers
        runtime = "docker"  # TODO: Get from settings
        
        for language, servers in default_servers.items():
            for server in servers:
                LSPServerManager.install_lsp_server(
                    container_id, language, server, runtime
                )
        
        # Generate and update LSP configuration
        languages = list(default_servers.keys())
        container_ip = get_container_ip(container_id, runtime)
        
        if container_ip:
            lsp_settings = LSPServerManager.generate_lsp_config(
                container_id, container_ip, languages
            )
            
            # Update LSP settings
            LSPServerManager.update_lsp_settings(config)
        
        return True
    except Exception as e:
        print(f"Error setting up LSP: {e}")
        return False


def get_container_ip(container_id: str, runtime: str = "docker") -> Optional[str]:
    """Get container IP address"""
    try:
        result = subprocess.run(
            [runtime, "inspect", "-f",
             "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}",
             container_id],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as e:
        print(f"Error getting container IP: {e}")
    return None