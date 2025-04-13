from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, current_app, json
from models import db, CalendarEvent, Job

calendar = Blueprint('calendar', __name__)

@calendar.route('/calendar')
def calendar_view():
    """캘린더 페이지"""
    jobs = Job.query.order_by(Job.created_at.desc()).all()
    jobs_data = [job.to_dict() for job in jobs]
    return render_template('calendar.html', jobs=jobs_data, mcp_enabled=current_app.config.get('MCP_ENABLED', False))

@calendar.route('/calendar/events', methods=['GET'])
def get_calendar_events():
    """캘린더 이벤트 목록 API"""
    try:
        # 시작일과 종료일 파라미터
        start_str = request.args.get('start', '')
        end_str = request.args.get('end', '')
        
        # 파라미터가 없으면 현재 달 기준으로 설정
        if not start_str or not end_str:
            today = datetime.now()
            start_date = datetime(today.year, today.month, 1)
            next_month = today.month + 1 if today.month < 12 else 1
            next_year = today.year + 1 if today.month == 12 else today.year
            end_date = datetime(next_year, next_month, 1) - timedelta(days=1)
        else:
            # 날짜 파싱 시도
            try:
                # 시도 1: ISO 형식으로 변환 시도
                start_date = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                end_date = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
                
                # 타임존 정보 제거 - offset-naive로 변환
                start_date = start_date.replace(tzinfo=None)
                end_date = end_date.replace(tzinfo=None)
            except ValueError:
                try:
                    # 시도 2: 일반 형식으로 파싱 시도
                    start_date = datetime.strptime(start_str[:10], '%Y-%m-%d')
                    end_date = datetime.strptime(end_str[:10], '%Y-%m-%d')
                except ValueError as e:
                    current_app.logger.error(f"날짜 형식 오류: {e}")
                    # 기본값 설정
                    today = datetime.now()
                    start_date = datetime(today.year, today.month, 1)
                    next_month = today.month + 1 if today.month < 12 else 1
                    next_year = today.year + 1 if today.month == 12 else today.year
                    end_date = datetime(next_year, next_month, 1) - timedelta(days=1)
        
        # 이벤트 조회
        try:
            events = CalendarEvent.query.filter(
                ((CalendarEvent.start_time >= start_date) & (CalendarEvent.start_time <= end_date)) |
                ((CalendarEvent.end_time >= start_date) & (CalendarEvent.end_time <= end_date)) |
                ((CalendarEvent.start_time <= start_date) & (CalendarEvent.end_time >= end_date))
            ).all()
            
            # 유효한 이벤트만 보관
            events_data = []
            for event in events:
                try:
                    event_dict = event.to_dict()
                    if event_dict:
                        events_data.append(event_dict)
                except Exception as e:
                    current_app.logger.error(f"이벤트 변환 오류 (ID: {event.id}): {str(e)}")
        except Exception as e:
            current_app.logger.error(f"이벤트 조회 오류: {str(e)}")
            events_data = []
        
        # 채용 마감일 이벤트 추가
        deadline_events = []
        jobs_with_deadline = Job.query.filter(Job.deadline.isnot(None)).all()
        for job in jobs_with_deadline:
            # datetime과 date 형식 비교를 위해 date를 datetime으로 변환
            job_deadline = datetime.combine(job.deadline, datetime.min.time())
            if start_date <= job_deadline <= end_date:
                deadline_events.append({
                    'id': f'job_deadline_{job.id}',
                    'title': f'[마감] {job.company_name}: {job.title}',
                    'start': job.deadline.strftime('%Y-%m-%d'),
                    'allDay': True,
                    'color': '#ff5555',
                    'type': '마감일',
                    'job_id': job.id
                })
        
        # 지원일 이벤트 추가
        application_events = []
        jobs_with_application = Job.query.filter(Job.application_date.isnot(None)).all()
        for job in jobs_with_application:
            # datetime과 date 형식 비교를 위해 date를 datetime으로 변환
            job_application_date = datetime.combine(job.application_date, datetime.min.time())
            if start_date <= job_application_date <= end_date:
                application_events.append({
                    'id': f'job_application_{job.id}',
                    'title': f'[지원] {job.company_name}: {job.title}',
                    'start': job.application_date.strftime('%Y-%m-%d'),
                    'allDay': True,
                    'color': '#55aa55',
                    'type': '지원일',
                    'job_id': job.id
                })
        
        # 중요: 유효한 값만 전송
        try:
            return jsonify([
                *events_data,
                *deadline_events,
                *application_events
            ])
        except Exception as e:
            current_app.logger.error(f"JSON 직렬화 오류: {str(e)}")
            # 대체 응답 전송
            return jsonify({"error": "데이터 변환 오류가 발생했습니다."}), 500
    except Exception as e:
        current_app.logger.error(f"캘린더 이벤트 조회 중 오류: {str(e)}")
        return jsonify({"error": f"이벤트 조회 중 오류가 발생했습니다: {str(e)}"}), 500

