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
    -e "ssh -p $PORT -o StrictHostKeyChecking=no" \
    ./ $USER@$HOST:/root/isomind/

# 2. Rebuild and Restart Remote Docker Containers
echo "🔄 Reloading infrastructure on remote host..."
ssh -p $PORT -o StrictHostKeyChecking=no $USER@$HOST << 'EOF'
    cd /root/isomind/infrastructure
    echo "Stopping existing containers..."
    docker compose down
    
    echo "Building and starting new containers..."
    docker compose up -d --build
    
    echo "✅ Deploy Complete! Active containers:"
    docker ps
EOF

echo "🎉 All Done!"
