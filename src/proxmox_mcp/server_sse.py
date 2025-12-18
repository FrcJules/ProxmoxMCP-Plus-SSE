"""
Complete MCP server with all Proxmox tools for n8n.
Handles both GET (SSE) and POST (JSON-RPC) on the same endpoint.
"""
import os
import sys
import uvicorn
import asyncio
import json
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional, AsyncGenerator
from uuid import uuid4

from proxmox_mcp.config.loader import load_config
from proxmox_mcp.core.logging import setup_logging
from proxmox_mcp.core.proxmox import ProxmoxManager
from proxmox_mcp.tools.node import NodeTools
from proxmox_mcp.tools.vm import VMTools
from proxmox_mcp.tools.storage import StorageTools
from proxmox_mcp.tools.cluster import ClusterTools
from proxmox_mcp.tools.containers import ContainerTools

API_KEY = None
logger = None
sessions = {}

# Global tools instances
node_tools = None
vm_tools = None
storage_tools = None
cluster_tools = None
container_tools = None

async def verify_api_key(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")
    
    token = authorization[7:]
    
    if token != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    return token

def get_all_tools():
    """Return list of all available tools"""
    return [
        # Node tools
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
                    "node": {"type": "string", "description": "Node name (e.g. 'pve1', 'proxmox-node2')"}
                },
                "required": ["node"]
            }
        },
        # VM tools
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
            "name": "create_vm",
            "description": "Create a new VM",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "node": {"type": "string", "description": "Host node name (e.g. 'pve')"},
                    "vmid": {"type": "string", "description": "New VM ID number (e.g. '200', '300')"},
                    "name": {"type": "string", "description": "VM name"},
                    "cpus": {"type": "integer", "description": "Number of CPU cores", "minimum": 1, "maximum": 32},
                    "memory": {"type": "integer", "description": "Memory size in MB (e.g. 2048 for 2GB)", "minimum": 512},
                    "disk_size": {"type": "integer", "description": "Disk size in GB", "minimum": 5},
                    "storage": {"type": "string", "description": "Storage name (optional)"},
                    "ostype": {"type": "string", "description": "OS type (optional, default: 'l26')"}
                },
                "required": ["node", "vmid", "name", "cpus", "memory", "disk_size"]
            }
        },
        {
            "name": "start_vm",
            "description": "Start a VM",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "node": {"type": "string", "description": "Host node name"},
                    "vmid": {"type": "string", "description": "VM ID number"}
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
                    "node": {"type": "string", "description": "Host node name"},
                    "vmid": {"type": "string", "description": "VM ID number"}
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
                    "node": {"type": "string", "description": "Host node name"},
                    "vmid": {"type": "string", "description": "VM ID number"}
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
                    "node": {"type": "string", "description": "Host node name"},
                    "vmid": {"type": "string", "description": "VM ID number"}
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
                    "node": {"type": "string", "description": "Host node name"},
                    "vmid": {"type": "string", "description": "VM ID number"},
                    "force": {"type": "boolean", "description": "Force deletion even if VM is running", "default": False}
                },
                "required": ["node", "vmid"]
            }
        },
        # Storage tools
        {
            "name": "get_storage",
            "description": "List all storage in the cluster",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        # Cluster tools
        {
            "name": "get_cluster_status",
            "description": "Get cluster status",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        # Container tools
        {
            "name": "get_containers",
            "description": "List all LXC containers",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "node": {"type": "string", "description": "Optional node name to filter"},
                    "include_stats": {"type": "boolean", "description": "Include live stats", "default": True},
                    "format_style": {"type": "string", "description": "Output format", "enum": ["pretty", "json"], "default": "pretty"}
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
                    "selector": {"type": "string", "description": "Container selector: ID, name, or 'node:id'"},
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
                    "selector": {"type": "string", "description": "Container selector"},
                    "graceful": {"type": "boolean", "description": "Graceful shutdown", "default": True},
                    "timeout_seconds": {"type": "integer", "description": "Timeout in seconds", "default": 10},
                    "format_style": {"type": "string", "enum": ["pretty", "json"], "default": "pretty"}
                },
                "required": ["selector"]
            }
        },
        {
            "name": "restart_container",
            "description": "Restart a container",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "Container selector"},
                    "timeout_seconds": {"type": "integer", "description": "Timeout in seconds", "default": 10},
                    "format_style": {"type": "string", "enum": ["pretty", "json"], "default": "pretty"}
                },
                "required": ["selector"]
            }
        },
        {
            "name": "update_container_resources",
            "description": "Update container resources (CPU, memory, disk)",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "Container selector"},
                    "cores": {"type": "integer", "description": "New CPU core count", "minimum": 1},
                    "memory": {"type": "integer", "description": "New memory limit in MiB", "minimum": 16},
                    "swap": {"type": "integer", "description": "New swap limit in MiB", "minimum": 0},
                    "disk_gb": {"type": "integer", "description": "Additional disk size in GiB", "minimum": 1},
                    "disk": {"type": "string", "description": "Disk to resize", "default": "rootfs"},
                    "format_style": {"type": "string", "enum": ["pretty", "json"], "default": "pretty"}
                },
                "required": ["selector"]
            }
        }
    ]

