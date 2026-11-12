import re
import json
from html import unescape

from app.law_api import (
    search_laws,
    search_cases,
    get_case_detail,
    get_law_article,
)


# 위험 유형별 검토할 법률과 판례 검색 조건
LEGAL_RULES = {
    "보증금 반환 제한": {
        "law": "민법",
        "article": 536,
        "case_query": "임대차보증금 반환",
        "topic_keywords": [
            "보증금반환의무",
            "임대차보증금",
            "동시이행",
            "임대차 종료",
        ],
        "exclude_keywords": [
            "공인중개사",
            "중개보조인",
            "공제약관",
            "사용자책임",
        ],
        "reason": (
            "보증금 반환 시기를 임대인이 일방적으로 "
            "연기할 수 있도록 하는 조항입니다. "
            "임대차 종료와 목적물 반환, 보증금 반환의무의 "
            "관계를 검토해야 합니다. 민법 제536조는 "
            "동시이행 관계를 검토하기 위한 참고 조문이며, "
            "일방적인 반환 연기의 허용 여부를 직접 "
            "판단하는 조문은 아닙니다."
        ),
    },

    "과도한 수선비 부담": {
        "law": "민법",
        "article": 623,
        "case_query": "임대인 수선의무",
        "topic_keywords": [
            "수선의무",
            "수선비용",
            "수리비",
            "유지의무",
        ],
        "exclude_keywords": [
            "사용자책임",
            "중개보조인",
            "보증금 편취",
        ],
        "reason": (
            "민법 제623조는 임대인이 목적물을 "
            "사용·수익에 필요한 상태로 유지할 의무를 "
            "규정합니다. 모든 수리비를 임차인에게 "
            "일괄적으로 부담시키는 조항은 수선의 "
            "원인, 범위, 특약의 효력 등을 검토해야 합니다."
        ),
    },

    "임대인의 임의 출입": {
        "law": "형법",
        "article": 319,
        "case_query": "주거침입",
        "topic_keywords": [
            "주거의 평온",
            "주거침입죄",
            "거주자의 의사",
            "출입 승낙",
        ],
        "exclude_keywords": [
            "야간주거침입절도",
            "절도의 고의",
            "절취",
        ],
        "reason": (
            "임대인이 임차인의 동의 없이 언제든지 "
            "출입할 수 있도록 하는 조항은 주거의 "
            "평온을 침해할 우려가 있습니다. "
            "형법 제319조는 주거침입 여부를 검토할 "
            "때 참고할 조문이며, 실제 범죄 성립 여부는 "
            "구체적인 출입 경위 등에 따라 달라집니다."
        ),
    },

    "일방적인 계약 해지": {
        "law": "민법",
        "article": 635,
        "case_query": "임대차계약 해지",
        "topic_keywords": [
            "임대차계약 해지",
            "해지통고",
            "계약해지",
        ],
        "exclude_keywords": [],
        "reason": (
            "임대인에게만 계약 해지 권한을 부여하는 "
            "특약은 해지 사유와 통지 요건 등을 "
            "검토해야 합니다. 민법 제635조는 "
            "기간의 약정이 없는 임대차 등에 관한 "
            "조문으로, 모든 계약 해지에 적용되지는 "
            "않습니다."
        ),
    },

    "관리비 변경 재량": {
        "law": None,
        "article": None,
        "case_query": "임대차 관리비",
        "topic_keywords": [
            "관리비",
            "관리비 인상",
            "관리비 변경",
        ],
        "exclude_keywords": [],
        "reason": (
            "관리비 변경 기준이 명확하지 않으면 "
            "임차인이 추가 비용을 예측하기 어렵습니다. "
            "관리비 항목과 변경 기준, 고지 방법을 "
            "명확하게 정할 필요가 있습니다."
        ),
    },
}


def as_list(value):
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return [value]
    return []


def clean_text(value):
    if isinstance(value, list):
        value = " ".join(clean_text(v) for v in value)
    elif isinstance(value, dict):
        value = " ".join(clean_text(v) for v in value.values())

    if value is None:
        return ""

    value = unescape(str(value))
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def get_article_text(data, article_number):
    if not isinstance(data, dict):
        return ""

    def find_matching_articles(obj):
        matches = []

        if isinstance(obj, dict):
            number = str(obj.get("조문번호", "")).strip()

            if number.isdigit() and int(number) == article_number:
                matches.append(obj)

            for value in obj.values():
                matches.extend(find_matching_articles(value))

        elif isinstance(obj, list):
            for value in obj:
                matches.extend(find_matching_articles(value))

        return matches

    articles = find_matching_articles(data)

    for article in articles:
        title = clean_text(article.get("조문제목", ""))
        content = clean_text(article.get("조문내용", ""))

        paragraphs = article.get("항", [])
        paragraph_text = clean_text(paragraphs)

        if not content and not paragraph_text:
            continue

        # 조문내용에 제목이 이미 포함되어 있으면 중복 추가하지 않음
        text = content if content else title

        if paragraph_text:
            # 항 내용이 조문 본문에 포함되지 않았다면 추가
            if paragraph_text not in text:
                text = f"{text} {paragraph_text}"

        # 제목 중복 제거
        if title and text.startswith(title + " "):
            text = text[len(title) + 1:]

        # 항 번호 중복 제거
        text = re.sub(r"([①-⑳])\s*\1", r"\1", text)

        text = re.sub(r"\s+", " ", text).strip()

        # 장·절 제목이 아닌 조문인지 확인
        if re.match(r"^제\d+장", text):
            continue

        return text

    return ""


