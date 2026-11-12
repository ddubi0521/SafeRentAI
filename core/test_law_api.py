from app.law_api import (
    search_laws,
    search_cases,
    get_case_detail,
)

import json


def show_result(data):
    print(json.dumps(
        data,
        ensure_ascii=False,
        indent=2
    )[:3000])


# ==============================
# TEST 1. 법령 검색
# ==============================
print("\n===== TEST 1: 법령 검색 =====")

try:
    laws = search_laws("주택임대차보호법")
    show_result(laws)

    total = int(laws.get("LawSearch", {}).get("totalCnt", 0))
    print(f"\n검색된 법령 수: {total}")

    if total > 0:
        print("TEST 1 성공")
    else:
        print("TEST 1 검색 결과 없음")

except Exception as e:
    print("TEST 1 실패:", e)


# ==============================
# TEST 2. 판례 검색
# ==============================
print("\n===== TEST 2: 판례 검색 =====")

case_id = None

try:
    cases = search_cases("임대차보증금")
    show_result(cases)

    root = cases.get("PrecSearch", {})
    total = int(root.get("totalCnt", 0))

    print(f"\n검색된 판례 수: {total}")

    if total > 0:
        print("TEST 2 성공")

        items = root.get("prec", [])

        if isinstance(items, dict):
            items = [items]

        if items:
            case_id = items[0].get("판례일련번호")
            print("첫 번째 판례 ID:", case_id)
    else:
        print("TEST 2 검색 결과 없음")

except Exception as e:
    print("TEST 2 실패:", e)



# ==============================
# TEST 3. 판례 상세 본문 조회
# ==============================
print("\n===== TEST 3: 판례 상세 조회 =====")

if case_id:
    try:
        detail = get_case_detail(case_id)
        show_result(detail)

        if isinstance(detail, dict) and isinstance(
                detail.get("PrecService"), dict
        ):
            record = detail["PrecService"]
        else:
            record = detail

        if (
                isinstance(record, dict)
                and (
                record.get("판례내용")
                or record.get("판결요지")
                or record.get("판시사항")
        )
        ):
            print("TEST 3 성공: 판례 상세 내용 확인")
        else:
            print("TEST 3 실패: 판례 상세 내용 없음")
            print("응답:", detail)

    except Exception as e:
        print("TEST 3 실패:", e)
else:
    print("TEST 3 건너뜀: 판례 ID 없음")

