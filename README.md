# 🏠 SafeRentAI

### AI 기반 임대차계약서 위험 분석 서비스

**SafeRentAI**는 임대차계약서 PDF를 분석하여 임차인에게 불리할 수 있는 계약 조항을 탐지하고, 관련 법령 및 판례를 제공하는 계약서 검토 지원 서비스입니다.

복잡한 법률 용어와 계약 조건을 보다 쉽게 이해하고, 계약 체결 전에 주의해야 할 사항을 확인할 수 있도록 돕습니다.

---

## 📌 Project Overview

임대차계약서에는 보증금 반환, 수선 의무, 계약 해지 등 임차인의 권리와 직접적으로 관련된 조항이 포함되어 있습니다.

그러나 법률 지식이 부족한 일반 사용자는 계약서에 포함된 불리한 조건을 쉽게 파악하기 어렵습니다.

SafeRentAI는 이러한 문제를 해결하기 위해 다음 기능을 제공합니다.

- 계약서 PDF 업로드 및 텍스트 추출
- 위험·주의 조항 자동 탐지
- 위험 수준에 따른 PDF 하이라이트
- 국가법령정보센터 API 기반 관련 법령·판례 조회
- 위험 조항별 법적 근거 및 검토 사항 제공
- 계약서 필수 항목 누락 여부 확인

## 🛠 Tech Stack

| Category | Technologies |
|---|---|
| Frontend | React, TypeScript, Vite |
| Backend | Java 17, Spring Boot |
| Analysis Core | Python, FastAPI |
| PDF Processing | PyMuPDF |
| Legal Data | 국가법령정보센터 Open API |
| AI Integration | OpenAI API (연동 개발 중) |
| Development Tools | Git, GitHub, VS Code, IntelliJ IDEA |

## ✨ Key Features

### 01. 계약서 PDF 분석

사용자가 업로드한 PDF에서 텍스트를 추출하고, 사전에 정의된 위험 탐지 규칙을 적용합니다.

- PDF 파일 형식 검증
- 최대 20MB, 100페이지 지원
- 계약서 텍스트 추출
- 정규표현식 기반 위험 조항 탐지

### 02. 위험 조항 자동 탐지

계약서에서 주의가 필요한 조항을 탐지하고 위험 수준을 분류합니다.

| 위험 수준 | 탐지 항목 |
|---|---|
| 🔴 위험 (Danger) | 보증금 반환 제한 |
| 🔴 위험 (Danger) | 임대인의 임의 출입 |
| 🟡 주의 (Warning) | 과도한 수선비 부담 |
| 🟡 주의 (Warning) | 일방적인 계약 해지 |
| 🟡 주의 (Warning) | 관리비 변경 재량 |

탐지된 조항에 대해서는 위험 사유와 수정·확인 권고사항을 제공합니다.

### 03. PDF 위험 조항 하이라이트

위험 조항을 원본 PDF에서 시각적으로 표시합니다.

- 🔴 빨간색: 위험 조항
- 🟡 노란색: 주의 조항

사용자는 분석 결과와 계약서 원문을 함께 확인할 수 있습니다.

### 04. 법령 및 판례 연동

국가법령정보센터 API를 활용하여 탐지된 조항과 관련된 법률 자료를 조회합니다.

- 관련 법령 검색
- 관련 판례 검색
- 법적 근거 설명
- 위험 사유 및 확인 사항 제공

검색 결과는 참고 자료이며, 특정 계약 조항의 위법성을 확정하는 법률 판단은 아닙니다.

### 05. 필수 계약 항목 확인

계약서에서 다음 항목의 기재 여부를 확인합니다.

- 보증금
- 월세 또는 차임
- 계약기간
- 관리비 및 세부 항목
- 임대인·임차인
- 목적물 주소

누락 가능성이 있는 항목은 별도로 안내합니다.

## 🏗 System Architecture

