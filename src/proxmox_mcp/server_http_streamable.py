"""
HTTP Streamable server implementation for Proxmox MCP (MCP-compliant).

This module implements an MCP server with HTTP Streamable transport (not SSE).
Conforms to MCP specification with list_tools and call_tool endpoints.
"""
import logging
import os
import sys
from typing import Optional, Annotated, Literal
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import Field, BaseModel
import json

from proxmox_mcp.config.loader import load_config
from proxmox_mcp.core.logging import setup_logging
from proxmox_mcp.core.proxmox import ProxmoxManager
from proxmox_mcp.tools.node import NodeTools
from proxmox_mcp.tools.vm import VMTools
from proxmox_mcp.tools.storage import StorageTools
from proxmox_mcp.tools.cluster import ClusterTools
from proxmox_mcp.tools.containers import ContainerTools

# Global instances
proxmox_manager = None
logger = None
API_KEY = None

# Tools instances
node_tools = None
vm_tools = None
storage_tools = None
cluster_tools = None
container_tools = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global proxmox_manager, logger, node_tools, vm_tools, storage_tools, cluster_tools, container_tools, API_KEY
    
    # Startup
    config_path = os.getenv("PROXMOX_MCP_CONFIG")
    if not config_path:
        raise RuntimeError("PROXMOX_MCP_CONFIG environment variable must be set")
    
    API_KEY = os.getenv("MCPO_API_KEY")
    if not API_KEY:
        raise RuntimeError("MCPO_API_KEY environment variable must be set")
    
    config = load_config(config_path)
    logger = setup_logging(config.logging)
    
    proxmox_manager = ProxmoxManager(config.proxmox, config.auth)
    proxmox = proxmox_manager.get_api()
    
    # Initialize tools
    node_tools = NodeTools(proxmox)
    vm_tools = VMTools(proxmox)
    storage_tools = StorageTools(proxmox)
    cluster_tools = ClusterTools(proxmox)
    container_tools = ContainerTools(proxmox)
    
    logger.info("Proxmox MCP HTTP Streamable Server started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Proxmox MCP HTTP Streamable Server")


app = FastAPI(
    title="Proxmox MCP HTTP Streamable Server",
    description="MCP-compliant server for Proxmox with HTTP Streamable transport",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)


