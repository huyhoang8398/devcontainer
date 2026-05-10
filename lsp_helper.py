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
                "install": "pip install basedpyright",
                "command": ["/usr/local/bin/basedpyright-langserver", "--stdio"],
                "selector": "source.python"
            }
        },
        "javascript": {
            "typescript-language-server": {
                "install": "npm install -g typescript-language-server typescript",
                "command": ["typescript-language-server", "--stdio"],
                "selector": "source.js"
            }
        },
        "typescript": {
            "typescript-language-server": {
                "install": "npm install -g typescript-language-server typescript",
                "command": ["typescript-language-server", "--stdio"],
                "selector": "source.ts"
            }
        },
        "rust": {
            "rust-analyzer": {
                "install": "rustup component add rust-analyzer",
                "command": ["rust-analyzer"],
                "selector": "source.rust"
            }
        },
        "go": {
            "gopls": {
                "install": "go install golang.org/x/tools/gopls@latest",
                "command": ["gopls"],
                "selector": "source.go"
            }
        },
        "c++": {
            "clangd": {
                "install": "apt-get update && apt-get install -y clangd",
                "command": ["clangd"],
                "selector": "source.c++, source.c"
            }
        },
        "ruby": {
            "solargraph": {
                "install": "gem install solargraph",
                "command": ["solargraph", "stdio"],
                "selector": "source.ruby"
            }
        },
        "java": {
            "jdtls": {
                "install": "",
                "command": ["jdtls"],
                "selector": "source.java"
            }
        }
    }
    
    @classmethod
    def detect_project_languages(cls, workspace_folder: str) -> set:
        """Detect project languages from file extensions"""
        from . import devcontainer
        import os
        
        languages = set()
        
        # Extensions to language mapping
        ext_to_lang = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.rs': 'rust',
            '.go': 'go',
            '.rb': 'ruby',
            '.java': 'java',
            '.cpp': 'c++',
            '.c': 'c++',
            '.h': 'c++',
        }
        
        # Folders to skip
        skip_dirs = {'.git', '.venv', 'venv', 'node_modules', '__pycache__', 
                     '.pytest_cache', 'dist', 'build', '.egg-info'}
        
        try:
            workspace = Path(workspace_folder).resolve()
            
            # Use os.walk for Python 3.11 compatibility
            for root, dirs, files in os.walk(workspace):
                # Remove skip directories from traversal
                dirs[:] = [d for d in dirs if d not in skip_dirs]
                
                # Check files
                for file in files:
                    ext = Path(file).suffix.lower()
                    if ext in ext_to_lang:
                        lang = ext_to_lang[ext]
                        languages.add(lang)
                        devcontainer.log(f"Detected language: {lang} (*.{ext})")
            
            if languages:
                devcontainer.log(f"Project languages detected: {sorted(languages)}")
            else:
                devcontainer.log("No supported languages detected", "warning")
            
            return languages
            
        except Exception as e:
            devcontainer.log(f"Error detecting languages: {e}", "error")
            import traceback
            devcontainer.log(traceback.format_exc(), "debug")
            return set()
    
    @classmethod
    def install_lsp_server(cls, container_id: str, language: str, 
                          server_name: str, runtime: str = "podman"):
        """Install LSP server in container"""
        from . import devcontainer
        
        if language not in cls.LSP_SERVERS:
            devcontainer.log(f"Unknown language: {language}", "warning")
            return False
        
        if server_name not in cls.LSP_SERVERS[language]:
            devcontainer.log(f"Unknown LSP server for {language}: {server_name}", "warning")
            return False
        
        server_config = cls.LSP_SERVERS[language][server_name]
        install_cmd = server_config.get("install", "")
        
        if not install_cmd:
            devcontainer.log(f"No installation command for {server_name}")
            return True
        
        # Execute installation in container
        cmd = [runtime, "exec", "-i", container_id, "sh", "-c", install_cmd]
        
        try:
            devcontainer.log(f"Installing {server_name} in container {container_id[:12]}...")
            devcontainer.log(f"Install command: {install_cmd}", "debug")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                devcontainer.log(f"✓ Successfully installed {server_name}")
                return True
            else:
                devcontainer.log(f"Installation failed for {server_name}", "warning")
                if result.stderr:
                    devcontainer.log(f"Error output: {result.stderr[:200]}", "debug")
                return False
        except subprocess.TimeoutExpired:
            devcontainer.log(f"Installation timeout for {server_name}", "error")
            return False
        except Exception as e:
            devcontainer.log(f"Error installing {server_name}: {e}", "error")
            return False

    @classmethod
    def generate_lsp_config(cls, container_name: str,
                           languages: List[str], 
                           runtime: str = "podman",
                           workspace_folder: str = None) -> Dict:
    
        lsp_config = {"clients": {}}
    
        for language in languages:
            if language not in cls.LSP_SERVERS:
                continue
    
            for server_name, server_config in cls.LSP_SERVERS[language].items():
                client_name = f"{language}-{server_name}"
    
                server_command = server_config["command"]
    
                remote_cmd = [
                    runtime, "exec", "-i",
                    "--workdir", workspace_folder,   # Same path
                    container_name
                ] + server_command
    
                lsp_config["clients"][client_name] = {
                    "enabled": True,
                    "command": remote_cmd,
                    "selector": server_config["selector"],
    
                    # No pathMap needed anymore!
                    "rootPath": workspace_folder,
                    "rootUri": f"file://{workspace_folder}",
    
                    "initializationOptions": {
                        "rootUri": f"file://{workspace_folder}",
                        "rootPath": workspace_folder
                    },
    
                    "workspaceFolders": [
                        {
                            "name": "workspace",
                            "uri": f"file://{workspace_folder}"
                        }
                    ],
    
                    "env": {
                        "DEVCONTAINER_ID": container_name,
                        "WORKSPACE_PATH": workspace_folder
                    }
                }
    
        return lsp_config

    @classmethod
    def update_lsp_settings(cls, lsp_config: Dict) -> bool:
        """Update LSP package settings with container configuration"""
        from . import devcontainer
        
        try:
            # Load current LSP settings
            lsp_settings = sublime.load_settings("LSP.sublime-settings")
            
            current_clients = lsp_settings.get("clients", {})
            
            # IMPORTANT: Only add our devcontainer clients, don't remove others
            for client_name, client_config in lsp_config["clients"].items():
                current_clients[client_name] = client_config
            
            lsp_settings.set("clients", current_clients)
            sublime.save_settings("LSP.sublime-settings")
            
            devcontainer.log(f"✓ LSP settings updated with {len(lsp_config['clients'])} client(s)")
            return True
        except Exception as e:
            devcontainer.log(f"Error updating LSP settings: {e}", "error")
            import traceback
            devcontainer.log(traceback.format_exc(), "debug")
            return False


