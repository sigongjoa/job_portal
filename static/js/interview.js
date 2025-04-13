document.addEventListener('DOMContentLoaded', function() {
    // 각 기능별 모듈 로드
    loadModule('question-manager');
    loadModule('interview-simulator');
    loadModule('ai-assistant');
});

// 모듈 로드 함수
function loadModule(moduleName) {
    const script = document.createElement('script');
    script.src = `/static/js/interview/${moduleName}.js`;
    document.head.appendChild(script);
}
