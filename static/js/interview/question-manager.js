/**
 * 면접 질문 관리 모듈
 */
document.addEventListener('DOMContentLoaded', function() {
    // 질문 저장 버튼 클릭 시
    const saveQuestionBtn = document.getElementById('save-question-btn');
    if (saveQuestionBtn) {
        saveQuestionBtn.addEventListener('click', function() {
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
    
    // 질문 편집 버튼 클릭 시
    const editButtons = document.querySelectorAll('.edit-question-btn');
    editButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const questionId = button.dataset.questionId;
            
            // 질문 정보 가져오기
            fetch(`/interview/questions/${questionId}`)
                .then(response => response.json())
                .then(question => {
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
    
    // 질문 삭제 버튼 클릭 시 (모달 내부)
    const deleteQuestionBtn = document.getElementById('delete-question-btn');
    if (deleteQuestionBtn) {
        deleteQuestionBtn.addEventListener('click', function() {
            const questionId = document.getElementById('edit-question-id').value;
            if (questionId && confirm('이 질문을 정말 삭제하시겠습니까?')) {
                deleteQuestion(questionId);
            }
        });
    }
    
    // 질문 삭제 버튼 클릭 시 (카드 내부)
    const deleteButtons = document.querySelectorAll('.delete-question-btn');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const questionId = button.dataset.questionId;
            if (questionId && confirm('이 질문을 정말 삭제하시겠습니까?')) {
                deleteQuestion(questionId);
            }
        });
    });
    
    // 질문 삭제 함수
    function deleteQuestion(questionId) {
        fetch(`/interview/questions/${questionId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
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
    
    // 질문 업데이트 버튼 클릭 시
    const updateQuestionBtn = document.getElementById('update-question-btn');
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
            
            fetch(`/interview/questions/${questionId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(questionData)
            })
            .then(response => response.json())
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
    }
});
