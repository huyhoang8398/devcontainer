# DevContainer for Sublime Text 4

A Sublime Text 4 plugin that brings VS Code's devcontainer functionality to Sublime Text, with full LSP (Language Server Protocol) support for intelligent code editing inside containers.

## Features

- 📦 **Full devcontainer.json Support** - Compatible with VS Code's devcontainer specification
- 🐳 **Docker & Podman Support** - Works with both Docker and Podman container runtimes
- 🔌 **LSP Integration** - Automatic LSP server configuration and management in containers
- 🚀 **Quick Start** - Start, stop, and attach to containers with simple commands
- 🔄 **Auto-configuration** - Automatically detects and configures development environments
- 📝 **Template Support** - Create new devcontainer.json files with templates
- 🔧 **Docker Compose Support** - Works with multi-container setups

## Requirements

- Sublime Text 4 (build 4000+)
- Docker or Podman installed and running
- LSP package (for language server support)

## Installation

### Via Package Control (Recommended)

1. Open Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`)
2. Select `Package Control: Install Package`
3. Search for `DevContainer`
4. Press Enter to install

### Manual Installation

1. Clone this repository to your Sublime Text Packages directory:
   ```bash
   cd ~/.config/sublime-text/Packages
   git clone https://github.com/yourusername/sublime-devcontainer DevContainer
   ```

2. Restart Sublime Text

## Quick Start

### 1. Open a Project with devcontainer.json

If your project already has a `.devcontainer/devcontainer.json` or `.devcontainer.json` file:

1. Open the project folder in Sublime Text
2. Open Command Palette
3. Run `DevContainer: Start`
4. Wait for the container to build and start
5. Run `DevContainer: Attach` to connect to the container

### 2. Create a New devcontainer.json

For projects without devcontainer configuration:

1. Open Command Palette
2. Run `DevContainer: Edit Config`
3. Select where to create the file (`.devcontainer/devcontainer.json` or `.devcontainer.json`)
4. Edit the generated configuration
5. Run `DevContainer: Start`

## Configuration

### Plugin Settings

Access settings via `Preferences > Package Settings > DevContainer > Settings`

```json
{
  // Container runtime: "docker", "podman", or null for auto-detect
  "container_runtime": null,
  
  // Compose command: "docker-compose", "podman-compose", or null
  "compose_command": null,
  
  // Auto-start containers when opening projects
  "auto_start": false,
  
  // Clean up containers on exit
  "clean_on_exit": false,
  
  // LSP integration
  "lsp": {
    "auto_configure": true,
    "default_servers": {
      "python": ["pyright", "ruff"],
      "javascript": ["typescript-language-server"],
      "rust": ["rust-analyzer"]
    }
  }
}
```

### Example devcontainer.json

**Simple Python Development:**
```json
{
  "name": "Python Dev Container",
  "image": "mcr.microsoft.com/devcontainers/python:3.11",
  "customizations": {
    "sublimetext": {
      "extensions": ["LSP-pyright", "LSP-ruff"],
      "settings": {}
    }
  },
  "forwardPorts": [8000],
  "postCreateCommand": "pip install -r requirements.txt"
}
```

**Node.js with Docker Compose:**
```json
{
  "name": "Node.js App",
  "dockerComposeFile": "docker-compose.yml",
  "service": "app",
  "workspaceFolder": "/workspace",
  "customizations": {
    "sublimetext": {
      "extensions": ["LSP-typescript"]
    }
  },
  "forwardPorts": [3000],
  "postCreateCommand": "npm install"
}
```

**Custom Dockerfile:**
```json
{
  "name": "Custom Dev Environment",
  "build": {
    "dockerfile": "Dockerfile",
    "context": ".",
    "args": {
      "NODE_VERSION": "18"
    }
  },
  "customizations": {
    "sublimetext": {
      "extensions": []
    }
  },
  "forwardPorts": [8080],
  "remoteUser": "developer"
}
```

## Available Commands

Access via Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`):

- **DevContainer: Start** - Start the development container
- **DevContainer: Stop** - Stop the running container
- **DevContainer: Attach** - Attach to a running container with LSP support
- **DevContainer: Edit Config** - Create or edit devcontainer.json
- **DevContainer: Exec** - Execute a command in the container
- **DevContainer: Logs** - View plugin logs
- **DevContainer: Stop All** - Stop all containers started by this plugin
- **DevContainer: Remove All** - Remove all containers and cleanup

## LSP Integration

### Automatic LSP Configuration

The plugin automatically:

1. Installs LSP servers in containers based on detected languages
2. Configures the LSP package to communicate with containerized servers
3. Maps file paths between your local workspace and container