@calendar.route('/calendar/events', methods=['POST'])
def create_calendar_event():
    """캘린더 이벤트 생성 API"""
    try:
        data = request.json
        
        # 필수 필드 확인
        if not data.get('title') or not data.get('start'):
            return jsonify({"error": "제목과 시작 시간은 필수 입력 항목입니다."}), 400
        
        # 시간 형식 변환
        try:
            start_time = datetime.fromisoformat(data['start'].replace('Z', '+00:00'))
            # 타임존 정보 제거
            start_time = start_time.replace(tzinfo=None)
            
            end_time = None
            if data.get('end'):
                end_time = datetime.fromisoformat(data['end'].replace('Z', '+00:00'))
                # 타임존 정보 제거
                end_time = end_time.replace(tzinfo=None)
        except ValueError as e:
            current_app.logger.error(f"날짜 형식 변환 오류: {e}")
            return jsonify({"error": f"날짜 형식이 잘못되었습니다: {str(e)}"}), 400
            
        # 이벤트 생성
        event = CalendarEvent(
            title=data['title'],
            description=data.get('description', ''),
            start_time=start_time,
            end_time=end_time,
            all_day=data.get('allDay', False),
            event_type=data.get('type', '일반'),
            color=data.get('color', '#3788d8'),
            job_id=data.get('job_id')
        )
        
        db.session.add(event)
        db.session.commit()
        
        return jsonify(event.to_dict())
    except Exception as e:
        current_app.logger.error(f"이벤트 생성 오류: {str(e)}")
        db.session.rollback()
        return jsonify({"error": f"이벤트 생성 중 오류 발생: {str(e)}"}), 500

@calendar.route('/calendar/events/<int:event_id>', methods=['PUT'])
def update_calendar_event(event_id):
    """캘린더 이벤트 업데이트 API"""
    try:
        event = CalendarEvent.query.get_or_404(event_id)
        data = request.json
        
        if not data:
            return jsonify({"error": "업데이트할 데이터가 없습니다."}), 400
        
        # 필드 업데이트
        if 'title' in data:
            event.title = data['title']
        if 'description' in data:
            event.description = data['description']
        if 'start' in data:
            try:
                start_time = datetime.fromisoformat(data['start'].replace('Z', '+00:00'))
                # 타임존 정보 제거
                event.start_time = start_time.replace(tzinfo=None)
            except ValueError as e:
                current_app.logger.error(f"시작 날짜 형식 오류: {e}")
                return jsonify({"error": f"시작 날짜 형식이 잘못되었습니다: {data['start']}"}), 400
        if 'end' in data:
            if data['end']:
                try:
                    end_time = datetime.fromisoformat(data['end'].replace('Z', '+00:00'))
                    # 타임존 정보 제거
                    event.end_time = end_time.replace(tzinfo=None)
                except ValueError as e:
                    current_app.logger.error(f"종료 날짜 형식 오류: {e}")
                    return jsonify({"error": f"종료 날짜 형식이 잘못되었습니다: {data['end']}"}), 400
            else:
                event.end_time = None
        if 'allDay' in data:
            event.all_day = data['allDay']
        if 'type' in data:
            event.event_type = data['type']
        if 'color' in data:
            event.color = data['color']
        if 'job_id' in data:
            event.job_id = data['job_id']
        
        db.session.commit()
        
        return jsonify(event.to_dict())
    except Exception as e:
        current_app.logger.error(f"이벤트 업데이트 오류: {str(e)}")
        db.session.rollback()  # 트랜잭션 롤백
        return jsonify({"error": f"이벤트 업데이트 중 오류가 발생했습니다: {str(e)}"}), 500

@calendar.route('/calendar/events/<int:event_id>', methods=['DELETE'])
def delete_calendar_event(event_id):
    """캘린더 이벤트 삭제 API"""
    try:
        event = CalendarEvent.query.get_or_404(event_id)
        db.session.delete(event)
        db.session.commit()
        
        return jsonify({"success": True})
    except Exception as e:
        current_app.logger.error(f"이벤트 삭제 중 오류: {str(e)}")
        db.session.rollback()  # 트랜잭션 롤백
        return jsonify({"error": f"이벤트 삭제 중 오류가 발생했습니다: {str(e)}"}), 500
