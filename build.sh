#!/bin/bash
# AEGIS Build Script — builds frontend and prepares for deployment
set -e

echo "🛡️  AEGIS Build"
echo "═══════════════════════"

# Install Python deps
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Build frontend
echo "🔨 Building frontend..."
cd frontend
npm install
npm run build
cd ..

echo ""
echo "✅ Build complete!"
echo "   Frontend: frontend/dist/"
echo "   Start:    python -m aegis.server"
