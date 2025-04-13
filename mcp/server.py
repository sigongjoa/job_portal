import os
import json
import sys
from typing import Any, Dict, List

# Try to import MCP implementation
try:
    from modelcontextprotocol.server import Server, types
    from modelcontextprotocol.server.stdio import stdio_server
    mcp_available = True
except ImportError:
    # Create mock classes for compatibility
    mcp_available = False
    
    class MockTypes:
        class TextContent:
            def __init__(self, type="text", text=""):
                self.type = type
                self.text = text
        
        class Tool:
            def __init__(self, name="", description="", inputSchema=None):
                self.name = name
                self.description = description
                self.inputSchema = inputSchema or {}
    
    class MockServer:
        def __init__(self, name):
            self.name = name
        
        def list_tools(self):
            def decorator(func):
                return func
            return decorator
        
        def call_tool(self):
            def decorator(func):
                return func
            return decorator
        
        def create_initialization_options(self):
            return {}
        
        async def run(self, *args, **kwargs):
            pass
    
    async def mock_stdio_server():
        class MockContext:
            async def __aenter__(self):
                return [None, None]
            
            async def __aexit__(self, *args):
                pass
        
        return MockContext()
    
    # Set up mocks
    Server = MockServer
    types = MockTypes()
    stdio_server = mock_stdio_server

# LM Studio integration using default OpenAI-compatible API
import requests

