# 학술 저널 대시보드 — 프로젝트 문서

> 카피라이터 밤나무  
> 최종 업데이트: 2026-06-25

---

## 개요

KCI(한국학술지인용색인) 및 AEA(미국경제학회) 오픈 저널 데이터를 자동 수집·요약하여
GitHub Pages에 배포하는 정적 대시보드.

- **배포 URL**: https://beechnamu.github.io/journal-dashboard/
- **GitHub 레포**: https://github.com/beechnamu/journal-dashboard (public)
- **업데이트 주기**: 매월 마지막 금요일 12:00 (윈도우 작업 스케줄러 자동 실행)
- **AI 요약**: Gemini 2.5 Flash Lite API (gemini-2.5-flash-lite)

---

## 대상 학회

### KCI 국내 학회 (Playwright 웹 크롤링)

| key | 학회명 | KCI sere_id | 비고 |
|-----|--------|-------------|------|
| rea | 한국지역경제학회 | SER000010170 | 실제 수집 중 |
| tra | 한국교통학회 | 000134 | 실제 수집 중 |
| kea | 한국경제학회 | — | 필터 등록만 (미수집) |
| das | 한국자료분석학회 | — | 필터 등록만 (미수집) |
| qms | 한국품질경영학회 | — | 필터 등록만 (미수집) |
| roa | 한국도로학회 | — | 필터 등록만 (미수집) |

### AEA 해외 학회 (aeaweb.org 크롤링)

| key | 저널명 | 코드 | 비고 |
|-----|--------|------|------|
| aea | American Economic Review | aer | 3년 이상 오픈 |
| aea | Journal of Economic Perspectives | jep | 완전 오픈 |
| aea | AEJ: Applied Economics | app | 완전 오픈 |
| aea | AEJ: Economic Policy | pol | 완전 오픈 |
| aea | AEJ: Macroeconomics | mac | 완전 오픈 |
| aea | AEJ: Microeconomics | mic | 완전 오픈 |

---

## 폴더 구조

```
journal-dashboard/
├── index.html              대시보드 UI (GitHub Pages)
├── .env                    Gemini API 키 (Git 제외)
├── .gitignore
├── requirements.txt
├── PROJECT.md              이 문서
├── data/
│   ├── papers.json         공개 논문 데이터 (빌드 산출물, Git 포함)
│   └── raw_papers.json     크롤링 원본 + 요약 중간 결과 (Git 제외)
└── scripts/
    ├── crawl.py            KCI + AEA 논문 수집 (Playwright)
    ├── summarize.py        Gemini API 요약·분류·핵심질문 생성
    └── build.py            최종 JSON 빌드 + GitHub 푸시
```

---

## 카드 구성

논문 카드에 표시되는 정보 (순서대로):

1. **학회 뱃지** (색상 구분) + **주제 대분류** + **세부 태그** 2~4개
2. **논문 제목**
3. **저자 · 발행연도 · 권호**
4. **AI 요약** — 3~5줄, Gemini 생성 (연구목적·방법·결론)
5. **메모장** — 브라우저 localStorage 저장 (800ms 디바운스)
6. **핵심 질문** — Gemini가 생성한 학술·정책 질문 1개
7. **원문 링크** — KCI 또는 aeaweb.org 직접 연결

---

## 주제 분류 체계

Gemini가 아래 7개 대분류 중 하나로 자동 분류하고 세부 태그를 부여합니다.

| 대분류 | 세부 예시 |
|--------|-----------|
| 거시경제·미시경제 | GDP, 인플레이션, 소비자이론 |
| 노동·고용 | 임금, 고용률, 노동시장 |
| 지역개발·도시 | 도시계획, 지역균형발전, 인프라 |
| 계량·통계·데이터분석 | 회귀분석, 머신러닝, 패널데이터 |
| 품질경영·생산성 | TQM, 6시그마, 생산성지수 |
| 산업·무역 | 수출입, 공급망, 산업정책 |
| 기타 | 위 분류에 해당하지 않는 논문 |

---

## 학회별 뱃지 색상

| key | 학회 | 색상 코드 |
|-----|------|-----------|
| aea | AEA | #1e3a8a (네이비) |
| kea | 한국경제학회 | #e53e3e (레드) |
| rea | 지역경제학회 | #38a169 (그린) |
| das | 자료분석학회 | #805ad5 (퍼플) |
| qms | 품질경영학회 | #dd6b20 (오렌지) |
| roa | 한국도로학회 | #2b6cb0 (블루) |
| tra | 한국교통학회 | #b7791f (브라운) |

---

## 환경 설정

### 1. 패키지 설치

```bash
pip install -r requirements.txt
pip install playwright
python -m playwright install chromium
```

`requirements.txt`:
```
requests==2.32.3
python-dotenv==1.0.1
```

### 2. API 키 설정 (`.env`)

```
GEMINI_API_KEY=발급받은_키
GEMINI_MODEL=gemini-2.5-flash-lite
```

Gemini API 키 발급: https://aistudio.google.com/app/apikey

### 3. 수동 실행 순서

```bash
# 1단계: 크롤링 (최근 2년치)
python scripts/crawl.py

# 특정 연도만 수집
python scripts/crawl.py --year 2026

# 2단계: Gemini 요약 생성 (미완료 논문만)
python scripts/summarize.py

# 3단계: 빌드 + GitHub 푸시 (마지막 금요일이 아니면 종료)
python scripts/build.py

# 강제 빌드 (날짜 무관)
python scripts/build.py --force
```

---

## 크롤링 상세

### KCI 크롤러 (`crawl.py`)

