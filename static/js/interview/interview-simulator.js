/**
 * 모의 면접 시뮬레이터 모듈
 */
document.addEventListener('DOMContentLoaded', function() {
    // 전역 변수
    let currentQuestionId = null;
    let interviewQuestions = [];
    let currentQuestionIndex = -1;
    let timerInterval = null;
    
    // 연습하기 버튼 클릭 시
    const practiceButtons = document.querySelectorAll('.practice-btn');
    practiceButtons.forEach(function(button) {
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
                    interviewQuestions = [question];
                    currentQuestionIndex = 0;
                    displayCurrentQuestion();
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('질문 정보를 가져오는 중 오류가 발생했습니다.');
                });
        });
    });
    
    // 시작 버튼 클릭 시
    const startPracticeBtn = document.getElementById('start-practice-btn');
    if (startPracticeBtn) {
        startPracticeBtn.addEventListener('click', function() {
            // 질문 세트 가져오기
            const questionSet = document.getElementById('question-set').value;
            const questionCount = parseInt(document.getElementById('question-count').value);
            
            // 선택에 따라 질문 필터링
            let filteredQuestions = [];
            
            if (questionSet === 'random') {
                // 모든 질문에서 랜덤 선택
                const allQuestionElements = document.querySelectorAll('.question-card');
                const allQuestions = [];
                
                allQuestionElements.forEach(function(element) {
                    const questionId = element.querySelector('.edit-question-btn').dataset.questionId;
                    fetch(`/interview/questions/${questionId}`)
                        .then(response => response.json())
                        .then(question => {
                            allQuestions.push(question);
                            
                            // 마지막 질문까지 로드되면 랜덤 선택
                            if (allQuestions.length === allQuestionElements.length) {
                                // 랜덤 선택
                                for (let i = 0; i < Math.min(questionCount, allQuestions.length); i++) {
                                    const randomIndex = Math.floor(Math.random() * allQuestions.length);
                                    filteredQuestions.push(allQuestions.splice(randomIndex, 1)[0]);
                                }
                                
                                interviewQuestions = filteredQuestions;
                                currentQuestionIndex = 0;
                                displayCurrentQuestion();
                                startTimer();
                            }
                        })
                        .catch(error => {
                            console.error('Error:', error);
                        });
                });
            } else if (questionSet.startsWith('category-')) {
                // 카테고리별 질문
                const category = questionSet.replace('category-', '');
                const categoryElements = document.querySelectorAll(`.question-card[data-category="${category}"]`);
                
                // 카테고리별 질문 가져오기
                const categoryQuestions = [];
                
                categoryElements.forEach(function(element) {
                    const questionId = element.querySelector('.edit-question-btn').dataset.questionId;
                    fetch(`/interview/questions/${questionId}`)
                        .then(response => response.json())
                        .then(question => {
                            categoryQuestions.push(question);
                            
                            // 마지막 질문까지 로드되면 랜덤 선택
                            if (categoryQuestions.length === categoryElements.length) {
                                // 랜덤 선택
                                for (let i = 0; i < Math.min(questionCount, categoryQuestions.length); i++) {
                                    const randomIndex = Math.floor(Math.random() * categoryQuestions.length);
                                    filteredQuestions.push(categoryQuestions.splice(randomIndex, 1)[0]);
                                }
                                
                                interviewQuestions = filteredQuestions;
                                currentQuestionIndex = 0;
                                displayCurrentQuestion();
                                startTimer();
                            }
                        })
                        .catch(error => {
                            console.error('Error:', error);
                        });
                });
            } else if (questionSet.startsWith('job-')) {
                // 특정 채용 공고 질문
                const jobId = questionSet.replace('job-', '');
                const jobElements = document.querySelectorAll(`.question-card[data-job-id="${jobId}"]`);
                
                // 채용 공고별 질문 가져오기
                const jobQuestions = [];
                
                jobElements.forEach(function(element) {
                    const questionId = element.querySelector('.edit-question-btn').dataset.questionId;
                    fetch(`/interview/questions/${questionId}`)
                        .then(response => response.json())
                        .then(question => {
                            jobQuestions.push(question);
                            
                            // 마지막 질문까지 로드되면 랜덤 선택
                            if (jobQuestions.length === jobElements.length) {
                                // 랜덤 선택
                                for (let i = 0; i < Math.min(questionCount, jobQuestions.length); i++) {
                                    const randomIndex = Math.floor(Math.random() * jobQuestions.length);
                                    filteredQuestions.push(jobQuestions.splice(randomIndex, 1)[0]);
                                }
                                
                                interviewQuestions = filteredQuestions;
                                currentQuestionIndex = 0;
                                displayCurrentQuestion();
                                startTimer();
                            }
                        })
                        .catch(error => {
                            console.error('Error:', error);
                        });
                });
            } else {
                // 모든 질문
                const allQuestionElements = document.querySelectorAll('.question-card');
                
                // 전체 질문 가져오기
                const allQuestions = [];
                
                allQuestionElements.forEach(function(element) {
                    const questionId = element.querySelector('.edit-question-btn').dataset.questionId;
                    fetch(`/interview/questions/${questionId}`)
                        .then(response => response.json())
                        .then(question => {
                            allQuestions.push(question);
                            
                            // 마지막 질문까지 로드되면 표시
                            if (allQuestions.length === allQuestionElements.length) {
                                interviewQuestions = allQuestions.slice(0, questionCount);
                                currentQuestionIndex = 0;
                                displayCurrentQuestion();
                                startTimer();
                            }
                        })
                        .catch(error => {
                            console.error('Error:', error);
                        });
                });
            }
            
            // 면접 질문 목록 표시
            updateInterviewQuestionsList();
            
            // 컨트롤 버튼 상태 변경
            startPracticeBtn.style.display = 'none';
            document.getElementById('pause-practice-btn').style.display = 'inline-block';
            document.getElementById('stop-practice-btn').style.display = 'inline-block';
            
            // 답변 입력창 표시
            document.getElementById('answer-section').style.display = 'block';
        });
    }
    
    // 현재 질문 표시 함수
    function displayCurrentQuestion() {
        if (currentQuestionIndex >= 0 && currentQuestionIndex < interviewQuestions.length) {
            const question = interviewQuestions[currentQuestionIndex];
            document.getElementById('current-question').textContent = question.question;
            
            // 질문 상세 정보 표시
            const questionDetails = document.getElementById('question-details');
            const questionCategory = document.getElementById('question-category');
            const questionDifficulty = document.getElementById('question-difficulty');
            
            questionDetails.style.display = 'block';
            
            // 카테고리 배지 색상 설정
            questionCategory.textContent = question.category;
            questionCategory.className = 'badge me-2';
            if (question.category === '일반') {
                questionCategory.classList.add('bg-secondary');
            } else if (question.category === '기술') {
                questionCategory.classList.add('bg-primary');
            } else if (question.category === '인성') {
                questionCategory.classList.add('bg-info');
            } else if (question.category === '경험') {
                questionCategory.classList.add('bg-success');
            } else {
                questionCategory.classList.add('bg-secondary');
            }
            
            // 난이도 표시
            questionDifficulty.innerHTML = '난이도: ';
            for (let i = 1; i <= 5; i++) {
                if (i <= question.difficulty) {
                    questionDifficulty.innerHTML += '<i class="bi bi-star-fill difficulty-star"></i> ';
                } else {
                    questionDifficulty.innerHTML += '<i class="bi bi-star difficulty-star text-muted"></i> ';
                }
            }
            
            // 답변 필드 초기화
            document.getElementById('practice-answer').value = '';
            
            // 답변 피드백 섹션 숨기기
            const feedbackSection = document.getElementById('feedback-section');
            if (feedbackSection) {
                feedbackSection.style.display = 'none';
            }
            
            // 면접 질문 목록 업데이트
            updateInterviewQuestionsList();
        }
    }
    
    // 타이머 시작 함수
    function startTimer() {
        // 이전 타이머 정리
        if (timerInterval) {
            clearInterval(timerInterval);
        }
        
        // 타이머 사용 여부 확인
        if (!document.getElementById('enable-timer').checked) {
            document.getElementById('timer-display').style.display = 'none';
            return;
        }
        
        // 타이머 설정
        const timerElement = document.getElementById('timer');
        const timerDisplay = document.getElementById('timer-display');
        const intervalTime = parseInt(document.getElementById('interview-time').value);
        
        // 타이머 표시
        timerDisplay.style.display = 'block';
        timerElement.textContent = intervalTime;
        
        // 타이머 시작
        timerInterval = setInterval(function() {
            let time = parseInt(timerElement.textContent);
            time -= 1;
            
            timerElement.textContent = time;
            
            // 시간 종료 시
            if (time <= 0) {
                clearInterval(timerInterval);
                alert('시간이 종료되었습니다!');
            }
        }, 1000);
    }
    
    // 면접 질문 목록 업데이트 함수
    function updateInterviewQuestionsList() {
        const listElement = document.getElementById('interview-questions-list');
        
        if (listElement && interviewQuestions.length > 0) {
            listElement.innerHTML = '';
            
            interviewQuestions.forEach(function(question, index) {
                const listItem = document.createElement('li');
                listItem.className = 'list-group-item';
                
                if (index === currentQuestionIndex) {
                    listItem.classList.add('active');
                }
                
                listItem.textContent = `${index + 1}. ${question.question}`;
                
                // 클릭 시 해당 질문으로 이동
                listItem.addEventListener('click', function() {
                    currentQuestionIndex = index;
                    displayCurrentQuestion();
                    
                    // 타이머 재시작
                    startTimer();
                });
                
                listElement.appendChild(listItem);
            });
        }
    }
    
    // 일시정지 버튼 클릭 시
    const pausePracticeBtn = document.getElementById('pause-practice-btn');
    if (pausePracticeBtn) {
        pausePracticeBtn.addEventListener('click', function() {
            if (timerInterval) {
                clearInterval(timerInterval);
                pausePracticeBtn.innerHTML = '<i class="bi bi-play-fill"></i> 재개';
                pausePracticeBtn.dataset.state = 'paused';
            } else if (pausePracticeBtn.dataset.state === 'paused') {
                startTimer();
                pausePracticeBtn.innerHTML = '<i class="bi bi-pause-fill"></i> 일시정지';
                pausePracticeBtn.dataset.state = 'playing';
            }
        });
    }
    
    // 종료 버튼 클릭 시
    const stopPracticeBtn = document.getElementById('stop-practice-btn');
    if (stopPracticeBtn) {
        stopPracticeBtn.addEventListener('click', function() {
            if (timerInterval) {
                clearInterval(timerInterval);
            }
            
            // 초기 상태로 되돌리기
            document.getElementById('current-question').textContent = '질문을 선택하거나 시작 버튼을 클릭하세요.';
            document.getElementById('question-details').style.display = 'none';
            document.getElementById('timer-display').style.display = 'none';
            document.getElementById('answer-section').style.display = 'none';
            
            // 피드백 섹션 숨기기
            const feedbackSection = document.getElementById('feedback-section');
            if (feedbackSection) {
                feedbackSection.style.display = 'none';
            }
            
            // 컨트롤 버튼 상태 변경
            document.getElementById('start-practice-btn').style.display = 'inline-block';
            pausePracticeBtn.style.display = 'none';
            stopPracticeBtn.style.display = 'none';
            
            // 질문 목록 초기화
            const listElement = document.getElementById('interview-questions-list');
            if (listElement) {
                listElement.innerHTML = '<li class="list-group-item text-muted">질문을 선택하거나 시작 버튼을 클릭하세요.</li>';
            }
            
            // 변수 초기화
            interviewQuestions = [];
            currentQuestionIndex = -1;
        });
    }
    
    // 답변 저장 버튼 클릭 시
    const saveAnswerBtn = document.getElementById('save-answer-btn');
    if (saveAnswerBtn) {
        saveAnswerBtn.addEventListener('click', function() {
            if (currentQuestionIndex >= 0 && currentQuestionIndex < interviewQuestions.length) {
                const question = interviewQuestions[currentQuestionIndex];
                const answer = document.getElementById('practice-answer').value;
                
                // 답변 저장 API 호출
                fetch(`/interview/questions/${question.id}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        answer: answer
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('답변이 저장되었습니다.');
                        
                        // 다음 질문으로 이동 (있는 경우)
                        if (currentQuestionIndex < interviewQuestions.length - 1) {
                            currentQuestionIndex++;
                            displayCurrentQuestion();
                            startTimer();
                        }
                    } else {
                        alert('답변 저장 실패: ' + (data.error || '알 수 없는 오류'));
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('답변 저장 중 오류가 발생했습니다.');
                });
            }
        });
    }
    
    // AI 피드백 버튼 클릭 시 (모의 면접 탭)
    const getFeedbackBtn = document.getElementById('get-feedback-btn');
    if (getFeedbackBtn) {
        getFeedbackBtn.addEventListener('click', function() {
            if (currentQuestionIndex >= 0 && currentQuestionIndex < interviewQuestions.length) {
                const question = interviewQuestions[currentQuestionIndex];
                const answer = document.getElementById('practice-answer').value;
                
                if (!answer.trim()) {
                    alert('피드백을 받으려면 먼저 답변을 입력하세요.');
                    return;
                }
                
                // MCP 도구 호출
                fetch('/ai/call_tool', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        tool_name: 'analyze_interview_answer',
                        arguments: {
                            question: question.question,
                            answer: answer,
                            category: question.category
                        }
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        alert('피드백 생성 실패: ' + data.error);
                    } else {
                        // 피드백 표시
                        const feedbackSection = document.getElementById('feedback-section');
                        const feedbackContent = document.getElementById('feedback-content');
                        
                        if (feedbackSection && feedbackContent) {
                            feedbackContent.innerHTML = data.result || '피드백을 생성할 수 없습니다.';
                            feedbackSection.style.display = 'block';
                        }
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('피드백 생성 중 오류가 발생했습니다.');
                });
            }
        });
    }
});
