# -*- coding: utf-8 -*-
"""
crawl.py  —  Playwright로 KCI 2개 학회 논문 목록 수집
의존: pip install playwright && python -m playwright install chromium
사용법:
  python scripts/crawl.py           # 최근 2년치
  python scripts/crawl.py --year 2026  # 특정 연도
"""
import asyncio, json, sys, re, pathlib
from datetime import date
from playwright.async_api import async_playwright

BASE_DIR = pathlib.Path(__file__).parent.parent

JOURNALS = [
    {"key": "rea", "name": "한국지역경제학회", "sere_id": "SER000010170"},
    {"key": "tra", "name": "한국교통학회",    "sere_id": "000134"},
]

BASE_URL   = "https://www.kci.go.kr"
LIST_URL   = BASE_URL + "/kciportal/po/search/poArtiSearList.kci?sereId={sere_id}&pageNo={page}"
DETAIL_URL = BASE_URL + "/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId={arti_id}"

YEARS_BACK = 2   # 최근 N년치 수집


def current_years():
    y = date.today().year
    return list(range(y - YEARS_BACK, y + 1))


async def parse_row(row) -> dict | None:
    """tbody tr 한 행 파싱"""
    try:
        # 제목 + artiId
        link_el = await row.query_selector("a.subject")
        if not link_el:
            return None
        title = (await link_el.inner_text()).strip()
        href  = await link_el.get_attribute("href") or ""
        m     = re.search(r"artiId=(ART\d+)", href)
        arti_id = m.group(1) if m else ""

        # 저자
        author_els = await row.query_selector_all("ul.subject-info li a[href*='poCretDetail']")
        authors = list(dict.fromkeys(  # 중복 제거
            [(await a.inner_text()).strip() for a in author_els]
        ))

        # 나머지 td 텍스트 (권호·연도·페이지 등)
        tds = await row.query_selector_all("td")
        td_texts = [(await td.inner_text()).strip() for td in tds]

        # 연도 추출 (YYYY.MM 패턴)
        year = 0
        volume_str = ""
        for txt in td_texts:
            ym = re.search(r"(\d{4})\.\d{2}", txt)
            if ym:
                year = int(ym.group(1))
            vol = re.search(r"(\d+\(\d+\))", txt)
            if vol:
                volume_str = vol.group(1)

        return {
            "arti_id": arti_id,
            "title":   title,
            "authors": authors,
            "year":    year,
            "volume":  volume_str,
        }
    except Exception:
        return None


async def crawl_journal(page, journal: dict, target_years: list[int]) -> list[dict]:
    results = []
    page_no = 1
    stop    = False

    print(f"\n▶ {journal['name']} 수집 중...")

    while not stop:
        url = LIST_URL.format(sere_id=journal["sere_id"], page=page_no)
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
        except Exception as e:
            print(f"  [오류] 페이지 {page_no}: {e}")
            break

        rows = await page.query_selector_all("table tbody tr")
        if not rows:
            break

        page_found = 0
        for row in rows:
            item = await parse_row(row)
            if not item:
                continue

            if item["year"] and item["year"] < min(target_years):
                stop = True   # 수집 연도 이전이면 종료
                break

            if item["year"] in target_years:
                results.append({
                    "id":            f"{journal['key'].upper()}-{item['arti_id']}",
                    "journal":       journal["name"],
                    "journal_key":   journal["key"],
                    "kci_id":        item["arti_id"],
                    "title":         item["title"],
                    "authors":       item["authors"],
                    "year":          item["year"],
                    "volume":        item["volume"],
                    "abstract":      "",   # 상세 페이지에서 별도 수집 가능
                    "pdf_url":       "",
                    "kci_url":       DETAIL_URL.format(arti_id=item["arti_id"]),
                    "category_main": "",
                    "category_tags": [],
                    "summary":       "",
                    "key_question":  "",
                })
                page_found += 1
                print(f"  [{item['year']}] {item['title'][:50]}")

        print(f"  페이지 {page_no}: {page_found}건")
        if stop or len(rows) < 10:
            break
        page_no += 1
        await asyncio.sleep(0.5)   # 페이지 간 대기

    print(f"  소계: {len(results)}건")
    return results


async def fetch_abstracts(page, papers: list[dict]) -> list[dict]:
    """상세 페이지에서 초록 수집 (초록 없는 것만)"""
    need = [p for p in papers if not p.get("abstract")]
    if not need:
        return papers

    print(f"\n초록 수집 중 ({len(need)}건)...")
    for p in need:
        try:
            await page.goto(p["kci_url"], wait_until="networkidle", timeout=20000)
            # 초록 선택자
            for sel in ["#abstractKo", ".abstract-ko", "[class*='abstract'] p", ".cont-abstract"]:
                el = await page.query_selector(sel)
                if el:
                    text = (await el.inner_text()).strip()
                    if text:
                        p["abstract"] = text
                        break
            await asyncio.sleep(0.3)
        except Exception:
            pass

    return papers


async def main():
    target_years = current_years()
    if "--year" in sys.argv:
        idx = sys.argv.index("--year")
        if idx + 1 < len(sys.argv):
            target_years = [int(sys.argv[idx + 1])]

    print(f"수집 연도: {target_years}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page    = await browser.new_page()
        await page.set_extra_http_headers({"Accept-Language": "ko-KR,ko;q=0.9"})

        all_papers = []
        for journal in JOURNALS:
            papers = await crawl_journal(page, journal, target_years)
            all_papers.extend(papers)

        # 초록 수집
        all_papers = await fetch_abstracts(page, all_papers)

        await browser.close()

    # 기존 데이터와 병합
    raw_path = BASE_DIR / "data" / "raw_papers.json"
    existing = json.loads(raw_path.read_text(encoding="utf-8")) if raw_path.exists() else []
    seen     = {p["id"] for p in existing}
    added    = [p for p in all_papers if p["id"] not in seen]
    merged   = existing + added

    raw_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n총 {len(merged)}건 저장 (신규 {len(added)}건) → {raw_path}")


if __name__ == "__main__":
    asyncio.run(main())
