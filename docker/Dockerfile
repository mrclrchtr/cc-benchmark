FROM buildpack-deps:jammy

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ca-certificates-java \
    openjdk-21-jdk \
    && rm -rf /var/lib/apt/lists/*

# Install pyenv
RUN curl -fsSL https://pyenv.run | bash

# Add pyenv to PATH and set up Python environment
ENV PATH="/root/.pyenv/bin:$PATH"
ENV PYENV_ROOT="/root/.pyenv"
ENV PATH="/root/.pyenv/versions/3.12.7/bin:$PATH"

# Initialize pyenv and install Python 3.12
RUN eval "$(pyenv init -)" && \
    eval "$(pyenv virtualenv-init -)" && \
    pyenv install 3.12.7 && \
    pyenv global 3.12.7 && \
    python -m pip install --upgrade pip setuptools uv
# Install Go with architecture detection
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then \
        GOARCH="amd64"; \
    elif [ "$ARCH" = "aarch64" ]; then \
        GOARCH="arm64"; \
    else \
        false; \
    fi && \
    curl -L "https://golang.org/dl/go1.21.5.linux-$GOARCH.tar.gz" -o go.tar.gz && \
    tar -C /usr/local -xzf go.tar.gz && \
    rm go.tar.gz
ENV PATH="/usr/local/go/bin:${PATH}"

# Install Rust
ADD https://sh.rustup.rs /tmp/rustup.sh
RUN chmod +x /tmp/rustup.sh && /tmp/rustup.sh -y && rm /tmp/rustup.sh
ENV PATH="/root/.cargo/bin:${PATH}"

# Install Node.js and dependencies
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/* && \
    mkdir -p /npm-install && \
    cd /npm-install && \
    npm init -y && \
    npm install \
    jest \
    @babel/core@7.25.2 \
    @exercism/babel-preset-javascript@0.2.1 \
    @exercism/eslint-config-javascript@0.6.0 \
    @types/jest@29.5.12 \
    @types/node@20.12.12 \
    babel-jest@29.6.4 \
    core-js@3.37.1 \
    eslint@8.49.0

# Install Claude Code CLI
RUN npm install -g @anthropic-ai/claude-code@latest
COPY . /cc-benchmark
RUN eval "$(pyenv init -)" && \
    uv pip install --system --no-cache-dir -e /cc-benchmark && \
    uv pip install --system --no-cache-dir claude-code-sdk

# Set Claude Code environment variables
ENV CLAUDE_CODE_NO_TELEMETRY=1
ENV CLAUDE_CODE_HEADLESS=1

# Copy and set up entrypoint script
COPY docker/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

RUN git config --global --add safe.directory /cc-benchmark
WORKDIR /cc-benchmark

ENTRYPOINT ["/docker-entrypoint.sh"]
