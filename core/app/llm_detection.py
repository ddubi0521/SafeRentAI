
import json
import os
from openai import OpenAI


def detect_risks_with_llm(pages: list[str]) -> list[dict]:
    """계약서 문맥을 검토하여 기존 5개 위험 유형의 후보를 찾는다."""

    if not any(page.strip() for page in pages):
        return []

    client = OpenAI(timeout=60, max_retries=1)

    instructions = """
당신은 한국 주택임대차계약서의 위험 신호를 검토하는 AI입니다.

계약서에서 임차인에게 불리할 가능성이 있는 조항을 찾으세요.
법적 위법성이나 계약 조항의 무효를 확정하지 마세요.

이번 단계에서는 다음 5개 유형만 탐지합니다.
1. 보증금 반환 제한
2. 과도한 수선비 부담
3. 임대인의 임의 출입
4. 일방적인 계약 해지
5. 관리비 변경 재량

판단 기준:
- 계약서의 전체 문맥을 고려하세요.
- 정상적인 보증금 공제, 임차인 귀책에 따른 원상복구,
  법정 해지 사유 등을 자동으로 위험하다고 판단하지 마세요.
- 관리비의 내부 규정이 불명확하거나 일방적인 변경 가능성이
  있는 경우는 추가 확인 후보로 분류할 수 있습니다.
- 임대인의 출입 권한을 과도하게 허용하는 조항을 찾으세요.
- 실제 계약서에 없는 내용을 만들어내지 마세요.
- quote는 반드시 해당 페이지의 원문에서 그대로 복사하세요.
- 페이지 번호는 입력의 page 값과 일치해야 합니다.
- 불확실한 사항은 위험 확정이 아닌 확인 필요로 설명하세요.
- 동일한 위험 조항을 중복 출력하지 마세요.
- 최대 10개까지만 출력하세요.

반드시 다음 형식의 JSON 객체만 반환하세요.

{
  "findings": [
    {
      "title": "관리비 변경 재량",
      "quote": "계약서에 실제로 있는 원문",
      "page": 1,
      "reason": "추가 확인이 필요한 이유",
      "recommendation": "구체적인 확인 또는 수정 권고"
    }
  ]
}

해당 유형에 속하는 위험 후보가 없으면
{"findings": []}를 반환하세요.
"""

    payload = {
        "pages": [
            {"page": i + 1, "text": text[:30000]}
            for i, text in enumerate(pages[:100])
        ]
    }

    try:
        response = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-5.1"),
            instructions=instructions,
            input=(
                    "다음 임대차계약서를 검토하고 "
                    "반드시 JSON 객체로 응답하세요.\n\n"
                    + json.dumps(payload, ensure_ascii=False)
            ),
            text={"format": {"type": "json_object"}},
            max_output_tokens=2500,
            store=False,
        )

        data = json.loads(response.output_text)
        results = data.get("findings", [])

        if not isinstance(results, list):
            return []

        allowed_titles = {
            "보증금 반환 제한",
            "과도한 수선비 부담",
            "임대인의 임의 출입",
            "일방적인 계약 해지",
            "관리비 변경 재량",
        }

        verified = []

        for item in results[:10]:
            if not isinstance(item, dict):
                continue

            title = item.get("title")
            quote = item.get("quote")
            page = item.get("page")
            reason = item.get("reason")
            recommendation = item.get("recommendation")

            if title not in allowed_titles:
                continue

            if not isinstance(page, int) or isinstance(page, bool):
                continue

            if not 1 <= page <= len(pages):
                continue

            if not isinstance(quote, str) or not quote.strip():
                continue

            # GPT가 만든 문장이 아닌 실제 PDF 원문인지 확인
            if quote not in pages[page - 1]:
                print(
                    "[GPT 탐지 제외] 원문 불일치:",
                    repr(quote[:80]),
                    flush=True,
                )
                continue

            if not isinstance(reason, str) or not reason.strip():
                continue

            if not isinstance(recommendation, str) or not recommendation.strip():
                continue

            verified.append({
                "title": title,
                "quote": quote,
                "page": page,
                "reason": reason,
                "recommendation": recommendation,
            })

        print(
            f"[GPT 위험 탐지] {len(verified)}건 확인",
            flush=True,
        )

        return verified

    except Exception as e:
        print(
            "[GPT 위험 탐지 오류]",
            type(e).__name__,
            str(e),
            flush=True,
        )
        return []
