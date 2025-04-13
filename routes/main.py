import os
import json
import zipfile
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, send_file, current_app
from models import db, Job

main = Blueprint('main', __name__)

@main.route('/')
def index():
    """홈페이지"""
    jobs = Job.query.order_by(Job.created_at.desc()).all()
    return render_template('index.html', jobs=jobs, mcp_enabled=current_app.config.get('MCP_ENABLED', False))

@main.route('/backup', methods=['POST'])
def backup():
    """데이터 백업 API"""
    try:
        # 모든 채용 정보 가져오기
        jobs = Job.query.all()
        jobs_data = [job.to_dict() for job in jobs]
        
        # 백업 파일 생성
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"job_portal_backup_{timestamp}.json"
        backup_path = os.path.join(current_app.config['UPLOAD_FOLDER'], backup_filename)
        
        # JSON 파일로 저장
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(jobs_data, f, ensure_ascii=False, indent=2)
        
        # 파일 다운로드
        return send_file(backup_path, as_attachment=True, download_name=backup_filename)
    
    except Exception as e:
        return jsonify({"error": f"백업 중 오류 발생: {str(e)}"}), 500

@main.route('/restore', methods=['POST'])
def restore():
    """데이터 복원 API"""
    try:
        if 'backup_file' not in request.files:
            return jsonify({"error": "백업 파일이 필요합니다."}), 400
        
        backup_file = request.files['backup_file']
        
        if backup_file.filename == '':
            return jsonify({"error": "선택된 파일이 없습니다."}), 400
        
        if not backup_file.filename.endswith('.json'):
            return jsonify({"error": "JSON 파일만 업로드 가능합니다."}), 400
        
        # 백업 파일 통해 직접 데이터 가져오기
        try:
            backup_data = backup_file.read().decode('utf-8')
            jobs_data = json.loads(backup_data)
        except json.JSONDecodeError as e:
            return jsonify({"error": f"유효하지 않은 JSON 형식입니다. 오류: {str(e)}"}), 400
        except UnicodeDecodeError as e:
            return jsonify({"error": f"파일 인코딩 오류: {str(e)}"}), 400
            
        # 데이터 복원 전 확인
        if not isinstance(jobs_data, list):
            return jsonify({"error": "유효하지 않은 백업 파일 형식입니다. JSON 배열이 필요합니다."}), 400
        
        # 추가된 데이터 개수 카운트
        added_count = 0
        
        # 백업 데이터 복원
        for job_data in jobs_data:
            # 필수 필드 확인
            if not all(key in job_data for key in ['company_name', 'title', 'url']):
                continue
            
            # 이미 존재하는 URL인지 확인
            existing_job = Job.query.filter_by(url=job_data.get('url', '')).first()
            if not existing_job:
                # 날짜 형식 변환
                deadline = None
                if job_data.get('deadline'):
                    try:
                        deadline = datetime.strptime(job_data['deadline'], '%Y-%m-%d').date()
                    except ValueError:
                        pass
                
                application_date = None
                if job_data.get('application_date'):
                    try:
                        application_date = datetime.strptime(job_data['application_date'], '%Y-%m-%d').date()
                    except ValueError:
                        pass
                
                job = Job(
                    site=job_data.get('site', '알 수 없음'),
                    company_name=job_data.get('company_name', '알 수 없음'),
                    title=job_data.get('title', '알 수 없음'),
                    url=job_data.get('url', ''),
                    status=job_data.get('status', '미지원'),
                    note=job_data.get('note', ''),
                    deadline=deadline,
                    resume=job_data.get('resume', ''),
                    resume_file=job_data.get('resume_file', ''),
                    portfolio_file=job_data.get('portfolio_file', ''),
                    application_date=application_date,
                    company_id=job_data.get('company_id')
                )
                db.session.add(job)
                added_count += 1
        
        db.session.commit()
        return jsonify({
            "success": True,
            "message": f"{added_count}개의 채용 정보가 성공적으로 비업로드되었습니다."
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()  # 상세한 오류 정보 서버 콘솔에 출력
        return jsonify({"error": f"복원 중 오류 발생: {str(e)}"}), 500

@main.route('/download_project', methods=['GET'])
def download_project():
    """프로젝트 전체를 ZIP 파일로 다운로드"""
    try:
        # 현재 디렉토리 (프로젝트 루트)
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # ZIP 파일 생성
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f"job_portal_project_{timestamp}.zip"
        zip_path = os.path.join(current_app.config['UPLOAD_FOLDER'], zip_filename)
        
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