### Supported Language Servers

- **Python**: pyright, pylsp, ruff-lsp
- **JavaScript/TypeScript**: typescript-language-server
- **Rust**: rust-analyzer
- **Go**: gopls
- **C/C++**: clangd
- **Ruby**: solargraph
- **Java**: jdtls

### Custom LSP Configuration

In devcontainer.json:

```json
{
  "customizations": {
    "sublimetext": {
      "extensions": ["LSP-pyright", "LSP-ruff"],
      "settings": {
        "LSP": {
          "pyright": {
            "settings": {
              "python.analysis.typeCheckingMode": "strict"
            }
          }
        }
      }
    }
  }
}
```

## Advanced Features

### Port Forwarding

Automatically forward ports from container to host:

```json
{
  "forwardPorts": [3000, 8080],
  "portsAttributes": {
    "3000": {
      "label": "Frontend"
    },
    "8080": {
      "label": "Backend API"
    }
  }
}
```

### Environment Variables

Set environment variables in the container:

```json
{
  "containerEnv": {
    "DATABASE_URL": "postgresql://localhost/devdb",
    "DEBUG": "true"
  },
  "remoteEnv": {
    "PATH": "${containerEnv:PATH}:/custom/bin"
  }
}
```

### Features

Install additional tools using devcontainer features:

```json
{
  "features": {
    "ghcr.io/devcontainers/features/git:1": {
      "version": "latest"
    },
    "ghcr.io/devcontainers/features/node:1": {
      "version": "18"
    }
  }
}
```

### Lifecycle Scripts

Run commands at different stages:

```json
{
  "postCreateCommand": "npm install && npm run build",
  "postStartCommand": "npm run dev",
  "postAttachCommand": "git status"
}
```

## Comparison with nvim-dev-container

This plugin is inspired by [nvim-dev-container](https://github.com/esensar/nvim-dev-container) but adapted for Sublime Text:

| Feature | nvim-dev-container | sublime-devcontainer |
|---------|-------------------|---------------------|
| Container Support | ✅ Docker/Podman | ✅ Docker/Podman |
| devcontainer.json | ✅ Full support | ✅ Full support |
| LSP Integration | ✅ Native nvim LSP | ✅ Via LSP package |
| Auto-start | ✅ | ✅ |
| Compose Support | ✅ | ✅ |
| Features Support | ⚠️ Partial | ⚠️ Partial |
| UI Integration | Neovim terminal | Sublime terminal |

## Troubleshooting

### Container Won't Start

1. Check Docker/Podman is running: `docker ps` or `podman ps`
2. View plugin logs: Run `DevContainer: Logs`
3. Verify devcontainer.json syntax
4. Check container runtime in settings

### LSP Not Working

1. Ensure LSP package is installed
2. Check container is running: `DevContainer: Attach`
3. Verify LSP servers are installed in container
4. Check LSP logs: `Tools > LSP > Troubleshoot Server`

### Path Mapping Issues

The plugin automatically maps paths between local workspace and container. If you encounter issues:

1. Check `workspaceMount` in devcontainer.json
2. Verify `workspaceFolder` is correct
3. Ensure workspace folder is mounted correctly

## Development

### Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Project Structure

```
sublime-devcontainer/
├── devcontainer.py          # Main plugin code
├── lsp_helper.py            # LSP integration
├── DevContainer.sublime-settings  # Default settings
├── package-metadata.json    # Package Control metadata
└── README.md               # This file
```

### Testing

Test the plugin with various devcontainer configurations:

```bash
# Python project
cd test-projects/python
subl .

# Node.js project
cd test-projects/nodejs
subl .

# Multi-container project
cd test-projects/fullstack
subl .
```

## Resources

- [Dev Container Specification](https://containers.dev/)
- [VS Code DevContainers Documentation](https://code.visualstudio.com/docs/devcontainers/containers)
- [Sublime LSP Package](https://github.com/sublimelsp/LSP)
- [nvim-dev-container](https://github.com/esensar/nvim-dev-container) - Inspiration for this plugin

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Inspired by [nvim-dev-container](https://github.com/esensar/nvim-dev-container)
- Built on the [Dev Container Specification](https://containers.dev/)
- Uses [Sublime LSP](https://github.com/sublimelsp/LSP) for language server support

## Support

- 📝 [Report Issues](https://github.com/yourusername/sublime-devcontainer/issues)
- 💬 [Discussions](https://github.com/yourusername/sublime-devcontainer/discussions)
- 📧 Email: your.email@example.com
