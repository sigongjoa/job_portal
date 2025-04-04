import os
import sys
import json
import zipfile
from datetime import datetime

# 크롤러 모듈 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), 'crawlers'))

from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file, flash
from flask_sqlalchemy import SQLAlchemy
import time
from datetime import datetime

# 애플리케이션 초기화
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///job_portal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = 'job_portal_secret_key'
db = SQLAlchemy(app)

# 업로드 폴더 생성
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 모델 정의
class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    site = db.Column(db.String(100), nullable=False)
    company_name = db.Column(db.String(200), nullable=False)
    title = db.Column(db.String(300), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    # applied 필드를 status 필드로 대체
    status = db.Column(db.String(20), default='미지원')  # '미지원', '지원', '보류' 중 하나
    note = db.Column(db.Text, nullable=True)  # 메모 저장을 위한 필드
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    applied = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'site': self.site,
            'company_name': self.company_name,
            'title': self.title,
            'url': self.url,
            'status': self.status,
            'note': self.note,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }


def migrate_db():
    """기존 데이터를 새 스키마로 마이그레이션"""
    with app.app_context():
        # 새 컬럼이 있는지 확인
        inspector = db.inspect(db.engine)
        has_status = 'status' in [col['name'] for col in inspector.get_columns('job')]
        has_note = 'note' in [col['name'] for col in inspector.get_columns('job')]
        
        # 새 컬럼이 없으면 추가
        if not has_status or not has_note:
            # 임시 테이블에 기존 데이터 저장
            jobs_data = []
            for job in Job.query.all():
                jobs_data.append({
                    'id': job.id,
                    'site': job.site,
                    'company_name': job.company_name,
                    'title': job.title,
                    'url': job.url,
                    'applied': job.applied,
                    'created_at': job.created_at
                })
            
            # 테이블 스키마 업데이트
            db.drop_all()
            db.create_all()
            
            # 데이터 복원 및 status 필드 설정
            for data in jobs_data:
                status = '지원' if data.pop('applied', False) else '미지원'
                new_job = Job(
                    id=data['id'],
                    site=data['site'],
                    company_name=data['company_name'],
                    title=data['title'],
                    url=data['url'],
                    status=status,
                    created_at=data['created_at']
                )
                db.session.add(new_job)
            
            db.session.commit()
            print("데이터베이스 마이그레이션이 완료되었습니다.")

# 크롤러 통합
def get_crawler(url):
    """URL을 기반으로 적절한 크롤러 반환"""
    if 'saramin.co.kr' in url:
        try:
            from final_saramin_crawler import FinalSaraminCrawler
            return FinalSaraminCrawler()
        except ImportError:
            try:
                from saramin_crawler import SaraminCrawler
                return SaraminCrawler()
            except ImportError:
                return None
    elif 'jobplanet.co.kr' in url:
        try:
            from jobplanet_crawler import JobPlanetCrawler
            return JobPlanetCrawler()
        except ImportError:
            return None
    elif 'incruit.com' in url:
        try:
            from incruit_crawler import IncruitCrawler
            return IncruitCrawler()
        except ImportError:
            return None
    elif 'jobkorea.co.kr' in url:
        try:
            from jobkorea_crawler import JobKoreaCrawler
            return JobKoreaCrawler()
        except ImportError:
            return None
    else:
        # 통합 크롤러 시도
        try:
            from job_korea_crawler import IntegratedCrawler
            return IntegratedCrawler()
        except ImportError:
            return None

def crawl_jobs(url):
    """URL에서 채용 정보 크롤링"""
    crawler = get_crawler(url)
    if not crawler:
        return {"error": "지원하지 않는 사이트이거나 크롤러를 찾을 수 없습니다."}
    
    try:
        # 크롤러 실행
        results = crawler.crawl(url)
        return {"success": True, "data": results}
    except Exception as e:
        return {"error": f"크롤링 중 오류 발생: {str(e)}"}

# 라우트 정의
@app.route('/')
def index():
    """홈페이지"""
    jobs = Job.query.order_by(Job.created_at.desc()).all()
    return render_template('index.html', jobs=jobs)