class LSPWorkspaceMapper:
    """Maps local workspace paths to container paths"""
    
    def __init__(self, workspace_mount: str):
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
        
        try:
            local = Path(local_path).resolve()
            local_workspace = Path(self.local_path).resolve()
            
            if not str(local).startswith(str(local_workspace)):
                return None
            
            relative = local.relative_to(local_workspace)
            container = Path(self.container_path) / relative
            
            return str(container)
        except Exception:
            return None
    
    def container_to_local(self, container_path: str) -> Optional[str]:
        """Convert container path to local path"""
        if not self.local_path or not self.container_path:
            return None
        
        try:
            container = Path(container_path)
            container_workspace = Path(self.container_path)
            
            if not str(container).startswith(str(container_workspace)):
                return None
            
            relative = container.relative_to(container_workspace)
            local = Path(self.local_path) / relative
            
            return str(local)
        except Exception:
            return None

    def rewrite_uri(self, uri: str) -> str:
        """
        Convert host file URIs to container URIs
        """
        if uri.startswith("file://"):
            path = uri[7:]
        else:
            path = uri
    
        converted = self.local_to_container(path)
        if converted:
            return "file://" + converted
    
        return uri

def setup_lsp_for_devcontainer(container_id: str, config: Dict,
                               workspace_folder: str, workspace_mount: str, 
                               runtime: str = "podman") -> bool:
    """
    Setup LSP integration for a devcontainer
    """
    from . import devcontainer
    
    try:
        devcontainer.log(f"Starting LSP setup for container {container_id[:12]}...")
        
        # Get settings
        settings = sublime.load_settings("DevContainer.sublime-settings")
        lsp_config = settings.get("lsp", {})
        
        if not lsp_config.get("auto_configure", True):
            devcontainer.log("LSP auto-configuration is disabled")
            return True
        
        # Detect project languages
        detected_languages = LSPServerManager.detect_project_languages(workspace_folder)
        
        if not detected_languages:
            devcontainer.log("No supported languages detected in project", "warning")
            return False
        
        devcontainer.log(f"Detected project languages: {sorted(detected_languages)}")
        
        # Get configured servers
        default_servers = lsp_config.get("default_servers", {})
        
        if not default_servers:
            devcontainer.log("No default LSP servers configured", "warning")
            return False
        
        # Only install servers for detected languages
        languages_to_install = [lang for lang in detected_languages if lang in default_servers]
        
        if not languages_to_install:
            devcontainer.log("No configured LSP servers for detected languages", "warning")
            return False
        
        devcontainer.log(f"Will install LSP servers for: {languages_to_install}")
        
        # Install LSP servers with retry
        import time
        for language in languages_to_install:
            servers = default_servers[language]
            if isinstance(servers, list) and servers:
                server = servers[0]
            else:
                continue
            
            # Retry installation up to 3 times
            for attempt in range(3):
                success = LSPServerManager.install_lsp_server(
                    container_id, language, server, runtime
                )
                if success:
                    break
                if attempt < 2:
                    time.sleep(2)
                    devcontainer.log(f"Retrying {server} installation (attempt {attempt + 2}/3)")
            else:
                devcontainer.log(f"Warning: Failed to install {server} for {language} after 3 attempts", "warning")
        
        # Wait longer for all installations to complete
        time.sleep(3)  # Increased from 1 second
        
        # Generate LSP configuration
        lsp_settings = LSPServerManager.generate_lsp_config(
            container_id, 
            languages_to_install, 
            runtime,
            workspace_folder=workspace_folder   # Pass the real host path
        )

        # Update Sublime's LSP settings
        if lsp_settings["clients"]:
            success = LSPServerManager.update_lsp_settings(lsp_settings)
            if success:
                devcontainer.log(f"✓ LSP setup complete with {len(lsp_settings['clients'])} server(s)")
                return True
            else:
                devcontainer.log("Failed to update LSP settings", "error")
                return False
        else:
            devcontainer.log("No LSP clients generated", "warning")
            return False
            
    except Exception as e:
        devcontainer.log(f"Error during LSP setup: {e}", "error")
        import traceback
        devcontainer.log(traceback.format_exc(), "debug")
        return False