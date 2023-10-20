#coding:utf-8
import requests
from bs4 import BeautifulSoup
from googlesearch import search
def button(url):
  headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
  }
  response=requests.get(url,headers=headers)
  soup = BeautifulSoup(response.content, 'html.parser')
  button=soup.find_all('a')
  for but in button:
   if "電子全文" in but.text:   
    return True
    break
  return False   
def essay(url):
  if button(url)==True:
   headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
  }
   response=requests.get(url,headers=headers)
   soup = BeautifulSoup(response.content, 'html.parser')
   essay = soup.select('font.fullhight_light')
   for item in essay:
            if "本篇電子全文限研究生所屬學校校內系統及IP範圍內開放" in item.text:
                return True
  else:return False
   
       
     
with open("(電子論文)能在論文系統上找到.txt","w",encoding='utf-8') as filea:  
 with open("(紙本論文)能在論文系統上找到.txt","w",encoding='utf-8') as fileb:
  with open("無法在論文系統上找到.txt","w",encoding='utf-8') as filec:
   with open("輸入端.txt","r",encoding='UTF-8') as data:
    print("執行中 完成後會自動關閉")
    names=data.readlines()
    for name in names:
     name=name.strip( )
     num=0
     for url in search(name, stop=5,lang="zh-tw"):
      if "ndltd.ncl.edu.tw" in url:
       if button(url)==True:
        if essay(url)==True:
         fileb.write("(只限在校ip)%s:\n%s\n"%(name,url))
         break
        else:
         filea.write("%s:\n%s\n"%(name,url))
         break
       else:
        fileb.write("%s:\n%s\n"%(name,url))
       break
      else:
       num+=1
      if num==5:
       filec.write("%s \n"%name)
print("已完成")
