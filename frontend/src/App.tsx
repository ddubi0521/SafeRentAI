import {useState} from 'react';
import {FileCheck2, ShieldCheck, UploadCloud, AlertCircle, Download} from 'lucide-react';

type LegalReference = {
    name: string;
    id?: string | number;
    case_number?: string;
};

// 법적 근거 분석 결과 표시
type LegalExplanation = {
    law_name: string;
    article_number: number | null;
    article_text: string;
    case: {
        name: string;
        case_number: string;
        id: string | number;
        judgment_summary: string;
        issue: string;
        match_score: number;
    } | null;
    risk_reason: string;
    verification_status: string;
};

// OpenAI 설정
type LLMAnalysis = {
    case_summary: string;
    risk_analysis: string;
    limitations: string;
};

type Finding = {
    severity: 'danger' | 'warning';
    title: string;
    quote: string;
    reason: string;
    recommendation: string;
    page: number | null;
    highlighted: boolean;
    legal_basis: string;

    // 국가법령정보센터 검색 결과
    related_laws?: LegalReference[];
    related_cases?: LegalReference[];

    // 법적 근거 분석 결과
    legal_explanation?: LegalExplanation | null;

    // OpenAPI 설정
    llm_analysis?: LLMAnalysis | null;
};

type Result = {
    filename: string;
    findings: Finding[];
    missing_checks: string[];
    annotated_pdf_base64: string;
    references_status: string;
    disclaimer: string;
    extracted_chars: number
};
export default function App() {
    const [file, setFile] = useState<File | null>(null), [loading, setLoading] = useState(false), [result, setResult] = useState<Result | null>(null), [error, setError] = useState('');
    const [jwt, setJwt] = useState('');

    async function analyze() {
        if (!file) return;
        setLoading(true);
        setError('');
        setResult(null);
        try {
            const data = new FormData();
            data.append('file', file);
            const res = await fetch('/api/tools/safe-rent/analyze', {
                method: 'POST',
                headers: jwt ? {'Authorization': `Bearer ${jwt}`} : {},
                body: data
            });
            const body = await res.json();
            if (!res.ok) throw new Error(body?.payload?.message || '분석 실패');
            setResult(body.data as Result);
        } catch (e) {
            setError(e instanceof Error ? e.message : '알 수 없는 오류')
        } finally {
            setLoading(false)
        }
    }

    function download() {
        if (!result) return;
        const raw = atob(result.annotated_pdf_base64);
        const array = Uint8Array.from(raw, c => c.charCodeAt(0));
        const url = URL.createObjectURL(new Blob([array], {type: 'application/pdf'}));
        const a = document.createElement('a');
        a.href = url;
        a.download = 'saferent-annotated.pdf';
        a.click();
        URL.revokeObjectURL(url)
    }

    return <div className="shell">
        <header>
            <div className="logo"><ShieldCheck size={24}/> SafeRent <strong>AI</strong></div>
            <div className="subtitle">임대차 계약서 위험 신호 사전 점검</div>
        </header>
        <main>
            <section className="hero">
                <span className="eyebrow">CONTRACT REVIEW</span>
                <h1>계약하기 전에,<br/>위험한 특약을 확인하세요.</h1>
                <p>PDF 계약서를 업로드하면 위험·주의 문구와 확인이 필요한 항목을 표시합니다.</p>
                <div className="notice">
                    <AlertCircle size={17}/>
                    규칙 기반 위험 조항 탐지와 국가법령정보센터 법령·판례 검색을 지원합니다.
                    검색 결과는 법적 판단이 아닌 참고 자료입니다.
                </div>
            </section>
            <section className="panel">
                <div className="sectionhead">
                    <h2>계약서 업로드</h2>
                    <span>PDF · 최대 20MB</span>
                </div>
                <label className="drop">
                    <UploadCloud size={36}/>
                    <b>{file ? file.name : '여기를 클릭해 PDF 계약서 선택'}</b>
                    <small>스캔본은 텍스트 OCR 처리 후 업로드해 주세요.</small>
                    <input type="file" accept="application/pdf,.pdf" onChange={e => setFile(e.target.files?.[0] || null)}/>
                </label>
                <label className="token">JWT 액세스 토큰 (운영 인증 사용 시)
                    <input type="password" value={jwt} onChange={e => setJwt(e.target.value)} placeholder="로컬 개발 모드에서는 비워두세요"/></label>
                <button disabled={!file || loading} onClick={analyze}>{loading ? '분석 중...' : '계약서 안전 분석 시작'}</button>
                {error && <div className="error">{error}</div>}
            </section>
            {result && <section className="panel results">
                <div className="sectionhead"><h2><FileCheck2 size={21}/> 분석 결과</h2>
                    <button className="secondary" onClick={download}><Download size={17}/> 표시된 PDF 받기</button>
                </div>
                <div className="stats">
                    <div><strong>{result.findings.filter(f => f.severity === 'danger').length}</strong><span>위험</span>
                    </div>
                    <div><strong>{result.findings.filter(f => f.severity === 'warning').length}</strong><span>주의</span>
                    </div>
                    <div><strong>{result.missing_checks.length}</strong><span>미확인 항목</span></div>
                </div>
                {result.findings.length === 0 ?
                    <p>사전 정의된 위험 문구가 발견되지 않았습니다. 안전하다는 의미는 아닙니다.</p> : result.findings.map((f, i) => <article key={i} className={'finding ' + f.severity}>
                        <div className="row">
                            <b>{f.title}</b>
                            <span className={'chip ' + f.severity}>{f.severity === 'danger' ? '위험' : '주의'}</span>
                        </div>
                        <blockquote>{f.quote}</blockquote>
                        <p>{f.reason}</p>
                        <p><b>권고:</b> {f.recommendation}</p>
                        <small>{f.page}페이지 · 원문 표시 {f.highlighted ? '성공' : '실패(텍스트 배치 확인 필요)'}</small>
                        {/* 관련 법령 */}
                        {(f.related_laws?.length ?? 0) > 0 && (
                            <div className="legal-section">
                                <h4>📘 관련 법령 검색 결과</h4>
                                <ul>
                                    {f.related_laws!.map((law, index) => (
                                        <li key={index}>
                                            <b>{law.name}</b>
                                            {law.id != null && (
                                                <span> (법령 ID: {law.id})</span>
                                            )}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        {/* 법적 근거 분석 */}
                        {f.legal_explanation && (
                            <div className="legal-section">
                                <h4>⚖️ 법적 근거 분석</h4>

                                <p>
                                    <b>① 위험 조항</b>
                                </p>
                                <blockquote>{f.quote}</blockquote>

                                <p>
                                    <b>② 관련 법률 조문</b>
                                </p>
                                <p>
                                    {f.legal_explanation.law_name}
                                    {f.legal_explanation.article_number != null &&
                                        ` 제${f.legal_explanation.article_number}조`}
                                </p>

                                {f.legal_explanation.article_text ? (
                                    <p>{f.legal_explanation.article_text}</p>
                                ) : (
                                    <p>조문 원문을 확인하지 못했습니다.</p>
                                )}

                                <p>
                                    <b>③ 관련 판례의 판단 내용</b>
                                </p>

                                {f.legal_explanation.case ? (
                                    <>
                                        <p>
                                            {f.legal_explanation.case.name}
                                            {' ('}
                                            {f.legal_explanation.case.case_number}
                                            {')'}
                                        </p>

                                        <p>
                                            {f.legal_explanation.case.judgment_summary}
                                        </p>
                                    </>
                                ) : (
                                    <p>관련 판례의 판단 내용을 확인하지 못했습니다.</p>
                                )}


                                <p><b>④ 위험한 이유</b></p>

                                {f.llm_analysis ? (
                                    <>
                                        <p>{f.llm_analysis.risk_analysis}</p>

                                        {f.llm_analysis.case_summary && (
                                            <>
                                                <p><b>⑤ AI 판례 핵심 요약</b></p>
                                                <p>{f.llm_analysis.case_summary}</p>
                                            </>
                                        )}

                                        {f.llm_analysis.limitations && (
                                            <>
                                                <p><b>⑥ 추가 확인 사항</b></p>
                                                <p>{f.llm_analysis.limitations}</p>
                                            </>
                                        )}

                                        <small>
                                            AI가 검색된 법률·판례를 바탕으로
                                            생성한 참고용 설명입니다.
                                        </small>
                                    </>
                                ) : (
                                    <p>
                                        {f.legal_explanation.risk_reason}
                                        <small> (규칙 기반 분석)</small>
                                    </p>
                                )}

                                <small>
                                    {f.legal_explanation.verification_status}
                                    {' · '}
                                    실제 법적 적용 여부는 별도 검토가 필요합니다.
                                </small>
                            </div>
                        )}
                    </article>)}
                <h3>계약서에서 확인되지 않은 항목</h3>{result.missing_checks.length ?
                <ul>{result.missing_checks.map(x => <li key={x}>{x}</li>)}</ul> :
                <p>기본 확인 항목의 키워드가 모두 발견되었습니다. 조항의 적정성은 별도 검토가 필요합니다.</p>}
                <div className="notice">{result.references_status}<br/>{result.disclaimer}</div>
            </section>}</main>
        <footer>SafeRent AI · 법률 자문 서비스가 아닌 사전 점검 도구</footer>
    </div>
}
