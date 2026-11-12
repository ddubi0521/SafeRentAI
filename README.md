<<<<<<< HEAD
# SafeRent AI — 싱크인사이트 SR 제출용 MVP

## 1. 도구 개요
자취생 대상 주택 임대차 계약서 PDF의 위험·주의 문구를 사전 탐지하여 문서에 색상으로 표시하고, 확인이 필요한 계약 항목을 안내합니다.
**법률 자문이 아니며 공식 표준계약서·법령·판례 API 조회/AI RAG/OCR은 현재 미구현**입니다. 자동 분석 범위는 정규식 휴리스틱이며 적법성·최신성 판정을 제공하지 않습니다.

## 2. 포함 축
- [x] Frontend: React 18 + TypeScript 5.7 + Vite 6
- [x] Backend: Java 17 + Spring Boot 3.3.10 + Gradle
- [x] Core: Python 3.11 + FastAPI + Pydantic v2 + Poetry

## 3. 실행
1. Core: `cd core && poetry install && CORE_SHARED_TOKEN=local-test-token poetry run uvicorn app.main:app --port 8001`
2. Backend: `cd backend && CORE_SHARED_TOKEN=local-test-token LOCAL_DEV_NO_AUTH=true gradle bootRun` (Gradle 8.x 설치 필요)
3. Frontend: `cd frontend && npm ci && npm run dev`
4. 브라우저에서 `http://localhost:5173/tools/safe-rent` 또는 `/` 열기 (Vite SPA fallback)

Windows PowerShell에서는 환경변수를 `$env:CORE_SHARED_TOKEN="local-test-token"` 형식으로 지정합니다.

## 4. 검증
- Frontend: `npm ci && npm run build`
- Backend: `gradle clean build` (시스템 Gradle 요구, wrapper 미포함)
- Core: `poetry install && poetry run pytest`
- 버전/환경별 실제 수행 여부는 `TEST_RESULT.md` 참고.

## 5. 보안
- 샘플 개인정보나 키/토큰 제출 금지
- 원본 PDF는 메모리 내에서 분석하며 파일 시스템에 저장하지 않음
- 운영에서는 JWT 및 Gateway 정책 준수; 개발용 인증 해제 옵션 반드시 비활성화
- PDF 전송이 있으므로 HTTPS 적용 권장

## 6. 도구 제출 및 확장
희망 Frontend 경로 `/tools/safe-rent`, API 경로 `/api/tools/safe-rent`.
manifest/API_SPEC/ENV.template/TEST_RESULT 포함. 싱크인사이트 CommonResponse의 구체적 객체 모양 및 라우팅은 SR 검토 후 최종 확정.