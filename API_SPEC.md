# SafeRent 도구 API 명세

- toolCode: `SAFE_RENT_AI`
- 희망 Backend BasePath: `/api/tools/safe-rent`
- Frontend는 Backend를 경유하고 Core 직접 호출 금지
- 인증: 운영 JWT `Authorization: Bearer <access_token>`; 개발 시에만 `LOCAL_DEV_NO_AUTH=true`

| 메서드 | 경로 | 입력 | 성공 응답 | 오류 |
|---|---|---|---|---|
| POST | `/api/tools/safe-rent/analyze` | multipart `file`(PDF) | JSON `{data: Analysis}` | `{payload:{message}}` |
| GET | `/api/tools/safe-rent/health` | 없음 | `{data:{status:"UP"}}` | - |
| POST | Core `/internal/analyze` | multipart `file` + `X-Core-Token` | `Analysis` | FastAPI `detail` |
| GET | Core `/health` | 없음 | `{status:"UP"}` | - |

Analysis: `filename:string, findings:Finding[], missing_checks:string[], extracted_chars:number, annotated_pdf_base64:string, references_status:string, disclaimer:string`.
Finding: `severity:"danger"|"warning", title:string, quote:string, reason:string, recommendation:string, legal_basis:string, page:number|null, highlighted:boolean`.

**통합 주의**: 이 번들의 `{data:...}` / `{payload:...}` 래퍼는 가이드에 설명된 필드 패턴을 따른 *제출용 초안*입니다. 실제 CommonResponse 구조는 싱크인사이트 팀에서 제공받아 확정해야 합니다. 인증 발급자와 Gateway 라우팅도 협의 대상입니다.

**제약**: Backend-Core 통신은 WebClient. Core URL `CORE_BASE_URL` 주입. 최대 파일 크기 Core 20MB, 최대 100페이지. 암호화 PDF/스캔 PDF 미지원. 공식 법령·판례 및 표준계약서 API 연결은 향후 단계로 표시하며, 법적 근거를 만들어내지 않습니다.
