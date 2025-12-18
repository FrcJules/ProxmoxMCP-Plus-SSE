"""
MCP SSE server implementation for n8n integration.

This module implements the standard MCP protocol with SSE transport,
compatible with n8n's MCP client.
"""
import os
import sys
import uvicorn
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Optional

from proxmox_mcp.config.loader import load_config
from proxmox_mcp.core.logging import setup_logging
from proxmox_mcp.server import ProxmoxMCPServer

# Global API key from environment
API_KEY = None

async def verify_api_key(authorization: Optional[str] = Header(None)):
    """Verify API key from Authorization header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    # Extract token from "Bearer <token>"
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization header format. Use: Bearer <token>")
    
    token = authorization[7:]  # Remove "Bearer " prefix
    
    if token != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    return token

def main():
    """Start the MCP server in SSE mode with authentication for n8n."""
    global API_KEY
    
    config_path = os.getenv("PROXMOX_MCP_CONFIG")
    if not config_path:
        print("PROXMOX_MCP_CONFIG environment variable must be set")
        sys.exit(1)
    
    # Get API key from environment
    API_KEY = os.getenv("MCPO_API_KEY")
    if not API_KEY:
        print("MCPO_API_KEY environment variable must be set")
        sys.exit(1)
    
    # Get host and port from environment
    host = os.getenv("SSE_HOST", "0.0.0.0")
    port = int(os.getenv("SSE_PORT", "3333"))
    
    try:
        # Create server instance
        server = ProxmoxMCPServer(config_path)
        
        server.logger.info(f"Starting Proxmox MCP SSE Server for n8n on {host}:{port}")
        server.logger.info(f"SSE Endpoint: http://{host}:{port}/mcp")
        server.logger.info(f"Authentication: Enabled (API Key required)")
        
        # Create FastAPI app
        app = FastAPI(
            title="Proxmox MCP SSE Server (n8n)",
            description="Proxmox MCP Server with SSE transport for n8n",
            version="1.0.0",
            docs_url=None,
            redoc_url=None,
            openapi_url=None
        )
        
        # Health check endpoint (no auth required)
        @app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "transport": "sse",
                "endpoint": "/mcp",
                "authentication": "enabled",
                "compatible_with": "n8n MCP client"
            }
        
        # Get the SSE app from FastMCP BEFORE creating middleware
        sse_app = server.mcp.sse_app()
        server.logger.info("SSE app created successfully")
        
        # Create a middleware to check authentication for /mcp
        @app.middleware("http")
        async def auth_middleware(request: Request, call_next):
            # Only check auth for /mcp paths
            if request.url.path.startswith("/mcp"):
                try:
                    await verify_api_key(request.headers.get("authorization"))
                except HTTPException as e:
                    return JSONResponse(
                        status_code=e.status_code,
                        content={"detail": e.detail}
                    )
            
            response = await call_next(request)
            return response
        
        # Mount the SSE app at /mcp BEFORE starting uvicorn
        app.mount("/mcp", sse_app)
        server.logger.info("SSE app mounted at /mcp")
        
        server.logger.info("SSE Server ready for n8n with authentication")
        server.logger.info("Configure n8n with URL: http://192.168.1.127:3333/mcp")
        
        # Run with uvicorn
        uvicorn.run(app, host=host, port=port, log_level="info")
        
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
