#!/bin/bash
set -e
cd "$(dirname "$0")"

if command -v python3 &> /dev/null; then
    python3 install.py "$@"
elif command -v python &> /dev/null; then
    version=$(python --version 2>&1 | awk '{print $2}')
    major=$(echo "$version" | cut -d. -f1)
    if [ "$major" -ge 3 ]; then
        python install.py "$@"
    else
        echo "Error: Python 3 is required, found Python $version"
        exit 1
    fi
else
    echo "Error: Python not found"
    exit 1
fi
