#!/bin/bash
set -e
cd "$(dirname "$0")"

if command -v python3 &> /dev/null; then
    python3 release.py "$@"
elif command -v python &> /dev/null; then
    python release.py "$@"
else
    echo "Error: Python not found"
    exit 1
fi
