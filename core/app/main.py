import time
import base64
import io
import json
import os
import re
from typing import Literal

import fitz
from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from app.law_api import search_laws, search_cases
from app.legal_reasoning import build_legal_explanation # 법적 근거 분석
from app.llm_analysis import analyze_with_llm # OpenAPI 설정
from concurrent.futures import ThreadPoolExecutor

app = FastAPI(title="SafeRent Core", version="1.0.0")
print("[서버 확인] 실행 파일:", __file__, flush=True)
MAX_FILE = 20 * 1024 * 1024

class Finding(BaseModel):
    severity: Literal["danger", "warning"]
    title: str
    quote: str
    reason: str
    recommendation: str
    legal_basis: str = "법률 전문가 및 최신 공식 자료 확인 필요"
    page: int | None = None
    highlighted: bool = False

    # 관련 법령 및 판례
    related_laws: list[dict] = Field(default_factory=list)
    related_cases: list[dict] = Field(default_factory=list)
    
    # 법적 근거 분석
    legal_explanation: dict | None = None
    
    # OpenAPI 설정
    llm_analysis: dict | None = None

class Analysis(BaseModel):
    filename: str
    findings: list[Finding] = Field(default_factory=list)
    missing_checks: list[str] = Field(default_factory=list)
    extracted_chars: int
    annotated_pdf_base64: str
    references_status: str
    disclaimer: str

# 탐지 규칙은 법적 위법성 확정 판정이 아닌 확인 신호임.
RULES = [
    ("danger", "보증금 반환 제한", r"(?:보증금.{0,30}(?:반환하지|반환을 거절|몰수)|반환.{0,20}(?:임대인.{0,10}재량|임의로 연기))", "보증금 반환이 일방적으로 제한될 가능성이 있습니다.", "반환 사유와 기한을 구체화하고 전문가에게 검토받으세요."),
    ("warning", "과도한 수선비 부담", r"(?:모든|일체의).{0,12}(?:수리비|수선비|보수비).{0,15}(?:임차인|세입자).{0,8}부담", "수선 책임을 일괄적으로 임차인에게 전가하는 표현입니다.", "노후·구조적 하자 등 원인별 수선 책임을 명확히 구분하세요."),
    ("danger", "임대인의 임의 출입", r"(?:임대인|집주인).{0,20}(?:사전 동의 없이|동의 없이|언제든).{0,15}(?:출입|방문)", "임차인의 주거 평온을 침해할 우려가 있습니다.", "긴급 상황 외에는 사전 협의와 동의를 요구하도록 수정하세요."),
    ("warning", "일방적인 계약 해지", r"(?:임대인.{0,15}(?:언제든|일방적으로).{0,10}(?:해지|종료)|임차인.{0,15}(?:중도해지 불가|해지할 수 없다))", "해지 권한이 일방에 불리하게 설정되었을 수 있습니다.", "법령상 해지 사유 및 통지 기간과 비교 검토하세요."),
    ("warning", "관리비 변경 재량", r"(?:관리비.{0,18}(?:임대인 재량|임의로 인상|일방적으로 인상))", "관리비 산정 근거 및 변경 요건이 불분명할 수 있습니다.", "관리비 항목과 인상 기준 및 통지 방법을 명시하세요."),
]
CHECKS = [
    ("보증금", r"보증금"),
    ("월세 또는 차임", r"월세|차임|임대료"),
    ("계약기간", r"계약기간|임대차기간|임대기간"),
    ("관리비 및 세부 항목", r"관리비"),
    ("임대인·임차인", r"임대인.{0,100}임차인|임차인.{0,100}임대인"),
    ("목적물 주소", r"소재지|임대차목적물|주택의 표시"),
]
LEGAL_QUERIES = {
    "보증금 반환 제한": {
        "law": "주택임대차보호법",
        "case": "임대차보증금 반환"
    },
    "과도한 수선비 부담": {
        "law": "민법",
        "case": "임대인 수선의무"
    },
    "임대인의 임의 출입": {
        "law": "주택임대차보호법",
        "case": "임대인 무단출입"
    },
    "일방적인 계약 해지": {
        "law": "주택임대차보호법",
        "case": "임대차계약 해지"
    },
    "관리비 변경 재량": {
        "law": "주택임대차보호법",
        "case": "임대차 관리비"
    }
}

