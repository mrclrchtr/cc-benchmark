# syntax=docker/dockerfile:1
# Multi-stage Dockerfile for CC-Benchmark
# Stage 1: Builder stage with all compilation tools
FROM buildpack-deps:jammy AS builder

# Install system dependencies more efficiently
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates-java \
    openjdk-21-jdk \
    && rm -rf /var/lib/apt/lists/*

# Install pyenv and Python in one layer
RUN curl -fsSL https://pyenv.run | bash && \
    export PATH="/root/.pyenv/bin:$PATH" && \
    export PYENV_ROOT="/root/.pyenv" && \
    eval "$(pyenv init -)" && \
    eval "$(pyenv virtualenv-init -)" && \
    pyenv install 3.12.7 && \
    pyenv global 3.12.7 && \
    /root/.pyenv/versions/3.12.7/bin/python -m pip install --upgrade pip setuptools wheel uv

# Set up pyenv environment
ENV PATH="/root/.pyenv/bin:$PATH"
ENV PYENV_ROOT="/root/.pyenv"
ENV PATH="/root/.pyenv/versions/3.12.7/bin:$PATH"

# Install Go with architecture detection
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then \
        GOARCH="amd64"; \
    elif [ "$ARCH" = "aarch64" ]; then \
        GOARCH="arm64"; \
    else \
        echo "Unsupported architecture: $ARCH" && exit 1; \
    fi && \
    curl -L "https://golang.org/dl/go1.21.5.linux-$GOARCH.tar.gz" | tar -C /usr/local -xz
ENV PATH="/usr/local/go/bin:${PATH}"

# Install Rust
RUN curl -fsSL https://sh.rustup.rs | sh -s -- -y --profile minimal --default-toolchain stable
ENV PATH="/root/.cargo/bin:${PATH}"

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    rm -rf /var/lib/apt/lists/*

# Install pnpm and Claude Code CLI globally
RUN npm install -g pnpm@latest @anthropic-ai/claude-code@latest

# Copy package file and install Node.js dependencies
WORKDIR /app
COPY package.json ./
RUN pnpm install

# Stage 2: Optimized runtime stage
FROM buildpack-deps:jammy

# Install runtime system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates-java \
    openjdk-21-jdk \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy pyenv and Python from builder
COPY --from=builder /root/.pyenv /root/.pyenv
ENV PATH="/root/.pyenv/bin:$PATH"
ENV PYENV_ROOT="/root/.pyenv"
ENV PATH="/root/.pyenv/versions/3.12.7/bin:$PATH"

# Copy Go installation
COPY --from=builder /usr/local/go /usr/local/go
ENV PATH="/usr/local/go/bin:${PATH}"

# Copy Rust installation
COPY --from=builder /root/.cargo /root/.cargo
COPY --from=builder /root/.rustup /root/.rustup
ENV PATH="/root/.cargo/bin:${PATH}"

# Copy Node.js and pnpm
COPY --from=builder /usr/bin/node /usr/bin/node
COPY --from=builder /usr/bin/npm /usr/bin/npm
COPY --from=builder /usr/bin/npx /usr/bin/npx
COPY --from=builder /usr/lib/node_modules /usr/lib/node_modules

# Copy installed Node.js dependencies from builder
COPY --from=builder /app/node_modules /pnpm-install/node_modules

# Create proper symlinks for pnpm binaries
RUN ln -s /usr/lib/node_modules/pnpm/bin/pnpm.cjs /usr/local/bin/pnpm && \
    ln -s /usr/lib/node_modules/pnpm/bin/pnpx.cjs /usr/local/bin/pnpx && \
    ln -s /usr/lib/node_modules/@anthropic-ai/claude-code/cli.js /usr/local/bin/claude && \
    chmod +x /usr/local/bin/claude

# Set up working directory
WORKDIR /cc-benchmark

# Copy Python dependency files first for better caching
COPY pyproject.toml uv.lock ./

# Install Python project dependencies (cached layer)
RUN eval "$(pyenv init -)" && \
    uv pip install --system --no-cache-dir -e . && \
    uv pip install --system --no-cache-dir claude-code-sdk

# Copy project files
COPY . /cc-benchmark

# Compile Python files
RUN eval "$(pyenv init -)" && \
    python -m compileall /cc-benchmark

# Set Claude Code environment variables
ENV CLAUDE_CODE_NO_TELEMETRY=1
ENV CLAUDE_CODE_HEADLESS=1

# Configure git and setup entrypoint
RUN git config --global --add safe.directory /cc-benchmark
COPY docker/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]