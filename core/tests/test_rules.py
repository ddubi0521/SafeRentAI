from app.main import analyze_text

def test_risk_and_missing():
    findings, missing=analyze_text(["임대인과 임차인. 보증금은 임대인이 임의로 연기 가능. 모든 수리비는 임차인 부담."])
    assert any(x.title == "과도한 수선비 부담" for x in findings)
    assert "계약기간" in missing

def test_no_fabricated_legal_conclusion():
    findings, _=analyze_text(["계약기간 관리비 보증금 월세 소재지 임대인 임차인"])
    assert findings == []
