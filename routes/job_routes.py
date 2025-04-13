import os
import time
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, send_file, current_app
from models import db, Job, Company

jobs = Blueprint('jobs', __name__)

@jobs.route('/crawl', methods=['POST'])
def crawl():
    """채용 정보 크롤링 API"""
    # 기존 크롤링 코드 유지
    return jsonify({"error": "크롤링 기능은 아직 구현되지 않았습니다."}), 501

@jobs.route('/add_job', methods=['POST'])
def add_job():
    """수동으로 채용 정보 추가 API"""
    company_name = request.form.get('company_name')
    title = request.form.get('title')
    url = request.form.get('url')
    site = request.form.get('site', '직접 입력')
    deadline_str = request.form.get('deadline')
    company_id = request.form.get('company_id', type=int)
    
    if not company_name or not title or not url:
        return jsonify({"error": "회사명, 채용공고, 링크는 필수 입력 항목입니다."}), 400
    
    # 이미 존재하는 URL인지 확인
    existing_job = Job.query.filter_by(url=url).first()
    if existing_job:
        return jsonify({"error": "이미 등록된 채용 공고입니다."}), 400
    
    # 마감일 형식 변환
    deadline = None
    if deadline_str:
        try:
            deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    # 회사 정보 확인 또는 생성
    if not company_id and company_name:
        company = Company.query.filter_by(name=company_name).first()
        if not company:
            company = Company(name=company_name)
            db.session.add(company)
            db.session.flush()  # ID 할당을 위해 flush
            company_id = company.id
    
    # 새 채용 정보 추가
    job = Job(
        site=site,
        company_name=company_name,
        title=title,
        url=url,
        deadline=deadline,
        status='미지원',
        company_id=company_id
    )
    db.session.add(job)
    db.session.commit()
    
    return redirect(url_for('main.index'))

@jobs.route('/toggle_applied/<int:job_id>', methods=['POST'])
def toggle_applied(job_id):
    """지원 상태 토글 API"""
    job = Job.query.get_or_404(job_id)
    job.applied = not job.applied
    db.session.commit()
    return jsonify({"success": True, "applied": job.applied})

