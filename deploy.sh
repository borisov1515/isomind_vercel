#!/bin/bash

# ==============================================================================
# IsoMind Deploy Script (Local -> Vast.ai)
# 
# Usage: ./deploy.sh [VAST_SSH_PORT] [VAST_IP]
# Example: ./deploy.sh 12345 192.168.1.1
# ==============================================================================

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: ./deploy.sh <VAST_SSH_PORT> <VAST_IP>"
    exit 1
fi

PORT=$1
HOST=$2
USER="root" # Vast.ai usually uses root by default

echo "🚀 Deploying to Vast.ai instance: $USER@$HOST:$PORT"

# 1. Sync the codebase using rsync
# We exclude everything in .gitignore automatically via git integration 
# or specific rsync exclude rules to avoid sending heavy data.
echo "📦 Syncing files via rsync..."
rsync -avz --progress \
    --exclude-from='.gitignore' \
    --exclude='.git' \
    -e "ssh -i ~/.ssh/isomind_key -p $PORT -o StrictHostKeyChecking=no" \
    ./ $USER@$HOST:/root/isomind/

# 2. Rebuild and Restart Remote Docker Containers
echo "🔄 Reloading infrastructure on remote host..."
ssh -i ~/.ssh/isomind_key -p $PORT -o StrictHostKeyChecking=no $USER@$HOST << 'EOF'
    cd /root/isomind/infrastructure
    # Setup Sandbox Virtual Environment
    if [ ! -d "/opt/venv" ]; then
        echo "Создаем виртуальное окружение для Agent API..."
        python3 -m venv /opt/venv
    fi
    /opt/venv/bin/pip install -r /root/isomind/infrastructure/requirements.txt
    /opt/venv/bin/playwright install chromium --with-deps

    # Setup vLLM Virtual Environment (Phase 3)
    if [ ! -d "/opt/vllm_env" ]; then
        echo "Создаем изолированное окружение для vLLM..."
        python3 -m venv /opt/vllm_env
        /opt/vllm_env/bin/pip install vllm
    fi

    # Update supervisord and start all services
    echo "Перезапускаем supervisor..."
    cp /root/isomind/infrastructure/supervisord.conf /etc/supervisor/conf.d/isomind.conf
    service supervisor restart
    
    echo "✅ Deploy Complete! Active processes:"
    # Assuming supervisord manages services, docker ps might not be relevant anymore
    # but keeping it for now as it was in the original script's success message.
    # If docker is no longer used, this line should be removed or changed.
    docker ps
EOF

echo "🎉 All Done!"