async def execute_tool(tool_name: str, arguments: dict) -> dict:
    """Execute a tool and return the result"""
    global node_tools, vm_tools, storage_tools, cluster_tools, container_tools, logger
    
    try:
        # Node tools
        if tool_name == "get_nodes":
            result = node_tools.get_nodes()
        elif tool_name == "get_node_status":
            result = node_tools.get_node_status(arguments["node"])
        
        # VM tools
        elif tool_name == "get_vms":
            result = vm_tools.get_vms()
        elif tool_name == "create_vm":
            result = vm_tools.create_vm(
                arguments["node"],
                arguments["vmid"],
                arguments["name"],
                arguments["cpus"],
                arguments["memory"],
                arguments["disk_size"],
                arguments.get("storage"),
                arguments.get("ostype")
            )
        elif tool_name == "start_vm":
            result = vm_tools.start_vm(arguments["node"], arguments["vmid"])
        elif tool_name == "stop_vm":
            result = vm_tools.stop_vm(arguments["node"], arguments["vmid"])
        elif tool_name == "shutdown_vm":
            result = vm_tools.shutdown_vm(arguments["node"], arguments["vmid"])
        elif tool_name == "reset_vm":
            result = vm_tools.reset_vm(arguments["node"], arguments["vmid"])
        elif tool_name == "delete_vm":
            result = vm_tools.delete_vm(
                arguments["node"],
                arguments["vmid"],
                arguments.get("force", False)
            )
        
        # Storage tools
        elif tool_name == "get_storage":
            result = storage_tools.get_storage()
        
        # Cluster tools
        elif tool_name == "get_cluster_status":
            result = cluster_tools.get_cluster_status()
        
        # Container tools
        elif tool_name == "get_containers":
            result = container_tools.get_containers(
                node=arguments.get("node"),
                include_stats=arguments.get("include_stats", True),
                include_raw=False,
                format_style=arguments.get("format_style", "pretty")
            )
        elif tool_name == "start_container":
            result = container_tools.start_container(
                selector=arguments["selector"],
                format_style=arguments.get("format_style", "pretty")
            )
        elif tool_name == "stop_container":
            result = container_tools.stop_container(
                selector=arguments["selector"],
                graceful=arguments.get("graceful", True),
                timeout_seconds=arguments.get("timeout_seconds", 10),
                format_style=arguments.get("format_style", "pretty")
            )
        elif tool_name == "restart_container":
            result = container_tools.restart_container(
                selector=arguments["selector"],
                timeout_seconds=arguments.get("timeout_seconds", 10),
                format_style=arguments.get("format_style", "pretty")
            )
        elif tool_name == "update_container_resources":
            result = container_tools.update_container_resources(
                selector=arguments["selector"],
                cores=arguments.get("cores"),
                memory=arguments.get("memory"),
                swap=arguments.get("swap"),
                disk_gb=arguments.get("disk_gb"),
                disk=arguments.get("disk", "rootfs"),
                format_style=arguments.get("format_style", "pretty")
            )
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        logger.info(f"Tool {tool_name} executed successfully")
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": str(result)
                }
            ]
        }
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {e}")
        raise

