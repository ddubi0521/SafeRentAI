# 제출 전 검증 결과

| 검증 항목 | 명령 | 결과 | 비고 |
|---|---|---|---|
| FE 의존성 설치 | `npm install --package-lock-only` | 미실행 | 네트워크 연결 필요, 잠금파일 생성 예정 |
| FE build | `npm run build` | 미실행 | Node 22 필요 |
| BE build | `gradle clean build` | 미실행 | 로컬 Gradle 미설치 |
| Core install | `poetry install` | 미실행 | Python 3.11/Poetry 필요 |
| Core tests | `poetry run pytest` | 미실행 | 관련 의존성 설치 필요 |
| API 계약 검토 | `API_SPEC.md` 수동 검토 | 문서 작성 | 운영 공통 응답 형식 최종 확인 필요 |

미실행 항목을 PASS로 허위 표시하지 않습니다.