@jobs.route('/delete_job/<int:job_id>', methods=['POST'])
def delete_job(job_id):
    """채용 정보 삭제 API"""
    try:
        job = Job.query.get_or_404(job_id)
        
        # 관련 파일도 삭제
        if job.resume_file and os.path.exists(job.resume_file):
            os.remove(job.resume_file)
        
        if job.portfolio_file and os.path.exists(job.portfolio_file):
            os.remove(job.portfolio_file)
        
        db.session.delete(job)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        logging.error(f"Error deleting job: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 400

@jobs.route('/job/<int:job_id>', methods=['GET'])
def job_detail(job_id):
    """채용 정보 상세 조회 페이지"""
    job = Job.query.get_or_404(job_id)
    return render_template('job_detail.html', job=job, mcp_enabled=current_app.config.get('MCP_ENABLED', False))

@jobs.route('/update_job_status/<int:job_id>', methods=['POST'])
def update_job_status(job_id):
    """채용 정보 상태 및 메모 업데이트 API"""
    try:
        # 요청 데이터가 JSON인지 확인
        if not request.is_json:
            return jsonify({"success": False, "error": "JSON 형식의 요청이 필요합니다."}), 400
            
        data = request.json
        job = Job.query.get_or_404(job_id)
        
        # 상태 업데이트
        if 'status' in data:
            job.status = data['status']
            
            # 처음 지원 상태로 변경 시 자동으로 지원 날짜 업데이트
            if data['status'] == '지원' and not job.application_date:
                job.application_date = datetime.now().date()
        
        # 메모 업데이트 (있는 경우에만)
        if 'note' in data:
            job.note = data['note']
        
        # 마감일 업데이트 (있는 경우에만)
        if 'deadline' in data:
            try:
                job.deadline = datetime.strptime(data['deadline'], '%Y-%m-%d').date()
            except ValueError:
                pass
        
        db.session.commit()
        
        # 성공 응답
        response_data = {
            "success": True, 
            "status": job.status,
            "note": job.note,
            "deadline": job.deadline.strftime('%Y-%m-%d') if job.deadline else None,
            "application_date": job.application_date.strftime('%Y-%m-%d') if job.application_date else None
        }
        
        return jsonify(response_data)
    except Exception as e:
        logging.error(f"Error updating job status: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 400

@jobs.route('/get_job_note/<int:job_id>', methods=['GET'])
def get_job_note(job_id):
    """채용 정보 메모 조회 API"""
    try:
        job = Job.query.get_or_404(job_id)
        return jsonify({
            "success": True,
            "note": job.note
        })
    except Exception as e:
        logging.error(f"Error getting job note: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 400

@jobs.route('/upload_job_materials/<int:job_id>', methods=['POST'])
def upload_job_materials(job_id):
    """채용 정보 지원 자료 업로드 API"""
    try:
        job = Job.query.get_or_404(job_id)
        
        # 자기소개서 텍스트 업데이트
        if 'resume_text' in request.form:
            job.resume = request.form.get('resume_text')
        
        # 자기소개서 파일 업로드
        if 'resume_file' in request.files and request.files['resume_file'].filename:
            resume_file = request.files['resume_file']
            filename = f"resume_{job_id}_{int(time.time())}_{resume_file.filename}"
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], 'resume', filename)
            resume_file.save(filepath)
            job.resume_file = filepath
        
        # 포트폴리오 파일 업로드
        if 'portfolio_file' in request.files and request.files['portfolio_file'].filename:
            portfolio_file = request.files['portfolio_file']
            filename = f"portfolio_{job_id}_{int(time.time())}_{portfolio_file.filename}"
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], 'portfolio', filename)
            portfolio_file.save(filepath)
            job.portfolio_file = filepath
        
        # 지원 날짜 업데이트
        if 'application_date' in request.form and request.form.get('application_date'):
            try:
                job.application_date = datetime.strptime(request.form.get('application_date'), '%Y-%m-%d').date()
            except ValueError:
                logging.warning(f"Invalid date format for application_date: {request.form.get('application_date')}")
        
        db.session.commit()
        
        return jsonify({"success": True})
    except Exception as e:
        logging.error(f"Error uploading job materials: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 400

@jobs.route('/download_file/<int:job_id>/<file_type>', methods=['GET'])
def download_file(job_id, file_type):
    """채용 정보 파일 다운로드 API"""
    try:
        job = Job.query.get_or_404(job_id)
        
        if file_type == 'resume' and job.resume_file:
            if os.path.exists(job.resume_file):
                return send_file(job.resume_file, as_attachment=True, download_name=os.path.basename(job.resume_file))
            else:
                logging.warning(f"Resume file not found: {job.resume_file}")
                return jsonify({"error": "파일을 찾을 수 없습니다."}), 404
        
        elif file_type == 'portfolio' and job.portfolio_file:
            if os.path.exists(job.portfolio_file):
                return send_file(job.portfolio_file, as_attachment=True, download_name=os.path.basename(job.portfolio_file))
            else:
                logging.warning(f"Portfolio file not found: {job.portfolio_file}")
                return jsonify({"error": "파일을 찾을 수 없습니다."}), 404
        
        else:
            return jsonify({"error": "파일이 없습니다."}), 404
    
    except Exception as e:
        logging.error(f"Error downloading file: {str(e)}")
        return jsonify({"error": str(e)}), 500

@jobs.route('/jobs', methods=['GET'])
def get_jobs():
    """모든 채용 정보 반환 API"""
    try:
        jobs = Job.query.order_by(Job.created_at.desc()).all()
        return jsonify([job.to_dict() for job in jobs])
    except Exception as e:
        logging.error(f"Error getting all jobs: {str(e)}")
        return jsonify({"error": str(e)}), 500
