import os
import requests

BASE_URL = "https://www.law.go.kr/DRF"

def request_api(endpoint, params):
    oc = os.getenv("LAW_API_OC")

    if not oc:
        raise ValueError("LAW_API_OC가 설정되지 않았습니다.")

    params["OC"] = oc
    params["type"] = "JSON"

    response = requests.get(
        f"{BASE_URL}/{endpoint}",
        params=params,
        timeout=20
    )
    response.raise_for_status()

    try:
        return response.json()
    except ValueError:
        raise ValueError(
            "JSON 응답을 받지 못했습니다. "
            f"응답 앞부분: {response.text[:300]}"
        )

def search_laws(query="주택임대차보호법"):
    return request_api("lawSearch.do", {
        "target": "law",
        "query": query,
        "search": 1,
        "display": 10
    })

def search_cases(query="임대차보증금"):
    return request_api("lawSearch.do", {
        "target": "prec",
        "query": query,
        "search": 2,
        "display": 10,
        "org": "400201",  # 대법원 판례만 검색
    })

def get_case_detail(case_id):
    return request_api("lawService.do", {
        "target": "prec",
        "ID": case_id
    })

# 법령 조문 조회 기능
def get_law_article(law_id, article_number):
    # JO는 조 번호 4자리 + 가지번호 2자리
    jo = f"{int(article_number):04d}00"

    return request_api("lawService.do", {
        "target": "lawjosub",
        "MST": str(law_id),
        "JO": jo,
    })