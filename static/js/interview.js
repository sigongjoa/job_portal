document.addEventListener('DOMContentLoaded', function() {
    // 각 기능별 모듈 로드
    loadModule('question-manager', function() {
        console.log('question-manager 모듈 로드 완료');
        // 다음 모듈 로드
        loadModule('interview-simulator', function() {
            console.log('interview-simulator 모듈 로드 완료');
            // 마지막 모듈 로드
            loadModule('ai-assistant', function() {
                console.log('ai-assistant 모듈 로드 완료');
                console.log('모든 모듈 로드 완료');
            });
        });
    });
});

// 모듈 로드 함수
function loadModule(moduleName, callback) {
    const script = document.createElement('script');
    script.src = `/static/js/interview/${moduleName}.js`;
    
    // 스크립트 로드 완료 후 콜백 실행
    script.onload = function() {
        if (typeof callback === 'function') {
            callback();
        }
    };
    
    // 스크립트 로드 오류 처리
    script.onerror = function() {
        console.error(`${moduleName} 모듈 로드 중 오류 발생`);
    };
    
    document.head.appendChild(script);
}
