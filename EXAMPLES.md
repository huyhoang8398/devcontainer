# Example DevContainer Configurations

This directory contains example devcontainer.json configurations for various development scenarios.

## Python Development

### Basic Python with pyright

```json
{
  "name": "Python 3.11",
  "image": "mcr.microsoft.com/devcontainers/python:3.11",
  "customizations": {
    "sublimetext": {
      "extensions": ["LSP-pyright"],
      "settings": {
        "LSP": {
          "pyright": {
            "settings": {
              "python.analysis.typeCheckingMode": "basic"
            }
          }
        }
      }
    }
  },
  "forwardPorts": [8000],
  "postCreateCommand": "pip install --user -r requirements.txt",
  "remoteUser": "vscode"
}
```

### Python with Multiple LSP Servers

```json
{
  "name": "Python Development",
  "image": "python:3.11-slim",
  "features": {
    "ghcr.io/devcontainers/features/git:1": {}
  },
  "customizations": {
    "sublimetext": {
      "extensions": ["LSP-pyright", "LSP-ruff", "LSP-pylsp"]
    }
  },
  "postCreateCommand": "pip install --user pyright ruff-lsp python-lsp-server[all]",
  "containerEnv": {
    "PYTHONPATH": "/workspace"
  }
}
```

## JavaScript/TypeScript

### Node.js Development

```json
{
  "name": "Node.js 18",
  "image": "mcr.microsoft.com/devcontainers/javascript-node:18",
  "customizations": {
    "sublimetext": {
      "extensions": ["LSP-typescript"],
      "settings": {}
    }
  },
  "forwardPorts": [3000, 3001],
  "postCreateCommand": "npm install",
  "portsAttributes": {
    "3000": {
      "label": "Application"
    },
    "3001": {
      "label": "Dev Server"
    }
  }
}
```

### React Development with Hot Reload

```json
{
  "name": "React App",
  "image": "node:18",
  "features": {
    "ghcr.io/devcontainers/features/git:1": {}
  },
  "customizations": {
    "sublimetext": {
      "extensions": ["LSP-typescript", "LSP-eslint"]
    }
  },
  "forwardPorts": [3000],
  "postCreateCommand": "npm install",
  "runArgs": [
    "--init"
  ]
}
```

## Rust Development

```json
{
  "name": "Rust",
  "image": "rust:latest",
  "customizations": {
    "sublimetext": {
      "extensions": ["LSP-rust-analyzer"],
      "settings": {
        "LSP": {
          "rust-analyzer": {
            "settings": {
              "rust-analyzer.checkOnSave.command": "clippy"
            }
          }
        }
      }
    }
  },
  "postCreateCommand": "rustup component add rust-analyzer clippy"
}
```

## Go Development

```json
{
  "name": "Go 1.21",
  "image": "golang:1.21",
  "customizations": {
    "sublimetext": {
      "extensions": ["LSP-gopls"]
    }
  },
  "postCreateCommand": "go install golang.org/x/tools/gopls@latest",
  "containerEnv": {
    "GOPATH": "/go",
    "PATH": "${containerEnv:PATH}:/go/bin"
  }
}
```

## Java Development

```json
{
  "name": "Java 17",
  "image": "mcr.microsoft.com/devcontainers/java:17",
  "features": {
    "ghcr.io/devcontainers/features/java:1": {
      "version": "17",
      "installMaven": "true",
      "installGradle": "true"
    }
  },
  "customizations": {
    "sublimetext": {
      "extensions": ["LSP-jdtls"]
    }
  },
  "postCreateCommand": "mvn clean install"
}
```

## Docker Compose Examples

### Full Stack Application

**devcontainer.json:**
```json
{
  "name": "Full Stack App",
  "dockerComposeFile": ["docker-compose.yml", "docker-compose.dev.yml"],
  "service": "app",
  "workspaceFolder": "/workspace",
  "customizations": {
    "sublimetext": {
      "extensions": ["LSP-typescript", "LSP-pyright"]
    }
  },
  "forwardPorts": [3000, 5000, 5432],
  "postCreateCommand": "npm install && pip install -r requirements.txt"
}
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    volumes:
      - .:/workspace:cached
    command: sleep infinity
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: dev
      POSTGRES_DB: appdb

  redis:
    image: redis:7-alpine
```

### Microservices Development

```json
{
  "name": "Microservices",
  "dockerComposeFile": "docker-compose.yml",
  "service": "api",
  "workspaceFolder": "/workspace",
  "customizations": {
    "sublimetext": {
      "extensions": ["LSP-typescript"]
    }
  },
  "forwardPorts": [3000, 3001, 3002],
  "shutdownAction": "stopCompose"
}
```

