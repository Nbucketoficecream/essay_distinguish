#coding:utf-8
import requests
from bs4 import BeautifulSoup
from googlesearch import search

def essay_post(url):
  headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
  }
  response=requests.get(url,headers=headers)
  soup = BeautifulSoup(response.content, 'html.parser')
  if "驗證碼檢查機制" in soup.get_text():
    return "驗證碼"
  button=soup.find_all('td')
  for but in button:
   if "電子全文" in but.text:
    if "本篇電子全文限研究生所屬學校校內系統及IP範圍內開放" in but.text:
     return False
    else:return True
    break
def classify(name: str) -> tuple[str, str]:
    for url in search(name, num_results=5, lang="zh-tw", sleep_interval=20):
        if "ndltd.ncl.edu.tw" in url:
            return ("電子全文", url) if essay_post(url) else ("紙本全文", url)
    return ("未找到", "")
         
    
