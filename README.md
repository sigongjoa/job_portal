# 구직 정보 관리 시스템

구직 정보 관리 시스템은 채용 공고를 저장하고 관리하며, 지원 상태를 추적하고 자기소개서와 포트폴리오를 관리할 수 있는 웹 애플리케이션입니다.

## 주요 기능

- 채용 공고 크롤링 및 수동 추가
- 채용 정보 상태 추적 (미지원, 지원, 서류합격 등)
- 자기소개서 및 포트폴리오 관리
- 지원 정보 백업 및 복원
- **AI 도우미 (LM Studio를 통한 로컬 LLM 통합)**

## MCP와 LM Studio 통합

이 애플리케이션은 Model Context Protocol(MCP)을 통해 로컬 LLM(대규모 언어 모델)을 통합합니다. 이를 통해 다음과 같은 AI 도우미 기능을 사용할 수 있습니다:

- 자기소개서 자동 생성
- 채용 공고 분석
- 자기소개서 초안 작성
- 면접 질문 답변 제안

### 설정 방법

1. [LM Studio](https://lmstudio.ai/)를 설치합니다.
2. LM Studio에서 모델을 다운로드하고 로드합니다.
3. "Local Server" 탭에서 서버를 시작합니다 (기본 URL: http://localhost:1234).
4. 애플리케이션을 실행하고 AI 도우미 기능을 사용합니다.

## 설치 및 실행

```bash
# 저장소 클론
git clone https://github.com/yourusername/job_portal.git
cd job_portal

# 가상 환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows의 경우: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 애플리케이션 실행
python app.py
```

## 기술 스택

- **백엔드**: Flask, SQLite, SQLAlchemy
- **프론트엔드**: HTML, CSS, JavaScript, Bootstrap
- **AI 통합**: Model Context Protocol (MCP), LM Studio
