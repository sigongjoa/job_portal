from flask import Blueprint, render_template, request, jsonify, current_app
from models import db, Job

ai = Blueprint('ai', __name__)

@ai.route('/ai/assistant')
def ai_assistant():
    """AI 도우미 페이지"""
    lm_studio_connected = False
    tools = []
    
    # LM Studio 연결 확인
    mcp_enabled = current_app.config.get('MCP_ENABLED', False)
    if mcp_enabled:
        try:
            from mcp import get_lm_studio, list_tools
            lm_studio = get_lm_studio(current_app.config['LM_STUDIO_URL'])
            lm_studio_connected = lm_studio.check_connection()
            
            # MCP 도구 목록 가져오기
            if lm_studio_connected:
                try:
                    tools = list_tools()
                except Exception as e:
                    current_app.logger.error(f"Error listing MCP tools: {e}")
                    # 기본 도구 목록 제공
                    tools = [
                        {
                            "name": "chat",
                            "description": "Chat with the language model"
                        },
                        {
                            "name": "generate_resume",
                            "description": "Generate a resume based on a job posting"
                        }
                    ]
        except Exception as e:
            current_app.logger.error(f"Error connecting to LM Studio: {e}")
            # 연결 오류 시에도 기본 도구 제공
            tools = [
                {
                    "name": "chat",
                    "description": "Chat with the language model"
                },
                {
                    "name": "generate_resume",
                    "description": "Generate a resume based on a job posting"
                }
            ]
    
    return render_template('ai_assistant.html', 
                           lm_studio_connected=lm_studio_connected,
                           tools=tools,
                           mcp_enabled=mcp_enabled)

@ai.route('/ai/assistant/<int:job_id>')
def ai_assistant_for_job(job_id):
    """특정 채용 정보에 대한 AI 도우미 페이지"""
    job = Job.query.get_or_404(job_id)
    lm_studio_connected = False
    tools = []
    
    # LM Studio 연결 확인
    mcp_enabled = current_app.config.get('MCP_ENABLED', False)
    if mcp_enabled:
        try:
            from mcp import get_lm_studio, list_tools
            lm_studio = get_lm_studio(current_app.config['LM_STUDIO_URL'])
            lm_studio_connected = lm_studio.check_connection()
            
            # MCP 도구 목록 가져오기
            if lm_studio_connected:
                try:
                    tools = list_tools()
                except Exception as e:
                    current_app.logger.error(f"Error listing MCP tools: {e}")
                    # 기본 도구 목록 제공
                    tools = [
                        {
                            "name": "chat",
                            "description": "Chat with the language model"
                        },
                        {
                            "name": "generate_resume",
                            "description": "Generate a resume based on a job posting"
                        }
                    ]
        except Exception as e:
            current_app.logger.error(f"Error connecting to LM Studio: {e}")
            # 연결 오류 시에도 기본 도구 제공
            tools = [
                {
                    "name": "chat",
                    "description": "Chat with the language model"
                },
                {
                    "name": "generate_resume",
                    "description": "Generate a resume based on a job posting"
                }
            ]
    
    return render_template('ai_assistant.html', 
                           job=job,
                           lm_studio_connected=lm_studio_connected,
                           tools=tools,
                           mcp_enabled=mcp_enabled)

@ai.route('/ai/call_tool', methods=['POST'])
def call_ai_tool():
    """AI 도구 호출 API"""
    mcp_enabled = current_app.config.get('MCP_ENABLED', False)
    if not mcp_enabled:
        return jsonify({"success": False, "error": "MCP 기능이 활성화되지 않았습니다."}), 400
    
    try:
        from mcp import call_tool
        data = request.json
        if not data:
            return jsonify({"success": False, "error": "요청 데이터가 없습니다."}), 400
            
        tool_name = data.get('tool_name')
        arguments = data.get('arguments', {})
        
        if not tool_name:
            return jsonify({"success": False, "error": "도구 이름이 필요합니다."}), 400
        
        # MCP 도구 호출
        result = call_tool(tool_name, arguments)
        
        if not result:
            return jsonify({"success": False, "error": "결과가 없습니다."}), 500
            
        return jsonify({"success": True, "result": result})
    except ImportError as e:
        current_app.logger.error(f"ImportError in call_ai_tool: {str(e)}")
        return jsonify({"success": False, "error": "MCP 모듈을 가져올 수 없습니다."}), 500
    except Exception as e:
        current_app.logger.error(f"Exception in call_ai_tool: {str(e)}")
        return jsonify({"success": False, "error": f"도구 호출 중 오류 발생: {str(e)}"}), 500

@ai.route('/ai/save_to_resume/<int:job_id>', methods=['POST'])
def save_to_resume(job_id):
    """AI 생성 내용을 자기소개서로 저장 API"""
    try:
        job = Job.query.get_or_404(job_id)
        data = request.json
        resume_text = data.get('resume_text')
        
        if not resume_text:
            return jsonify({"error": "저장할 내용이 없습니다."}), 400
        
        # 자기소개서 내용 업데이트
        job.resume = resume_text
        db.session.commit()
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": f"저장 중 오류 발생: {str(e)}"}), 500

@ai.route('/ai/analyze_job/<int:job_id>', methods=['GET'])
def analyze_job(job_id):
    """채용 공고 분석 API"""
    mcp_enabled = current_app.config.get('MCP_ENABLED', False)
    if not mcp_enabled:
        return jsonify({"error": "MCP 기능이 활성화되지 않았습니다."}), 400
    
    try:
        job = Job.query.get_or_404(job_id)
        
        # 샘플 분석 결과
        analysis = f"## {job.company_name} - {job.title} 분석 결과\n\n"
        analysis += "### 주요 업무\n\n"
        analysis += "- 웹 애플리케이션 개발 및 유지보수\n"
        analysis += "- 서버 사이드 로직 구현\n"
        analysis += "- 데이터베이스 설계 및 최적화\n\n"
        
        analysis += "### 자격 요건\n\n"
        analysis += "- 관련 분야 2년 이상 경력\n"
        analysis += "- 웹 개발 프레임워크 경험\n"
        analysis += "- 데이터베이스 지식\n\n"
        
        analysis += "### 권장 핵심 역량\n\n"
        analysis += "1. 문제 해결 능력\n"
        analysis += "2. 효율적인 코드 작성 능력\n"
        analysis += "3. 팀 협업 능력\n"
        
        return jsonify({"success": True, "analysis": analysis})
    
    except Exception as e:
        return jsonify({"error": f"분석 중 오류 발생: {str(e)}"}), 500

@ai.route('/ai/chat', methods=['POST'])
def chat_with_ai():
    """AI와 채팅 API"""
    mcp_enabled = current_app.config.get('MCP_ENABLED', False)
    if not mcp_enabled:
        return jsonify({"error": "MCP 기능이 활성화되지 않았습니다."}), 400
    
    try:
        from mcp import call_tool
        data = request.json
        message = data.get('message', '')
        
        if not message:
            return jsonify({"error": "메시지가 필요합니다."}), 400
        
        # MCP 도구 호출
        result = call_tool("chat", {"prompt": message})
        
        return jsonify({"success": True, "response": result})
    
    except ImportError:
        return jsonify({"error": "MCP 모듈을 가져올 수 없습니다."}), 500
    except Exception as e:
        return jsonify({"error": f"채팅 중 오류 발생: {str(e)}"}), 500
