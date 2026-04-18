FROM python:3.12-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive

# ============================================================================
# Base utilities required by VS Code remote extension and CLI tools
# ============================================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    git \
    ca-certificates \
    sudo \
    gnupg \
    lsb-release \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# ============================================================================
# Create non-root vscode user (required by VS Code devcontainer)
# ============================================================================
RUN groupadd --gid 1000 vscode \
    && useradd --uid 1000 --gid 1000 --shell /bin/bash --create-home vscode \
    && echo "vscode ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/vscode \
    && chmod 0440 /etc/sudoers.d/vscode

# ============================================================================
# Azure CLI
# ============================================================================
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash \
    && rm -rf /var/lib/apt/lists/*

# ============================================================================
# GitHub CLI
# ============================================================================
RUN mkdir -p -m 755 /etc/apt/keyrings \
    && wget -qO /etc/apt/keyrings/githubcli-archive-keyring.gpg \
       https://cli.github.com/packages/githubcli-archive-keyring.gpg \
    && chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
       > /etc/apt/sources.list.d/github-cli.list \
    && apt-get update && apt-get install -y gh \
    && rm -rf /var/lib/apt/lists/*

# ============================================================================
# Azure Developer CLI (azd)
# ============================================================================
RUN curl -fsSL https://aka.ms/install-azd.sh | bash

# ============================================================================
# Python dependencies
# ============================================================================
COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

# ============================================================================
# Azure CLI config + fix rpds-py for az's bundled Python 3.13
# (host ~/.azure/cliextensions may reference rpds; ensure it's available)
# ============================================================================
RUN az config set extension.use_dynamic_install=no 2>/dev/null || true \
    && /opt/az/bin/python3 -m pip install --no-cache-dir rpds-py

# ============================================================================
# Pre-register Jupyter kernel so VS Code never prompts for kernel source
# ============================================================================
RUN python -m ipykernel install --name python3 --display-name "Python 3"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    AZURE_EXTENSION_USE_DYNAMIC_INSTALL=no

# ============================================================================
# Azure login on first terminal open after VS Code is fully attached.
# postAttachCommand touches /tmp/.vscode-attached; the lock prevents
# a second terminal from firing a duplicate login.
# ============================================================================
RUN printf '\nif [ -t 0 ] && [ -f /tmp/.vscode-attached ] && ! az account show > /dev/null 2>&1; then\n  if mkdir /tmp/.az-login-lock 2>/dev/null; then\n    echo ""\n    echo "🔐 Setting up for Azure..."\n    echo ""\n    az login\n    rmdir /tmp/.az-login-lock 2>/dev/null\n  fi\nfi\n' >> /home/vscode/.bashrc
