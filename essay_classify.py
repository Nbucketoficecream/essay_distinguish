# coding: utf-8
import re
import time
import random
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE = "https://ndltd.ncl.edu.tw"
UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0",
]
HEADERS["User-Agent"] = random.choice(UAS)

# 全域變數（保持你想要的 essay_title 名稱）
essay_title = ""

# 全域共用 session 與 CCD 快取，減少被當機器人的風險
SESSION = requests.Session()
SESSION.headers.update(HEADERS)
CCD_CACHE = {"value": None}
TITLE_HTML_CACHE = {}  # 可選：快取同標題查詢結果，避免重複請求

def _looks_like_captcha(resp: requests.Response) -> bool:
    """簡單判斷是否被 captcha/防護頁攔截（不嘗試繞過）"""
    if resp is None:
        return True
    if resp.status_code in (403, 429):
        return True
    url_low = resp.url.lower() if resp.url else ""
    body_low = (resp.text or "").lower()
    hints = ["驗證碼", "請輸入驗證碼", "我不是機器人", "recaptcha", "/sorry/", "cloudflare", "cf-challenge", "human verification"]
    if any(h in url_low for h in hints):
        return True
    if any(h in body_low for h in hints):
        return True
    return False

def _ensure_ccd():
    """取得並快取 CCD（若遇到驗證碼則回 None）"""
    if CCD_CACHE["value"]:
        return CCD_CACHE["value"]

    try:
        # 隨機短暫延遲，讓請求更像人為操作
        time.sleep(random.uniform(0.5, 1.2))
        r = SESSION.get(f"{BASE}/cgi-bin/gs32/gsweb.cgi/webmge?mode=basic", timeout=12, allow_redirects=True)
    except Exception:
        return None

    if _looks_like_captcha(r):
        return None

    m = re.search(r"ccd=([A-Za-z0-9]+)", r.text)
    if not m:
        return None
    CCD_CACHE["value"] = m.group(1)
    return CCD_CACHE["value"]

def search_thesis(title: str, min_delay: float = 3.5, max_delay: float = 8.5):
    """
    在 NDLTD 中搜尋論文名稱，返回搜尋結果 HTML。
    - 使用全域 SESSION 與 CCD 快取。
    - 加入隨機 sleep (jitter) 以降低觸發驗證碼機率。
    - 回傳 "驗證碼審查機制" 表示檢測到驗證碼/被攔截。
    """
    global essay_title
    essay_title = title  # 使用全域變數（你要求的不改變名稱）

    # 快取：若同題已查過直接回 HTML（避免重複請求）
    if title in TITLE_HTML_CACHE:
        return TITLE_HTML_CACHE[title]

    # 取得 CCD
    ccd = _ensure_ccd()
    if not ccd:
        return "驗證碼審查機制"

    # 節流：每次查詢前隨機 sleep（模擬人類間隔）
    delay = random.uniform(min_delay, max_delay)
    time.sleep(delay)

    action = f"{BASE}/cgi-bin/gs32/gsweb.cgi/ccd={ccd}/search"
    payload = {"qs0": title, "searchmode": "basic"}
    headers = {"Referer": f"{BASE}/cgi-bin/gs32/gsweb.cgi/webmge?mode=basic"}

    try:
        r = SESSION.post(action, data=payload, headers=headers, timeout=18, allow_redirects=True)
    except Exception:
        return "驗證碼審查機制"

    # 若被擋回傳特定字串
    if _looks_like_captcha(r):
        # 碰到 captcha 就把 CCD 清掉，避免下次用錯的 CCD，但不自動重試
        CCD_CACHE["value"] = None
        return "驗證碼審查機制"

    # 成功：快取並回傳 HTML
    TITLE_HTML_CACHE[title] = r.text
    return r.text

# 你原本的 parse_result(html) 簽名保持不變（直接使用全域 essay_title）
def parse_result(html):
    """解析搜尋結果頁，只處理與全域 essay_title 比對的論文"""
    soup = BeautifulSoup(html, "html.parser")
    matched = []

    for block in soup.select("td.std2"):
        title_tag = block.select_one("a.slink")
        title = title_tag.get_text(strip=True) if title_tag else "無標題"

        # 使用全域 essay_title 做比對（忽略空白與大小寫）
        if title.replace(" ", "").lower() == essay_title.replace(" ", "").lower():
            title_url = urljoin(BASE, title_tag.get("href")) if title_tag else None

            fulltext_tag = block.find("a", string=lambda t: t and "電子全文" in t)
            web_essay = fulltext_tag is not None

            paper_tag = block.find("a", string=lambda t: t and "紙本論文" in t)
            paper_essay = paper_tag is not None

            matched = {
                "title": title,
                "title_url": title_url,
                "web_essay": web_essay,
                "paper_essay": paper_essay,
            }
            print("DEBUG matched:", matched)
            break

    return matched  # 若沒找到會回空 list []，呼叫端可用 if not result 判斷

def classify(name: str) -> list[str]:
    """
    統一回傳三欄 [web_status, paper_status, title_url]（固定長度）
    - 若遇驗證碼回 ["驗證碼審查", "", ""]
    - 若查無此論文回 ["", "", ""]
    """
    html = search_thesis(name)
    if html == "驗證碼審查機制":
        return ["驗證碼審查", "", ""]

    result = parse_result(html)
    if not result:
        return ["", "", ""]  # 查無此論文

    url = result.get("title_url") or ""
    web = "電子全文" if result.get("web_essay") else ""
    paper = "紙本全文" if result.get("paper_essay") else ""
    return [web, paper, url]

