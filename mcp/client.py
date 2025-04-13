import os
import sys
import json
import asyncio
import subprocess
from pathlib import Path
import signal
import atexit
import time
import threading
from typing import Dict, List, Any, Optional, Union, Tuple

# Import ClientSession from separate file to avoid circular imports
from .client_session import ClientSession
from mcp.client.stdio import stdio_client, StdinStdoutStream, StdioServerParameters

class MCPClient:
    """MCP client for the job portal application"""
    
    def __init__(self, server_path=None, lm_server_url=None):
        """Initialize the MCP client with optional server configuration"""
        self.server_path = server_path or os.path.join(os.path.dirname(__file__), 'server.py')
        self.lm_server_url = lm_server_url or "http://localhost:1234/v1"
        self.server_process = None
        self.session = None
        self._lock = threading.RLock()
        self._transport = None
        
    async def start_server(self):
        """Start the MCP server process"""
        try:
            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"  # Ensure output is not buffered
            self.server_process = subprocess.Popen(
                [sys.executable, self.server_path],
                env=env,
                stdout=subprocess.PIPE,
                stdin=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=False,
                bufsize=0,
            )
            # Register cleanup function to ensure server is terminated
            atexit.register(self.terminate_server)
            
            # Wait for server to initialize
            time.sleep(1)
            
            return True
        except Exception as e:
            print(f"Error starting MCP server: {e}")
            return False
    
    def terminate_server(self):
        """Terminate the MCP server process"""
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
            finally:
                self.server_process = None
                atexit.unregister(self.terminate_server)
    
    async def connect(self):
        """Connect to the MCP server"""
        try:
            with self._lock:
                if self.server_process is None:
                    await self.start_server()
                
                if self.server_process and self.session is None:
                    params = StdioServerParameters(process=self.server_process)
                    self._transport = await stdio_client(params)
                    self.session = await ClientSession.connect(*self._transport)
                    return True
                return False
        except Exception as e:
            print(f"Error connecting to MCP server: {e}")
            return False
    
    async def close(self):
        """Close the connection to the MCP server"""
        with self._lock:
            if self.session:
                await self.session.aclose()
                self.session = None
            
            if self._transport:
                await self._transport[0].aclose()
                await self._transport[1].aclose()
                self._transport = None
            
            self.terminate_server()
    
    async def list_tools(self) -> List[dict]:
        """List available tools from the MCP server"""
        try:
            if not self.session:
                if not await self.connect():
                    return []
            
            response = await self.session.list_tools()
            return [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema
                }
                for tool in response.tools
            ]
        except Exception as e:
            print(f"Error listing tools: {e}")
            return []
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call a tool on the MCP server"""
        try:
            if not self.session:
                if not await self.connect():
                    return "Failed to connect to MCP server"
            
            result = await self.session.call_tool(tool_name, arguments)
            
            # Extract text from response
            text_parts = []
            for content in result.content:
                if hasattr(content, "text") and content.text:
                    text_parts.append(content.text)
            
            return "\n".join(text_parts)
        except Exception as e:
            print(f"Error calling tool '{tool_name}': {e}")
            return f"Error calling tool: {str(e)}"

# Helper function to run async functions from synchronous code
def run_async(coro):
    """Run an asynchronous coroutine from synchronous code"""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

# 해당 함수들은 __init__.py로 옮겨갔습니다
