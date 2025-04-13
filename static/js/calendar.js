document.addEventListener('DOMContentLoaded', function() {
    let currentEventId = null;
    
    // 전역 변수 jobs가 정의되었는지 확인
    if (typeof jobs === 'undefined' || jobs === null) {
        console.warn('jobs 변수가 정의되지 않았습니다.');
        // 빈 배열로 초기화
        window.jobs = [];
    }
    
    // FullCalendar 초기화
    const calendarEl = document.getElementById('calendar');
    const calendar = new FullCalendar.Calendar(calendarEl, {
        locale: 'ko',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        initialView: 'dayGridMonth',
        editable: true,
        selectable: true,
        selectMirror: true,
        dayMaxEvents: true,
        weekNumbers: true,
        navLinks: true,
        businessHours: true,
        nowIndicator: true,
        
        // 날짜 선택 시 이벤트 추가 모달 열기
        select: function(info) {
            openAddEventModal(info.startStr, info.endStr, info.allDay);
        },
        
        // 이벤트 클릭 시 상세 정보 모달 열기
        eventClick: function(info) {
            openEventDetailModal(info.event);
        },
        
        // 이벤트 드래그 & 리사이즈 시 업데이트
        eventDrop: function(info) {
            updateEventDates(info.event);
        },
        eventResize: function(info) {
            updateEventDates(info.event);
        },
        
        // 이벤트 데이터 가져오기
        events: {
            url: '/calendar/calendar/events',
            method: 'GET',
            failure: function(error) {
                console.error('일정 데이터 로딩 오류:', error);
                console.warn('등록된 일정이 없거나 데이터를 불러올 수 없습니다.');
            },
            error: function(xhr, textStatus, error) {
                console.error('서버 응답 오류:', xhr, textStatus, error);
                
                // 오류 메시지 표시
                let errorMsg = '캘린더 데이터를 가져오는 데 실패했습니다.';
                
                // 응답 데이터가 있을 경우 해당 메시지 표시 시도
                try {
                    if (xhr.responseJSON && xhr.responseJSON.error) {
                        errorMsg = xhr.responseJSON.error;
                    }
                } catch (e) {}
                
                // 에러 처리 후 빈 이벤트 배열 반환
                console.warn(errorMsg);
                return { events: [] };
            }
        },

        // 이벤트가 표시될 때 호출되는 콜백
        eventDidMount: function(info) {
            // 이벤트가 제대로 표시되는지 확인
            if (info.event && !info.event.start) {
                console.warn('잘못된 이벤트 데이터 발견:', info.event);
                // 잘못된 이벤트는 삭제
                info.event.remove();
            }
        }
    });
    
    calendar.render();
    
    // 새 이벤트 추가 버튼 클릭 시
    document.getElementById('add-event-btn').addEventListener('click', function() {
        const now = new Date();
        const todayStr = now.toISOString().substring(0, 10);
        openAddEventModal(todayStr, null, true);
    });
    
    // 이벤트 저장 버튼 클릭 시
    document.getElementById('save-event-btn').addEventListener('click', function() {
        saveEvent();
    });
    
    // 이벤트 삭제 버튼 클릭 시
    document.getElementById('delete-event-btn').addEventListener('click', function() {
        if (currentEventId) {
            if (confirm('이 이벤트를 삭제하시겠습니까?')) {
                deleteEvent(currentEventId);
            }
        }
    });
    
    // 상세보기 모달에서 삭제 버튼 클릭 시
    document.getElementById('detail-delete-event-btn').addEventListener('click', function() {
        if (currentEventId) {
            if (confirm('이 이벤트를 삭제하시겠습니까?')) {
                deleteEvent(currentEventId);
                const detailModal = bootstrap.Modal.getInstance(document.getElementById('event-detail-modal'));
                detailModal.hide();
            }
        }
    });
    
    // 상세보기 모달에서 편집 버튼 클릭 시
    document.getElementById('edit-event-btn').addEventListener('click', function() {
        const detailModal = bootstrap.Modal.getInstance(document.getElementById('event-detail-modal'));
        detailModal.hide();
        
        const event = calendar.getEventById(currentEventId);
        if (event) {
            openEditEventModal(event);
        }
    });
    
    // 종일 체크박스 변경 시 시간 입력 필드 토글
    document.getElementById('event-all-day').addEventListener('change', function() {
        const timeInputs = document.querySelectorAll('.time-group');
        for (const input of timeInputs) {
            input.style.display = this.checked ? 'none' : 'block';
        }
    });
    
    // 색상 선택 시
    document.querySelectorAll('.color-option').forEach(function(option) {
        option.addEventListener('click', function() {
            document.querySelectorAll('.color-option').forEach(opt => opt.classList.remove('selected'));
            this.classList.add('selected');
            document.getElementById('event-color').value = this.dataset.color;
        });
    });
    
    // 새 이벤트 추가 모달 열기
    function openAddEventModal(startStr, endStr, allDay) {
        currentEventId = null;
        
        const modal = document.getElementById('event-modal');
        const modalTitle = document.getElementById('event-modal-title');
        const form = document.getElementById('event-form');
        
        modalTitle.textContent = '새 이벤트 추가';
        form.reset();
        
        document.getElementById('event-id').value = '';
        document.getElementById('event-start-date').value = startStr.substring(0, 10);
        
        if (endStr) {
            // 종료일이 있는 경우 (FullCalendar에서는 종료일이 익일로 설정됨)
            const endDate = new Date(endStr);
            endDate.setDate(endDate.getDate() - 1);
            document.getElementById('event-end-date').value = endDate.toISOString().substring(0, 10);
        } else {
            document.getElementById('event-end-date').value = startStr.substring(0, 10);
        }
        
        document.getElementById('event-all-day').checked = allDay;
        
        // 시간 필드 표시/숨김 처리
        const timeInputs = document.querySelectorAll('.time-group');
        for (const input of timeInputs) {
            input.style.display = allDay ? 'none' : 'block';
        }
        
        // 기본 시작/종료 시간 설정
        const now = new Date();
        const startTime = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
        const endTime = `${String(now.getHours() + 1).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
        
        document.getElementById('event-start-time').value = startTime;
        document.getElementById('event-end-time').value = endTime;
        
        // 색상 선택 초기화
        document.querySelectorAll('.color-option').forEach(opt => opt.classList.remove('selected'));
        document.querySelector('.color-option[data-color="#3788d8"]').classList.add('selected');
        document.getElementById('event-color').value = '#3788d8';
        
        // 삭제 버튼 숨김
        document.getElementById('delete-event-btn').style.display = 'none';
        
        // 모달 열기
        const eventModal = new bootstrap.Modal(modal);
        eventModal.show();
    }
    
    // 이벤트 편집 모달 열기
    function openEditEventModal(event) {
        currentEventId = event.id;
        
        const modal = document.getElementById('event-modal');
        const modalTitle = document.getElementById('event-modal-title');
        
        modalTitle.textContent = '이벤트 편집';
        
        document.getElementById('event-id').value = event.id;
        document.getElementById('event-title').value = event.title;
        document.getElementById('event-description').value = event.extendedProps.description || '';
        document.getElementById('event-type').value = event.extendedProps.type || '일반';
        document.getElementById('event-job').value = event.extendedProps.job_id || '';
        document.getElementById('event-all-day').checked = event.allDay;
        
        // 시작 날짜/시간 설정
        const startDate = new Date(event.start);
        document.getElementById('event-start-date').value = startDate.toISOString().substring(0, 10);
        
        if (!event.allDay) {
            const startHours = String(startDate.getHours()).padStart(2, '0');
            const startMinutes = String(startDate.getMinutes()).padStart(2, '0');
            document.getElementById('event-start-time').value = `${startHours}:${startMinutes}`;
        }
        
        // 종료 날짜/시간 설정
        if (event.end) {
            const endDate = new Date(event.end);
            if (event.allDay) {
                // 종일 이벤트의 경우 종료일이 익일로 설정되므로 하루 빼기
                endDate.setDate(endDate.getDate() - 1);
            }
            document.getElementById('event-end-date').value = endDate.toISOString().substring(0, 10);
            
            if (!event.allDay) {
                const endHours = String(endDate.getHours()).padStart(2, '0');
                const endMinutes = String(endDate.getMinutes()).padStart(2, '0');
                document.getElementById('event-end-time').value = `${endHours}:${endMinutes}`;
            }
        } else {
            document.getElementById('event-end-date').value = startDate.toISOString().substring(0, 10);
        }
        
        // 색상 설정
        const eventColor = event.backgroundColor || '#3788d8';
        document.querySelectorAll('.color-option').forEach(opt => {
            opt.classList.remove('selected');
            if (opt.dataset.color === eventColor) {
                opt.classList.add('selected');
            }
        });
        document.getElementById('event-color').value = eventColor;
        
        // 시간 필드 표시/숨김 처리
        const timeInputs = document.querySelectorAll('.time-group');
        for (const input of timeInputs) {
            input.style.display = event.allDay ? 'none' : 'block';
        }
        
        // 삭제 버튼 표시
        document.getElementById('delete-event-btn').style.display = 'block';
        
        // 모달 열기
        const eventModal = new bootstrap.Modal(modal);
        eventModal.show();
    }
    
    // 이벤트 상세 정보 모달 열기
    function openEventDetailModal(event) {
        currentEventId = event.id;
        
        const modal = document.getElementById('event-detail-modal');
        
        // 이벤트 정보 설정
        document.getElementById('event-detail-title').textContent = event.title;
        
        // 이벤트 유형 배지 설정
        const typeBadge = document.getElementById('event-detail-type-badge');
        typeBadge.textContent = event.extendedProps.type || '일반';
        typeBadge.style.backgroundColor = event.backgroundColor || '#3788d8';
        typeBadge.style.color = '#fff';
        
        // 날짜 정보 설정
        const dateText = document.getElementById('event-detail-date');
        const startDate = new Date(event.start);
        let dateString = '';
        
        if (event.allDay) {
            dateString = startDate.toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' });
            
            if (event.end) {
                const endDate = new Date(event.end);
                endDate.setDate(endDate.getDate() - 1);  // 종일 이벤트의 경우 종료일이 익일로 설정되므로 하루 빼기
                
                if (startDate.toDateString() !== endDate.toDateString()) {
                    dateString += ` - ${endDate.toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' })}`;
                }
            }
            dateString += ' (종일)';
        } else {
            dateString = startDate.toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' });
            dateString += ` ${startDate.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })}`;
            
            if (event.end) {
                const endDate = new Date(event.end);
                if (startDate.toDateString() === endDate.toDateString()) {
                    dateString += ` - ${endDate.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })}`;
                } else {
                    dateString += ` - ${endDate.toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' })} `;
                    dateString += endDate.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });
                }
            }
        }
        dateText.textContent = dateString;
        
        // 관련 채용 정보 설정
        const jobContainer = document.getElementById('event-detail-job-container');
        const jobLink = document.getElementById('event-detail-job-link');
        
        if (event.extendedProps.job_id) {
            const jobId = event.extendedProps.job_id;
            const job = window.jobs && window.jobs.find ? window.jobs.find(j => j.id === jobId) : null;
            
            if (job) {
                jobContainer.style.display = 'block';
                jobLink.textContent = `${job.company_name} - ${job.title}`;
                jobLink.href = `/job/${jobId}`;
            } else {
                jobContainer.style.display = 'none';
            }
        } else {
            jobContainer.style.display = 'none';
        }
        
        // 설명 설정
        const descContainer = document.getElementById('event-detail-description-container');
        const descText = document.getElementById('event-detail-description');
        
        if (event.extendedProps.description) {
            descContainer.style.display = 'block';
            descText.textContent = event.extendedProps.description;
        } else {
            descContainer.style.display = 'none';
        }
        
        // 특별한 이벤트 처리 (마감일, 지원일 등)
        const editBtn = document.getElementById('edit-event-btn');
        const deleteBtn = document.getElementById('detail-delete-event-btn');
        
        // job_deadline_*, job_application_* 형태의 ID는 자동 생성 이벤트이므로 편집/삭제 불가
        if (event.id.startsWith('job_deadline_') || event.id.startsWith('job_application_')) {
            editBtn.style.display = 'none';
            deleteBtn.style.display = 'none';
        } else {
            editBtn.style.display = 'inline-block';
            deleteBtn.style.display = 'inline-block';
        }
        
        // 모달 열기
        const detailModal = new bootstrap.Modal(modal);
        detailModal.show();
    }
    
    // 이벤트 저장
    function saveEvent() {
        const title = document.getElementById('event-title').value;
        const description = document.getElementById('event-description').value;
        const type = document.getElementById('event-type').value;
        const jobId = document.getElementById('event-job').value || null;
        const color = document.getElementById('event-color').value;
        const allDay = document.getElementById('event-all-day').checked;
        
        const startDate = document.getElementById('event-start-date').value;
        const startTime = document.getElementById('event-start-time').value || '00:00';
        const endDate = document.getElementById('event-end-date').value || startDate;
        const endTime = document.getElementById('event-end-time').value || '23:59';
        
        // 잘못된 날짜 형식 처리 방지
        let startDateTime = '';
        let endDateTime = '';
        
        try {
            if (allDay) {
                startDateTime = startDate;
                // 종일 이벤트의 경우 종료일을 익일로 설정 (FullCalendar 규칙)
                const tempEndDate = new Date(endDate);
                tempEndDate.setDate(tempEndDate.getDate() + 1);
                endDateTime = tempEndDate.toISOString().substring(0, 10);
            } else {
                startDateTime = `${startDate}T${startTime}`;
                endDateTime = `${endDate}T${endTime}`;
            }
        } catch (e) {
            console.error('날짜 변환 오류:', e);
            alert('날짜 형식이 올바르지 않습니다.');
            return;
        }
        
        // 이벤트 데이터 준비
        const eventData = {
            title,
            description,
            start: startDateTime,
            end: endDateTime,
            allDay,
            type,
            color,
            job_id: jobId
        };
        
        // 기존 이벤트 수정인 경우 ID 추가
        const eventId = document.getElementById('event-id').value;
        if (eventId) {
            // 이벤트 업데이트
            fetch(`/calendar/calendar/events/${eventId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(eventData)
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP 오류: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    alert('이벤트 업데이트 실패: ' + data.error);
                } else {
                    // 캘린더 새로고침
                    calendar.refetchEvents();
                    
                    // 모달 닫기
                    const modal = bootstrap.Modal.getInstance(document.getElementById('event-modal'));
                    modal.hide();
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('이벤트 업데이트 중 오류가 발생했습니다.');
            });
        } else {
            // 새 이벤트 생성
            fetch('/calendar/calendar/events', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(eventData)
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP 오류: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    alert('이벤트 생성 실패: ' + data.error);
                } else {
                    // 캘린더 새로고침
                    calendar.refetchEvents();
                    
                    // 모달 닫기
                    const modal = bootstrap.Modal.getInstance(document.getElementById('event-modal'));
                    modal.hide();
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('이벤트 생성 중 오류가 발생했습니다.');
            });
        }
    }
    
    // 이벤트 삭제
    function deleteEvent(eventId) {
        fetch(`/calendar/calendar/events/${eventId}`, {
        method: 'DELETE'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP 오류: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                alert('이벤트 삭제 실패: ' + data.error);
            } else {
                // 캘린더 새로고침
                calendar.refetchEvents();
                
                // 모달 닫기
                const modal = bootstrap.Modal.getInstance(document.getElementById('event-modal'));
                if (modal) {
                    modal.hide();
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('이벤트 삭제 중 오류가 발생했습니다.');
        });
    }
    
    // 이벤트 날짜 업데이트 (드래그 & 리사이즈 후)
    function updateEventDates(event) {
        // 자동 생성 이벤트는 업데이트 불가
        if (event.id.startsWith('job_deadline_') || event.id.startsWith('job_application_')) {
            calendar.refetchEvents();
            return;
        }
        
        // 이벤트 데이터 준비
        const eventData = {
            start: event.start ? event.start.toISOString() : null,
            end: event.end ? event.end.toISOString() : null,
            allDay: event.allDay
        };
        
        // 경고: 전송 전 데이터 확인
        console.log('Updating event dates:', eventData);
        
        // 이벤트 업데이트
        fetch(`/calendar/calendar/events/${event.id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(eventData)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP 오류: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                alert('이벤트 업데이트 실패: ' + data.error);
                calendar.refetchEvents();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('이벤트 업데이트 중 오류가 발생했습니다.');
            calendar.refetchEvents();
        });
    }
});
