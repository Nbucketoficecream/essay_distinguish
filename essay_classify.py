#coding:utf-8
from email.message import EmailMessage
import requests
from bs4 import BeautifulSoup
from googlesearch import search
from urllib.parse import urljoin
BASE = "https://ndltd.ncl.edu.tw"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}
essay_title=""
def search_thesis(title: str):
    """在 NDLTD 中搜尋論文名稱，返回搜尋結果 HTML"""
    essay_title=title
    with requests.Session() as s:
        s.headers.update(HEADERS)

        # step 1️⃣：先開啟首頁（取得 cookie 與 ccd）
        ndltd_web = s.get(f"{BASE}/cgi-bin/gs32/gsweb.cgi/webmge?mode=basic", timeout=10)
        ndltd_web.raise_for_status()
        soup1 = BeautifulSoup(ndltd_web.text, "html.parser")
        if "驗證碼審查機制" in ndltd_web.text:
          return "驗證碼審查機制"  # 遇到驗證碼審查機制，直接放棄
        # step 2️⃣：找出 form 的 action（動態包含 ccd=xxxxx）
        form = soup1.find("form")
        action = urljoin(ndltd_web.url, form.get("action")) if form and form.get("action") else ndltd_web.url

        # step 3️⃣：組合 POST 資料
        payload = {
            "ysearchinput0": title,  # 論文名稱輸入框
            "searchmode": "basic",
        }
        # 同時帶上所有隱藏欄位，確保搜尋成功
        for inp in form.select("input[type=hidden][name]"):
            payload[inp["name"]] = inp.get("value", "")

        # step 4️⃣：送出搜尋請求
        thesis_result = s.post(action, data=payload, timeout=15)
        thesis_result.raise_for_status()
        return  thesis_result.text
#解析網頁
def parse_result(html):
    """解析搜尋結果頁，只處理與使用者輸入名稱吻合的論文"""
    soup = BeautifulSoup(html, "html.parser")


    for block in soup.select("td.std2"):  # 每篇論文一個區塊
        title_tag = block.select_one("a.slink")
        title = title_tag.get_text(strip=True) if title_tag else "無標題"

        # ✳️ 判斷是否與使用者輸入吻合（忽略空白與大小寫）
        if title.replace(" ", "").lower() == essay_title.replace(" ", "").lower():
            print(f"✅ 找到符合的論文標題：{title}")

            # ✅ 論文主連結（標題的 <a>）
            title_url = urljoin(BASE, title_tag.get("href")) if title_tag else None

            # ✅ 檢查「電子全文」是否為超連結
            fulltext_tag = block.find("a", string=lambda t: t and "電子全文" in t)
            web_essay = fulltext_tag is not None         

            # ✅ 檢查「紙本論文」是否存在
            paper_tag = block.find(string=lambda t: t and "紙本論文" in t)
            paper_essay = paper_tag is not None


        break  # 找到第一個就結束迴圈
    return {
                "title": essay_title,
                "title_url": title_url,
                "web_essay": web_essay,
                "paper_essay": paper_essay,             
            }
    return None  # 沒有找到符合的論文

def classify(name: str) -> list[str]:
    if search_thesis(name) == "驗證碼審查機制":
      return ["驗證碼審查機制"]
    elif parse_result(search_thesis(name))==None:
      return ["查無此論文"]
    result = parse_result(search_thesis(name))
    if result["web_essay"] and result["paper_essay"]:
        return ["電子全文","紙本全文", result["title_url"]]
    elif result["web_essay"]:
        return ["電子全文", result["title_url"]]
    elif result["paper_essay"]:
        return ["紙本全文", result["title_url"]]
    else:
        return ["查無此論文"]
         
    
