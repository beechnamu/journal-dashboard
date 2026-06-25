# 학술 저널 대시보드 — 프로젝트 문서

## 개요

KCI(한국학술지인용색인) 오픈 저널 데이터를 자동 수집·요약하여 GitHub Pages에 배포하는 정적 대시보드.

- **대상 학회**: 6개 (한국경제학회, 한국지역경제학회, 한국자료분석학회, 한국품질경영학회, 한국도로학회, 한국교통학회)
- **업데이트**: 매월 마지막 금요일 12:00 (윈도우 작업 스케줄러)
- **배포**: https://beechnamu.github.io/journal-dashboard/
- **레포**: https://github.com/beechnamu/journal-dashboard

---

## 학회 정보

| 학회 | KCI sereId | key |
|------|-----------|-----|
| 한국경제학회 | publisher-name 필터 | kea |
| 한국지역경제학회 | publisher-name 필터 | rea |
| 한국자료분석학회 | publisher-name 필터 | das |
| 한국품질경영학회 | publisher-name 필터 | qms |
| 한국도로학회 | publisher-name 필터 | roa |
| 한국교통학회 (대한교통학회) | publisher-name 필터 | tra |

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
│   ├── papers.json         공개 논문 데이터 (빌드 산출물)
│   └── raw_papers.json     크롤링 원본 (Git 제외)
└── scripts/
    ├── crawl.py            KCI OAI-PMH 수집
    ├── summarize.py        Gemini API 요약·분류·질문 생성
    └── build.py            최종 JSON 빌드 + GitHub 푸시
```

---

## 카드 구성

논문 카드에 표시되는 정보:

1. 학회명 뱃지 + 주제 대분류 + 세부 태그
2. 논문 제목
3. 저자 · 발행연도 · 권호
4. 요약 (3~5줄, Gemini 생성)
5. 메모장 (브라우저 localStorage에 저장)
6. 핵심 질문 1개 (Gemini 생성)
7. KCI 원문 링크

---

## 주제 대분류

Gemini가 아래 7개 중 하나로 자동 분류 + 세부 태그 2~4개 자동 부여:

- 거시경제·미시경제
- 노동·고용
- 지역개발·도시
- 계량·통계·데이터분석
- 품질경영·생산성
- 산업·무역
- 기타

---

## 데이터 수집 방식

**KCI OAI-PMH** (`open.kci.go.kr/oai/request`)

- API 키 불필요, 합법적 수집
- `set=ARTI`로 전체 논문 수집 후 `publisher-name`으로 6개 학회 필터링
- 초기 수집: `--full` 옵션 (최근 2년)
- 월별 업데이트: 지난달 1일 이후 증분 수집

---

## 환경 설정

### 1. 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. API 키 설정

`.env` 파일:

```
GEMINI_API_KEY=발급받은_키
GEMINI_MODEL=gemini-2.5-flash-lite
```

Gemini API 키 발급: https://aistudio.google.com/app/apikey

### 3. 수동 실행

```bash
# 크롤링 (지난달 이후)
python scripts/crawl.py

# 크롤링 (전체 2년치)
python scripts/crawl.py --full

# 요약 생성
python scripts/summarize.py

# 빌드 + GitHub 푸시
python scripts/build.py
```

---

## 자동화 (윈도우 작업 스케줄러)

매월 마지막 금요일 12:00 자동 실행 설정:

### PowerShell로 등록

```powershell
$action  = New-ScheduledTaskAction `
    -Execute "python" `
    -Argument "C:\Users\L2404161\claude\2026-06-25\journal-dashboard\scripts\build.py" `
    -WorkingDirectory "C:\Users\L2404161\claude\2026-06-25\journal-dashboard"

$trigger = New-ScheduledTaskTrigger -Weekly -WeeksInterval 1 -DaysOfWeek Friday -At "12:00"

Register-ScheduledTask `
    -TaskName "JournalDashboardUpdate" `
    -Action   $action `
    -Trigger  $trigger `
    -RunLevel Highest `
    -Force
```

> **주의**: 윈도우 작업 스케줄러는 "마지막 금요일"을 직접 지원하지 않으므로,
> `build.py`에 "오늘이 이달의 마지막 금요일인지" 확인 로직이 포함되어 있습니다.

---

## 의존 패키지

| 패키지 | 용도 |
|--------|------|
| sickle | KCI OAI-PMH 수집 |
| requests | Gemini API 호출 |
| python-dotenv | .env 환경변수 로드 |

---

## 업데이트 이력

| 날짜 | 내용 |
|------|------|
| 2026-06-25 | 최초 구축 (6개 학회, GitHub Pages 배포) |
