// 메인 스크립트 파일
document.addEventListener('DOMContentLoaded', function() {
    // 에러 발생 시 공통 핸들러 함수
    function handleApiError(error, customMessage) {
        console.error('Error:', error);
        alert(customMessage || '서버와 통신 중 오류가 발생했습니다.');
    }
    
    // 지정된 URL에 AJAX 요청을 보내는 함수
    function fetchWithErrorHandling(url, options, successCallback, errorCallback) {
        fetch(url, options)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Server responded with status: ' + response.status);
                }
                return response.json();
            })
            .then(data => {
                if (successCallback) successCallback(data);
            })
            .catch(error => {
                if (errorCallback) {
                    errorCallback(error);
                } else {
                    handleApiError(error);
                }
            });
    }
    // 새로고침 버튼
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            fetch('/jobs/jobs')
                .then(response => response.json())
                .then(jobs => {
                    updateJobsTable(jobs);
                })
                .catch(error => {
                    handleApiError(error, '채용 정보를 불러오는 중 오류가 발생했습니다.');
                });
        });
    }
    
    // 크롤링 폼 제출
    const crawlForm = document.getElementById('crawlForm');
    if (crawlForm) {
        crawlForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const url = document.getElementById('url').value;
            if (!url) {
                alert('URL을 입력해주세요.');
                return;
            }
            
            // 로딩 표시
            const crawlBtn = document.getElementById('crawlBtn');
            const loadingIndicator = document.getElementById('loadingIndicator');
            
            crawlBtn.classList.add('d-none');
            loadingIndicator.classList.remove('d-none');
            
            // API 호출
            fetch('/jobs/crawl', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    url: url
                })
            })
            .then(response => response.json())
            .then(data => {
                // 로딩 숨기기
                crawlBtn.classList.remove('d-none');
                loadingIndicator.classList.add('d-none');
                
                if (data.success) {
                    alert('채용 정보를 성공적으로 가져왔습니다.');
                    location.reload();
                } else {
                    alert('오류: ' + (data.error || '크롤링에 실패했습니다.'));
                }
            })
            .catch(error => {
                handleApiError(error, '크롤링 중 오류가 발생했습니다.');
                crawlBtn.classList.remove('d-none');
                loadingIndicator.classList.add('d-none');
            });
        });
    }
    
    // 채용 정보 상태 변경
    const jobStatusSelects = document.querySelectorAll('.job-status-select');
    jobStatusSelects.forEach(select => {
        select.addEventListener('change', function() {
            const jobId = this.getAttribute('data-job-id');
            const status = this.value;
            const currentSelect = this;
            
            fetchWithErrorHandling(
                `/jobs/update_job_status/${jobId}`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        status: status
                    })
                },
                function(data) {
                    if (data.success) {
                        const noteBtn = document.querySelector(`.note-btn[data-job-id="${jobId}"]`);
                        
                        // 메모 버튼 표시 여부 업데이트
                        if (status === '보류' && noteBtn) {
                            noteBtn.style.display = 'inline-block';
                            
                            // 메모 모달 표시
                            const noteModal = new bootstrap.Modal(document.getElementById('noteModal'));
                            document.getElementById('noteJobId').value = jobId;
                            noteModal.show();
                        } else if (data.note && noteBtn) {
                            noteBtn.style.display = 'inline-block';
                        }
                    } else {
                        alert('상태 업데이트에 실패했습니다.');
                        // 상태 선택 원래대로 되돌리기
                        currentSelect.value = data.status || '미지원';
                    }
                },
                function(error) {
                    handleApiError(error, '상태 업데이트 중 오류가 발생했습니다.');
                    // 오류 발생 시 상태 선택 원래대로 되돌리기
                    currentSelect.value = '미지원'; // 기본값으로 설정
                }
            );
        });
    });
    
    // 메모 버튼 클릭
    const noteBtns = document.querySelectorAll('.note-btn');
    noteBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const jobId = this.getAttribute('data-job-id');
            
            // 현재 메모 가져오기
            fetchWithErrorHandling(
                `/jobs/get_job_note/${jobId}`,
                { method: 'GET' },
                function(data) {
                    if (data.success) {
                        const noteModal = new bootstrap.Modal(document.getElementById('noteModal'));
                        document.getElementById('noteJobId').value = jobId;
                        document.getElementById('noteText').value = data.note || '';
                        noteModal.show();
                    } else {
                        alert('메모를 불러오는 중 오류가 발생했습니다.');
                    }
                },
                function(error) {
                    handleApiError(error, '메모를 불러오는 중 오류가 발생했습니다.');
                }
            );
        });
    });
    
    // 메모 저장 버튼
    const saveNoteBtn = document.getElementById('saveNoteBtn');
    if (saveNoteBtn) {
        saveNoteBtn.addEventListener('click', function() {
            const jobId = document.getElementById('noteJobId').value;
            const note = document.getElementById('noteText').value;
            
            fetchWithErrorHandling(
                `/jobs/update_job_status/${jobId}`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        note: note
                    })
                },
                function(data) {
                    if (data.success) {
                        const modal = bootstrap.Modal.getInstance(document.getElementById('noteModal'));
                        modal.hide();
                    } else {
                        alert('메모 저장에 실패했습니다.');
                    }
                },
                function(error) {
                    handleApiError(error, '메모 저장 중 오류가 발생했습니다.');
                }
            );
        });
    }
    
    // 채용 정보 삭제 버튼
    const deleteJobBtns = document.querySelectorAll('.delete-job');
    deleteJobBtns.forEach(btn => {
        btn.addEventListener('click', function(event) {
            // 이벤트 버블링 방지
            event.stopPropagation();
            event.preventDefault();
            
            if (confirm('정말로 이 채용 정보를 삭제하시겠습니까?')) {
                const jobId = this.closest('tr').getAttribute('data-job-id');
                const row = this.closest('tr');
                
                fetchWithErrorHandling(
                    `/jobs/delete_job/${jobId}`,
                    {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    },
                    function(data) {
                        if (data.success) {
                            // 행 삭제
                            row.remove();
                        } else {
                            alert('삭제에 실패했습니다: ' + (data.error || ''));
                        }
                    },
                    function(error) {
                        handleApiError(error, '삭제 중 오류가 발생했습니다.');
                    }
                );
            }
        });
    });
    
    // 채용 정보 테이블 업데이트 함수
    function updateJobsTable(jobs) {
        const tableBody = document.getElementById('jobsTableBody');
        if (!tableBody) return;
        
        tableBody.innerHTML = '';
        
        if (jobs.length === 0) {
            const emptyRow = document.createElement('tr');
            emptyRow.innerHTML = '<td colspan="6" class="text-center">채용 정보가 없습니다. 구직 사이트 URL을 입력하여 크롤링을 시작하세요.</td>';
            tableBody.appendChild(emptyRow);
            return;
        }
        
        jobs.forEach(job => {
            const row = document.createElement('tr');
            row.setAttribute('data-job-id', job.id);
            
            const statusOptions = [
                { value: '미지원', text: '미지원' },
                { value: '지원', text: '지원' },
                { value: '서류합격', text: '서류합격' },
                { value: '1차면접', text: '1차면접' },
                { value: '2차면접', text: '2차면접' },
                { value: '최종합격', text: '최종합격' },
                { value: '불합격', text: '불합격' },
                { value: '보류', text: '보류' }
            ];
            
            let statusOptionsHtml = '';
            statusOptions.forEach(option => {
                statusOptionsHtml += `<option value="${option.value}" ${job.status === option.value ? 'selected' : ''}>${option.text}</option>`;
            });
            
            row.innerHTML = `
                <td>${job.site}</td>
                <td id="company_name_${job.id}">${job.company_name}</td>
                <td><a href="${job.url}" target="_blank">${job.title}</a></td>
                <td>${job.deadline || '-'}</td>
                <td>
                    <div class="d-flex align-items-center">
                        <select class="form-select form-select-sm job-status-select" data-job-id="${job.id}">
                            ${statusOptionsHtml}
                        </select>
                        <button type="button" class="btn btn-sm btn-outline-info ms-2 note-btn" data-job-id="${job.id}" ${job.note ? '' : 'style="display:none;"'}>
                            <i class="bi bi-sticky"></i>
                        </button>
                    </div>
                </td>
                <td>
                    <div class="btn-group">
                        <a href="/jobs/job/${job.id}" class="btn btn-sm btn-primary">상세</a>
                        <button class="btn btn-sm btn-warning llm-btn" data-job-id="${job.id}">
                            <i class="bi bi-robot"></i>
                        </button>
                        <button class="btn btn-sm btn-danger delete-job">삭제</button>
                    </div>
                </td>
            `;
            
            tableBody.appendChild(row);
        });
        
        // 이벤트 리스너 재등록
        const newStatusSelects = document.querySelectorAll('.job-status-select');
        newStatusSelects.forEach(select => {
            select.addEventListener('change', function() {
                const jobId = this.getAttribute('data-job-id');
                const status = this.value;
                
                fetch(`/jobs/update_job_status/${jobId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        status: status
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const noteBtn = document.querySelector(`.note-btn[data-job-id="${jobId}"]`);
                        
                        // 메모 버튼 표시 여부 업데이트
                        if (status === '보류' && noteBtn) {
                            noteBtn.style.display = 'inline-block';
                            
                            // 메모 모달 표시
                            const noteModal = new bootstrap.Modal(document.getElementById('noteModal'));
                            document.getElementById('noteJobId').value = jobId;
                            noteModal.show();
                        } else if (data.note && noteBtn) {
                            noteBtn.style.display = 'inline-block';
                        }
                    } else {
                        alert('상태 업데이트에 실패했습니다.');
                        // 상태 선택 원래대로 되돌리기
                        this.value = data.status || '미지원';
                    }
                })
                .catch(error => {
                    handleApiError(error, '상태 업데이트 중 오류가 발생했습니다.');
                });
            });
        });
        
        const newNoteBtns = document.querySelectorAll('.note-btn');
        newNoteBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const jobId = this.getAttribute('data-job-id');
                
                // 현재 메모 가져오기
                fetch(`/jobs/get_job_note/${jobId}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            const noteModal = new bootstrap.Modal(document.getElementById('noteModal'));
                            document.getElementById('noteJobId').value = jobId;
                            document.getElementById('noteText').value = data.note || '';
                            noteModal.show();
                        } else {
                            alert('메모를 불러오는 중 오류가 발생했습니다.');
                        }
                    })
                    .catch(error => {
                        handleApiError(error, '메모를 불러오는 중 오류가 발생했습니다.');
                    });
            });
        });
        
        const newDeleteBtns = document.querySelectorAll('.delete-job');
        newDeleteBtns.forEach(btn => {
            btn.addEventListener('click', function(event) {
                // 이벤트 버블링 방지
                event.stopPropagation();
                event.preventDefault();
                
                if (confirm('정말로 이 채용 정보를 삭제하시겠습니까?')) {
                    const jobId = this.closest('tr').getAttribute('data-job-id');
                    
                    fetch(`/jobs/delete_job/${jobId}`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    })
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Network response was not ok: ' + response.statusText);
                        }
                        return response.json();
                    })
                    .then(data => {
                        if (data.success) {
                            // 행 삭제
                            this.closest('tr').remove();
                        } else {
                            alert('삭제에 실패했습니다: ' + (data.error || ''));
                        }
                    })
                    .catch(error => {
                        handleApiError(error, '삭제 중 오류가 발생했습니다: ' + error.message);
                    });
                }
            });
        });
        
        // LLM 버튼 이벤트 추가 등록
        const newLlmBtns = document.querySelectorAll('.llm-btn');
        if (newLlmBtns.length > 0 && typeof attachLlmButtonEvents === 'function') {
            newLlmBtns.forEach(button => {
                attachLlmButtonEvents(button);
            });
        }
    }
});
