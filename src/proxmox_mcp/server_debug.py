"""Debug server to see what n8n sends"""
import os
import sys
import uvicorn
from fastapi import FastAPI, Request, Header
from typing import Optional

API_KEY = None

async def verify_api_key(authorization: Optional[str] = Header(None)):
    global API_KEY
    return True  # Accept everything for debugging

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.api_route("/proxmox/mcp/sse", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def debug_endpoint(request: Request):
    body = None
    try:
        body = await request.body()
        body_text = body.decode('utf-8')
    except:
        body_text = "<unable to decode>"
    
    print(f"\n{'='*80}")
    print(f"METHOD: {request.method}")
    print(f"PATH: {request.url.path}")
    print(f"HEADERS:")
    for name, value in request.headers.items():
        print(f"  {name}: {value}")
    print(f"BODY:")
    print(f"  {body_text}")
    print(f"{'='*80}\n")
    
    return {"debug": "received", "method": request.method, "body": body_text}

if __name__ == "__main__":
    API_KEY = os.getenv("MCPO_API_KEY", "test")
    uvicorn.run(app, host="0.0.0.0", port=8812, log_level="info")