async def verify_api_key(authorization: Optional[str] = Header(None)):
    """Verify API key from Authorization header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")
    
    token = authorization[7:]
    if token != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    return token


@app.get("/health")
async def health_check():
    """Health check endpoint (no auth required)."""
    return {
        "status": "healthy",
        "transport": "http-streamable",
        "mcp_version": "1.0.0"
    }


@app.post("/mcp/list_tools")
async def list_tools(authorization: str = Header(None)):
    """MCP list_tools endpoint - returns available tools."""
    await verify_api_key(authorization)
    
    tools = [
        {
            "name": "get_nodes",
            "description": "List all Proxmox nodes in the cluster",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "get_node_status",
            "description": "Get status of a specific Proxmox node",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "node": {"type": "string", "description": "Node name"}
                },
                "required": ["node"]
            }
        },
        {
            "name": "get_vms",
            "description": "List all VMs across all nodes",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "start_vm",
            "description": "Start a VM",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "node": {"type": "string", "description": "Node name"},
                    "vmid": {"type": "string", "description": "VM ID"}
                },
                "required": ["node", "vmid"]
            }
        },
        {
            "name": "stop_vm",
            "description": "Stop a VM (forced)",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "node": {"type": "string", "description": "Node name"},
                    "vmid": {"type": "string", "description": "VM ID"}
                },
                "required": ["node", "vmid"]
            }
        },
        {
            "name": "shutdown_vm",
            "description": "Gracefully shutdown a VM",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "node": {"type": "string", "description": "Node name"},
                    "vmid": {"type": "string", "description": "VM ID"}
                },
                "required": ["node", "vmid"]
            }
        },
        {
            "name": "reset_vm",
            "description": "Reset/reboot a VM",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "node": {"type": "string", "description": "Node name"},
                    "vmid": {"type": "string", "description": "VM ID"}
                },
                "required": ["node", "vmid"]
            }
        },
        {
            "name": "delete_vm",
            "description": "Delete a VM",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "node": {"type": "string", "description": "Node name"},
                    "vmid": {"type": "string", "description": "VM ID"},
                    "force": {"type": "boolean", "description": "Force deletion", "default": False}
                },
                "required": ["node", "vmid"]
            }
        },
        {
            "name": "get_storage",
            "description": "List all storage in the cluster",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "get_cluster_status",
            "description": "Get cluster status",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "get_containers",
            "description": "List all LXC containers",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "node": {"type": "string", "description": "Optional node name"},
                    "include_stats": {"type": "boolean", "default": True},
                    "format_style": {"type": "string", "enum": ["pretty", "json"], "default": "pretty"}
                },
                "required": []
            }
        },
        {
            "name": "start_container",
            "description": "Start a container",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "Container selector (ID or name)"},
                    "format_style": {"type": "string", "enum": ["pretty", "json"], "default": "pretty"}
                },
                "required": ["selector"]
            }
        },
        {
            "name": "stop_container",
            "description": "Stop a container",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "selector": {"type": "string"},
                    "graceful": {"type": "boolean", "default": True},
                    "timeout_seconds": {"type": "integer", "default": 10},
                    "format_style": {"type": "string", "enum": ["pretty", "json"], "default": "pretty"}
                },
                "required": ["selector"]
            }
        }
    ]
    
    return {"tools": tools}


class CallToolRequest(BaseModel):
    """Request model for call_tool endpoint."""
    name: str
    arguments: dict = {}


@app.post("/mcp/call_tool")
async def call_tool(request: CallToolRequest, authorization: str = Header(None)):
    """MCP call_tool endpoint - execute a tool and return results."""
    await verify_api_key(authorization)
    
    tool_name = request.name
    args = request.arguments
    
    try:
        # Route to appropriate tool
        if tool_name == "get_nodes":
            result = node_tools.get_nodes()
        elif tool_name == "get_node_status":
            result = node_tools.get_node_status(args["node"])
        elif tool_name == "get_vms":
            result = vm_tools.get_vms()
        elif tool_name == "start_vm":
            result = vm_tools.start_vm(args["node"], args["vmid"])
        elif tool_name == "stop_vm":
            result = vm_tools.stop_vm(args["node"], args["vmid"])
        elif tool_name == "shutdown_vm":
            result = vm_tools.shutdown_vm(args["node"], args["vmid"])
        elif tool_name == "reset_vm":
            result = vm_tools.reset_vm(args["node"], args["vmid"])
        elif tool_name == "delete_vm":
            force = args.get("force", False)
            result = vm_tools.delete_vm(args["node"], args["vmid"], force)
        elif tool_name == "get_storage":
            result = storage_tools.get_storage()
        elif tool_name == "get_cluster_status":
            result = cluster_tools.get_cluster_status()
        elif tool_name == "get_containers":
            result = container_tools.get_containers(
                node=args.get("node"),
                include_stats=args.get("include_stats", True),
                format_style=args.get("format_style", "pretty")
            )
        elif tool_name == "start_container":
            result = container_tools.start_container(
                selector=args["selector"],
                format_style=args.get("format_style", "pretty")
            )
        elif tool_name == "stop_container":
            result = container_tools.stop_container(
                selector=args["selector"],
                graceful=args.get("graceful", True),
                timeout_seconds=args.get("timeout_seconds", 10),
                format_style=args.get("format_style", "pretty")
            )
        else:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
        
        # Return result in MCP format
        return {
            "content": [
                {
                    "type": "text",
                    "text": str(result)
                }
            ]
        }
        
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing required argument: {e}")
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Error executing tool: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HTTP_HOST", "0.0.0.0")
    port = int(os.getenv("HTTP_PORT", "3333"))
    
    uvicorn.run(app, host=host, port=port)