@app.route('/crawl', methods=['POST'])
def crawl():
    """채용 정보 크롤링 API"""
    url = request.form.get('url')
    if not url:
        return jsonify({"error": "URL이 필요합니다."}), 400
    
    result = crawl_jobs(url)
    
    if "error" in result:
        return jsonify(result), 400
    
    # 크롤링 결과 저장
    for job_data in result["data"]:
        # 이미 존재하는 URL인지 확인
        existing_job = Job.query.filter_by(url=job_data.get('url', '')).first()
        if not existing_job:
            job = Job(
                site=job_data.get('site', '알 수 없음'),
                company_name=job_data.get('company_name', '알 수 없음'),
                title=job_data.get('title', '알 수 없음'),
                url=job_data.get('url', ''),
                applied=False
            )
            db.session.add(job)
    
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/add_job', methods=['POST'])
def add_job():
    """수동으로 채용 정보 추가 API"""
    company_name = request.form.get('company_name')
    title = request.form.get('title')
    url = request.form.get('url')
    site = request.form.get('site', '직접 입력')
    
    if not company_name or not title or not url:
        return jsonify({"error": "회사명, 채용공고, 링크는 필수 입력 항목입니다."}), 400
    
    # 이미 존재하는 URL인지 확인
    existing_job = Job.query.filter_by(url=url).first()
    if existing_job:
        return jsonify({"error": "이미 등록된 채용 공고입니다."}), 400
    
    # 새 채용 정보 추가
    job = Job(
        site=site,
        company_name=company_name,
        title=title,
        url=url,
        applied=False
    )
    db.session.add(job)
    db.session.commit()
    
    return redirect(url_for('index'))

@app.route('/backup', methods=['POST'])
def backup():
    """데이터 백업 API"""
    try:
        # 모든 채용 정보 가져오기
        jobs = Job.query.all()
        jobs_data = [job.to_dict() for job in jobs]
        
        # 백업 파일 생성
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"job_portal_backup_{timestamp}.json"
        backup_path = os.path.join(app.config['UPLOAD_FOLDER'], backup_filename)
        
        # JSON 파일로 저장
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(jobs_data, f, ensure_ascii=False, indent=2)
        
        # 파일 다운로드
        return send_file(backup_path, as_attachment=True, download_name=backup_filename)
    
    except Exception as e:
        return jsonify({"error": f"백업 중 오류 발생: {str(e)}"}), 500

@app.route('/restore', methods=['POST'])
def restore():
    """데이터 복원 API"""
    if 'backup_file' not in request.files:
        return jsonify({"error": "백업 파일이 필요합니다."}), 400
    
    backup_file = request.files['backup_file']
    
    if backup_file.filename == '':
        return jsonify({"error": "선택된 파일이 없습니다."}), 400
    
    if not backup_file.filename.endswith('.json'):
        return jsonify({"error": "JSON 파일만 업로드 가능합니다."}), 400
    
    try:
        # 백업 파일 저장
        backup_path = os.path.join(app.config['UPLOAD_FOLDER'], backup_file.filename)
        backup_file.save(backup_path)
        
        # 백업 파일 읽기
        with open(backup_path, 'r', encoding='utf-8') as f:
            jobs_data = json.load(f)
        
        # 데이터 복원 전 확인
        if not isinstance(jobs_data, list):
            return jsonify({"error": "유효하지 않은 백업 파일입니다."}), 400
        
        # 기존 데이터 삭제 (선택적)
        # Job.query.delete()
        
        # 백업 데이터 복원
        for job_data in jobs_data:
            # 필수 필드 확인
            if not all(key in job_data for key in ['company_name', 'title', 'url']):
                continue
            
            # 이미 존재하는 URL인지 확인
            existing_job = Job.query.filter_by(url=job_data.get('url', '')).first()
            if not existing_job:
                job = Job(
                    site=job_data.get('site', '알 수 없음'),
                    company_name=job_data.get('company_name', '알 수 없음'),
                    title=job_data.get('title', '알 수 없음'),
                    url=job_data.get('url', ''),
                    applied=job_data.get('applied', False)
                )
                db.session.add(job)
        
        db.session.commit()
        return redirect(url_for('index'))
    
    except Exception as e:
        return jsonify({"error": f"복원 중 오류 발생: {str(e)}"}), 500

