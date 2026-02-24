#!/bin/bash

# Ensure we exit if any command fails
set -e

echo "=========================================="
echo "    🚀 Starting IsoMind Platform...     "
echo "=========================================="

# 1. Cleanup old processes using our ports
echo "[1/3] 🧹 Cleaning up old processes on ports 3000, 8003..."
lsof -ti:3000,8003 | xargs kill -9 2>/dev/null || true

# 2. Start Orchestrator API
echo "[2/3] 🧠 Booting Central Orchestrator & SSH Tunnels (brain/api.py)..."
cd brain
# Ensure venv is active
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "❌ Error: Virtual environment not found in brain/venv"
    exit 1
fi
python3 api.py &
API_PID=$!
cd ..

# Wait a moment for API and SSH tunnels to establish
sleep 3

# 3. Start Next.js Dashboard
echo "[3/3] 🖥️ Booting Next.js UI (platform/)..."
cd platform
npm run dev &
NEXT_PID=$!
cd ..

echo ""
echo "=========================================="
echo " ✅ IsoMind is LIVE!"
echo " 🌐 Open http://localhost:3000"
echo "=========================================="
echo ""
echo "Press [Ctrl+C] to stop all services and close tunnels."

# Trap Ctrl+C to kill both children
trap "echo '🛑 Stopping IsoMind...'; kill -TERM $API_PID $NEXT_PID 2>/dev/null; exit 0" INT TERM
wait $API_PID $NEXT_PID