async def handle_jsonrpc(request_data: dict) -> dict:
    """Handle JSON-RPC 2.0 MCP requests"""
    method = request_data.get("method")
    params = request_data.get("params", {})
    req_id = request_data.get("id")
    
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "proxmox-mcp",
                    "version": "1.0.0"
                }
            }
        }
    
    elif method == "tools/list":
        tools = get_all_tools()
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": tools
            }
        }
    
    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        try:
            result = await execute_tool(tool_name, arguments)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": result
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
    
    else:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}"
            }
        }

async def sse_generator(session_id: str) -> AsyncGenerator[str, None]:
    """Generate SSE events"""
    yield f"event: endpoint\ndata: /proxmox/mcp/sse?session_id={session_id}\n\n"
    
    while True:
        await asyncio.sleep(30)
        yield ": keepalive\n\n"

def main():
    global API_KEY, logger, node_tools, vm_tools, storage_tools, cluster_tools, container_tools
    
    config_path = os.getenv("PROXMOX_MCP_CONFIG")
    if not config_path:
        print("PROXMOX_MCP_CONFIG environment variable must be set")
        sys.exit(1)
    
    API_KEY = os.getenv("MCPO_API_KEY")
    if not API_KEY:
        print("MCPO_API_KEY environment variable must be set")
        sys.exit(1)
    
    host = os.getenv("SSE_HOST", "0.0.0.0")
    port = int(os.getenv("SSE_PORT", "8812"))
    
    try:
        # Initialize configuration and tools
        config = load_config(config_path)
        logger = setup_logging(config.logging)
        
        logger.info(f"Starting Proxmox MCP Complete Server for n8n on {host}:{port}")
        
        proxmox_manager = ProxmoxManager(config.proxmox, config.auth)
        proxmox = proxmox_manager.get_api()
        
        node_tools = NodeTools(proxmox)
        vm_tools = VMTools(proxmox)
        storage_tools = StorageTools(proxmox)
        cluster_tools = ClusterTools(proxmox)
        container_tools = ContainerTools(proxmox)
        
        logger.info(f"Initialized all Proxmox tools")
        logger.info(f"Total tools available: {len(get_all_tools())}")
        
        app = FastAPI(
            title="Proxmox MCP Complete Server (n8n)",
            version="1.0.0",
            docs_url=None,
            redoc_url=None,
            openapi_url=None
        )
        
        @app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "transport": "hybrid-sse-jsonrpc",
                "endpoint": "/proxmox/mcp/sse",
                "total_tools": len(get_all_tools())
            }
        
        @app.get("/proxmox/mcp/sse")
        async def mcp_sse_get(authorization: str = Header(None)):
            """Handle GET requests - SSE connection"""
            await verify_api_key(authorization)
            
            session_id = str(uuid4())
            sessions[session_id] = {}
            
            logger.info(f"SSE connection established, session: {session_id}")
            
            return StreamingResponse(
                sse_generator(session_id),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-store",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        
        @app.post("/proxmox/mcp/sse")
        async def mcp_sse_post(request: Request, authorization: str = Header(None)):
            """Handle POST requests - JSON-RPC messages"""
            await verify_api_key(authorization)
            
            body = await request.json()
            logger.info(f"JSON-RPC request: {body.get('method')}")
            
            response = await handle_jsonrpc(body)
            return JSONResponse(response)
        
        logger.info("Complete MCP Server ready for n8n")
        logger.info(f"Available tools: {', '.join([t['name'] for t in get_all_tools()])}")
        
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
