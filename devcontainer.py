"""
Sublime DevContainer Plugin
Provides devcontainer support similar to VS Code's remote container development
with LSP integration for Sublime Text 4
"""

import sublime
import sublime_plugin
import json
import os
import subprocess
import threading
import tempfile
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple


SETTINGS_FILE = "DevContainer.sublime-settings"
PLUGIN_NAME = "DevContainer"


def plugin_loaded():
    """Called when plugin is loaded"""
    log("DevContainer plugin loaded")
    
def plugin_unloaded():
    """Called when plugin is unloaded"""
    log("DevContainer plugin unloaded")
    # Clean up any running containers if configured
    settings = sublime.load_settings(SETTINGS_FILE)
    if settings.get("clean_on_exit", False):
        ContainerManager.stop_all_containers()


def log(message: str, level: str = "info"):
    """Log messages to console"""
    settings = sublime.load_settings(SETTINGS_FILE)
    log_level = settings.get("log_level", "info")
    
    levels = {"debug": 0, "info": 1, "warning": 2, "error": 3}
    if levels.get(level, 1) >= levels.get(log_level, 1):
        print(f"[{PLUGIN_NAME}] [{level.upper()}] {message}")


class DevContainerConfig:
    """Handles devcontainer.json configuration"""
    
    @staticmethod
    def find_config(start_path: str) -> Optional[Path]:
        """Find devcontainer.json file"""
        settings = sublime.load_settings(SETTINGS_FILE)
        disable_recursive = settings.get("disable_recursive_config_search", False)
        
        current = Path(start_path).resolve()
        
        # Check common locations
        candidates = [
            current / ".devcontainer.json",
            current / ".devcontainer" / "devcontainer.json"
        ]
        
        for candidate in candidates:
            if candidate.exists():
                log(f"Found devcontainer config: {candidate}")
                return candidate
        
        # Recursive search if enabled
        if not disable_recursive:
            while current.parent != current:
                current = current.parent
                for candidate in [
                    current / ".devcontainer.json",
                    current / ".devcontainer" / "devcontainer.json"
                ]:
                    if candidate.exists():
                        log(f"Found devcontainer config: {candidate}")
                        return candidate
        
        return None
    
    @staticmethod
    def load_config(config_path: Path) -> Optional[Dict]:
        """Load and parse devcontainer.json"""
        try:
            with open(config_path, 'r') as f:
                # Remove comments for JSON parsing
                content = f.read()
                # Simple comment removal (doesn't handle all edge cases)
                lines = []
                for line in content.split('\n'):
                    # Remove line comments
                    if '//' in line:
                        line = line[:line.index('//')]
                    lines.append(line)
                clean_content = '\n'.join(lines)
                
                config = json.loads(clean_content)
                log(f"Loaded devcontainer config: {config.get('name', 'unnamed')}")
                return config
        except Exception as e:
            log(f"Error loading config: {e}", "error")
            return None
    
    @staticmethod
    def create_default_config(workspace_folder: str) -> Dict:
        """Create a default devcontainer.json configuration"""
        settings = sublime.load_settings(SETTINGS_FILE)
        template_provider = settings.get("devcontainer_json_template")
        
        if template_provider:
            # Use custom template if provided
            return template_provider()
        
        # Default template
        return {
            "name": Path(workspace_folder).name,
            "image": "mcr.microsoft.com/devcontainers/base:ubuntu",
            "customizations": {
                "sublimetext": {
                    "extensions": [],
                    "settings": {}
                }
            },
            "forwardPorts": [],
            "postCreateCommand": "",
            "remoteUser": "root"
        }


class ContainerRuntime:
    """Manages container runtime (Docker/Podman)"""
    
    @staticmethod
    def detect_runtime() -> str:
        """Detect available container runtime"""
        settings = sublime.load_settings(SETTINGS_FILE)
        runtime = settings.get("container_runtime")
        
        if runtime:
            return runtime
        
        # Try to detect
        for cmd in ["podman", "docker"]:
            try:
                result = subprocess.run([cmd, "--version"], 
                                      capture_output=True, 
                                      timeout=5)
                if result.returncode == 0:
                    log(f"Detected container runtime: {cmd}")
                    return cmd
            except:
                pass
        
        log("No container runtime detected", "warning")
        return "docker"  # default
    
    @staticmethod
    def detect_compose() -> str:
        """Detect available compose command"""
        settings = sublime.load_settings(SETTINGS_FILE)
        compose = settings.get("compose_command")
        
        if compose:
            return compose
        
        # Try to detect
        for cmd in ["podman-compose", "docker-compose"]:
            try:
                result = subprocess.run([cmd, "--version"], 
                                      capture_output=True, 
                                      timeout=5)
                if result.returncode == 0:
                    log(f"Detected compose command: {cmd}")
                    return cmd
            except:
                pass
        
        return "docker-compose"  # default


