import os
import sys
import json
import zipfile
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional
from flask.json.provider import JSONProvider
import jinja2

# nl2br 필터 추가
def nl2br(value):
    if value:
        return jinja2.utils.markupsafe.Markup(value.replace('\n', '<br>'))
    return ''

# MCP 패키지 로드 시도
try:
    from mcp import get_client, list_tools, call_tool, shutdown, get_lm_studio
    mcp_enabled = True
except ImportError as e:
    mcp_enabled = False
    print(f"ImportError: MCP 패키지 로드 중 문제가 발생했습니다.")
    print(f"오류 메시지: {e}")
except Exception as e:
    mcp_enabled = False
    print(f"Error: MCP 패키지 초기화 중 예상치 못한 오류가 발생했습니다.")
    print(f"오류 메시지: {e}")

# 크롤러 모듈 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), 'crawlers'))

from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file, flash, session
import time

# 모델 임포트
from models import db, Job, Company, CalendarEvent, InterviewPrep

# 라우트 임포트
from routes.main import main
from routes.job_routes import jobs
from routes.calendar_routes import calendar
from routes.company_routes import companies
from routes.interview_routes import interview
from routes.ai_routes import ai

# 자동으로 JSON을 직렬화하는 방법 설정을 수정
# datetime 객체를 문자열로 변환하는 함수 정의
def custom_json_encoder(obj):
    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%dT%H:%M:%S')
    elif isinstance(obj, date):
        return obj.strftime('%Y-%m-%d')
    return str(obj)

# JSON 직렬화 오류 처리
class FixedJSONProvider(JSONProvider):
    def dumps(self, obj, **kwargs):
        try:
            return json.dumps(obj, default=custom_json_encoder, **kwargs)
        except (TypeError, ValueError, OverflowError) as e:
            app.logger.error(f"JSON serialization error: {e}")
            # 오류가 발생하면 기본 오류 메시지 반환
            if isinstance(obj, (list, tuple)):
                return json.dumps({"error": "JSON 직렬화 오류가 발생했습니다."})
            return json.dumps(str(obj))

    def loads(self, s, **kwargs):
        return json.loads(s, **kwargs)
        
# 애플리케이션 초기화
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///job_portal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB 최대 파일 크기 제한
app.secret_key = 'job_portal_secret_key'

# nl2br 필터 등록
app.jinja_env.filters['nl2br'] = nl2br

# 커스텀 JSON 직렬화 설정
app.json = FixedJSONProvider(app)

# LM Studio 설정
app.config['LM_STUDIO_URL'] = 'http://localhost:12345/v1'
app.config['MCP_ENABLED'] = mcp_enabled

# 데이터베이스 초기화
db.init_app(app)

# 업로드 폴더 생성
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'portfolio'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'resume'), exist_ok=True)

# 블루프린트 등록
app.register_blueprint(main)
app.register_blueprint(jobs, url_prefix='/jobs')
app.register_blueprint(calendar, url_prefix='/calendar')
app.register_blueprint(companies, url_prefix='/companies')
app.register_blueprint(interview, url_prefix='/interview')
app.register_blueprint(ai, url_prefix='/ai')

# API 엔드포인트 추가 등록 (URL 충돌 해결)
from routes.company_routes import get_company, get_companies
app.add_url_rule('/api/companies/<int:company_id>', 'get_company_api', get_company)
app.add_url_rule('/api/companies', 'get_companies_api', get_companies)

def migrate_db():
    """기존 데이터를 새 스키마로 마이그레이션"""
    with app.app_context():
        # 새 컬럼이 있는지 확인
        inspector = db.inspect(db.engine)
        
        # Job 테이블 확인
        if 'job' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('job')]
            
            # 새 컬럼이 없으면 추가
            new_columns = ['status', 'note', 'deadline', 'resume', 'resume_file', 
                        'portfolio_file', 'application_date', 'company_id']
            
            if not all(col in columns for col in new_columns):
                # 임시 테이블에 기존 데이터 저장
                jobs_data = []
                for job in Job.query.all():
                    job_dict = {}
                    for column in columns:
                        job_dict[column] = getattr(job, column)
                    jobs_data.append(job_dict)
                
                # 테이블 스키마 업데이트
                db.drop_all()
                db.create_all()
                
                # 데이터 복원 및 status 필드 설정
                for data in jobs_data:
                    status = '지원' if data.pop('applied', False) else '미지원'
                    company_name = data.get('company_name', '알 수 없음')
                    
                    # 회사 정보 찾기 또는 생성
                    company = Company.query.filter_by(name=company_name).first()
                    if not company:
                        company = Company(name=company_name)
                        db.session.add(company)
                        db.session.flush()  # ID 할당을 위해 flush
                    
                    new_job = Job(
                        status=status,
                        company_id=company.id
                    )
                    # 나머지 데이터 복사
                    for key, value in data.items():
                        if key != 'id' and key != 'company_id':  # id, company_id는 제외
                            setattr(new_job, key, value)
                    
                    db.session.add(new_job)
                
                db.session.commit()
                print("데이터베이스 마이그레이션이 완료되었습니다.")
        else:
            # 테이블이 없으면 생성
            db.create_all()
            print("데이터베이스 테이블이 생성되었습니다.")

