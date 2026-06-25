# -*- coding: utf-8 -*-
"""
summarize.py  —  Gemini API로 논문 요약·분류·핵심질문 생성
사용법: python scripts/summarize.py
"""
import os, json, time, pathlib, requests
from dotenv import load_dotenv

BASE_DIR = pathlib.Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")

API_KEY  = os.getenv("GEMINI_API_KEY", "")
MODEL    = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"

MAIN_CATEGORIES = [
    "거시경제·미시경제",
    "노동·고용",
    "지역개발·도시",
    "계량·통계·데이터분석",
    "품질경영·생산성",
    "산업·무역",
    "기타",
]

SYSTEM_PROMPT = f"""당신은 학술 논문 분석 전문가입니다.
논문 제목과 초록을 보고 아래 JSON 형식으로 정확히 응답하세요.

{{
  "category_main": "<아래 대분류 중 하나>",
  "category_tags": ["<세부태그1>", "<세부태그2>", "<세부태그3>"],
  "summary": "<논문의 연구목적·방법·결론을 3~5줄로 요약. 한국어.>",
  "key_question": "<이 논문이 제기하는 핵심 학술·정책 질문 1개. 한국어.>"
}}

대분류 목록: {", ".join(MAIN_CATEGORIES)}

규칙:
- category_main은 반드시 대분류 목록 중 하나
- category_tags는 2~4개, 핵심 키워드
- summary는 객관적 서술, 논문 내 근거 기반
- key_question은 "~인가?" 형태의 질문문
- JSON만 출력, 다른 텍스트 없음"""


def call_gemini(title: str, abstract: str) -> dict | None:
    user_text = f"[제목]\n{title}\n\n[초록]\n{abstract or '(초록 없음)'}"
    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": user_text}]}],
        "generationConfig": {
            "temperature":    0.2,
            "maxOutputTokens": 800,
            "responseMimeType": "application/json",
        },
    }
    for attempt in range(3):
        try:
            res = requests.post(
                GEMINI_URL,
                params={"key": API_KEY},
                json=payload,
                timeout=30,
            )
            data = res.json()
            if res.status_code == 429:   # rate limit
                wait = 65
                import re
                m = re.search(r"retry in (\d+)", data.get("error", {}).get("message", ""))
                if m:
                    wait = int(m.group(1)) + 5
                print(f"  [한도 초과] {wait}초 대기 후 재시도...")
                time.sleep(wait)
                continue
            if not res.ok:
                print(f"  [API 오류] {data.get('error', {}).get('message', res.status_code)}")
                return None
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(text)
        except Exception as e:
            print(f"  [오류] {e}")
            return None
    return None


def summarize_all():
    raw_path = BASE_DIR / "data" / "raw_papers.json"
    if not raw_path.exists():
        print("raw_papers.json 없음 — crawl.py 먼저 실행하세요.")
        return

    papers = json.loads(raw_path.read_text(encoding="utf-8"))
    print(f"{len(papers)}건 요약 시작...\n")

    for i, p in enumerate(papers, 1):
        if p.get("summary"):   # 이미 요약된 논문 건너뜀
            continue

        print(f"[{i}/{len(papers)}] {p['title'][:50]}...")
        result = call_gemini(p["title"], p.get("abstract", ""))

        if result:
            p["category_main"] = result.get("category_main", "기타")
            p["category_tags"] = result.get("category_tags", [])
            p["summary"]       = result.get("summary", "")
            p["key_question"]  = result.get("key_question", "")
            print(f"  OK {p['category_main']} / {p['category_tags']}")
        else:
            p["category_main"] = "기타"
            p["category_tags"] = []
            p["summary"]       = "(요약 실패)"
            p["key_question"]  = ""

        time.sleep(7)   # 분당 10건 한도 → 6초 이상 간격

    # 요약 결과 덮어쓰기
    raw_path.write_text(json.dumps(papers, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n요약 완료 → {raw_path}")


if __name__ == "__main__":
    summarize_all()
