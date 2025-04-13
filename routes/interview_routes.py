from flask import Blueprint, render_template, request, jsonify, current_app
from models import db, InterviewPrep, Job

interview = Blueprint('interview', __name__)

@interview.route('/interview')
def interview_prep():
    """면접 준비 페이지"""
    jobs = Job.query.filter(Job.status.in_(['서류합격', '1차면접', '2차면접'])).order_by(Job.created_at.desc()).all()
    interview_questions = InterviewPrep.query.order_by(InterviewPrep.created_at.desc()).all()
    
    return render_template('interview.html', 
                          jobs=jobs, 
                          questions=interview_questions, 
                          mcp_enabled=current_app.config.get('MCP_ENABLED', False))

@interview.route('/interview/<int:job_id>')
def interview_prep_for_job(job_id):
    """특정 채용에 대한 면접 준비 페이지"""
    job = Job.query.get_or_404(job_id)
    interview_questions = InterviewPrep.query.filter_by(job_id=job_id).order_by(InterviewPrep.created_at.desc()).all()
    
    return render_template('interview.html', 
                          job=job, 
                          questions=interview_questions, 
                          mcp_enabled=current_app.config.get('MCP_ENABLED', False))

@interview.route('/interview/questions', methods=['GET'])
def get_interview_questions():
    """면접 질문 목록 API"""
    job_id = request.args.get('job_id', type=int)
    category = request.args.get('category')
    
    # 쿼리 생성
    query = InterviewPrep.query
    
    # 필터 적용
    if job_id:
        query = query.filter_by(job_id=job_id)
    if category:
        query = query.filter_by(category=category)
    
    questions = query.order_by(InterviewPrep.created_at.desc()).all()
    
    return jsonify([q.to_dict() for q in questions])

@interview.route('/interview/questions', methods=['POST'])
def create_interview_question():
    """면접 질문 생성 API"""
    try:
        data = request.json or {}
        
        # 폼 데이터에서 가져오기
        if not data:
            data = {
                'job_id': request.form.get('job_id', type=int),
                'question': request.form.get('question'),
                'answer': request.form.get('answer'),
                'category': request.form.get('category', '일반'),
                'difficulty': request.form.get('difficulty', type=int, default=1)
            }
        
        # 필수 필드 확인
        if not data.get('question'):
            return jsonify({"error": "질문 내용은 필수 입력 항목입니다."}), 400
        
        # 면접 질문 생성
        question = InterviewPrep(
            job_id=data.get('job_id'),
            question=data['question'],
            answer=data.get('answer'),
            category=data.get('category', '일반'),
            difficulty=data.get('difficulty', 1)
        )
        
        db.session.add(question)
        db.session.commit()
        
        return jsonify({"success": True, "question": question.to_dict()})
    
    except Exception as e:
        return jsonify({"error": f"면접 질문 생성 중 오류 발생: {str(e)}"}), 500

@interview.route('/interview/questions/<int:question_id>', methods=['PUT'])
def update_interview_question(question_id):
    """면접 질문 업데이트 API"""
    try:
        question = InterviewPrep.query.get_or_404(question_id)
        data = request.json
        
        # 필드 업데이트
        if 'question' in data:
            question.question = data['question']
        if 'answer' in data:
            question.answer = data['answer']
        if 'category' in data:
            question.category = data['category']
        if 'difficulty' in data:
            question.difficulty = data['difficulty']
        if 'job_id' in data:
            question.job_id = data['job_id']
        
        db.session.commit()
        
        return jsonify({"success": True, "question": question.to_dict()})
    
    except Exception as e:
        return jsonify({"error": f"면접 질문 업데이트 중 오류 발생: {str(e)}"}), 500

@interview.route('/interview/questions/<int:question_id>', methods=['DELETE'])
def delete_interview_question(question_id):
    """면접 질문 삭제 API"""
    try:
        question = InterviewPrep.query.get_or_404(question_id)
        db.session.delete(question)
        db.session.commit()
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": f"면접 질문 삭제 중 오류 발생: {str(e)}"}), 500

@interview.route('/interview/generate', methods=['POST'])
def generate_interview_questions():
    """AI를 사용한 면접 질문 자동 생성 API"""
    if not current_app.config.get('MCP_ENABLED', False):
        return jsonify({"error": "AI 기능이 활성화되지 않았습니다."}), 400
    
    try:
        data = request.json
        job_id = data.get('job_id')
        job_title = data.get('job_title')
        company_name = data.get('company_name')
        categories = data.get('categories', ['일반', '기술', '인성', '경험'])
        count = data.get('count', 5)
        
        if not job_title:
            # 직무 정보가 없으면 DB에서 조회
            if job_id:
                job = Job.query.get_or_404(job_id)
                job_title = job.title
                company_name = job.company_name
                
        if not job_title:
            return jsonify({"error": "직무 정보가 필요합니다."}), 400
            
        # 여기서 MCP 또는 LM Studio를 통해 질문 생성
        # 실제 구현은 AI 기능이 준비되면 추가
        return jsonify({"error": "아직 구현되지 않은 기능입니다."}), 501
    
    except Exception as e:
        return jsonify({"error": f"질문 생성 중 오류 발생: {str(e)}"}), 500

@interview.route('/interview/simulate', methods=['POST'])
def simulate_interview():
    """AI를 사용한 모의 면접 API"""
    if not current_app.config.get('MCP_ENABLED', False):
        return jsonify({"error": "AI 기능이 활성화되지 않았습니다."}), 400
    
    try:
        data = request.json
        question_id = data.get('question_id')
        answer = data.get('answer')
        
        if not question_id or not answer:
            return jsonify({"error": "질문 ID와 답변이 필요합니다."}), 400
        
        question = InterviewPrep.query.get_or_404(question_id)
        
        # 여기서 MCP 또는 LM Studio를 통해 답변 피드백 생성
        # 실제 구현은 AI 기능이 준비되면 추가
        return jsonify({"error": "아직 구현되지 않은 기능입니다."}), 501
    
    except Exception as e:
        return jsonify({"error": f"모의 면접 중 오류 발생: {str(e)}"}), 500
