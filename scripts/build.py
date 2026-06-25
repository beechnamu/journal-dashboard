# -*- coding: utf-8 -*-
"""
build.py  —  최종 papers.json 빌드 + GitHub 푸시
사용법: python scripts/build.py
윈도우 작업 스케줄러: 매월 마지막 금요일 12:00 실행
"""
import os, json, subprocess, pathlib, sys, calendar
from datetime import date


def is_last_friday_of_month(d: date = None) -> bool:
    """오늘이 이달의 마지막 금요일(weekday=4)인지 확인"""
    d = d or date.today()
    if d.weekday() != 4:   # 금요일이 아니면 False
        return False
    # 7일 후가 같은 달이면 마지막 금요일이 아님
    next_friday = d.replace(day=d.day + 7) if d.day + 7 <= calendar.monthrange(d.year, d.month)[1] else None
    return next_friday is None

BASE_DIR   = pathlib.Path(__file__).parent.parent
RAW_PATH   = BASE_DIR / "data" / "raw_papers.json"
OUT_PATH   = BASE_DIR / "data" / "papers.json"
SCRIPTS    = BASE_DIR / "scripts"


def run(cmd: list[str], cwd=None):
    result = subprocess.run(cmd, cwd=cwd or BASE_DIR, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[오류] {' '.join(cmd)}\n{result.stderr}")
        sys.exit(1)
    return result.stdout.strip()


def build_json():
    """raw_papers.json → papers.json (불필요 필드 제거, 정렬)"""
    if not RAW_PATH.exists():
        print("raw_papers.json 없음")
        sys.exit(1)

    raw = json.loads(RAW_PATH.read_text(encoding="utf-8"))

    # abstract, kci_id 등 내부 필드 제거 후 정렬
    clean = []
    for p in raw:
        clean.append({
            "id":             p["id"],
            "journal":        p["journal"],
            "journal_key":    p["journal_key"],
            "title":          p["title"],
            "authors":        p["authors"],
            "year":           p["year"],
            "volume":         p["volume"],
            "category_main":  p["category_main"],
            "category_tags":  p["category_tags"],
            "summary":        p["summary"],
            "key_question":   p["key_question"],
            "kci_url":        p["kci_url"],
            "pdf_url":        p.get("pdf_url", ""),
        })

    # 최신순 정렬
    clean.sort(key=lambda x: (x["year"], x["id"]), reverse=True)

    output = {
        "updated": date.today().isoformat(),
        "papers":  clean,
    }
    OUT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"papers.json 생성 완료 ({len(clean)}건)")


def git_push():
    """변경사항 커밋 후 GitHub 푸시"""
    today = date.today().isoformat()

    # git 상태 확인
    status = run(["git", "status", "--porcelain"])
    if not status:
        print("변경사항 없음 — 푸시 생략")
        return

    run(["git", "add", "data/papers.json"])
    run(["git", "commit", "-m", f"chore: 저널 업데이트 {today}"])
    run(["git", "push", "origin", "main"])
    print(f"GitHub 푸시 완료 ({today})")


if __name__ == "__main__":
    # 스케줄러에서 매주 금요일 실행 — 마지막 금요일인지 확인
    if "--force" not in sys.argv and not is_last_friday_of_month():
        print(f"오늘({date.today().isoformat()})은 이달의 마지막 금요일이 아닙니다. 종료.")
        sys.exit(0)

    print("=" * 50)
    print(f"학술 저널 대시보드 빌드 — {date.today().isoformat()}")
    print("=" * 50)

    # 1. 크롤링
    print("\n[1/3] KCI 크롤링...")
    exec(open(SCRIPTS / "crawl.py", encoding="utf-8").read())

    # 2. Gemini 요약
    print("\n[2/3] Gemini 요약...")
    exec(open(SCRIPTS / "summarize.py", encoding="utf-8").read())

    # 3. 빌드 + 푸시
    print("\n[3/3] 빌드 및 GitHub 푸시...")
    build_json()
    git_push()

    print("\n✅ 전체 완료")