class ContainerManager:
    """Manages container lifecycle"""
    
    _active_containers = {}  # Changed to dict for metadata storage
    
    @classmethod
    def build_container(cls, config: Dict, config_path: Path, 
                       callback=None) -> Optional[str]:
        """Build container from config"""
        runtime = ContainerRuntime.detect_runtime()
        
        # Handle different config types
        if "dockerComposeFile" in config:
            return cls._build_compose(config, config_path, callback)
        elif "image" in config:
            return cls._run_from_image(config, config_path, callback)
        elif "build" in config or "dockerfile" in config:
            return cls._build_from_dockerfile(config, config_path, callback)
        else:
            log("Unknown container configuration type", "error")
            return None
    
    @classmethod
    def _run_from_image(cls, config: Dict, config_path: Path, 
                       callback=None) -> Optional[str]:
        """Run container from image"""
        runtime = ContainerRuntime.detect_runtime()
        image = config.get("image")
        name = config.get("name", "devcontainer")
        
        # Build docker run command
        cmd = [runtime, "run", "-d", "--name", name]
        
        # Add workspace mount
        workspace = config_path.parent.parent.resolve()
        workspace_str = str(workspace)        

        workspace_mount = config.get("workspaceMount", 
                                    f"type=bind,source={workspace_str},target={workspace_str}")
        cmd.extend(["--mount", workspace_mount])
        
        # Add port forwards
        for port in config.get("forwardPorts", []):
            cmd.extend(["-p", f"{port}:{port}"])
        
        # Add environment variables
        for key, value in config.get("containerEnv", {}).items():
            cmd.extend(["-e", f"{key}={value}"])
        
        # Add the image
        cmd.append(image)

        # TODO: better way to handle this
        # Keep container alive without blocking stdin/stdout for LSP
        # Use tail -f /dev/null instead of sleep infinity to allow proper I/O
        cmd.extend([
            "tail",
            "-f",
            "/dev/null"
        ])        

        # Run in thread
        def run():
            try:
                log(f"Starting container with command: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    container_id = result.stdout.strip()
                    
                    # Store container metadata
                    cls._active_containers[container_id] = {
                        "name": name,
                        "config": config,
                        "config_path": config_path,
                        "workspace_mount": workspace_mount,
                        "workspace_folder": str(workspace)
                    }
                    
                    log(f"Container started: {container_id}")
                    
                    # Run post-create command
                    post_create = config.get("postCreateCommand")
                    if post_create:
                        cls._safe_exec(container_id, post_create)
                    
                    # Setup LSP in background after 2 seconds
                    def setup_lsp():
                        try:
                            import time
                            time.sleep(2)
                            from . import lsp_helper
                            container_name = config.get("name", "devcontainer")
                            lsp_helper.setup_lsp_for_devcontainer(
                                container_name, config, str(workspace), workspace_mount, runtime
                            )
                        except Exception as e:
                            log(f"Error in LSP setup thread: {e}", "error")
                            import traceback
                            log(traceback.format_exc(), "debug")
                    
                    lsp_thread = threading.Thread(target=setup_lsp, daemon=True)
                    lsp_thread.start()
                    
                    if callback:
                        sublime.set_timeout(lambda: callback(container_id), 0)
                    return container_id
                else:
                    log(f"Failed to start container: {result.stderr}", "error")
                    if callback:
                        sublime.set_timeout(lambda: callback(None), 0)
            except Exception as e:
                log(f"Exception starting container: {e}", "error")
                if callback:
                    sublime.set_timeout(lambda: callback(None), 0)
        
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        return None
    
    @classmethod
    def _build_from_dockerfile(cls, config: Dict, config_path: Path,
                              callback=None) -> Optional[str]:
        """Build container from Dockerfile"""
        runtime = ContainerRuntime.detect_runtime()
        
        build_config = config.get("build", {})
        if isinstance(build_config, str):
            dockerfile = build_config
        else:
            dockerfile = build_config.get("dockerfile", "Dockerfile")
            
        context = build_config.get("context", ".") if isinstance(build_config, dict) else "."
        
        dockerfile_path = config_path.parent / dockerfile
        context_path = config_path.parent / context
        
        image_name = f"devcontainer-{config.get('name', 'unnamed')}"
        
        def build():
            try:
                # Build image
                build_cmd = [runtime, "build", "-t", image_name, "-f", 
                           str(dockerfile_path), str(context_path)]
                
                log(f"Building image: {' '.join(build_cmd)}")
                result = subprocess.run(build_cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    log(f"Failed to build image: {result.stderr}", "error")
                    if callback:
                        sublime.set_timeout(lambda: callback(None), 0)
                    return
                
                log(f"Image built: {image_name}")
                
                # Now run the container
                config["image"] = image_name
                cls._run_from_image(config, config_path, callback)
                
            except Exception as e:
                log(f"Exception building image: {e}", "error")
                if callback:
                    sublime.set_timeout(lambda: callback(None), 0)
        
        thread = threading.Thread(target=build, daemon=True)
        thread.start()
        return None
    
    @classmethod
    def _build_compose(cls, config: Dict, config_path: Path,
                      callback=None) -> Optional[str]:
        """Build using docker-compose"""
        compose_cmd = ContainerRuntime.detect_compose()
        compose_files = config.get("dockerComposeFile", [])
        
        if isinstance(compose_files, str):
            compose_files = [compose_files]
        
        service = config.get("service")
        
        def build():
            try:
                cmd = [compose_cmd]
                for f in compose_files:
                    cmd.extend(["-f", str(config_path.parent / f)])
                cmd.extend(["up", "-d"])
                
                if service:
                    cmd.append(service)
                
                log(f"Running compose: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True,
                                      cwd=str(config_path.parent))
                
                if result.returncode == 0:
                    log("Compose container started")
                    if callback:
                        sublime.set_timeout(lambda: callback("compose"), 0)
                else:
                    log(f"Compose failed: {result.stderr}", "error")
                    if callback:
                        sublime.set_timeout(lambda: callback(None), 0)
            except Exception as e:
                log(f"Exception running compose: {e}", "error")
                if callback:
                    sublime.set_timeout(lambda: callback(None), 0)
        
        thread = threading.Thread(target=build, daemon=True)
        thread.start()
        return None
    
    @classmethod
    def _safe_exec(cls, container_id: str, command: str):
        runtime = ContainerRuntime.detect_runtime()
    
        # wait until container is actually running
        import time
        for _ in range(20):  # ~4 seconds max
            if cls.is_container_running(container_id, runtime):
                break
            time.sleep(0.2)
        else:
            log("Container never reached running state", "error")
            return
    
        cmd = [runtime, "exec", "-i", container_id, "sh", "-lc", command]
    
        try:
            subprocess.run(cmd)
        except Exception as e:
            log(f"Exec failed: {e}", "error")    

    @classmethod
    def stop_container(cls, container_id: str):
        """Stop a container"""
        runtime = ContainerRuntime.detect_runtime()
        try:
            subprocess.run([runtime, "stop", container_id])
            if container_id in cls._active_containers:
                del cls._active_containers[container_id]
            log(f"Stopped container: {container_id}")
        except Exception as e:
            log(f"Error stopping container: {e}", "error")
    
    @classmethod
    def stop_all_containers(cls):
        """Stop all active containers"""
        for container_id in list(cls._active_containers.keys()):
            cls.stop_container(container_id)
    
    @classmethod
    def get_container_ip(cls, container_id: str) -> Optional[str]:
        """Get container IP address"""
        runtime = ContainerRuntime.detect_runtime()
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
            log(f"Error getting container IP: {e}", "error")
        return None

    @classmethod
    def is_container_running(cls, container_id: str, runtime: str = "podman") -> bool:
        try:
            result = subprocess.run(
                [runtime, "inspect", "-f", "{{.State.Running}}", container_id],
                capture_output=True,
                text=True
            )
            return result.returncode == 0 and result.stdout.strip().lower() == "true"
        except Exception:
            return False

class LSPIntegration:
    """Handles LSP server integration in containers"""
    
    @staticmethod
    def setup_lsp_for_container(container_id: str, config: Dict):
        """Setup LSP servers in container"""
        # This would integrate with LSP package
        # For now, we'll prepare the environment
        
        customizations = config.get("customizations", {})
        sublime_config = customizations.get("sublimetext", {})
        
        # Extensions/plugins to install
        extensions = sublime_config.get("extensions", [])

        mapper = LSPWorkspaceMapper(workspace_mount)
        log(f"Workspace mount: {workspace_mount}")
        log(f"Mapper local root: {mapper.local_path}")
        log(f"Mapper container root: {mapper.container_path}")
        
        # LSP servers to configure
        # This would need to coordinate with the LSP package
        log(f"LSP setup for container {container_id} with extensions: {extensions}")
        
        return {
            "extensions": extensions,
            "settings": sublime_config.get("settings", {})
        }


# Commands

class DevcontainerStartCommand(sublime_plugin.WindowCommand):
    """Start devcontainer"""
    
    def run(self):
        window = self.window
        folders = window.folders()
        
        if not folders:
            sublime.error_message("No folder opened")
            return
        
        config_path = DevContainerConfig.find_config(folders[0])
        
        if not config_path:
            sublime.error_message("No devcontainer.json found")
            return
        
        config = DevContainerConfig.load_config(config_path)
        
        if not config:
            sublime.error_message("Invalid devcontainer.json")
            return
        
        def on_started(container_id):
            if container_id:
                sublime.status_message(f"Container started: {container_id}")
            else:
                sublime.error_message("Failed to start container")
        
        ContainerManager.build_container(config, config_path, on_started)
        sublime.status_message("Starting devcontainer...")


class DevcontainerStopCommand(sublime_plugin.WindowCommand):
    """Stop devcontainer"""
    
    def run(self):
        if ContainerManager._active_containers:
            ContainerManager.stop_all_containers()
            sublime.status_message("Containers stopped")
        else:
            sublime.status_message("No active containers")


class DevcontainerAttachCommand(sublime_plugin.WindowCommand):
    """Attach to running devcontainer"""
    
    def run(self):
        window = self.window
        folders = window.folders()
        
        if not folders:
            sublime.error_message("No folder opened")
            return
        
        config_path = DevContainerConfig.find_config(folders[0])
        
        if not config_path:
            sublime.error_message("No devcontainer.json found")
            return
        
        config = DevContainerConfig.load_config(config_path)
        
        if not config:
            sublime.error_message("Invalid devcontainer.json")
            return
        
        # Find or start container
        name = config.get("name", "devcontainer")
        runtime = ContainerRuntime.detect_runtime()
        
        try:
            # Check if container exists and is running
            result = subprocess.run(
                [runtime, "ps", "-f", f"name={name}", "--format", "{{.ID}}"],
                capture_output=True,
                text=True
            )
            
            container_id = result.stdout.strip()
            
            if not container_id:
                sublime.error_message("Container not running. Use 'Start' first.")
                return
            
            # Setup LSP
            LSPIntegration.setup_lsp_for_container(container_id, config)
            
            # Open terminal to container
            self._open_container_terminal(container_id)
            
            sublime.status_message(f"Attached to container: {container_id}")
            
        except Exception as e:
            log(f"Error attaching to container: {e}", "error")
            sublime.error_message(f"Failed to attach: {e}")
    
    def _open_container_terminal(self, container_id: str):
        """Open terminal connected to container"""
        runtime = ContainerRuntime.detect_runtime()
        
        # Create a terminal view
        view = self.window.new_file()
        view.set_scratch(True)
        view.set_name(f"DevContainer: {container_id[:12]}")
        
        # This is a simplified version - actual implementation would
        # use Sublime's terminal API or a terminal emulator
        view.run_command("insert", {
            "characters": f"# Connected to container {container_id}\n"
                        f"# Use: {runtime} exec -it {container_id} /bin/bash\n"
        })


class DevcontainerEditConfigCommand(sublime_plugin.WindowCommand):
    """Edit or create devcontainer.json"""
    
    def run(self):
        folders = self.window.folders()
        
        if not folders:
            sublime.error_message("No folder opened")
            return
        
        config_path = DevContainerConfig.find_config(folders[0])
        
        if config_path:
            # Open existing config
            self.window.open_file(str(config_path))
        else:
            # Create new config
            self._create_new_config(folders[0])
    
    def _create_new_config(self, workspace_folder: str):
        """Create a new devcontainer.json"""
        # Ask user where to create it
        items = [
            ".devcontainer/devcontainer.json",
            ".devcontainer.json"
        ]
        
        def on_done(index):
            if index < 0:
                return
            
            config_file = Path(workspace_folder) / items[index]
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Create default config
            default_config = DevContainerConfig.create_default_config(workspace_folder)
            
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            
            # Open the file
            self.window.open_file(str(config_file))
        
        self.window.show_quick_panel(items, on_done)


class DevcontainerExecCommand(sublime_plugin.WindowCommand):
    """Execute command in container"""
    
    def run(self):
        if not ContainerManager._active_containers:
            sublime.error_message("No active containers")
            return
        
        def on_done(command):
            if command:
                container_id = list(ContainerManager._active_containers.keys())[0]
                ContainerManager._safe_exec(container_id, command)
        
        self.window.show_input_panel(
            "Command to execute:",
            "",
            on_done,
            None,
            None
        )


class DevcontainerLogsCommand(sublime_plugin.WindowCommand):
    """View plugin logs"""
    
    def run(self):
        # This would show the console output
        self.window.run_command("show_panel", {"panel": "console"})