def check_token(token: str | None) -> None:
    expected = os.getenv("CORE_SHARED_TOKEN")
    if not expected or token != expected:
        raise HTTPException(401, "Core 인증 실패: CORE_SHARED_TOKEN 설정과 x-core-token 헤더를 확인하세요")

def extract_pages(doc: fitz.Document) -> list[str]:
    pages = [p.get_text(sort=True) for p in doc]
    if sum(len(s.strip()) for s in pages) < 30:
        raise HTTPException(422, "텍스트가 없는 스캔 PDF입니다. OCR 후 다시 업로드해 주세요. 이미지 OCR은 현재 버전에 포함되지 않습니다.")
    return pages

def analyze_text(pages: list[str]) -> tuple[list[Finding],list[str]]:
    findings = []
    for idx, text in enumerate(pages):
        for severity, title, pattern, reason, recommendation in RULES:
            for m in list(re.finditer(pattern, text, re.IGNORECASE))[:5]:
                findings.append(Finding(severity=severity,title=title,quote=m.group(0),reason=reason,recommendation=recommendation,page=idx+1))
    all_text = "\n".join(pages)
    missing = [name for name, pattern in CHECKS if not re.search(pattern, all_text, re.I)]
    return findings, missing

# 법적 근거 분석
def attach_legal_explanations(findings):
    titles = list(dict.fromkeys(
        finding.title for finding in findings
    ))

    if not titles:
        return findings

    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(
            executor.map(build_legal_explanation, titles)
        )

    cache = dict(zip(titles, results))

    for finding in findings:
        finding.legal_explanation = cache.get(finding.title)

    return findings

def attach_legal_references(findings: list[Finding]):
    """위험 조항에 관련 법령 및 판례 검색 결과 연ㅁ결"""

    cache = {}

    for finding in findings:
        query = LEGAL_QUERIES.get(finding.title)

        if not query:
            continue

        if finding.title not in cache:
            laws = []
            cases = []

            try:
                law_data = search_laws(query["law"])
                root = law_data.get("LawSearch", {})
                items = root.get("law", [])

                if isinstance(items, dict):
                    items = [items]

                target_law = query["law"]

                for item in items:
                    law_name = item.get("법령명한글", "")

                    if law_name == target_law or law_name.startswith(target_law + " 시행"):
                        laws.append({
                            "name": law_name,
                            "id": item.get("법령일련번호", "")
                        })

                    if len(laws) >= 3:
                        break

            except Exception as e:
                print("법령 API 오류:", e)

            try:
                case_data = search_cases(query["case"])
                root = case_data.get("PrecSearch", {})
                items = root.get("prec", [])

                if isinstance(items, dict):
                    items = [items]

                for item in items[:3]:
                    cases.append({
                        "name": item.get("사건명", ""),
                        "case_number": item.get("사건번호", ""),
                        "id": item.get("판례일련번호", ""),
                    })

            except Exception as e:
                print("판례 API 오류:", e)

            cache[finding.title] = (laws, cases)

        finding.related_laws = cache[finding.title][0]
        finding.related_cases = cache[finding.title][1]

    return findings

# OpenAPI 설정
def attach_llm_analyses(findings):
    cache = {}
    tasks = {}

    # 1. 분석이 필요한 조항 수집
    for finding in findings:
        explanation = finding.legal_explanation

        if not explanation:
            continue

        key = (finding.title, finding.quote)

        # 동일한 조항 중복 분석 방지
        if key not in tasks:
            tasks[key] = (
                finding.quote,
                explanation,
            )

    if not tasks:
        return findings

    # 2. GPT 분석 함수
    def run_analysis(task):
        key, (quote, explanation) = task

        try:
            result = analyze_with_llm(
                quote,
                explanation,
            )
            return key, result

        except Exception as e:
            print(
                "[GPT 위험 분석 실패]",
                str(e),
                flush=True,
            )
            return key, None

    # 3. 최대 3개 조항 병렬 분석
    with ThreadPoolExecutor(max_workers=3) as executor:
        results = executor.map(
            run_analysis,
            tasks.items(),
        )

        for key, result in results:
            cache[key] = result

    # 4. 기존 findings에 결과 연결
    for finding in findings:
        key = (finding.title, finding.quote)

        if key in cache:
            finding.llm_analysis = cache[key]

    return findings

