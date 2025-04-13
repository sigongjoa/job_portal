/**
 * AI 면접 도우미 모듈
 */
document.addEventListener('DOMContentLoaded', function() {
    // AI 채팅 관련 기능
    initAIChat();
    initQuestionGenerator();
});

/**
 * AI 채팅 기능 초기화
 */
function initAIChat() {
    const aiChatInput = document.getElementById('ai-chat-input');
    const aiChatSend = document.getElementById('ai-chat-send');
    const aiChatMessages = document.getElementById('ai-chat-messages');
    
    if (aiChatInput && aiChatSend && aiChatMessages) {
        // 메시지 전송 버튼 클릭 시
        aiChatSend.addEventListener('click', function() {
            sendMessage();
        });
        
        // 엔터 키로 메시지 전송
        aiChatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
        
        // 메시지 전송 함수
        function sendMessage() {
            const message = aiChatInput.value.trim();
            
            if (!message) return;
            
            // 사용자 메시지 추가
            addMessage(message, 'user');
            
            // 입력창 초기화
            aiChatInput.value = '';
            
            // AI 응답 생성
            generateAIResponse(message);
        }
        
        // 메시지 추가 함수
        function addMessage(text, sender) {
            const messageElement = document.createElement('div');
            messageElement.className = `message ${sender}-message`;
            messageElement.textContent = text;
            
            aiChatMessages.appendChild(messageElement);
            
            // 스크롤 맨 아래로
            aiChatMessages.scrollTop = aiChatMessages.scrollHeight;
        }
        
        // AI 응답 생성 함수
        function generateAIResponse(userMessage) {
            // AI 로딩 메시지 추가
            const loadingMessage = document.createElement('div');
            loadingMessage.className = 'message ai-message';
            loadingMessage.innerHTML = '<i class="bi bi-hourglass-split"></i> 생각 중...';
            aiChatMessages.appendChild(loadingMessage);
            
            // AI 응답 생성 API 호출
            fetch('/ai/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: userMessage
                })
            })
            .then(response => response.json())
            .then(data => {
                // 로딩 메시지 제거
                aiChatMessages.removeChild(loadingMessage);
                
                if (data.error) {
                    addMessage('죄송합니다. 응답을 생성하는 중 오류가 발생했습니다. 다시 시도해주세요.', 'ai');
                } else {
                    // AI 응답 추가
                    addMessage(data.response, 'ai');
                }
            })
            .catch(error => {
                // 로딩 메시지 제거
                aiChatMessages.removeChild(loadingMessage);
                
                // 오류 메시지 추가
                addMessage('서버와 통신 중 오류가 발생했습니다. 다시 시도해주세요.', 'ai');
                console.error('Error:', error);
            });
        }
    }
}

/**
 * AI 면접 질문 생성 기능 초기화
 */
function initQuestionGenerator() {
    const generateQuestionsBtn = document.getElementById('generate-questions-btn');
    const saveAllQuestionsBtn = document.getElementById('save-all-questions-btn');
    
    if (generateQuestionsBtn) {
        generateQuestionsBtn.addEventListener('click', function() {
            generateInterviewQuestions();
        });
    }
    
    if (saveAllQuestionsBtn) {
        saveAllQuestionsBtn.addEventListener('click', function() {
            saveAllGeneratedQuestions();
        });
    }
    
    // AI 피드백 버튼 클릭 시 (질문 카드)
    const aiFeedbackButtons = document.querySelectorAll('.ai-feedback-btn');
    aiFeedbackButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const questionId = button.dataset.questionId;
            
            // 모의면접 탭으로 이동
            const simulatorTab = document.getElementById('simulator-tab');
            bootstrap.Tab.getInstance(simulatorTab).show();
            
            // 해당 질문 불러오기
            fetch(`/interview/questions/${questionId}`)
                .then(response => response.json())
                .then(question => {
                    // 단일 질문으로 면접 시작
                    window.interviewQuestions = [question];
                    window.currentQuestionIndex = 0;
                    
                    // 질문 표시 함수 호출 (interview-simulator.js에 정의됨)
                    if (typeof window.displayCurrentQuestion === 'function') {
                        window.displayCurrentQuestion();
                    }
                    
                    // AI 피드백 섹션으로 스크롤
                    const feedbackSection = document.getElementById('feedback-section');
                    if (feedbackSection) {
                        feedbackSection.scrollIntoView({ behavior: 'smooth' });
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('질문 정보를 가져오는 중 오류가 발생했습니다.');
                });
        });
    });
}

