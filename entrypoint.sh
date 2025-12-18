#!/bin/bash
set -e

# Export environment variables
export PROXMOX_MCP_CONFIG="/app/proxmox-config/config.json"
export PATH="/app/.venv/bin:$PATH"

# Set default API key if not provided
API_KEY=${MCPO_API_KEY:-"please-change-this-secret-key"}

# Activate virtual environment
source /app/.venv/bin/activate

# Start mcpo proxy with API key authentication
exec mcpo --host 0.0.0.0 --port 8811 --api-key "$API_KEY" -- python -m proxmox_mcp.server
