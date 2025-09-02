# Debian Package Manager Docker Environment
FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PATH="/root/.local/bin:$PATH"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-apt \
    apt-utils \
    dpkg-dev \
    debhelper \
    build-essential \
    curl \
    wget \
    git \
    openssh-client \
    openssh-server \
    sudo \
    vim \
    nano \
    htop \
    tree \
    jq \
    iputils-ping \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# Create workspace directory
WORKDIR /workspace

# Copy Docker setup files
COPY scripts/ /docker-setup/scripts/
COPY config/ /docker-setup/config/
COPY packages/ /docker-setup/packages/
COPY bashrc-additions /docker-setup/bashrc-additions

# Make scripts executable
RUN chmod +x /docker-setup/scripts/*.sh

# Build example packages first
RUN /docker-setup/scripts/build-examples.sh

# Copy source code (this will be overridden by volume mount in docker-compose)
COPY .. /workspace/

# Run setup script
RUN /docker-setup/scripts/setup-dpm.sh

# Create helpful aliases and environment
RUN cat /docker-setup/bashrc-additions >> /root/.bashrc

# Set up working directory
WORKDIR /workspace

# Default command
CMD ["/bin/bash"]