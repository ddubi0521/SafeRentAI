# Backend — Spring Boot 3.3.10 / Java 17

```bash
export CORE_BASE_URL=http://localhost:8001
export CORE_SHARED_TOKEN=local-test-token
export LOCAL_DEV_NO_AUTH=true  # 로컬 개발에서만!
gradle bootRun
```

검증 환경에서는 `gradle clean build` 또는 설치된 Gradle Wrapper의 `./gradlew clean build`를 사용하세요.
운영 연동 시 `LOCAL_DEV_NO_AUTH=false`, `JWT_ISSUER_URI`를 실제 발급자 주소로 설정하세요. 싱크인사이트 공통 응답 규격 확정 시 응답 래퍼를 맞춰야 합니다.
