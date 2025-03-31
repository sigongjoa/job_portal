// 메인 JavaScript 파일
document.addEventListener('DOMContentLoaded', function() {
    // 요소 참조
    const crawlForm = document.getElementById('crawlForm');
    const crawlBtn = document.getElementById('crawlBtn');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const jobsTableBody = document.getElementById('jobsTableBody');
    const refreshBtn = document.getElementById('refreshBtn');

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

    // 지원 상태 토글 처리
    document.querySelectorAll('.toggle-applied').forEach(function(toggle) {
        toggle.addEventListener('change', function() {
            const jobId = this.closest('tr').dataset.jobId;
            const label = this.nextElementSibling;
            const isApplied = this.checked;
            
            // 라벨 텍스트 업데이트
            label.textContent = isApplied ? '지원' : '미지원';
            
            // 서버에 상태 업데이트 요청
            fetch(`/toggle_applied/${jobId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            })
            .then(response => response.json())
            .then(data => {
                if (!data.success) {
                    // 실패 시 상태 되돌리기
                    this.checked = !isApplied;
                    label.textContent = !isApplied ? '지원' : '미지원';
                    alert('상태 업데이트에 실패했습니다.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                // 오류 시 상태 되돌리기
                this.checked = !isApplied;
                label.textContent = !isApplied ? '지원' : '미지원';
                alert('상태 업데이트 중 오류가 발생했습니다.');
            });
        });
    });

    // 채용 정보 삭제 처리
    document.querySelectorAll('.delete-job').forEach(function(button) {
        button.addEventListener('click', function() {
            if (confirm('이 채용 정보를 삭제하시겠습니까?')) {
                const row = this.closest('tr');
                const jobId = row.dataset.jobId;
                
                // 서버에 삭제 요청
                fetch(`/delete_job/${jobId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // 성공 시 행 제거
                        row.remove();
                        
                        // 테이블이 비었는지 확인
                        if (jobsTableBody.children.length === 0) {
                            const emptyRow = document.createElement('tr');
                            emptyRow.innerHTML = '<td colspan="5" class="text-center">채용 정보가 없습니다. 구직 사이트 URL을 입력하여 크롤링을 시작하세요.</td>';
                            jobsTableBody.appendChild(emptyRow);
                        }
                    } else {
                        alert('삭제에 실패했습니다.');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('삭제 중 오류가 발생했습니다.');
                });
            }
        });
    });

    // 테이블 행 호버 효과
    document.querySelectorAll('#jobsTableBody tr').forEach(function(row) {
        row.addEventListener('mouseenter', function() {
            this.classList.add('table-active');
        });
        
        row.addEventListener('mouseleave', function() {
            this.classList.remove('table-active');
        });
    });
});
