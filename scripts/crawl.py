# -*- coding: utf-8 -*-
"""
crawl.py  —  KCI에서 4개 학회 최신 논문 목록 수집
사용법: python scripts/crawl.py
"""
import os, time, json, pathlib, requests
from datetime import datetime

BASE_DIR = pathlib.Path(__file__).parent.parent

# ── KCI 학회 설정 ──────────────────────────────────────────────────────────
# journal_cd: KCI 저널 코드 (crawl 후 실제 코드로 교체 필요)
JOURNALS = [
    {"key": "kea", "name": "한국경제학회",  "journal_cd": "J000550"},
    {"key": "rea", "name": "지역경제학회",  "journal_cd": "J000000"},  # 확인 필요
    {"key": "das", "name": "자료분석학회",  "journal_cd": "J000000"},  # 확인 필요
    {"key": "qms", "name": "품질경영학회",  "journal_cd": "J000460"},
]

KCI_API   = "https://www.kci.go.kr/kciportal/po/openapi/openApiJournal.kci"
KCI_ART   = "https://www.kci.go.kr/kciportal/po/openapi/openApiArticle.kci"
HEADERS   = {"User-Agent": "Mozilla/5.0 (compatible; JournalBot/1.0)"}
MAX_PAGES = 3   # 학회당 최대 페이지 수 (페이지당 10건)


def fetch_articles(journal_cd: str, page: int = 1) -> list[dict]:
    """KCI OpenAPI로 논문 목록 조회"""
    params = {
        "journalCd": journal_cd,
        "pageNum":   page,
        "pageSize":  10,
        "openYn":    "Y",   # 오픈 액세스만
    }
    try:
        res = requests.get(KCI_ART, params=params, headers=HEADERS, timeout=15)
        res.raise_for_status()
        data = res.json()
        return data.get("article", [])
    except Exception as e:
        print(f"  [오류] {journal_cd} p{page}: {e}")
        return []


def fetch_article_detail(arti_id: str) -> dict:
    """논문 상세 정보(초록 등) 조회"""
    params = {"artiId": arti_id}
    try:
        res = requests.get(KCI_ART, params=params, headers=HEADERS, timeout=15)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print(f"  [오류] 상세 {arti_id}: {e}")
        return {}


def crawl_all() -> list[dict]:
    """전체 학회 크롤링"""
    results = []

    for j in JOURNALS:
        print(f"\n▶ {j['name']} ({j['journal_cd']}) 크롤링 중...")
        for page in range(1, MAX_PAGES + 1):
            articles = fetch_articles(j["journal_cd"], page)
            if not articles:
                break

            for art in articles:
                arti_id = art.get("artiId", "")
                item = {
                    "id":           f"{j['key'].upper()}-{arti_id}",
                    "journal":      j["name"],
                    "journal_key":  j["key"],
                    "kci_id":       arti_id,
                    "title":        art.get("artiNm", "").strip(),
                    "authors":      [a.strip() for a in art.get("authNm", "").split(",") if a.strip()],
                    "year":         int(art.get("pubYear", 0) or 0),
                    "volume":       art.get("volNum", ""),
                    "abstract":     art.get("abstractKo", "") or art.get("abstractEn", ""),
                    "pdf_url":      art.get("pdfUrl", ""),
                    "kci_url":      f"https://www.kci.go.kr/kciportal/landing/article.kci?arti_id={arti_id}",
                    # summarize.py가 채울 필드
                    "category_main": "",
                    "category_tags": [],
                    "summary":       "",
                    "key_question":  "",
                }
                results.append(item)
                print(f"  └ {item['title'][:40]}...")

            time.sleep(0.5)   # KCI 서버 부하 방지

    print(f"\n총 {len(results)}건 수집 완료")
    return results


def save_raw(papers: list[dict]):
    """크롤링 원본 저장 (summarize.py 입력용)"""
    out = BASE_DIR / "data" / "raw_papers.json"
    out.write_text(json.dumps(papers, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"원본 저장: {out}")


if __name__ == "__main__":
    papers = crawl_all()
    save_raw(papers)