- **방식**: Playwright (Chromium, headless) — JS 렌더링 필요
- **URL 패턴**: `https://www.kci.go.kr/kciportal/po/search/poArtiSearList.kci?sereId={sere_id}&pageNo={page}`
- **파싱**: `table tbody tr` → `a.subject` (제목/artiId), `ul.subject-info li a` (저자)
- **연도 필터**: 최근 2년 (YEARS_BACK = 2), `--year YYYY`로 지정 가능
- **초록 수집**: 상세 페이지 (`ciSereArtiView.kci`) 별도 방문

### AEA 크롤러 (`crawl.py` 내 `crawl_aea()`)

- **방식**: Playwright — aeaweb.org JS 렌더링
- **이슈 목록**: `https://www.aeaweb.org/journals/{code}/issues`
- **해당 연도 호만** 필터링 후 논문 수집
- **Accept-Language**: `en-US,en;q=0.9` (KCI와 다른 헤더 사용)

---

## AI 요약 상세

### Gemini API 설정

- **모델**: `gemini-2.5-flash-lite`
- **엔드포인트**: `https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent`
- **출력 형식**: `responseMimeType: "application/json"` 강제

### 요청 구조 (논문당)

```json
{
  "category_main": "대분류 중 하나",
  "category_tags": ["태그1", "태그2", "태그3"],
  "summary": "3~5줄 한국어 요약",
  "key_question": "핵심 학술·정책 질문 1개 (~인가? 형태)"
}
```

### 속도 제한 처리

- **무료 티어**: 분당 10건
- **기본 딜레이**: 요청 간 7초
- **429 재시도**: 오류 메시지에서 대기 시간 파싱 → 최대 3회 재시도
- **기존 요약 건너뜀**: `summary` 필드가 비어있는 논문만 처리

---

## 자동화 (윈도우 작업 스케줄러)

### 등록 방법 (PowerShell)

```powershell
$action = New-ScheduledTaskAction `
    -Execute "python" `
    -Argument "C:\Users\L2404161\claude\2026-06-25\journal-dashboard\scripts\build.py" `
    -WorkingDirectory "C:\Users\L2404161\claude\2026-06-25\journal-dashboard"

$trigger = New-ScheduledTaskTrigger -Weekly -WeeksInterval 1 -DaysOfWeek Friday -At "12:00"

Register-ScheduledTask `
    -TaskName "JournalDashboardUpdate" `
    -Action   $action `
    -Trigger  $trigger `
    -Force
```

> **참고**: 작업 스케줄러는 "마지막 금요일"을 직접 지원하지 않습니다.
> `build.py`의 `is_last_friday_of_month()` 함수가 매주 금요일 실행 시
> "이달의 마지막 금요일인지" 확인하고, 아니면 아무것도 하지 않고 종료합니다.

### 전체 파이프라인 (`build.py`)

```
is_last_friday_of_month? → NO → 종료
         ↓ YES
crawl.py 실행 (크롤링)
         ↓
summarize.py 실행 (요약)
         ↓
papers.json 빌드 (요약 실패 제외, 연도 내림차순)
         ↓
git add data/papers.json → commit → push origin master
```

---

## GitHub Pages 배포

- **브랜치**: `master` (main 아님)
- **루트 경로**: `/` (별도 docs/ 폴더 불필요)
- **레포 공개 여부**: public (무료 플랜 GitHub Pages 요건)
- **`.env` 보안**: `.gitignore`에 포함 — API 키 미노출

---

## 데이터 현황 (2026-06-25 기준)

| 항목 | 수치 |
|------|------|
| 전체 수집 논문 | 40건 (raw_papers.json) |
| 요약 완료 | 13건 |
| 요약 미완료 | 27건 |
| 공개 배포 (papers.json) | 13건 |
| 수집 학회 | 한국지역경제학회(rea), 한국교통학회(tra) + AEA 추가 중 |
| 수집 연도 | 2024~2026 |

---

## 주요 이슈 및 해결

| 이슈 | 원인 | 해결 |
|------|------|------|
| KCI OAI-PMH sereId 필터 미작동 | set 파라미터가 per-journal 지원 안 함 | Playwright 웹 스크래핑으로 전환 |
| OAI-PMH 5000건 후 타임아웃 | 서버 레이트 리밋 | Playwright 방식으로 완전 대체 |
| Gemini 429 에러 | 무료 티어 분당 10건 제한 | 7초 딜레이 + 재시도 로직 추가 |
| GitHub Pages 미작동 | private 레포는 무료 플랜 미지원 | public 전환 (.env gitignore 확인 후) |
| Task Scheduler RunLevel Highest 오류 | 관리자 권한 없음 | RunLevel 제거, 현재 사용자 수준 등록 |
| `git push origin main` 실패 | 브랜치명이 master | `origin master`로 수정 |
| 터미널 UnicodeEncodeError | cp949 터미널에서 ✔ 문자 출력 | `✔` → `OK`로 대체 |

---

## 업데이트 이력

| 날짜 | 내용 |
|------|------|
| 2026-06-25 | 최초 구축 — KCI OAI-PMH 시도 → Playwright 전환 |
| 2026-06-25 | 한국지역경제학회·한국교통학회 2개 학회 Playwright 크롤링 성공 |
| 2026-06-25 | Gemini 요약 13건 완료, GitHub Pages 배포 |
| 2026-06-25 | 업데이트 날짜 영역에 "카피라이터 밤나무" 추가 |
| 2026-06-25 | AEA(미국경제학회) 6개 저널 추가 — UI 뱃지·필터·크롤러 |