@app.route('/download_project', methods=['GET'])
def download_project():
    """프로젝트 전체를 ZIP 파일로 다운로드"""
    try:
        # 현재 디렉토리 (프로젝트 루트)
        project_dir = os.path.dirname(os.path.abspath(__file__))
        
        # ZIP 파일 생성
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f"job_portal_project_{timestamp}.zip"
        zip_path = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)
        
        # ZIP 파일 생성
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 프로젝트 파일 추가
            for root, dirs, files in os.walk(project_dir):
                # uploads 폴더와 __pycache__ 폴더는 제외
                if '__pycache__' in root or 'uploads' in root:
                    continue
                
                for file in files:
                    # .pyc 파일과 .db 파일은 제외
                    if file.endswith('.pyc') or file.endswith('.db'):
                        continue
                    
                    file_path = os.path.join(root, file)
                    # ZIP 파일 내 경로 설정 (프로젝트 루트 기준)
                    arcname = os.path.relpath(file_path, project_dir)
                    zipf.write(file_path, arcname)
        
        # 파일 다운로드
        return send_file(zip_path, as_attachment=True, download_name=zip_filename)
    
    except Exception as e:
        return jsonify({"error": f"프로젝트 다운로드 중 오류 발생: {str(e)}"}), 500

@app.route('/toggle_applied/<int:job_id>', methods=['POST'])
def toggle_applied(job_id):
    """지원 상태 토글 API"""
    job = Job.query.get_or_404(job_id)
    job.applied = not job.applied
    db.session.commit()
    return jsonify({"success": True, "applied": job.applied})


@app.route('/delete_job/<int:job_id>', methods=['POST'])
def delete_job(job_id):
    """채용 정보 삭제 API"""
    job = Job.query.get_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    return jsonify({"success": True})

# 테스트용 더미 데이터 추가
def add_test_data():
    """테스트용 더미 데이터 추가"""
    # 기존 데이터가 없을 경우에만 추가
    if Job.query.count() == 0:
        test_jobs = [
            {
                'site': '사람인',
                'company_name': '테스트 회사 1',
                'title': '백엔드 개발자 채용',
                'url': 'https://www.saramin.co.kr/job/1',
                'applied': False
            },
            {
                'site': '잡플래닛',
                'company_name': '테스트 회사 2',
                'title': '프론트엔드 개발자 채용',
                'url': 'https://www.jobplanet.co.kr/job/2',
                'applied': True
            },
            {
                'site': '인크루트',
                'company_name': '테스트 회사 3',
                'title': '풀스택 개발자 채용',
                'url': 'https://www.incruit.com/job/3',
                'applied': False
            }
        ]
        
        for job_data in test_jobs:
            job = Job(**job_data)
            db.session.add(job)
        
        db.session.commit()
        print("테스트 데이터가 추가되었습니다.")

@app.route('/update_job_status/<int:job_id>', methods=['POST'])
def update_job_status(job_id):
    """채용 정보 상태 및 메모 업데이트 API"""
    try:
        data = request.json
        job = Job.query.get_or_404(job_id)
        
        # 상태 업데이트
        if 'status' in data:
            job.status = data['status']
        
        # 메모 업데이트 (있는 경우에만)
        if 'note' in data:
            job.note = data['note']
        
        db.session.commit()
        
        return jsonify({
            "success": True, 
            "status": job.status,
            "note": job.note
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/get_job_note/<int:job_id>', methods=['GET'])
def get_job_note(job_id):
    """채용 정보 메모 조회 API"""
    try:
        job = Job.query.get_or_404(job_id)
        return jsonify({
            "success": True,
            "note": job.note
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

# 기존 get_jobs 라우트 업데이트
@app.route('/jobs', methods=['GET'])
def get_jobs():
    """모든 채용 정보 반환 API"""
    jobs = Job.query.order_by(Job.created_at.desc()).all()
    return jsonify([job.to_dict() for job in jobs])

# app.py 실행 부분 수정 (마이그레이션 실행)
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        migrate_db()  # 마이그레이션 함수 호출
        add_test_data()  # 테스트 데이터 추가
    app.run(host='0.0.0.0', port=5000, debug=True)