/**
 * AI 면접 질문 생성 함수
 */
function generateInterviewQuestions() {
    // 생성 옵션 가져오기
    const jobTitle = document.getElementById('job-title-input').value;
    const companyName = document.getElementById('company-name-input').value;
    const jobId = document.getElementById('job-selector').value;
    const questionCount = parseInt(document.getElementById('question-count-input').value);
    
    // 카테고리 선택 확인
    let categories = [];
    if (document.getElementById('category-general-check').checked) categories.push('일반');
    if (document.getElementById('category-technical-check').checked) categories.push('기술');
    if (document.getElementById('category-personality-check').checked) categories.push('인성');
    if (document.getElementById('category-experience-check').checked) categories.push('경험');
    
    if (!jobTitle || categories.length === 0) {
        alert('직무명과 최소 하나의 카테고리를 선택해주세요.');
        return;
    }
    
    // 로딩 메시지 표시
    document.getElementById('generate-questions-btn').disabled = true;
    document.getElementById('generate-questions-btn').innerHTML = '<i class="bi bi-hourglass-split"></i> 질문 생성 중...';
    
    // API 호출
    fetch('/interview/generate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            job_title: jobTitle,
            company_name: companyName,
            job_id: jobId || null,
            categories: categories,
            count: questionCount
        })
    })
    .then(response => response.json())
    .then(data => {
        // 버튼 상태 복원
        document.getElementById('generate-questions-btn').disabled = false;
        document.getElementById('generate-questions-btn').innerHTML = '<i class="bi bi-magic"></i> 질문 생성';
        
        if (data.error) {
            alert('질문 생성 실패: ' + data.error);
            return;
        }
        
        // 생성된 질문 표시
        displayGeneratedQuestions(data.questions || []);
    })
    .catch(error => {
        // 버튼 상태 복원
        document.getElementById('generate-questions-btn').disabled = false;
        document.getElementById('generate-questions-btn').innerHTML = '<i class="bi bi-magic"></i> 질문 생성';
        
        console.error('Error:', error);
        alert('질문 생성 중 오류가 발생했습니다.');
    });
}

/**
 * 생성된 질문 표시 함수
 */
function displayGeneratedQuestions(questions) {
    const container = document.getElementById('generated-questions-container');
    const listElement = document.getElementById('generated-questions-list');
    
    if (!container || !listElement) return;
    
    // 질문 목록 초기화
    listElement.innerHTML = '';
    
    if (questions.length === 0) {
        listElement.innerHTML = '<div class="list-group-item text-muted">생성된 질문이 없습니다.</div>';
        return;
    }
    
    // 질문 목록 생성
    questions.forEach(function(question, index) {
        const item = document.createElement('div');
        item.className = 'list-group-item';
        item.dataset.questionData = JSON.stringify(question);
        
        const header = document.createElement('div');
        header.className = 'd-flex justify-content-between align-items-center mb-2';
        
        const badge = document.createElement('span');
        badge.className = 'badge';
        badge.textContent = question.category;
        
        if (question.category === '일반') {
            badge.classList.add('bg-secondary');
        } else if (question.category === '기술') {
            badge.classList.add('bg-primary');
        } else if (question.category === '인성') {
            badge.classList.add('bg-info');
        } else if (question.category === '경험') {
            badge.classList.add('bg-success');
        } else {
            badge.classList.add('bg-secondary');
        }
        
        const saveBtn = document.createElement('button');
        saveBtn.className = 'btn btn-sm btn-outline-success save-question-btn';
        saveBtn.innerHTML = '<i class="bi bi-check-circle"></i>';
        saveBtn.title = '이 질문 저장';
        saveBtn.addEventListener('click', function() {
            saveGeneratedQuestion(question);
        });
        
        header.appendChild(badge);
        header.appendChild(saveBtn);
        
        const questionText = document.createElement('div');
        questionText.textContent = question.question;
        
        item.appendChild(header);
        item.appendChild(questionText);
        
        if (question.answer) {
            const answerContainer = document.createElement('div');
            answerContainer.className = 'mt-2 text-muted small';
            answerContainer.innerHTML = '<strong>참고 답변:</strong><br>' + question.answer;
            item.appendChild(answerContainer);
        }
        
        listElement.appendChild(item);
    });
    
    // 컨테이너 표시
    container.style.display = 'block';
}

