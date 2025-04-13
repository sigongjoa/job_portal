from flask import Blueprint, render_template, request, jsonify, redirect, url_for, current_app
from models import db, Company, Job

companies = Blueprint('companies', __name__)

@companies.route('/companies')
def companies_list():
    """회사 목록 페이지"""
    companies = Company.query.order_by(Company.name).all()
    return render_template('companies.html', companies=companies, mcp_enabled=current_app.config.get('MCP_ENABLED', False))

@companies.route('/companies/<int:company_id>')
def company_detail(company_id):
    """회사 상세 정보 페이지"""
    company = Company.query.get_or_404(company_id)
    jobs = Job.query.filter_by(company_id=company_id).order_by(Job.created_at.desc()).all()
    return render_template('company_detail.html', company=company, jobs=jobs, mcp_enabled=current_app.config.get('MCP_ENABLED', False))

@companies.route('/companies/create', methods=['POST'])
def create_company():
    """회사 정보 생성 API"""
    try:
        # 폼 데이터 가져오기
        name = request.form.get('name')
        industry = request.form.get('industry')
        location = request.form.get('location')
        website = request.form.get('website')
        description = request.form.get('description')
        
        if not name:
            return jsonify({"error": "회사명은 필수 입력 항목입니다."}), 400
        
        # 이미 존재하는 회사인지 확인
        existing_company = Company.query.filter_by(name=name).first()
        if existing_company:
            return jsonify({"error": "이미 등록된 회사입니다."}), 400
        
        # 회사 정보 생성
        company = Company(
            name=name,
            industry=industry,
            location=location,
            website=website,
            description=description
        )
        
        db.session.add(company)
        db.session.commit()
        
        # 성공시 리다이렉트
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"success": True, "company": company.to_dict()})
        else:
            return redirect(url_for('companies.companies_list'))
    
    except Exception as e:
        return jsonify({"error": f"회사 생성 중 오류 발생: {str(e)}"}), 500

@companies.route('/companies/update/<int:company_id>', methods=['POST'])
def update_company(company_id):
    """회사 정보 업데이트 API"""
    try:
        company = Company.query.get_or_404(company_id)
        
        # 폼 데이터 가져오기
        name = request.form.get('name')
        industry = request.form.get('industry')
        location = request.form.get('location')
        website = request.form.get('website')
        description = request.form.get('description')
        
        if not name:
            return jsonify({"error": "회사명은 필수 입력 항목입니다."}), 400
        
        # 다른 회사와 중복되는지 확인
        existing_company = Company.query.filter(Company.name == name, Company.id != company_id).first()
        if existing_company:
            return jsonify({"error": "이미 등록된 회사명입니다."}), 400
        
        # 회사 정보 업데이트
        company.name = name
        company.industry = industry
        company.location = location
        company.website = website
        company.description = description
        
        db.session.commit()
        
        # 성공시 리다이렉트
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"success": True, "company": company.to_dict()})
        else:
            return redirect(url_for('companies.company_detail', company_id=company_id))
    
    except Exception as e:
        return jsonify({"error": f"회사 정보 업데이트 중 오류 발생: {str(e)}"}), 500

@companies.route('/companies/delete/<int:company_id>', methods=['POST'])
def delete_company(company_id):
    """회사 정보 삭제 API"""
    try:
        company = Company.query.get_or_404(company_id)
        
        # 회사에 연결된 채용 정보 확인
        jobs = Job.query.filter_by(company_id=company_id).all()
        if jobs:
            return jsonify({"error": "회사에 연결된 채용 정보가 있어 삭제할 수 없습니다."}), 400
        
        db.session.delete(company)
        db.session.commit()
        
        return jsonify({"success": True})
    
    except Exception as e:
        return jsonify({"error": f"회사 삭제 중 오류 발생: {str(e)}"}), 500

@companies.route('/api/companies', methods=['GET'])
def get_companies():
    """모든 회사 정보 반환 API"""
    companies = Company.query.order_by(Company.name).all()
    return jsonify([company.to_dict() for company in companies])

@companies.route('/api/companies/<int:company_id>', methods=['GET'])
def get_company(company_id):
    """특정 회사 정보 반환 API"""
    company = Company.query.get_or_404(company_id)
    return jsonify(company.to_dict())