class MCPJobPortalServer:
    """MCP Server for Job Portal application with LM Studio integration"""
    
    def __init__(self, lm_studio_api_url="http://localhost:1234/v1", model_name="Local Model"):
        """Initialize the MCP server with LM Studio connection details"""
        self.lm_studio_api_url = lm_studio_api_url
        self.model_name = model_name
        self.app = Server("job-portal-server")
        
        # Register MCP tools and handlers
        self.register_tools()
    
    def register_tools(self):
        """Register MCP tools for job portal functions"""
        
        @self.app.list_tools()
        async def list_tools() -> list[types.Tool]:
            """List all available tools for the job portal"""
            return [
                types.Tool(
                    name="generate_resume",
                    description="Generate a resume for a job application",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "job_title": {"type": "string", "description": "Title of the job posting"},
                            "company_name": {"type": "string", "description": "Name of the company"},
                            "job_description": {"type": "string", "description": "Description of the job"},
                            "user_skills": {"type": "string", "description": "User's skills and experiences"}
                        },
                        "required": ["job_title", "company_name", "job_description"]
                    }
                ),
                types.Tool(
                    name="analyze_job_posting",
                    description="Analyze a job posting to find key requirements and skills",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "job_title": {"type": "string", "description": "Title of the job posting"},
                            "job_description": {"type": "string", "description": "Full job description text"}
                        },
                        "required": ["job_title", "job_description"]
                    }
                ),
                types.Tool(
                    name="draft_cover_letter",
                    description="Draft a cover letter for a job application",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "job_title": {"type": "string", "description": "Title of the job posting"},
                            "company_name": {"type": "string", "description": "Name of the company"},
                            "user_background": {"type": "string", "description": "Brief background of the user"},
                            "key_points": {"type": "string", "description": "Key points to emphasize"}
                        },
                        "required": ["job_title", "company_name"]
                    }
                ),
                types.Tool(
                    name="suggest_interview_answers",
                    description="Suggest answers for common interview questions",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "job_title": {"type": "string", "description": "Title of the job posting"},
                            "interview_question": {"type": "string", "description": "The interview question to answer"},
                            "user_background": {"type": "string", "description": "Brief background of the user"}
                        },
                        "required": ["interview_question"]
                    }
                )
            ]
    
        @self.app.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
            """Handle tool calls by calling LM Studio API"""
            try:
                if name == "generate_resume":
                    return await self._call_generate_resume(arguments)
                elif name == "analyze_job_posting":
                    return await self._call_analyze_job_posting(arguments)
                elif name == "draft_cover_letter":
                    return await self._call_draft_cover_letter(arguments)
                elif name == "suggest_interview_answers":
                    return await self._call_suggest_interview_answers(arguments)
                else:
                    return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
            except Exception as e:
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]
    
    async def _call_lm_studio(self, system_prompt: str, user_prompt: str) -> str:
        """Call LM Studio API with the given prompts"""
        try:
            # Create OpenAI-compatible request
            api_endpoint = f"{self.lm_studio_api_url}/chat/completions"
            
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 1500
            }
            
            # Make the API request
            response = requests.post(api_endpoint, json=payload)
            response.raise_for_status()
            
            # Extract and return the generated text
            result = response.json()
            return result['choices'][0]['message']['content']
        except Exception as e:
            print(f"Error calling LM Studio API: {str(e)}", file=sys.stderr)
            return f"Failed to generate response: {str(e)}"
    
    async def _call_generate_resume(self, arguments: Dict[str, Any]) -> list[types.TextContent]:
        """Generate a resume using LM Studio"""
        job_title = arguments.get("job_title", "")
        company_name = arguments.get("company_name", "")
        job_description = arguments.get("job_description", "")
        user_skills = arguments.get("user_skills", "No specific skills provided")
        
        system_prompt = "You are an expert resume writer. Create a professional resume tailored for the specific job posting."
        
        user_prompt = f"""
        I'm applying for the position of {job_title} at {company_name}.
        
        Job Description:
        {job_description}
        
        My Skills and Experience:
        {user_skills}
        
        Please create a professional resume that highlights my relevant skills and experience for this position.
        Format it properly with sections for Summary, Skills, Experience, and Education.
        """
        
        response = await self._call_lm_studio(system_prompt, user_prompt)
        return [types.TextContent(type="text", text=response)]
    
    async def _call_analyze_job_posting(self, arguments: Dict[str, Any]) -> list[types.TextContent]:
        """Analyze a job posting using LM Studio"""
        job_title = arguments.get("job_title", "")
        job_description = arguments.get("job_description", "")
        
        system_prompt = "You are an expert job posting analyst. Extract key requirements, skills, and qualifications from job descriptions."
        
        user_prompt = f"""
        Please analyze this job posting for {job_title} and provide:
        
        1. A list of required technical skills
        2. Required years of experience
        3. Required education level
        4. Any specific certifications or qualifications mentioned
        5. Key responsibilities
        6. Any red flags or warning signs in the posting (if any)
        
        Job Description:
        {job_description}
        """
        
        response = await self._call_lm_studio(system_prompt, user_prompt)
        return [types.TextContent(type="text", text=response)]
    
    async def _call_draft_cover_letter(self, arguments: Dict[str, Any]) -> list[types.TextContent]:
        """Draft a cover letter using LM Studio"""
        job_title = arguments.get("job_title", "")
        company_name = arguments.get("company_name", "")
        user_background = arguments.get("user_background", "No specific background provided")
        key_points = arguments.get("key_points", "No specific points provided")
        
        system_prompt = "You are an expert cover letter writer. Create a professional cover letter tailored for the specific job posting."
        
        user_prompt = f"""
        I'm applying for the position of {job_title} at {company_name}.
        
        My Background:
        {user_background}
        
        Key points I want to emphasize:
        {key_points}
        
        Please draft a professional cover letter that highlights my qualifications for this position.
        Keep it concise, professional, and persuasive.
        """
        
        response = await self._call_lm_studio(system_prompt, user_prompt)
        return [types.TextContent(type="text", text=response)]
    
    async def _call_suggest_interview_answers(self, arguments: Dict[str, Any]) -> list[types.TextContent]:
        """Suggest interview answers using LM Studio"""
        job_title = arguments.get("job_title", "")
        interview_question = arguments.get("interview_question", "")
        user_background = arguments.get("user_background", "No specific background provided")
        
        system_prompt = "You are an expert interview coach. Provide effective answers to interview questions."
        
        user_prompt = f"""
        I'm preparing for an interview for the position of {job_title}.
        
        My Background:
        {user_background}
        
        Please suggest a good answer for this interview question:
        "{interview_question}"
        
        Provide a structured answer with:
        1. A brief introduction/approach to the question
        2. The main points to cover
        3. A strong closing statement
        """
        
        response = await self._call_lm_studio(system_prompt, user_prompt)
        return [types.TextContent(type="text", text=response)]
    
    async def run(self):
        """Run the MCP server"""
        print("Starting MCP server for Job Portal with LM Studio integration...", file=sys.stderr)
        async with stdio_server() as streams:
            await self.app.run(
                streams[0],
                streams[1],
                self.app.create_initialization_options()
            )

async def main():
    """Main function to start the MCP server"""
    if not mcp_available:
        print("Error: modelcontextprotocol package is not available.", file=sys.stderr)
        print("Please install it with: pip install modelcontextprotocol", file=sys.stderr)
        return
    
    server = MCPJobPortalServer()
    await server.run()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
