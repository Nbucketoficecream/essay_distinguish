#coding:utf-8
import requests
from bs4 import BeautifulSoup
from googlesearch import search
if __name__ == "__main__":
  try:
    results = list(search("台灣大學 site:ntu.edu.tw", num_results=3, lang="zh-tw"))
    print("✅ 搜尋成功！找到結果：")
    for r in results:
        print(r)
  except Exception as e:
    print("❌ Google 搜尋模組無法使用：", e)

def essay_post(url):
  headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
  }
  response=requests.get(url,headers=headers)
  soup = BeautifulSoup(response.content, 'html.parser')
  button=soup.find_all('td')
  for but in button:
   if "電子全文" in but.text:
    if "本篇電子全文限研究生所屬學校校內系統及IP範圍內開放" in but.text:
     return False
    else:return True
    break
def classify(name: str) -> tuple[str, str]:
    """
    回傳 (狀態, 連結)：
      - ("電子全文", url)
      - ("紙本全文", url)   # 有頁面但沒有對外電子全文
      - ("未找到", "")      # 找不到 NDLTD 連結
    """
    # 你安裝的是 googlesearch-python 1.2.3 → 參數用 num_results、lang
    for url in search(name, num_results=5, lang="zh-tw", sleep_interval=2):
        if "ndltd.ncl.edu.tw" in url:
            return ("電子全文", url) if essay_post(url) else ("紙本全文", url)
    return ("未找到", "")
         
    