```text
                   User
                     |
                     v
          +---------------------+
          |      Frontend       |
          |   React / Vite      |
          |      :5173          |
          +---------------------+
                     |
                     | HTTP Request
                     v
          +---------------------+
          |       Backend       |
          |     Spring Boot     |
          |       :8081         |
          +---------------------+
                     |
                     | Internal API
                     v
          +---------------------+
          |    Analysis Core    |
          |       FastAPI       |
          |       :8001         |
          +---------------------+
                     |
             +-------+-------+
             |               |
             v               v
       PDF Analysis     Legal Data API
        PyMuPDF         국가법령정보센터
             |               |
             +-------+-------+
                     |
                     v
              Analysis Result
                     |
                     v
                  Frontend
```

## 📂 Project Structure

```text
SafeRentAI/
├── frontend/           # React + TypeScript UI
├── backend/            # Spring Boot REST API
├── core/               # FastAPI PDF 분석 및 법령 연동
│   └── app/
│       ├── main.py
│       ├── law_api.py
│       ├── legal_reasoning.py
│       └── llm_analysis.py
├── .gitignore
└── README.md
```

## 🚀 Getting Started

### 1. Clone Repository

```bash
git clone https://github.com/ddubi0521/SafeRentAI.git
cd SafeRentAI
```

### 2. Run Analysis Core

Python 및 Poetry가 설치되어 있어야 합니다.

```powershell
cd core

poetry install

$env:CORE_SHARED_TOKEN = "your-local-core-token"
$env:LAW_API_OC = "your-law-api-id"

poetry run uvicorn app.main:app --reload --port 8001
```

Core 상태 확인:

`http://localhost:8001/health`

### 3. Run Backend

별도의 터미널에서 실행합니다.

```powershell
cd backend

$env:CORE_SHARED_TOKEN = "your-local-core-token"
$env:CORE_BASE_URL = "http://127.0.0.1:8001"
$env:LOCAL_DEV_NO_AUTH = "true"

.\gradlew.bat bootRun
```

`CORE_SHARED_TOKEN`은 Core와 Backend에서 동일하게 설정해야 합니다.

`LOCAL_DEV_NO_AUTH`는 로컬 개발 환경에서만 사용합니다.

### 4. Run Frontend

별도의 터미널에서 실행합니다.

```powershell
cd frontend

npm install
npm run dev
```

브라우저에서 다음 주소에 접속합니다.

`http://localhost:5173`

## 🔄 Analysis Workflow

1. 사용자가 임대차계약서 PDF 업로드
2. Frontend에서 Backend로 분석 요청
3. Backend에서 FastAPI Core로 파일 전달
4. PyMuPDF로 PDF 텍스트 추출
5. 위험 조항 탐지 및 필수 항목 확인
6. 관련 법령·판례 검색 및 법적 근거 분석
7. 원본 PDF에 위험 조항 하이라이트
8. 분석 결과를 Frontend에 표시

## 📈 Future Improvements

- [ ] LLM 기반 위험 조항 상세 분석 활성화
- [ ] 계약서 위험도 종합 점수 제공
- [ ] 위험 조항별 수정 문구 추천
- [ ] 이미지 기반 스캔 PDF OCR 지원
- [ ] 계약서 분석 결과 리포트 기능 확장
- [ ] 위험 조항 탐지 규칙 및 적용 범위 확대

## ⚠️ Disclaimer

SafeRentAI는 계약서 검토를 지원하기 위한 프로젝트로, 전문적인 법률 자문을 대체하지 않습니다.

분석 결과는 참고용이며, 탐지되지 않은 조항이 반드시 안전하다는 의미는 아닙니다. 실제 계약 체결 전에는 최신 법령, 등기부등본, 선순위 권리관계 등을 별도로 확인해야 합니다.

---

**SafeRentAI — 더 안전한 임대차계약을 위한 스마트 계약서 분석 서비스.**