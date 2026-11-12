# 환경변수 (실제 비밀값 제출 금지)

| 변수 | 사용 위치 | 용도 | 로컬 예시 |
|---|---|---|---|
| CORE_BASE_URL | Backend | Python Core 주소 | http://127.0.0.1:8001 |
| CORE_SHARED_TOKEN | Backend/Core | 내부 호출 공유 비밀 | 임의의 긴 랜덤 문자열 |
| JWT_ISSUER_URI | Backend | 운영 JWT 발급자 | https://issuer.example.invalid/ |
| LOCAL_DEV_NO_AUTH | Backend | 로컬만 인증 생략 | true (운영 false) |
| OPENAI_API_KEY | 향후 확장 | LLM API 키 (현재 미사용) | 제출하지 않음 |
| OPENAI_MODEL | 향후 확장 | 사용 모델 (현재 미사용) | 설정 시 입력 |
| VITE_API_BASE | 향후 확장 | API prefix (현재 /api 고정) | /api |

`CORE_SHARED_TOKEN`을 Backend와 Core 프로세스에 동일하게 설정하세요. 실제 키를 소스에 저장하지 마세요.
