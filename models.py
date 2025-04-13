from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# 채용 정보 모델
class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    site = db.Column(db.String(100), nullable=False)
    company_name = db.Column(db.String(200), nullable=False)
    title = db.Column(db.String(300), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    # 상태 변경: 더 자세한 지원 상태 추가
    status = db.Column(db.String(20), default='미지원')  # '미지원', '지원', '서류합격', '1차면접', '2차면접', '최종합격', '불합격', '보류' 중 하나
    note = db.Column(db.Text, nullable=True)  # 메모 저장을 위한 필드
    deadline = db.Column(db.Date, nullable=True)  # 마감일 추가
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    applied = db.Column(db.Boolean, default=False)
    
    # 지원 자료 추가
    resume = db.Column(db.Text, nullable=True)  # 자기소개서 내용
    resume_file = db.Column(db.String(500), nullable=True)  # 자기소개서 파일 경로
    portfolio_file = db.Column(db.String(500), nullable=True)  # 포트폴리오 파일 경로
    application_date = db.Column(db.Date, nullable=True)  # 지원 날짜
    
    # 회사 정보 관계
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'site': self.site,
            'company_name': self.company_name,
            'title': self.title,
            'url': self.url,
            'status': self.status,
            'note': self.note,
            'deadline': self.deadline.strftime('%Y-%m-%d') if self.deadline else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'resume': self.resume,
            'resume_file': self.resume_file,
            'portfolio_file': self.portfolio_file,
            'application_date': self.application_date.strftime('%Y-%m-%d') if self.application_date else None,
            'company_id': self.company_id
        }

# 회사 정보 모델
class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    industry = db.Column(db.String(100), nullable=True)
    location = db.Column(db.String(200), nullable=True)
    website = db.Column(db.String(500), nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    jobs = db.relationship('Job', backref='company', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'industry': self.industry,
            'location': self.location,
            'website': self.website,
            'description': self.description,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'jobs_count': len(self.jobs)
        }

# 캘린더 이벤트 모델
class CalendarEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=True)
    all_day = db.Column(db.Boolean, default=False)
    event_type = db.Column(db.String(50), default='일반')  # '일반', '면접', '마감일' 등
    color = db.Column(db.String(20), default='#3788d8')  # 이벤트 색상
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        # 앞서 날짜 정보가 유효한지 확인
        try:
            start_str = self.start_time.strftime('%Y-%m-%dT%H:%M:%S') if self.start_time else None
            end_str = self.end_time.strftime('%Y-%m-%dT%H:%M:%S') if self.end_time else None
            created_str = self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
            
            return {
                'id': self.id,
                'title': self.title,
                'description': self.description or '',
                'start': start_str,
                'end': end_str,
                'allDay': bool(self.all_day),
                'type': self.event_type or '일반',
                'color': self.color or '#3788d8',
                'job_id': self.job_id,
                'created_at': created_str
            }
        except Exception as e:
            # 오류 발생 시 기본 값으로 반환
            print(f"Error in CalendarEvent.to_dict: {e}")
            return {
                'id': self.id,
                'title': self.title or '',
                'description': '',
                'start': '2025-01-01T00:00:00',
                'end': None,
                'allDay': True,
                'type': '일반',
                'color': '#3788d8',
                'job_id': None,
                'created_at': '2025-01-01 00:00:00'
            }

# 면접 준비 모델
class InterviewPrep(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(100), default='일반')  # '일반', '기술', '인성', '경험' 등
    difficulty = db.Column(db.Integer, default=1)  # 1-5 난이도
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'job_id': self.job_id,
            'question': self.question,
            'answer': self.answer,
            'category': self.category,
            'difficulty': self.difficulty,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
