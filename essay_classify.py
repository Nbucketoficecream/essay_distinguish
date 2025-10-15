# -*- coding: utf-8 -*-
from __future__ import annotations
import random, time
from typing import Optional, Dict, Any, List

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

NDLTD_URL = "https://ndltd.ncl.edu.tw/cgi-bin/gs32/gsweb.cgi/webmge?mode=basic"

def _build_driver(headless: bool, profile_path: Optional[str], version_main: Optional[int] = 141):
    options = webdriver.ChromeOptions()
    if profile_path:
        options.add_argument(f"--user-data-dir={profile_path}")
    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--lang=zh-TW")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    # 避免 devtools 連線偶發報錯
    options.add_argument("--remote-allow-origins=*")

    if version_main:
        service = ChromeService(ChromeDriverManager(version_main=version_main).install())
    else:
        service = ChromeService(ChromeDriverManager().install())

    driver = webdriver.Chrome(service=service, options=options)
    try:
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument",
                               {"source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"})
    except Exception:
        pass
    return driver

# 1) search_thesis：只要 HTML 含「驗證碼」就直接回傳 "驗證碼審查"
def search_thesis(title: str, driver: webdriver.Chrome, timeout: int = 30) -> str:
    driver.get(NDLTD_URL)
    wait = WebDriverWait(driver, 15)
    # 搜尋欄
    box = wait.until(EC.presence_of_element_located((By.ID, "ysearchinput0")))
    # 人類式打字
    box.clear()
    for ch in title:
        box.send_keys(ch)
        time.sleep(0.05 + random.random() * 0.05)
    box.send_keys(Keys.RETURN)

    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "td.std2, table"))
        )
    except Exception:
        pass

    html = driver.page_source or ""
    if "驗證碼" in html:
        return "驗證碼審查"
    return html

# 2) parse_result：用 <a> 是否存在判斷有無電子/紙本全文
def parse_result(html: str) -> Optional[Dict[str, Any]]:
    if not html or html == "驗證碼審查":
        return None
    soup = BeautifulSoup(html, "html.parser")

    link = soup.select_one("td.std2 a.slink") or soup.select_one("a[href*='record']")
    if not link or not link.get("href"):
        return None
    title_url = link.get("href")

    has_web = bool(soup.find("a", string=lambda s: s and "電子全文" in s))
    has_paper = bool(soup.find("a", string=lambda s: s and ("紙本論文" in s or "圖書紙本論文" in s)))

    return {"title_url": title_url, "web_essay": has_web, "paper_essay": has_paper}

# 3) classify：套用你的三欄格式
def classify(name: str):
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
    html = search_thesis(name, driver=driver, timeout=30)
    if html == "驗證碼審查":
        return ["驗證碼審查", "", ""]
    r = parse_result(html)
    if not r:
        return ["", "", ""]
    return ["電子全文" if r["web_essay"] else "",
            "紙本全文" if r["paper_essay"] else "",
            r["title_url"]]

