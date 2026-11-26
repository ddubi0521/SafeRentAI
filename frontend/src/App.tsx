import {useEffect, useRef, useState} from 'react';
import {FileCheck2, ShieldCheck, UploadCloud, AlertCircle, Download, ChevronDown, FileText, CheckCircle2, Clock3, Sparkles, SearchCheck} from 'lucide-react';

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
        relevance?: 'direct' | 'indirect';
        relevance_reason?: string;
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
    const [filter, setFilter] = useState<'all' | 'danger' | 'warning'>('all');
    const [elapsedSeconds, setElapsedSeconds] = useState(0);
    const [lastDurationSeconds, setLastDurationSeconds] = useState<number | null>(null);
    const [estimatedSeconds, setEstimatedSeconds] = useState<number | null>(() => {
        try {
            const raw = localStorage.getItem('saferent-analysis-times-v1');
            const times: number[] = raw ? JSON.parse(raw) : [];
            const valid = Array.isArray(times) ? times.filter(t => typeof t === 'number' && Number.isFinite(t) && t > 0) : [];
            return valid.length ? Math.round(valid.reduce((a, b) => a + b, 0) / valid.length) : null;
        } catch { return null; }
    });
    const startedAtRef = useRef<number | null>(null);

    useEffect(() => {
        if (!loading) return;
        const tick = () => {
            if (startedAtRef.current !== null) {
                setElapsedSeconds(Math.floor((Date.now() - startedAtRef.current) / 1000));
            }
        };
        tick();
        const interval = window.setInterval(tick, 1000);
        return () => window.clearInterval(interval);
    }, [loading]);

    const formatDuration = (seconds: number) => {
        const minutes = Math.floor(seconds / 60);
        const remaining = seconds % 60;
        return minutes > 0 ? `${minutes}분 ${remaining}초` : `${remaining}초`;
    };


    async function analyze() {
        if (!file) return;
        startedAtRef.current = Date.now();
        setElapsedSeconds(0);
        setLastDurationSeconds(null);
        setLoading(true);
        setError('');
        setResult(null);
        setFilter('all');
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
            const duration = Math.max(1, Math.round((Date.now() - startedAtRef.current!) / 1000));
            setLastDurationSeconds(duration);
            try {
                const raw = localStorage.getItem('saferent-analysis-times-v1');
                const oldTimes: number[] = raw ? JSON.parse(raw) : [];
                const valid = Array.isArray(oldTimes) ? oldTimes.filter(t => typeof t === 'number' && Number.isFinite(t) && t > 0) : [];
                const nextTimes = [...valid.slice(-4), duration];
                localStorage.setItem('saferent-analysis-times-v1', JSON.stringify(nextTimes));
                setEstimatedSeconds(Math.round(nextTimes.reduce((a, b) => a + b, 0) / nextTimes.length));
            } catch { /* 저장이 차단된 환경에서는 이번 소요 시간만 표시 */ }
        } catch (e) {
            setError(e instanceof Error ? e.message : '알 수 없는 오류')
        } finally {
            setLoading(false)
        }
    }

    function download() {
        if (!result) return;
        if (!result.annotated_pdf_base64) return;
        const raw = atob(result.annotated_pdf_base64);
        const array = Uint8Array.from(raw, c => c.charCodeAt(0));
        const url = URL.createObjectURL(new Blob([array], {type: 'application/pdf'}));
        const a = document.createElement('a');
        a.href = url;
        a.download = 'saferent-annotated.pdf';
        a.click();
        window.setTimeout(() => URL.revokeObjectURL(url), 1000)
    }

    const dangerCount = result?.findings.filter(f => f.severity === 'danger').length ?? 0;
    const warningCount = result?.findings.filter(f => f.severity === 'warning').length ?? 0;
    const visibleFindings = result?.findings.filter(f => filter === 'all' || f.severity === filter) ?? [];

    return <div className="shell">
        <header>
            <div className="logo"><ShieldCheck size={24}/> SafeRent <strong>AI</strong></div>
            <div className="subtitle">더 안전한 계약을 위한 사전 점검</div>
        </header>
        <main>
            <section className="hero">
                <span className="eyebrow"><Sparkles size={14}/> SMART CONTRACT REVIEW</span>
                <h1>계약하기 전에,<br/>위험한 특약을 확인하세요.</h1>
                <p>계약서의 위험한 특약을 찾아주고, 관련 법률과 판례를 바탕으로 확인할 내용을 정리해 드려요.</p>
                <div className="notice">
                    <AlertCircle size={17}/>
                    규칙 및 AI 기반 위험 조항 탐지와 국가법령정보센터 법령·판례 검색을 지원합니다.
                    검색 결과는 법적 판단이 아닌 참고 자료입니다.
                </div>
            </section>
            <section className="panel">
                <div className="sectionhead">
                    <h2><UploadCloud size={21}/> 계약서 업로드</h2>
                    <span>PDF · 최대 20MB</span>
                </div>
                <label className="drop">
                    <UploadCloud size={36}/>
                    <b>{file ? file.name : '분석할 PDF 계약서를 선택해 주세요'}</b>
                    <small>{file ? `${(file.size / 1024 / 1024).toFixed(2)} MB · 다른 파일을 선택하려면 클릭` : '클릭해서 파일 선택 · PDF 최대 20MB · 스캔본은 OCR 처리 후 업로드'}</small>
                    <input type="file" accept="application/pdf,.pdf" onChange={e => setFile(e.target.files?.[0] || null)}/>
                </label>
                <label className="token">JWT 액세스 토큰 (운영 인증 사용 시)
                    <input type="password" value={jwt} onChange={e => setJwt(e.target.value)} placeholder="로컬 개발 모드에서는 비워두세요"/></label>
                <button disabled={!file || loading} onClick={analyze} className="sr-primary-action">{loading ? <><Clock3 size={18}/> 계약서 분석 중...</> : <><SearchCheck size={18}/> 계약서 위험 분석 시작</>}</button>
                {loading && (
                    <div className="sr-progress" role="status" aria-live="off">
                        <div className="sr-progress-top">
                            <strong>계약서를 분석하고 있어요</strong>
                            <span>경과 {formatDuration(elapsedSeconds)}</span>
                        </div>
                        <div className="sr-progress-track"><div className="sr-progress-indeterminate" /></div>
                        {estimatedSeconds === null ? (
                            <p>첫 분석이라 예상 시간을 계산 중이에요. 완료 후 다음 분석부터 예상 시간이 표시됩니다.</p>
                        ) : elapsedSeconds < estimatedSeconds ? (
                            <p>이전 분석 평균 {formatDuration(estimatedSeconds)} · 예상 남은 시간 약 {formatDuration(estimatedSeconds - elapsedSeconds)}</p>
                        ) : (
                            <p>이전 분석 평균 {formatDuration(estimatedSeconds)}을 지났어요. 계속 분석 중이며 곧 완료된다는 보장은 없어요.</p>
                        )}
                        <small>실제 서버 진행률이 아닌 과거 분석 시간 기반 추정치예요.</small>
                    </div>
                )}
                {!loading && result && lastDurationSeconds !== null && (
                    <div className="sr-completed-time"><CheckCircle2 size={16}/> 분석 완료 · 총 {formatDuration(lastDurationSeconds)} 소요</div>
                )}
                {error && <div className="error">{error}</div>}
            </section>
            {result && <section className="panel results" aria-label="계약서 분석 결과">
                <div className="sr-report-head">
                    <div>
                        <span className="eyebrow">ANALYSIS REPORT</span>
                        <h2><FileCheck2 size={24}/> 계약서 분석 결과</h2>
                        <p className="sr-report-file"><FileText size={15}/> {result.filename}</p>
                    </div>
                    <button className="secondary sr-download" onClick={download} disabled={!result.annotated_pdf_base64}>
                        <Download size={17}/> 표시된 PDF 받기
                    </button>
                </div>
                <div className="sr-report-intro">
                    <div className="sr-report-icon"><ShieldCheck size={24}/></div>
                    <div>
                        <strong>{result.findings.length ? `${result.findings.length}건의 확인 신호가 발견됐어요` : '탐지된 위험 신호가 없어요'}</strong>
                        <p>{result.findings.length ? '계약 전 아래 조항과 권고 사항을 확인해 보세요.' : '자동 탐지 결과이며, 계약서가 안전하다는 의미는 아니에요.'}</p>
                    </div>
                </div>
                <div className="stats" aria-label="위험도별 분석 요약">
                    <div className="sr-stat-danger"><strong>{dangerCount}</strong><span>위험 조항</span></div>
                    <div className="sr-stat-warning"><strong>{warningCount}</strong><span>주의 조항</span></div>
                    <div className="sr-stat-missing"><strong>{result.missing_checks.length}</strong><span>미확인 항목</span></div>
                </div>
                <div className="sr-list-head">
                    <div><h3>발견된 위험 신호</h3><p>위험도를 선택하면 해당 항목만 볼 수 있어요.</p></div>
                    <div className="sr-filter-group" role="group" aria-label="위험도 필터">
                        <button type="button" className={filter === 'all' ? 'sr-filter active' : 'sr-filter'} aria-pressed={filter === 'all'} onClick={() => setFilter('all')}>전체 {result.findings.length}</button>
                        <button type="button" className={filter === 'danger' ? 'sr-filter active' : 'sr-filter'} aria-pressed={filter === 'danger'} onClick={() => setFilter('danger')}>위험 {dangerCount}</button>
                        <button type="button" className={filter === 'warning' ? 'sr-filter active' : 'sr-filter'} aria-pressed={filter === 'warning'} onClick={() => setFilter('warning')}>주의 {warningCount}</button>
                    </div>
                </div>
                {visibleFindings.length === 0 ? (
                    <div className="sr-empty sr-no-findings">{result.findings.length ? '선택한 위험도에 해당하는 조항이 없어요.' : '자동 탐지된 위험 문구가 없어요. 미탐지가 안전을 보장하지는 않아요.'}</div>
                ) : visibleFindings.map((f, i) => {
                    const legal = f.legal_explanation;
                    const ai = f.llm_analysis;
                    const hasCase = Boolean(legal?.case);
                    const originalIndex = result.findings.indexOf(f);
                    const laws = (f.related_laws ?? []).filter(law => law.name?.trim());
                    return (
                        <article key={originalIndex} className={'finding ' + f.severity + ' sr-finding'}>
                            <div className="sr-finding-head">
                                <div>
                                    <span className="sr-overline">확인 신호 {String(originalIndex + 1).padStart(2, '0')}</span>
                                    <h3>{f.title}</h3>
                                </div>
                                <span className={'chip ' + f.severity}>{f.severity === 'danger' ? '위험' : '주의'}</span>
                            </div>
                            <div className="sr-quote"><span>계약서 원문</span><p>“{f.quote}”</p></div>
                            <p className="sr-summary">{f.reason}</p>
                            <div className="sr-recommend"><strong>권고 사항</strong><p>{f.recommendation}</p></div>
                            <div className="sr-meta"><FileText size={14}/> {f.page != null ? `${f.page}페이지` : '페이지 정보 없음'} <span>·</span> PDF 원문 표시 {f.highlighted ? '완료' : '미확인'}</div>

                            {legal && (
                                <details className="sr-analysis sr-analysis-details">
                                    <summary className="sr-analysis-toggle">
                                        <span><FileCheck2 size={17}/> 법률 근거 및 AI 상세 분석 <em>{ai ? 'AI 분석 포함' : '규칙 기반 설명'}</em></span>
                                        <ChevronDown className="sr-toggle-chevron" size={19}/>
                                    </summary>
                                    <div className="sr-analysis-content">
                                        <section className="sr-info-card">
                                            <h5>관련 법률 조문</h5>
                                            <strong>{legal.law_name}{legal.article_number != null ? ` 제${legal.article_number}조` : ''}</strong>
                                            <p>{legal.article_text || '조문 원문을 확인하지 못했습니다.'}</p>
                                        </section>
                                        <section className="sr-info-card">
                                            <h5>관련 판례</h5>
                                            {hasCase && legal.case ? <>
                                                <strong>{legal.case.name} ({legal.case.case_number})</strong>
                                                {legal.case.relevance && <div className="sr-case-verification">
                                                    <span className="sr-case-badge">{legal.case.relevance === 'direct' ? '직접 관련 판례' : '간접 관련 · 참고 판례'}</span>
                                                    {legal.case.relevance_reason && <details className="sr-case-reason-details">
                                                        <summary>관련성 검토 이유 보기</summary>
                                                        <p>{legal.case.relevance_reason}</p>
                                                    </details>}
                                                </div>}
                                                <details className="sr-details">
                                                    <summary>판결 내용 자세히 보기</summary>
                                                    <p>{legal.case.judgment_summary || '판결요지 원문이 제공되지 않았습니다.'}</p>
                                                </details>
                                            </> : <div className="sr-empty">현재 검색 조건에서 적절한 관련 판례를 확보하지 못했어요. 관련 판례가 없다는 뜻은 아니에요.</div>}
                                        </section>
                                        <section className="sr-info-card sr-ai-card">
                                            <h5>위험한 이유 {ai && <span className="sr-ai-label">AI 분석</span>}</h5>
                                            <p>{ai?.risk_analysis || legal.risk_reason}</p>
                                        </section>
                                        {hasCase && <section className="sr-info-card">
                                            <h5>AI 판례 핵심 요약</h5>
                                            {ai?.case_summary ? <p>{ai.case_summary}</p> : <div className="sr-empty">AI 판례 요약이 제공되지 않았습니다.</div>}
                                        </section>}
                                        {ai?.limitations && <section className="sr-info-card sr-caution-card">
                                            <h5>추가 확인 사항</h5><p>{ai.limitations}</p>
                                        </section>}
                                        {laws.length > 0 && <details className="sr-reference-details">
                                            <summary>검색된 관련 법령 목록 ({laws.length}건)</summary>
                                            <ul>{laws.map((law, index) => <li key={index}>{law.name}{law.id != null ? ` · 법령 ID ${law.id}` : ''}</li>)}</ul>
                                        </details>}
                                        <p className="sr-disclaimer">{ai ? 'AI가 조회된 법률·판례를 바탕으로 생성한 참고용 설명입니다. ' : ''}{legal.verification_status} · 실제 법적 적용 여부는 별도 검토가 필요합니다.</p>
                                    </div>
                                </details>
                            )}
                        </article>
                    );
                })}
                <section className="sr-checks">
                    <h3><CheckCircle2 size={19}/> 계약서 기본 항목 점검</h3>
                    {result.missing_checks.length ? <ul>{result.missing_checks.map((x, i) => <li key={i}>{x}</li>)}</ul> :
                        <p>기본 확인 항목의 키워드는 모두 발견됐어요. 다만 각 조항의 적정성은 별도로 검토해야 해요.</p>}
                </section>
                <div className="notice sr-final-notice"><AlertCircle size={17}/><div><p>{result.references_status}</p><p>{result.disclaimer}</p></div></div>
            </section>}</main>
        <footer>SafeRent AI · 법률 자문 서비스가 아닌 사전 점검 도구</footer>
    </div>
}