def find_law_id(law_name):
    data = search_laws(law_name)
    root = data.get("LawSearch", {})
    items = as_list(root.get("law", []))

    for item in items:
        if item.get("법령명한글") == law_name:
            return item.get("법령일련번호")

    return None


def get_case_root(data):
    if not isinstance(data, dict):
        return {}

    for key in ("PrecService", "판례"):
        root = data.get(key)
        if isinstance(root, dict):
            return root

    return data


def score_case(case_data, rule):
    """
    판시사항과 판결요지 중심으로 후보를 평가한다.
    키워드 일치만으로 법적 관련성이 확정되지는 않는다.
    """
    issue = clean_text(case_data.get("판시사항", ""))
    summary = clean_text(case_data.get("판결요지", ""))
    referenced = clean_text(case_data.get("참조조문", ""))

    # 판시사항 또는 판결요지가 없는 판례는 제외
    if not issue or not summary:
        return -1

    combined = issue + " " + summary

    # 제외 키워드가 핵심 쟁점에 있으면 제외
    for keyword in rule["exclude_keywords"]:
        if keyword in issue:
            return -1

    # 핵심 주제 키워드 점수
    issue_hits = sum(
        keyword in issue
        for keyword in rule["topic_keywords"]
    )

    summary_hits = sum(
        keyword in summary
        for keyword in rule["topic_keywords"]
    )

    score = issue_hits * 3 + summary_hits

    # 관련 조문이 참조조문에 있으면 가산점
    if rule["law"] and rule["article"] is not None:
        article_pattern = (
            rf"제{rule['article']}조(?!\d)"
        )

        if (
                rule["law"] in referenced
                and re.search(article_pattern, referenced)
        ):
            score += 5

    # 판시사항에서 주제가 확인되지 않으면 제외
    if issue_hits == 0:
        return -1

    # 일정 수준 이상인 경우만 후보로 인정
    return score if score >= 4 else -1


def find_relevant_case(query, rule):
    data = search_cases(query)
    root = data.get("PrecSearch", {})
    items = as_list(root.get("prec", []))

    best_case = None
    best_score = -1

    # 검색된 판례 중 최대 3개 상세 조회
    for item in items[:3]:
        case_id = item.get("판례일련번호")

        if not case_id:
            continue

        try:
            detail = get_case_detail(case_id)
            case_data = get_case_root(detail)

            score = score_case(case_data, rule)

            if score <= best_score:
                continue

            best_score = score
            best_case = {
                "name": clean_text(
                    case_data.get(
                        "사건명",
                        item.get("사건명", "")
                    )
                ),
                "case_number": clean_text(
                    case_data.get(
                        "사건번호",
                        item.get("사건번호", "")
                    )
                ),
                "id": case_id,
                "judgment_summary": clean_text(
                    case_data.get("판결요지", "")
                )[:1200],
                "issue": clean_text(
                    case_data.get("판시사항", "")
                )[:500],
                "match_score": score,
            }

        except Exception as e:
            print("판례 상세 조회 실패:", e)

    return best_case


def build_legal_explanation(title):
    rule = LEGAL_RULES.get(title)

    if not rule:
        return None

    result = {
        "law_name": rule["law"] or "검토 조문 미지정",
        "article_number": rule["article"],
        "article_text": "",
        "case": None,
        "risk_reason": rule["reason"],
        "verification_status": (
            "자동 검색된 법률 검토 자료"
            " (법적 관련성 미확정)"
        ),
    }

    # 1. 법률 조문 조회
    if rule["law"] and rule["article"] is not None:
        try:
            law_id = find_law_id(rule["law"])

            if law_id:
                data = get_law_article(
                    law_id,
                    rule["article"]
                )

                print(
                    "법령 조문 API 응답:",
                    json.dumps(data, ensure_ascii=False, indent=2)[:3000]
                )

                result["article_text"] = get_article_text(
                    data,
                    rule["article"]
                )

        except Exception as e:
            print("법률 조문 조회 실패:", e)

    # 2. 판례 검색 및 후보 평가
    try:
        result["case"] = find_relevant_case(
            rule["case_query"],
            rule,
        )
    except Exception as e:
        print("판례 검색 실패:", e)

    return result