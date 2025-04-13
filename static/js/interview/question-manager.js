/**
 * 면접 질문 관리 모듈
 */
console.log('면접 질문 관리 모듈 초기화 시작');

// 질문 삭제 함수
function deleteQuestion(questionId) {
    console.log(`질문 ID: ${questionId} 삭제 시도`);
    
    fetch(`/interview/questions/${questionId}`, {
        method: 'DELETE'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP 오류: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('응답 데이터:', data);
        if (data.success) {
            // 삭제 성공 시 페이지 새로고침
            location.reload();
        } else {
            alert('질문 삭제 실패: ' + (data.error || '알 수 없는 오류'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('질문 삭제 중 오류가 발생했습니다.');
    });
}

// 페이지 로드되면 실행
window.addEventListener('load', function() {
    console.log('면접 질문 관리 모듈 - window load 이벤트 발생');
    
    // DOM 요소 참조 처리
    const deleteButtons = document.querySelectorAll('.delete-question-btn');
    const editButtons = document.querySelectorAll('.edit-question-btn');
    const deleteQuestionBtn = document.getElementById('delete-question-btn');
    const updateQuestionBtn = document.getElementById('update-question-btn');
    const saveQuestionBtn = document.getElementById('save-question-btn');
    const practiceButtons = document.querySelectorAll('.practice-btn');
    const aiFeedbackButtons = document.querySelectorAll('.ai-feedback-btn');

    // 여기에 버튼 상태 확인 출력
    console.log('삭제 버튼 개수:', deleteButtons ? deleteButtons.length : '0, 버튼이 없습니다.');
    console.log('편집 버튼 개수:', editButtons ? editButtons.length : '0, 버튼이 없습니다.');
    console.log('모달 삭제 버튼:', deleteQuestionBtn ? '존재함' : '없음');
    console.log('연습하기 버튼 개수:', practiceButtons ? practiceButtons.length : '0, 버튼이 없습니다.');
    console.log('AI 피드백 버튼 개수:', aiFeedbackButtons ? aiFeedbackButtons.length : '0, 버튼이 없습니다.');

    // 질문 저장 버튼 클릭 시
    if (saveQuestionBtn) {
        saveQuestionBtn.addEventListener('click', function() {
            console.log('질문 저장 버튼 클릭');
            document.getElementById('add-question-form').submit();
        });
    }
    
    // 질문 목록 필터링 기능
    function filterQuestions() {
        const searchText = document.getElementById('search-question').value.toLowerCase();
        const categoryFilter = document.getElementById('category-filter').value;
        const jobFilter = document.getElementById('job-filter').value;
        
        const questions = document.querySelectorAll('.question-card');
        
        questions.forEach(function(question) {
            const questionText = question.dataset.questionText.toLowerCase();
            const category = question.dataset.category;
            const jobId = question.dataset.jobId;
            
            const textMatch = questionText.includes(searchText);
            const categoryMatch = !categoryFilter || category === categoryFilter;
            const jobMatch = !jobFilter || jobId === jobFilter;
            
            if (textMatch && categoryMatch && jobMatch) {
                question.style.display = '';
            } else {
                question.style.display = 'none';
            }
        });
    }
    
    // 검색 버튼 클릭 시
    const searchBtn = document.getElementById('search-btn');
    if (searchBtn) {
        searchBtn.addEventListener('click', filterQuestions);
    }
    
    // 검색어 입력 시 (Enter 키)
    const searchQuestion = document.getElementById('search-question');
    if (searchQuestion) {
        searchQuestion.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                filterQuestions();
            }
        });
    }
    
    // 필터 변경 시
    const categoryFilter = document.getElementById('category-filter');
    const jobFilter = document.getElementById('job-filter');
    if (categoryFilter) categoryFilter.addEventListener('change', filterQuestions);
    if (jobFilter) jobFilter.addEventListener('change', filterQuestions);
    
    // 필터 초기화 버튼 클릭 시
    const resetFilterBtn = document.getElementById('reset-filter-btn');
    if (resetFilterBtn) {
        resetFilterBtn.addEventListener('click', function() {
            if (searchQuestion) searchQuestion.value = '';
            if (categoryFilter) categoryFilter.value = '';
            if (jobFilter) jobFilter.value = '';
            filterQuestions();
        });
    }
    
    // 연습하기 버튼 클릭 시
    if (practiceButtons && practiceButtons.length > 0) {
        console.log('연습하기 버튼 이벤트 핸들러 등록');
        practiceButtons.forEach(function(button) {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                const questionId = this.dataset.questionId;
                console.log('연습하기 버튼 클릭: 질문 ID =', questionId);
                // 탭 전환
                const simulatorTab = document.getElementById('simulator-tab');
                if (simulatorTab) {
                    simulatorTab.click();
                    // 질문 로드 함수 호출 (interview-simulator.js에 정의돼 있어야 함)
                    if (typeof loadQuestionForSimulator === 'function') {
                        loadQuestionForSimulator(questionId);
                    } else {
                        console.error('질문 로드 함수가 정의되지 않았습니다.');
                    }
                }
            });
        });
    }
    
    // AI 피드백 버튼 클릭 시
    if (aiFeedbackButtons && aiFeedbackButtons.length > 0) {
        console.log('AI 피드백 버튼 이벤트 핸들러 등록');
        aiFeedbackButtons.forEach(function(button) {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                const questionId = this.dataset.questionId;
                console.log('AI 피드백 버튼 클릭: 질문 ID =', questionId);
                // 탭 전환
                const aiAssistantTab = document.getElementById('ai-assistant-tab');
                if (aiAssistantTab) {
                    aiAssistantTab.click();
                    // 질문 로드 함수 호출 (ai-assistant.js에 정의돼 있어야 함)
                    if (typeof loadQuestionForAI === 'function') {
                        loadQuestionForAI(questionId);
                    } else {
                        console.error('AI 질문 로드 함수가 정의되지 않았습니다.');
                    }
                }
            });
        });
    }
    
    // 질문 편집 버튼 클릭 시
    if (editButtons && editButtons.length > 0) {
        console.log('편집 버튼 이벤트 핸들러 등록:', editButtons.length);
        editButtons.forEach(function(button) {
            button.addEventListener('click', function(event) {
                event.preventDefault();
                event.stopPropagation();
                const questionId = this.dataset.questionId;
                if (!questionId) {
                    console.error('질문 ID가 없습니다:', button);
                    return;
                }
                
                console.log('질문 편집 시도:', questionId);
                
                // 질문 정보 가져오기
                fetch(`/interview/questions/${questionId}`)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error(`HTTP 오류: ${response.status}`);
                        }
                        return response.json();
                    })
                    .then(question => {
                        if (!question) {
                            throw new Error('질문 데이터가 없습니다.');
                        }
                        
                        console.log('받은 질문 데이터:', question);
                        
                        // 모달에 질문 정보 채우기
                        document.getElementById('edit-question-id').value = question.id;
                        document.getElementById('edit-question-text').value = question.question;
                        document.getElementById('edit-question-answer').value = question.answer || '';
                        document.getElementById('edit-question-category').value = question.category || '일반';
                        document.getElementById('edit-question-difficulty').value = question.difficulty || 3;
                        document.getElementById('edit-question-job').value = question.job_id || '';
                        
                        // 모달 열기
                        const modal = new bootstrap.Modal(document.getElementById('edit-question-modal'));
                        modal.show();
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('질문 정보를 가져오는 중 오류가 발생했습니다.');
                    });
            });
        });
    } else {
        console.warn('편집 버튼을 찾을 수 없습니다.');
    }
    
    // 질문 삭제 버튼 클릭 시 (모달 내부)
    if (deleteQuestionBtn) {
        deleteQuestionBtn.addEventListener('click', function(event) {
            event.preventDefault();
            const questionId = document.getElementById('edit-question-id').value;
            if (questionId && confirm('이 질문을 정말 삭제하시겠습니까?')) {
                console.log('모달에서 질문 삭제 시도:', questionId);
                deleteQuestion(questionId);
            }
        });
    } else {
        console.warn('모달의 삭제 버튼을 찾을 수 없습니다.');
    }
    
    // 질문 삭제 버튼 클릭 시 (카드 내부)
    if (deleteButtons && deleteButtons.length > 0) {
        console.log('삭제 버튼 이벤트 핸들러 등록:', deleteButtons.length);
        deleteButtons.forEach(function(button) {
            button.addEventListener('click', function(event) {
                event.preventDefault();
                event.stopPropagation();
                const questionId = this.dataset.questionId;
                if (questionId && confirm('이 질문을 정말 삭제하시겠습니까?')) {
                    console.log('질문 삭제 시도:', questionId);
                    deleteQuestion(questionId);
                }
            });
        });
    } else {
        console.warn('삭제 버튼을 찾을 수 없습니다.');
    }
    
    // 질문 업데이트 버튼 클릭 시
    if (updateQuestionBtn) {
        updateQuestionBtn.addEventListener('click', function() {
            const questionId = document.getElementById('edit-question-id').value;
            const questionData = {
                question: document.getElementById('edit-question-text').value,
                answer: document.getElementById('edit-question-answer').value,
                category: document.getElementById('edit-question-category').value,
                difficulty: document.getElementById('edit-question-difficulty').value,
                job_id: document.getElementById('edit-question-job').value || null
            };
            
            console.log('질문 업데이트 시도:', questionId, questionData);
            
            fetch(`/interview/questions/${questionId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(questionData)
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP 오류: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    // 업데이트 성공 시 페이지 새로고침
                    location.reload();
                } else {
                    alert('질문 업데이트 실패: ' + (data.error || '알 수 없는 오류'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('질문 업데이트 중 오류가 발생했습니다.');
            });
        });
    } else {
        console.warn('업데이트 버튼을 찾을 수 없습니다.');
    }
    
    // 이벤트 핸들러 추가 완료 로그
    console.log('면접 질문 관리 모듈 - 이벤트 핸들러 등록 완료');
});

// 초기화 완료 로그
console.log('면접 질문 관리 모듈 초기화 완료');
