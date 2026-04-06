#!/usr/bin/env bash
# build.sh — Render build script
# Compiles C and C++ shared libraries, installs Python deps, seeds DB

set -e

echo "=== Building C Security Module ==="
cd c_security
make clean || true
make
cd ..

echo "=== Building C++ Wallet Engine ==="
cd cpp_wallet_engine
make clean || true
make
cd ..

echo "=== Installing Python dependencies ==="
cd backend_python
pip install -r requirements.txt

echo "=== Seeding database ==="
python seed_data.py
cd ..

echo "✅ Build complete!"
