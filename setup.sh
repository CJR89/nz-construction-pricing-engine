#!/bin/bash

# NZ Construction Pricing Engine - Setup Script

echo "=== NZ Construction Pricing Engine Setup ==="
echo ""

# Check Python
echo "Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    exit 1
fi
python3 --version

# Check Node.js
echo "Checking Node.js..."
if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js is not installed"
    exit 1
fi
node --version

echo ""
echo "=== Installing Backend Dependencies ==="
cd backend
pip install -r requirements.txt
cd ..

echo ""
echo "=== Installing Frontend Dependencies ==="
cd frontend
npm install
cd ..

echo ""
echo "=== Setup Environment ==="
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file from .env.example"
else
    echo ".env file already exists"
fi

echo ""
echo "=== Creating uploads directory ==="
mkdir -p uploads

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "To start the application:"
echo ""
echo "Terminal 1 (Backend):"
echo "  cd backend"
echo "  python main.py"
echo ""
echo "Terminal 2 (Frontend):"
echo "  cd frontend"
echo "  npm run dev"
echo ""
echo "Then open http://localhost:5173 in your browser"
echo ""
