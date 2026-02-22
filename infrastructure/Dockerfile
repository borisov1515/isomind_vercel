FROM nvidia/cuda:12.1.1-base-ubuntu22.04

# Avoid tzdata interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Install core GUI, display server, and Python utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb \
    x11vnc \
    openbox \
    supervisor \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    gnupg \
    wget \
    scrot \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (required for Playwright)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Add non-root agent user
RUN useradd -m -s /bin/bash agent

# Setup Python environment for backend API
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (Chromium and its OS dependencies)
RUN npx playwright install --with-deps chromium

# Copy configuration and code
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY agent_api /app/agent_api

# Change ownership to agent user
RUN chown -R agent:agent /app

# Switch to agent user for executing the supervisor
USER agent

# X11 virtual display variables
ENV DISPLAY=:99
ENV RESOLUTION=1920x1080x24

EXPOSE 8000 5900 8080

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
