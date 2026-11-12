# Core (Python 3.11 / FastAPI / Poetry)

```bash
poetry install
export CORE_SHARED_TOKEN=local-test-token
poetry run uvicorn app.main:app --host 127.0.0.1 --port 8001
poetry run pytest
```

- `POST /internal/analyze`: `multipart/form-data` PDF, `X-Core-Token` 필요
- `GET /health`: 헬스 체크
- 이미지 전용 스캔 PDF OCR, LLM 판정, 공식 법령/판례 API 조회는 **현재 미구현**. 미구현 기능을 완성된 것으로 표시하지 않음.
- 업로드 PDF는 저장하지 않고 요청 메모리에서 분석. Backend 전달 JSON에는 PDF base64가 포함되어 크기가 큼.