## Custom Dockerfile Examples

### Python with Custom Dependencies

**devcontainer.json:**
```json
{
  "name": "Custom Python",
  "build": {
    "dockerfile": "Dockerfile",
    "context": "..",
    "args": {
      "PYTHON_VERSION": "3.11"
    }
  },
  "customizations": {
    "sublimetext": {
      "extensions": ["LSP-pyright", "LSP-ruff"]
    }
  },
  "remoteUser": "developer",
  "workspaceFolder": "/workspace",
  "mounts": [
    "source=${localWorkspaceFolder}/.vscode,target=/home/developer/.config/sublime-text,type=bind"
  ]
}
```

**Dockerfile:**
```dockerfile
ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim

RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash developer
USER developer
WORKDIR /workspace

RUN pip install --user pyright ruff-lsp python-lsp-server[all]
```

### Multi-Language Development

```json
{
  "name": "Multi-Language Dev",
  "build": {
    "dockerfile": "Dockerfile"
  },
  "features": {
    "ghcr.io/devcontainers/features/python:1": {
      "version": "3.11"
    },
    "ghcr.io/devcontainers/features/node:1": {
      "version": "18"
    },
    "ghcr.io/devcontainers/features/rust:1": {}
  },
  "customizations": {
    "sublimetext": {
      "extensions": [
        "LSP-pyright",
        "LSP-typescript",
        "LSP-rust-analyzer"
      ]
    }
  }
}
```

## Advanced Features

### GPU Support (NVIDIA)

```json
{
  "name": "ML Development",
  "image": "tensorflow/tensorflow:latest-gpu",
  "runArgs": [
    "--gpus=all"
  ],
  "customizations": {
    "sublimetext": {
      "extensions": ["LSP-pyright"]
    }
  },
  "postCreateCommand": "pip install --user pyright jupyter"
}
```

### SSH Access to Container

```json
{
  "name": "Dev Container with SSH",
  "image": "ubuntu:22.04",
  "features": {
    "ghcr.io/devcontainers/features/sshd:1": {
      "version": "latest"
    }
  },
  "forwardPorts": [22],
  "portsAttributes": {
    "22": {
      "label": "SSH"
    }
  }
}
```

### Database Development

```json
{
  "name": "Database Dev",
  "dockerComposeFile": "docker-compose.yml",
  "service": "dev",
  "workspaceFolder": "/workspace",
  "customizations": {
    "sublimetext": {
      "extensions": ["LSP-sql"]
    }
  },
  "features": {
    "ghcr.io/devcontainers/features/postgresql-client:1": {}
  }
}
```

## Testing Configurations

### Integration Test Environment

```json
{
  "name": "Test Environment",
  "dockerComposeFile": "docker-compose.test.yml",
  "service": "test",
  "customizations": {
    "sublimetext": {
      "extensions": ["LSP-pyright"]
    }
  },
  "postCreateCommand": "pip install --user -r requirements-test.txt",
  "overrideCommand": false,
  "shutdownAction": "stopCompose"
}
```

## Best Practices

### Minimal Base Image

```json
{
  "name": "Minimal Dev",
  "image": "alpine:latest",
  "features": {
    "ghcr.io/devcontainers/features/common-utils:1": {
      "installZsh": true,
      "installOhMyZsh": true
    }
  },
  "customizations": {
    "sublimetext": {
      "extensions": []
    }
  }
}
```

### Optimized Build with Cache

```json
{
  "name": "Cached Build",
  "build": {
    "dockerfile": "Dockerfile",
    "context": "..",
    "cacheFrom": [
      "myregistry/myimage:latest"
    ]
  },
  "customizations": {
    "sublimetext": {
      "extensions": ["LSP-typescript"]
    }
  }
}
```

## Platform-Specific Configurations

### macOS Optimization

```json
{
  "name": "macOS Optimized",
  "image": "node:18",
  "mounts": [
    "source=${localWorkspaceFolder}/node_modules,target=/workspace/node_modules,type=volume"
  ],
  "customizations": {
    "sublimetext": {
      "extensions": ["LSP-typescript"]
    }
  }
}
```

### Windows WSL2 Optimization

```json
{
  "name": "WSL2 Optimized",
  "image": "ubuntu:22.04",
  "workspaceMount": "source=${localWorkspaceFolder},target=/workspace,type=bind,consistency=cached",
  "workspaceFolder": "/workspace",
  "customizations": {
    "sublimetext": {
      "extensions": []
    }
  }
}
```
