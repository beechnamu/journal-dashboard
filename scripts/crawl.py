# -*- coding: utf-8 -*-
"""
crawl.py  —  KCI OAI-PMH로 4개 학회 최신 논문 목록 수집
의존: pip install sickle
사용법: python scripts/crawl.py
"""
import json, time, pathlib
from datetime import date, timedelta
from sickle import Sickle
from sickle.oaiexceptions import NoRecordsMatch

BASE_DIR = pathlib.Path(__file__).parent.parent

OAI_ENDPOINT = "https://open.kci.go.kr/oai/request"

# sereId: KCI 학술지 식별 코드
JOURNALS = [
    {"key": "kea", "name": "한국경제학회",   "sere_id": "000214"},
    {"key": "rea", "name": "한국지역경제학회", "sere_id": "SER000010170"},
    {"key": "das", "name": "한국자료분석학회", "sere_id": "000930"},
    {"key": "qms", "name": "한국품질경영학회", "sere_id": "000306"},
    {"key": "roa", "name": "한국도로학회",    "sere_id": "001414"},
    {"key": "tra", "name": "한국교통학회",    "sere_id": "000134"},
]

DELAY = 0.5   # 요청 간 지연(초) — 서버 부하 방지


def parse_record(record, journal: dict) -> dict | None:
    """OAI-PMH 레코드 → 논문 딕셔너리"""
    try:
        meta = record.metadata
        arti_id = record.header.identifier.split(":")[-1]

        title = (meta.get("title") or [""])[0].strip()
        if not title:
            return None

        authors_raw = meta.get("creator") or []
        authors = [a.strip() for a in authors_raw if a.strip()]

        year_raw = (meta.get("date") or ["0"])[0]
        year = int(year_raw[:4]) if year_raw else 0

        abstract = (meta.get("description") or [""])[0].strip()
        volume   = (meta.get("source") or [""])[0].strip()

        return {
            "id":            f"{journal['key'].upper()}-{arti_id}",
            "journal":       journal["name"],
            "journal_key":   journal["key"],
            "kci_id":        arti_id,
            "title":         title,
            "authors":       authors,
            "year":          year,
            "volume":        volume,
            "abstract":      abstract,
            "pdf_url":       "",
            "kci_url":       f"https://www.kci.go.kr/kciportal/landing/article.kci?arti_id={arti_id}",
            # summarize.py가 채울 필드
            "category_main": "",
            "category_tags": [],
            "summary":       "",
            "key_question":  "",
        }
    except Exception as e:
        print(f"  [파싱 오류] {e}")
        return None


def crawl_journal(sickle: Sickle, journal: dict, from_date: str | None = None) -> list[dict]:
    """학회 1개 수집"""
    params = {
        "metadataPrefix": "oai_kci",
        "set":            journal["sere_id"],
    }
    if from_date:
        params["from"] = from_date

    print(f"\n▶ {journal['name']} (sereId={journal['sere_id']}) 수집 중...")

    results = []
    try:
        records = sickle.ListRecords(**params)
        for record in records:
            item = parse_record(record, journal)
            if item:
                results.append(item)
                print(f"  └ [{item['year']}] {item['title'][:45]}...")
            time.sleep(DELAY)
    except NoRecordsMatch:
        print(f"  (신규 논문 없음)")
    except Exception as e:
        print(f"  [오류] {e}")

    return results


def crawl_all(incremental: bool = False) -> list[dict]:
    """전체 학회 수집
    incremental=True: 지난달 이후 논문만 수집 (월별 업데이트용)
    """
    from_date = None
    if incremental:
        # 지난달 1일부터 수집
        today = date.today()
        first_of_last_month = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
        from_date = first_of_last_month.isoformat()
        print(f"증분 수집 모드: {from_date} 이후")

    sickle = Sickle(OAI_ENDPOINT)
    all_papers = []

    for j in JOURNALS:
        papers = crawl_journal(sickle, j, from_date)
        all_papers.extend(papers)

    print(f"\n총 {len(all_papers)}건 수집 완료")
    return all_papers


def merge_with_existing(new_papers: list[dict]) -> list[dict]:
    """기존 raw_papers.json과 병합 (중복 제거)"""
    raw_path = BASE_DIR / "data" / "raw_papers.json"

    existing = []
    if raw_path.exists():
        existing = json.loads(raw_path.read_text(encoding="utf-8"))

    existing_ids = {p["id"] for p in existing}
    added = [p for p in new_papers if p["id"] not in existing_ids]

    merged = existing + added
    print(f"기존 {len(existing)}건 + 신규 {len(added)}건 = {len(merged)}건")
    return merged


def save_raw(papers: list[dict]):
    out = BASE_DIR / "data" / "raw_papers.json"
    out.write_text(json.dumps(papers, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"저장: {out}")


if __name__ == "__main__":
    # 첫 실행: incremental=False (전체)
    # 월별 업데이트: incremental=True
    papers = crawl_all(incremental=False)
    merged = merge_with_existing(papers)
    save_raw(merged)
