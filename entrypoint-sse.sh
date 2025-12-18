#!/bin/bash
set -e

# Export environment variables
export PROXMOX_MCP_CONFIG="/app/proxmox-config/config.json"
export PATH="/app/.venv/bin:$PATH"

# Activate virtual environment
source /app/.venv/bin/activate

# Start MCP server in SSE mode
exec python -m proxmox_mcp.server_sse
