// main.js 파일 업데이트

document.addEventListener('DOMContentLoaded', function() {
    // 페이지 로드 시 상태 스타일 적용
    document.querySelectorAll('.job-status-select').forEach(function(select) {
        updateStatusStyles(select);
    });
    // 기존 요소 참조
    const crawlForm = document.getElementById('crawlForm');
    const crawlBtn = document.getElementById('crawlBtn');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const jobsTableBody = document.getElementById('jobsTableBody');
    const refreshBtn = document.getElementById('refreshBtn');

    // 새 요소 참조
    const noteModal = new bootstrap.Modal(document.getElementById('noteModal'));
    const noteJobId = document.getElementById('noteJobId');
    const noteText = document.getElementById('noteText');
    const saveNoteBtn = document.getElementById('saveNoteBtn');

    // 크롤링 폼 제출 처리
    if (crawlForm) {
        crawlForm.addEventListener('submit', function(e) {
            // 로딩 표시 보이기
            crawlBtn.disabled = true;
            loadingIndicator.classList.remove('d-none');
            
            // 폼 제출은 그대로 진행 (서버에서 처리)
            // 여기서는 로딩 표시만 처리
        });
    }

    // 새로고침 버튼 클릭 처리
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            location.reload();
        });
    }

    // 상태 변경 이벤트 처리
    document.querySelectorAll('.job-status-select').forEach(function(select) {
        select.addEventListener('change', function() {
            const jobId = this.dataset.jobId;
            const status = this.value;
            
            // 보류 상태를 선택한 경우 메모 모달 표시
            if (status === '보류') {
                // 현재 메모 가져오기
                fetch(`/get_job_note/${jobId}`)
                    .then(response => response.json())
                    .then(data => {
                        noteJobId.value = jobId;
                        noteText.value = data.note || '';
                        noteModal.show();
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('메모를 가져오는 중 오류가 발생했습니다.');
                    });
            } else {
                // 보류가 아닌 상태로 변경 시 바로 상태 업데이트
                updateJobStatus(jobId, status);
            }
        });
    });

    // 메모 버튼 클릭 이벤트
    document.querySelectorAll('.note-btn').forEach(function(button) {
        button.addEventListener('click', function() {
            const jobId = this.dataset.jobId;
            
            // 메모 가져오기
            fetch(`/get_job_note/${jobId}`)
                .then(response => response.json())
                .then(data => {
                    noteJobId.value = jobId;
                    noteText.value = data.note || '';
                    noteModal.show();
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('메모를 가져오는 중 오류가 발생했습니다.');
                });
        });
    });

    // 메모 저장 버튼 클릭 이벤트
    if (saveNoteBtn) {
        saveNoteBtn.addEventListener('click', function() {
            const jobId = noteJobId.value;
            const note = noteText.value;
            const status = document.querySelector(`.job-status-select[data-job-id="${jobId}"]`).value;
            
            // 상태와 메모 업데이트
            updateJobStatus(jobId, status, note);
            
            // 모달 닫기
            noteModal.hide();
        });
    }

    // 상태 및 메모 업데이트 함수
    function updateJobStatus(jobId, status, note = null) {
        const data = { status: status };
        if (note !== null) {
            data.note = note;
        }
        
        fetch(`/update_job_status/${jobId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // 메모 버튼 표시 업데이트
                const noteBtn = document.querySelector(`.note-btn[data-job-id="${jobId}"]`);
                if (noteBtn) {
                    if (data.note) {
                        noteBtn.style.display = 'block';
                    } else {
                        noteBtn.style.display = 'none';
                    }
                }
                
                // 상태 스타일 업데이트
                const statusSelect = document.querySelector(`.job-status-select[data-job-id="${jobId}"]`);
                if (statusSelect) {
                    updateStatusStyles(statusSelect);
                }
            } else {
                alert('상태 업데이트에 실패했습니다.');
                // 실패 시 상태 선택을 원래대로 되돌리기
                location.reload();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('상태 업데이트 중 오류가 발생했습니다.');
            location.reload();
        });
    }
    
    // 상태에 따른 스타일 업데이트 함수
    function updateStatusStyles(selectElement) {
        const status = selectElement.value;
        const row = selectElement.closest('tr');
        
        // 모든 상태 클래스 제거
        row.classList.remove('table-success', 'table-info', 'table-warning', 'table-danger', 'table-secondary');
        
        // 상태에 따라 적절한 클래스 추가
        if (status === '최종합격') {
            row.classList.add('table-success');
        } else if (status === '서류합격') {
            row.classList.add('table-info');
        } else if (status === '1차면접' || status === '2차면접') {
            row.classList.add('table-warning');
        } else if (status === '불합격') {
            row.classList.add('table-danger');
        } else if (status === '미지원') {
            row.classList.add('table-secondary');
        }
    }
}); 