# 테스트용 더미 데이터 추가
def add_test_data():
    """테스트용 더미 데이터 추가"""
    # 기존 데이터가 없을 경우에만 추가
    if Job.query.count() == 0:
        # 회사 데이터 추가
        companies_data = [
            {
                'name': '테스트 회사 1',
                'industry': 'IT',
                'location': '서울',
                'website': 'https://company1.example.com',
                'description': '테스트 회사 1 설명'
            },
            {
                'name': '테스트 회사 2',
                'industry': '금융',
                'location': '부산',
                'website': 'https://company2.example.com',
                'description': '테스트 회사 2 설명'
            },
            {
                'name': '테스트 회사 3',
                'industry': '교육',
                'location': '대전',
                'website': 'https://company3.example.com',
                'description': '테스트 회사 3 설명'
            }
        ]
        
        # 회사 데이터 생성
        company_objects = {}
        for data in companies_data:
            company = Company(**data)
            db.session.add(company)
            db.session.flush()  # ID 할당을 위해 flush
            company_objects[company.name] = company
        
        # 채용 공고 데이터
        test_jobs = [
            {
                'site': '사람인',
                'company_name': '테스트 회사 1',
                'title': '백엔드 개발자 채용',
                'url': 'https://www.saramin.co.kr/job/1',
                'status': '미지원',
                'deadline': datetime.strptime('2025-05-10', '%Y-%m-%d').date(),
                'company_id': company_objects['테스트 회사 1'].id
            },
            {
                'site': '잡플래닛',
                'company_name': '테스트 회사 2',
                'title': '프론트엔드 개발자 채용',
                'url': 'https://www.jobplanet.co.kr/job/2',
                'status': '지원',
                'application_date': datetime.strptime('2025-04-01', '%Y-%m-%d').date(),
                'deadline': datetime.strptime('2025-04-30', '%Y-%m-%d').date(),
                'company_id': company_objects['테스트 회사 2'].id
            },
            {
                'site': '인크루트',
                'company_name': '테스트 회사 3',
                'title': '풀스택 개발자 채용',
                'url': 'https://www.incruit.com/job/3',
                'status': '서류합격',
                'application_date': datetime.strptime('2025-03-15', '%Y-%m-%d').date(),
                'deadline': datetime.strptime('2025-03-31', '%Y-%m-%d').date(),
                'company_id': company_objects['테스트 회사 3'].id
            }
        ]
        
        # 채용 공고 데이터 생성
        job_objects = []
        for job_data in test_jobs:
            job = Job(**job_data)
            db.session.add(job)
            db.session.flush()  # ID 할당을 위해 flush
            job_objects.append(job)
        
        # 캘린더 이벤트 데이터
        today = datetime.now()
        calendar_events = [
            {
                'title': '1차 면접',
                'description': '테스트 회사 1 백엔드 개발자 1차 면접',
                'start_time': today + timedelta(days=5, hours=14),
                'end_time': today + timedelta(days=5, hours=15),
                'all_day': False,
                'event_type': '면접',
                'color': '#ff9f89',
                'job_id': job_objects[0].id
            },
            {
                'title': '코딩 테스트',
                'description': '테스트 회사 2 프론트엔드 개발자 코딩 테스트',
                'start_time': today + timedelta(days=3),
                'all_day': True,
                'event_type': '코딩테스트',
                'color': '#8e44ad',
                'job_id': job_objects[1].id
            }
        ]
        
        # 캘린더 이벤트 생성
        for event_data in calendar_events:
            event = CalendarEvent(**event_data)
            db.session.add(event)
        
        # 면접 질문 데이터
        interview_questions = [
            {
                'job_id': job_objects[2].id,
                'question': '지원하신 직무에 가장 필요한 역량은 무엇이라고 생각하시나요?',
                'answer': '저는 풀스택 개발자로서 프론트엔드와 백엔드 모두에 대한 이해와 기술이 중요하다고 생각합니다...',
                'category': '일반',
                'difficulty': 3
            },
            {
                'job_id': job_objects[2].id,
                'question': 'REST API에 대해 설명해주세요.',
                'answer': 'REST API는 Representational State Transfer의 약자로, 웹 서비스에서 자원을 정의하고 자원에 대한 주소를 지정하는 방법입니다...',
                'category': '기술',
                'difficulty': 4
            },
            {
                'job_id': job_objects[1].id,
                'question': '팀 프로젝트에서 갈등이 발생했을 때 어떻게 해결하셨나요?',
                'answer': '팀 프로젝트에서 디자인 방향에 대한 의견 차이가 있었을 때, 저는 모두의 의견을 들어보고 각 방안의 장단점을 분석해서...',
                'category': '인성',
                'difficulty': 2
            }
        ]
        
        # 면접 질문 생성
        for question_data in interview_questions:
            question = InterviewPrep(**question_data)
            db.session.add(question)
        
        db.session.commit()
        print("테스트 데이터가 추가되었습니다.")

# 앱 종료 시 MCP 리소스 정리
@app.teardown_appcontext
def teardown_mcp(exception):
    if mcp_enabled:
        shutdown()

# app.py 실행 부분 수정 (마이그레이션 실행)
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        migrate_db()  # 마이그레이션 함수 호출
        add_test_data()  # 테스트 데이터 추가
    app.run(host='0.0.0.0', port=5000, debug=True)
