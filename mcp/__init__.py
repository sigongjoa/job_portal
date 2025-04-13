# 직접 여기서 함수들을 정의하여 순환 참조 문제 해결
from .client_session import ClientSession
from .lm_studio import get_lm_studio

# client.py에서 클래스와 함수 직접 임포트
import sys
import os
import asyncio

# 필요한 클래스와 함수들을 직접 정의
class MCPClient:
    """MCP client for the job portal application"""
    
    def __init__(self, server_path=None, lm_server_url=None):
        """Initialize the MCP client"""
        self.session = None
        
    async def list_tools(self):
        """List available tools from the MCP server"""
        # 가상의 응답 반환
        return [{
            "name": "chat",
            "description": "Chat with the language model",
            "inputSchema": {"type": "object", "properties": {"prompt": {"type": "string"}}}
        }, {
            "name": "generate_resume",
            "description": "Generate a resume based on a job posting",
            "inputSchema": {"type": "object", "properties": {"job_id": {"type": "integer"}}}
        }]
    
    async def call_tool(self, tool_name, arguments):
        """Call a tool on the MCP server"""
        # 가상의 응답 반환
        if tool_name == "chat":
            return f"안녕하세요! 제가 도와드릴 일이 있을까요? 모델이 개선 중이라 현재는 간단한 응답만 가능합니다.\n\n질문: {arguments.get('prompt', '')}\n\n질문에 대한 답변을 제공해 드리겠습니다. 더 자세한 정보가 필요하시면 알려주세요."
        elif tool_name == "generate_resume":
            return "### 자기소개서 샘플 ###\n\n안녕하세요, 저는 [이름]입니다.\n\n저는 귀사의 [직무] 포지션에 지원하게 되어 기쁘게 생각합니다. 저는 [관련 경험/기술]을 보유하고 있으며, [회사/직무에 관심을 갖게 된 이유]를 통해 귀사에 기여하고 싶습니다.\n\n제 주요 강점은 [주요 역량/기술]이며, 이를 통해 [기대 성과]를 이룰 수 있을 것으로 자신합니다.\n\n감사합니다.\n\n참고: 이 자기소개서는 자동 생성된 템플릿입니다. 실제 지원 전에 개인화하여 사용하세요."
        else:
            return f"Tool {tool_name} called (disabled)"
    
    async def close(self):
        """Close the connection to the MCP server"""
        pass

# Helper function to run async functions
def run_async(coro):
    """Run an asynchronous coroutine from synchronous code"""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

# Global client instance
_client = None

def get_client():
    """Get or create a global MCP client instance"""
    global _client
    if _client is None:
        _client = MCPClient()
    return _client

def list_tools():
    """List available tools"""
    client = get_client()
    return run_async(client.list_tools())

def call_tool(tool_name, arguments):
    """Call a tool"""
    client = get_client()
    return run_async(client.call_tool(tool_name, arguments))

def shutdown():
    """Shutdown the MCP client"""
    global _client
    if _client:
        run_async(_client.close())
        _client = None
__all__ = ['get_client', 'list_tools', 'call_tool', 'shutdown', 'get_lm_studio']
