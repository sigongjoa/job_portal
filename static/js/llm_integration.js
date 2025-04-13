/**
 * LLM Studio 통합 자바스크립트
 */

// LLM 버튼 이벤트 처리 함수 - 다른 파일에서 호출 가능하도록 전역화
function attachLlmButtonEvents(button) {
    button.addEventListener('click', function(event) {
        // 삭제 버튼 클릭 이벤트가 버블링되지 않도록 방지
        event.stopPropagation();
        
        const job_id = this.dataset.jobId;
        const jobRow = document.querySelector(`tr[data-job-id="${job_id}"]`);
        const company_name = document.getElementById(`company_name_${job_id}`).textContent;
        
        // 모달 표시
        const modal = new bootstrap.Modal(document.getElementById('llmModal'));
        
        // 모달 제목 설정
        document.getElementById('llmModalLabel').textContent = 
            `${company_name} - ${jobRow.querySelector('a').textContent}`;
        
        // 프롬프트 영역 초기화
        const promptArea = document.getElementById('llmPromptArea');
        if (promptArea) {
            promptArea.style.display = 'block';
            promptArea.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>';
        }
        
        // API 호출하여 AI 분석 가져오기
        fetch(`/ai/analyze_job/${job_id}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok: ' + response.statusText);
                }
                return response.json();
            })
            .then(data => {
                if (promptArea) {
                    if (data.success) {
                        promptArea.innerHTML = data.analysis || '분석 결과가 없습니다.';
                    } else {
                        promptArea.innerHTML = 
                            `<div class="alert alert-danger">${data.error || '분석 중 오류가 발생했습니다.'}</div>`;
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
                if (promptArea) {
                    promptArea.innerHTML = 
                        `<div class="alert alert-danger">서버와 통신 중 오류가 발생했습니다.<br><small>${error.message || ''}</small></div>`;
                }
            });
        
        modal.show();
    });
}

// 화면 로드 시 실행
 document.addEventListener('DOMContentLoaded', function() {
    // AI 도우미 버튼 클릭 이벤트
    const aiAssistBtn = document.getElementById('aiAssistBtn');
    if (aiAssistBtn) {
        aiAssistBtn.addEventListener('click', function() {
            // 현재 페이지에서 job_id 가져오기
            const pathParts = window.location.pathname.split('/');
            const job_id = pathParts[pathParts.length - 1]; // URL에서 마지막 부분이 job_id
            
            // AI.ai_assistant 블루프린트로 이동
            window.location.href = `/ai/assistant/${job_id}`;
        });
    }
    
    // LLM 버튼 클릭 이벤트 (채용 목록 페이지)
    const llmButtons = document.querySelectorAll('.llm-btn');
    if (llmButtons.length > 0) {
        llmButtons.forEach(button => {
            attachLlmButtonEvents(button);
        });
    }
    
    // AI 채팅 전송 버튼 클릭 이벤트
    const sendBtn = document.getElementById('llmSendBtn');
    const promptInput = document.getElementById('llmPromptInput');
    const resultArea = document.getElementById('llmResultArea');
    
    if (sendBtn && promptInput && resultArea) {
        sendBtn.addEventListener('click', function() {
            const prompt = promptInput.value.trim();
            if (!prompt) return;
            
            // 입력창 초기화
            promptInput.value = '';
            
            // 요청 중임을 표시
            resultArea.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>';
            
            // API 호출
            fetch('/ai/call_tool', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    tool_name: 'chat',
                    arguments: {
                        prompt: prompt
                    }
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    resultArea.innerHTML = `<div class="card">
                        <div class="card-header">
                            <h5>AI 응답</h5>
                        </div>
                        <div class="card-body">
                            ${data.result.replace(/\n/g, '<br>')}
                        </div>
                    </div>`;
                } else {
                    resultArea.innerHTML = `<div class="alert alert-danger">${data.error || 'API 호출 중 오류가 발생했습니다.'}</div>`;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                resultArea.innerHTML = '<div class="alert alert-danger">서버와 통신 중 오류가 발생했습니다.</div>';
            });
        });
        
        // 엔터 키로 전송
        promptInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendBtn.click();
            }
        });
    }
    
    // 자기소개서 생성 기능
    const generateResumeBtn = document.getElementById('generateResumeBtn');
    if (generateResumeBtn) {
        generateResumeBtn.addEventListener('click', function() {
            const jobId = this.dataset.jobId;
            const resultArea = document.getElementById('llmResultArea');
            
            // 요청 중임을 표시
            resultArea.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>';
            
            // API 호출
            fetch(`/ai/analyze_job/${jobId}`, {
                method: 'GET'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // 분석 결과 표시
                    resultArea.innerHTML = `<div class="card mb-3">
                        <div class="card-header">
                            <h5>채용 공고 분석</h5>
                        </div>
                        <div class="card-body">
                            ${data.analysis.replace(/\n/g, '<br>')}
                        </div>
                    </div>
                    <div class="d-grid gap-2">
                        <button id="createResumeBtn" class="btn btn-primary" data-job-id="${jobId}">자기소개서 생성하기</button>
                    </div>`;
                    
                    // 자기소개서 생성 버튼 이벤트 추가
                    document.getElementById('createResumeBtn').addEventListener('click', function() {
                        generateResume(jobId);
                    });
                } else {
                    resultArea.innerHTML = `<div class="alert alert-danger">${data.error || '분석 중 오류가 발생했습니다.'}</div>`;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                resultArea.innerHTML = '<div class="alert alert-danger">서버와 통신 중 오류가 발생했습니다.</div>';
            });
        });
    }
    
    // 자기소개서 생성 함수
    function generateResume(jobId) {
        const resultArea = document.getElementById('llmResultArea');
        
        // 생성 중임을 표시
        resultArea.innerHTML += '<div id="resumeLoading" class="my-3"><div class="spinner-border text-primary" role="status"></div> <span>자기소개서 생성 중...</span></div>';
        
        // API 호출
        fetch('/ai/call_tool', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                tool_name: 'generate_resume',
                arguments: {
                    job_id: jobId
                }
            })
        })
        .then(response => response.json())
        .then(data => {
            // 로딩 표시 제거
            document.getElementById('resumeLoading').remove();
            
            if (data.success) {
                resultArea.innerHTML += `<div class="card mt-3">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5>생성된 자기소개서</h5>
                        <button id="saveResumeBtn" class="btn btn-sm btn-success" data-job-id="${jobId}">저장하기</button>
                    </div>
                    <div class="card-body">
                        <div id="generatedResume">${data.result.replace(/\n/g, '<br>')}</div>
                    </div>
                </div>`;
                
                // 저장 버튼 이벤트 추가
                document.getElementById('saveResumeBtn').addEventListener('click', function() {
                    saveGeneratedResume(jobId, data.result);
                });
            } else {
                resultArea.innerHTML += `<div class="alert alert-danger mt-3">${data.error || '생성 중 오류가 발생했습니다.'}</div>`;
            }
        })
        .catch(error => {
            // 로딩 표시 제거
            if (document.getElementById('resumeLoading')) {
                document.getElementById('resumeLoading').remove();
            }
            
            console.error('Error:', error);
            resultArea.innerHTML += '<div class="alert alert-danger mt-3">서버와 통신 중 오류가 발생했습니다.</div>';
        });
    }
    
    // 생성된 자기소개서 저장 함수
    function saveGeneratedResume(jobId, resumeText) {
        fetch(`/ai/save_to_resume/${jobId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                resume_text: resumeText
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('자기소개서가 저장되었습니다.');
                
                // 페이지 새로고침 또는 리다이렉트
                window.location.href = `/job/${jobId}`;
            } else {
                alert('저장 실패: ' + (data.error || '알 수 없는 오류'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('저장 중 오류가 발생했습니다.');
        });
    }
});
