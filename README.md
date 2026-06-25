# 학술 저널 대시보드

KCI·AEA 논문을 자동 수집·요약하여 GitHub Pages에 배포하는 대시보드.

- **사이트**: https://beechnamu.github.io/journal-dashboard/
- **업데이트**: 매월 마지막 금요일 12:00 자동 실행

---

## 클론 후 설치 순서

### 1. 레포 클론

```bash
git clone https://github.com/beechnamu/journal-dashboard.git
cd journal-dashboard
```

### 2. Python 패키지 설치

```bash
pip install -r requirements.txt
```

### 3. Playwright (브라우저 자동화) 설치

```bash
pip install playwright
python -m playwright install chromium
```

> Playwright는 `requirements.txt`에 포함되지 않아 **별도로** 설치해야 합니다.

### 4. API 키 설정

프로젝트 루트에 `.env` 파일 생성:

```
GEMINI_API_KEY=여기에_발급받은_키_입력
GEMINI_MODEL=gemini-2.5-flash-lite
```

Gemini API 키 발급: https://aistudio.google.com/app/apikey (무료)

---

## 실행 순서

### 전체 파이프라인 (순서대로)

```bash
# 1. 논문 수집 (KCI + AEA, 최근 2년치)
python scripts/crawl.py

# 2. AI 요약 생성 (Gemini, 미완료 논문만)
python scripts/summarize.py

# 3. 빌드 + GitHub 자동 푸시
python scripts/build.py --force
```

### 특정 연도만 수집

```bash
python scripts/crawl.py --year 2026
```

---

## 의존 패키지

| 패키지 | 설치 방법 | 용도 |
|--------|-----------|------|
| `requests` | `pip install -r requirements.txt` | Gemini API 호출 |
| `python-dotenv` | `pip install -r requirements.txt` | .env 환경변수 로드 |
| `playwright` | `pip install playwright` + `python -m playwright install chromium` | KCI·AEA 웹 스크래핑 |

---

## 주의사항

- `data/raw_papers.json` — gitignore 대상이므로 클론 후 **크롤링부터 다시** 실행
- `.env` — gitignore 대상이므로 **직접 생성** 필요 (API 키 포함)
- Gemini 무료 티어: 분당 10건 제한 → 요약 완료까지 논문 수에 따라 수십 분 소요
- GitHub 푸시 권한: `git push`가 되려면 해당 계정으로 `gh auth login` 또는 SSH 키 설정 필요
