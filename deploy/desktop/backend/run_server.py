#!/usr/bin/env python
"""Run script for uvicorn with correct module paths."""

import sys
import os

# Ensure the backend directory is in the path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# Change to backend directory
os.chdir(backend_dir)

import uvicorn

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001)