/**
 * 생성된 질문 저장 함수
 */
function saveGeneratedQuestion(question) {
    const jobId = document.getElementById('job-selector').value;
    
    fetch('/interview/questions', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            question: question.question,
            answer: question.answer || '',
            category: question.category,
            difficulty: question.difficulty || 3,
            job_id: jobId || null
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('질문이 저장되었습니다.');
        } else {
            alert('질문 저장 실패: ' + (data.error || '알 수 없는 오류'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('질문 저장 중 오류가 발생했습니다.');
    });
}

/**
 * 모든 생성된 질문 저장 함수
 */
function saveAllGeneratedQuestions() {
    const questionItems = document.querySelectorAll('#generated-questions-list .list-group-item');
    const jobId = document.getElementById('job-selector').value;
    
    if (questionItems.length === 0) {
        alert('저장할 질문이 없습니다.');
        return;
    }
    
    // 저장 버튼 비활성화
    document.getElementById('save-all-questions-btn').disabled = true;
    document.getElementById('save-all-questions-btn').innerHTML = '<i class="bi bi-hourglass-split"></i> 저장 중...';
    
    // 모든 질문 저장
    let savedCount = 0;
    let totalCount = questionItems.length;
    let errorCount = 0;
    
    questionItems.forEach(function(item) {
        try {
            const questionData = JSON.parse(item.dataset.questionData);
            
            fetch('/interview/questions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    question: questionData.question,
                    answer: questionData.answer || '',
                    category: questionData.category,
                    difficulty: questionData.difficulty || 3,
                    job_id: jobId || null
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    savedCount++;
                } else {
                    errorCount++;
                }
                
                // 모든 요청 완료 시
                if (savedCount + errorCount === totalCount) {
                    finishSaving(savedCount, errorCount);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                errorCount++;
                
                // 모든 요청 완료 시
                if (savedCount + errorCount === totalCount) {
                    finishSaving(savedCount, errorCount);
                }
            });
        } catch (e) {
            console.error('Error parsing question data:', e);
            errorCount++;
            
            // 모든 요청 완료 시
            if (savedCount + errorCount === totalCount) {
                finishSaving(savedCount, errorCount);
            }
        }
    });
    
    // 저장 완료 후 상태 업데이트
    function finishSaving(saved, failed) {
        // 버튼 상태 복원
        document.getElementById('save-all-questions-btn').disabled = false;
        document.getElementById('save-all-questions-btn').innerHTML = '<i class="bi bi-save"></i> 모든 질문 저장';
        
        if (failed === 0) {
            alert(`${saved}개의 질문이 성공적으로 저장되었습니다.`);
            
            // 생성된 질문 컨테이너 숨기기
            document.getElementById('generated-questions-container').style.display = 'none';
            
            // 페이지 새로고침 (선택적)
            if (saved > 0) {
                location.reload();
            }
        } else {
            alert(`${saved}개의 질문이 저장되었습니다. ${failed}개의 질문 저장 중 오류가 발생했습니다.`);
        }
    }
}