def highlight(doc: fitz.Document, findings: list[Finding]) -> bytes:
    for f in findings:
        if not f.page or not f.quote:
            continue
        page = doc[f.page - 1]
        rects = page.search_for(f.quote)
        # 긴 줄/텍스트 추출 과정에서 공백이 달라진 경우에는 표시를 생략하고 별도 보고
        for rect in rects[:10]:
            mark = page.add_highlight_annot(rect)
            mark.set_colors(stroke=(1, .18, .18) if f.severity == 'danger' else (1, .78, .08))
            mark.update(opacity=.4)
            f.highlighted = True
    return doc.tobytes(garbage=4, deflate=True)

@app.get('/health')
def health():
    return {'status':'UP'}

@app.post('/internal/analyze',response_model=Analysis)
async def analyze(file: UploadFile = File(...), x_core_token: str | None = Header(None)):
    check_token(x_core_token)
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(415, 'PDF 파일만 지원합니다')
    raw = await file.read(MAX_FILE+1)
    if len(raw)>MAX_FILE:
        raise HTTPException(413, '최대 20MB PDF만 지원합니다')
    if not raw.startswith(b'%PDF-'):
        raise HTTPException(415, 'PDF 시그니처가 올바르지 않습니다')
    try:
        doc = fitz.open(stream=raw,filetype='pdf')
        if doc.is_encrypted:
            raise HTTPException(422,'암호화 PDF는 지원하지 않습니다')
        if len(doc)>100:
            raise HTTPException(413,'100페이지 이하만 지원합니다')
        pages=extract_pages(doc)
        findings,missing=analyze_text(pages)
        pdf=highlight(doc,findings)
        doc.close()
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(422,'PDF 분석 실패: 파일 형식을 확인하세요')

    t0 = time.perf_counter()

    findings = attach_legal_references(findings)
    t1 = time.perf_counter()
    print(f"[시간] 법령·판례 검색: {t1-t0:.2f}초", flush=True)

    findings = attach_legal_explanations(findings) # 법적 근거 분석
    t2 = time.perf_counter()
    print(f"[시간] 판례 검증 및 법률 설명: {t2-t1:.2f}초", flush=True)

    findings = attach_llm_analyses(findings) # OpenAPI 설정
    t3 = time.perf_counter()
    print(f"[시간] GPT 위험 분석: {t3-t2:.2f}초", flush=True)

    print(f"[시간] 세 단계 합계: {t3-t0:.2f}초", flush=True)


    return Analysis(filename=file.filename,findings=findings,missing_checks=missing,
        extracted_chars=sum(map(len,pages)),annotated_pdf_base64=base64.b64encode(pdf).decode(),
        references_status='국가법령정보센터 법령·판례 검색 API 연동 완료. 검색 결과는 참고 자료이며 실제 조항에 대한 법적 적용 여부는 별도 검토가 필요합니다.',
        disclaimer='법률 자문 또는 계약 안전성 보증이 아닙니다. 미탐지 조항이 안전하다는 의미가 아니며, 최신 법령·등기부·선순위 권리는 별도 확인하세요.')


@app.get("/api/laws")
def get_laws(query: str = "주택임대차보호법"):
    try:
        return search_laws(query)
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="법령 검색 API 호출 실패"
        )

@app.get("/api/cases")
def get_cases(query: str = "임대차보증금"):
    try:
        return search_cases(query)
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="판례 검색 API 호출 실패"
        )

